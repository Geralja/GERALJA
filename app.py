import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GeralJá | Grajaú", page_icon="⚡", layout="centered")

# --- CONEXÃO FIREBASE (BLINDADA) ---
if not firebase_admin._apps:
    try:
        b64_data = st.secrets["FIREBASE_BASE64"]
        json_data = base64.b64decode(b64_data).decode("utf-8")
        info_chave = json.loads(json_data)
        cred = credentials.Certificate(info_chave)
        firebase_admin.initialize_app(cred)
    except: st.stop()

db = firestore.client()

# --- LISTA DE PROFISSÕES (EXEMPLO EXPANSÍVEL) ---
# DICA: Você pode alimentar esta lista com as 1000 que desejar
LISTA_PROFISSOES = [
    "Ajudante Geral", "Almoxarife", "Arquiteto", "Azulejista", "Babá", "Barbeiro", 
    "Borracheiro", "Cabeleireiro", "Carpinteiro", "Confeiteira", "Costureira", 
    "Cozinheira", "Diarista", "Eletricista", "Encanador", "Esteticista", 
    "Fisioterapeuta", "Gesseiro", "Jardineiro", "Manicure", "Marceneiro", 
    "Mecânico", "Montador de Móveis", "Motorista", "Nutricionista", "Padeiro", 
    "Pedreiro", "Pintor", "Psicólogo", "Serralheiro", "Técnico em TI", "Vendedor"
]
LISTA_PROFISSOES.sort()

# --- DESIGN PREMIUM ---
st.markdown("""
    <style>
    .azul { color: #0047AB; font-size: 45px; font-weight: 800; }
    .laranja { color: #FF8C00; font-size: 45px; font-weight: 800; }
    .pro-card {
        background: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px;
        border-left: 8px solid #0047AB;
    }
    .badge {
        background: #25D366; color: white; padding: 3px 10px;
        border-radius: 10px; font-size: 12px; font-weight: bold;
    }
    .btn-zap {
        background-color: #25D366; color: white !important;
        padding: 12px; border-radius: 8px; text-decoration: none;
        display: block; text-align: center; font-weight: bold; margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO ---
st.markdown('<center><span class="azul">GERAL</span><span class="laranja">JÁ</span></center>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🔍 BUSCAR SERVIÇO", "👷 CADASTRAR-SE", "👥 MURAL"])

# --- TAB 1: BUSCA INTELIGENTE (1000+ PROFISSÕES) ---
with tab1:
    st.subheader("O que você precisa no Grajaú?")
    
    # Campo de busca com sugestão (melhor para 1000 profissões)
    profissao_buscada = st.selectbox(
        "Digite ou selecione a profissão:",
        [""] + LISTA_PROFISSOES,
        help="Digite o nome do serviço que você procura"
    )

    if profissao_buscada:
        query = db.collection("profissionais")\
                  .where("area", "==", profissao_buscada)\
                  .where("aprovado", "==", True).stream()
        
        encontrou = False
        for p in query:
            encontrou = True
            d = p.to_dict()
            zap_link = "".join(filter(str.isdigit, d['whatsapp']))
            
            st.markdown(f"""
            <div class="pro-card">
                <div style="display: flex; justify-content: space-between;">
                    <span style="font-size: 19px; font-weight: bold;">👤 {d['nome']}</span>
                    <span class="badge">WHATSAPP DISPONÍVEL</span>
                </div>
                <p style="margin: 10px 0;"><b>Serviço:</b> {d['area']}<br>
                <small>✅ Profissional Verificado pelo GeralJá</small></p>
                <a href="https://wa.me/55{zap_link}" class="btn-zap">CHAMAR AGORA</a>
            </div>
            """, unsafe_allow_html=True)
        
        if not encontrou:
            st.info(f"Ainda não temos '{profissao_buscada}' cadastrados. Tente outra categoria!")

# --- TAB 2: CADASTRO COM LISTA COMPLETA ---
with tab2:
    st.subheader("Faça seu Cadastro Profissional")
    with st.form("cad_completo", clear_on_submit=True):
        nome = st.text_input("Seu Nome")
        zap = st.text_input("Seu WhatsApp (com DDD)")
        # Aqui o profissional escolhe entre as 1000 opções
        area = st.selectbox("Qual sua profissão?", LISTA_PROFISSOES)
        
        if st.form_submit_button("SOLICITAR MEU ANÚNCIO"):
            if nome and zap:
                db.collection("profissionais").document(zap).set({
                    "nome": nome, "whatsapp": zap, "area": area,
                    "aprovado": False, "data": datetime.datetime.now()
                })
                st.success("✅ Pedido enviado! Aguarde a aprovação do Admin.")

# --- TAB 3: MURAL (Reduzido para agilizar) ---
with tab3:
    st.info("Mural em breve com sistema de likes e fotos!")
