import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json, base64

# --- [BLOCO A] CONFIGURAÇÃO E INICIALIZAÇÃO ---
st.set_page_config(page_title="GeralJá | Busca Local", page_icon="📍", layout="centered")

# CSS para o estilo "Google" centralizado
st.markdown("""
    <style>
        .stApp { background-color: #0f172a; }
        .main-container { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 60vh; }
        .search-bar { width: 100%; max-width: 600px; }
        .stTextInput > div > div > input { border-radius: 50px; padding: 20px; border: 1px solid #334155; }
    </style>
""", unsafe_allow_html=True)

# Inicialização de estado
if 'logado' not in st.session_state:
    st.session_state.logado = False

# --- [BLOCO B] INTERFACE DE LOGIN E BUSCA ---
def renderizar_login():
    st.markdown("<div class='main-container'>", unsafe_allow_html=True)
    st.title("📍 GeralJá")
    query = st.text_input("", placeholder="O que você procura no Grajaú hoje?", label_visibility="collapsed")
    
    col1, col2 = st.columns([1, 1])
    if col1.button("Pesquisar"):
        st.info("Resultados da busca apareceriam aqui...")
    
    if col2.button("Acesso Profissional 🔐"):
        st.session_state.show_login = True
    
    if st.session_state.get('show_login', False):
        user = st.text_input("Usuário")
        pwd = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if user == "admin" and pwd == "admin": # Substituir por lógica real de auth
                st.session_state.logado = True
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- [BLOCO C] DASHBOARD APÓS LOGIN ---
def renderizar_dashboard():
    st.sidebar.title("Painel de Controle")
    tabs = st.tabs(["👥 Parceiros", "📰 Notícias", "🛍️ Loja", "📜 Vendas"])
    
    with tabs[0]:
        st.write("Gerenciamento de parceiros desbloqueado.")
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

# --- [BLOCO D] FLUXO PRINCIPAL ---
if not st.session_state.logado:
    renderizar_login()
else:
    renderizar_dashboard()
