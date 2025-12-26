import streamlit as st
import random
import time

# --- 1. CONFIGURAÇÃO DE ELITE ---
st.set_page_config(page_title="GeralJá | Elite HUB", layout="centered", initial_sidebar_state="collapsed")

# --- 2. CSS ULTRA MODERNO (GLASSMORPHISM) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: radial-gradient(circle at top, #1a2a40 0%, #050a10 100%); color: white; }

    /* Efeito de Vidro (Glass) */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 25px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }

    /* Radar Animado */
    .radar-container { position: relative; width: 100px; height: 100px; margin: 0 auto; }
    .circle {
        position: absolute; width: 100%; height: 100%;
        background: #f39c12; border-radius: 50%; opacity: 0;
        animation: scaleIn 2s infinite cubic-bezier(.36, .11, .89, .32);
    }
    .circle:nth-child(2) { animation-delay: 0.5s; }
    .circle:nth-child(3) { animation-delay: 1s; }
    @keyframes scaleIn {
        from { transform: scale(0.5); opacity: 0.5; }
        to { transform: scale(2.5); opacity: 0; }
    }

    /* Botão Premium */
    .stButton>button {
        background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%) !important;
        border: none !important; color: white !important;
        padding: 15px !important; border-radius: 16px !important;
        font-weight: 900 !important; transition: 0.3s !important;
        box-shadow: 0 4px 15px rgba(243, 156, 18, 0.3) !important;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 6px 20px rgba(243, 156, 18, 0.5) !important; }

    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. LÓGICA DE ESTADOS ---
if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'

# --- 4. TELA DE ABERTURA (MODERNA) ---
if 'abertura' not in st.session_state:
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("""
            <div style="text-align: center; margin-top: 20vh;">
                <div class="radar-container">
                    <div class="circle"></div>
                    <div class="circle"></div>
                    <div class="circle"></div>
                    <div style="position:relative; font-size:40px; top:25px;">🛰️</div>
                </div>
                <h1 style="color:#f39c12; font-size:50px; margin-top:50px; font-weight:900;">GERAL<span style="color:white">JÁ</span></h1>
                <p style="color:#3498db; letter-spacing:5px; font-size:12px;">SISTEMA DE RADAR ATIVO</p>
            </div>
        """, unsafe_allow_html=True)
        time.sleep(3)
    st.session_state.abertura = True
    placeholder.empty()

# --- 5. NAVEGAÇÃO DO APP ---
if st.session_state.get('abertura'):

    # ETAPA: BUSCA
    if st.session_state.etapa == 'busca':
        st.markdown("<h2 style='text-align:center;'>O que você precisa hoje?</h2>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            servico = st.selectbox("Serviço", ["Selecione...", "Pintor", "Eletricista", "Encanador", "Diarista", "Pedreiro"])
            endereco = st.text_input("📍 Seu Endereço (Grajaú)")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if st.button("BUSCAR AGORA"):
                if servico != "Selecione..." and endereco:
                    st.session_state.servico = servico
                    st.session_state.etapa = 'resultado'
                    st.rerun()
                else:
                    st.warning("Preencha os campos para ativar o radar.")

    # ETAPA: RESULTADO
    elif st.session_state.etapa == 'resultado':
        st.markdown(f"<h3 style='text-align:center;'>Profissional Disponível</h3>", unsafe_allow_html=True)
        
        st.markdown(f"""
            <div class="glass-card" style="text-align:center;">
                <div style="font-size:50px;">👨‍🔧</div>
                <h2 style="margin:5px 0; color:#f39c12;">Bony Silva</h2>
                <p style="color:#27ae60; font-weight:bold;">⭐ 4.9 (248 serviços feitos)</p>
                <hr style="opacity:0.1">
                <p style="color:gray;">Valor do serviço estimado:</p>
                <h1 style="margin:0;">R$ {random.randint(180, 400)},00</h1>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("💳 CONTRATAR COM SEGURO GERALJÁ"):
            st.session_state.etapa = 'pagamento'
            st.rerun()
        if st.button("⬅️ VOLTAR", type="secondary"):
            st.session_state.etapa = 'busca'
            st.rerun()

    # ETAPA: PAGAMENTO (10% TAXA)
    # --- ETAPA 3: PAGAMENTO (PIX COM QR CODE E COPIA/COLA) ---
    elif st.session_state.etapa == 'pagamento':
        total = st.session_state.valor_total
        # Chave aleatória fictícia para o design
        chave_aleatoria = "00020101021226850014br.gov.bcb.pix0123geralja88991122334455"
        
        st.markdown("<h3 style='text-align:center;'>Finalizar Pagamento</h3>", unsafe_allow_html=True)
        
        # Card de Pagamento Estilo Banco Digital
        st.markdown(f"""
            <div class="glass-card" style="background:white; color:black; text-align:center;">
                <p style="color:#777; font-size:12px; margin-bottom:5px;">VALOR A PAGAR</p>
                <h1 style="margin:0; color:#27ae60; font-size:40px;">R$ {total},00</h1>
                
                <div style="margin: 20px 0;">
                    <p style="font-size:14px; font-weight:bold; color:#333;">Escaneie o QR Code abaixo:</p>
                    <img src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={chave_aleatoria}" 
                         style="border: 10px solid #f9f9f9; border-radius:15px; width:180px;">
                </div>
                
                <hr style="opacity:0.1">
                
                <p style="font-size:13px; color:#555; margin-bottom:10px;">Ou use o Pix Copia e Cola:</p>
                <div style="background:#f0f0f0; padding:15px; border-radius:12px; border: 1px dashed #ccc;">
                    <code style="font-size:11px; word-break: break-all; color:#333;">{chave_aleatoria}</code>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Botão de ação para simular o "Copiar"
        if st.button("📋 COPIAR CHAVE PIX"):
            # No Streamlit, a cópia real precisa de componentes extras, 
            # mas aqui simulamos visualmente para o usuário.
            st.toast("Chave copiada para a área de transferência!", icon="✅")

        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("✅ JÁ REALIZEI O PAGAMENTO"):
            with st.spinner('Validando transação com o banco...'):
                time.sleep(2)
                st.balloons()
                st.success("Pagamento confirmado! O profissional Bony Silva recebeu seu chamado.")
                st.info("📱 O contato dele foi enviado para o seu WhatsApp cadastrado.")
                
                if st.button("Voltar para o Início"):
                    st.session_state.etapa = 'busca'
                    st.rerun()
        st.markdown("<h3 style='text-align:center;'>Finalizar Contratação</h3>", unsafe_allow_html=True)
        st.markdown("""
            <div class="glass-card" style="background:white; color:black;">
                <p style="color:gray; font-size:12px; margin:0;">PAGAMENTO SEGURO PIX</p>
                <h2 style="margin:0; color:#27ae60;">Copie e Cole</h2>
                <code style="background:#f0f0f0; padding:10px; display:block; border-radius:8px; margin:15px 0;">11991853488</code>
                <p style="font-size:11px; color:#555;">O <b>GeralJá</b> segura seu dinheiro por 24h após o serviço para garantir que tudo ficou perfeito. Taxa de proteção inclusa (10%).</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("✅ CONFIRMAR PAGAMENTO"):
            st.balloons()
            st.success("Pagamento enviado para análise! O profissional vai te chamar no WhatsApp.")
            if st.button("Fazer outra busca"):
                st.session_state.etapa = 'busca'
                st.rerun()

