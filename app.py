import streamlit as st
import random
import time

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="GeralJá | Elite HUB", layout="wide", initial_sidebar_state="collapsed")

# --- 2. ESTILO CSS REVISADO ---
st.markdown("""
    <style>
    .stApp { background: #050a10; color: white; }
    
    /* Splash Screen sem erro de imagem */
    @keyframes fadeIn { from { opacity: 0; transform: scale(0.9); } to { opacity: 1; transform: scale(1); } }
    
    .splash { 
        text-align: center; 
        margin-top: 15vh; 
        animation: fadeIn 1.5s ease-out; 
    }
    
    /* Círculo de Humanização com Emoji (Garante que não apareça a mãozinha) */
    .hero-circle {
        width: 150px; height: 150px;
        background: linear-gradient(135deg, #f39c12 0%, #d35400 100%);
        margin: 0 auto;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 80px;
        box-shadow: 0 0 30px rgba(243, 156, 18, 0.4);
        border: 4px solid white;
    }

    .checkout-card { 
        background: white; color: black; padding: 25px; 
        border-radius: 20px; text-align: center; border: 4px solid #27ae60; 
    }
    
    .stButton>button {
        background: #f39c12 !important;
        color: white !important; border-radius: 12px !important;
        font-weight: 700 !important; width: 100%; height: 50px;
        border: none !important;
    }
    
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. LÓGICA DE ABERTURA ---
if 'abertura_concluida' not in st.session_state:
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("""
            <div class="splash">
                <div class="hero-circle">🤝</div>
                <h1 style="color:#f39c12; font-size:55px; margin-top:20px; font-weight:900; letter-spacing:-2px;">
                    GERAL<span style="color:white">JÁ</span>
                </h1>
                <p style="color:gray; letter-spacing:4px; font-size:14px;">O RADAR DO GRAJAÚ</p>
                <div style="margin-top:40px; color:#3498db;">🚀 Conectando profissionais...</div>
            </div>
        """, unsafe_allow_html=True)
        time.sleep(3) 
    st.session_state.abertura_concluida = True
    placeholder.empty()

# --- 4. CONTEÚDO PRINCIPAL ---
if st.session_state.get('abertura_concluida'):
    
    if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'
    if 'valor_total' not in st.session_state: st.session_state.valor_total = 0
    
    st.markdown('<h2 style="text-align:center; color:#f39c12;">GERALJÁ</h2>', unsafe_allow_html=True)

    # --- BUSCA ---
    if st.session_state.etapa == 'busca':
        st.markdown("### 🔍 O que você precisa hoje?")
        escolha = st.selectbox("Escolha o serviço:", ["", "Pintor", "Eletricista", "Encanador", "Diarista", "Pedreiro"])
        rua = st.text_input("📍 Seu endereço no bairro:")

        if st.button("BUSCAR PROFISSIONAL"):
            if escolha != "" and rua != "":
                st.session_state.profissao = escolha
                st.session_state.etapa = 'resultado'
                st.rerun()
            else:
                st.warning("Preencha todos os campos!")

    # --- RESULTADO ---
    elif st.session_state.etapa == 'resultado':
        if st.session_state.valor_total == 0:
            st.session_state.valor_total = random.randint(180, 450)
        
        st.markdown(f"### Profissional encontrado!")
        st.markdown(f"""
            <div style="background: rgba(255,255,255,0.05); padding:20px; border-radius:15px; border-left: 6px solid #f39c12;">
                <h2 style="margin:0;">Bony Silva</h2>
                <p style="margin:0; color:#27ae60;">⭐ 4.9 | Especialista em {st.session_state.profissao}</p>
                <h1 style="color:#f39c12; margin:15px 0;">R$ {st.session_state.valor_total},00</h1>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("💳 CONTRATAR E PAGAR (VIA PIX)"):
            st.session_state.etapa = 'pagamento'
            st.rerun()
        if st.button("⬅️ VOLTAR"):
            st.session_state.etapa = 'busca'
            st.rerun()

    # --- PAGAMENTO (TAXA 10%) ---
    elif st.session_state.etapa == 'pagamento':
        total = st.session_state.valor_total
        taxa = total * 0.10
        pro = total - taxa
        
        st.markdown("### 💳 Pagamento Seguro")
        st.markdown(f"""
            <div class="checkout-card">
                <p style="margin:0; color:gray;">VALOR TOTAL</p>
                <h1 style="margin:0; font-size:45px; color:#27ae60;">R$ {total},00</h1>
                <hr>
                <p style="font-weight:bold;">Chave PIX GeralJá:</p>
                <code style="background:#eee; padding:10px; display:block; border-radius:8px; font-size:20px; color:black;">11991853488</code>
                <br>
                <p style="text-align:left; font-size:12px; color:#666;">
                    ✅ <b>Garantia:</b> O GeralJá retém o valor e só paga R$ {pro:.2f} ao profissional após sua confirmação.
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("✅ JÁ REALIZEI O PIX"):
            st.success("Pagamento identificado! Aguarde o contato do especialista.")
            st.balloons()
