# ==============================================================================
# GERALJÁ 6.0 - SISTEMA INTEGRADO GRAJAÚ TEM (ESTILO BING)
# ==============================================================================
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64, json, math, re, time, io, pandas as pd, pytz, unicodedata, requests, feedparser, urllib.parse
from datetime import datetime
from PIL import Image
from groq import Groq
from fuzzywuzzy import process
from google_auth_oauthlib.flow import Flow

# --- CONFIGURAÇÃO INICIAL (Obrigatório primeiro) ---
st.set_page_config(page_title="Grajaú Tem | Portal Oficial", page_icon="📍", layout="wide", initial_sidebar_state="collapsed")

# --- CSS: ESTILO BING + FUNDO GRAJAÚ ---
# Se a imagem estiver no repositório, use o caminho local. Se for link, use a URL.
IMG_FUNDO = "https://images.unsplash.com/photo-1549492423-455208616167" # Substitua pelo link da sua foto

st.markdown(f"""
<style>
    .stApp {{
        background-image: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('{IMG_FUNDO}');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .search-container {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-top: 10vh;
        color: white;
    }}
    .logo-main {{ font-weight: 900; font-size: 4rem; text-shadow: 2px 2px 10px rgba(0,0,0,0.5); margin-bottom: 20px; }}
    .search-bar-box {{ width: 100%; max-width: 600px; background: white; padding: 10px 20px; border-radius: 50px; display: flex; align-items: center; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }}
    .stTextInput > div > div > input {{ border: none !important; background: transparent !important; font-size: 1.2rem !important; }}
</style>
""", unsafe_allow_html=True)

# --- MANTENDO SEU MOTOR ORIGINAL (FIREBASE, ENGINE, UTILS) ---
class GeralJaEngine:
    def __init__(self): self.fuso = pytz.timezone('America/Sao_Paulo')
    def sanitizar(self, texto): return re.sub(r'[^\x20-\x7E\n\t\r]', '', texto)

engine = GeralJaEngine()
fuso_br = engine.fuso

@st.cache_resource
def conectar_banco_master():
    if not firebase_admin._apps:
        b64_key = st.secrets["firebase"]["base64"]
        cred_dict = json.loads(base64.b64decode(b64_key).decode("utf-8"))
        firebase_admin.initialize_app(credentials.Certificate(cred_dict))
    return firebase_admin.get_app()

db = firestore.client()

# --- FUNÇÕES DE BUSCA (SEM ERRO DE ÍNDICE) ---
def buscar_profissionais(termo):
    # BUSCA OTIMIZADA: SEM order_by PARA EVITAR ERRO NO FIRESTORE
    profs = db.collection("profissionais").where("aprovado", "==", True).stream()
    resultados = []
    for doc in profs:
        p = doc.to_dict()
        if termo.lower() in p.get('area', '').lower() or termo.lower() in p.get('nome', '').lower():
            p['id'] = doc.id
            resultados.append(p)
    return resultados

# --- HOME "BING" ---
st.markdown('<div class="search-container">', unsafe_allow_html=True)
st.markdown('<div class="logo-main">GRAJAÚ <span style="color:#FF8C00">TEM</span></div>', unsafe_allow_html=True)

col_search = st.columns([1, 4, 1])[1]
with col_search:
    termo = st.text_input("", placeholder="🔍 O que você procura no Grajaú?", key="busca_home")

st.markdown('</div>', unsafe_allow_html=True)

# --- RESULTADOS DA BUSCA (SE HOUVER TERMO) ---
if termo:
    st.markdown('<div style="background: white; padding: 20px; border-radius: 20px; margin: 20px;">', unsafe_allow_html=True)
    res = buscar_profissionais(termo)
    if res:
        for p in res:
            st.markdown(f"### {p.get('nome')}")
            st.write(p.get('area'))
    else:
        st.warning("Nenhum profissional encontrado.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- SEU CÓDIGO ORIGINAL (ABAS E DEMAIS FUNÇÕES) ---
# Cole aqui abaixo a partir das suas abas (menu_abas = st.tabs(...))
# e o restante da estrutura original do seu arquivo app.py.
# ==============================================================================
# MÓDULO DE INTERFACE "HOME GRAJAÚ TEM" (ESTILO BING)
# ==============================================================================

# --- CSS DE FUNDO E BUSCA (ESTILO BING) ---
st.markdown(f"""
<style>
    .stApp {{
        background-image: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('https://images.unsplash.com/photo-1549492423-455208616167');
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    .search-container {{ display: flex; flex-direction: column; align-items: center; justify-content: center; margin-top: 15vh; color: white; }}
    .logo-main {{ font-weight: 900; font-size: 4rem; text-shadow: 2px 2px 15px rgba(0,0,0,0.5); margin-bottom: 20px; }}
    .search-box {{ width: 100%; max-width: 650px; background: white; padding: 15px 25px; border-radius: 50px; display: flex; align-items: center; box-shadow: 0 8px 20px rgba(0,0,0,0.3); }}
    .search-input {{ border: none !important; background: transparent !important; font-size: 1.3rem !important; color: #333 !important; }}
</style>
""", unsafe_allow_html=True)

# --- CABEÇALHO E BUSCA ---
st.markdown('<div class="search-container">', unsafe_allow_html=True)
st.markdown('<div class="logo-main">GRAJAÚ <span style="color:#FF8C00">TEM</span></div>', unsafe_allow_html=True)

col_mid = st.columns([1, 8, 1])[1]
with col_mid:
    # A BUSCA DINÂMICA
    termo = st.text_input("", placeholder="🔍 O que você procura no Grajaú hoje?", label_visibility="collapsed", key="input_busca_bing")

st.markdown('</div>', unsafe_allow_html=True)

# --- LÓGICA DE BUSCA HÍBRIDA (VITRINE + GOOGLE) ---
if termo:
    st.markdown('<div style="background: rgba(255,255,255,0.95); padding: 30px; border-radius: 20px; margin-top: 50px; color: #333;">', unsafe_allow_html=True)
    
    # 1. BUSCA NA SUA VITRINE (SEM ORDER_BY PARA NÃO TRAVAR)
    # Aqui usamos o seu motor de busca, mas sem o order_by que causava o erro.
    st.subheader("🛍️ Vitrine do Grajaú")
    resultados = db.collection("profissionais").where("aprovado", "==", True).stream()
    
    achou = False
    for p_doc in resultados:
        p = p_doc.to_dict()
        if termo.lower() in p.get('area', '').lower() or termo.lower() in p.get('nome', '').lower():
            st.success(f"✅ **{p.get('nome')}** — {p.get('area')}")
            st.write(p.get('descricao', ''))
            st.link_button("💬 Chamar no Zap", criar_link_zap(limpar_whatsapp(p.get('whatsapp','')), "Vi seu perfil no Grajaú Tem"))
            achou = True
    
    if not achou:
        st.warning("Nenhum profissional encontrado na vitrine. Buscando notícias locais...")
        
        # 2. BUSCA NO GOOGLE (RSS) SE NÃO ACHAR NA VITRINE
        st.subheader("📰 Notícias Recentes")
        try:
            url_rss = f"https://news.google.com/rss/search?q={urllib.parse.quote(termo + ' Grajaú')}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
            feed = feedparser.parse(url_rss)
            for n in feed.entries[:3]:
                st.markdown(f"[{n.title}]({n.link})")
        except:
            st.error("Sem notícias disponíveis agora.")

    st.markdown('</div>', unsafe_allow_html=True)

# --- RESTANTE DO CÓDIGO ---
# Aqui você mantém o código das suas abas (menu_abas = st.tabs(...)) 
# para que os outros módulos continuem funcionando.
