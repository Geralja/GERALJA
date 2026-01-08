import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import math
import re
import pytz
import unicodedata
from datetime import datetime
from urllib.parse import quote
from streamlit_js_eval import streamlit_js_eval, get_geolocation

# 1. CONFIGURAÇÃO DA PÁGINA (ÚNICA CHAMADA)
st.set_page_config(
    page_title="GeralJá | Criando Soluções",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. CONSTANTES E POLÍTICAS
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ADMIN = "mumias"
LAT_REF, LON_REF = -23.5505, -46.6333

CATEGORIAS_OFICIAIS = sorted([
    "Academia", "Ajudante Geral", "Assistência Técnica", "Barbearia/Salão", 
    "Chaveiro", "Diarista / Faxineira", "Eletricista", "Encanador", 
    "Estética Automotiva", "Freteiro", "Mecânico de Autos", "Montador de Móveis",
    "Padaria", "Pet Shop", "Pintor", "Pizzaria", "TI (Tecnologia)", "Web Designer"
    # ... adicione as demais aqui se necessário
])

CONCEITOS_IA = {
    "pizza": "Pizzaria", "pizzaria": "Pizzaria", "fome": "Pizzaria",
    "lanche": "Lanchonete", "hamburguer": "Lanchonete",
    "vazamento": "Encanador", "cano": "Encanador",
    "curto": "Eletricista", "luz": "Eletricista",
    "carro": "Mecânico de Autos", "oficina": "Mecânico de Autos",
    "celular": "Assistência Técnica", "iphone": "Assistência Técnica",
    "faxina": "Diarista / Faxineira", "limpeza": "Diarista / Faxineira"
}

# 3. FUNÇÕES DE SUPORTE (BACKEND)
@st.cache_resource
def conectar_banco():
    if not firebase_admin._apps:
        try:
            b64_key = st.secrets["FIREBASE_BASE64"]
            cred_dict = json.loads(base64.b64decode(b64_key).decode("utf-8"))
            cred = credentials.Certificate(cred_dict)
            return firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Erro de Conexão: {e}")
            st.stop()
    return firebase_admin.get_app()

db = firestore.client() if conectar_banco() else None

def normalizar(t):
    return "".join(c for c in unicodedata.normalize('NFD', str(t)) if unicodedata.category(c) != 'Mn').lower().strip()

def identificar_categoria(texto):
    t_clean = normalizar(texto)
    for chave, cat in CONCEITOS_IA.items():
        if re.search(rf"\b{normalizar(chave)}\b", t_clean): return cat
    for cat in CATEGORIAS_OFICIAIS:
        if normalizar(cat) in t_clean: return cat
    return "OUTROS"

def calc_distancia(lat1, lon1, lat2, lon2):
    try:
        R = 6371
        dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)
    except: return 999.0

# 4. DESIGN SYSTEM (CSS CONSOLIDADO)
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    * {{ font-family: 'Inter', sans-serif; }}
    .stApp {{ background-color: white; }}
    .header-container {{ background: white; padding: 30px; text-align: center; border-bottom: 5px solid #FF8C00; margin-bottom: 20px; }}
    .logo-azul {{ color: #0047AB; font-weight: 900; font-size: 40px; }}
    .logo-laranja {{ color: #FF8C00; font-weight: 900; font-size: 40px; }}
    .card-pro {{ border-radius: 15px; padding: 15px; border: 1px solid #eee; margin-bottom: 10px; background: #fefefe; }}
    #MainMenu, footer, header {{ visibility: hidden; display: none !important; }}
</style>
""", unsafe_allow_html=True)

# 5. INTERFACE PRINCIPAL
st.markdown('<div class="header-container"><span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span></div>', unsafe_allow_html=True)

abas = ["🔍 BUSCAR", "🚀 CADASTRAR", "👤 PAINEL", "👑 ADMIN"]
comando = st.sidebar.text_input("Acesso Restrito", type="password")
if comando == "abracadabra": abas.append("📊 FINANCEIRO")

menu = st.tabs(abas)

# --- ABA BUSCA ---
with menu[0]:
    col_s1, col_s2 = st.columns([3, 1])
    busca = col_s1.text_input("O que você precisa hoje?", placeholder="Ex: encanador, pizza, mecânico...")
    raio = col_s2.slider("Raio (km)", 1, 100, 10)

    if busca:
        cat_alvo = identificar_categoria(busca)
        st.info(f"Buscando por: **{cat_alvo}**")
        
        # Localização do Usuário
        loc = get_geolocation()
        u_lat = loc['coords']['latitude'] if loc else LAT_REF
        u_lon = loc['coords']['longitude'] if loc else LON_REF

        # Query Firebase
        query = db.collection("profissionais").where("area", "==", cat_alvo).where("aprovado", "==", True).stream()
        
        resultados = []
        for doc in query:
            p = doc.to_dict()
            p['id'] = doc.id
            dist = calc_distancia(u_lat, u_lon, p.get('lat', LAT_REF), p.get('lon', LON_REF))
            if dist <= raio:
                p['dist'] = dist
                # Cálculo de Ranking
                p['rank'] = (p.get('saldo', 0) * 10) + (500 if p.get('verificado') else 0)
                resultados.append(p)

        resultados.sort(key=lambda x: (-x['rank'], x['dist']))

        if not resultados:
            st.warning("Nenhum profissional encontrado nesta região.")
            st.link_button("📢 Convidar profissionais no WhatsApp", f"https://wa.me/?text=Vi que faltam profissionais de {cat_alvo} no GeralJá! Cadastre-se.")
        else:
            for p in resultados:
                with st.container():
                    st.markdown(f"""<div class="card-pro">
                        <b>{p.get('nome').upper()}</b> {'✅' if p.get('verificado') else ''} <br>
                        <small>📍 {p['dist']} km de você</small><br>
                        <p>{p.get('descricao')[:100]}...</p>
                    </div>""", unsafe_allow_html=True)
                    
                    # Botão Zap Direto
                    msg_zap = quote(f"Olá {p.get('nome')}, vi seu perfil no GeralJá!")
                    link_zap = f"https://wa.me/{re.sub(r'D', '', p['id'])}?text={msg_zap}"
                    st.link_button(f"💬 FALAR COM {p.get('nome').split()[0]}", link_zap, use_container_width=True)

# --- ABA PAINEL DO PARCEIRO ---
with menu[2]:
    if 'logado' not in st.session_state: st.session_state.logado = False

    if not st.session_state.logado:
        with st.form("Login"):
            u_user = st.text_input("WhatsApp")
            u_pass = st.text_input("Senha", type="password")
            if st.form_submit_button("Acessar Painel"):
                user_doc = db.collection("profissionais").document(u_user).get()
                if user_doc.exists and user_doc.to_dict().get('senha') == u_pass:
                    st.session_state.logado = True
                    st.session_state.u_id = u_user
                    st.rerun()
                else: st.error("Acesso negado.")
    else:
        # Dashboard do Profissional
        p_data = db.collection("profissionais").document(st.session_state.u_id).get().to_dict()
        st.subheader(f"Bem-vindo, {p_data.get('nome')}!")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Moedas", p_data.get('saldo', 0))
        c2.metric("Cliques", p_data.get('cliques', 0))
        c3.metric("Status", "Ativo" if p_data.get('aprovado') else "Pendente")

        if st.button("📍 Atualizar meu GPS agora"):
            nova_loc = get_geolocation()
            if nova_loc:
                db.collection("profissionais").document(st.session_state.u_id).update({
                    "lat": nova_loc['coords']['latitude'],
                    "lon": nova_loc['coords']['longitude']
                })
                st.success("Localização atualizada!")
