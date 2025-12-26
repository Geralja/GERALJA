import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
import datetime
import random

# --- 1. CONFIGURAÇÃO E CONEXÃO SEGURA ---
st.set_page_config(page_title="GeralJá | Oficial", page_icon="⚡", layout="centered")

# Inicializa o banco de dados como None para evitar erros de travamento
db = None

if not firebase_admin._apps:
    try:
        # Tenta ler a chave secreta do cofre do Streamlit
        firebase_info = json.loads(st.secrets["FIREBASE_JSON"])
        cred = credentials.Certificate(firebase_info)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
    except Exception as e:
        st.error(f"Erro de Conexão: Verifique se o JSON nos Secrets está correto. Detalhe: {e}")
else:
    db = firestore.client()

# --- 2. FUNÇÕES DE APOIO ---
def criar_link_zap(numero, mensagem):
    numero_limpo = "".join(filter(str.isdigit, numero))
    msg_url = mensagem.replace(" ", "%20")
    return f"https://wa.me/55{numero_limpo}?text={msg_url}"

# --- 3. ESTADO DO APP ---
if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'
CHAVE_PIX = "09be938c-ee95-469f-b221-a3beea63964b"

# --- 4. DESIGN CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    .azul { color: #0047AB; font-size: 42px; font-weight: 900; }
    .laranja { color: #FF8C00; font-size: 42px; font-weight: 900; }
    div.stButton > button { border-radius: 10px; font-weight: bold; width: 100%; }
    .btn-acao div.stButton > button { background-color: #FF8C00 !important; color: white !important; height: 50px; }
    .card-post { background: #f9f9f9; padding: 15px; border-radius: 12px; margin-bottom: 10px; border-left: 5px solid #0047AB; }
    </style>
""", unsafe_allow_html=True)

# --- 5. CABEÇALHO ---
st.markdown('<div style="text-align:center"><span class="azul">GERAL</span><span class="laranja">JÁ</span></div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1: 
    if st.button("🔍 Busca"): st.session_state.etapa = 'busca'; st.rerun()
with c2: 
    if st.button("👥 Mural"): st.session_state.etapa = 'social'; st.rerun()
with c3: 
    if st.button("👷 Cadastro"): st.session_state.etapa = 'cadastro'; st.rerun()
with c4: 
    if st.button("📊 Admin"): st.session_state.etapa = 'admin'; st.rerun()

st.divider()

# --- 6. TELAS DO APP ---

if db is None:
    st.warning("⚠️ O sistema está operando em modo offline. Verifique as chaves do Firebase.")

# TELA DE CADASTRO COM VERIFICAÇÃO ZAP
elif st.session_state.etapa == 'cadastro':
    st.subheader("👷 Cadastro de Profissional")
    passo = st.radio("Siga os passos:", ["1. Dados", "2. Validar"], horizontal=True)

    if passo == "1. Dados":
        nome_p = st.text_input("Nome")
        area_p = st.selectbox("Área", ["Pintor", "Eletricista", "Encanador", "Diarista", "Mecânico"])
        zap_p = st.text_input("WhatsApp (DDD+Número)")
        
        if st.button("GERAR CÓDIGO GRATUITO"):
            if nome_p and zap_p:
                cod = str(random.randint(1000, 9999))
                db.collection("verificacoes").document(zap_p).set({
                    "nome": nome_p, "area": area_p, "codigo": cod, "data": datetime.datetime.now()
                })
                link = criar_link_zap(zap_p, f"Seu código GeralJá é: {cod}")
                st.success(f"Código {cod} gerado!")
                st.markdown(f'<a href="{link}" target="_blank"><button style="width:100%; background: #25D366; color:white; border:none; padding:10px; border-radius:10px;">RECEBER NO WHATSAPP</button></a>', unsafe_allow_html=True)
            else: st.error("Preencha tudo!")

    else:
        v_zap = st.text_input("Confirme seu Zap")
        v_cod = st.text_input("Digite o Código")
        if st.button("FINALIZAR"):
            res = db.collection("verificacoes").document(v_zap).get()
            if res.exists and res.to_dict()['codigo'] == v_cod:
                dados = res.to_dict()
                db.collection("profissionais").document(v_zap).set({
                    "nome": dados['nome'], "profissao": dados['area'], "status": "Verificado ✔️"
                })
                st.balloons()
                st.success("Perfil Ativo!")
            else: st.error("Código inválido!")

# TELA DE BUSCA
elif st.session_state.etapa == 'busca':
    servico = st.selectbox("O que você procura no Grajaú?", ["", "Pintor", "Eletricista", "Encanador", "Diarista"])
    if servico:
        profs = db.collection("profissionais").where("profissao", "==", servico).stream()
        for p in profs:
            d = p.to_dict()
            with st.expander(f"👤 {d['nome']}"):
                st.write(f"Status: {d['status']}")
                if st.button(f"Contratar {d['nome']}", key=p.id):
                    st.session_state.etapa = 'pagamento'; st.rerun()

# TELA SOCIAL
elif st.session_state.etapa == 'social':
    with st.form("post"):
        txt = st.text_area("Mural do Bairro")
        if st.form_submit_button("Postar"):
            db.collection("mural").add({"msg": txt, "data": datetime.datetime.now()})
    posts = db.collection("mural").order_by("data", direction=firestore.Query.DESCENDING).limit(5).stream()
    for p in posts: st.markdown(f'<div class="card-post">{p.to_dict()["msg"]}</div>', unsafe_allow_html=True)

# TELA PAGAMENTO
elif st.session_state.etapa == 'pagamento':
    st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={CHAVE_PIX}")
    st.info("Apoie o projeto com R$ 25,00 para liberar o contato.")
    if st.button("PAGUEI"): st.success("Obrigado!"); st.session_state.etapa = 'busca'
