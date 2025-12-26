import streamlit as st
import random
import datetime

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="GeralJá | Home", layout="centered", initial_sidebar_state="collapsed")

# --- 2. INICIALIZAÇÃO DE VARIÁVEIS ---
if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'
if 'lucro_plataforma' not in st.session_state: st.session_state.lucro_plataforma = 0.0
if 'pedidos_concluidos' not in st.session_state: st.session_state.pedidos_concluidos = 0
if 'posts' not in st.session_state: 
    st.session_state.posts = [{"user": "Equipe GeralJá", "msg": "Bem-vindos à nossa comunidade!", "data": "26/12"}]

CHAVE_PIX_ALERATORIA = "09be938c-ee95-469f-b221-a3beea63964b"
LISTA_PROS = sorted(["Pintor", "Eletricista", "Encanador", "Diarista", "Pedreiro", "Montador de Móveis", "Mecânico", "Jardineiro", "Chaveiro"])

# --- 3. CSS "WHITE LABEL" (LIMPEZA TOTAL) ---
st.markdown("""
    <style>
    /* Força Fundo Branco Total */
    .stApp, .stAppViewContainer, .stMain {
        background-color: #FFFFFF !important;
    }
    
    /* Logo Centralizado */
    .logo-container { text-align: center; margin-top: -30px; padding-bottom: 20px; }
    .logo-geral { color: #0047AB; font-size: 55px; font-weight: 900; }
    .logo-ja { color: #FF8C00; font-size: 55px; font-weight: 900; }

    /* Estilização da Barra Lateral (Sidebar) */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa !important;
        border-right: 1px solid #eee;
    }

    /* Botões da Home e Sidebar */
    div.stButton > button {
        background-color: #FF8C00 !important;
        color: white !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        height: 55px !important;
        width: 100% !important;
        border: none !important;
    }

    /* Estilo dos cards da Rede Social */
    .post-card {
        background: white;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #eee;
        margin-bottom: 12px;
        color: #333;
    }

    /* Ocultar elementos desnecessários */
    header, footer { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 4. JANELA LATERAL RESPONSIVA (SIDEBAR) ---
with st.sidebar:
    st.markdown("<h2 style='color:#0047AB;'>Menu GeralJá</h2>", unsafe_allow_html=True)
    st.write("Escolha uma opção:")
    
    if st.button("🏠 Início / Buscar"):
        st.session_state.etapa = 'busca'
        st.rerun()
        
    if st.button("👥 Rede Social"):
        st.session_state.etapa = 'social'
        st.rerun()
        
    if st.button("🆘 Suporte 24h"):
        st.toast("Conectando ao WhatsApp de suporte...")
        
    st.divider()
    
    # ACESSO ADMIN DENTRO DA LATERAL
    with st.expander("🔐 Área Restrita"):
        senha = st.text_input("Senha Admin", type="password")
        if senha == "admin777":
            if st.button("Acessar Dashboard"):
                st.session_state.etapa = 'admin'
                st.rerun()

# --- 5. ROTEAMENTO DE TELAS ---

# TELA PRINCIPAL (BUSCA)
if st.session_state.etapa == 'busca':
    st.markdown("""
        <div class="logo-container">
            <span class="logo-geral">GERAL</span><span class="logo-ja">JÁ</span>
            <p style="color: #666; margin-top: -15px;">O Grajaú resolve aqui.</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        servico = st.selectbox("O que você precisa hoje?", [""] + LISTA_PROS)
        rua = st.text_input("📍 Seu Endereço ou Referência")
        
        st.write("")
        if st.button("🚀 BUSCAR PROFISSIONAL"):
            if servico and rua:
                st.session_state.servico_busca = servico
                st.session_state.etapa = 'resultado'
                st.rerun()
            else:
                st.warning("⚠️ Por favor, informe o serviço e o endereço.")

# TELA REDE SOCIAL
elif st.session_state.etapa == 'social':
    st.markdown("<h2 style='color:#0047AB;'>👥 Comunidade Grajaú</h2>", unsafe_allow_html=True)
    with st.expander("📝 Criar Publicação"):
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
    st.markdown("<h2 style='color:#0047AB;'>📊 Painel Administrativo</h2>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.metric("Lucro Bruto", f"R$ {st.session_state.get('lucro_plataforma', 0):.2f}")
    c2.metric("Serviços Pagos", st.session_state.get('pedidos_concluidos', 0))
    if st.button("⬅ Sair"):
        st.session_state.etapa = 'busca'; st.rerun()

# TELA RESULTADO
elif st.session_state.etapa == 'resultado':
    st.image("https://api.mapbox.com/styles/v1/mapbox/streets-v11/static/-46.6682,-23.7721,13/600x220?access_token=pk.eyJ1IjoiZ3VpZG94IiwiYSI6ImNrZnduZnR4MDBhNnoycnBnbm9idG9yejkifQ.7Wp6M_2yA6_z_rG-vH0Z6A")
    st.success(f"Encontramos especialistas em {st.session_state.servico_busca} próximos a você!")
    if st.button("CONTRATAR BONY SILVA"): 
        st.session_state.etapa = 'pagamento'; st.rerun()
    if st.button("⬅ Voltar"): 
        st.session_state.etapa = 'busca'; st.rerun()

# TELA PAGAMENTO
elif st.session_state.etapa == 'pagamento':
    st.markdown("<h3 style='text-align:center;'>Pagamento via PIX</h3>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style="background:#f8f9fa; padding:25px; border-radius:15px; text-align:center; border: 1px solid #eee;">
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={CHAVE_PIX_ALERATORIA}">
            <p style='font-size:12px; color:gray; margin-top:10px;'>{CHAVE_PIX_ALERATORIA}</p>
        </div>
    """, unsafe_allow_html=True)
    if st.button("✅ CONFIRMAR PAGAMENTO"): 
        st.session_state.lucro_plataforma += 25.0
        st.session_state.pedidos_concluidos += 1
        st.session_state.etapa = 'busca'; st.balloons(); st.rerun()
