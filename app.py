import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GeralJá | Oficial", page_icon="⚡", layout="centered")

# --- CONEXÃO FIREBASE ---
if not firebase_admin._apps:
    try:
        b64_data = st.secrets["FIREBASE_BASE64"]
        json_data = base64.b64decode(b64_data).decode("utf-8")
        info_chave = json.loads(json_data)
        cred = credentials.Certificate(info_chave)
        firebase_admin.initialize_app(cred)
    except: st.stop()

db = firestore.client()

# --- CSS AVANÇADO ---
st.markdown("""
    <style>
    .azul { color: #0047AB; font-size: 45px; font-weight: 800; }
    .laranja { color: #FF8C00; font-size: 45px; font-weight: 800; }
    
    /* Estilo dos Cards de Profissionais */
    .pro-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        border-top: 5px solid #0047AB;
    }
    .status-verificado {
        background: #e8f5e9;
        color: #2e7d32;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
    }
    .btn-zap {
        background-color: #25D366;
        color: white !important;
        padding: 12px;
        border-radius: 8px;
        text-decoration: none;
        display: block;
        text-align: center;
        font-weight: bold;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO ---
st.markdown('<center><span class="azul">GERAL</span><span class="laranja">JÁ</span></center>', unsafe_allow_html=True)
st.markdown("<center>O ponto de encontro do Grajaú</center>", unsafe_allow_html=True)
st.write("---")

tab1, tab2, tab3 = st.tabs(["🔍 ENCONTRAR SERVIÇO", "👷 CADASTRAR-SE", "👥 MURAL SOCIAL"])

# --- TAB 1: BUSCA MELHORADA ---
with tab1:
    st.subheader("O que você precisa hoje?")
    
    # Busca por texto e categoria
    col1, col2 = st.columns([2, 1])
    with col1:
        busca_nome = st.text_input("Buscar por nome ou palavra-chave", placeholder="Ex: Pintura, Reparo...")
    with col2:
        filtro_cat = st.selectbox("Categoria", ["Todas", "Pintor", "Eletricista", "Encanador", "Diarista", "Mecânico", "Outros"])

    # Lógica de Busca no Firebase
    query = db.collection("profissionais").where("aprovado", "==", True)
    if filtro_cat != "Todas":
        query = query.where("area", "==", filtro_cat)
    
    profs = query.stream()
    
    # Exibição em Grid
    encontrou = False
    for p in profs:
        d = p.to_dict()
        if busca_nome.lower() in d['nome'].lower() or busca_nome == "":
            encontrou = True
            zap_link = "".join(filter(str.isdigit, d['whatsapp']))
            
            st.markdown(f"""
            <div class="pro-card">
                <div style="display: flex; justify-content: space-between;">
                    <span style="font-size: 18px; font-weight: bold;">👤 {d['nome']}</span>
                    <span class="status-verificado">PROFISSIONAL APROVADO ✔️</span>
                </div>
                <p style="margin: 10px 0; color: #555;">
                    <b>Especialidade:</b> {d['area']}<br>
                    <b>Local:</b> Grajaú e Região
                </p>
                <a href="https://wa.me/55{zap_link}" class="btn-zap">CHAMAR NO WHATSAPP</a>
            </div>
            """, unsafe_allow_html=True)

    if not encontrou:
        st.warning("Nenhum profissional encontrado com esses filtros.")

# --- TAB 2: CADASTRO DETALHADO ---
with tab2:
    st.subheader("👷 Painel de Cadastro")
    st.write("Junte-se aos profissionais mais recomendados do bairro.")
    
    with st.form("form_cadastro_vip", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            nome = st.text_input("Nome Completo")
            zap = st.text_input("WhatsApp (com DDD)")
        with col_b:
            area = st.selectbox("Sua Especialidade", ["Pintor", "Eletricista", "Encanador", "Diarista", "Mecânico", "Outros"])
            exp = st.selectbox("Tempo de Experiência", ["Iniciante", "1-3 anos", "3-5 anos", "Mais de 5 anos"])
        
        descricao = st.text_area("Fale um pouco sobre o seu serviço (opcional)")
        
        st.markdown("---")
        termos = st.checkbox("Aceito que meus dados sejam exibidos para moradores do Grajaú.")
        
        btn_enviar = st.form_submit_button("SOLICITAR ENTRADA NO GERALJÁ")
        
        if btn_enviar:
            if nome and zap and termos:
                db.collection("profissionais").document(zap).set({
                    "nome": nome,
                    "whatsapp": zap,
                    "area": area,
                    "experiencia": exp,
                    "descricao": descricao,
                    "aprovado": False, # Começa como falso para você aprovar
                    "data": datetime.datetime.now()
                })
                st.balloons()
                st.success("✅ Pedido enviado! Em breve seu perfil aparecerá na busca após aprovação.")
            else:
                st.error("Preencha os campos obrigatórios e aceite os termos.")

# --- TAB 3: MURAL (MANTENDO A LÓGICA ANTERIOR) ---
with tab3:
    st.info("O mural social está disponível para membros aprovados.")
    # (Mantemos o código do Mural do passo anterior aqui...)
