import streamlit as st
import random
import time

# --- 1. CONFIGURAÇÃO DA PLATAFORMA ---
st.set_page_config(page_title="GeralJá | Elite HUB", layout="centered", initial_sidebar_state="collapsed")

# --- 2. BANCO DE DADOS DE SESSÃO ---
if 'lucro_plataforma' not in st.session_state: st.session_state.lucro_plataforma = 0.0
if 'pedidos_concluidos' not in st.session_state: st.session_state.pedidos_concluidos = 0
if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'

# CHAVE PIX OFICIAL DO NODO
CHAVE_PIX_ALERATORIA = "09be938c-ee95-469f-b221-a3beea63964b"

if 'db_pros' not in st.session_state:
    st.session_state.db_pros = {
        "BONY77": {"nome": "Bony Silva", "cargo": "Eletricista", "saldo": 0.0, "status": "Ativo"},
        "MARIA22": {"nome": "Maria Limpeza", "cargo": "Diarista", "saldo": 0.0, "status": "Ativo"},
    }

LISTA_PROS = sorted(["Pintor", "Eletricista", "Encanador", "Diarista", "Pedreiro", "Montador de Móveis", "Mecânico", "Jardineiro", "Chaveiro"])

# --- 3. ESTILO CSS ---
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top, #1a2a40 0%, #050a10 100%); color: white; }
    .glass-card {
        background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(12px);
        border-radius: 20px; padding: 25px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px;
    }
    .stButton>button {
        background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%) !important;
        color: white !important; border-radius: 12px !important; border: none !important; font-weight: 900;
        width: 100%; height: 50px;
    }
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 4. ÁREA DE ACESSO (SIDEBAR) ---
with st.sidebar:
    st.title("🔐 Portão de Acesso")
    token = st.text_input("Token ou Chave Mestra", type="password")
    if token == "admin777":
        st.session_state.etapa = 'admin'
    elif token in st.session_state.db_pros:
        st.session_state.token_ativo = token
        st.session_state.etapa = 'painel_pro'
    else:
        st.session_state.etapa = 'busca'

# --- 5. ROTEAMENTO ---

# VISÃO ADMIN
if st.session_state.etapa == 'admin':
    st.title("📊 Painel do Nodo")
    col1, col2 = st.columns(2)
    col1.metric("Faturamento (10%)", f"R$ {st.session_state.lucro_plataforma:.2f}")
    col2.metric("Serviços", st.session_state.pedidos_concluidos)

    t1, t2, t3 = st.tabs(["✅ Ativos", "❄️ Bloqueados", "🗑️ Lixeira"])
    with t1:
        for tok, d in st.session_state.db_pros.items():
            if d['status'] == 'Ativo':
                with st.expander(f"🟢 {d['nome']}"):
                    if st.button(f"Bloquear {d['nome']}", key=f"blk_{tok}"):
                        d['status'] = 'Bloqueado'; st.rerun()
    with t2:
        for tok, d in st.session_state.db_pros.items():
            if d['status'] == 'Bloqueado':
                st.error(f"Bloqueado: {d['nome']}")
                if st.button(f"🔓 Reativar", key=f"re_at_{tok}"):
                    d['status'] = 'Ativo'; st.rerun()
    with t3:
        for tok, d in st.session_state.db_pros.items():
            if d['status'] == 'Excluído':
                st.warning(f"Excluído: {d['nome']}")
                if st.button(f"♻️ Restaurar", key=f"rest_{tok}"):
                    d['status'] = 'Ativo'; st.rerun()

# VISÃO CLIENTE
elif st.session_state.etapa == 'busca':
    st.markdown("<h1 style='text-align:center; color:#f39c12;'>GERALJÁ</h1>", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        servico = st.selectbox("O que você procura?", [""] + LISTA_PROS)
        rua = st.text_input("📍 Seu Endereço no Grajaú")
        st.markdown('</div>', unsafe_allow_html=True)
        if st.button("ATIVAR RADAR"):
            if servico and rua:
                st.session_state.servico_busca = servico
                st.session_state.etapa = 'resultado'
                st.rerun()

elif st.session_state.etapa == 'resultado':
    st.markdown("### 📍 Localizado no Grajaú")
    # Mapa Estático Mapbox
    st.markdown("""
        <div style="width:100%; height:200px; background: url('https://api.mapbox.com/styles/v1/mapbox/dark-v10/static/pin-s+f39c12(-46.6682,-23.7721)/-46.6682,-23.7721,13/600x200?access_token=pk.eyJ1IjoiZ3VpZG94IiwiYSI6ImNrZnduZnR4MDBhNnoycnBnbm9idG9yejkifQ.7Wp6M_2yA6_z_rG-vH0Z6A'); background-size: cover; border-radius: 15px; border: 1px solid #f39c12; margin-bottom: 15px;"></div>
    """, unsafe_allow_html=True)
    
    preco = random.randint(180, 400)
    st.markdown(f'<div class="glass-card"><h2>Bony Silva</h2><p>⭐ 4.9 | {st.session_state.servico_busca}</p><h1>R$ {preco},00</h1></div>', unsafe_allow_html=True)
    if st.button("💳 CONTRATAR"):
        st.session_state.valor_final = preco
        st.session_state.etapa = 'pagamento'
        st.rerun()

elif st.session_state.etapa == 'pagamento':
    val = st.session_state.valor_final
    st.markdown("<h3 style='text-align:center;'>Pagamento via PIX</h3>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class="glass-card" style="background:white; color:black; text-align:center;">
            <p style="color:gray; margin:0;">TOTAL: <b>R$ {val},00</b></p>
            <br>
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={CHAVE_PIX_ALERATORIA}" style="border-radius:10px;">
            <p style="font-size:10px; margin-top:10px; color:#555;">CHAVE ALEATÓRIA:</p>
            <code style="word-break:break-all; font-size:11px;">{CHAVE_PIX_ALERATORIA}</code>
        </div>
    """, unsafe_allow_html=True)
    if st.button("✅ JÁ REALIZEI O PAGAMENTO"):
        st.session_state.lucro_plataforma += (val * 0.10)
        st.session_state.pedidos_concluidos += 1
        st.session_state.etapa = 'chat_sucesso'
        st.rerun()

elif st.session_state.etapa == 'chat_sucesso':
    st.balloons()
    st.markdown('<div class="glass-card"><h3>📲 Conversa Iniciada</h3><p style="background:#056162; padding:15px; border-radius:15px 15px 0 15px;"><b>Bony Silva:</b> Opa! Pagamento confirmado. Já estou saindo com as ferramentas! 🛠️</p></div>', unsafe_allow_html=True)
    if st.button("Nova Busca"):
        st.session_state.etapa = 'busca'; st.rerun()
