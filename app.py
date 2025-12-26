import streamlit as st
import random
import time

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="GeralJá | Elite HUB", layout="centered", initial_sidebar_state="collapsed")

# --- 2. ESTADOS ---
if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'
if 'lucro_plataforma' not in st.session_state: st.session_state.lucro_plataforma = 0.0
if 'pedidos_concluidos' not in st.session_state: st.session_state.pedidos_concluidos = 0

CHAVE_PIX_ALERATORIA = "09be938c-ee95-469f-b221-a3beea63964b"
LISTA_PROS = sorted(["Pintor", "Eletricista", "Encanador", "Diarista", "Pedreiro", "Montador de Móveis", "Mecânico", "Jardineiro", "Chaveiro"])

# --- 3. CSS PARA O BOTÃO PULSANTE (FORÇADO) ---
st.markdown("""
    <style>
    .stApp { background: #050a10; color: white; }
    
    /* ANIMAÇÃO DE PULSAR */
    @keyframes pulse-glow {
        0% { box-shadow: 0 0 5px #f39c12; transform: scale(1); }
        50% { box-shadow: 0 0 25px #f1c40f; transform: scale(1.02); }
        100% { box-shadow: 0 0 5px #f39c12; transform: scale(1); }
    }

    div.stButton > button {
        background: linear-gradient(135deg, #f39c12, #e67e22) !important;
        color: white !important;
        border: none !important;
        border-radius: 15px !important;
        font-weight: 900 !important;
        animation: pulse-glow 2s infinite !important;
        height: 55px !important;
    }
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 4. FLUXO ---

if st.session_state.etapa == 'busca':
    # --- LOGO COM DEGRADÊ FORÇADO VIA INLINE ---
    st.markdown("""
        <div style="text-align: center; padding: 20px;">
            <h1 style="
                font-size: 70px; 
                font-weight: 900; 
                margin: 0;
                background: -webkit-linear-gradient(#f39c12, #f1c40f);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                filter: drop-shadow(0 0 10px rgba(243,156,18,0.4));
            ">GERALJÁ</h1>
            <p style="color: #666; letter-spacing: 3px; font-weight: bold; margin-top: -10px;">
                SOLUÇÕES NO GRAJAÚ
            </p>
        </div>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.1);">', unsafe_allow_html=True)
        servico = st.selectbox("Qual profissional você precisa?", [""] + LISTA_PROS)
        rua = st.text_input("📍 Digite sua rua ou ponto de referência")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.write("") # Espaço
        
        # BOTÃO ATIVAR RADAR
        if st.button("🚀 ATIVAR RADAR DE PROFISSIONAIS"):
            if servico and rua:
                st.session_state.servico_busca = servico
                st.session_state.etapa = 'resultado'
                st.rerun()
            else:
                st.warning("Preencha o serviço e o endereço!")

    # --- BOTÃO DE SUPORTE COM FRASE DE EFEITO ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🆘 NÃO ENCONTROU? FALE COM NOSSA CENTRAL 24H"):
        st.success("Chamando suporte via WhatsApp...")

elif st.session_state.etapa == 'resultado':
    st.markdown("<h2 style='text-align:center;'>Profissional Encontrado!</h2>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style="background: rgba(255,255,255,0.05); padding: 25px; border-radius: 20px; border: 2px solid #f39c12; text-align: center;">
            <h2 style="color: #f39c12; margin:0;">Bony Silva</h2>
            <p>Especialista em {st.session_state.servico_busca}</p>
            <hr style="opacity:0.1">
            <h1 style="color: white;">R$ {random.randint(150, 300)},00</h1>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("💳 CONTRATAR AGORA"):
        st.session_state.etapa = 'pagamento'
        st.rerun()
    if st.button("⬅ Voltar"):
        st.session_state.etapa = 'busca'
        st.rerun()

# --- ABAIXO: TELA DE PAGAMENTO COM PIX ATUALIZADO ---
elif st.session_state.etapa == 'pagamento':
    st.markdown("<h3 style='text-align:center;'>Pagamento via PIX</h3>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style="background: white; color: black; padding: 20px; border-radius: 20px; text-align: center;">
            <p style="margin:0; color: gray;">CHAVE ALEATÓRIA:</p>
            <code style="font-size: 12px;">{CHAVE_PIX_ALERATORIA}</code>
            <br><br>
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={CHAVE_PIX_ALERATORIA}">
            <p style="font-size: 12px; margin-top: 10px;">Escaneie para pagar</p>
        </div>
    """, unsafe_allow_html=True)
    if st.button("✅ JÁ PAGUEI"):
        st.session_state.etapa = 'busca'
        st.balloons()
        st.rerun()
