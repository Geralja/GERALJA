import streamlit as st
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="GeralJá | Elite HUB", layout="wide", initial_sidebar_state="collapsed")

# --- CSS PARA ANIMAÇÃO COM IMAGEM ---
st.markdown("""
    <style>
    .stApp { background: #050a10; }
    
    @keyframes heroZoom {
        from { transform: scale(0.8); opacity: 0; }
        to { transform: scale(1); opacity: 1; }
    }
    
    @keyframes revealText {
        from { letter-spacing: 15px; opacity: 0; }
        to { letter-spacing: 2px; opacity: 1; }
    }

    .splash-box {
        text-align: center;
        margin-top: 10vh;
    }

    .hero-img {
        width: 280px;
        border-radius: 50%; /* Deixa a imagem redonda como um selo */
        border: 4px solid #f39c12;
        animation: heroZoom 2s ease-out;
        box-shadow: 0 0 30px rgba(243, 156, 18, 0.4);
    }

    .logo-main {
        font-size: 50px;
        font-weight: 900;
        color: #f39c12;
        margin-top: 20px;
        animation: revealText 1.5s ease-in-out;
    }

    /* Ocultar elementos padrão */
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- LÓGICA DA TELA DE ABERTURA ---
if 'abertura_concluida' not in st.session_state:
    placeholder = st.empty()
    with placeholder.container():
        # AQUI VAI O LINK DA IMAGEM DAS 2 PESSOAS QUE GERAMOS
        # Você pode usar o link da imagem que mais gostou aqui
        url_imagem = "https://img.freepik.com/vetores-premium/logotipo-de-servicos-domesticos-com-encanador-e-cliente_origem.jpg"
        
        st.markdown(f"""
            <div class="splash-box">
                <img src="{url_imagem}" class="hero-img">
                <h1 class="logo-main">GERAL<span style="color:white">JÁ</span></h1>
                <p style="color:#bdc3c7; font-size:12px;">SOLUÇÕES REAIS PARA O GRAJAÚ</p>
                <div style="margin-top:30px; border-top: 1px solid #333; width: 50%; margin-left: 25%;"></div>
            </div>
        """, unsafe_allow_html=True)
        
        time.sleep(4.0) # Tempo para o cliente ver a logo e a imagem
    
    st.session_state.abertura_concluida = True
    placeholder.empty()

# --- CONTEÚDO DO APP APÓS ABERTURA ---
if st.session_state.get('abertura_concluida'):
    # Menu Superior Minimalista
    st.markdown('<h3 style="text-align:center; color:#f39c12; margin-top:0;">GERALJÁ</h3>', unsafe_allow_html=True)
    
    # Restante das funcionalidades (Busca, Resultado, Pagamento 10%)
    if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'

    if st.session_state.etapa == 'busca':
        st.markdown("### 🔍 O que vamos resolver hoje?")
        servico = st.selectbox("Escolha uma categoria:", ["Pintura", "Elétrica", "Hidráulica", "Limpeza"])
        rua = st.text_input("📍 Sua localização:")
        
        if st.button("ATIVAR RADAR", use_container_width=True):
            st.session_state.etapa = 'resultado'
            st.rerun()
            
    # Adicione aqui o código do resultado e pagamento (10%) que já validamos!
