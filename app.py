import streamlit as st
import random
import datetime
import time

# --- 1. CONFIGURAÇÃO DE ALTA PERFORMANCE ---
st.set_page_config(
    page_title="GeralJá | Oficial",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. INICIALIZAÇÃO BLINDADA (Garante que nada suma) ---
def inicializar_estados():
    variaveis = {
        'etapa': 'busca',
        'lucro_plataforma': 0.0,
        'pedidos_concluidos': 0,
        'servico_busca': '',
        'posts': [{"user": "Sistema", "msg": "Bem-vindo ao Elite HUB Grajaú!", "data": "26/12"}]
    }
    for var, valor in variaveis.items():
        if var not in st.session_state:
            st.session_state[var] = valor

inicializar_estados()

LISTA_PROS = sorted(["Pintor", "Eletricista", "Encanador", "Diarista", "Pedreiro", "Montador de Móveis", "Mecânico", "Jardineiro", "Chaveiro"])
CHAVE_PIX = "09be938c-ee95-469f-b221-a3beea63964b"

# --- 3. CSS UNIFICADO (Fundo Branco e Botões Padronizados) ---
st.markdown("""
    <style>
    /* Reset de Fundo */
    .stApp { background-color: #FFFFFF !important; }
    
    /* Logo Moderno */
    .logo-container { text-align: center; margin-bottom: 25px; padding-top: 10px; }
    .logo-geral { color: #0047AB; font-size: 52px; font-weight: 900; letter-spacing: -1.5px; }
    .logo-ja { color: #FF8C00; font-size: 52px; font-weight: 900; letter-spacing: -1.5px; }

    /* Botões de Ação */
    div.stButton > button {
        background: #FF8C00 !important;
        color: white !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        height: 55px !important;
        width: 100% !important;
        border: none !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }

    /* Cards da Rede Social */
    .post-card {
        background: #FDFDFD;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #EEE;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }

    /* Ocultar Lixo Visual */
    header, footer { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 4. MENU LATERAL (ORGANIZADO) ---
with st.sidebar:
    st.markdown("<h2 style='color:#0047AB;'>📌 Menu</h2>", unsafe_allow_html=True)
    if st.button("🔍 Buscar Profissional"):
        st.session_state.etapa = 'busca'
        st.rerun()
    if st.button("👥 Rede Social"):
        st.session_state.etapa = 'social'
        st.rerun()
    
    st.divider()
    with st.expander("🛡️ Área Administrativa"):
        acesso = st.text_input("Senha", type="password", key="admin_key")
        if acesso == "admin777":
            if st.button("Entrar no Painel"):
                st.session_state.etapa = 'admin'
                st.rerun()

# --- 5. ROTEAMENTO DE TELAS ---

# --- TELA: BUSCA (HOME) ---
if st.session_state.etapa == 'busca':
    st.markdown("""
        <div class="logo-container">
            <span class="logo-geral">GERAL</span><span class="logo-ja">JÁ</span>
            <p style="color: #666; margin-top: -10px;">Encontre o que precisa no Grajaú</p>
        </div>
    """, unsafe_allow_html=True)
    
    servico = st.selectbox("O que você procura?", [""] + LISTA_PROS)
    rua = st.text_input("📍 Seu Endereço ou Referência")
    
    if st.button("PESQUISAR AGORA"):
        if servico and rua:
            st.session_state.servico_busca = servico
            st.session_state.etapa = 'resultado'
            st.rerun()
        else:
            st.warning("⚠️ Preencha todos os campos.")

# --- TELA: REDE SOCIAL ---
elif st.session_state.etapa == 'social':
    st.markdown("<h2 style='color:#0047AB;'>👥 Comunidade Grajaú</h2>", unsafe_allow_html=True)
    
    with st.form("novo_post", clear_on_submit=True):
        nome = st.text_input("Seu Nome")
        mensagem = st.text_area("Sua mensagem...")
        if st.form_submit_button("Publicar"):
            if nome and mensagem:
                novo = {"user": nome, "msg": mensagem, "data": datetime.datetime.now().strftime("%d/%m %H:%M")}
                st.session_state.posts.insert(0, novo)
                st.rerun()

    for post in st.session_state.posts:
        st.markdown(f"""
            <div class="post-card">
                <b>{post['user']}</b> <small style='color:gray;'>• {post['data']}</small><br>
                <div style="margin-top:5px; color:#444;">{post['msg']}</div>
            </div>
        """, unsafe_allow_html=True)

# --- TELA: ADMIN ---
elif st.session_state.etapa == 'admin':
    st.markdown("<h2 style='color:#0047AB;'>📊 Painel Administrativo</h2>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.metric("Lucro Nodo (10%)", f"R$ {st.session_state.lucro_plataforma:.2f}")
    c2.metric("Total de Pedidos", st.session_state.pedidos_concluidos)
    
    if st.button("⬅ Sair do Painel"):
        st.session_state.etapa = 'busca'
        st.rerun()

# --- TELA: RESULTADO ---
elif st.session_state.etapa == 'resultado':
    st.markdown(f"### 📍 Especialista em {st.session_state.servico_busca}")
    st.image("https://api.mapbox.com/styles/v1/mapbox/streets-v11/static/-46.6682,-23.7721,13/600x200?access_token=pk.eyJ1IjoiZ3VpZG94IiwiYSI6ImNrZnduZnR4MDBhNnoycnBnbm9idG9yejkifQ.7Wp6M_2yA6_z_rG-vH0Z6A")
    
    st.markdown("""
        <div style="background:#f9f9f9; padding:15px; border-radius:15px; border:1px solid #ddd; text-align:center; margin-top:10px;">
            <h3 style="margin:0; color:#0047AB;">Bony Silva</h3>
            <p style="color:#555;">⭐ 4.9 (120 serviços realizados)</p>
            <h2 style="color:#FF8C00;">R$ 250,00</h2>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("CONTRATAR AGORA"):
        st.session_state.etapa = 'pagamento'
        st.rerun()
    if st.button("⬅ Voltar"):
        st.session_state.etapa = 'busca'; st.rerun()

# --- TELA: PAGAMENTO ---
elif st.session_state.etapa == 'pagamento':
    st.markdown("<h3 style='text-align:center;'>Pagamento via Pix</h3>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style="background:white; padding:25px; border-radius:20px; text-align:center; border: 2px solid #FF8C00;">
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={CHAVE_PIX}">
            <p style='margin-top:10px; font-size:12px; color:gray;'>Copia e Cola:<br><b>{CHAVE_PIX}</b></p>
        </div>
    """, unsafe_allow_html=True)
    if st.button("✅ JÁ REALIZEI O PAGAMENTO"):
        st.session_state.lucro_plataforma += 25.0
        st.session_state.pedidos_concluidos += 1
        st.session_state.etapa = 'busca'
        st.balloons()
        st.rerun()
