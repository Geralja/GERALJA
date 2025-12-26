import streamlit as st
import random
import time

# Configurações de página
st.set_page_config(page_title="GeralJá | Elite HUB", layout="wide", initial_sidebar_state="collapsed")

# Estilo CSS (Design de Elite)
st.markdown("""
    <style>
    .stApp { background: #050a10; color: #e0e0e0; }
    .brand-header {
        background: linear-gradient(90deg, #004a8c 0%, #0d1117 100%);
        padding: 25px; border-radius: 0 0 25px 25px; text-align: center;
        border-bottom: 2px solid #f39c12; margin-bottom: 30px;
    }
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px; padding: 25px; margin-bottom: 20px;
    }
    .trust-badge { background: #27ae60; color: white; padding: 5px 15px; border-radius: 50px; font-size: 11px; font-weight: bold; }
    .stButton>button {
        background: linear-gradient(90deg, #f39c12 0%, #d35400 100%) !important;
        color: white !important; border-radius: 12px !important; border: none !important;
        height: 50px !important; font-weight: 700 !important; width: 100%;
    }
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Cabeçalho
st.markdown('<div class="brand-header"><h1 style="font-size: 45px; font-weight: 900; margin: 0;">GERAL<span style="color:#f39c12">JÁ</span></h1><p style="color:#bdc3c7;">O HUB DE SERVIÇOS DO GRAJAÚ</p></div>', unsafe_allow_html=True)

# Menu
tab_busca, tab_pro = st.tabs(["🔍 RADAR", "👷 SOU PROFISSIONAL"])

with tab_busca:
    st.markdown("### O que você precisa hoje?")
    col1, col2 = st.columns(2)
    with col1: st.button("🎨 Pintura")
    with col2: st.button("⚡ Elétrica")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.text_input("📍 Local do serviço", placeholder="Rua Jequirituba...")

    # BOTÃO CORRIGIDO (Lugar exato dos espaços)
    if st.button("🚀 ATIVAR RADAR GERALJÁ"):
        with st.spinner("Buscando profissionais..."):
            time.sleep(1.5)
        
        # CARD DE RESULTADO
        st.markdown(f"""
            <div class="glass-card">
                <div style="display: flex; justify-content: space-between;">
                    <span class="trust-badge">🛡️ VERIFICADO</span>
                    <span style="color:#f39c12;">📍 1.5 km</span>
                </div>
                <h2>Bony Silva</h2>
                <p>Especialista em Pintura Residencial</p>
                <div style="background: rgba(243, 156, 18, 0.1); padding: 15px; border-radius: 10px;">
                    <h1 style="color:#f39c12; margin:0;">R$ {random.randint(180, 250)},00</h1>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("✅ CONTRATAR AGORA"):
            st.balloons()
            st.success("Redirecionando para o WhatsApp de pagamento...")

with tab_pro:
    st.info("Área destinada ao cadastro de novos profissionais.")
