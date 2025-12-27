import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="GeralJá | Grajaú", page_icon="⚡", layout="centered")

# --- CONEXÃO FIREBASE (SISTEMA BASE64) ---
if not firebase_admin._apps:
    try:
        b64_data = st.secrets["FIREBASE_BASE64"]
        json_data = base64.b64decode(b64_data).decode("utf-8")
        info_chave = json.loads(json_data)
        cred = credentials.Certificate(info_chave)
        firebase_admin.initialize_app(cred)
    except: st.stop()

db = firestore.client()

# --- SUPER LISTA DE PROFISSÕES (CONSOLIDADA) ---
profissoes_brutas = [
    # Suas e Essenciais de Bairro
    "Barman", "Bartender", "Garçom", "Garçonete", "Churrasqueiro", "Cozinheiro(a)", "Padeiro", "Confeiteiro(a)",
    "Diarista", "Doméstica", "Passadeira", "Pintor", "Eletricista", "Encanador", "Pedreiro", "Ajudante Geral",
    "Jardineiro", "Piscineiro", "Marceneiro", "Carpinteiro", "Serralheiro", "Gesseiro", "Azulejista",
    "Mecânico", "Borracheiro", "Montador de Móveis", "Manicure", "Pedicure", "Cabeleireiro(a)", "Barbeiro",
    "Esteticista", "Massagista", "Depiladora", "Maquiador(a)", "Fotógrafo", "Motorista", "Entregador",
    "Segurança", "Vigilante", "Babá", "Cuidador de Idosos", "Pet Sitter", "Adestrador",
    
    # Saúde e Bem-estar
    "Médico Especialista", "Enfermeiro(a)", "Técnico em Enfermagem", "Fisioterapeuta", "Nutricionista", 
    "Psicólogo(a)", "Dentista", "Fonoaudiólogo", "Terapeuta Holístico", "Acupuncturista", "Biomédico",
    "Massoterapeuta", "Naturopata", "Terapeuta Ocupacional",
    
    # Tecnologia e Digital
    "Desenvolvedor Mobile", "Desenvolvedor Web", "Especialista em IA", "Cientista de Dados", 
    "Analista de Redes", "Analista de TI", "Especialista em UX/UI", "Game Designer", "Especialista em Marketing Digital",
    "Analista de Mídia Social", "Designer Gráfico", "Editor de Vídeo", "Especialista em Cibersegurança",
    
    # Educação e Negócios
    "Professor(a) Particular", "Professor de Idiomas", "Tutor", "Contador", "Analista Financeiro",
    "Advogado(a)", "Corretor de Imóveis", "Vendedor", "Representante Comercial", "Consultor de Vendas",
    "Analista de RH", "Gerente de Projetos", "Arquiteto(a)", "Engenheiro Civil",
    
    # Artes e Entretenimento
    "DJ", "Cantor(a)", "Músico", "Produtor de Eventos", "Cerimonialista", "Animador de Festas",
    "Ilustrador", "Artista Plástico", "Designer de Interiores", "Palestrante", "Escritor(a)"
]

# Remove duplicatas e ordena de A a Z
LISTA_FINAL = sorted(list(set(profissoes_brutas)))

# --- CSS PERSONALIZADO ---
st.markdown("""
    <style>
    .azul { color: #0047AB; font-size: 45px; font-weight: 900; }
    .laranja { color: #FF8C00; font-size: 45px; font-weight: 900; }
    .card-pro {
        background: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px;
        border-left: 10px solid #0047AB;
    }
    .badge-verificado {
        background: #25D366; color: white; padding: 4px 12px;
        border-radius: 20px; font-size: 12px; font-weight: bold;
    }
    .botao-zap {
        background-color: #25D366; color: white !important;
        text-decoration: none; padding: 12px; border-radius: 10px;
        display: block; text-align: center; font-weight: bold; margin-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO ---
st.markdown('<center><span class="azul">GERAL</span><span class="laranja">JÁ</span></center>', unsafe_allow_html=True)
st.write("---")

tab1, tab2, tab3 = st.tabs(["🔍 BUSCAR", "👷 CADASTRAR", "👥 MURAL"])

# --- ABA 1: BUSCA ---
with tab1:
    st.subheader("O que você procura no bairro?")
    escolha = st.selectbox("Selecione a profissão ou digite para buscar:", [""] + LISTA_FINAL)
    
    if escolha:
        # Busca profissionais aprovados dessa categoria
        query = db.collection("profissionais").where("area", "==", escolha).where("aprovado", "==", True).stream()
        
        encontrou = False
        for p in query:
            encontrou = True
            d = p.to_dict()
            zap_limpo = "".join(filter(str.isdigit, d.get('whatsapp', '')))
            
            st.markdown(f"""
            <div class="card-pro">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 20px; font-weight: bold;">👤 {d['nome']}</span>
                    <span class="badge-verificado">VERIFICADO ✔️</span>
                </div>
                <div style="margin-top: 10px; color: #555;">
                    <b>Serviço:</b> {d['area']}<br>
                    📍 Atendimento no Grajaú e proximidades
                </div>
                <a href="https://wa.me/55{zap_limpo}?text=Olá%20{d['nome']},%20vi%20seu%20anúncio%20no%20GeralJá!" class="botao-zap">
                    CHAMAR NO WHATSAPP
                </a>
            </div>
            """, unsafe_allow_html=True)
        
        if not encontrou:
            st.info(f"Ainda não temos '{escolha}' aprovados. Seja o primeiro a indicar um!")

# --- ABA 2: CADASTRO ---
with tab2:
    st.subheader("👷 Divulgue seu Trabalho")
    with st.form("form_cad_final", clear_on_submit=True):
        nome_f = st.text_input("Nome Completo")
        zap_f = st.text_input("WhatsApp (Ex: 11988887777)")
        area_f = st.selectbox("Qual sua profissão?", LISTA_FINAL)
        
        submit = st.form_submit_button("SOLICITAR MEU ANÚNCIO")
        
        if submit:
            if nome_f and zap_f:
                db.collection("profissionais").document(zap_f).set({
                    "nome": nome_f, "whatsapp": zap_f, "area": area_f,
                    "aprovado": False, "data": datetime.datetime.now()
                })
                st.balloons()
                st.success("✅ Pedido enviado! Você aparecerá na busca após nossa revisão.")
            else:
                st.error("Por favor, preencha todos os campos.")

# --- ABA 3: MURAL ---
with tab3:
    st.write("Em breve: Mural social com fotos e curtidas para a comunidade!")
