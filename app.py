import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="GeralJá | Grajaú", page_icon="⚡", layout="centered")

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

# --- GRANDE LISTA DE PROFISSÕES (CONSOLIDADA) ---
# Adicionei as que você enviou e mantive a ordem alfabética
PROFISSOES_MESTRE = sorted(list(set([
    "Acupuncturista", "Agente de Tráfico", "Ajudante Geral", "Almoxarife", "Analista de Big Data", 
    "Analista de Crédito", "Analista de E-commerce", "Analista de Financeiro", "Analista de Investimentos",
    "Analista de Logística", "Analista de Mercado", "Analista de Melhoria Contínua", "Analista de Processos",
    "Analista de Redes", "Analista de RH", "Analista de Risco", "Analista de Segurança da Informação",
    "Analista de Sistemas Sênior", "Antropólogo", "Apresentador de TV", "Árbitro", "Árbitro de VAR",
    "Arquiteto", "Arquiteto de Soluções", "Artista de Efeitos Visuais", "Artista Plástico", "Atleta de Alto Desempenho",
    "Ator/Atriz de Teatro", "Auditor", "Auxiliar de Saúde Bucal", "Azulejista", "Babá", "Barbeiro", 
    "Biólogo", "Biólogo Marinho", "Biomédico", "Borracheiro", "Cabeleireiro", "Cantor(a)", "Carpinteiro", 
    "Ceramista", "Cientista de Dados Sênior", "Cineasta", "Comentarista Esportivo", "Compositor", 
    "Confeiteira", "Consultor Ambiental", "Consultor de Gestão", "Consultor de Investimentos", 
    "Contador Público", "Coordenador Pedagógico", "Costureira", "Cozinheira", "Dançarino", 
    "Designer de Interiores", "Designer de Jogos", "Designer de Produtos", "Desenvolvedor Mobile", 
    "Diarista", "Diretor Financeiro", "DJ", "Economista", "Editor de Vídeo", "Eletricista", 
    "Encanador", "Enfermeiro", "Engenheiro Ambiental", "Engenheiro de IA", "Escritor", "Escultor",
    "Especialista em Cibersegurança", "Esteticista", "Fisioterapeuta", "Fotógrafo", "Gesseiro", 
    "Guia Turístico", "Historiador", "Ilustrador", "Investigador", "Jardineiro", "Jornalista", 
    "Manicure", "Marceneiro", "Mecânico", "Médico Pediatra", "Montador de Móveis", "Motorista", 
    "Nutricionista", "Orientador Educacional", "Padeiro", "Pedreiro", "Pintor", "Psicólogo", 
    "Publicitário", "Recepcionista", "Roteirista", "Serralheiro", "Sociólogo", "Técnico em TI", 
    "Tutor", "Vendedor", "Vigilante"
]))) # Adicione mais aqui conforme desejar

# --- ESTILIZAÇÃO ---
st.markdown("""
    <style>
    .main-title { color: #0047AB; font-size: 42px; font-weight: 900; text-align: center; }
    .sub-title { color: #FF8C00; font-size: 42px; font-weight: 900; }
    .card {
        background: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 15px;
        border-left: 10px solid #0047AB;
    }
    .verificado { color: #28a745; font-weight: bold; font-size: 13px; }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown('<div class="main-title">GERAL<span class="sub-title">JÁ</span></div>', unsafe_allow_html=True)
st.markdown("<center>O maior catálogo de profissionais do Grajaú</center>", unsafe_allow_html=True)
st.write("---")

aba1, aba2, aba3 = st.tabs(["🔍 ENCONTRAR", "👷 CADASTRAR", "👥 MURAL"])

# --- ABA 1: BUSCA INTELIGENTE ---
with aba1:
    escolha = st.selectbox("Selecione o serviço que você procura:", [""] + PROFISSOES_MESTRE)
    
    if escolha:
        query = db.collection("profissionais").where("area", "==", escolha).where("aprovado", "==", True).stream()
        
        count = 0
        for p in query:
            count += 1
            d = p.to_dict()
            zap = "".join(filter(str.isdigit, d['whatsapp']))
            st.markdown(f"""
            <div class="card">
                <div style="display: flex; justify-content: space-between;">
                    <span style="font-size: 20px; font-weight: bold;">{d['nome']}</span>
                    <span class="verificado">VERIFICADO ✔️</span>
                </div>
                <div style="color: #666; margin: 10px 0;">📍 Atendimento em todo o Grajaú</div>
                <a href="https://wa.me/55{zap}" target="_blank" 
                   style="background:#25D366; color:white; text-decoration:none; padding:10px; display:block; text-align:center; border-radius:8px; font-weight:bold;">
                   CONVERSAR NO WHATSAPP
                </a>
            </div>
            """, unsafe_allow_html=True)
        
        if count == 0:
            st.info(f"Ainda não temos profissionais de '{escolha}' aprovados. Conhece um? Indique o GeralJá!")

# --- ABA 2: CADASTRO COM TODAS AS OPÇÕES ---
with aba2:
    st.subheader("Trabalha no Grajaú? Cadastre-se!")
    with st.form("form_novo"):
        nome = st.text_input("Nome Completo")
        zap = st.text_input("WhatsApp (Ex: 11988887777)")
        profissao = st.selectbox("Sua Profissão", PROFISSOES_MESTRE)
        
        if st.form_submit_button("SOLICITAR ANÚNCIO GRATUITO"):
            if nome and zap:
                db.collection("profissionais").document(zap).set({
                    "nome": nome, "whatsapp": zap, "area": profissao,
                    "aprovado": False, "data": datetime.datetime.now()
                })
                st.success("✅ Solicitação enviada! Você aparecerá na busca após nossa revisão.")

# --- ABA 3: MURAL ---
with aba3:
    st.write("O Mural está sendo otimizado para a nova lista de usuários!")
