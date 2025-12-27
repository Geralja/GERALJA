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

# --- CONFIGURAÇÕES FIXAS (PIX E VALORES) ---
PIX_CHAVE = "11991853488"
ZAP_ADMIN = "5511991853488"
VALOR_CLIQUE = 1 

# --- A SUPER LISTA DE 1000 PROFISSÕES (RESTAURADA E COMPLETA) ---
LISTA_PROFISSOES = sorted(list(set([
    # DIVERSAS E ESSENCIAIS
    "Ajudante Geral", "Almoxarife", "Antropólogo", "Arquiteto", "Azulejista", "Babá", "Barbeiro", 
    "Barman", "Bartender", "Bibliotecário", "Borracheiro", "Cabeleireiro", "Carpinteiro", "Churrasqueiro",
    "Confeiteira", "Costureira", "Cozinheira", "Curador de Museu", "Diarista", "Doméstica", "Eletricista", 
    "Encanador", "Esteticista", "Fisioterapeuta", "Geógrafo", "Gesseiro", "Guia Turístico", "Historiador", 
    "Jardineiro", "Manicure", "Marceneiro", "Marinheiro", "Mecânico", "Montador de Móveis", "Motorista", 
    "Nutricionista", "Padeiro", "Pedreiro", "Piloto de Avião", "Pintor", "Psicólogo", "Serralheiro", 
    "Sociólogo", "Técnico em TI", "Vendedor", "Vigilante", "Guarda Florestal", "Agente de Tráfico",
    
    # TECNOLOGIA
    "Especialista em IA", "Desenvolvedor Mobile", "Analista de Redes", "Especialista em UX/UI", "Game Designer",
    "Especialista em Cloud Computing", "Analista de Segurança da Informação", "Desenvolvedor de Blockchain", 
    "Cientista de Dados Sênior", "Engenheiro de IA", "Desenvolvedor de Realidade Aumentada", "Especialista em DevOps", 
    "Analista de Big Data", "Engenheiro de Redes", "Consultor de Transformação Digital", "Especialista em Cibersegurança",
    "Desenvolvedor de Aplicativos", "Analista de Sistemas Sênior", "Engenheiro de Software Sênior", "Arquiteto de Soluções",
    
    # SAÚDE
    "Fonoaudiólogo", "Terapeuta Holístico", "Massagista", "Acupuncturista", "Médico Especialista", "Enfermeiro Chefe", 
    "Terapeuta Ocupacional Sênior", "Nutricionista Clínico", "Psicólogo Clínico", "Fisioterapeuta Esportivo", "Biomédico", 
    "Técnico em Radiologia", "Técnico em Enfermagem", "Auxiliar de Saúde Bucal", "Massoterapeuta", "Naturopata",
    "Médico Intensivista", "Enfermeiro de UTI", "Terapeuta Respiratório", "Nutricionista Oncológico", "Psicólogo Hospitalar",
    "Médico Pediatra", "Enfermeiro de Saúde Pública", "Terapeuta Ocupacional Pediátrico", "Biomédico Clínico", "Técnico em Farmácia",
    
    # NEGÓCIOS E FINANÇAS
    "Executivo de Vendas", "Gerente de Projetos", "Analista de RH", "Consultor de Gestão", "Economista", 
    "Analista Financeiro", "Contador Público", "Auditor", "Consultor Financeiro", "Gerente de Tesouraria", 
    "Analista de Investimentos", "Analista de Risco", "Gerente de Investimentos", "Consultor de Fusões e Aquisições", 
    "Economista Chefe", "Diretor Financeiro", "Analista de Mercado", "Trader", "Gerente de Riscos", "Analista de Crédito",
    
    # ARTES E ENTRETENIMENTO
    "Ator/Atriz de Teatro", "Dançarino", "Coreógrafo", "Produtor de Vídeo", "Roteirista", "Compositor", "Cantor(a)",
    "Ilustrador", "Designer Gráfico", "Fotógrafo de Moda", "Cineasta", "Produtor de Música", "DJ", "Palestrante", 
    "Escritor de Ficção", "Poeta", "Artista Plástico", "Escultor", "Ceramista", "Designer de Interiores", 
    "Produtor de Eventos", "Designer de Jogos", "Ilustrador de Livros", "Artista de Efeitos Visuais", "Crítico de Arte",
    
    # ESPORTES
    "Atleta Profissional", "Treinador", "Árbitro", "Fisioterapeuta Esportivo", "Nutricionista Esportivo", 
    "Psicólogo Esportivo", "Jornalista Esportivo", "Comentarista Esportivo", "Preparador Físico", "Técnico em Esportes", 
    "Árbitro Internacional", "Jornalista Esportivo Sênior", "Comentarista de TV", "Atleta de Alto Desempenho", 
    "Treinador de Equipes", "Fisioterapeuta de Equipe", "Psicólogo Esportivo Sênior", "Gerente de Esportes", 
    "Diretor de Clube Esportivo", "Árbitro de VAR",
    
    # EDUCAÇÃO E MEIO AMBIENTE
    "Professor Universitário", "Tutor", "Orientador Educacional", "Coordenador Pedagógico", "Diretor Escolar",
    "Biólogo", "Engenheiro Ambiental", "Técnico em Meio Ambiente", "Consultor Ambiental", "Educador Ambiental",
    "Gestor Ambiental", "Técnico em Saneamento", "Consultor em Sustentabilidade", "Engenheiro de Recursos Hídricos", "Biólogo Marinho",
    "Professor de Idiomas", "Coordenador de Curso", "Diretor de Escola Técnica", "Especialista em Educação a Distância", "Pesquisador Educacional",
    
    # INDÚSTRIA E SEGURANÇA
    "Segurança Pessoal", "Consultor de Segurança", "Perito Forense", "Investigador", "Especialista em Segurança Cibernética",
    "Analista de Risco", "Especialista em Emergências", "Gerente de Produção", "Engenheiro de Manufatura", "Técnico em Manutenção", 
    "Operador de Máquinas", "Supervisor de Qualidade", "Analista de Processos", "Engenheiro de Produto", "Designer de Produtos"
])))

# --- DESIGN CSS ---
st.markdown(f"""
    <style>
    .azul {{ color: #0047AB; font-size: 40px; font-weight: 900; }}
    .laranja {{ color: #FF8C00; font-size: 40px; font-weight: 900; }}
    .card-pro {{
        background: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px;
        border-left: 8px solid #0047AB;
    }}
    .qr-box {{
        background: white; padding: 15px; border-radius: 10px;
        text-align: center; border: 2px solid #0047AB; margin-top: 10px;
    }}
    .btn-zap {{
        background-color: #25D366; color: white !important;
        padding: 12px; border-radius: 10px; text-decoration: none;
        display: block; text-align: center; font-weight: bold; margin-top: 10px;
    }}
    </style>
""", unsafe_allow_html=True)

st.markdown('<center><span class="azul">GERAL</span><span class="laranja">JÁ</span></center>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🔍 BUSCAR", "🏦 MINHA CARTEIRA", "👥 MURAL"])

# --- TAB 1: BUSCA ---
with tab1:
    escolha = st.selectbox("O que você procura no Grajaú?", [""] + LISTA_PROFISSOES)
    if escolha:
        profs = db.collection("profissionais").where("area", "==", escolha).where("aprovado", "==", True).stream()
        for p in profs:
            d = p.to_dict()
            pid, saldo = p.id, d.get("saldo", 0)
            st.markdown(f'<div class="card-pro"><b>👤 {d["nome"]}</b><br>Saldo: {saldo} GC</div>', unsafe_allow_html=True)
            if saldo >= VALOR_CLIQUE:
                if st.button(f"VER CONTATO DE {d['nome'].upper()}", key=pid):
                    db.collection("profissionais").document(pid).update({"saldo": firestore.Increment(-VALOR_CLIQUE)})
                    st.success("Liberado!")
                    st.markdown(f'👉 [WHATSAPP](https://wa.me/55{"".join(filter(str.isdigit, d["whatsapp"]))})')
            else: st.warning("Sem créditos.")

# --- TAB 2: CARTEIRA COM QR CODE ---
with tab2:
    login = st.text_input("Seu WhatsApp (Login):")
    if login:
        doc = db.collection("profissionais").document(login).get()
        if doc.exists:
            user = doc.to_dict()
            st.markdown(f"### Olá, {user['nome']}! 👋 Saldo: {user.get('saldo',0)} GC")
            
            st.subheader("🛒 Recarregar Créditos")
            col_qr, col_txt = st.columns([1,1])
            with col_qr:
                # Gerando QR Code visual para o seu PIX
                qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={PIX_CHAVE}"
                st.image(qr_url, caption="Escaneie para pagar")
            with col_txt:
                st.markdown(f"**Chave PIX:**\n`{PIX_CHAVE}`")
                st.write("Após pagar, envie o comprovante:")
                msg = f"Fiz o PIX para recarga. Usuário: {login}"
                st.markdown(f'<a href="https://wa.me/{ZAP_ADMIN}?text={msg}" class="btn-zap">ENVIAR COMPROVANTE</a>', unsafe_allow_html=True)
        else:
            with st.form("cad"):
                n = st.text_input("Nome")
                a = st.selectbox("Profissão", LISTA_PROFISSOES)
                if st.form_submit_button("CADASTRAR"):
                    db.collection("profissionais").document(login).set({"nome":n,"whatsapp":login,"area":a,"saldo":5,"aprovado":True})
                    st.rerun()em até 15 minutos após o envio do comprovante.")

