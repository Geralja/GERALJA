import streamlit as st
import datetime
import random
try:
    from gtts import gTTS
    audio_ready = True
except:
    audio_ready = False

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="GeralJá | Profissionais", page_icon="⚡", layout="centered")

# --- 2. MOTOR DE ESTADO (ESTENDIDO) ---
if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'
if 'posts' not in st.session_state: st.session_state.posts = []
if 'lucro' not in st.session_state: st.session_state.lucro = 0.0
if 'vendas' not in st.session_state: st.session_state.vendas = 0
if 'codigo_verificacao' not in st.session_state: st.session_state.codigo_verificacao = None
if 'profissional_logado' not in st.session_state: st.session_state.profissional_logado = False

CHAVE_PIX = "09be938c-ee95-469f-b221-a3beea63964b"

# --- 3. CSS PROFISSIONAL ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    .logo-box { text-align: center; padding: 10px 0; }
    .azul { color: #0047AB; font-size: 40px; font-weight: 900; }
    .laranja { color: #FF8C00; font-size: 40px; font-weight: 900; }
    div.stButton > button {
        background-color: #FF8C00 !important;
        color: white !important;
        border-radius: 25px !important;
        font-weight: bold !important;
        width: 100%;
    }
    .status-verificado { color: #28a745; font-weight: bold; border: 1px solid #28a745; padding: 5px; border-radius: 10px; text-align: center; }
    header, footer { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 4. MENU DE NAVEGAÇÃO REFORÇADO (4 BOTÕES) ---
st.markdown('<div class="logo-box"><span class="azul">GERAL</span><span class="laranja">JÁ</span></div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)

with c1: 
    if st.button("🏠 Busca"): st.session_state.etapa = 'busca'; st.rerun()
with c2: 
    if st.button("👥 Social"): st.session_state.etapa = 'social'; st.rerun()
with c3: 
    if st.button("👷 Cadastro"): st.session_state.etapa = 'cadastro'; st.rerun()
with c4: 
    if st.button("📊 Admin"): st.session_state.etapa = 'admin'; st.rerun()

st.divider()

# --- 5. LÓGICA DE TELAS ---

# TELA: CADASTRO DE PROFISSIONAL
if st.session_state.etapa == 'cadastro':
    st.markdown("### 👷 Cadastro de Prestador")
    
    if not st.session_state.profissional_logado:
        tab1, tab2 = st.tabs(["1. Dados", "2. Verificação"])
        
        with tab1:
            nome = st.text_input("Nome Completo")
            profissao = st.selectbox("Sua Especialidade", ["Pintor", "Eletricista", "Encanador", "Diarista", "Mecânico", "Outros"])
            contato = st.text_input("WhatsApp ou E-mail para contato")
            
            if st.button("Gerar Código de Verificação"):
                if nome and contato:
                    # Simulação de envio de código
                    st.session_state.codigo_verificacao = str(random.randint(1000, 9999))
                    st.info(f"🛡️ Simulação de SMS/E-mail: Seu código é **{st.session_state.codigo_verificacao}**")
                    st.success("Código enviado com sucesso!")
                else:
                    st.error("Preencha todos os campos.")

        with tab2:
            st.write("Insira o código de 4 dígitos enviado:")
            input_cod = st.text_input("Código", max_chars=4)
            if st.button("Confirmar Identidade"):
                if input_cod == st.session_state.codigo_verificacao:
                    st.session_state.profissional_logado = True
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Código incorreto.")
    else:
        st.markdown('<div class="status-verificado">✅ PERFIL VERIFICADO E ATIVO</div>', unsafe_allow_html=True)
        st.write(f"Bem-vindo ao time, seu perfil já está aparecendo nas buscas do Grajaú!")
        if st.button("Sair / Deslogar"):
            st.session_state.profissional_logado = False
            st.rerun()

# TELA: BUSCA (MANTIDA)
elif st.session_state.etapa == 'busca':
    st.markdown("### 🔍 O que você precisa hoje?")
    serv = st.selectbox("Serviço", ["", "Pintor", "Eletricista", "Encanador", "Diarista"])
    if st.button("PESQUISAR"):
        if serv: st.session_state.servico_busca = serv; st.session_state.etapa = 'resultado'; st.rerun()

# TELA: RESULTADO (COM SELO DE VERIFICADO)
elif st.session_state.etapa == 'resultado':
    st.markdown(f"### 📍 Profissional Localizado")
    st.markdown("#### Bony Silva <span style='color:#0047AB;'>✔️ Verificado</span>", unsafe_allow_html=True)
    
    # Mapa
    st.image("https://api.mapbox.com/styles/v1/mapbox/streets-v11/static/-46.6682,-23.7721,14/600x250?access_token=pk.eyJ1IjoiZ3VpZG94IiwiYSI6ImNrZnduZnR4MDBhNnoycnBnbm9idG9yejkifQ.7Wp6M_2yA6_z_rG-vH0Z6A")

    if audio_ready and st.button("🔊 OUVIR DETALHES"):
        tts = gTTS(text=f"Encontramos um profissional verificado para {st.session_state.servico_busca}", lang='pt')
        tts.save("voz.mp3")
        st.audio("voz.mp3", autoplay=True)

    if st.button("✅ CONTRATAR"): st.session_state.etapa = 'pagamento'; st.rerun()

# --- REPETIR TELAS SOCIAL, ADMIN E PAGAMENTO DO V10 ---
elif st.session_state.etapa == 'social':
    st.write("### 👥 Comunidade")
    with st.form("social"):
        u, m = st.text_input("Nome"), st.text_area("Mensagem")
        if st.form_submit_button("Postar"): st.session_state.posts.insert(0, {"u":u, "m":m}); st.rerun()
    for p in st.session_state.posts: st.info(f"{p['u']}: {p['m']}")

elif st.session_state.etapa == 'pagamento':
    st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={CHAVE_PIX}")
    if st.button("✅ CONFIRMAR"): 
        st.session_state.lucro += 25; st.session_state.vendas += 1
        st.session_state.etapa = 'busca'; st.rerun()

elif st.session_state.etapa == 'admin':
    senha = st.text_input("Senha Admin", type="password")
    if senha == "admin777":
        st.metric("Lucro", f"R$ {st.session_state.lucro}")
        st.metric("Vendas", st.session_state.vendas)
