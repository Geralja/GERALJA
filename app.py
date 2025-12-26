import streamlit as st
import random
import time

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="GeralJá | Elite HUB", layout="centered", initial_sidebar_state="collapsed")

# --- 2. CSS DE ALTA PERFORMANCE ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: radial-gradient(circle at top, #1a2a40 0%, #050a10 100%); color: white; }

    /* Glassmorphism */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px; padding: 25px; margin-bottom: 20px;
    }

    /* Balão de Chat Estilo WhatsApp */
    .chat-bubble {
        background: #056162; color: white;
        padding: 12px 16px; border-radius: 15px 15px 0 15px;
        margin-bottom: 10px; width: fit-content; max-width: 80%;
        align-self: flex-end; margin-left: auto;
        font-size: 14px; position: relative;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%) !important;
        border: none !important; color: white !important;
        border-radius: 16px !important; font-weight: 900 !important;
    }
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGICA DE NAVEGAÇÃO ---
if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'
if 'abertura' not in st.session_state:
    placeholder = st.empty()
    with placeholder.container():
        st.markdown('<div style="text-align:center; margin-top:30vh;"><h1 style="color:#f39c12; font-size:60px;">GERALJÁ</h1><p style="letter-spacing:5px;">CONECTANDO O GRAJAÚ...</p></div>', unsafe_allow_html=True)
        time.sleep(2.5)
    st.session_state.abertura = True
    placeholder.empty()

# --- 4. FLUXO DO APLICATIVO ---
if st.session_state.get('abertura'):

    # TELA DE BUSCA
    if st.session_state.etapa == 'busca':
        st.markdown("<h2 style='text-align:center;'>Radar de Profissionais</h2>", unsafe_allow_html=True)
        with st.container():
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            servico = st.selectbox("O que você precisa?", ["Selecione...", "Eletricista", "Encanador", "Pintor"])
            rua = st.text_input("📍 Seu Endereço")
            st.markdown('</div>', unsafe_allow_html=True)
            if st.button("ATIVAR RADAR"):
                if servico != "Selecione..." and rua:
                    st.session_state.servico = servico
                    st.session_state.etapa = 'resultado'
                    st.rerun()

    # TELA DE RESULTADO
    elif st.session_state.etapa == 'resultado':
        st.markdown(f"<h3 style='text-align:center;'>Profissional Encontrado</h3>", unsafe_allow_html=True)
        st.markdown(f"""
            <div class="glass-card" style="text-align:center;">
                <div style="font-size:50px;">👨‍🔧</div>
                <h2 style="color:#f39c12;">Bony Silva</h2>
                <p>⭐ 4.9 | Especialista em {st.session_state.servico}</p>
                <h1 style="margin:10px 0;">R$ {random.randint(150, 300)},00</h1>
            </div>
        """, unsafe_allow_html=True)
        if st.button("💳 CONTRATAR AGORA"):
            st.session_state.etapa = 'pagamento'
            st.rerun()

    # TELA DE PAGAMENTO
    elif st.session_state.etapa == 'pagamento':
        st.markdown("<h3 style='text-align:center;'>Pagamento Seguro</h3>", unsafe_allow_html=True)
        chave_pix = "00020101021226850014br.gov.bcb.pix0123geralja998877665544"
        
        st.markdown(f"""
            <div class="glass-card" style="background:white; color:black; text-align:center;">
                <img src="https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={chave_pix}" style="margin-bottom:15px;">
                <p style="font-size:12px; color:gray;">PIX COPIA E COLA:</p>
                <code style="word-break:break-all; font-size:10px; background:#f0f0f0; padding:10px; display:block;">{chave_pix}</code>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("✅ JÁ REALIZEI O PIX"):
            st.session_state.etapa = 'chat'
            st.rerun()

    # TELA DE CHAT (A MÁGICA)
    elif st.session_state.etapa == 'chat':
        st.markdown("<h3 style='text-align:center;'>📲 Conexão Estabelecida</h3>", unsafe_allow_html=True)
        
        # Container de Chat
        st.markdown('<div class="glass-card" style="min-height:300px; display:flex; flex-direction:column; justify-content:flex-end;">', unsafe_allow_html=True)
        
        # Simulação de digitação
        msg_placeholder = st.empty()
        with msg_placeholder:
            st.markdown('<p style="color:gray; font-size:12px;">Bony Silva está digitando...</p>', unsafe_allow_html=True)
            time.sleep(2)
        
        st.markdown(f'<div class="chat-bubble">Olá! Aqui é o Bony. Acabei de receber seu pedido para <b>{st.session_state.servico}</b> aqui no GeralJá! ✅</div>', unsafe_allow_html=True)
        time.sleep(1.5)
        st.markdown('<div class="chat-bubble">Já estou organizando minhas ferramentas. Em 10 minutos te chamo no WhatsApp real para confirmar a chegada, beleza? 🛠️</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.balloons()
        if st.button("CONCLUIR E VOLTAR"):
            st.session_state.etapa = 'busca'
            st.rerun()
