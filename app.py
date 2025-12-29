# ==============================================================================
# GERALJÁ BRASIL - PROFESSIONAL EDITION v2.1 (ESTÁVEL & ESCALÁVEL)
# ==============================================================================
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime
import math
import random
import re

# ------------------------------------------------------------------------------
# 1. CONFIGURAÇÃO E METADADOS (Obrigatório ser o primeiro comando Streamlit)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="GeralJá | Ecossistema Nacional de Serviços",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ------------------------------------------------------------------------------
# 2. CONSTANTES E INFRAESTRUTURA (Definir antes de usar nas abas)
# ------------------------------------------------------------------------------
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ACESSO_ADMIN = "mumias"
TAXA_CONTATO = 1
BONUS_WELCOME = 5
LAT_SP_REF, LON_SP_REF = -23.5505, -46.6333

LISTA_ESTADOS = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]

# Dicionário de Profissões e Palavras-Chave para a IA
MAPA_PROFISSOES = {
    "Encanador": ["vazamento", "cano", "torneira", "esgoto", "hidraulico", "caixa d'água", "pia", "privada"],
    "Eletricista": ["fio", "luz", "chuveiro", "tomada", "disjuntor", "curto", "energia", "fiação"],
    "Pintor": ["pintar", "parede", "verniz", "massa corrida", "textura", "grafiato"],
    "Pedreiro": ["reforma", "construção", "tijolo", "cimento", "piso", "azulejo", "alvenaria", "laje"],
    "Marceneiro": ["madeira", "móvel", "armário", "porta", "guarda-roupa", "restauração"],
    "Mecânico": ["carro", "motor", "freio", "suspensão", "oficina", "veículo"],
    "Diarista": ["limpeza", "faxina", "passar roupa", "organização", "casa"],
    "Manicure": ["unha", "esmalte", "mão", "pé", "cutícula"],
    "Cabeleireiro": ["cabelo", "corte", "tintura", "escova", "progressiva"],
    "Barbeiro": ["barba", "degrade", "navalha"],
    "Técnico TI": ["computador", "notebook", "celular", "wi-fi", "formatar", "software"],
    "Refrigeração": ["ar condicionado", "geladeira", "freezer", "carregar gás"],
    "Montador": ["montar", "desmontar", "móveis", "ikea", "magazine"],
    "Freteiro": ["frete", "mudança", "transporte", "carreto", "entrega"],
    "Jardineiro": ["grama", "jardim", "planta", "poda", "adubo"],
    "Gesseiro": ["gesso", "drywall", "sanca", "forro"]
}

LISTA_AREAS_DROP = sorted(list(MAPA_PROFISSOES.keys()) + ["Ajudante Geral"])

# ------------------------------------------------------------------------------
# 3. CONEXÃO FIREBASE
# ------------------------------------------------------------------------------
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
            st.error(f"Erro de Conexão: {e}")
            st.stop()
    return firebase_admin.get_app()

app_engine = inicializar_infraestrutura_dados()
db = firestore.client()

# ------------------------------------------------------------------------------
# 4. FUNÇÕES CORE (LÓGICA E IA)
# ------------------------------------------------------------------------------
def processar_servico_ia(texto):
    if not texto: return "Ajudante Geral"
    t_clean = texto.lower()
    for prof, palavras in MAPA_PROFISSOES.items():
        if any(p in t_clean for p in palavras):
            return prof
    return "Ajudante Geral"

def calcular_distancia(lat1, lon1, lat2, lon2):
    try:
        R = 6371.0
        dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))), 1)
    except: return 0.0

# ------------------------------------------------------------------------------
# 5. UI CUSTOMIZADA (CSS)
# ------------------------------------------------------------------------------
st.markdown("""
    <style>
    .stApp { background-color: #F0F2F6; }
    .main-header { text-align: center; padding: 2rem; background: white; border-radius: 0 0 30px 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 2rem; }
    .azul { color: #0047AB; font-weight: 900; font-size: 45px; }
    .laranja { color: #FF8C00; font-weight: 900; font-size: 45px; }
    .card-pro { background: white; padding: 20px; border-radius: 15px; border-left: 8px solid #0047AB; margin-bottom: 15px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    .btn-wpp { background-color: #25D366; color: white !important; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><span class="azul">GERAL</span><span class="laranja">JÁ</span><br><b>SOLUÇÕES PROFISSIONAIS 24H</b></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 6. SISTEMA DE NAVEGAÇÃO
# ------------------------------------------------------------------------------
UI_ABAS = st.tabs(["🔍 ENCONTRAR PROFISSIONAL", "💼 MEU PAINEL", "📝 QUERO ME CADASTRAR", "🛡️ ADMIN"])

# --- ABA 1: BUSCA ---
with UI_ABAS[0]:
    c1, c2 = st.columns([1, 2])
    cid_busca = c1.text_input("📍 Cidade", placeholder="Sua cidade")
    termo = c2.text_input("🛠️ O que você precisa?", placeholder="Ex: Eletricista, Pintor, Faxina...")
    
    if termo:
        cat_sugerida = processar_servico_ia(termo)
        st.caption(f"Categoria detectada: **{cat_sugerida}**")
        
        # Busca no Firebase
        query = db.collection("profissionais").where("area", "==", cat_sugerida).where("aprovado", "==", True).stream()
        results = []
        for d in query:
            p = d.to_dict()
            if not cid_busca or cid_busca.lower() in p.get('cidade', '').lower():
                p['id'] = d.id
                results.append(p)
        
        if results:
            for r in results:
                dist = calcular_distancia(LAT_SP_REF, LON_SP_REF, r.get('lat', LAT_SP_REF), r.get('lon', LON_SP_REF))
                with st.container():
                    st.markdown(f"""
                    <div class="card-pro">
                        <h3>{r['nome'].upper()} ⭐ {r.get('rating', 5.0)}</h3>
                        <p>📍 {r.get('cidade')} ({dist}km de você) | <b>{r['area']}</b></p>
                        <p><i>"{r.get('descricao', '')}"</i></p>
                    </div>
                    """, unsafe_allow_html=True)
                    if r.get('saldo', 0) > 0:
                        if st.button(f"VER CONTATO DE {r['nome'].split()[0]}", key=f"v_{r['id']}"):
                            db.collection("profissionais").document(r['id']).update({"saldo": firestore.Increment(-1), "cliques": firestore.Increment(1)})
                            st.markdown(f'<a href="https://wa.me/55{r["whatsapp"]}" class="btn-wpp">CHAMAR NO WHATSAPP</a>', unsafe_allow_html=True)
                    else:
                        st.warning("Profissional ocupado no momento.")
        else:
            st.info("Nenhum profissional encontrado para esta busca.")

# --- ABA 2: PAINEL DO PROFISSIONAL ---
with UI_ABAS[1]:
    if 'auth' not in st.session_state: st.session_state.auth = False
    
    if not st.session_state.auth:
        c1, c2 = st.columns(2)
        login_z = c1.text_input("WhatsApp (Login)")
        login_p = c2.text_input("Senha", type="password")
        if st.button("ACESSAR MINHA CONTA"):
            doc = db.collection("profissionais").document(login_z).get()
            if doc.exists and doc.to_dict().get('senha') == login_p:
                st.session_state.auth = True
                st.session_state.user = login_z
                st.rerun()
            else: st.error("Acesso negado.")
    else:
        u = db.collection("profissionais").document(st.session_state.user).get().to_dict()
        st.subheader(f"Olá, {u['nome']}!")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Moedas", f"{u.get('saldo')} 🪙")
        m2.metric("Visualizações", u.get('cliques'))
        m3.metric("Status", "ATIVO" if u.get('aprovado') else "PENDENTE")
        
        st.divider()
        st.write("### 💰 Recarregar Créditos")
        st.info(f"Pague via PIX: **{PIX_OFICIAL}** e envie o comprovante.")
        st.markdown(f'<a href="https://wa.me/{ZAP_ADMIN}?text=Recarga de Moedas para {st.session_state.user}" class="btn-wpp">ENVIAR COMPROVANTE</a>', unsafe_allow_html=True)
        
        if st.button("SAIR"):
            st.session_state.auth = False
            st.rerun()

# --- ABA 3: CADASTRO ---
with UI_ABAS[2]:
    st.subheader("🚀 Cadastre-se e comece a receber serviços")
    with st.form("novo_cadastro"):
        c1, c2 = st.columns(2)
        fn = c1.text_input("Seu Nome")
        fz = c2.text_input("WhatsApp (Ex: 11999999999)")
        fs = st.text_input("Crie uma Senha", type="password")
        fa = st.selectbox("Sua Área Principal", LISTA_AREAS_DROP)
        fc = st.text_input("Sua Cidade")
        fu = st.selectbox("Estado", LISTA_ESTADOS)
        fd = st.text_area("Descrição dos seus serviços")
        
        if st.form_submit_button("CRIAR PERFIL PROFISSIONAL"):
            if fn and fz and fs:
                db.collection("profissionais").document(fz).set({
                    "nome": fn, "whatsapp": fz, "senha": fs, "area": fa,
                    "cidade": fc, "uf": fu, "descricao": fd, "saldo": BONUS_WELCOME,
                    "aprovado": False, "cliques": 0, "rating": 5.0,
                    "timestamp": datetime.datetime.now(),
                    "lat": LAT_SP_REF + random.uniform(-0.1, 0.1),
                    "lon": LON_SP_REF + random.uniform(-0.1, 0.1)
                })
                st.success("Cadastro realizado! Aguarde a aprovação do Admin.")
                st.balloons()
            else: st.warning("Preencha todos os campos!")

# --- ABA 4: ADMIN MASTER ---
with UI_ABAS[3]:
    chave = st.text_input("Chave Mestra", type="password")
    if chave == CHAVE_ACESSO_ADMIN:
        st.subheader("🛡️ Gestão Geral do Sistema")
        
        if st.button("🧹 EXECUTAR MANUTENÇÃO DE DADOS"):
            docs = db.collection("profissionais").stream()
            for d in docs:
                data = d.to_dict()
                if "saldo" not in data: db.collection("profissionais").document(d.id).update({"saldo": 5})
            st.success("Base de dados higienizada!")
            
        st.divider()
        busca_adm = st.text_input("Filtrar por nome no Admin").lower()
        profs = db.collection("profissionais").stream()
        
        for p_doc in profs:
            p = p_doc.to_dict()
            if not busca_adm or busca_adm in p['nome'].lower():
                with st.expander(f"{'✅' if p['aprovado'] else '⏳'} {p['nome']} | {p['area']}"):
                    st.write(f"WhatsApp: {p_doc.id}")
                    c1, c2, c3, c4 = st.columns(4)
                    if c1.button("APROVAR", key=f"ap_{p_doc.id}"):
                        db.collection("profissionais").document(p_doc.id).update({"aprovado": True}); st.rerun()
                    if c2.button("BLOQUEAR", key=f"bl_{p_doc.id}"):
                        db.collection("profissionais").document(p_doc.id).update({"aprovado": False}); st.rerun()
                    if c3.button("+10 MOEDAS", key=f"m1_{p_doc.id}"):
                        db.collection("profissionais").document(p_doc.id).update({"saldo": firestore.Increment(10)}); st.rerun()
                    if c4.button("EXCLUIR", key=f"ex_{p_doc.id}"):
                        db.collection("profissionais").document(p_doc.id).delete(); st.rerun()

st.markdown("<br><center><small>GeralJá Brasil © 2025 - Professional Service Platform</small></center>", unsafe_allow_html=True)


