import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import random

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="GeralJá | Oficial", page_icon="⚡", layout="centered")

# --- 2. CONEXÃO FIREBASE (PEÇA POR PEÇA) ---
db = None

if not firebase_admin._apps:
    try:
        # Monta o dicionário manualmente usando as chaves individuais dos Secrets
        firebase_dict = {
            "type": "service_account",
            "project_id": st.secrets["PROJECT_ID"],
            "private_key_id": st.secrets["PRIVATE_KEY_ID"],
            # O .replace garante que as quebras de linha da chave sejam lidas corretamente
            "private_key": st.secrets["PRIVATE_KEY"].replace('\\n', '\n'),
            "client_email": st.secrets["CLIENT_EMAIL"],
            "client_id": st.secrets["CLIENT_ID"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{st.secrets['CLIENT_EMAIL']}",
            "universe_domain": "googleapis.com"
        }
        
        cred = credentials.Certificate(firebase_dict)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        st.toast("Conexão estabelecida!", icon="✅")
    except Exception as e:
        st.error(f"❌ Erro de Configuração: {e}")
        st.info("Verifique se os nomes das chaves no Secrets estão corretos (PROJECT_ID, etc).")
else:
    db = firestore.client()

# --- 3. FUNÇÕES ---
def criar_link_zap(numero, mensagem):
    n = "".join(filter(str.isdigit, numero))
    return f"https://wa.me/55{n}?text={mensagem.replace(' ', '%20')}"

# --- 4. ESTADO E DESIGN ---
if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'
CHAVE_PIX = "09be938c-ee95-469f-b221-a3beea63964b"

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    .azul { color: #0047AB; font-size: 40px; font-weight: 900; }
    .laranja { color: #FF8C00; font-size: 40px; font-weight: 900; }
    div.stButton > button { border-radius: 8px; font-weight: bold; width: 100%; }
    .card-social { background: #f8f9fa; padding: 12px; border-radius: 10px; margin-bottom: 8px; border-left: 5px solid #0047AB; }
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

# --- 6. TELAS ---

if db is None:
    st.warning("Sistema aguardando configuração do banco de dados.")

elif st.session_state.etapa == 'busca':
    area = st.selectbox("O que você procura no Grajaú?", ["", "Pintor", "Eletricista", "Encanador", "Diarista", "Mecânico"])
    if area:
        profs = db.collection("profissionais").where("profissao", "==", area).stream()
        for p in profs:
            d = p.to_dict()
            with st.expander(f"👤 {d['nome']}"):
                st.write(f"Serviço: {area}")
                if st.button(f"Liberar Contato: {d['nome']}", key=p.id):
                    st.session_state.etapa = 'pagamento'; st.rerun()

elif st.session_state.etapa == 'social':
    st.subheader("👥 Mural do Bairro")
    with st.form("mural_form"):
        msg = st.text_area("Poste algo para o Grajaú")
        if st.form_submit_button("Enviar"):
            if msg:
                db.collection("mural").add({"msg": msg, "data": datetime.datetime.now()})
                st.rerun()
    posts = db.collection("mural").order_by("data", direction=firestore.Query.DESCENDING).limit(10).stream()
    for p in posts:
        st.markdown(f'<div class="card-social">{p.to_dict()["msg"]}</div>', unsafe_allow_html=True)

elif st.session_state.etapa == 'cadastro':
    st.subheader("👷 Cadastro de Profissional")
    n = st.text_input("Nome")
    a = st.selectbox("Sua Área", ["Pintor", "Eletricista", "Encanador", "Diarista", "Mecânico"])
    z = st.text_input("WhatsApp")
    if st.button("CADASTRAR"):
        if n and z:
            db.collection("profissionais").document(z).set({
                "nome": n, "profissao": a, "status": "Verificado ✔️", "data": datetime.datetime.now()
            })
            st.success("Cadastro realizado!")
            st.balloons()

elif st.session_state.etapa == 'pagamento':
    st.subheader("💳 Pagamento de Taxa")
    st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={CHAVE_PIX}")
    st.info("Taxa de R$ 25,00 para liberar o contato verificado.")
    if st.button("VOLTAR"):
        st.session_state.etapa = 'busca'; st.rerun()
