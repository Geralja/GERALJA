import streamlit as st
import datetime
import time
try:
    from gtts import gTTS
    audio_ready = True
except:
    audio_ready = False

# --- 1. CONFIGURAÇÃO DE NÚCLEO (PRIORIDADE TOTAL AO MENU) ---
st.set_page_config(
    page_title="GeralJá | Grajaú",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="expanded" # Garante que o menu lateral comece visível
)

# --- 2. MOTOR DE ESTADO ---
if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'
if 'lucro' not in st.session_state: st.session_state.lucro = 0.0
if 'vendas' not in st.session_state: st.session_state.vendas = 0
if 'posts' not in st.session_state: 
    st.session_state.posts = [{"user": "Admin", "msg": "Sistema GeralJá Online! 🚀", "data": "26/12"}]

CHAVE_PIX = "09be938c-ee95-469f-b221-a3beea63964b"

# --- 3. MENU LATERAL (COLOCADO ANTES DO CSS PARA NÃO BUGAR) ---
with st.sidebar:
    st.markdown("<h1 style='color:#0047AB;'>📌 Navegação</h1>", unsafe_allow_html=True)
    if st.button("🏠 Início / Busca", key="menu_v8_home"):
        st.session_state.etapa = 'busca'
        st.rerun()
    if st.button("👥 Rede Social", key="menu_v8_social"):
        st.session_state.etapa = 'social'
        st.rerun()
    st.divider()
    with st.expander("🔐 Administração"):
        pwd = st.text_input("Senha", type="password", key="pwd_v8_admin")
        if pwd == "admin777":
            if st.button("Abrir Painel", key="btn_v8_admin"):
                st.session_state.etapa = 'admin'
                st.rerun()

# --- 4. CSS AJUSTADO (SEM CONFLITO COM A SIDEBAR) ---
st.markdown("""
    <style>
    /* Força Fundo Branco apenas no conteúdo principal */
    .stAppViewContainer { background-color: #FFFFFF !important; }
    
    /* Ajuste da Logo */
    .logo-box { text-align: center; padding: 15px 0; margin-top: -20px; }
    .azul { color: #0047AB; font-size: 48px; font-weight: 900; }
    .laranja { color: #FF8C00; font-size: 48px; font-weight: 900; }

    /* Botões Grandes e Visíveis */
    .stButton > button {
        background-color: #FF8C00 !important;
        color: white !important;
        border-radius: 12px !important;
        height: 55px !important;
        font-weight: bold !important;
        border: none !important;
    }
    
    /* Garante que o cabeçalho não esconda o menu */
    header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 5. ROTEAMENTO DE TELAS ---

if st.session_state.etapa == 'busca':
    st.markdown('<div class="logo-box"><span class="azul">GERAL</span><span class="laranja">JÁ</span></div>', unsafe_allow_html=True)
    servico = st.selectbox("O que você precisa?", ["", "Pintor", "Eletricista", "Encanador", "Diarista", "Mecânico"], key="sel_v8")
    rua = st.text_input("📍 Seu Endereço", key="rua_v8")
    if st.button("🚀 BUSCAR AGORA", key="btn_v8_search"):
        if servico and rua:
            st.session_state.servico_busca = servico
            st.session_state.etapa = 'resultado'; st.rerun()

elif st.session_state.etapa == 'social':
    st.markdown("### 👥 Comunidade Grajaú")
    with st.form("form_v8"):
        u, m = st.text_input("Nome"), st.text_area("Mensagem")
        if st.form_submit_button("Postar") and u and m:
            st.session_state.posts.insert(0, {"user": u, "msg": m, "data": "Agora"})
            st.rerun()
    for p in st.session_state.posts:
        st.info(f"**{p['user']}**: {p['msg']}")

elif st.session_state.etapa == 'resultado':
    st.markdown(f"### 📍 Profissional: {st.session_state.servico_busca}")
    
    # NOVO MAPA: Usando Iframe para garantir que apareça sempre
    map_html = '<iframe width="100%" height="250" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" src="https://maps.google.com/maps?q=-23.7721,-46.6682&hl=pt&z=14&amp;output=embed"></iframe>'
    st.markdown(f'<div style="border-radius:15px; overflow:hidden; border:1px solid #ddd;">{map_html}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("#### Bony Silva ⭐ 4.9")
    
    if audio_ready and st.button("🔊 OUVIR DETALHES"):
        tts = gTTS(text=f"Encontramos o Bony Silva para {st.session_state.servico_busca}", lang='pt')
        tts.save("v8.mp3")
        st.audio("v8.mp3", autoplay=True)

    if st.button("✅ CONTRATAR", key="btn_v8_pay"):
        st.session_state.etapa = 'pagamento'; st.rerun()
    if st.button("⬅ Voltar"): st.session_state.etapa = 'busca'; st.rerun()

elif st.session_state.etapa == 'pagamento':
    st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={CHAVE_PIX}")
    if st.button("✅ CONCLUIR"):
        st.session_state.lucro += 25.0; st.session_state.vendas += 1
        st.session_state.etapa = 'busca'; st.balloons(); st.rerun()
