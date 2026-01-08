import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import math
import unicodedata
from datetime import datetime
import pytz
from streamlit_js_eval import streamlit_js_eval, get_geolocation

# ==============================================================================
# 1. CONFIGURAÇÃO E CSS (VISUAL LIMPO E PROFISSIONAL)
# ==============================================================================
st.set_page_config(page_title="GeralJá", page_icon="🎯", layout="centered")

st.markdown("""
    <style>
        /* Esconde elementos de administração do Streamlit */
        header[data-testid="stHeader"] { visibility: hidden; height: 0px; }
        footer { visibility: hidden; }
        #MainMenu { visibility: hidden; }
        .stDeployButton { display:none; }
        
        /* Ajuste do container principal */
        .block-container { padding-top: 1rem !important; }
        
        /* Estilo dos Cards de Profissionais */
        .prof-card {
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            border-left: 6px solid #1E3A8A;
            margin-bottom: 20px;
        }
        .btn-wpp {
            background-color: #25D366;
            color: white !important;
            padding: 10px 20px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: bold;
            display: block;
            text-align: center;
            margin-top: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. FUNÇÕES ESSENCIAIS
# ==============================================================================
def remover_acentos(texto):
    if not texto: return ""
    return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').lower()

def calcular_distancia(lat1, lon1, lat2, lon2):
    R = 6371 
    dLat, dLon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dLat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2) ** 2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

# ==============================================================================
# 3. CONEXÃO FIREBASE
# ==============================================================================
@st.cache_resource
def conectar_banco():
    if not firebase_admin._apps:
        try:
            b64_key = st.secrets["FIREBASE_BASE64"]
            decoded_json = base64.b64decode(b64_key).decode("utf-8")
            cred = credentials.Certificate(json.loads(decoded_json))
            return firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error("Erro na conexão com o banco.")
            st.stop()
    return firebase_admin.get_app()

db = firestore.client() if conectar_banco() else None

# ==============================================================================
# 4. LOCALIZAÇÃO E ABAS
# ==============================================================================
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🎯 GeralJá</h1>", unsafe_allow_html=True)

loc = get_geolocation()
lat_usuario = loc['coords']['latitude'] if loc else -23.5505
lon_usuario = loc['coords']['longitude'] if loc else -46.6333

titulos = ["🔍 BUSCAR", "🚀 CADASTRAR", "👤 PERFIL", "👑 ADMIN"]
with st.sidebar:
    st.title("Menu GeralJá")
    senha_fin = st.text_input("Comando Secreto", type="password")
    if senha_fin == "abracadabra":
        titulos.append("📊 FINANCEIRO")

abas = st.tabs(titulos)

# --- ABA BUSCAR ---
with abas[0]:
    st.write("### O que você precisa hoje?")
    col1, col2, col3, col4 = st.columns(4)
    atalho = ""
    if col1.button("📱 Celular"): atalho = "Técnico de Celular"
    if col2.button("🔧 Reparos"): atalho = "Marido de Aluguel"
    if col3.button("🏠 Obra"): atalho = "Pedreiro"
    if col4.button("🍔 Fome"): atalho = "Lanchonete"
    
    busca = st.text_input("", value=atalho, placeholder="Ex: encanador, pizza, mecânico...")
    
    if busca:
        st.info(f"Buscando profissionais para: {busca}")
        # Aqui o seu código de busca no Firestore continua...

# --- ABA CADASTRAR ---
with abas[1]:
    st.write("### 🚀 Cadastre seu serviço")
    with st.form("cadastro_prof"):
        nome = st.text_input("Seu Nome ou Empresa")
        whats = st.text_input("WhatsApp (com DDD)")
        bio = st.text_area("Descrição do serviço")
        if st.form_submit_button("CRIAR PERFIL"):
            st.success("Cadastro enviado para aprovação!")

# --- DEMAIS ABAS ---
with abas[2]: st.write("### 👤 Meu Perfil")
with abas[3]: 
    if st.text_input("Senha Admin", type="password") == "mumias":
        st.write("Painel de Controle Ativo")

if "📊 FINANCEIRO" in titulos:
    with abas[4]: st.write("### 📊 Gestão Financeira")
