import streamlit as st
import random
import time

# --- CONFIGURAÇÃO E DESIGN ---
st.set_page_config(page_title="GeralJá | Elite HUB", layout="wide")

st.markdown("""
    <style>
    .stApp { background: #050a10; color: white; }
    .checkout-card { 
        background: white; color: black; padding: 25px; 
        border-radius: 20px; text-align: center; border: 4px solid #27ae60; 
    }
    .fee-badge {
        background: #e1f5fe; color: #01579b; padding: 5px 10px;
        border-radius: 5px; font-size: 12px; font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Lista de profissões
PROFISOES = ["Pintor", "Eletricista", "Encanador", "Diarista", "Pedreiro"]

if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'

# --- LOGICA DE FLUXO ---
if st.session_state.etapa == 'busca':
    st.markdown("## 🔍 Encontre um Profissional")
    profissao = st.selectbox("O que você precisa?", [""] + PROFISOES)
    local = st.text_input("📍 Seu endereço no Grajaú:")

    if st.button("BUSCAR AGORA", use_container_width=True):
        if professions and local:
            st.session_state.profissao = profissao
            st.session_state.etapa = 'resultado'
            st.rerun()

elif st.session_state.etapa == 'resultado':
    # Simulando um valor de mercado
    preco_base = random.randint(150, 400)
    st.session_state.valor_total = preco_base
    
    st.markdown(f"### Melhor opção para {st.session_state.profissao}")
    st.markdown(f"""
        <div style="background: rgba(255,255,255,0.05); padding:20px; border-radius:15px;">
            <h2>Bony Silva</h2>
            <p>⭐ 4.9 | Especialista Verificado</p>
            <h1 style="color:#f39c12;">R$ {preco_base},00</h1>
            <span class="fee-badge">🛡️ Pagamento 100% Protegido pelo GeralJá</span>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("💳 SEGUIR PARA PAGAMENTO", use_container_width=True):
        st.session_state.etapa = 'pagamento'
        st.rerun()

elif st.session_state.etapa == 'pagamento':
    # CÁLCULO FINANCEIRO (REGRA DOS 10%)
    total = st.session_state.valor_total
    taxa_plataforma = total * 0.10  # SEU LUCRO DE 10%
    repasse_profissional = total - taxa_plataforma
    
    st.markdown("### 💳 Checkout Seguro")
    st.markdown(f"""
        <div class="checkout-card">
            <p style="margin:0; color:gray;">VALOR TOTAL A PAGAR</p>
            <h1 style="margin:0; font-size:45px;">R$ {total},00</h1>
            <hr>
            <p>Escaneie ou use o PIX Copia e Cola:</p>
            <code style="background:#f0f0f0; padding:10px; display:block; border-radius:10px;">11991853488</code>
            <br>
            <p style="font-size:13px; color:#555;">
                <b>Como funciona?</b><br>
                Você paga R$ {total},00 agora.<br>
                O GeralJá retém o valor e libera R$ {repasse_profissional},00 ao profissional 
                somente após você confirmar a conclusão do serviço.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("✅ JÁ REALIZEI O PIX"):
        st.success("Confirmando com o banco... Em instantes você receberá o contato!")
        st.balloons()
