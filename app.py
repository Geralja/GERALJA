import streamlit as st
import time

# --- 1. CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="GeralJá | Elite HUB", layout="wide", initial_sidebar_state="collapsed")

# --- 2. ESTILO CSS (Animação e Design) ---
st.markdown("""
    <style>
    .stApp { background: #050a10; color: white; }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .splash-container {
        text-align: center;
        margin-top: 15vh;
        animation: fadeIn 2s ease-in-out;
    }

    .hero-img {
        width: 200px;
        height: 200px;
        border-radius: 50%;
        border: 5px solid #f39c12;
        object-fit: cover;
        box-shadow: 0 0 20px rgba(243, 156, 18, 0.5);
    }

    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. LÓGICA DE ABERTURA (Splash Screen) ---
if 'abertura_concluida' not in st.session_state:
    placeholder = st.empty()
    with placeholder.container():
        # Usando uma imagem pública de exemplo (Encanador e Cliente)
        # Se você tiver o link da SUA imagem, troque abaixo:
        img_url = "https://cdn-icons-png.flaticon.com/512/9437/9437568.png" 
        
        st.markdown(f"""
            <div class="splash-container">
                <img src="{img_url}" class="hero-img">
                <h1 style="font-size: 50px; color: #f39c12; margin-top:20px;">GERAL<span style="color:white">JÁ</span></h1>
                <p style="letter-spacing: 3px; color: #bdc3c7;">CONECTANDO O GRAJAÚ</p>
                <p style="font-size: 10px; color: gray; margin-top: 50px;">Carregando Radar...</p>
            </div>
        """, unsafe_allow_html=True)
        time.sleep(4) 
    st.session_state.abertura_concluida = True
    placeholder.empty()

# --- 4. CONTEÚDO DO APP (Após a abertura) ---
if st.session_state.get('abertura_concluida'):
    # Inicialização de etapas
    if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'

    # Topo do site
    st.markdown('<h2 style="text-align:center; color:#f39c12;">GERALJÁ</h2>', unsafe_allow_html=True)

    if st.session_state.etapa == 'busca':
        st.markdown("### 🔍 O que você precisa?")
        profissao = st.selectbox("Escolha o serviço:", ["", "Pintor", "Eletricista", "Encanador", "Diarista"])
        endereco = st.text_input("📍 Local do serviço:")
        
        if st.button("ATIVAR RADAR", use_container_width=True):
            if profissao and endereco:
                st.session_state.servico_nome = profissao
                st.session_state.etapa = 'resultado'
                st.rerun()
            else:
                st.warning("Preencha os campos para buscar.")

    elif st.session_state.etapa == 'resultado':
        st.markdown(f"### Profissional encontrado para: {st.session_state.servico_nome}")
        st.info("Bony Silva - ⭐ 4.9 (Verificado)")
        if st.button("💳 CONTRATAR (Taxa 10%)", use_container_width=True):
            st.session_state.etapa = 'pagamento'
            st.rerun()
        if st.button("⬅️ Voltar"):
            st.session_state.etapa = 'busca'
            st.rerun()

    elif st.session_state.etapa == 'pagamento':
        st.markdown("### 💳 Checkout GeralJá")
        st.success("Pague via PIX para garantir o serviço e sua segurança.")
        st.code("Chave PIX: 11991853488")
        st.write("O valor será liberado ao profissional após a conclusão.")
        if st.button("CONCLUÍDO"):
            st.balloons()
            st.session_state.etapa = 'busca'
            st.rerun()
