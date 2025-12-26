import streamlit as st
import random
import time

# --- 1. CONFIGURAÇÃO DA PLATAFORMA ---
st.set_page_config(page_title="GeralJá | Elite HUB", layout="centered", initial_sidebar_state="collapsed")

# --- 2. BANCO DE DADOS DE SESSÃO ---
if 'lucro_plataforma' not in st.session_state: st.session_state.lucro_plataforma = 0.0
if 'pedidos_concluidos' not in st.session_state: st.session_state.pedidos_concluidos = 0
if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'

if 'db_pros' not in st.session_state:
    st.session_state.db_pros = {
        "BONY77": {"nome": "Bony Silva", "cargo": "Eletricista", "saldo": 0.0, "status": "Ativo", "lat": -23.7750, "lon": -46.6650},
        "MARIA22": {"nome": "Maria Limpeza", "cargo": "Diarista", "saldo": 0.0, "status": "Ativo", "lat": -23.7650, "lon": -46.6750},
        "MARCOS55": {"nome": "Marcos Pintor", "cargo": "Pintor", "saldo": 0.0, "status": "Ativo", "lat": -23.7850, "lon": -46.6550},
    }

LISTA_PROS = sorted(["Pintor", "Eletricista", "Encanador", "Diarista", "Pedreiro", "Montador de Móveis", "Mecânico", "Jardineiro", "Chaveiro"])

# --- 3. ESTILO CSS (MODERNIZAÇÃO DARK) ---
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
        width: 100%; height: 50px; text-transform: uppercase;
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
    elif token == "":
        pass
    else:
        st.error("Token inválido")

# --- 5. LOGICA DE NAVEGAÇÃO ---

# VISÃO ADMIN
if st.session_state.etapa == 'admin':
    st.title("📊 Painel do Nodo (Dono)")
    col1, col2 = st.columns(2)
    col1.metric("Faturamento (10%)", f"R$ {st.session_state.lucro_plataforma:.2f}")
    col2.metric("Serviços Hoje", st.session_state.pedidos_concluidos)

    t1, t2, t3 = st.tabs(["✅ Ativos", "❄️ Bloqueados", "🗑️ Lixeira"])
    
    with t1:
        for tok, d in st.session_state.db_pros.items():
            if d['status'] == 'Ativo':
                with st.expander(f"🟢 {d['nome']}"):
                    st.write(f"Saldo: R$ {d['saldo']:.2f}")
                    if st.button(f"Bloquear {d['nome']}", key=f"blk_{tok}"):
                        d['status'] = 'Bloqueado'; st.rerun()

    with t2:
        for tok, d in st.session_state.db_pros.items():
            if d['status'] == 'Bloqueado':
                st.error(f"Bloqueado: {d['nome']}")
                if st.button(f"🔓 Desfazer Bloqueio", key=f"re_at_{tok}"):
                    d['status'] = 'Ativo'; st.rerun()
                if st.button(f"🗑️ Mover p/ Lixeira", key=f"mov_lix_{tok}"):
                    d['status'] = 'Excluído'; st.rerun()

    with t3:
        for tok, d in st.session_state.db_pros.items():
            if d['status'] == 'Excluído':
                st.warning(f"Excluído: {d['nome']}")
                if st.button(f"♻️ Restaurar Profissional", key=f"rest_{tok}"):
                    d['status'] = 'Ativo'; st.rerun()

# VISÃO CLIENTE (BUSCA)
elif st.session_state.etapa == 'busca':
    st.markdown("<h1 style='text-align:center; color:#f39c12; font-size:45px;'>GERAL<span style='color:white'>JÁ</span></h1>", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        servico = st.selectbox("O que você precisa hoje?", [""] + LISTA_PROS)
        urgencia = st.select_slider("Urgência", options=["Hoje", "Urgente", "Emergência 🔥"])
        rua = st.text_input("📍 Seu Endereço no Grajaú")
        st.markdown('</div>', unsafe_allow_html=True)
        if st.button("ATIVAR RADAR"):
            if servico and rua:
                st.session_state.servico_busca = servico
                st.session_state.etapa = 'resultado'
                st.rerun()

# VISÃO RESULTADO COM MAPA
elif st.session_state.etapa == 'resultado':
    st.markdown("### 📍 Profissional Localizado")
    
    # Simulação de Mapa moderno (Integrado ao design)
    st.markdown("""
        <div style="width:100%; height:250px; background: url('https://api.mapbox.com/styles/v1/mapbox/dark-v10/static/pin-s+f39c12(-46.6682,-23.7721)/-46.6682,-23.7721,13/600x250?access_token=pk.eyJ1IjoiZ3VpZG94IiwiYSI6ImNrZnduZnR4MDBhNnoycnBnbm9idG9yejkifQ.7Wp6M_2yA6_z_rG-vH0Z6A'); background-size: cover; border-radius: 20px; border: 2px solid #f39c12; margin-bottom: 20px;">
        </div>
    """, unsafe_allow_html=True)
    
    preco = random.randint(180, 380)
    st.markdown(f"""
        <div class="glass-card">
            <h2 style="color:#f39c12; margin:0;">Bony Silva</h2>
            <p>⭐ 4.9 | Especialista em {st.session_state.servico_busca}</p>
            <p>📍 Localização: Cantinho do Céu - Grajaú</p>
            <hr style="opacity:0.1">
            <h1 style="margin:0;">R$ {preco},00</h1>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("💳 CONTRATAR E PAGAR AGORA"):
        st.session_state.valor_final = preco
        st.session_state.etapa = 'pagamento'
        st.rerun()
    if st.button("⬅ Voltar"):
        st.session_state.etapa = 'busca'; st.rerun()

# VISÃO PAGAMENTO
elif st.session_state.etapa == 'pagamento':
    val = st.session_state.valor_final
    st.markdown("<h3 style='text-align:center;'>Pagamento via PIX</h3>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class="glass-card" style="background:white; color:black; text-align:center;">
            <p style="color:gray; margin:0;">VALOR TOTAL</p>
            <h1 style="margin:0; color:#27ae60;">R$ {val},00</h1>
            <br>
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=GeralJa-{val}" style="border-radius:10px;">
            <p style="font-size:12px; margin-top:10px;"><b>Chave PIX:</b> 11991853488</p>
        </div>
    """, unsafe_allow_html=True)
    if st.button("✅ JÁ REALIZEI O PAGAMENTO"):
        st.session_state.lucro_plataforma += (val * 0.10)
        st.session_state.pedidos_concluidos += 1
        st.session_state.etapa = 'chat_sucesso'
        st.rerun()

# VISÃO SUCESSO / CHAT
elif st.session_state.etapa == 'chat_sucesso':
    st.balloons()
    st.markdown("""
        <div class="glass-card">
            <h3 style="color:#27ae60;">📲 Conexão Confirmada!</h3>
            <div style="background:#056162; padding:15px; border-radius:15px 15px 0 15px; margin-top:20px;">
                <b>Bony Silva:</b><br>
                Opa! Acabei de receber a confirmação do GeralJá. Já estou pegando as ferramentas aqui no Grajaú e chego no seu endereço em 15 min! 🛠️🚀
            </div>
            <p style="font-size:12px; color:gray; margin-top:15px; text-align:center;">O profissional recebeu seu contato de WhatsApp.</p>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Nova Busca"):
        st.session_state.etapa = 'busca'; st.rerun()
