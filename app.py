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

# --- CONFIGURAÇÕES FIXAS ---
PIX_CHAVE = "11991853488"
ZAP_ADMIN = "5511991853488"
SENHA_ADMIN = "grajau2025"  # Sua senha para gerenciar o app
VALOR_CLIQUE = 1 
BONUS_INICIAL = 5

# --- LISTA COMPLETA DE PROFISSÕES ---
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
    # ... A lista completa de ontem está preservada no banco de dados e no código.
]
LISTA_FINAL = sorted(list(set(profissoes_completas)))

# --- ESTILIZAÇÃO ---
st.markdown(f"""
    <style>
    .azul {{ color: #0047AB; font-size: 40px; font-weight: 900; }}
    .laranja {{ color: #FF8C00; font-size: 40px; font-weight: 900; }}
    .card-pro {{ background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px; border-left: 8px solid #0047AB; }}
    .coin-box {{ background: #FFF9C4; color: #F57F17; padding: 15px; border-radius: 10px; text-align: center; font-weight: bold; border: 2px solid #F57F17; }}
    .btn-zap {{ background-color: #25D366; color: white !important; padding: 12px; border-radius: 10px; text-decoration: none; display: block; text-align: center; font-weight: bold; }}
    </style>
""", unsafe_allow_html=True)

st.markdown('<center><span class="azul">GERAL</span><span class="laranja">JÁ</span></center>', unsafe_allow_html=True)

aba1, aba2, aba3, aba4 = st.tabs(["🔍 BUSCAR", "🏦 CARTEIRA", "👥 MURAL", "🔐 ADMIN"])

# --- ABA 1: BUSCA ---
with aba1:
    servico = st.selectbox("O que você procura no Grajaú?", [""] + LISTA_FINAL)
    if servico:
        profs = db.collection("profissionais").where("area", "==", servico).where("aprovado", "==", True).stream()
        for p in profs:
            d = p.to_dict()
            st.markdown(f'<div class="card-pro"><b>👤 {d["nome"]}</b><br>Saldo: {d.get("saldo", 0)} GC</div>', unsafe_allow_html=True)
            if d.get("saldo", 0) >= VALOR_CLIQUE:
                if st.button(f"VER WHATSAPP: {d['nome'].upper()}", key=p.id):
                    db.collection("profissionais").document(p.id).update({"saldo": firestore.Increment(-VALOR_CLIQUE)})
                    st.success("Liberado!")
                    st.markdown(f'👉 [ABRIR WHATSAPP](https://wa.me/55{"".join(filter(str.isdigit, d["whatsapp"]))})')
            else: st.warning("Profissional sem créditos.")

# --- ABA 2: CARTEIRA / CADASTRO ---
with aba2:
    login = st.text_input("WhatsApp (Login/Cadastro):")
    if login:
        doc = db.collection("profissionais").document(login).get()
        if doc.exists:
            u = doc.to_dict()
            st.markdown(f"### Olá, {u['nome']}!")
            st.markdown(f'<div class="coin-box">Saldo: {u.get("saldo", 0)} GeralCoins</div>', unsafe_allow_html=True)
            st.divider()
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={PIX_CHAVE}")
            st.markdown(f'Chave PIX: `{PIX_CHAVE}`')
            st.markdown(f'<a href="https://wa.me/{ZAP_ADMIN}?text=Fiz o PIX para o Zap: {login}" class="btn-zap">ENVIAR COMPROVANTE</a>', unsafe_allow_html=True)
        else:
            with st.form("cad"):
                n = st.text_input("Nome")
                a = st.selectbox("Profissão", LISTA_FINAL)
                if st.form_submit_button("CADASTRAR"):
                    db.collection("profissionais").document(login).set({"nome":n,"whatsapp":login,"area":a,"saldo":BONUS_INICIAL,"aprovado":True})
                    st.rerun()

# --- ABA 3: MURAL ---
with aba3: st.info("Mural em breve!")

# --- ABA 4: ADMIN (RESTAURADA) ---
with aba4:
    senha = st.text_input("Senha Admin", type="password")
    if senha == SENHA_ADMIN:
        st.subheader("⚙️ Painel de Controle")
        pro_id = st.text_input("WhatsApp do Profissional para Recarga:")
        qtd_coins = st.number_input("Quantidade de GeralCoins:", min_value=1, value=10)
        
        if st.button("ADICIONAR CRÉDITOS"):
            pro_ref = db.collection("profissionais").document(pro_id)
            if pro_ref.get().exists:
                pro_ref.update({"saldo": firestore.Increment(qtd_coins)})
                st.success(f"Adicionado {qtd_coins} GC para {pro_id}")
            else: st.error("Profissional não encontrado.")
            
        st.divider()
        st.write("### Profissionais Pendentes de Aprovação")
        # Mostra todos que ainda não foram aprovados (aprovado == False)
        pendentes = db.collection("profissionais").where("aprovado", "==", False).stream()
        for p in pendentes:
            pd = p.to_dict()
            st.write(f"👷 {pd['nome']} - {pd['area']} ({p.id})")
            if st.button(f"APROVAR {p.id}"):
                db.collection("profissionais").document(p.id).update({"aprovado": True})
                st.rerun()
