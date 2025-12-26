import streamlit as st
import random
import time

# 1. Configurações de página
st.set_page_config(page_title="GeralJá | Elite HUB", layout="wide", initial_sidebar_state="collapsed")

# 2. Inicialização de Memória (Session State)
if 'radar_ligado' not in st.session_state:
    st.session_state.radar_ligado = False
if 'servico' not in st.session_state:
    st.session_state.servico = "Pintura"

# 3. Estilo CSS (Foco em Reatividade)
st.markdown("""
    <style>
    .stApp { background: #050a10; color: #e0e0e0; }
    .brand-header {
        background: linear-gradient(90deg, #004a8c 0%, #0d1117 100%);
        padding: 20px; border-radius: 0 0 20px 20px; text-align: center;
        border-bottom: 2px solid #f39c12; margin-bottom: 20px;
    }
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px; padding: 20px; margin-top: 10px;
    }
    /* Estilo dos botões de categoria para parecerem ativos */
    .btn-cat {
        background: #1a2a40; color: white; padding: 10px; 
        border-radius: 10px; text-align: center; border: 1px solid #34495e;
        margin: 5px; cursor: pointer;
    }
    </style>
""", unsafe_allow_html=True)

# Cabeçalho
st.markdown('<div class="brand-header"><h1 style="font-size: 35px; font-weight: 900; margin: 0;">GERAL<span style="color:#f39c12">JÁ</span></h1></div>', unsafe_allow_html=True)

tab_busca, tab_pro = st.tabs(["🔍 RADAR", "👷 SOU PROFISSIONAL"])

with tab_busca:
    st.markdown("### 🛠️ Escolha o Serviço")
    
    # Seleção por rádio (mais estável para celular que botões soltos)
    opcao = st.radio("", ["🎨 Pintura", "⚡ Elétrica", "🚰 Hidráulica", "🧹 Limpeza"], horizontal=True)
    st.session_state.servico = opcao

    local = st.text_input("📍 Onde você está?", placeholder="Ex: Rua Jequirituba, 100")

    # Botão de Busca (Este reage e muda o estado)
    if st.button("🚀 ATIVAR RADAR AGORA", use_container_width=True):
        st.session_state.radar_ligado = True
        with st.spinner("Buscando no Grajaú..."):
            time.sleep(1)

    # Exibição do Resultado (Só aparece se o radar estiver ligado)
    if st.session_state.radar_ligado:
        valor = random.randint(160, 280)
        st.markdown(f"""
            <div class="glass-card">
                <span style="color:#27ae60; font-weight:bold; font-size:12px;">● PROFISSIONAL DISPONÍVEL</span>
                <h2 style="margin:5px 0;">Bony Silva</h2>
                <p style="color:#bdc3c7; margin:0;">Especialista em {st.session_state.servico}</p>
                <h1 style="color:#f39c12; margin:10px 0;">R$ {valor},00</h1>
                <hr style="opacity:0.1">
                <p style="font-size:12px; color:gray;">Pagamento via PIX com Garantia GeralJá</p>
            </div>
        """, unsafe_allow_html=True)
        
        # O BOTÃO QUE REAGE: Link direto via HTML (funciona 100% no celular)
        link_zap = f"https://wa.me/5511991853488?text=Olá! Quero contratar o {st.session_state.servico} (Bony Silva) no endereço: {local}. Valor: R${valor}"
        
        st.markdown(f'''
            <a href="{link_zap}" target="_blank" style="text-decoration:none;">
                <div style="background: linear-gradient(90deg, #25d366, #128c7e); color:white; padding:18px; 
                text-align:center; border-radius:15px; font-weight:bold; font-size:18px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                    ✅ CONTRATAR VIA WHATSAPP
                </div>
            </a>
        ''', unsafe_allow_html=True)

with tab_pro:
    st.markdown("### 👷 Área do Prestador")
    st.info("Cadastre-se para receber chamados no seu celular.")
    st.markdown('<a href="https://forms.gle/WWj6XcbLEbcttbe76" target="_blank" style="text-decoration:none;"><div style="background:#f39c12; color:white; padding:15px; text-align:center; border-radius:10px; font-weight:bold;">📝 INICIAR CADASTRO</div></a>', unsafe_allow_html=True)

st.markdown("<br><p style='text-align:center; color:gray; font-size:10px;'>GeralJá v2.8 - Grajaú SP</p>", unsafe_allow_html=True)
