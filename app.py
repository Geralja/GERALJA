import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime

# --- 1. CONFIGURAÇÃO (Mobile First) ---
st.set_page_config(page_title="GeralJá | Oficial", page_icon="⚡", layout="centered")

# --- 2. CONEXÃO FIREBASE ---
if not firebase_admin._apps:
    try:
        b64_data = st.secrets["FIREBASE_BASE64"]
        json_data = base64.b64decode(b64_data).decode("utf-8")
        info_chave = json.loads(json_data)
        cred = credentials.Certificate(info_chave)
        firebase_admin.initialize_app(cred)
    except: st.stop()

db = firestore.client()

# --- 3. CONFIGURAÇÕES ---
PIX_CHAVE = "11991853488"
ZAP_ADMIN = "5511991853488"
SENHA_ADMIN = "mumias"
VALOR_CLIQUE = 1 
BONUS_INICIAL = 5

# --- 4. LISTA DE PROFISSÕES ---
profissoes_completas = [
    "Ajudante Geral", "Almoxarife", "Antropólogo", "Arquiteto", "Azulejista", "Babá", "Barbeiro", 
    "Barman", "Bartender", "Bibliotecário", "Borracheiro", "Cabeleireiro", "Carpinteiro", "Churrasqueiro",
    "Confeiteira", "Costureira", "Cozinheira", "Curador de Museu", "Diarista", "Doméstica", "Eletricista", 
    "Encanador", "Esteticista", "Fonoaudiólogo", "Garçom", "Garçonete", "Geógrafo", "Gesseiro", "Guia Turístico", 
    "Historiador", "Jardineiro", "Manicure", "Marceneiro", "Marinheiro", "Massagista", "Mecânico", 
    "Médico Especialista", "Montador de Móveis", "Motorista", "Nutricionista", "Padeiro", "Pedreiro", 
    "Piloto de Avião", "Pintor", "Psicólogo", "Serralheiro", "Sociólogo", "Técnico em TI", "Vendedor", 
    "Vigilante", "Especialista em IA", "Desenvolvedor Mobile", "Analista de Redes", "Especialista em UX/UI", 
    "Game Designer", "Analista Financeiro", "Contador Público", "Gerente de Projetos", "Atleta Profissional",
    "Professor Universitário", "Biólogo", "Engenheiro Ambiental", "Segurança Pessoal", "Investigador",
    "Jornalista de TV", "Fotógrafo", "DJ", "Cantor(a)", "Designer de Interiores", "Corretor de Imóveis"
]
LISTA_FINAL = sorted(list(set(profissoes_completas)))

# --- 5. MAPEAMENTO IA ---
MAPEAMENTO_IA = {
    "vazamento": "Encanador", "cano": "Encanador", "torneira": "Encanador", "esgoto": "Encanador", "pia": "Encanador", "privada": "Encanador",
    "curto": "Eletricista", "luz": "Eletricista", "tomada": "Eletricista", "chuveiro": "Eletricista", "fiação": "Eletricista", "disjuntor": "Eletricista",
    "pintar": "Pintor", "parede": "Pintor", "massa": "Pintor", "pintor": "Pintor",
    "reforma": "Pedreiro", "laje": "Pedreiro", "tijolo": "Pedreiro", "reboco": "Pedreiro", "piso": "Pedreiro", "pedreiro": "Pedreiro",
    "unha": "Manicure", "pé": "Manicure", "mão": "Manicure", "manicure": "Manicure",
    "cabelo": "Cabeleireiro", "corte": "Cabeleireiro", "barba": "Barbeiro", "degradê": "Barbeiro",
    "faxina": "Diarista", "limpeza": "Diarista", "diarista": "Diarista",
    "pneu": "Borracheiro", "estepe": "Borracheiro", "furou": "Borracheiro",
    "carreto": "Ajudante Geral", "mudança": "Ajudante Geral", "carro": "Mecânico", "moto": "Mecânico de Motos"
}

# --- 6. ESTILO CSS BLINDADO PARA IPHONE ---
st.markdown(f"""
    <style>
    /* Forçar cores para evitar erro no Modo Escuro do iOS */
    .main {{ background-color: #f8f9fa; }}
    .azul {{ color: #0047AB; font-size: 32px; font-weight: 900; }}
    .laranja {{ color: #FF8C00; font-size: 32px; font-weight: 900; }}
    
    .card-pro {{ 
        background-color: #ffffff !important; 
        padding: 15px; 
        border-radius: 12px; 
        box-shadow: 0 2px 8px rgba(0,0,0,0.1); 
        margin-bottom: 10px; 
        border-left: 6px solid #0047AB;
    }}
    /* Forçar texto Escuro dentro do card */
    .card-pro h4 {{ color: #1a1a1a !important; margin-bottom: 5px; font-size: 18px; }}
    .card-pro p {{ color: #444444 !important; margin: 2px 0; font-size: 14px; }}
    
    .coin-box {{ background: #FFF9C4; color: #F57F17; padding: 15px; border-radius: 10px; text-align: center; font-weight: bold; border: 2px solid #F57F17; }}
    .btn-zap {{ background-color: #25D366; color: white !important; padding: 15px; border-radius: 10px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; }}
    
    /* Ajuste de abas para telas pequenas */
    .stTabs [data-baseweb="tab"] {{ padding-left: 10px; padding-right: 10px; font-size: 12px; }}
    </style>
""", unsafe_allow_html=True)

st.markdown('<center><span class="azul">GERAL</span><span class="laranja">JÁ</span></center>', unsafe_allow_html=True)

aba1, aba2, aba3, aba4 = st.tabs(["🔍 BUSCAR", "🏦 CONTA", "📝 CRIAR", "🔐 ADM"])

# --- ABA 1: BUSCA ---
with aba1:
    pergunta = st.text_input("O que você precisa?", placeholder="Ex: Pintor", key="mob_search")
    if pergunta:
        busca = pergunta.lower()
        cat = None
        for k, v in MAPEAMENTO_IA.items():
            if k in busca: cat = v; break
        if not cat:
            for p in LISTA_FINAL:
                if p.lower() in busca: cat = p; break

        if cat:
            st.success(f"Encontramos: {cat}")
            res = db.collection("profissionais").where("area", "==", cat).where("aprovado", "==", True).stream()
            for doc in res:
                d = doc.to_dict()
                st.markdown(f'''
                    <div class="card-pro">
                        <h4>👤 {d["nome"]}</h4>
                        <p>📍 {d.get("localizacao", "Grajaú")}</p>
                        <p>💼 {d["area"]}</p>
                    </div>
                ''', unsafe_allow_html=True)
                if d.get("saldo", 0) >= VALOR_CLIQUE:
                    if st.button(f"ZAP DE {d['nome'].split()[0].upper()}", key=doc.id):
                        db.collection("profissionais").document(doc.id).update({"saldo": firestore.Increment(-VALOR_CLIQUE)})
                        st.markdown(f'<a href="https://wa.me/55{d["whatsapp"]}" class="btn-zap">ABRIR WHATSAPP</a>', unsafe_allow_html=True)
                else: st.warning("Profissional sem créditos.")
        else: st.error("Não entendi. Tente 'Pintor' ou 'Vazamento'.")

# --- ABA 2: CONTA ---
with aba2:
    st.subheader("🏦 Sua Carteira")
    uz = st.text_input("WhatsApp:", key="u_z")
    us = st.text_input("Senha:", type="password", key="u_s")
    if uz and us:
        doc = db.collection("profissionais").document(uz).get()
        if doc.exists and doc.to_dict().get("senha") == us:
            d = doc.to_dict()
            st.markdown(f'<div class="coin-box">Saldo: {d.get("saldo", 0)} Moedas</div>', unsafe_allow_html=True)
            st.write(f"PIX Recarga: {PIX_CHAVE}")
            st.markdown(f'<a href="https://wa.me/{ZAP_ADMIN}?text=Recarga:{uz}" class="btn-zap">ENVIAR COMPROVANTE</a>', unsafe_allow_html=True)
        else: st.error("Dados incorretos.")

# --- ABA 3: CADASTRO ---
with aba3:
    st.subheader("📝 Cadastre-se")
    with st.form("f_cad"):
        n = st.text_input("Nome")
        z = st.text_input("WhatsApp")
        s = st.text_input("Senha", type="password")
        l = st.text_input("Bairro")
        p = st.selectbox("Profissão", LISTA_FINAL)
        if st.form_submit_button("CADASTRAR"):
            db.collection("profissionais").document(z).set({
                "nome": n, "whatsapp": z, "senha": s, "area": p, "localizacao": l, "saldo": BONUS_INICIAL, "aprovado": False
            })
            st.success("Aguarde aprovação!")

# --- ABA 4: ADMIN ---
with aba4:
    ap = st.text_input("Senha Admin", type="password")
    if ap == SENHA_ADMIN:
        tz = st.text_input("WhatsApp do Profissional:")
        if tz:
            ref = db.collection("profissionais").document(tz)
            if ref.get().exists:
                if st.button("PUNIR (-5)"): ref.update({"saldo": firestore.Increment(-5)}); st.rerun()
                if st.button("RESETAR SENHA"): ref.update({"senha": "1234"}); st.success("Senha: 1234")
        st.divider()
        pend = db.collection("profissionais").where("aprovado", "==", False).stream()
        for p in pend:
            if st.button(f"APROVAR {p.to_dict()['nome']}", key=f"ap_{p.id}"):
                db.collection("profissionais").document(p.id).update({"aprovado": True}); st.rerun()
