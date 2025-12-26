import streamlit as st
import random
import time

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="GeralJá | Elite HUB", layout="centered", initial_sidebar_state="collapsed")

# --- 2. ESTADOS ---
if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'
if 'lucro_plataforma' not in st.session_state: st.session_state.lucro_plataforma = 0.0
if 'pedidos_concluidos' not in st.session_state: st.session_state.pedidos_concluidos = 0

CHAVE_PIX_ALERATORIA = "09be938c-ee95-469f-b221-a3beea63964b"
LISTA_PROS = sorted(["Pintor", "Eletricista", "Encanador", "Diarista", "Pedreiro", "Montador de Móveis", "Mecânico", "Jardineiro", "Chaveiro"])

# --- 3. CSS (BRILHO, DEGRADÊ E LARGURA) ---
st.markdown("""
    <style>
    .stApp { background: #050a10; color: white; }
    
    /* LOGO DEGRADÊ */
    .logo-text {
        font-size: 65px !important;
        font-weight: 900 !important;
        background: linear-gradient(135deg, #f39c12, #f1c40f);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0px;
    }

    /* BOTÃO PULSANTE LARGURA TOTAL */
    div.stButton > button {
        background: linear-gradient(135deg, #f39c12, #e67e22) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 900 !important;
        height: 55px !important;
        width: 100% !important; /* Mesma largura da barra de pesquisa */
        animation: pulse-glow 2s infinite !important;
    }

    @keyframes pulse-glow {
        0% { box-shadow: 0 0 5px rgba(243, 156, 18, 0.4); }
        50% { box-shadow: 0 0 20px rgba(243, 156, 18, 0.8); }
        100% { box-shadow: 0 0 5px rgba(243, 156, 18, 0.4); }
    }
    
    /* Ajuste para inputs ficarem iguais aos botões */
    .stSelectbox, .stTextInput { width: 100% !important; }

    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 4. BARRA LATERAL (CORRIGIDA) ---
with st.sidebar:
    st.title("🔐 Área Restrita")
    senha = st.text_input("Senha Admin", type="password")
    if senha == "admin777":
        st.session_state.etapa = 'admin'
        # O botão abaixo força a atualização para abrir a tela admin
        if st.button("ACESSAR PAINEL"): st.rerun()

# --- 5. FLUXO DO APLICATIVO ---

# VISÃO ADMIN
if st.session_state.etapa == 'admin':
    st.title("📊 Painel do Nodo")
    st.metric("Lucro (10%)", f"R$ {st.session_state.lucro_plataforma:.2f}")
    if st.button("⬅ VOLTAR PARA BUSCA"):
        st.session_state.etapa = 'busca'
        st.rerun()

# ETAPA BUSCA
elif st.session_state.etapa == 'busca':
    st.markdown('<h1 class="logo-text">GERALJÁ</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; color:gray; margin-top:-15px;">Soluções Rápidas no Grajaú</p>', unsafe_allow_html=True)
    
    with st.container():
        servico = st.selectbox("O que você procura?", [""] + LISTA_PROS)
        rua = st.text_input("📍 Seu Endereço no Grajaú")
        
        st.write("") 
        if st.button("🚀 ATIVAR RADAR AGORA", use_container_width=True):
            if servico and rua:
                st.session_state.servico_busca = servico
                st.session_state.etapa = 'resultado'
                st.rerun()
            else:
                st.warning("Preencha os campos para buscar.")

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🆘 NÃO ACHOU? CHAMAR SUPORTE 24H", use_container_width=True):
        st.info("Conectando ao suporte...")

# ETAPA RESULTADO COM MAPA (FORÇADO)
elif st.session_state.etapa == 'resultado':
    st.markdown("### 📍 Profissional Localizado")
    
    # MAPA ESTÁTICO (Este link sempre funciona)
    st.markdown("""
        <div style="width:100%; height:220px; border-radius:15px; border:2px solid #f39c12; overflow:hidden; margin-bottom:20px;">
            <img src="https://api.mapbox.com/styles/v1/mapbox/dark-v10/static/-46.6682,-23.7721,13/600x220?access_token=pk.eyJ1IjoiZ3VpZG94IiwiYSI6ImNrZnduZnR4MDBhNnoycnBnbm9idG9yejkifQ.7Wp6M_2yA6_z_rG-vH0Z6A" style="width:100%; height:100%; object-fit:cover;">
        </div>
    """, unsafe_allow_html=True)
    
    preco = random.randint(180, 350)
    st.markdown(f"""
        <div style="background:rgba(255,255,255,0.05); padding:20px; border-radius:20px; border:1px solid rgba(255,255,255,0.1); text-align:center;">
            <h2 style="color:#f39c12; margin:0;">Bony Silva</h2>
            <p>Especialista em {st.session_state.servico_busca}</p>
            <h1 style="margin:10px 0;">R$ {preco},00</h1>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("💳 CONTRATAR E PAGAR", use_container_width=True):
        st.session_state.valor_final = preco
        st.session_state.etapa = 'pagamento'
        st.rerun()
    if st.button("⬅ VOLTAR", use_container_width=True):
        st.session_state.etapa = 'busca'; st.rerun()

# ETAPA PAGAMENTO
elif st.session_state.etapa == 'pagamento':
    val = st.session_state.valor_final
    st.markdown(f"""
        <div style="background:white; color:black; padding:30px; border-radius:20px; text-align:center;">
            <p style="color:gray; margin:0;">PAGAR VIA PIX</p>
            <h1 style="color:#27ae60; margin:0;">R$ {val},00</h1>
            <br>
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={CHAVE_PIX_ALERATORIA}">
            <p style="font-size:11px; margin-top:15px; word-break:break-all;"><b>Chave Aleatória:</b><br>{CHAVE_PIX_ALERATORIA}</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("✅ JÁ REALIZEI O PAGAMENTO", use_container_width=True):
        st.session_state.lucro_plataforma += (val * 0.10)
        st.session_state.pedidos_concluidos += 1
        st.session_state.etapa = 'sucesso'
        st.rerun()

elif st.session_state.etapa == 'sucesso':
    st.balloons()
    st.success("Pagamento confirmado! O profissional está a caminho.")
    if st.button("VOLTAR AO INÍCIO", use_container_width=True):
        st.session_state.etapa = 'busca'; st.rerun()
