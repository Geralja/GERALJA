import streamlit as st
import random
import datetime

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="GeralJá | Social", layout="centered", initial_sidebar_state="collapsed")

# --- 2. INICIALIZAÇÃO DE VARIÁVEIS ---
if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'
if 'lucro_plataforma' not in st.session_state: st.session_state.lucro_plataforma = 0.0
if 'pedidos_concluidos' not in st.session_state: st.session_state.pedidos_concluidos = 0
if 'posts' not in st.session_state: 
    st.session_state.posts = [{"user": "Admin", "msg": "Bem-vindos ao GeralJá Grajaú! 🚀", "data": "26/12"}]

CHAVE_PIX_ALERATORIA = "09be938c-ee95-469f-b221-a3beea63964b"
LISTA_PROS = sorted(["Pintor", "Eletricista", "Encanador", "Diarista", "Pedreiro", "Montador de Móveis", "Mecânico", "Jardineiro", "Chaveiro"])

# --- 3. CSS "FORÇA BRUTA" (REMOVE FUNDO PRETO E IGUALA BOTÕES) ---
st.markdown("""
    <style>
    /* Força o fundo branco em tudo, inclusive nas bordas externas */
    .stApp, .stAppViewContainer, .stAppMainContent {
        background-color: #FFFFFF !important;
        color: #333333 !important;
    }
    
    /* Remove sombras e bordas pretas de containers */
    [data-testid="stVerticalBlock"] { background-color: transparent !important; }

    /* LOGO COLORIDO */
    .logo-container { text-align: center; margin-top: 0px; padding-bottom: 10px; }
    .logo-geral { color: #0047AB; font-size: 50px; font-weight: 900; }
    .logo-ja { color: #FF8C00; font-size: 50px; font-weight: 900; }

    /* BOTÕES IGUAIS (LARGURA TOTAL E ALTURA FIXA) */
    div.stButton > button {
        background-color: #FF8C00 !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        height: 55px !important;
        width: 100% !important;
        border: none !important;
        margin-bottom: 10px !important;
        display: block !important;
    }

    /* Estilo dos cards da Rede Social */
    .post-card {
        background: #f1f3f5;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #0047AB;
        margin-bottom: 12px;
        color: #333;
    }

    /* Esconde elementos nativos que podem causar faixas pretas */
    header, footer, [data-testid="stSidebar"] { visibility: hidden; height: 0; }
    </style>
""", unsafe_allow_html=True)

# --- 4. MENU SUPERIOR ☰ ---
col_v, col_menu = st.columns([5, 1.5])
with col_menu:
    with st.popover("☰ MENU"):
        st.write("📍 **Navegação**")
        if st.button("🏠 Início"): 
            st.session_state.etapa = 'busca'
            st.rerun()
        if st.button("👥 Rede Social"): 
            st.session_state.etapa = 'social'
            st.rerun()
        st.divider()
        st.caption("Admin")
        senha_admin = st.text_input("Senha", type="password", key="nav_pwd")
        if senha_admin == "admin777":
            if st.button("Abrir Painel"):
                st.session_state.etapa = 'admin'
                st.rerun()

# --- 5. ROTEAMENTO ---

# TELA REDE SOCIAL
if st.session_state.etapa == 'social':
    st.markdown("<h2 style='color:#0047AB; text-align:center;'>Comunidade Grajaú</h2>", unsafe_allow_html=True)
    
    with st.expander("📝 Nova Publicação"):
        n = st.text_input("Nome")
        t = st.text_area("Mensagem")
        if st.button("Publicar"):
            if n and t:
                st.session_state.posts.insert(0, {"user": n, "msg": t, "data": datetime.datetime.now().strftime("%d/%m")})
                st.rerun()

    for p in st.session_state.posts:
        st.markdown(f"""<div class="post-card"><b>{p['user']}</b> <small style='color:gray;'>• {p['data']}</small><br>{p['msg']}</div>""", unsafe_allow_html=True)

# TELA ADMIN
elif st.session_state.etapa == 'admin':
    st.markdown("<h2 style='color:#0047AB;'>📊 Painel de Controle</h2>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.metric("Lucro", f"R$ {st.session_state.get('lucro_plataforma', 0):.2f}")
    c2.metric("Pedidos", st.session_state.get('pedidos_concluidos', 0))
    if st.button("⬅ VOLTAR"):
        st.session_state.etapa = 'busca'; st.rerun()

# TELA INICIAL
elif st.session_state.etapa == 'busca':
    st.markdown("""
        <div class="logo-container">
            <span class="logo-geral">GERAL</span><span class="logo-ja">JÁ</span>
            <p style="color: #666; margin-top: -10px;">O bairro na palma da mão.</p>
        </div>
    """, unsafe_allow_html=True)
    
    servico = st.selectbox("O que você precisa?", [""] + LISTA_PROS)
    rua = st.text_input("📍 Seu Endereço")
    
    if st.button("🚀 BUSCAR AGORA"):
        if servico and rua:
            st.session_state.servico_busca = servico
            st.session_state.etapa = 'resultado'
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🆘 SUPORTE 24H"):
        st.toast("Chamando...")

# RESULTADOS
elif st.session_state.etapa == 'resultado':
    st.image("https://api.mapbox.com/styles/v1/mapbox/streets-v11/static/-46.6682,-23.7721,13/600x200?access_token=pk.eyJ1IjoiZ3VpZG94IiwiYSI6ImNrZnduZnR4MDBhNnoycnBnbm9idG9yejkifQ.7Wp6M_2yA6_z_rG-vH0Z6A")
    st.info(f"Localizamos especialistas em {st.session_state.servico_busca}")
    if st.button("CONTRATAR BONY SILVA"): 
        st.session_state.etapa = 'pagamento'; st.rerun()
    if st.button("⬅ VOLTAR"): 
        st.session_state.etapa = 'busca'; st.rerun()

# PAGAMENTO
elif st.session_state.etapa == 'pagamento':
    st.markdown("<h3 style='text-align:center;'>Pagamento Pix</h3>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style="background:#f8f9fa; padding:20px; border-radius:15px; text-align:center; color:black; border: 1px solid #ddd;">
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={CHAVE_PIX_ALERATORIA}">
            <p style='font-size:10px;'>{CHAVE_PIX_ALERATORIA}</p>
        </div>
    """, unsafe_allow_html=True)
    if st.button("✅ JÁ PAGUEI"): 
        st.session_state.lucro_plataforma += 25.0
        st.session_state.pedidos_concluidos += 1
        st.session_state.etapa = 'busca'; st.balloons(); st.rerun()
