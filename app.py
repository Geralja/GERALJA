import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime
import math
import pandas as pd
import unicodedata
from urllib.parse import quote

# 1. CONFIGURAÇÃO DE AMBIENTE (Baseado no seu app.py original)
st.set_page_config(page_title="GeralJá | Pesquisa Inteligente", page_icon="🎯", layout="wide", initial_sidebar_state="collapsed")

# 2. CONEXÃO FIREBASE (Soma dos seus arquivos - Camada de Persistência)
@st.cache_resource
def conectar_banco_master():
    if not firebase_admin._apps:
        try:
            b64_key = st.secrets["FIREBASE_BASE64"]
            # Limpeza de padding para evitar erro de base64
            missing_padding = len(b64_key) % 4
            if missing_padding: b64_key += '=' * (4 - missing_padding)
            
            decoded_json = base64.b64decode(b64_key).decode("utf-8")
            cred_dict = json.loads(decoded_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            return firestore.client()
        except Exception as e:
            st.error(f"Erro na conexão com o Banco: {e}")
            return None
    return firestore.client()

db = conectar_banco_master()

# 3. FUNÇÕES CORE (As melhores funções dos seus arquivos)
def normalizar(t):
    return "".join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn').lower()

def calcular_distancia(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

# 4. ESTILO GOOGLE (Sua nova UI Clean)
st.markdown("""
    <style>
        .stApp { background-color: white !important; }
        div.stTextInput > div > div > input {
            border-radius: 24px !important; border: 1px solid #dfe1e5 !important;
            padding: 12px 25px !important; box-shadow: none !important;
        }
        .result-card { max-width: 650px; margin-bottom: 25px; font-family: 'Arial'; }
        .result-title { color: #1a0dab; font-size: 20px; text-decoration: none; cursor: pointer; }
        .badge-elite { background-color: #FF8C00; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; }
    </style>
""", unsafe_allow_html=True)

# 5. GERENCIAMENTO DE ESTADO (Navegação dos Botões)
if 'page' not in st.session_state: st.session_state.page = 'home'
if 'q' not in st.session_state: st.session_state.q = ""

# --- MODO HOME (PÁGINA INICIAL) ---
if st.session_state.page == 'home':
    st.write("##")
    st.write("##")
    st.markdown("<h1 style='text-align: center; font-size: 90px; color:#4285F4;'>GeralJá</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        query = st.text_input("", placeholder="O que você precisa?", key="main_search")
        st.write("##")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c2:
            if st.button("Buscar Agora", use_container_width=True) or (query != ""):
                if query:
                    st.session_state.q = query
                    st.session_state.page = 'results'
                    st.rerun()
        with c4:
            if st.button("Sou Profissional", use_container_width=True):
                st.session_state.page = 'cadastro'
                st.rerun()

# --- MODO RESULTADOS (ESTILO GOOGLE SEARCH) ---
elif st.session_state.page == 'results':
    t1, t2 = st.columns([1, 5])
    with t1:
        if st.button("← Voltar"):
            st.session_state.page = 'home'
            st.rerun()
    with t2:
        st.session_state.q = st.text_input("", value=st.session_state.q)

    st.divider()
    
    # Busca Real no Firebase usando sua lógica de categoria
    if db:
        profs = db.collection("profissionais").where("aprovado", "==", True).stream()
        lista = []
        termo = normalizar(st.session_state.q)
        
        for p in profs:
            dados = p.to_dict()
            if termo in normalizar(dados.get('categoria','')) or termo in normalizar(dados.get('nome','')):
                lista.append(dados)
        
        # Ranking de Elite (Sua meta de 90% de sucesso)
        lista = sorted(lista, key=lambda x: (x.get('elite', False), x.get('nota', 0)), reverse=True)

        for p in lista:
            elite = "<span class='badge-elite'>ELITE</span>" if p.get('elite') else ""
            link_wa = f"https://wa.me/{p.get('telefone')}?text=Vim+pelo+GeralJa"
            st.markdown(f"""
                <div class="result-card">
                    <div style="color:#202124; font-size:14px;">https://geralja.com.br › {p.get('categoria')}</div>
                    <a href="{link_wa}" target="_blank" class="result-title">{p.get('nome')} {elite}</a>
                    <div style="color:#4d5156; font-size:14px;">⭐ {p.get('nota')} • {p.get('bairro')}</div>
                    <div style="color:#4d5156; font-size:14px;">{p.get('descricao')}</div>
                </div>
            """, unsafe_allow_html=True)
            if st.button(f"Contratar {p.get('nome')}", key=p.get('nome')):
                st.success("Redirecionando...")

# --- MODO ADMIN (O SEU COFRE) ---
elif st.session_state.page == 'admin':
    if st.button("Sair"): st.session_state.page = 'home'; st.rerun()
    senha = st.text_input("Chave do Cofre", type="password")
    if senha == "riqueza2026": # Sua senha original
        st.title("🤝 Gestão de Parceiros")
        # Aqui entra sua lógica de aprovação que já estava no código limpo
        pendentes = db.collection("profissionais").where("aprovado", "==", False).stream()
        for p in pendentes:
            st.write(f"Novo Cadastro: {p.to_dict().get('nome')}")
            if st.button(f"Aprovar {p.id}"):
                db.collection("profissionais").document(p.id).update({"aprovado": True})
                st.rerun()

# --- RODAPÉ ÚNICO ---
st.markdown(f"<div style='position:fixed; bottom:0; width:100%; text-align:center; padding:10px; background:#f2f2f2; color:#70757a; font-size:12px;'>GeralJá v20.0 © {datetime.datetime.now().year} | São Paulo - Brasil</div>", unsafe_allow_html=True)
