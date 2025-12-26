import streamlit as st
import datetime
try:
    from gtts import gTTS
    audio_ready = True
except:
    audio_ready = False

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="GeralJá | Grajaú", page_icon="⚡", layout="centered")

# --- 2. MOTOR DE ESTADO ---
for key, val in {'etapa': 'busca', 'lucro': 0.0, 'vendas': 0, 'posts': []}.items():
    if key not in st.session_state: st.session_state[key] = val

CHAVE_PIX = "09be938c-ee95-469f-b221-a3beea63964b"

# --- 3. CSS PROFISSIONAL (DESIGN ORIGINAL REFINADO) ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    .logo-box { text-align: center; padding: 10px 0; }
    .azul { color: #0047AB; font-size: 45px; font-weight: 900; }
    .laranja { color: #FF8C00; font-size: 45px; font-weight: 900; }
    
    /* Botões Arredondados e Elegantes */
    div.stButton > button {
        background-color: #FF8C00 !important;
        color: white !important;
        border-radius: 25px !important;
        font-weight: bold !important;
        border: none !important;
        width: 100%;
    }
    
    /* Estilo para as "Bolhas" da Rede Social */
    .post-box {
        background: #F0F2F6; padding: 15px; border-radius: 15px; 
        margin-bottom: 10px; border-left: 5px solid #0047AB;
    }
    header, footer { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 4. MENU DE NAVEGAÇÃO SUPERIOR (Substitui a Sidebar bugada) ---
st.markdown('<div class="logo-box"><span class="azul">GERAL</span><span class="laranja">JÁ</span></div>', unsafe_allow_html=True)
col_nav1, col_nav2, col_nav3 = st.columns(3)

with col_nav1:
    if st.button("🏠 Início"): st.session_state.etapa = 'busca'; st.rerun()
with col_nav2:
    if st.button("👥 Social"): st.session_state.etapa = 'social'; st.rerun()
with col_nav3:
    if st.button("📊 Admin"): st.session_state.etapa = 'admin'; st.rerun()

st.divider()

# --- 5. TELAS COM TODAS AS FUNÇÕES ---

# BUSCA
if st.session_state.etapa == 'busca':
    st.markdown("### 🔍 Encontre um Especialista")
    servico = st.selectbox("O que você precisa?", ["", "Pintor", "Eletricista", "Encanador", "Diarista", "Mecânico"])
    rua = st.text_input("📍 Seu endereço no Grajaú")
    if st.button("BUSCAR AGORA") and servico and rua:
        st.session_state.servico_busca = servico
        st.session_state.etapa = 'resultado'; st.rerun()

# REDE SOCIAL (Com memória)
elif st.session_state.etapa == 'social':
    st.markdown("### 👥 Comunidade Grajaú")
    with st.form("post_form"):
        u, m = st.text_input("Nome"), st.text_area("O que quer dizer?")
        if st.form_submit_button("Publicar") and u and m:
            st.session_state.posts.insert(0, {"u": u, "m": m, "d": "Agora"})
            st.rerun()
    for p in st.session_state.posts:
        st.markdown(f'<div class="post-box"><b>{p["u"]}</b>: {p["m"]}</div>', unsafe_allow_html=True)

# RESULTADO (Com Mapa e Áudio)
elif st.session_state.etapa == 'resultado':
    st.success(f"Encontramos um {st.session_state.servico_busca}!")
    
    # Mapa Estático Mapbox
    mapa = "https://api.mapbox.com/styles/v1/mapbox/streets-v11/static/-46.6682,-23.7721,14/600x250?access_token=pk.eyJ1IjoiZ3VpZG94IiwiYSI6ImNrZnduZnR4MDBhNnoycnBnbm9idG9yejkifQ.7Wp6M_2yA6_z_rG-vH0Z6A"
    st.image(mapa, caption="Localização do Profissional")

    if audio_ready and st.button("🔊 OUVIR DETALHES"):
        tts = gTTS(text=f"Encontramos o Bony Silva para {st.session_state.servico_busca}", lang='pt')
        tts.save("voz.mp3")
        st.audio("voz.mp3", autoplay=True)

    if st.button("✅ CONTRATAR PROFISSIONAL"):
        st.session_state.etapa = 'pagamento'; st.rerun()

# PAGAMENTO (Com Pix)
elif st.session_state.etapa == 'pagamento':
    st.markdown("### 💳 Pagamento via Pix")
    st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={CHAVE_PIX}")
    st.code(CHAVE_PIX)
    if st.button("✅ PAGAMENTO CONFIRMADO"):
        st.session_state.lucro += 25.0; st.session_state.vendas += 1
        st.balloons(); st.session_state.etapa = 'busca'; st.rerun()

# ADMIN (Com Senha)
elif st.session_state.etapa == 'admin':
    st.markdown("### 🔐 Área Administrativa")
    senha = st.text_input("Senha", type="password")
    if senha == "admin777":
        st.metric("Faturamento Total", f"R$ {st.session_state.lucro:.2f}")
        st.metric("Serviços Realizados", st.session_state.vendas)
