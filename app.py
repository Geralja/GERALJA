# ==============================================================================
# GERALJÁ 6.0 (ENGINE) + GRAJAÚ TEM (PORTAL) - SISTEMA INTEGRADO
# ==============================================================================
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64, json, math, re, time, io, pandas as pd
from datetime import datetime
import pytz, unicodedata, requests, feedparser, urllib.parse
from PIL import Image
from groq import Groq
from fuzzywuzzy import process
from google_auth_oauthlib.flow import Flow

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Grajaú Tem | Portal Oficial", page_icon="📍", layout="wide")

# --- CSS ESTILO GOOGLE SEARCH ---
st.markdown("""
<style>
    .google-bar { text-align: center; margin-top: 20px; margin-bottom: 40px; }
    .stTextInput > div > div > input { border-radius: 25px !important; padding: 20px !important; border: 1px solid #dfe1e5 !important; box-shadow: 0 1px 6px rgba(0,0,0,0.1); }
    .header-logo { font-weight: 900; font-size: 3rem; color: #0047AB; text-align: center; margin-top: 20px; }
    .header-logo span { color: #FF8C00; }
</style>
""", unsafe_allow_html=True)

# --- MOTOR GERALJÁ (INFRAESTRUTURA MANTIDA) ---
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

app_engine = conectar_banco_master()
db = firestore.client()

# --- INTERFACE PORTAL ---
st.markdown('<div class="header-logo">GRAJAÚ <span>TEM</span></div>', unsafe_allow_html=True)

# ABA BUSCA (COM ESTILO GOOGLE)
col1, col2, col3 = st.columns([1, 6, 1])
with col2:
    termo_busca = st.text_input("", placeholder="🔍 Pesquise serviços ou profissionais...", label_visibility="collapsed")

# --- LÓGICA DE BUSCA DO MOTOR GERALJÁ ---
if termo_busca:
    with st.spinner("Buscando no Grajaú..."):
        # Notícias (ERRO CORRIGIDO: Removido order_by para não exigir índice composto)
        noticias_locais = db.collection("noticias_locais").where("ativo", "==", True).limit(3).stream()
        for n in noticias_locais:
            d = n.to_dict()
            st.info(f"🚨 **{d.get('titulo', 'Notícia')}**: {d.get('texto', '')[:100]}...")
            
        # Busca Profissionais
        profs = db.collection("profissionais").where("aprovado", "==", True).stream()
        for p_doc in profs:
            p = p_doc.to_dict()
            if termo_busca.lower() in p.get('area', '').lower() or termo_busca.lower() in p.get('nome', '').lower():
                st.write(f"✅ **{p.get('nome')}** — {p.get('area')}")

# --- CADASTRO E ADMIN (ABAS) ---
tab_cad, tab_admin = st.tabs(["🚀 CADASTRAR", "👑 ADMIN"])

with tab_cad:
    st.header("Cadastre seu Negócio")
    # Aqui entra o formulário original que você já tinha

with tab_admin:
    st.header("Gestão de Notícias")
    with st.form("pub_noticia"):
        titulo = st.text_input("Título")
        texto = st.text_area("Resumo")
        if st.form_submit_button("Publicar"):
            db.collection("noticias_locais").add({"titulo": titulo, "texto": texto, "ativo": True, "data_criacao": datetime.now(fuso_br)})
            st.success("Publicado!")

# --- RODAPÉ (BLINDAGEM MANTIDA) ---
st.markdown("---")
st.caption("GeralJá v6.0 | Sistema Integrado")
