import streamlit as st
import random
import time

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="GeralJá | Soluções", layout="centered", initial_sidebar_state="collapsed")

# --- 2. BANCO DE DATOS (CONSTANTES) ---
if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'
if 'lucro_plataforma' not in st.session_state: st.session_state.lucro_plataforma = 0.0
if 'pedidos_concluidos' not in st.session_state: st.session_state.pedidos_concluidos = 0

CHAVE_PIX_ALERATORIA = "09be938c-ee95-469f-b221-a3beea63964b"
LISTA_PROS = sorted(["Pintor", "Eletricista", "Encanador", "Diarista", "Pedreiro", "Montador de Móveis", "Mecânico", "Jardineiro", "Chaveiro"])

# --- 3. CSS (LIMPO E PROFISSIONAL) ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; color: #333333 !important; }
    
    .logo-container { text-align: center; padding: 10px; margin-top: 15px; }
    .logo-geral { color: #0047AB; font-size: 55px; font-weight: 900; }
    .logo-ja { color: #FF8C00; font-size: 55px; font-weight: 900; }

    /* Botões Padrão */
    div.stButton > button {
        background-color: #FF8C00 !important;
        color: white !important;
        border-radius: 12px !important;
        font-weight: 900 !important;
        height: 50px !important;
        width: 100% !important;
        border: none !important;
    }

    /* Esconder Sidebar */
    [data-testid="stSidebar"] { display: none; }
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 4. MENU SUPERIOR DIREITO (ENGRENAGEM DISCRETA) ---
col_logo, col_admin = st.columns([6, 1])
with col_admin:
    with st.popover("⚙️"):
        st.caption("Acesso Restrito")
        acesso = st.text_input("Senha/Token", type="password")
        if acesso == "admin777":
            if st.button("Abrir Admin"):
                st.session_state.etapa = 'admin'
                st.rerun()

# --- 5. FLUXO ---

# TELA ADMIN
if st.session_state.etapa == 'admin':
    st.title("📊 Gestão GeralJá")
    st.metric("Faturamento", f"R$ {st.session_state.lucro_plataforma:.2f}")
    if st.button("⬅ VOLTAR"):
        st.session_state.etapa = 'busca'
        st.rerun()

# TELA DE BUSCA
elif st.session_state.etapa == 'busca':
    st.markdown("""
        <div class="logo-container">
            <span class="logo-geral">GERAL</span><span class="logo-ja">JÁ</span>
            <p style="color: #666; margin-top: -10px;"><b>Grajaú:</b> Soluções em um clique.</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        servico = st.selectbox("O que você precisa?", [""] + LISTA_PROS)
        rua = st.text_input("📍 Seu Endereço")
        
        if st.button("ATIVAR RADAR AGORA"):
            if servico and rua:
                st.session_state.servico_busca = servico
                st.session_state.etapa = 'resultado'
                st.rerun()
            else:
                st.warning("Preencha os dados.")

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🆘 SUPORTE 24H"):
        st.toast("Chamando suporte...", icon="💬")

# TELA RESULTADO
elif st.session_state.etapa == 'resultado':
    st.markdown("### 📍 Profissional Localizado")
    # Mapa Estático
    st.image(f"https://api.mapbox.com/styles/v1/mapbox/streets-v11/static/-46.6682,-23.7721,13/600x200?access_token=pk.eyJ1IjoiZ3VpZG94IiwiYSI6ImNrZnduZnR4MDBhNnoycnBnbm9idG9yejkifQ.7Wp6M_2yA6_z_rG-vH0Z6A")
    
    preco = random.randint(180, 350)
    st.markdown(f"""
        <div style="background:#f9f9f9; padding:20px; border-radius:20px; border:1px solid #eee; text-align:center;">
            <h2 style="color:#0047AB; margin:0;">Bony Silva</h2>
            <p>Especialista em {st.session_state.servico_busca}</p>
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
    
    if st.button("✅ JÁ REALIZEI O PAGAMENTO"):
        st.session_state.lucro_plataforma += (val * 0.10)
        st.session_state.pedidos_concluidos += 1
        st.session_state.etapa = 'busca'
        st.balloons()
        st.rerun()
