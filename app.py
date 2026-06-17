import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import re
import unicodedata
# ... (Manter todos os seus outros imports aqui)

# --- CONFIGURAÇÕES GERAIS ---
ZAP_VENDAS = '5511980168513'
st.set_page_config(page_title="Portal Grajaú Tem", layout="wide")

# --- BLOCO 1: CSS E BRANDING ---
def configurar_estilo():
    st.markdown("""
        <style>
            .titulo-azul { color: #003399; font-weight: 800; font-size: 3rem; margin-bottom: 0; }
            .titulo-amarelo { color: #FFD700; font-weight: 800; font-size: 3rem; margin-bottom: 0; }
            .subtitulo { color: #555; font-size: 1.2rem; margin-top: 0; }
            .yellow-line { border-bottom: 3px solid #FFD700; width: 100%; margin-top: 20px; margin-bottom: 20px; }
            .centered-layout { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 60vh; }
        </style>
    """, unsafe_allow_html=True)

configurar_estilo()

# --- BLOCO 2: MOTOR E ESTADO ---
if 'pesquisou' not in st.session_state:
    st.session_state.pesquisou = False

# --- BLOCO 3: INTERFACE ---
def main():
    # Painel Admin Escondido no Topo
    with st.sidebar:
        if st.button("⚙️"):
            senha = st.text_input("Acesso:", type="password")
            if senha == "1234": st.success("Admin Ativo")

    # Layout Dinâmico
    if not st.session_state.pesquisou:
        # PÁGINA INICIAL (CENTRALIZADA)
        st.markdown('<div class="centered-layout">', unsafe_allow_html=True)
        st.markdown('<div><span class="titulo-azul">Portal</span> <span class="titulo-amarelo">Grajaú Tem</span></div>', unsafe_allow_html=True)
        st.markdown('<p class="subtitulo">GeralJá</p>', unsafe_allow_html=True)
        
        busca = st.text_input("", placeholder="O que você precisa hoje no Grajaú?", key="busca_init")
        raio = st.slider("Raio de distância (km)", 0, 50, 5)
        
        if busca:
            st.session_state.pesquisou = True
            st.session_state.ultima_busca = busca
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    else:
        # PÁGINA DE RESULTADOS (TOPO)
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown('<h2 style="color:#003399; margin:0;">Grajaú</h2>', unsafe_allow_html=True)
        with col2:
            nova_busca = st.text_input("", value=st.session_state.get("ultima_busca", ""), key="busca_top")
        
        st.markdown('<div class="yellow-line"></div>', unsafe_allow_html=True)
        
        # Resultados da Vitrine
        st.subheader(f"Resultados para: {nova_busca}")
        st.write("--- Aqui entrarão os cards do Firebase ---")
        
        if st.button("Nova Busca"):
            st.session_state.pesquisou = False
            st.rerun()

if __name__ == "__main__":
    main()
