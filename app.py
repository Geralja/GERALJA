import streamlit as st
import random
import datetime

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="GeralJá | Social", layout="centered", initial_sidebar_state="collapsed")

# --- 2. BANCO DE DADOS (SESSÃO) ---
if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'
if 'posts' not in st.session_state: 
    st.session_state.posts = [
        {"user": "João Silva", "msg": "Recomendo o Bony! Eletricista nota 10 aqui no centrão.", "data": "25/12"},
        {"user": "Maria Souza", "msg": "Alguém conhece um bom encanador disponível agora?", "data": "26/12"}
    ]

CHAVE_PIX_ALERATORIA = "09be938c-ee95-469f-b221-a3beea63964b"
LISTA_PROS = sorted(["Pintor", "Eletricista", "Encanador", "Diarista", "Pedreiro", "Montador de Móveis", "Mecânico", "Jardineiro", "Chaveiro"])

# --- 3. CSS (BRANCO + ÍCONE ☰) ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; color: #333333 !important; }
    
    /* LOGO */
    .logo-container { text-align: center; margin-top: 10px; }
    .logo-geral { color: #0047AB; font-size: 55px; font-weight: 900; }
    .logo-ja { color: #FF8C00; font-size: 55px; font-weight: 900; }

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

    /* CARD DE POST DA REDE SOCIAL */
    .post-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #0047AB;
        margin-bottom: 10px;
    }

    [data-testid="stSidebar"] { display: none; }
    header, footer { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 4. MENU SUPERIOR (AS 3 BARRAS ☰) ---
col_v, col_menu = st.columns([6, 1])
with col_menu:
    with st.popover("☰"):
        st.subheader("Navegação")
        if st.button("🏠 Início"): st.session_state.etapa = 'busca'; st.rerun()
        if st.button("👥 Rede Social"): st.session_state.etapa = 'social'; st.rerun()
        st.divider()
        st.caption("Acesso Administrativo")
        senha = st.text_input("Senha", type="password")
        if senha == "admin777":
            if st.button("Abrir Painel"): st.session_state.etapa = 'admin'; st.rerun()

# --- 5. ROTEAMENTO DE TELAS ---

# TELA REDE SOCIAL
if st.session_state.etapa == 'social':
    st.markdown("<h2 style='color:#0047AB;'>👥 Comunidade Grajaú</h2>", unsafe_allow_html=True)
    
    # Criar novo post
    with st.expander("📝 Criar nova publicação"):
        nome = st.text_input("Seu Nome")
        texto = st.text_area("O que deseja compartilhar?")
        if st.button("Publicar"):
            if nome and texto:
                novo_post = {"user": nome, "msg": texto, "data": datetime.datetime.now().strftime("%d/%m")}
                st.session_state.posts.insert(0, novo_post)
                st.rerun()

    # Feed de notícias
    for post in st.session_state.posts:
        st.markdown(f"""
            <div class="post-card">
                <b>{post['user']}</b> <small style='color:gray;'>• {post['data']}</small><br>
                {post['msg']}
            </div>
        """, unsafe_allow_html=True)

# TELA ADMIN
elif st.session_state.etapa == 'admin':
    st.title("📊 Gestão GeralJá")
    st.metric("Faturamento", f"R$ {st.session_state.lucro_plataforma:.2f}")
    if st.button("⬅ Voltar"): st.session_state.etapa = 'busca'; st.rerun()

# TELA DE BUSCA (HOME)
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

# TELAS DE RESULTADO E PAGAMENTO (SIMPLIFICADAS PARA FOCO NA REDE)
elif st.session_state.etapa == 'resultado':
    st.success(f"Profissional localizado para {st.session_state.servico_busca}!")
    if st.button("Contratar"): st.session_state.etapa = 'pagamento'; st.rerun()
    if st.button("Voltar"): st.session_state.etapa = 'busca'; st.rerun()

elif st.session_state.etapa == 'pagamento':
    st.info(f"Escaneie o QR Code Pix: {CHAVE_PIX_ALERATORIA}")
    if st.button("Concluir"): st.session_state.etapa = 'busca'; st.rerun()
