import streamlit as st
import random
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="GeralJá | O HUB do Grajaú", layout="wide", initial_sidebar_state="collapsed")

# --- ANIMAÇÃO DE ABERTURA (CSS) ---
st.markdown("""
    <style>
    /* Fundo do App */
    .stApp { background: #050a10; color: white; }

    /* Animação da Logo */
    @keyframes pulse {
        0% { transform: scale(1); opacity: 0.8; }
        50% { transform: scale(1.05); opacity: 1; }
        100% { transform: scale(1); opacity: 0.8; }
    }

    @keyframes slideUp {
        from { transform: translateY(30px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }

    .splash-container {
        text-align: center;
        margin-top: 15vh;
        animation: slideUp 1.5s ease-out;
    }

    .logo-texto {
        font-size: 60px;
        font-weight: 900;
        color: #f39c12;
        letter-spacing: -2px;
        margin-bottom: 0;
    }

    .sub-texto {
        color: #5dade2;
        font-size: 14px;
        letter-spacing: 5px;
        text-transform: uppercase;
        animation: pulse 2s infinite;
    }

    /* Esconder menus padrão do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- LÓGICA DE ABERTURA ---
if 'abertura' not in st.session_state:
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("""
            <div class="splash-container">
                <div style="font-size: 80px;">👷‍♂️</div>
                <h1 class="logo-texto">GERAL<span style="color:white">JÁ</span></h1>
                <p class="sub-texto">Conectando o Grajaú</p>
                <div style="margin-top:20px;">
                    <small style="color:gray;">Carregando radar de profissionais...</small>
                </div>
            </div>
        """, unsafe_allow_html=True)
        time.sleep(3.5) # Tempo da animação de abertura
    st.session_state.abertura = True
    placeholder.empty()

# --- CONTEÚDO PRINCIPAL (Só aparece após a abertura) ---
if st.session_state.get('abertura'):
    # Cabeçalho Fixo Minimalista
    st.markdown('<h2 style="text-align:center; color:#f39c12; margin-top:0;">GERALJÁ</h2>', unsafe_allow_html=True)
    
    # Inicialização de etapas
    if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'

    # (Abaixo segue a lógica de busca e pagamento que já validamos)
    # ... Coloque aqui o código das etapas 'busca', 'resultado' e 'pagamento' ...
    
    # Exemplo simplificado para teste:
    if st.session_state.etapa == 'busca':
        st.markdown("### 🔍 Qual serviço você procura?")
        prof = st.selectbox("", ["Pintor", "Eletricista", "Encanador", "Diarista"])
        if st.button("ATIVAR RADAR", use_container_width=True):
            st.session_state.etapa = 'resultado'
            st.rerun()

    elif st.session_state.etapa == 'resultado':
        st.success(f"Profissional encontrado para {prof}!")
        if st.button("Voltar"):
            st.session_state.etapa = 'busca'
            st.rerun()
