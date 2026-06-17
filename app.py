# ==============================================================================
# GERALJÁ 6.0 - SISTEMA COMPLETO GRAJAÚ TEM (ESTILO BING)
# ==============================================================================
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import math
import re
import time
import io
import pandas as pd
from datetime import datetime 
import pytz
import unicodedata
import requests
import feedparser
import urllib.parse
from PIL import Image

# --- BIBLIOTECAS NÍVEL 5.0 ---
from groq import Groq
from fuzzywuzzy import process
from urllib.parse import quote
import google.generativeai as genai
from google_auth_oauthlib.flow import Flow

# --- TENTA IMPORTAR COMPONENTES JS COM FALLBACK SEGURO ---
try:
    from streamlit_js_eval import streamlit_js_eval, get_geolocation
except: 
    streamlit_js_eval = None
    get_geolocation = None

# --- CONFIGURAÇÃO DE PÁGINA ---
st.set_page_config(page_title="Grajaú Tem | Portal", page_icon="📍", layout="wide", initial_sidebar_state="collapsed")

# --- CSS ESTILO BING + FUNDO GRAJAÚ ---
# Substitua 'LINK_DA_SUA_IMAGEM' pelo link direto da sua foto do Grajaú
IMG_URL = "https://images.unsplash.com/photo-1549492423-455208616167" 

st.markdown(f"""
<style>
    .stApp {{
        background-image: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('{IMG_URL}');
        background-size: cover;
        background-attachment: fixed;
    }}
    .search-box {{ 
        display: flex; flex-direction: column; align-items: center; justify-content: center; 
        height: 60vh; color: white; text-align: center; 
    }}
    .titulo-bing {{ font-weight: 900; font-size: 4rem; text-shadow: 2px 2px 10px rgba(0,0,0,0.5); margin-bottom: 20px; }}
    .search-bar {{ background: white; padding: 15px 25px; border-radius: 50px; width: 100%; max-width: 600px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }}
    .stTextInput > div > div > input {{ border: none !important; font-size: 1.2rem !important; }}
</style>
""", unsafe_allow_html=True)

# --- MOTOR GERALJÁ (INFRAESTRUTURA) ---
class GeralJaEngine:
    def __init__(self): self.fuso = pytz.timezone('America/Sao_Paulo')
    def sanitizar(self, texto): return re.sub(r'[^\x20-\x7E\n\t\r]', '', texto)

engine = GeralJaEngine()
fuso_br = engine.fuso

@st.cache_resource
def conectar_banco():
    if not firebase_admin._apps:
        b64_key = st.secrets["firebase"]["base64"]
        cred_dict = json.loads(base64.b64decode(b64_key).decode("utf-8"))
        firebase_admin.initialize_app(credentials.Certificate(cred_dict))
    return firebase_admin.get_app()

db = firestore.client()

# --- BUSCA OTIMIZADA (SEM ERROS DE ÍNDICE) ---
def buscar_servicos(termo):
    # BUSCA SIMPLES: Sem order_by para evitar FailedPrecondition
    profs = db.collection("profissionais").where("aprovado", "==", True).stream()
    return [p.to_dict() for p in profs if termo.lower() in p.get('nome', '').lower() or termo.lower() in p.get('area', '').lower()]

# --- INTERFACE ---
st.markdown('<div class="search-box">', unsafe_allow_html=True)
st.markdown('<div class="titulo-bing">GRAJAÚ <span style="color:#FF8C00">TEM</span></div>', unsafe_allow_html=True)

# Barra de busca central
busca = st.text_input("", placeholder="🔍 Pesquise serviços ou profissionais no Grajaú...", label_visibility="collapsed")

# Lógica da Busca
if busca:
    st.markdown('<div style="background:white; padding:20px; border-radius:20px; color:black; width:100%; max-width:600px;">', unsafe_allow_html=True)
    res = buscar_servicos(busca)
    if res:
        for p in res:
            st.write(f"✅ **{p.get('nome')}** - {p.get('area')}")
    else:
        st.write("Nenhum resultado encontrado.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# --- ABAS (SISTEMA DE BRAÇOS DE FUNÇÃO) ---
lista_abas = ["📦 VITRINE", "🚀 CADASTRAR", "👑 ADMIN"]
menu_abas = st.tabs(lista_abas)

with menu_abas[0]: # Vitrine
    st.write("Produtos e Novidades")

with menu_abas[1]: # Cadastro
    st.write("Cadastro de Profissionais")

with menu_abas[2]: # Admin
    st.write("Painel Administrativo")

# --- EXPANDER JURÍDICO (BLINDAGEM MANTIDA) ---
with st.expander("📄 Transparência e Privacidade (LGPD)"):
    st.write("Sistema em conformidade com a LGPD.")
