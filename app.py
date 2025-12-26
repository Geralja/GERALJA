import streamlit as st
import random
import time

# --- 1. CONFIGURAÇÃO DA PLATAFORMA ---
st.set_page_config(page_title="GeralJá | Elite HUB", layout="centered", initial_sidebar_state="collapsed")

# --- 2. BANCO DE DADOS DE SESSÃO (Simulando persistência na nuvem) ---
if 'lucro_plataforma' not in st.session_state: st.session_state.lucro_plataforma = 0.0
if 'pedidos_concluidos' not in st.session_state: st.session_state.pedidos_concluidos = 0
if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'

# Cadastro inicial de profissionais (Status: Ativo, Bloqueado ou Excluído)
if 'db_pros' not in st.session_state:
    st.session_state.db_pros = {
        "BONY77": {"nome": "Bony Silva", "cargo": "Eletricista", "saldo": 0.0, "status": "Ativo"},
        "MARIA22": {"nome": "Maria Limpeza", "cargo": "Diarista", "saldo": 0.0, "status": "Ativo"},
        "MARCOS55": {"nome": "Marcos Pintor", "cargo": "Pintor", "saldo": 0.0, "status": "Ativo"},
    }

LISTA_PROS = sorted(["Pintor", "Eletricista", "Encanador", "Diarista", "Pedreiro", "Montador de Móveis", "Mecânico", "Jardineiro", "Chaveiro"])

# --- 3. ESTILO CSS PARA DESIGN MOBILE-FIRST ---
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top, #1a2a40 0%, #050a10 100%); color: white; }
    .glass-card {
        background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(12px);
        border-radius: 20px; padding: 25px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px;
    }
    .stButton>button {
        background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%) !important;
        color: white !important; border-radius: 12px !important; border: none !important; font-weight: bold;
    }
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 4. ÁREA DE ACESSO (SIDEBAR OCULTA) ---
with st.sidebar:
    st.title("🔐 Portão de Acesso")
    token = st.text_input("Token ou Chave Mestra", type="password")
    if token == "admin777":
        st.session_state.etapa = 'admin'
    elif token in st.session_state.db_pros:
        st.session_state.token_ativo = token
        st.session_state.etapa = 'painel_pro'
    elif token == "":
        pass # Mantém no fluxo de cliente
    else:
        st.error("Token inválido")

# --- 5. TELA DE ABERTURA ---
if 'abertura_concluida' not in st.session_state:
    p = st.empty()
    with p.container():
        st.markdown('<div style="text-align:center; margin-top:30vh;"><h1 style="color:#f39c12; font-size:60px; font-weight:900;">GERALJÁ</h1><p style="letter-spacing:5px; color:gray;">SISTEMA NODO ATIVO</p></div>', unsafe_allow_html=True)
        time.sleep(2.5)
    st.session_state.abertura_concluida = True
    p.empty()

# --- 6. ROTEAMENTO DE VISÕES ---

# VISÃO ADMIN (VOCÊ)
if st.session_state.etapa == 'admin':
    st.title("📊 Painel do Nodo (Dono)")
    col1, col2 = st.columns(2)
    col1.metric("Lucro GeralJá (10%)", f"R$ {st.session_state.lucro_plataforma:.2f}")
    col2.metric("Total de Pedidos", st.session_state.pedidos_concluidos)

    t1, t2, t3 = st.tabs(["✅ Ativos", "❄️ Bloqueados", "🗑️ Lixeira"])
    
    with t1: # ATIVOS
        for tok, d in st.session_state.db_pros.items():
            if d['status'] == 'Ativo':
                with st.expander(f"🟢 {d['nome']}"):
                    st.write(f"Saldo Pro: R$ {d['saldo']:.2f} | Cargo: {d['cargo']}")
                    if st.button(f"Bloquear {d['nome']}", key=f"blk_{tok}"):
                        d['status'] = 'Bloqueado'; st.rerun()

    with t2: # BLOQUEADOS (OPÇÃO DE DESFAZER)
        for tok, d in st.session_state.db_pros.items():
            if d['status'] == 'Bloqueado':
                st.error(f"Bloqueado: {d['nome']}")
                if st.button(f"🔓 Reativar {d['nome']}", key=f"re_at_{tok}"):
                    d['status'] = 'Ativo'; st.rerun()
                if st.button(f"Mover p/ Lixeira {d['nome']}", key=f"mov_lix_{tok}"):
                    d['status'] = 'Excluído'; st.rerun()

    with t3: # LIXEIRA (OPÇÃO DE RESTAURAR)
        for tok, d in st.session_state.db_pros.items():
            if d['status'] == 'Excluído':
                st.warning(f"Excluído: {d['nome']}")
                if st.button(f"♻️ Restaurar {d['nome']}", key=f"rest_{tok}"):
                    d['status'] = 'Ativo'; st.rerun()

# VISÃO CLIENTE
elif st.session_state.etapa == 'busca':
    st.markdown("<h1 style='text-align:center; color:#f39c12;'>GERALJÁ</h1>", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        servico = st.selectbox("O que você procura?", [""] + LISTA_PROS)
        urgencia = st.select_slider("Urgência", options=["Hoje", "Urgente", "Emergência 🔥"])
        rua = st.text_input("📍 Seu Endereço no Grajaú")
        st.markdown('</div>', unsafe_allow_html=True)
        if st.button("ATIVAR RADAR", use_container_width=True):
            if servico and rua:
                st.session_state.servico_busca = servico
                st.session_state.etapa = 'resultado'
                st.rerun()

elif st.session_state.etapa == 'resultado':
    dist = round(random.uniform(0.5, 3.8), 1)
    preco = random.randint(160, 350)
    st.markdown(f"### 📍 Profissional a {dist}km")
    st.markdown(f'<div class="glass-card"><h2 style="color:#f39c12;">Bony Silva</h2><p>⭐ 4.9 | Verificado</p><h1>R$ {preco},00</h1></div>', unsafe_allow_html=True)
    if st.button("💳 CONTRATAR AGORA"):
        st.session_state.valor_final = preco
        st.session_state.etapa = 'pagamento'
        st.rerun()

elif st.session_state.etapa == 'pagamento':
    val = st.session_state.valor_final
    st.markdown("<h3 style='text-align:center;'>Pagamento PIX</h3>", unsafe_allow_html=True)
    st.markdown(f'<div class="glass-card" style="background:white; color:black; text-align:center;"><img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=GeralJa-{val}"/><br><br><code>11991853488</code></div>', unsafe_allow_html=True)
    if st.button("✅ JÁ REALIZEI O PAGAMENTO"):
        st.session_state.lucro_plataforma += (val * 0.10)
        st.session_state.pedidos_concluidos += 1
        st.session_state.etapa = 'chat_sucesso'
        st.rerun()

elif st.session_state.etapa == 'chat_sucesso':
    st.balloons()
    st.markdown('<div class="glass-card"><h3>📲 Conversa Iniciada</h3><p style="background:#056162; padding
