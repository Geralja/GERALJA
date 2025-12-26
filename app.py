import streamlit as st
import random
import datetime

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="GeralJá | Social", layout="centered", initial_sidebar_state="collapsed")

# --- 2. BLOCO DE SEGURANÇA (INICIALIZAÇÃO DE VARIÁVEIS) ---
# Isso garante que o erro de 'AttributeError' não aconteça mais
if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'
if 'lucro_plataforma' not in st.session_state: st.session_state.lucro_plataforma = 0.0
if 'pedidos_concluidos' not in st.session_state: st.session_state.pedidos_concluidos = 0
if 'posts' not in st.session_state: 
    st.session_state.posts = [
        {"user": "Admin", "msg": "Bem-vindos à Comunidade GeralJá Grajaú! 🚀", "data": "26/12"}
    ]

CHAVE_PIX_ALERATORIA = "09be938c-ee95-469f-b221-a3beea63964b"
LISTA_PROS = sorted(["Pintor", "Eletricista", "Encanador", "Diarista", "Pedreiro", "Montador de Móveis", "Mecânico", "Jardineiro", "Chaveiro"])

# --- 3. CSS (VISUAL CLEAN + REDE SOCIAL) ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; color: #333333 !important; }
    
    .logo-container { text-align: center; margin-top: 10px; }
    .logo-geral { color: #0047AB; font-size: 55px; font-weight: 900; }
    .logo-ja { color: #FF8C00; font-size: 55px; font-weight: 900; }

    div.stButton > button {
        background-color: #FF8C00 !important;
        color: white !important;
        border-radius: 12px !important;
        font-weight: 900 !important;
        height: 50px !important;
        width: 100% !important;
        border: none !important;
    }

    .post-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #0047AB;
        margin-bottom: 10px;
        color: #333;
    }

    [data-testid="stSidebar"] { display: none; }
    header, footer { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 4. MENU SUPERIOR ☰ ---
col_v, col_menu = st.columns([6, 1.2])
with col_menu:
    with st.popover("☰"):
        if st.button("🏠 Início"): 
            st.session_state.etapa = 'busca'
            st.rerun()
        if st.button("👥 Rede Social"): 
            st.session_state.etapa = 'social'
            st.rerun()
        st.divider()
        st.caption("Acesso Privado")
        senha_admin = st.text_input("Senha", type="password", key="pwd_nav")
        if senha_admin == "admin777":
            if st.button("Abrir Admin"):
                st.session_state.etapa = 'admin'
                st.rerun()

# --- 5. ROTEAMENTO DE TELAS ---

# TELA REDE SOCIAL
if st.session_state.etapa == 'social':
    st.markdown("<h2 style='color:#0047AB;'>👥 Comunidade Grajaú</h2>", unsafe_allow_html=True)
    
    with st.expander("📝 Criar nova publicação"):
        nome_user = st.text_input("Seu Nome")
        texto_user = st.text_area("O que deseja compartilhar?")
        if st.button("Publicar Agora"):
            if nome_user and texto_user:
                novo = {"user": nome_user, "msg": texto_user, "data": datetime.datetime.now().strftime("%d/%m")}
                st.session_state.posts.insert(0, novo)
                st.rerun()

    for p in st.session_state.posts:
        st.markdown(f"""<div class="post-card"><b>{p['user']}</b> <small style='color:gray;'>• {p['data']}</small><br>{p['msg']}</div>""", unsafe_allow_html=True)

# TELA ADMIN (ONDE DAVA O ERRO)
elif st.session_state.etapa == 'admin':
    st.markdown("<h2 style='color:#0047AB;'>📊 Gestão GeralJá</h2>", unsafe_allow_html=True)
    
    # Adicionando verificação extra de segurança
    lucro = st.session_state.get('lucro_plataforma', 0.0)
    vendas = st.session_state.get('pedidos_concluidos', 0)
    
    col1, col2 = st.columns(2)
    col1.metric("Faturamento (10%)", f"R$ {lucro:.2f}")
    col2.metric("Serviços Concluídos", vendas)
    
    if st.button("⬅ Voltar para Início"):
        st.session_state.etapa = 'busca'
        st.rerun()

# TELA INICIAL (BUSCA)
elif st.session_state.etapa == 'busca':
    st.markdown("""
        <div class="logo-container">
            <span class="logo-geral">GERAL</span><span class="logo-ja">JÁ</span>
            <p style="color: #666; margin-top: -10px;">Soluções rápidas no bairro.</p>
        </div>
    """, unsafe_allow_html=True)
    
    servico = st.selectbox("O que você precisa?", [""] + LISTA_PROS)
    rua = st.text_input("📍 Seu Endereço")
    
    if st.button("ATIVAR RADAR AGORA"):
        if servico and rua:
            st.session_state.servico_busca = servico
            st.session_state.etapa = 'resultado'
            st.rerun()

# TELAS DE RESULTADO E PAGAMENTO
elif st.session_state.etapa == 'resultado':
    st.image("https://api.mapbox.com/styles/v1/mapbox/streets-v11/static/-46.6682,-23.7721,13/600x200?access_token=pk.eyJ1IjoiZ3VpZG94IiwiYSI6ImNrZnduZnR4MDBhNnoycnBnbm9idG9yejkifQ.7Wp6M_2yA6_z_rG-vH0Z6A")
    st.success(f"Profissional localizado para {st.session_state.servico_busca}!")
    if st.button("Contratar Profissional"): 
        st.session_state.etapa = 'pagamento'
        st.rerun()
    if st.button("Voltar"): 
        st.session_state.etapa = 'busca'
        st.rerun()

elif st.session_state.etapa == 'pagamento':
    st.markdown(f"""
        <div style="background:#f1f1f1; padding:20px; border-radius:15px; text-align:center; color:black;">
            <h3>Pague via Pix</h3>
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={CHAVE_PIX_ALERATORIA}">
            <p><small>{CHAVE_PIX_ALERATORIA}</small></p>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Confirmar Pagamento"): 
        st.session_state.lucro_plataforma += 25.0 # Exemplo de taxa fixa
        st.session_state.pedidos_concluidos += 1
        st.session_state.etapa = 'busca'
        st.balloons()
        st.rerun()
