import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime
import math
from fuzzywuzzy import fuzz

# ------------------------------------------------------------------------------
# 1. INFRAESTRUTURA E CONEXÃO
# ------------------------------------------------------------------------------
st.set_page_config(page_title="GeralJá | Ecossistema Profissional", page_icon="🏙️", layout="wide")

@st.cache_resource
def inicializar_infraestrutura_dados():
    if not firebase_admin._apps:
        try:
            b64_key = st.secrets["FIREBASE_BASE64"]
            decoded_json = base64.b64decode(b64_key).decode("utf-8")
            cred_dict = json.loads(decoded_json)
            credenciais = credentials.Certificate(cred_dict)
            return firebase_admin.initialize_app(credenciais)
        except Exception as e:
            st.error(f"Erro Crítico: {e}")
            st.stop()
    return firebase_admin.get_app()

app_engine = inicializar_infraestrutura_dados()
db = firestore.client()

# ------------------------------------------------------------------------------
# 2. PARÂMETROS GERAIS
# ------------------------------------------------------------------------------
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ACESSO_ADMIN = "mumias"
TAXA_CONTATO = 1
BONUS_WELCOME = 5

MAPA_PROFISSOES = {
    "Encanador": ["vazamento", "cano", "torneira", "esgoto", "hidraulico", "caixa d'água", "pia", "privada", "infiltração"],
    "Eletricista": ["fio", "luz", "chuveiro", "tomada", "disjuntor", "curto", "energia", "fiação", "lâmpada"],
    "Pintor": ["pintar", "parede", "verniz", "massa corrida", "textura", "grafiato", "pintura"],
    "Pedreiro": ["reforma", "construção", "tijolo", "cimento", "piso", "azulejo", "alvenaria", "muro", "laje"],
    "Marceneiro": ["madeira", "móvel", "armário", "porta", "guarda-roupa", "restauração"],
    "Mecânico": ["carro", "motor", "freio", "suspensão", "oficina", "veículo", "bateria"],
    "Diarista": ["limpeza", "faxina", "passar roupa", "organização", "casa", "lavar"],
    "Manicure": ["unha", "esmalte", "mão", "pé", "cutícula", "gel"],
    "Cabeleireiro": ["cabelo", "corte", "tintura", "escova", "progressiva", "luzes"],
    "Barbeiro": ["barba", "degrade", "navalha", "cabelo masculino"],
    "Técnico TI": ["computador", "notebook", "celular", "wi-fi", "formatar", "software", "internet", "wifi"],
    "Refrigeração": ["ar condicionado", "geladeira", "freezer", "carregar gás"],
    "Montador": ["montar", "desmontar", "móveis", "guarda-roupa", "armário"],
    "Freteiro": ["frete", "mudança", "transporte", "carreto", "entrega", "vuc"],
    "Jardineiro": ["grama", "jardim", "planta", "poda", "adubo", "roçagem"],
    "Gesseiro": ["gesso", "drywall", "sanca", "forro", "moldura"]
}
LISTA_AREAS_DROP = sorted(list(MAPA_PROFISSOES.keys()) + ["Ajudante Geral"])
LISTA_ESTADOS = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]

# ------------------------------------------------------------------------------
# 3. MOTORES AUXILIARES
# ------------------------------------------------------------------------------
def processar_servico_ia(texto):
    if not texto: return None
    t_clean = texto.lower()
    for prof, palavras in MAPA_PROFISSOES.items():
        if any(p in t_clean for p in palavras): return prof
    for prof in LISTA_AREAS_DROP:
        if prof.lower() in t_clean: return prof
    melhor_match, maior_score = None, 0
    for prof in LISTA_AREAS_DROP:
        score = fuzz.partial_ratio(t_clean, prof.lower())
        if score > 80 and score > maior_score:
            maior_score, melhor_match = score, prof
    return melhor_match if melhor_match else "Ajudante Geral"

def processar_foto(file):
    if file:
        return base64.b64encode(file.read()).decode()
    return None

def exibir_foto(b64):
    if b64:
        st.image(f"data:image/png;base64,{b64}", use_container_width=True)

# ------------------------------------------------------------------------------
# 4. DESIGN (CSS)
# ------------------------------------------------------------------------------
st.markdown("""
    <style>
    .card-pro { background: white; border-radius: 15px; padding: 20px; border-left: 10px solid #0047AB; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .btn-zap { background: #25D366; color: white !important; padding: 12px; border-radius: 10px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 5. INTERFACE PRINCIPAL
# ------------------------------------------------------------------------------
UI_ABAS = st.tabs(["🔍 BUSCAR", "💼 CARTEIRA", "📝 CADASTRAR", "🛡️ ADMIN"])

# --- ABA 1: BUSCA ---
with UI_ABAS[0]:
    c1, c2 = st.columns([1, 2])
    cidade_filtro = c1.text_input("📍 Localização", key="cid_in", placeholder="Cidade")
    termo_busca = c2.text_input("🛠️ O que você precisa?", key="term_in", placeholder="Ex: Chuveiro queimou")

    if termo_busca:
        cat = processar_servico_ia(termo_busca)
        st.info(f"✨ IA detectou: **{cat}**")
        query = db.collection("profissionais").where("area", "==", cat).where("aprovado", "==", True).stream()
        
        encontrados = 0
        for d in query:
            p = d.to_dict()
            if not cidade_filtro or cidade_filtro.lower() in p.get('cidade', '').lower():
                encontrados += 1
                with st.container():
                    st.markdown(f'<div class="card-pro"><h3>{p["nome"].upper()}</h3><p>{p.get("descricao", "")}</p><small>📍 {p.get("cidade")} - {p.get("uf")}</small></div>', unsafe_allow_html=True)
                    
                    with st.expander("👁️ Ver Perfil e Portfólio"):
                        st.write(p.get("descricao"))
                        fotos = p.get('portfolio', [])
                        if fotos:
                            cols = st.columns(2)
                            for idx, img in enumerate(fotos):
                                with cols[idx%2]: exibir_foto(img)
                    
                    if p.get('saldo', 0) >= TAXA_CONTATO:
                        if st.button(f"VER WHATSAPP DE {p['nome'].split()[0].upper()}", key=f"btn_{d.id}"):
                            db.collection("profissionais").document(d.id).update({
                                "saldo": firestore.Increment(-TAXA_CONTATO),
                                "cliques": firestore.Increment(1)
                            })
                            st.markdown(f'<a href="https://wa.me/55{p["whatsapp"]}" target="_blank" class="btn-zap">CHAMAR NO WHATSAPP</a>', unsafe_allow_html=True)
                    else:
                        st.warning("Profissional offline.")
        if encontrados == 0:
            st.warning("Nenhum profissional encontrado.")

# --- ABA 2: CARTEIRA ---
with UI_ABAS[1]:
    if 'logado' not in st.session_state:
        st.session_state.logado = False
    
    if not st.session_state.logado:
        st.subheader("🔑 Login do Profissional")
        lz = st.text_input("WhatsApp", key="login_z")
        ls = st.text_input("Senha", type="password", key="login_s")
        if st.button("ACESSAR"):
            doc = db.collection("profissionais").document(lz).get()
            if doc.exists and doc.to_dict().get('senha') == ls:
                st.session_state.logado, st.session_state.user_id = True, lz
                st.rerun()
            else:
                st.error("Dados incorretos.")
    else:
        u_ref = db.collection("profissionais").document(st.session_state.user_id)
        u_data = u_ref.get().to_dict()
        tab_p1, tab_p2, tab_p3 = st.tabs(["💰 Saldo", "📝 Editar Perfil", "📸 Portfólio"])
        
        with tab_p1:
            st.metric("Meus Créditos", f"{u_data.get('saldo')} GeralCoins")
            st.divider()
            st.code(f"PIX: {PIX_OFICIAL}")
            st.markdown(f'<a href="https://wa.me/{ZAP_ADMIN}" class="btn-zap">ENVIAR COMPROVANTE</a>', unsafe_allow_html=True)
            if st.button("DESLOGAR"):
                st.session_state.logado = False
                st.rerun()

        with tab_p2:
            with st.form("edit_perfil"):
                n_nome = st.text_input("Nome", value=u_data.get('nome'))
                n_desc = st.text_area("Descrição", value=u_data.get('descricao'))
                n_cid = st.text_input("Cidade", value=u_data.get('cidade'))
                if st.form_submit_button("SALVAR"):
                    u_ref.update({"nome": n_nome, "descricao": n_desc, "cidade": n_cid})
                    st.success("Atualizado!")
                    st.rerun()

        with tab_p3:
            f_up = st.file_uploader("Subir foto", type=['jpg', 'png'])
            if st.button("SUBIR FOTO") and f_up:
                p_list = u_data.get('portfolio', [])
                if len(p_list) < 4:
                    p_list.append(processar_foto(f_up))
                    u_ref.update({"portfolio": p_list})
                    st.rerun()
            for i, f_b64 in enumerate(u_data.get('portfolio', [])):
                exibir_foto(f_b64)
                if st.button(f"Excluir Foto {i+1}", key=f"del_{i}"):
                    curr = u_data.get('portfolio', [])
                    curr.pop(i)
                    u_ref.update({"portfolio": curr})
                    st.rerun()

# --- ABA 3: CADASTRO ---
with UI_ABAS[2]:
    st.subheader("📝 Novo Cadastro")
    with st.form("form_cad", clear_on_submit=True):
        c_nome = st.text_input("Nome Completo")
        c_zap = st.text_input("WhatsApp (DDD + Número)")
        c_pass = st.text_input("Senha", type="password")
        c_area = st.selectbox("Especialidade", LISTA_AREAS_DROP)
        c_cid = st.text_input("Cidade")
        c_uf = st.selectbox("Estado", LISTA_ESTADOS, index=24)
        c_desc = st.text_area("Descrição")
        if st.form_submit_button("CADASTRAR"):
            if c_nome and c_zap and c_pass:
                if db.collection("profissionais").document(c_zap).get().exists:
                    st.error("WhatsApp já cadastrado.")
                else:
                    db.collection("profissionais").document(c_zap).set({
                        "nome": c_nome, "whatsapp": c_zap, "senha": c_pass, "area": c_area,
                        "cidade": c_cid, "uf": c_uf, "descricao": c_desc, "saldo": BONUS_WELCOME,
                        "cliques": 0, "rating": 5.0, "aprovado": False, "portfolio": [],
                        "data_cadastro": datetime.datetime.now()
                    })
                    st.success("Cadastrado! Aguarde aprovação.")
            else:
                st.warning("Preencha os campos obrigatórios.")

# --- ABA 4: ADMIN ---
with UI_ABAS[3]:
    adm_p = st.text_input("Senha Admin", type="password")
    if adm_p == CHAVE_ACESSO_ADMIN:
        pends = db.collection("profissionais").where("aprovado", "==", False).stream()
        for p_doc in pends:
            pd = p_doc.to_dict()
            col_a, col_b = st.columns([3,1])
            col_a.write(f"👤 {pd['nome']} | {pd['area']}")
            if col_b.button("APROVAR", key=f"ap_{p_doc.id}"):
                db.collection("profissionais").document(p_doc.id).update({"aprovado": True})
                st.rerun()
        
        st.divider()
        target = st.text_input("WhatsApp para Recarga")
        valor = st.number_input("Moedas", min_value=1, value=10)
        if st.button("RECARREGAR"):
            db.collection("profissionais").document(target).update({"saldo": firestore.Increment(valor)})
            st.success("Recarregado!")
