import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime
import math
import requests
from fuzzywuzzy import fuzz # Adicionado import que faltava

# ------------------------------------------------------------------------------
# 1. CONFIGURAÇÃO E INFRAESTRUTURA (FIREBASE)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="GeralJá | Ecossistema Profissional",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
            st.error(f"Erro Crítico de Conexão: {e}")
            st.stop()
    return firebase_admin.get_app()

app_engine = inicializar_infraestrutura_dados()
db = firestore.client()

# ------------------------------------------------------------------------------
# 2. PARÂMETROS E INTELIGÊNCIA
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

# --- FUNÇÕES UTILITÁRIAS ---
def processar_servico_ia(texto):
    if not texto: return None
    t_clean = texto.lower()
    for prof, palavras in MAPA_PROFISSOES.items():
        if any(p in t_clean for p in palavras): return prof
    for prof in LISTA_AREAS_DROP:
        if prof.lower() in t_clean: return prof
    
    # Fuzzy Match
    melhor_match, maior_score = None, 0
    for prof in LISTA_AREAS_DROP:
        score = fuzz.partial_ratio(t_clean, prof.lower())
        if score > 80 and score > maior_score:
            maior_score = score
            melhor_match = prof
    return melhor_match if melhor_match else "Ajudante Geral"

def processar_foto(file):
    if file is not None:
        return base64.b64encode(file.read()).decode()
    return None

def exibir_foto(base64_string, width=300):
    if base64_string:
        st.image(f"data:image/png;base64,{base64_string}", use_container_width=True)

# ------------------------------------------------------------------------------
# 4. DESIGN SYSTEM (CSS)
# ------------------------------------------------------------------------------
st.markdown("""
    <style>
    .stApp { background-color: #F1F5F9; }
    .card-pro { background: white; border-radius: 15px; padding: 20px; border-left: 10px solid #0047AB; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 10px; }
    .btn-zap { background: #25D366; color: white !important; padding: 12px; border-radius: 10px; text-decoration: none; display: block; text-align: center; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 5. INTERFACE
# ------------------------------------------------------------------------------
UI_ABAS = st.tabs(["🔍 BUSCAR", "💼 CARTEIRA", "📝 CADASTRAR", "🛡️ ADMIN"])

with UI_ABAS[0]:
    c1, c2 = st.columns([1, 2])
    cidade_filtro = c1.text_input("📍 Localização", key="busc_cid")
    termo_busca = c2.text_input("🛠️ O que você precisa?", key="busc_ter")

    if termo_busca:
        cat = processar_servico_ia(termo_busca)
        st.info(f"IA: Buscando por {cat}")
        query = db.collection("profissionais").where("area", "==", cat).where("aprovado", "==", True).stream()
        
        encontrados = 0
        for d in query:
            p = d.to_dict()
            if not cidade_filtro or cidade_filtro.lower() in p.get('cidade', '').lower():
                encontrados += 1
                st.markdown(f'<div class="card-pro"><h3>{p["nome"].upper()}</h3><p>{p.get("descricao", "")}</p></div>', unsafe_allow_html=True)
                
                # PORTFÓLIO E FOTOS
                with st.expander(f"👁️ Ver Portfólio de {p['nome']}"):
                    st.write(f"📍 Atende em: {p.get('cidade')}")
                    fotos = p.get('portfolio', [])
                    if fotos:
                        cols = st.columns(2)
                        for idx, img in enumerate(fotos):
                            with cols[idx % 2]: exibir_foto(img)
                    else: st.write("Sem fotos.")

                if p.get('saldo', 0) >= TAXA_CONTATO:
                    if st.button(f"WHATSAPP DE {p['nome'].split()[0]}", key=f"zap_{d.id}"):
                        db.collection("profissionais").document(d.id).update({"saldo": firestore.Increment(-TAXA_CONTATO)})
                        st.markdown(f'<a href="https://wa.me/55{p["whatsapp"]}" class="btn-zap">ABRIR WHATSAPP</a>', unsafe_allow_html=True)

with UI_ABAS[1]:
    if 'logado' not in st.session_state: st.session_state.logado = False
    
    if not st.session_state.logado:
        lz = st.text_input("WhatsApp", key="log_z")
        ls = st.text_input("Senha", type="password", key="log_s")
        if st.button("ENTRAR"):
            doc = db.collection("profissionais").document(lz).get()
            if doc.exists and doc.to_dict().get('senha') == ls:
                st.session_state.logado = True
                st.session_state.user_id = lz
                st.rerun()
    else:
        u_ref = db.collection("profissionais").document(st.session_state.user_id)
        u_data = u_ref.get().to_dict()
        
        menu = st.segmented_control("Menu", ["Financeiro", "Editar Perfil", "Fotos"], default="Financeiro")
        
        if menu == "Financeiro":
            st.metric("Saldo", f"{u_data.get('saldo')} cr")
            st.code(f"PIX: {PIX_OFICIAL}")
        elif menu == "Editar Perfil":
            with st.form("ed"):
                n_nome = st.text_input("Nome", value=u_data.get('nome'))
                n_desc = st.text_area("Bio", value=u_data.get('descricao'))
                if st.form_submit_button("Salvar"):
                    u_ref.update({"nome": n_nome, "descricao": n_desc})
                    st.rerun()
        elif menu == "Fotos":
            f_up = st.file_uploader("Subir Trabalho", type=['jpg', 'png'])
            if st.button("Enviar Foto"):
                if f_up:
                    lista = u_data.get('portfolio', [])
                    if len(lista) < 4:
                        lista.append(processar_foto(f_up))
                        u_ref.update({"portfolio": lista})
                        st.rerun()
            
            # Galeria de remoção
            fotos_atuais = u_data.get('portfolio', [])
            for i, f in enumerate(fotos_atuais):
                exibir_foto(f, width=150)
                if st.button(f"Remover {i}", key=f"del_{i}"):
                    fotos_atuais.pop(i)
                    u_ref.update({"portfolio": fotos_atuais})
                    st.rerun()

# ABA 3 e 4 (CADASTRAR E ADMIN) permanecem como no seu código original, apenas certifique-se da indentação.
