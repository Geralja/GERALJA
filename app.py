import streamlit as st
import random
import time

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="GeralJá | Soluções", layout="centered", initial_sidebar_state="collapsed")

# --- 2. ESTADOS ---
if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'
if 'lucro_plataforma' not in st.session_state: st.session_state.lucro_plataforma = 0.0
if 'pedidos_concluidos' not in st.session_state: st.session_state.pedidos_concluidos = 0

CHAVE_PIX_ALERATORIA = "09be938c-ee95-469f-b221-a3beea63964b"
LISTA_PROS = sorted(["Pintor", "Eletricista", "Encanador", "Diarista", "Pedreiro", "Montador de Móveis", "Mecânico", "Jardineiro", "Chaveiro"])

# --- 3. CSS (FUNDO BRANCO E CORES DO LOGO) ---
st.markdown("""
    <style>
    /* FUNDO BRANCO */
    .stApp { background-color: #FFFFFF !important; color: #333333 !important; }
    
    /* LOGO: GERAL (AZUL) JÁ (LARANJA) */
    .logo-container { text-align: center; padding: 20px; }
    .logo-geral { color: #0047AB; font-size: 60px; font-weight: 900; }
    .logo-ja { color: #FF8C00; font-size: 60px; font-weight: 900; }

    /* BOTÃO PULSANTE (LARANJA COM TEXTO BRANCO) */
    div.stButton > button {
        background-color: #FF8C00 !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 900 !important;
        height: 55px !important;
        width: 100% !important;
        box-shadow: 0 4px 15px rgba(255, 140, 0, 0.3) !important;
        transition: 0.3s;
    }
    
    div.stButton > button:hover {
        background-color: #E67E22 !important;
        transform: translateY(-2px);
    }

    /* AJUSTE DE INPUTS PARA FUNDO BRANCO */
    .stSelectbox, .stTextInput { color: black !important; }
    
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 4. BARRA LATERAL ---
with st.sidebar:
    st.title("🔐 Admin")
    senha = st.text_input("Senha", type="password")
    if senha == "admin777":
        if st.button("ACESSAR PAINEL"):
            st.session_state.etapa = 'admin'
            st.rerun()

# --- 5. FLUXO ---

# VISÃO ADMIN
if st.session_state.etapa == 'admin':
    st.title("📊 Gestão GeralJá")
    st.metric("Faturamento", f"R$ {st.session_state.lucro_plataforma:.2f}")
    if st.button("⬅ VOLTAR"):
        st.session_state.etapa = 'busca'
        st.rerun()

# ETAPA BUSCA
elif st.session_state.etapa == 'busca':
    # LOGO COLORIDO
    st.markdown("""
        <div class="logo-container">
            <span class="logo-geral">GERAL</span><span class="logo-ja">JÁ</span>
            <p style="color: #666; margin-top: -10px; font-weight: 500;">O Grajaú resolve aqui.</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        servico = st.selectbox("O que você precisa hoje?", [""] + LISTA_PROS)
        rua = st.text_input("📍 Seu Endereço no Grajaú")
        
        st.write("") 
        if st.button("ATIVAR RADAR AGORA", use_container_width=True):
            if servico and rua:
                st.session_state.servico_busca = servico
                st.session_state.etapa = 'resultado'
                st.rerun()
            else:
                st.warning("Preencha os campos.")

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🆘 SUPORTE 24H", use_container_width=True):
        st.info("Conectando...")

# ETAPA RESULTADO
elif st.session_state.etapa == 'resultado':
    st.markdown("### 📍 Profissional Localizado")
    
    # MAPA DARK PARA CONTRASTE NO FUNDO BRANCO
    st.markdown("""
        <div style="width:100%; height:220px; border-radius:15px; overflow:hidden; border: 1px solid #ddd; margin-bottom:20px;">
            <img src="https://api.mapbox.com/styles/v1/mapbox/streets-v11/static/-46.6682,-23.7721,13/600x220?access_token=pk.eyJ1IjoiZ3VpZG94IiwiYSI6ImNrZnduZnR4MDBhNnoycnBnbm9idG9yejkifQ.7Wp6M_2yA6_z_rG-vH0Z6A" style="width:100%; height:100%; object-fit:cover;">
        </div>
    """, unsafe_allow_html=True)
    
    preco = random.randint(180, 350)
    st.markdown(f"""
        <div style="background:#f9f9f9; padding:20px; border-radius:20px; border:1px solid #eee; text-align:center; color: #333;">
            <h2 style="color:#0047AB; margin:0;">Bony Silva</h2>
            <p>Especialista em {st.session_state.servico_busca}</p>
            <h1 style="color: #FF8C00; margin:10px 0;">R$ {preco},00</h1>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("💳 CONTRATAR", use_container_width=True):
        st.session_state.valor_final = preco
        st.session_state.etapa = 'pagamento'
        st.rerun()
    if st.button("⬅ VOLTAR", use_container_width=True):
        st.session_state.etapa = 'busca'; st.rerun()

# ETAPA PAGAMENTO
elif st.session_state.etapa == 'pagamento':
    val = st.session_state.valor_final
    st.markdown(f"""
        <div style="background:#f1f1f1; padding:30px; border-radius:20px; text-align:center; color: black;">
            <p style="color:gray;">VALOR DO SERVIÇO</p>
            <h1 style="color:#27ae60; margin:0;">R$ {val},00</h1>
            <br>
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={CHAVE_PIX_ALERATORIA}">
            <p style="font-size:11px; margin-top:15px; color: #333;"><b>Chave Pix Aleatória:</b><br>{CHAVE_PIX_ALERATORIA}</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("✅ JÁ REALIZEI O PAGAMENTO", use_container_width=True):
        st.session_state.lucro_plataforma += (val * 0.10)
        st.session_state.pedidos_concluidos += 1
        st.session_state.etapa = 'sucesso'
        st.rerun()

elif st.session_state.etapa == 'sucesso':
    st.balloons()
    st.success("Tudo pronto! O profissional já recebeu seu chamado.")
    if st.button("VOLTAR AO INÍCIO", use_container_width=True):
        st.session_state.etapa = 'busca'; st.rerun()
