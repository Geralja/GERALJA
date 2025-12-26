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

# --- 3. CSS COM EFEITO DE BRILHO (GLOW) ---
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top, #1a2a40 0%, #050a10 100%); color: white; }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(12px);
        border-radius: 20px; padding: 25px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px;
    }

    /* BOTÃO COM BRILHO E PULSAÇÃO */
    div.stButton > button {
        background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 15px 25px !important;
        font-weight: 900 !important;
        font-size: 18px !important;
        transition: all 0.3s ease-in-out !important;
        box-shadow: 0 0 15px rgba(243, 156, 18, 0.5) !important;
        width: 100% !important;
        animation: pulse-glow 2s infinite !important;
    }

    @keyframes pulse-glow {
        0% { box-shadow: 0 0 5px rgba(243, 156, 18, 0.5); transform: scale(1); }
        50% { box-shadow: 0 0 25px rgba(243, 156, 18, 0.9); transform: scale(1.02); }
        100% { box-shadow: 0 0 5px rgba(243, 156, 18, 0.5); transform: scale(1); }
    }

    div.stButton > button:hover {
        background: #f1c40f !important;
        box-shadow: 0 0 35px rgba(241, 196, 15, 1) !important;
    }
    
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 4. ROTEAMENTO DE ETAPAS ---

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

# ETAPA: BUSCA (CORRIGIDO)
elif st.session_state.etapa == 'busca':
    st.markdown("<h1 style='text-align:center; color:#f39c12;'>GERALJÁ</h1>", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        servico_input = st.selectbox("Qual profissional você precisa?", [""] + LISTA_PROS, key="sel_servico")
        rua_input = st.text_input("📍 Seu Endereço no Grajaú", key="inp_rua")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Botão com lógica de transição explícita
        if st.button("ATIVAR RADAR 🛰️"):
            if servico_input != "" and rua_input != "":
                st.session_state.servico_busca = servico_input
                st.session_state.etapa = 'resultado'
                st.rerun()
            else:
                st.warning("⚠️ Selecione a profissão e digite seu endereço.")

# ETAPA: RESULTADO
elif st.session_state.etapa == 'resultado':
    st.markdown("### 📍 Localizado no Grajaú")
    st.markdown("""<div style="width:100%; height:180px; background: url('https://api.mapbox.com/styles/v1/mapbox/dark-v10/static/-46.6682,-23.7721,13/600x180?access_token=pk.eyJ1IjoiZ3VpZG94IiwiYSI6ImNrZnduZnR4MDBhNnoycnBnbm9idG9yejkifQ.7Wp6M_2yA6_z_rG-vH0Z6A'); background-size: cover; border-radius: 15px; border: 1px solid #f39c12;"></div>""", unsafe_allow_html=True)
    
    preco = random.randint(180, 400)
    st.markdown(f'<div class="glass-card"><h2>Bony Silva</h2><p>⭐ 4.9 | {st.session_state.servico_busca}</p><h1>R$ {preco},00</h1></div>', unsafe_allow_html=True)
    
    if st.button("💳 CONTRATAR"):
        st.session_state.valor_final = preco
        st.session_state.etapa = 'pagamento'
        st.rerun()
    if st.button("⬅ Voltar"):
        st.session_state.etapa = 'busca'; st.rerun()

# ETAPA: PAGAMENTO
elif st.session_state.etapa == 'pagamento':
    val = st.session_state.valor_final
    st.markdown("<h3 style='text-align:center;'>Pagamento via PIX</h3>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class="glass-card" style="background:white; color:black; text-align:center;">
            <p style="color:gray;">TOTAL: <b>R$ {val},00</b></p>
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={CHAVE_PIX_ALERATORIA}" style="margin:10px;">
            <p style="font-size:10px; color:#555;">CHAVE ALEATÓRIA:</p>
            <code style="word-break:break-all; font-size:11px;">{CHAVE_PIX_ALERATORIA}</code>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("✅ JÁ REALIZEI O PAGAMENTO"):
        st.session_state.lucro_plataforma += (val * 0.10)
        st.session_state.pedidos_concluidos += 1
        st.session_state.etapa = 'chat_sucesso'
        st.rerun()

# ETAPA: CHAT SUCESSO
elif st.session_state.etapa == 'chat_sucesso':
    st.balloons()
    st.markdown('<div class="glass-card"><h3>📲 Conversa Iniciada</h3><p style="background:#056162; padding:15px; border-radius:15px 15px 0 15px;"><b>Bony Silva:</b> Pagamento confirmado! Já estou preparando as ferramentas para ir até você! 🛠️</p></div>', unsafe_allow_html=True)
    if st.button("Nova Busca"):
        st.session_state.etapa = 'busca'; st.rerun()

# BARRA LATERAL (ACESSAR ADMIN)
with st.sidebar:
    st.title("🔐 Acesso")
    token = st.text_input("Senha Admin", type="password")
    if token == "admin777":
        st.session_state.etapa = 'admin'
        st.rerun()
