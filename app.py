import streamlit as st
import random
import time

# --- 1. CONFIGURAÇÃO E LISTA DE PROFISSÕES ---
st.set_page_config(page_title="GeralJá | O HUB do Grajaú", layout="centered")

# Lista expandida - o usuário pode digitar qualquer uma delas
LISTA_PROS = [
    "Ajudante Geral", "Arquiteto", "Azulejista", "Babá", "Bombeiro Civil", "Cabeleireiro", 
    "Carpinteiro", "Chaveiro", "Confeiteira", "Costureira", "Cozinheira", "Diarista", 
    "Eletricista", "Encanador", "Estofador", "Esteticista", "Fardamento", "Ferreiro", 
    "Gesseiro", "Instalador de Ar-Condicionado", "Jardineiro", "Lanterneiro", 
    "Limpeza de Piscina", "Marceneiro", "Marido de Aluguel", "Mecânico de Carro", 
    "Mecânico de Moto", "Montador de Móveis", "Motorista Particular", "Nutricionista", 
    "Organizador de Eventos", "Pedreiro", "Pintor", "Podador", "Serralheiro", 
    "Técnico de Celular", "Técnico de Geladeira", "Técnico de TI", "Vidraceiro"
]

# --- 2. ESTILO CSS (Design Moderno) ---
st.markdown("""
    <style>
    .stApp { background: #050a10; color: white; }
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 20px; padding: 25px; margin-bottom: 20px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. BANCO DE DADOS EM SESSÃO ---
if 'lucro_total' not in st.session_state: st.session_state.lucro_total = 0.0
if 'pedidos_concluidos' not in st.session_state: st.session_state.pedidos_concluidos = 0
if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'

# --- 4. PAINEL DE FATURAMENTO (BARRA LATERAL) ---
with st.sidebar:
    st.title("⚙️ Painel GeralJá")
    acesso = st.text_input("Senha Admin", type="password")
    if acesso == "admin123":
        st.subheader("💰 Seu Faturamento (10%)")
        st.metric("Lucro Acumulado", f"R$ {st.session_state.lucro_total:.2f}")
        st.metric("Total de Pedidos", st.session_state.pedidos_concluidos)
        if st.button("Resetar Caixa"):
            st.session_state.lucro_total = 0.0
            st.session_state.pedidos_concluidos = 0
            st.rerun()

# --- 5. LÓGICA DE ABERTURA ANIMADA ---
if 'abertura_concluida' not in st.session_state:
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("""
            <div style="text-align:center; margin-top:25vh;">
                <h1 style="color:#f39c12; font-size:60px; font-weight:900;">GERALJÁ</h1>
                <p style="letter-spacing:5px; color:#3498db;">SISTEMA DE BUSCA INTELIGENTE</p>
            </div>
        """, unsafe_allow_html=True)
        time.sleep(2.5)
    st.session_state.abertura_concluida = True
    placeholder.empty()

# --- 6. FLUXO DO APLICATIVO ---

if st.session_state.get('abertura_concluida'):

    # --- ETAPA 1: BUSCA INTELIGENTE ---
    if st.session_state.etapa == 'busca':
        st.markdown("<h2 style='text-align:center;'>🔍 Radar de Profissionais</h2>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            
            # Aqui está a busca que você pediu: o usuário digita e a lista filtra
            servico = st.selectbox(
                "Qual profissional você precisa?", 
                options=[""] + sorted(LISTA_PROS),
                index=0,
                help="Digite o nome da profissão para filtrar"
            )
            
            urgencia = st.select_slider(
                "Nível de Urgência:", 
                options=["Hoje", "Urgente", "Emergência 🔥"]
            )
            
            endereco = st.text_input("📍 Seu Endereço no Grajaú")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if st.button("ATIVAR RADAR AGORA", use_container_width=True):
                if servico != "" and endereco != "":
                    st.session_state.servico = servico
                    st.session_state.urgencia = urgencia
                    st.session_state.distancia = round(random.uniform(0.3, 5.0), 1)
                    st.session_state.etapa = 'resultado'
                    st.rerun()
                else:
                    st.error("⚠️ Selecione a profissão e digite o endereço.")

    # --- ETAPA 2: RESULTADO ---
    elif st.session_state.etapa == 'resultado':
        # Cálculo de preço com base na urgência
        base_price = random.randint(140, 320)
        if "Emergência" in st.session_state.urgencia: base_price += 60
        st.session_state.valor_total = base_price
        
        st.markdown(f"### 📍 Profissional a {st.session_state.distancia}km de você")
        st.markdown(f"""
            <div class="glass-card">
                <h2 style="color:#f39c12; margin:0;">Bony Silva</h2>
                <p style="margin:0;">⭐ 4.9 | Especialista em {st.session_state.servico}</p>
                <hr style="opacity:0.1">
                <h1 style="margin:0; color:white;">R$ {st.session_state.valor_total},00</h1>
                <p style="font-size:12px; color:#27ae60;">✔ Disponibilidade imediata para {st.session_state.urgencia}</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("💳 CONTRATAR E PAGAR", use_container_width=True):
            st.session_state.etapa = 'pagamento'
            st.rerun()
        if st.button("⬅ Voltar"):
            st.session_state.etapa = 'busca'
            st.rerun()

    # --- ETAPA 3: PAGAMENTO (COM TAXA DE 10%) ---
    elif st.session_state.etapa == 'pagamento':
        total = st.session_state.valor_total
        comissao = total * 0.10
        
        st.markdown("<h3 style='text-align:center;'>Pagamento via PIX</h3>", unsafe_allow_html=True)
        st.markdown(f"""
            <div class="glass-card" style="background:white; color:black; text-align:center;">
                <h4 style="margin:0; color:gray;">TOTAL A PAGAR</h4>
                <h1 style="margin:0; font-size:45px; color:#27ae60;">R$ {total},00</h1>
                <br>
                <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=PIX-GERALJA-11991853488">
                <p style="font-size:12px; margin-top:10px;"><b>Chave PIX:</b> 11991853488</p>
                <p style="font-size:11px; color:#666;">Intermediação Segura GeralJá</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("✅ JÁ REALIZEI O PAGAMENTO"):
            # Contabiliza faturamento para o dono
            st.session_state.lucro_total += comissao
            st.session_state.pedidos_concluidos += 1
            
            st.balloons()
            st.success("Pagamento confirmado pelo sistema!")
            st.info(f"O profissional foi notificado e chegará em instantes.")
            
            if st.button("Fazer Nova Busca"):
                st.session_state.etapa = 'busca'
                st.rerun()
