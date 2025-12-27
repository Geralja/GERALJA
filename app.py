import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime
import random

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="GeralJá | Grajaú", page_icon="⚡", layout="centered")

# --- 2. CONEXÃO FIREBASE (MÉTODO BASE64 - BLINDADO) ---
db = None

if not firebase_admin._apps:
    try:
        # Pega a sopa de letrinhas do Secrets
        b64_data = st.secrets["FIREBASE_BASE64"]
        # Transforma de volta no seu JSON original
        json_data = base64.b64decode(b64_data).decode("utf-8")
        info_chave = json.loads(json_data)
        
        cred = credentials.Certificate(info_chave)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        st.toast("🔥 GeralJá Conectado!", icon="✅")
    except Exception as e:
        st.error(f"❌ Erro na Chave: {e}")
        st.info("Certifique-se de que codificou o CONTEÚDO do arquivo JSON no site Base64.")
        st.stop()
else:
    db = firestore.client()

# --- 3. ESTADO E DESIGN ---
if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'
CHAVE_PIX = "09be938c-ee95-469f-b221-a3beea63964b"

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    .azul { color: #0047AB; font-size: 40px; font-weight: 900; }
    .laranja { color: #FF8C00; font-size: 40px; font-weight: 900; }
    div.stButton > button { border-radius: 8px; font-weight: bold; width: 100%; height: 45px; }
    .card-mural { background: #f8f9fa; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #0047AB; }
    </style>
""", unsafe_allow_html=True)

# --- 4. MENU SUPERIOR ---
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

# --- 5. TELAS DO SISTEMA ---

if st.session_state.etapa == 'busca':
    st.subheader("O que você procura no Grajaú?")
    servico = st.selectbox("Escolha uma categoria", ["", "Pintor", "Eletricista", "Encanador", "Diarista", "Mecânico"])
    if servico:
        profs = db.collection("profissionais").where("profissao", "==", servico).stream()
        for p in profs:
            d = p.to_dict()
            st.info(f"👤 {d['nome']} | Status: {d.get('status', 'Ativo')}")
            if st.button(f"Ver Contato de {d['nome']}", key=p.id):
                st.session_state.etapa = 'pagamento'; st.rerun()

elif st.session_state.etapa == 'social':
    st.subheader("👥 Mural da Comunidade")
    with st.form("mural"):
        msg = st.text_area("O que está rolando no bairro?")
        if st.form_submit_button("Postar"):
            if msg:
                db.collection("mural").add({"msg": msg, "data": datetime.datetime.now()})
                st.rerun()
    posts = db.collection("mural").order_by("data", direction=firestore.Query.DESCENDING).limit(5).stream()
    for p in posts:
        st.markdown(f'<div class="card-mural">{p.to_dict()["msg"]}</div>', unsafe_allow_html=True)

elif st.session_state.etapa == 'cadastro':
    st.subheader("👷 Cadastro de Profissional")
    nome = st.text_input("Nome")
    zap = st.text_input("WhatsApp")
    area = st.selectbox("Área", ["Pintor", "Eletricista", "Encanador", "Diarista", "Mecânico"])
    if st.button("SALVAR"):
        if nome and zap:
            db.collection("profissionais").document(zap).set({
                "nome": nome, "profissao": area, "status": "Verificado ✔️", "data": datetime.datetime.now()
            })
            st.success("Cadastrado!")
            st.balloons()

elif st.session_state.etapa == 'pagamento':
    st.subheader("💳 Liberação de Contato")
    st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={CHAVE_PIX}")
    st.code(CHAVE_PIX)
    if st.button("VOLTAR"):
        st.session_state.etapa = 'busca'; st.rerun()
