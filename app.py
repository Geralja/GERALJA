import streamlit as st
import random
import time

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="GeralJá | Elite HUB", layout="wide", initial_sidebar_state="collapsed")

# --- 2. ESTILO CSS COMPLETO (Design, Animações e Cores) ---
st.markdown("""
    <style>
    .stApp { background: #050a10; color: white; }
    
    /* Splash Screen Animada */
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    .splash { text-align: center; margin-top: 15vh; animation: fadeIn 2s; }
    
    .hero-avatar {
        width: 180px; height: 180px;
        background: url('https://cdn-icons-png.flaticon.com/512/9437/9437568.png') no-repeat center;
        background-size: contain; margin: 0 auto;
        border: 4px solid #f39c12; border-radius: 50%; background-color: white;
    }

    /* Cards e Botões */
    .checkout-card { 
        background: white; color: black; padding: 25px; 
        border-radius: 20px; text-align: center; border: 4px solid #27ae60; 
    }
    .stButton>button {
        background: linear-gradient(90deg, #f39c12 0%, #d35400 100%) !important;
        color: white !important; border-radius: 12px !important; border: none !important;
        font-weight: 700 !important; width: 100%; height: 45px;
    }
    
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. LÓGICA DE ABERTURA (Splash Screen) ---
if 'abertura_concluida' not in st.session_state:
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("""
            <div class="splash">
                <div class="hero-avatar"></div>
                <h1 style="color:#f39c12; font-size:50px; margin-top:20px; font-weight:900;">GERAL<span style="color:white">JÁ</span></h1>
                <p style="color:gray; letter-spacing:3px; font-size:12px;">O HUB DE SERVIÇOS DO GRAJAÚ</p>
                <div style="margin-top:30px;"><small style="color:#3498db;">Iniciando Radar Inteligente...</small></div>
            </div>
        """, unsafe_allow_html=True)
        time.sleep(3.5) 
    st.session_state.abertura_concluida = True
    placeholder.empty()

# --- 4. CONTEÚDO PRINCIPAL (Só aparece após a abertura) ---
if st.session_state.get('abertura_concluida'):
    
    # Inicialização de etapas e variáveis
    if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'
    if 'valor_total' not in st.session_state: st.session_state.valor_total = 0
    
    PROFISOES = ["Pintor", "Eletricista", "Encanador", "Diarista", "Pedreiro", "Montador de Móveis"]

    # Topo Fixo
    st.markdown('<h2 style="text-align:center; color:#f39c12; margin-bottom:30px;">GERALJÁ</h2>', unsafe_allow_html=True)

    # --- ETAPA 1: BUSCA ---
    if st.session_state.etapa == 'busca':
        st.markdown("### 🔍 O que você precisa hoje?")
        profissao_escolhida = st.selectbox("Selecione a profissão:", [""] + PROFISOES)
        local_servico = st.text_input("📍 Seu endereço no Grajaú:", placeholder="Ex: Rua Jequirituba, 100")

        if st.button("ATIVAR RADAR AGORA"):
            if profissao_escolhida != "" and local_servico != "":
                st.session_state.profissao = profissao_escolhida
                st.session_state.local = local_servico
                st.session_state.etapa = 'resultado'
                st.rerun()
            else:
                st.error("Por favor, preencha a profissão e o endereço.")

    # --- ETAPA 2: RESULTADO ---
    elif st.session_state.etapa == 'resultado':
        if st.session_state.valor_total == 0:
            st.session_state.valor_total = random.randint(180, 420)
        
        st.markdown(f"### Profissional encontrado para: **{st.session_state.profissao}**")
        st.markdown(f"""
            <div style="background: rgba(255,255,255,0.05); padding:20px; border-radius:15px; border-left: 6px solid #f39c12;">
                <h2 style="margin:0;">Bony Silva</h2>
                <p style="margin:0; color:#27ae60;">⭐ 4.9 | Especialista Verificado</p>
                <h1 style="color:#f39c12; margin:15px 0;">R$ {st.session_state.valor_total},00</h1>
                <p style="font-size:12px; color:gray;">Pagamento Seguro Intermediado pelo GeralJá.</p>
            </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("⬅️ VOLTAR"):
                st.session_state.etapa = 'busca'
                st.session_state.valor_total = 0
                st.rerun()
        with c2:
            if st.button("💳 CONTRATAR AGORA"):
                st.session_state.etapa = 'pagamento'
                st.rerun()

    # --- ETAPA 3: PAGAMENTO (CHECKOUT COM TAXA DE 10%) ---
    elif st.session_state.etapa == 'pagamento':
        total = st.session_state.valor_total
        taxa_geralja = total * 0.10  # Sua comissão de 10%
        repasse_pro = total - taxa_geralja
        
        st.markdown("### 💳 Checkout Seguro")
        st.markdown(f"""
            <div class="checkout-card">
                <p style="margin:0; color:gray; font-size:14px;">VALOR TOTAL DO SERVIÇO</p>
                <h1 style="margin:0; font-size:48px; color:#27ae60;">R$ {total},00</h1>
                <hr>
                <p style="font-weight:bold;">Chave PIX (GeralJá Intermediações):</p>
                <code style="background:#f0f0f0; padding:12px; display:block; border-radius:10px; font-size:22px; color:black;">11991853488</code>
                <br>
                <div style="text-align:left; font-size:13px; color:#555; background:#f9f9f9; padding:15px; border-radius:10px;">
                    <b>🛡️ Como funciona a sua segurança:</b><br>
                    1. Você faz o PIX de R$ {total},00.<br>
                    2. O dinheiro fica guardado com o <b>GeralJá</b>.<br>
                    3. O profissional recebe R$ {repasse_pro:.2f} só após você confirmar o serviço.<br>
                    4. Os R$ {taxa_geralja:.2f} (10%) cobrem o seguro e a garantia do app.
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("✅ JÁ REALIZEI O PAGAMENTO"):
            st.success("Pagamento em análise! O profissional entrará em contato em instantes.")
            st.balloons()
