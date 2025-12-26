import streamlit as st
import datetime
import time

# --- 1. CONFIGURAÇÃO DE NÚCLEO (FORÇA BARRA LATERAL) ---
st.set_page_config(
    page_title="GeralJá | Grajaú",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="expanded" # Força o menu a iniciar aberto para o usuário ver
)

# --- 2. MOTOR DE ESTADO BLINDADO ---
if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'
if 'lucro' not in st.session_state: st.session_state.lucro = 0.0
if 'vendas' not in st.session_state: st.session_state.vendas = 0
if 'posts' not in st.session_state: 
    st.session_state.posts = [{"user": "Admin", "msg": "Sistema GeralJá Online! 🚀", "data": "26/12"}]

CHAVE_PIX = "09be938c-ee95-469f-b221-a3beea63964b"

# --- 3. CSS ANTI-BUG (FUNDO BRANCO TOTAL) ---
st.markdown("""
    <style>
    /* Forçar fundo branco e remover faixas pretas */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMainViewContainer"] {
        background-color: #FFFFFF !important;
        color: #333333 !important;
    }

    /* Logo Central */
    .logo-box { text-align: center; padding: 20px 0; margin-top: -30px; }
    .azul { color: #0047AB; font-size: 52px; font-weight: 900; }
    .laranja { color: #FF8C00; font-size: 52px; font-weight: 900; }

    /* Botões Padronizados */
    .stButton > button {
        background-color: #FF8C00 !important;
        color: white !important;
        border-radius: 12px !important;
        height: 55px !important;
        width: 100% !important;
        font-weight: bold !important;
        border: none !important;
    }
    
    /* Esconder cabeçalhos nativos */
    header, footer { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 4. MENU LATERAL (Sincronizado) ---
with st.sidebar:
    st.markdown("<h1 style='color:#0047AB;'>GeralJá</h1>", unsafe_allow_html=True)
    st.write("---")
    if st.button("🏠 Início / Busca", key="menu_home"):
        st.session_state.etapa = 'busca'
        st.rerun()
    if st.button("👥 Rede Social", key="menu_social"):
        st.session_state.etapa = 'social'
        st.rerun()
    
    st.write("---")
    with st.expander("🔐 Administração"):
        pwd = st.text_input("Senha", type="password", key="pwd_admin")
        if pwd == "admin777":
            if st.button("Abrir Painel", key="btn_go_admin"):
                st.session_state.etapa = 'admin'
                st.rerun()

# --- 5. ROTEAMENTO DE TELAS ---

# TELA: BUSCA
if st.session_state.etapa == 'busca':
    st.markdown('<div class="logo-box"><span class="azul">GERAL</span><span class="laranja">JÁ</span></div>', unsafe_allow_html=True)
    
    servico = st.selectbox("O que você precisa hoje?", ["", "Pintor", "Eletricista", "Encanador", "Diarista", "Pedreiro", "Mecânico", "Montador"], key="sel_serv")
    rua = st.text_input("📍 Localização no Grajaú", key="input_rua")
    
    if st.button("🚀 PESQUISAR AGORA", key="btn_main_search"):
        if servico and rua:
            st.session_state.servico_busca = servico
            st.session_state.etapa = 'resultado'
            st.rerun()
        else:
            st.warning("Preencha o serviço e o endereço.")

# TELA: REDE SOCIAL
elif st.session_state.etapa == 'social':
    st.markdown("<h2 style='color:#0047AB;'>👥 Comunidade Grajaú</h2>", unsafe_allow_html=True)
    with st.form("form_social"):
        u = st.text_input("Seu Nome")
        m = st.text_area("O que quer postar?")
        if st.form_submit_button("Publicar"):
            if u and m:
                st.session_state.posts.insert(0, {"user": u, "msg": m, "data": datetime.datetime.now().strftime("%d/%m")})
                st.rerun()

    for p in st.session_state.posts:
        st.markdown(f"""<div style="background:#F0F2F6; padding:15px; border-radius:10px; margin-bottom:10px; border-left: 5px solid #0047AB;">
            <b>{p['user']}</b> <small>• {p['data']}</small><br>{p['msg']}</div>""", unsafe_allow_html=True)

# TELA: ADMIN
elif st.session_state.etapa == 'admin':
    st.title("📊 Relatório Nodo")
    col1, col2 = st.columns(2)
    col1.metric("Faturamento", f"R$ {st.session_state.lucro:.2f}")
    col2.metric("Vendas", st.session_state.vendas)
    if st.button("⬅ Sair", key="btn_exit_admin"):
        st.session_state.etapa = 'busca'
        st.rerun()

# TELA: RESULTADO (MAPA CORRIGIDO)
elif st.session_state.etapa == 'resultado':
    st.markdown(f"### 📍 Profissional para {st.session_state.servico_busca}")
    
    # Mapa Estático com Pin Laranja
    map_url = "https://api.mapbox.com/styles/v1/mapbox/streets-v11/static/pin-s+ff8c00(-46.6682,-23.7721)/-46.6682,-23.7721,14/600x250?access_token=pk.eyJ1IjoiZ3VpZG94IiwiYSI6ImNrZnduZnR4MDBhNnoycnBnbm9idG9yejkifQ.7Wp6M_2yA6_z_rG-vH0Z6A"
    
    st.markdown(f'<img src="{map_url}" style="width:100%; border-radius:15px; border: 1px solid #ddd;">', unsafe_allow_html=True)
    
    st.markdown("""
        <div style="background:#f9f9f9; padding:15px; border-radius:15px; text-align:center; margin-top:10px;">
            <h3 style="color:#0047AB; margin:0;">Bony Silva</h3>
            <p>⭐ 4.9 | Chegada em 15 min</p>
            <h2 style="color:#FF8C00;">R$ 250,00</h2>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("✅ CONTRATAR", key="btn_confirm_pay"):
        st.session_state.etapa = 'pagamento'
        st.rerun()
    if st.button("⬅ Voltar", key="btn_back_res"):
        st.session_state.etapa = 'busca'; st.rerun()

# TELA: PAGAMENTO
elif st.session_state.etapa == 'pagamento':
    st.markdown("<h3 style='text-align:center;'>Pagamento Pix</h3>", unsafe_allow_html=True)
    st.markdown(f"""<div style='text-align:center; border:2px solid #FF8C00; padding:20px; border-radius:20px; background: white;'>
        <img src='https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={CHAVE_PIX}'>
        <p style='color:black;'><br><b>Chave:</b> {CHAVE_PIX}</p></div>""", unsafe_allow_html=True)
    
    if st.button("✅ JÁ PAGUEI", key="btn_finish"):
        st.session_state.lucro += 25.0
        st.session_state.vendas += 1
        st.session_state.etapa = 'busca'
        st.balloons()
        st.rerun()
