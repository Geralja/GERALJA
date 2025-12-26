import streamlit as st
import random
import time

# Configurações de página
st.set_page_config(page_title="GeralJá | Elite HUB", layout="wide", initial_sidebar_state="collapsed")

# Inicializar estados (Para os botões funcionarem)
if 'radar_ativo' not in st.session_state:
    st.session_state.radar_ativo = False
if 'servico_selecionado' not in st.session_state:
    st.session_state.servico_selecionado = "Pintura"

# Estilo CSS Profissional
st.markdown("""
    <style>
    .stApp { background: #050a10; color: #e0e0e0; }
    .brand-header {
        background: linear-gradient(90deg, #004a8c 0%, #0d1117 100%);
        padding: 25px; border-radius: 0 0 25px 25px; text-align: center;
        border-bottom: 2px solid #f39c12; margin-bottom: 30px;
    }
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px; padding: 20px; margin-top: 20px;
    }
    .stButton>button {
        background: linear-gradient(90deg, #f39c12 0%, #d35400 100%) !important;
        color: white !important; border-radius: 12px !important; border: none !important;
        font-weight: 700 !important; width: 100%; height: 45px;
    }
    </style>
""", unsafe_allow_html=True)

# Cabeçalho
st.markdown('<div class="brand-header"><h1 style="font-size: 40px; font-weight: 900; margin: 0;">GERAL<span style="color:#f39c12">JÁ</span></h1><p style="color:#bdc3c7;">O HUB DE SERVIÇOS DO GRAJAÚ</p></div>', unsafe_allow_html=True)

tab_busca, tab_pro = st.tabs(["🔍 RADAR", "👷 SOU PROFISSIONAL"])

with tab_busca:
    st.markdown("### Selecione o Serviço:")
    
    # Grid de Categorias (Botões que agora guardam a escolha)
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("🎨 Pintura"): st.session_state.servico_selecionado = "Pintura"
    if c2.button("⚡ Elétrica"): st.session_state.servico_selecionado = "Elétrica"
    if c3.button("🚰 Hidráulica"): st.session_state.servico_selecionado = "Hidráulica"
    if c4.button("🧹 Limpeza"): st.session_state.servico_selecionado = "Limpeza"

    st.info(f"Selecionado: **{st.session_state.servico_selecionado}**")
    
    local = st.text_input("📍 Onde será o serviço?", placeholder="Ex: Rua Jequirituba...")

    # Ativar Radar
    if st.button("🚀 BUSCAR PROFISSIONAIS AGORA"):
        st.session_state.radar_ativo = True
        with st.spinner("Escaneando profissionais no Grajaú..."):
            time.sleep(1.5)

    # Se o radar foi ativado, mostra o resultado
    if st.session_state.radar_ativo:
        valor = random.randint(150, 300)
        st.markdown(f"""
            <div class="glass-card">
                <span style="background:#27ae60; padding:4px 10px; border-radius:50px; font-size:10px; font-weight:bold;">🛡️ VERIFICADO</span>
                <h2 style="margin:10px 0 0 0;">Bony Silva</h2>
                <p style="color:gray;">Especialista em {st.session_state.servico_selecionado}</p>
                <h1 style="color:#f39c12;">R$ {valor},00</h1>
            </div>
        """, unsafe_allow_html=True)
        
        # Botão de Contratação Real
        whatsapp_url = f"https://wa.me/5511991853488?text=Olá! Quero contratar {st.session_state.servico_selecionado} pelo GeralJá no endereço {local}."
        
        st.markdown(f'''
            <a href="{whatsapp_url}" target="_blank" style="text-decoration:none;">
                <div style="background:#25d366; color:white; padding:15px; text-align:center; border-radius:12px; font-weight:bold; margin-top:10px;">
                    ✅ CONFIRMAR E CHAMAR NO WHATSAPP
                </div>
            </a>
        ''', unsafe_allow_html=True)

with tab_pro:
    st.subheader("Trabalhe Conosco")
    st.markdown("""
    Faça parte do HUB que mais cresce na Zona Sul.
    <br><br>
    <a href="https://forms.gle/WWj6XcbLEbcttbe76" target="_blank">
        <button style="width:100%; background:#f39c12; border:none; color:white; padding:15px; border-radius:12px; font-weight:bold;">📝 QUERO ME CADASTRAR</button>
    </a>
    """, unsafe_allow_html=True)
