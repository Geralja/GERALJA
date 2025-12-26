import streamlit as st
import datetime

# --- 1. CONFIGURAÇÃO DE NÚCLEO ---
st.set_page_config(
    page_title="GeralJá | Grajaú",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed" # Escondemos a lateral de vez
)

# --- 2. MOTOR DE ESTADO ---
if 'etapa' not in st.session_state: st.session_state.etapa = 'home'
if 'lucro' not in st.session_state: st.session_state.lucro = 0.0
if 'vendas' not in st.session_state: st.session_state.vendas = 0
if 'posts' not in st.session_state: 
    st.session_state.posts = [{"user": "Admin", "msg": "Sistema GeralJá Online! 🚀", "data": "26/12"}]

# --- 3. CSS PARA BOTÕES GIGANTES E CENTRALIZADOS ---
st.markdown("""
    <style>
    /* Fundo Branco e Texto Escuro */
    .stApp { background-color: #FFFFFF !important; }
    
    /* Logo Centralizada e Gigante */
    .logo-container { text-align: center; padding: 40px 0; }
    .azul { color: #0047AB; font-size: 60px; font-weight: 900; }
    .laranja { color: #FF8C00; font-size: 60px; font-weight: 900; }

    /* Estilo dos Botões de Menu (Página Inteira) */
    div.stButton > button {
        width: 100% !important;
        height: 80px !important;
        background-color: #0047AB !important; /* Azul para botões principais */
        color: white !important;
        font-size: 22px !important;
        font-weight: bold !important;
        border-radius: 15px !important;
        margin-bottom: 20px !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
    }
    
    /* Botão de Pesquisar Laranja */
    .btn-laranja div.stButton > button {
        background-color: #FF8C00 !important;
    }

    /* Esconder elementos desnecessários */
    header, footer { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 4. ROTEAMENTO DE TELAS ---

# TELA 0: HOME (O NOVO MENU)
if st.session_state.etapa == 'home':
    st.markdown('<div class="logo-container"><span class="azul">GERAL</span><span class="laranja">JÁ</span></div>', unsafe_allow_html=True)
    
    st.write("### O que vamos fazer hoje?")
    
    if st.button("🔍 BUSCAR UM SERVIÇO", key="home_busca"):
        st.session_state.etapa = 'busca'
        st.rerun()
        
    if st.button("👥 COMUNIDADE / REDE SOCIAL", key="home_social"):
        st.session_state.etapa = 'social'
        st.rerun()
        
    if st.button("📊 PAINEL DE CONTROLE", key="home_admin"):
        st.session_state.etapa = 'admin'
        st.rerun()

# TELA 1: BUSCA
elif st.session_state.etapa == 'busca':
    st.markdown("## 🔍 Qual profissional você precisa?")
    servico = st.selectbox("Escolha o serviço", ["", "Pintor", "Eletricista", "Encanador", "Diarista"], key="s_v9")
    rua = st.text_input("📍 Seu Endereço no Grajaú", key="r_v9")
    
    st.markdown('<div class="btn-laranja">', unsafe_allow_html=True)
    if st.button("ENCONTRAR AGORA", key="b_v9"):
        if servico and rua:
            st.session_state.servico_busca = servico
            st.session_state.etapa = 'resultado'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("⬅ VOLTAR AO MENU"):
        st.session_state.etapa = 'home'; st.rerun()

# TELA 2: SOCIAL
elif st.session_state.etapa == 'social':
    st.markdown("## 👥 Rede Social Grajaú")
    if st.button("⬅ VOLTAR AO MENU"):
        st.session_state.etapa = 'home'; st.rerun()
    
    with st.form("social_v9"):
        u, m = st.text_input("Seu Nome"), st.text_area("O que está acontecendo no bairro?")
        if st.form_submit_button("POSTAR"):
            st.session_state.posts.insert(0, {"user": u, "msg": m})
            st.rerun()
    
    for p in st.session_state.posts:
        st.info(f"**{p['user']}**: {p['msg']}")

# TELA 3: RESULTADO
elif st.session_state.etapa == 'resultado':
    st.success(f"✅ Profissional localizado para {st.session_state.servico_busca}!")
    
    # Mapa mais simples possível (Imagem)
    st.image("https://api.mapbox.com/styles/v1/mapbox/streets-v11/static/-46.6682,-23.7721,13/600x300?access_token=pk.eyJ1IjoiZ3VpZG94IiwiYSI6ImNrZnduZnR4MDBhNnoycnBnbm9idG9yejkifQ.7Wp6M_2yA6_z_rG-vH0Z6A")
    
    st.write("### Bony Silva ⭐ 4.9")
    if st.button("💳 CONTRATAR AGORA"):
        st.session_state.etapa = 'pagamento'; st.rerun()
    if st.button("⬅ VOLTAR"):
        st.session_state.etapa = 'home'; st.rerun()

# TELA 4: ADMIN / PAGAMENTO (Simplificados para teste)
elif st.session_state.etapa == 'admin':
    st.write(f"### Lucro: R$ {st.session_state.lucro}")
    if st.button("⬅ VOLTAR"): st.session_state.etapa = 'home'; st.rerun()

elif st.session_state.etapa == 'pagamento':
    st.write("### Escaneie para pagar")
    st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={CHAVE_PIX}")
    if st.button("✅ CONCLUÍDO"):
        st.session_state.lucro += 25; st.session_state.etapa = 'home'; st.rerun()
