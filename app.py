import streamlit as st
import random
import time

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="GeralJá | Elite HUB", layout="centered", initial_sidebar_state="collapsed")

# --- 2. BANCO DE DADOS E ESTADOS ---
if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'
if 'lucro_plataforma' not in st.session_state: st.session_state.lucro_plataforma = 0.0
if 'pedidos_concluidos' not in st.session_state: st.session_state.pedidos_concluidos = 0

CHAVE_PIX_ALERATORIA = "09be938c-ee95-469f-b221-a3beea63964b"

if 'db_pros' not in st.session_state:
    st.session_state.db_pros = {
        "BONY77": {"nome": "Bony Silva", "cargo": "Eletricista", "saldo": 0.0, "status": "Ativo"},
        "MARIA22": {"nome": "Maria Limpeza", "cargo": "Diarista", "saldo": 0.0, "status": "Ativo"},
    }

LISTA_PROS = sorted(["Pintor", "Eletricista", "Encanador", "Diarista", "Pedreiro", "Montador de Móveis", "Mecânico", "Jardineiro", "Chaveiro"])

# --- 3. CSS MESTRE (LOGO DEGRADÊ + BRILHO) ---
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top, #1a2a40 0%, #050a10 100%); color: white; }
    
    /* LOGO EM DEGRADÊ */
    .logo-gradient {
        font-size: 60px !important;
        font-weight: 900 !important;
        background: linear-gradient(135deg, #f39c12, #f1c40f);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0px;
        filter: drop-shadow(0 0 10px rgba(243, 156, 18, 0.3));
    }

    .glass-card {
        background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(12px);
        border-radius: 20px; padding: 25px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px;
    }

    /* BOTÃO PULSANTE COM BRILHO */
    div.stButton > button {
        background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 15px 25px !important;
        font-weight: 900 !important;
        transition: all 0.3s ease-in-out !important;
        width: 100% !important;
        animation: pulse-glow 2s infinite !important;
    }

    @keyframes pulse-glow {
        0% { box-shadow: 0 0 5px rgba(243, 156, 18, 0.5); transform: scale(1); }
        50% { box-shadow: 0 0 20px rgba(243, 156, 18, 0.8); transform: scale(1.01); }
        100% { box-shadow: 0 0 5px rgba(243, 156, 18, 0.5); transform: scale(1); }
    }
    
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 4. FLUXO DO APP ---

# VISÃO ADMIN
if st.session_state.etapa == 'admin':
    st.title("📊 Painel do Nodo")
    col1, col2 = st.columns(2)
    col1.metric("Faturamento (10%)", f"R$ {st.session_state.lucro_plataforma:.2f}")
    col2.metric("Serviços", st.session_state.pedidos_concluidos)
    if st.button("⬅ Sair do Admin"):
        st.session_state.etapa = 'busca'
        st.rerun()

# ETAPA: BUSCA
elif st.session_state.etapa == 'busca':
    # LOGO EM DEGRADÊ
    st.markdown('<h1 class="logo-gradient">GERALJÁ</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; color:gray; margin-top:-10px;">O Grajaú resolve aqui.</p>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        servico_input = st.selectbox("Qual profissional você precisa?", [""] + LISTA_PROS, key="sel_servico")
        rua_input = st.text_input("📍 Seu Endereço no Grajaú", key="inp_rua")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # BOTÃO PRINCIPAL
        if st.button("ATIVAR RADAR 🛰️"):
            if servico_input != "" and rua_input != "":
                st.session_state.servico_busca = servico_input
                st.session_state.etapa = 'resultado'
                st.rerun()
            else:
                st.warning("⚠️ Selecione a profissão e o endereço.")

    # FRASE DE EFEITO NO BOTÃO INFERIOR
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🆘 NÃO ACHOU O QUE PRECISAVA? CHAMAR NO SUPORTE"):
        st.toast("Redirecionando para o suporte humano do GeralJá...", icon="💬")

# ETAPA: RESULTADO
elif st.session_state.etapa == 'resultado':
    st.markdown('<h1 class="logo-gradient" style="font-size:30px !important;">GERALJÁ</h1>', unsafe_allow_html=True)
    st.markdown("### 📍 Profissional Localizado")
    
    preco = random.randint(180, 400)
    st.markdown(f'<div class="glass-card"><h2>Bony Silva</h2><p>⭐ 4.9 | {st.session_state.servico_busca}</p><h1>R$ {preco},00</h1></div>', unsafe_allow_html=True)
    
    if st.button("💳 CONTRATAR PROFISSIONAL"):
        st.session_state.valor_final = preco
        st.session_state.etapa = 'pagamento'
        st.rerun()
    if st.button("⬅ Voltar"):
        st.session_state.etapa = 'busca'; st.rerun()

# ETAPA: PAGAMENTO
elif st.session_state.etapa == 'pagamento':
    val = st.session_state.valor_final
    st.markdown("<h3 style='text-align:center;'>Pagamento Seguro</h3>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class="glass-card" style="background:white; color:black; text-align:center;">
            <p style="color:gray;">TOTAL: <b>R$ {val},00</b></p>
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={CHAVE_PIX_ALERATORIA}" style="margin:10px;">
            <p style="font-size:10px; color:#555;">CHAVE ALEATÓRIA:</p>
            <code style="word-break:break-all; font-size:11px;">{CHAVE_PIX_ALERATORIA}</code>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("✅ CONFIRMAR PAGAMENTO"):
        st.session_state.lucro_plataforma += (val * 0.10)
        st.session_state.pedidos_concluidos += 1
        st.session_state.etapa = 'chat_sucesso'
        st.rerun()

# ETAPA: CHAT SUCESSO
elif st.session_state.etapa == 'chat_sucesso':
    st.balloons()
    st.markdown('<div class="glass-card"><h3>📲 Conversa Iniciada</h3><p style="background:#056162; padding:15px; border-radius:15px 15px 0 15px;"><b>Bony Silva:</b> Tudo certo! Já estou a caminho com o material. Chego em 15 minutos! 🛠️</p></div>', unsafe_allow_html=True)
    if st.button("Nova Busca"):
        st.session_state.etapa = 'busca'; st.rerun()

# BARRA LATERAL (ACESSAR ADMIN)
with st.sidebar:
    st.title("🔐 Acesso")
    token = st.text_input("Senha Admin", type="password")
    if token == "admin777":
        st.session_state.etapa = 'admin'
        st.rerun()
