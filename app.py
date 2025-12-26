import streamlit as st
import random
import datetime
import time

# --- 1. CONFIGURAÇÃO DE ELITE ---
st.set_page_config(
    page_title="GeralJá | Elite HUB",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. INICIALIZAÇÃO E PERSISTÊNCIA ---
if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'
if 'lucro_plataforma' not in st.session_state: st.session_state.lucro_plataforma = 0.0
if 'pedidos_concluidos' not in st.session_state: st.session_state.pedidos_concluidos = 0
if 'posts' not in st.session_state: 
    st.session_state.posts = [{"user": "Equipe GeralJá", "msg": "Conectando o Grajaú aos melhores profissionais! 🚀", "data": "Agora"}]

LISTA_PROS = sorted(["Pintor", "Eletricista", "Encanador", "Diarista", "Pedreiro", "Montador de Móveis", "Mecânico", "Jardineiro", "Chaveiro"])
CHAVE_PIX = "09be938c-ee95-469f-b221-a3beea63964b"

# --- 3. CSS ULTRA MODERNO (DESIGN SYSTEM) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #FFFFFF !important;
        font-family: 'Inter', sans-serif;
    }

    /* Logo com Efeito de Profundidade */
    .logo-container { text-align: center; padding: 20px 0; margin-top: -20px; }
    .logo-geral { color: #0047AB; font-size: 58px; font-weight: 900; letter-spacing: -2px; }
    .logo-ja { color: #FF8C00; font-size: 58px; font-weight: 900; letter-spacing: -2px; }

    /* Inputs e Selects Modernos */
    .stSelectbox div[data-baseweb="select"] { border-radius: 12px !important; }
    .stTextInput input { border-radius: 12px !important; }

    /* Botão com Gradiente e Sombra */
    div.stButton > button {
        background: linear-gradient(90deg, #FF8C00 0%, #F39C12 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 14px !important;
        font-weight: 700 !important;
        height: 58px !important;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 140, 0, 0.2) !important;
    }
    
    div.stButton > button:active { transform: scale(0.98); }

    /* Sidebar Clean */
    [data-testid="stSidebar"] { background-color: #FDFDFD !important; border-right: 1px solid #F0F0F0; }
    
    /* Esconder Header/Footer */
    header, footer { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 4. BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.markdown("<h2 style='color:#0047AB;'>Navegação</h2>", unsafe_allow_html=True)
    if st.button("🏠 Home / Buscar"): st.session_state.etapa = 'busca'; st.rerun()
    if st.button("👥 Comunidade"): st.session_state.etapa = 'social'; st.rerun()
    if st.button("🆘 Suporte Direto"): st.toast("Abrindo WhatsApp..."); time.sleep(1)
    
    st.divider()
    with st.expander("🔐 Nodo Admin"):
        pwd = st.text_input("Acesso", type="password")
        if pwd == "admin777":
            if st.button("Ver Relatórios"): st.session_state.etapa = 'admin'; st.rerun()

# --- 5. LÓGICA DE TELAS ---

# TELA DE BUSCA (HOME)
if st.session_state.etapa == 'busca':
    st.markdown("""
        <div class="logo-container">
            <span class="logo-geral">GERAL</span><span class="logo-ja">JÁ</span>
            <p style="color: #888; font-weight: 500; margin-top: -10px;">Elite HUB Grajaú</p>
        </div>
    """, unsafe_allow_html=True)

    servico = st.selectbox("O que você precisa hoje?", [""] + LISTA_PROS)
    rua = st.text_input("📍 Localização (Rua ou Ponto de Ref.)")

    if st.button("🚀 ENCONTRAR PROFISSIONAL AGORA"):
        if servico and rua:
            with st.status("📡 Escaneando profissionais na região...", expanded=True) as status:
                st.write("Verificando disponibilidade...")
                time.sleep(1)
                st.write("Validando avaliações no Grajaú...")
                time.sleep(1)
                status.update(label="✅ Especialista Encontrado!", state="complete", expanded=False)
            
            st.session_state.servico_busca = servico
            st.session_state.etapa = 'resultado'
            st.rerun()
        else:
            st.error("Preencha o serviço e o endereço.")

# TELA COMUNIDADE (SOCIAL)
elif st.session_state.etapa == 'social':
    st.markdown("<h2 style='color:#0047AB;'>👥 Comunidade</h2>", unsafe_allow_html=True)
    with st.chat_message("user"):
        n = st.text_input("Seu Nome")
        t = st.text_area("O que está acontecendo no bairro?")
        if st.button("Postar na Rede"):
            if n and t:
                st.session_state.posts.insert(0, {"user": n, "msg": t, "data": "Agora"})
                st.rerun()

    for p in st.session_state.posts:
        with st.container():
            st.markdown(f"""
                <div style="background:#F8F9FB; padding:15px; border-radius:15px; border:1px solid #EEE; margin-bottom:10px;">
                    <b style="color:#0047AB;">{p['user']}</b> <small style="color:#AAA;">• {p['data']}</small><br>
                    <span style="color:#444;">{p['msg']}</span>
                </div>
            """, unsafe_allow_html=True)

# TELA ADMIN
elif st.session_state.etapa == 'admin':
    st.markdown("<h2 style='color:#0047AB;'>📊 Dashboard de Elite</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    col1.metric("Receita Nodo", f"R$ {st.session_state.lucro_plataforma:.2f}", "+ 10%")
    col2.metric("Serviços Hoje", st.session_state.pedidos_concluidos)
    
    st.write("### Últimas Transações")
    st.dataframe({"Serviço": ["Eletricista", "Pintor"], "Status": ["Pago", "Pendente"], "Valor": [250, 180]})
    
    if st.button("⬅ Voltar"): st.session_state.etapa = 'busca'; st.rerun()

# RESULTADO E PAGAMENTO
elif st.session_state.etapa == 'resultado':
    st.markdown("### 🏆 Melhor Avaliado Encontrado")
    st.image("https://api.mapbox.com/styles/v1/mapbox/streets-v11/static/-46.6682,-23.7721,13/600x200?access_token=pk.eyJ1IjoiZ3VpZG94IiwiYSI6ImNrZnduZnR4MDBhNnoycnBnbm9idG9yejkifQ.7Wp6M_2yA6_z_rG-vH0Z6A")
    st.info(f"O Sr. Bony Silva está disponível para {st.session_state.servico_busca}")
    if st.button("CONTRATAR AGORA"): st.session_state.etapa = 'pagamento'; st.rerun()
    if st.button("Voltar"): st.session_state.etapa = 'busca'; st.rerun()

elif st.session_state.etapa == 'pagamento':
    st.markdown("<h3 style='text-align:center;'>Check-out Seguro</h3>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style="background:#FFF; padding:20px; border-radius:20px; text-align:center; border: 2px solid #FF8C00;">
            <p style='color:#555;'>Total do Serviço: <b>R$ 250,00</b></p>
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={CHAVE_PIX}">
            <p style='font-size:11px; color:#888; margin-top:10px;'>Copia e Cola: {CHAVE_PIX}</p>
        </div>
    """, unsafe_allow_html=True)
    if st.button("✅ PAGAMENTO REALIZADO"):
        st.session_state.lucro_plataforma += 25.0
        st.session_state.pedidos_concluidos += 1
        st.session_state.etapa = 'busca'; st.balloons(); st.rerun()
