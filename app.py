import pandas as pd

# Função para carregar os profissionais da sua planilha
def carregar_profissionais():
    try:
        df = pd.read_csv('candidatos.csv')
        return df
    except:
        # Caso o arquivo não exista ainda, retorna um exemplo
        return pd.DataFrame({'Nome': ['Bony Silva'], 'Servico': ['Pintura'], 'Cidade': ['Grajaú']})
import streamlit as st
import random
import time

# 1. Configurações Iniciais
st.set_page_config(page_title="GeralJá | Elite HUB", layout="wide", initial_sidebar_state="collapsed")

# 2. Design de Elite (CSS Profissional)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
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

# --- CABEÇALHO ---
st.markdown("""
    <div class="brand-header">
        <h1 style="font-size: 45px; font-weight: 900; letter-spacing: -2px; margin: 0;">GERAL<span style="color:#f39c12">JÁ</span></h1>
        <p style="color:#bdc3c7; font-size:14px;">A PLATAFORMA DE SERVIÇOS NÚMERO 1 DO GRAJAÚ</p>
    </div>
""", unsafe_allow_html=True)

# --- NAVEGAÇÃO ---
tab_busca, tab_pro, tab_pedidos = st.tabs(["🔍 RADAR", "👷 SOU PROFISSIONAL", "📊 MEU EXTRATO"])

with tab_busca:
    st.markdown("### Qual serviço você busca hoje?")
    
    # Grid de Categorias
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.button("🎨 Pintura")
    with c2: st.button("⚡ Elétrica")
    with c3: st.button("🚰 Encanador")
    with c4: st.button("🧹 Limpeza")

    st.markdown("<br>", unsafe_allow_html=True)
    st.text_input("📍 Onde será o serviço?", placeholder="Rua Jequirituba, Grajaú...")
    
    # Ativação do Radar
    if st.button("🚀 ATIVAR RADAR GERALJÁ"):
        # Efeito de busca compatível com Windows 7
        placeholder = st.empty()
        with placeholder.container():
            with st.spinner("Buscando profissionais verificados..."):
                st.write("🛰️ Localizando profissionais próximos...")
                time.sleep(1)
                st.write("🛡️ Validando segurança e preço...")
                time.sleep(1)
        placeholder.empty()

        # CARD DO RESULTADO
        valor_simulado = random.randint(180, 290)
        st.markdown(f"""
            <div class="glass-card">
                <div style="display: flex; justify-content: space-between;">
                    <span class="trust-badge">🛡️ PARCEIRO VERIFICADO</span>
                    <span style="color:#f39c12;">📍 1.5 km de distância</span>
                </div>
                <h2 style="margin: 15px 0 5px 0;">Bony Silva</h2>
                <p style="color:#bdc3c7;">Especialista Master em Pintura Residencial</p>
                <div style="background: rgba(243, 156, 18, 0.1); padding: 15px; border-radius: 10px; margin: 15px 0;">
                    <p style="margin:0; font-size:12px; color:gray;">PREÇO FINAL (COM SEGURO GERALJÁ)</p>
                    <h1 style="margin:0; color:#f39c12;">R$ {valor_simulado},00</h1>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # AGORA A ETAPA DE CONTRATAÇÃO ORGANIZADA
        if st.button("✅ CONFIRMAR E CONTRATAR AGORA"):
            st.markdown(f"""
                <div style="background: white; color: black; padding: 25px; border-radius: 15px; text-align: center; border: 3px solid #f39c12;">
                    <h3 style="color: #004a8c; margin-top:0;">Pagamento Seguro GeralJá</h3>
                    <p style="font-size: 14px; color: #555;">O valor fica protegido conosco até o fim do serviço.</p>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 10px; font-family: monospace; border: 1px dashed #ccc;">
                        <strong>CHAVE PIX (CNPJ/CEL):</strong><br>
                        <span style="font-size: 18px;">11991853488</span>
                    </div>
                    <h2 style="color: #27ae60; margin: 15px 0;">R$ {valor_simulado},00</h2>
                </div>
            """, unsafe_allow_html=True)
            
            # Botão de WhatsApp direto para o Prestador/Administrador
            whatsapp_msg = f"https://wa.me/5511991853488?text=Olá! Contratei o Bony Silva pelo GeralJá. Valor: R${valor_simulado}. Já realizei o PIX."
            st.markdown(f"""
                <a href="{whatsapp_msg}" target="_blank" style="text-decoration:none;">
                    <div style="background:#25d366; color:white; padding:18px; text-align:center; border-radius:12px; font-weight:bold; margin-top:15px; font-size:18px;">
                        📱 AVISAR PAGAMENTO NO WHATSAPP
                    </div>
                </a>
            """, unsafe_allow_html=True)
            st.balloons()

with tab_pro:
    st.markdown("""
        <div class="glass-card" style="text-align:center;">
            <h2>Seja um Parceiro Elite</h2>
            <a href="https://forms.gle/WWj6XcbLEbcttbe76" target="_blank" style="text-decoration:none;">
                <div style="background:#f39c12; color:white; padding:18px; border-radius:12px; font-weight:bold; margin-top:20px;">
                    📝 INICIAR CADASTRO
                </div>
            </a>
        </div>
    """, unsafe_allow_html=True)

with tab_pedidos:
    st.info("📊 Seus serviços contratados aparecerão aqui após a confirmação do pagamento.")

st.markdown("<p style='text-align:center; color:#34495e; font-size:12px; margin-top:50px;'>GERALJÁ v2.5 | O HUB da Zona Sul</p>", unsafe_allow_html=True)