# ============================================================================== 
# GERALJÁ SP - ULTIMATE EDITION v18.0 (PROFISSIONAL + EDITÁVEL + IA) 
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

# 1. CONFIGURAÇÃO DE ALTA PERFORMANCE 
st.set_page_config( 
    page_title="GeralJá | Profissionais de São Paulo", 
    page_icon="🛠️", 
    layout="centered", 
    initial_sidebar_state="collapsed" 
) 

# 2. CONEXÃO BLINDADA AO FIREBASE 
@st.cache_resource 
def init_infra(): 
    if not firebase_admin._apps: 
        try: 
            b64_key = st.secrets["FIREBASE_BASE64"] 
            decoded_json = base64.b64decode(b64_key.encode()).decode("utf-8") 
            cred = credentials.Certificate(json.loads(decoded_json)) 
            return firebase_admin.initialize_app(cred) 
        except Exception as e: 
            st.error(f"Erro Crítico de Banco de Dados: {e}") 
            st.stop() 
    return firebase_admin.get_app() 
init_infra() 
db = firestore.client() 

# 3. REGRAS DE NEGÓCIO E CONSTANTES 
PIX_OFICIAL = "11991853488" 
ZAP_ADMIN = "5511991853488" 
CHAVE_ADMIN = "mumias" 
TAXA_LEAD = 1 
BONUS_NOVO = 5 
LAT_SP = -23.5505 
LON_SP = -46.6333 

# 4. MOTOR DE INTELIGÊNCIA ARTIFICIAL (MAPEAMENTO) 
MAPA_IA = { 
    "vazamento": "Encanador", 
    "chuveiro": "Eletricista", 
    "pintura": "Pintor", 
    "faxina": "Diarista", 
    "mudança": "Fretes", 
    "unha": "Manicure", 
    "carro": "Mecânico", 
    "computador": "TI", 
    "reforma": "Pedreiro", 
    "gesso": "Gesseiro", 
    "telhado": "Telhadista", 
    "jardim": "Jardineiro", 
    "limpeza": "Diarista", 
    "esgoto": "Encanador", 
    "fiação": "Eletricista" 
} 

def classificar_ia(texto): 
    t = texto.lower() if texto else "" 
    for k, v in MAPA_IA.items(): 
        if k in t: 
            return v 
    return "Ajudante Geral" 

def calcular_km(lat1, lon1, lat2, lon2): 
    if None in [lat1, lon1, lat2, lon2]: 
        return 99.9 
    R = 6371 
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1) 
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2 
    return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1) 

# 5. ESTILIZAÇÃO PREMIUM 
st.markdown(""" 
<style> 
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap'); 
    * { font-family: 'Montserrat', sans-serif; } 
    .stApp { background-color: #F4F7F9; } 
    .main-logo { text-align: center; padding: 30px; background: #FFF; border-radius: 0 0 50px 50px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); } 
    .azul { color: #0047AB; font-weight: 900; font-size: 50px; } 
    .laranja { color: #FF8C00; font-weight: 900; font-size: 50px; } 
    .card-pro { background: white; border-radius: 20px; padding: 20px; margin-bottom: 15px; border-left: 10px solid #0047AB; box-shadow: 0 5px 15px rgba(0,0,0,0.05); display: flex; align-items: center; } 
    .img-perfil { width: 80px; height: 80px; border-radius: 50%; object-fit: cover; margin-right: 20px; border: 2px solid #0047AB; } 
    .btn-wpp { background: #25D366; color: white !important; padding: 12px; border-radius: 10px; text-decoration: none; font-weight: 700; display: block; text-align: center; } 
    .metric-card { background: #0047AB; color: white; padding: 15px; border-radius: 15px; text-align: center; } 
</style> 
""", unsafe_allow_html=True) 

st.markdown('<div class="main-logo"><span class="azul">GERAL</span><span class="laranja">JÁ</span><br><small>SÃO PAULO PROFISSIONAL</small></div>', unsafe_allow_html=True) 

# 6. NAVEGAÇÃO POR ABAS 
Abas = st.tabs(["🔍 BUSCAR", "👤 MEU PERFIL", "✍️ CADASTRAR", "🛡️ ADMIN"]) 

# ------------------------------------------------------------------------------ 
# ABA 1: CLIENTE (BUSCA GPS) 
# ------------------------------------------------------------------------------ 
with Abas[0]: 
    st.write("### 📍 Encontre um profissional perto de você") 
    busca = st.text_input("O que você precisa hoje?", placeholder="Ex: Preciso de um pintor para minha sala") 
    raio_km = st.slider("Distância máxima (km)", 1, 50, 15) 
    if busca: 
        cat = classificar_ia(busca) 
        st.info(f"Buscando por: **{cat}** em um raio de {raio_km}km") 
        # Query Otimizada 
        docs = db.collection("profissionais").where("area", "==", cat).where("aprovado", "==", True).stream() 
        resultados = [] 
        for d in docs: 
            p = d.to_dict() 
            p['id'] = d.id 
            dist = calcular_km(LAT_SP, LON_SP, p.get('lat', LAT_SP), p.get('lon', LON_SP)) 
            if dist <= raio_km: 
                p['dist'] = dist 
                resultados.append(p) 
        resultados.sort(key=lambda x: x['dist']) 
        if not resultados: 
            st.warning("Nenhum profissional encontrado tão próximo. Tente aumentar o raio de busca.") 
        else: 
            for pro in resultados: 
                with st.container(): 
                    st.markdown(f""" 
                    <div class="card-pro"> 
                        <img src="{pro.get('foto_url') or 'https://cdn-icons-png.flaticon.com/512/3135/3135715.png'}" class="img-perfil"> 
                        <div style="flex-grow:1;"> 
                            <b style="font-size:18px;">{pro['nome'].upper()}</b><br> 
                            <small>📍 {pro['dist']} km de você | ⭐ {pro.get('rating', 5.0)}</small><br> 
                            <span style="color:#666; font-size:13px;">{pro.get('localizacao', 'São Paulo')}</span> 
                        </div> 
                    </div> 
                    """, unsafe_allow_html=True) 
                    if pro.get('saldo', 0) >= TAXA_LEAD: 
                        if st.button(f"SOLICITAR ORÇAMENTO DE {pro['nome'].split()[0]}", key=f"btn_{pro['id']}"):
