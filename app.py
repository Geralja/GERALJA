# ============================================================================== 
# GERALJÁ SP - ENTERPRISE EDITION v19.0 
# O SISTEMA MAIS COMPLETO JÁ DESENVOLVIDO PARA GESTÃO DE SERVIÇOS 
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
import time
import pandas as pd
from io import BytesIO

# ------------------------------------------------------------------------------ 
# 1. ARQUITETURA DE SISTEMA (CONFIGURAÇÃO GLOBAL) 
# ------------------------------------------------------------------------------ 
st.set_page_config(
    page_title="GeralJá | Ecossistema Profissional SP",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ------------------------------------------------------------------------------ 
# 2. CONEXÃO E INFRAESTRUTURA DE DADOS (FIREBASE CORE) 
# ------------------------------------------------------------------------------ 
@st.cache_resource
def conectar_banco_master():
    if not firebase_admin._apps:
        try:
            b64_key = st.secrets["FIREBASE_BASE64"]
            decoded_json = base64.b64decode(b64_key).decode("utf-8")
            cred_dict = json.loads(decoded_json)
            cred = credentials.Certificate(cred_dict)
            return firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"❌ ERRO CRÍTICO NA CONEXÃO: {e}")
            st.stop()
    return firebase_admin.get_app()

app_engine = conectar_banco_master()
db = firestore.client()

# ------------------------------------------------------------------------------ 
# 3. CONSTANTES E PARÂMETROS DE GOVERNANÇA 
# ------------------------------------------------------------------------------ 
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ADMIN = "mumias"
VALOR_MOEDA_REAL = 1.00
TAXA_CONTATO = 1
BONUS_WELCOME = 5
LAT_REF_SP = -23.5505
LON_REF_SP = -46.6333
CATEGORIAS_OFICIAIS = [
    "Encanador", "Eletricista", "Pintor", "Pedreiro", "Gesseiro", 
    "Telhadista", "Mecânico", "Borracheiro", "Guincho 24h", "Diarista", 
    "Jardineiro", "Piscineiro", "TI", "Refrigeração", "Ajudante Geral"
]

# ------------------------------------------------------------------------------ 
# 4. MOTOR DE INTELIGÊNCIA ARTIFICIAL (MAPEAMENTO SEMÂNTICO) 
# ------------------------------------------------------------------------------ 
CONCEITOS_EXPANDIDOS = {
    # HIDRÁULICA
    "vazamento": "Encanador", "cano": "Encanador", "torneira": "Encanador",
    # ELÉTRICA
    "curto": "Eletricista", "luz": "Eletricista", "tomada": "Eletricista",
    # ... (restante do dicionário)
}

def processar_ia_avancada(texto):
    if not texto: return "Ajudante Geral"
    t_clean = texto.lower().strip()
    for chave, categoria in CONCEITOS_EXPANDIDOS.items():
        if re.search(rf"\b{chave}\b", t_clean): return categoria
    return "Ajudante Geral"

def calcular_distancia_real(lat1, lon1, lat2, lon2):
    if None in [lat1, lon1, lat2, lon2]: return 999.0
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return round(R * c, 1)

# ------------------------------------------------------------------------------ 
# 5. DESIGN SYSTEM (INTERFACE PREMIUM SÃO PAULO) 
# ------------------------------------------------------------------------------ 
st.markdown(r"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F8FAFC; }
    /* Header Estilizado */
    .header-container { background: white; padding: 40px; border-radius: 0 0 60px 60px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.05); border-bottom: 8px solid #FF8C00; }
    .logo-azul { color: #0047AB; font-weight: 900; font-size: 60px; letter-spacing: -2px; }
    .logo-laranja { color: #FF8C00; font-weight: 900; font-size: 60px; letter-spacing: -2px; }
    /* Cards de Profissionais */
    .pro-card { background: white; border-radius: 30px; padding: 25px; margin-bottom: 20px; border-left: 15px solid #0047AB; box-shadow: 0 10px 20px rgba(0,0,0,0.03); display: flex; align-items: center; transition: 0.3s; }
    .pro-card:hover { transform: translateY(-5px); box-shadow: 0 15px 35px rgba(0,0,0,0.08); }
    .pro-img { width: 100px; height: 100px; border-radius: 50%; object-fit: cover; border: 4px solid #F1F5F9; margin-right: 25px; }
    /* Badges e Botões */
    .badge-dist { background: #DBEAFE; color: #1E40AF; padding: 6px 14px; border-radius: 12px; font-weight: 900; font-size: 11px; text-transform: uppercase; }
    .badge-area { background: #FFEDD5; color: #9A3412; padding: 6px 14px; border-radius: 12px; font-weight: 900; font-size: 11px; text-transform: uppercase; margin-left: 5px; }
    .btn-zap { background: #22C55E; color: white !important; padding: 16px; border-radius: 18px; text-decoration: none; font-weight: 900; display: block; text-align: center; font-size: 16px; margin-top: 10px; }
    /* Painel de Métricas */
    .metric-box { background: #1E293B; color: white; padding: 25px; border-radius: 25px; text-align: center; border-bottom: 5px solid #FF8C00; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------ 
# 6. NÚCLEO DE NAVEGAÇÃO (ESTRUTURA DE 4 NÍVEIS) 
# ------------------------------------------------------------------------------ 
st.markdown('<div class="header-container"><span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span><br><small style="letter-spacing:8px; color:#64748B;">SÃO PAULO ELITE</small></div>', unsafe_allow_html=True)
menu_abas = st.tabs(["🔍 ENCONTRAR ESPECIALISTA", "💼 CENTRAL DO PROFISSIONAL", "📝 NOVO CADASTRO", "🛡️ TERMINAL ADMIN"])

# ... (restante do código)
















