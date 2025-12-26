import streamlit as st
import random

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="GeralJá", layout="centered", initial_sidebar_state="collapsed")

# --- 2. ESTADOS ---
if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'
if 'lucro_plataforma' not in st.session_state: st.session_state.lucro_plataforma = 0.0

CHAVE_PIX_ALERATORIA = "09be938c-ee95-469f-b221-a3beea63964b"
LISTA_PROS = sorted(["Pintor", "Eletricista", "Encanador", "Diarista", "Pedreiro", "Montador de Móveis", "Mecânico", "Jardineiro", "Chaveiro"])

# --- 3. CSS (FUNDO BRANCO + MENU FIXO) ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    
    /* LOGO COLORIDO */
    .logo-container { text-align: center; margin-top: 30px; margin-bottom: 20px; }
    .logo-geral { color: #0047AB; font-size: 50px; font-weight: 900; }
    .logo-ja { color: #FF8C00; font-size: 50px; font-weight: 900; }

    /* BOTÃO LARANJA */
    div.stButton > button {
        background-color: #FF8C00 !important;
        color: white !important;
        border-radius: 12px !important;
        font-weight: 900 !important;
        height: 50px !important;
        width: 100% !important;
        border: none !important;
    }

    /* ESCONDER SIDEBAR E HEADER PADRÃO */
    [data-testid="stSidebar"] { display: none; }
    header { visibility: hidden; }
    footer { visibility: hidden; }
    
    /* ESTILO DO BOTÃO DE ACESSO NO CANTO */
    .floating-auth {
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 9999;
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. MENU DE ACESSO (FLUTUANTE NO TOPO DIREITO) ---
# Criamos uma área fixa no topo para a engrenagem
with st.container():
    col_vazia, col_btn = st.columns([5, 1])
    with col_btn:
        with st.popover("⚙️"):
            st.write("🔒 **Acesso Nodo**")
            senha = st.text_input("Senha", type="password", key="login_admin")
            if senha == "admin777":
                if st.button("Entrar no Painel"):
                    st.session_state.etapa = 'admin'
                    st.rerun()

# --- 5. FLUXO DE TELAS ---

# TELA ADMIN
if st.session_state.etapa == 'admin':
    st.title("📊 Gestão GeralJá")
    st.metric("Faturamento Acumulado", f"R$ {st.session_state.lucro_plataforma:.2f}")
    if st.button("⬅ SAIR DO ADMIN"):
        st.session_state.etapa = 'busca'
        st.rerun()

# TELA DE BUSCA (HOME)
elif st.session_state.etapa == 'busca':
    st.markdown("""
        <div class="logo-container">
            <span class="logo-geral">GERAL</span><span class="logo-ja">JÁ</span>
            <p style="color: #666; margin-top: -10px;">O Grajaú resolve aqui.</p>
        </div>
    """, unsafe_allow_html=True)
    
    servico = st.selectbox("O que você precisa hoje?", [""] + LISTA_PROS)
    rua = st.text_input("📍 Seu Endereço no Grajaú")
    
    if st.button("ATIVAR RADAR AGORA"):
        if servico and rua:
            st.session_state.servico_busca = servico
            st.session_state.etapa = 'resultado'
            st.rerun()
        else:
            st.warning("⚠️ Por favor, preencha o serviço e o endereço.")

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🆘 SUPORTE 24H"):
        st.info("Conectando ao suporte via WhatsApp...")

# TELA RESULTADO
elif st.session_state.etapa == 'resultado':
    st.markdown("### 📍 Profissional Localizado")
    st.image("https://api.mapbox.com/styles/v1/mapbox/streets-v11/static/-46.6682,-23.7721,13/600x200?access_token=pk.eyJ1IjoiZ3VpZG94IiwiYSI6ImNrZnduZnR4MDBhNnoycnBnbm9idG9yejkifQ.7Wp6M_2yA6_z_rG-vH0Z6A")
    
    preco = random.randint(180, 350)
    st.markdown(f"""
        <div style="background:#f9f9f9; padding:20px; border-radius:20px; border:1px solid #eee; text-align:center;">
            <h2 style="color:#0047AB; margin:0;">Bony Silva</h2>
            <p style="color: #333;">Especialista em {st.session_state.servico_busca}</p>
            <h1 style="color: #FF8C00;">R$ {preco},00</h1>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("💳 CONTRATAR"):
        st.session_state.valor_final = preco
        st.session_state.etapa = 'pagamento'
        st.rerun()
    if st.button("⬅ VOLTAR"):
        st.session_state.etapa = 'busca'; st.rerun()

# TELA PAGAMENTO
elif st.session_state.etapa == 'pagamento':
    val = st.session_state.valor_final
    st.markdown(f"""
        <div style="background:#f1f1f1; padding:30px; border-radius:20px; text-align:center; color: black;">
            <h1 style="color:#27ae60;">R$ {val},00</h1>
            <br>
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={CHAVE_PIX_ALERATORIA}">
            <p style="font-size:11px; margin-top:15px; color: #333;"><b>Chave Pix:</b> {CHAVE_PIX_ALERATORIA}</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("✅ JÁ PAGUEI"):
        st.session_state.lucro_plataforma += (val * 0.10)
        st.session_state.etapa = 'busca'
        st.balloons()
        st.rerun()
