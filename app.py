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
SENHA_ADMIN = "grajau2025"
VALOR_CLIQUE = 1 
BONUS_INICIAL = 5

# --- LISTA DE PROFISSÕES ---
profissoes_completas = ["Ajudante Geral", "Borracheiro", "Cabeleireiro", "Diarista", "Eletricista", "Encanador", "Manicure", "Mecânico", "Montador de Móveis", "Pedreiro", "Pintor"]
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

aba1, aba2, aba3, aba4 = st.tabs(["🔍 BUSCAR", "🏦 CARTEIRA", "📝 CADASTRO", "🔐 ADMIN"])

# mapeamento da IA (Necessário para ambas as abas)
MAPEAMENTO_IA = {
    "vazamento": "Encanador", "cano": "Encanador", "torneira": "Encanador",
    "curto": "Eletricista", "luz": "Eletricista", "fiação": "Eletricista",
    "pintar": "Pintor", "parede": "Pintor",
    "reforma": "Pedreiro", "laje": "Pedreiro", "piso": "Pedreiro",
    "pneu": "Borracheiro", "estepe": "Borracheiro", "furou": "Borracheiro",
    "faxina": "Diarista", "limpeza": "Diarista",
    "unha": "Manicure", "cabelo": "Cabeleireiro",
    "montar": "Montador de Móveis", "guarda-roupa": "Montador de Móveis"
}

# --- ABA 1: BUSCA ---
with aba1:
    st.markdown("### 🔍 O que você precisa no Grajaú hoje?")
    pergunta = st.text_input("Descreva o que você precisa:", placeholder="Ex: meu pneu furou")
    
    if pergunta:
        busca_limpa = pergunta.lower()
        categoria_detectada = None
        for chave, profissao in MAPEAMENTO_IA.items():
            if chave in busca_limpa:
                categoria_detectada = profissao
                break

        if categoria_detectada:
            st.success(f"🤖 IA: Você precisa de: **{categoria_detectada}**")
            resultados = db.collection("profissionais").where("area", "==", categoria_detectada).where("aprovado", "==", True).stream()
            
            for doc in resultados:
                d = doc.to_dict()
                st.markdown(f'<div class="card-pro"><h4>👤 {d["nome"]}</h4><p><b>Especialidade:</b> {d["area"]}</p></div>', unsafe_allow_html=True)
                if d.get("saldo", 0) >= VALOR_CLIQUE:
                    if st.button(f"VER CONTATO: {d['nome'].upper()}", key=f"src_{doc.id}"):
                        db.collection("profissionais").document(doc.id).update({"saldo": firestore.Increment(-VALOR_CLIQUE)})
                        st.success(f"👉 [FALAR NO WHATSAPP](https://wa.me/55{d['whatsapp']})")
                else:
                    st.warning("Profissional sem créditos.")

# --- ABA 2: CARTEIRA ---
with aba2:
    st.subheader("🏦 Sua Carteira")
    login = st.text_input("Seu WhatsApp cadastrado:", key="login_carteira")
    if login:
        doc = db.collection("profissionais").document(login).get()
        if doc.exists:
            u = doc.to_dict()
            st.markdown(f"### Olá, {u['nome']}!")
            st.markdown(f'<div class="coin-box">Saldo: {u.get("saldo", 0)} GeralCoins</div>', unsafe_allow_html=True)
            st.divider()
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={PIX_CHAVE}")
            st.markdown(f'Chave PIX: `{PIX_CHAVE}`')
            st.markdown(f'<a href="https://wa.me/{ZAP_ADMIN}?text=Recarga: {login}" class="btn-zap">ENVIAR COMPROVANTE</a>', unsafe_allow_html=True)
        else:
            st.error("❌ WhatsApp não encontrado. Cadastre-se na aba ao lado.")

# --- ABA 3: CADASTRO COM IA ---
with aba3:
    st.subheader("🚀 Novo Cadastro com IA")
    novo_zap = st.text_input("WhatsApp para novo cadastro:", key="novo_cadastro")
    if novo_zap:
        check = db.collection("profissionais").document(novo_zap).get()
        if check.exists:
            st.warning("Você já tem cadastro!")
        else:
            with st.form("form_ia"):
                n = st.text_input("Nome Completo")
                desc = st.text_area("Descreva seu serviço")
                if st.form_submit_button("CADASTRAR"):
                    cat_ia = "Ajudante Geral"
                    for k, v in MAPEAMENTO_IA.items():
                        if k in desc.lower():
                            cat_ia = v
                            break
                    db.collection("profissionais").document(novo_zap).set({
                        "nome": n, "whatsapp": novo_zap, "area": cat_ia,
                        "saldo": BONUS_INICIAL, "aprovado": False
                    })
                    st.success(f"✅ Cadastrado como {cat_ia}! Aguarde aprovação.")

# --- ABA 4: ADMIN ---
with aba4:
    senha = st.text_input("Senha Admin", type="password")
    if senha == SENHA_ADMIN:
        st.subheader("⚙️ Painel Admin")
        pendentes = db.collection("profissionais").where("aprovado", "==", False).stream()
        for p in pendentes:
            pd = p.to_dict()
            if st.button(f"APROVAR {pd['nome']} ({p.id})"):
                db.collection("profissionais").document(p.id).update({"aprovado": True})
                st.rerun()











