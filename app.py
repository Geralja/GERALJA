# ==============================================================================
# GERALJÁ: SISTEMA INTEGRAL - VERSÃO BLINDADA E ORGANIZADA
# ==============================================================================
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64, json, math, re, time, pandas as pd
from datetime import datetime
import pytz, unicodedata, requests, sys, os, importlib, io
import feedparser, urllib.parse
from PIL import Image
from groq import Groq
from fuzzywuzzy import process
from urllib.parse import quote
import google.generativeai as genai
from google_auth_oauthlib.flow import Flow

# Tenta importar JS para Geolocation
try:
    from streamlit_js_eval import streamlit_js_eval, get_geolocation
except ImportError:
    streamlit_js_eval = None
    get_geolocation = None

# --- CONSTANTES E VARIÁVEIS GLOBAIS ---
REDIRECT_URI = "https://geralja-zxiaj2ot56fuzgcz7xhcks.streamlit.app/"
IMG_PADRAO = "https://images.unsplash.com/photo-1504711432869-0df30d7eaf4d?w=500&q=80"
CATEGORIAS_OFICIAIS = ["Encanador", "Eletricista", "Pintor", "Pedreiro", "Gesseiro", "Diarista", "Outro"]

# --- INFRAESTRUTURA E CONEXÕES ---
class GeralJaEngine:
    def sanitizar(self, texto):
        return re.sub(r'[^\x20-\x7E\n\t\r]', '', str(texto))

engine = GeralJaEngine()

@st.cache_resource
def conectar_banco():
    if not firebase_admin._apps:
        b64_key = st.secrets["firebase"]["base64"]
        cred = credentials.Certificate(json.loads(base64.b64decode(b64_key).decode("utf-8")))
        return firebase_admin.initialize_app(cred)
    return firebase_admin.get_app()

db = firestore.client()
conectar_banco()

# --- FUNÇÕES UTILITÁRIAS (FORA DE QUALQUER BLOCO) ---
def calcular_distancia_real(lat1, lon1, lat2, lon2):
    try:
        R = 6371
        dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)
    except: return 999.0

# --- CARREGAMENTO DE PLUGINS (DINÂMICO) ---
def carregar_plugins():
    pasta_plugins = os.path.join(os.getcwd(), "modulos")
    if not os.path.exists(pasta_plugins): return
    
    arquivos = sorted([f for f in os.listdir(pasta_plugins) if f.endswith(".py") and f != "__init__.py"])
    for arquivo in arquivos:
        try:
            spec = importlib.util.spec_from_file_location(arquivo[:-3], os.path.join(pasta_plugins, arquivo))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "run"): mod.run()
        except Exception as e:
            st.error(f"Erro no plugin {arquivo}: {e}")

# --- INTERFACE (UI) ---
st.set_page_config(page_title="GeralJá", layout="wide")
st.markdown("<div class='header-container'><h1>GERALJÁ</h1></div>", unsafe_allow_html=True)

menu_abas = st.tabs(["🔍 BUSCAR", "🚀 CADASTRAR", "👤 MEU PERFIL", "👑 ADMIN", "⭐ FEEDBACK"])

# --- ROTAS DAS ABAS ---
with menu_abas[0]: # BUSCAR
    st.markdown("### 🏙️ O que você precisa?")
    termo = st.text_input("Ex: 'Eletricista'")
    if termo: st.write(f"Buscando: {termo}...")

with menu_abas[1]: # CADASTRAR
    st.markdown("### 🚀 Cadastro")
    with st.form("form_cad"):
        nome = st.text_input("Nome")
        if st.form_submit_button("CADASTRAR"): st.success("Enviado!")

with menu_abas[2]: # PERFIL
    st.markdown("### 👤 Painel")
    if 'auth' not in st.session_state: st.session_state.auth = False

with menu_abas[3]: # ADMIN
    st.markdown("### 👑 Admin")

with menu_abas[4]: # FEEDBACK
    st.markdown("### ⭐ Avalie")

# --- CARREGA PLUGINS NO FINAL ---
carregar_plugins()

# --- RODAPÉ ---
st.markdown("<div style='text-align:center;'>© 2026 GeralJá</div>", unsafe_allow_html=True)
