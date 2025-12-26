import streamlit as st
import random
import time

# --- 1. CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="GeralJá | Gestão Pro", layout="centered")

st.markdown("""
    <style>
    .stApp { background: #050a10; color: white; }
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 20px; padding: 20px; margin-bottom: 20px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .stat-box {
        background: #f39c12; color: black; padding: 15px;
        border-radius: 10px; text-align: center; font-weight: bold;
    }
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 2. BANCO DE DADOS TEMPORÁRIO (Sessão) ---
if 'lucro_total' not in st.session_state: st.session_state.lucro_total = 0.0
if 'pedidos_totais' not in st.session_state: st.session_state.pedidos_totais = 0
if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'

# --- 3. BARRA LATERAL (PAINEL DO DONO) ---
with st.sidebar:
    st.title("🔑 Área Admin")
    senha = st.text_input("Senha do Dono", type="password")
    if senha == "admin123":
        st.markdown("### 💰 Faturamento GeralJá")
        st.metric("Seu Lucro (10%)", f"R$ {st.session_state.lucro_total:.2f}")
        st.metric("Pedidos Concluídos", st.session_state.pedidos_totais)
        if st.button("Zerar Caixa"): 
            st.session_state.lucro_total = 0
            st.rerun()

# --- 4. FLUXO DO APP ---

# ETAPA 1: BUSCA COM URGÊNCIA
if st.session_state.etapa == 'busca':
    st.markdown("<h1 style='text-align:center; color:#f39c12;'>GERALJÁ</h1>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        servico = st.selectbox("O que precisa?", ["Pintor", "Eletricista", "Encanador", "Diarista"])
        urgencia = st.select_slider("Qual a urgência?", options=["Hoje", "Urgente", "Emergência 🔥"])
        rua = st.text_input("📍 Endereço no Grajaú")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("ATIVAR RADAR"):
            if rua:
                st.session_state.servico = servico
                st.session_state.urgencia = urgencia
                st.session_state.distancia = round(random.uniform(0.5, 4.5), 1)
                st.session_state.etapa = 'resultado'
                st.rerun()

# ETAPA 2: RESULTADO COM DISTÂNCIA E PREÇO DINÂMICO
elif st.session_state.etapa == 'resultado':
    # Preço base + taxa de urgência
    base = random.randint(150, 250)
    adicional = 50 if "Emergência" in st.session_state.urgencia else 0
    st.session_state.valor_total = base + adicional
    
    st.markdown(f"### 📍 Profissional a {st.session_state.distancia} km de você")
    
    st.markdown(f"""
        <div class="glass-card">
            <h2 style="color:#f39c12; margin:0;">Bony Silva</h2>
            <p>⭐ 4.9 | Especialista Verificado</p>
            <hr opacity="0.1">
            <p style="font-size:14px;">Nível de Urgência: <b>{st.session_state.urgencia}</b></p>
            <h1 style="margin:0;">R$ {st.session_state.valor_total},00</h1>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("💳 IR PARA PAGAMENTO"):
        st.session_state.etapa = 'pagamento'
        st.rerun()

# ETAPA 3: PAGAMENTO E CONTABILIDADE
elif st.session_state.etapa == 'pagamento':
    total = st.session_state.valor_total
    taxa_dono = total * 0.10
    
    st.markdown("### 💳 Pagamento Seguro")
    st.markdown(f"""
        <div class="glass-card" style="background:white; color:black; text-align:center;">
            <p style="margin:0; color:gray;">VALOR TOTAL</p>
            <h1 style="margin:0; color:#27ae60;">R$ {total},00</h1>
            <br>
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=geralja-pix-ficticio">
            <p style="font-size:12px; margin-top:10px;">Chave: 11991853488</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("✅ CONFIRMAR PAGAMENTO"):
        # CONTABILIZA O LUCRO PRO DONO
        st.session_state.lucro_total += taxa_dono
        st.session_state.pedidos_totais += 1
        
        st.balloons()
        st.success(f"Pagamento de R$ {total} confirmado!")
        st.info(f"O GeralJá reteve sua comissão de R$ {taxa_dono:.2f} (10%)")
        
        if st.button("Voltar ao Início"):
            st.session_state.etapa = 'busca'
            st.rerun()
