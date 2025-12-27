import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime

# --- CONEXÃO FIREBASE (MÉTODO BASE64 - À PROVA DE ERROS) ---
db = None

if not firebase_admin._apps:
    try:
        # 1. Pega o código do cofre
        b64_data = st.secrets["FIREBASE_BASE64"]
        # 2. Decodifica para JSON original
        json_data = base64.b64decode(b64_data).decode("utf-8")
        info_chave = json.loads(json_data)
        
        cred = credentials.Certificate(info_chave)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        st.toast("Conectado com sucesso!", icon="✅")
    except Exception as e:
        st.error(f"❌ Erro na decodificação: {e}")
        st.stop()
else:
    db = firestore.client()

# --- ABAIXO SEGUE O RESTANTE DO SEU CÓDIGO (Busca, Mural, etc) ---
st.title("GeralJá Grajaú")
st.write("Se você está vendo isso, o banco de dados finalmente conectou!")

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="GeralJá | Grajaú", page_icon="⚡", layout="centered")

# --- 2. CONEXÃO FIREBASE (SISTEMA BLINDADO) ---
db = None

if not firebase_admin._apps:
    try:
        # Pega a chave e limpa qualquer erro de formatação invisível
        p_key = st.secrets["PRIVATE_KEY"].strip()
        
        # Resolve o problema das barras invertidas que causa o erro de PEM file
        if "\\n" in p_key:
            p_key = p_key.replace("\\n", "\n")
        
        # Garante que as quebras de linha sejam interpretadas corretamente
        p_key = p_key.replace(" ", " ") # Mantém espaços internos
            
        firebase_dict = {
            "type": "service_account",
            "project_id": st.secrets["PROJECT_ID"],
            "private_key_id": st.secrets["PRIVATE_KEY_ID"],
            "private_key": p_key,
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
        st.toast("Conectado ao Firebase!", icon="🔥")
    except Exception as e:
        st.error(f"❌ Erro de Configuração: {e}")
        st.stop() # Para o app aqui para não dar erro embaixo
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
    .card-pro { background: #ffffff; padding: 20px; border-radius: 15px; border: 1px solid #eee; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 4. CABEÇALHO ---
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

# --- 5. TELAS ---

# TELA DE BUSCA
if st.session_state.etapa == 'busca':
    st.subheader("O que você procura no Grajaú?")
    servico = st.selectbox("Escolha uma categoria", ["", "Pintor", "Eletricista", "Encanador", "Diarista", "Mecânico"])
    
    if servico:
        profs = db.collection("profissionais").where("profissao", "==", servico).stream()
        encontrou = False
        for p in profs:
            encontrou = True
            d = p.to_dict()
            st.markdown(f'<div class="card-pro"><h3>{d["nome"]}</h3><p>Status: {d.get("status", "Ativo")}</p></div>', unsafe_allow_html=True)
            if st.button(f"Ver Contato de {d['nome']}", key=p.id):
                st.session_state.etapa = 'pagamento'; st.rerun()
        if not encontrou:
            st.info("Nenhum profissional cadastrado nesta área ainda.")

# TELA DO MURAL
elif st.session_state.etapa == 'social':
    st.subheader("👥 Mural da Comunidade")
    with st.form("form_mural", clear_on_submit=True):
        msg = st.text_area("O que está acontecendo no bairro?")
        if st.form_submit_button("Postar"):
            if msg:
                db.collection("mural").add({"msg": msg, "data": datetime.datetime.now()})
                st.rerun()
    
    posts = db.collection("mural").order_by("data", direction=firestore.Query.DESCENDING).limit(10).stream()
    for p in posts:
        st.markdown(f'<div class="card-mural">{p.to_dict()["msg"]}</div>', unsafe_allow_html=True)

# TELA DE CADASTRO
elif st.session_state.etapa == 'cadastro':
    st.subheader("👷 Cadastro de Profissional")
    nome = st.text_input("Nome Completo")
    area = st.selectbox("Sua Profissão", ["Pintor", "Eletricista", "Encanador", "Diarista", "Mecânico"])
    zap = st.text_input("WhatsApp (com DDD)")
    
    if st.button("FINALIZAR CADASTRO"):
        if nome and zap:
            db.collection("profissionais").document(zap).set({
                "nome": nome, "profissao": area, "status": "Verificado ✔️", "data": datetime.datetime.now()
            })
            st.balloons()
            st.success("Cadastrado com sucesso!")
        else:
            st.error("Preencha todos os campos.")

# TELA DE PAGAMENTO
elif st.session_state.etapa == 'pagamento':
    st.subheader("💳 Liberação de Contato")
    st.write("Para ver o WhatsApp do profissional, realize o pagamento da taxa única de verificação.")
    st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={CHAVE_PIX}")
    st.code(CHAVE_PIX)
    if st.button("VOLTAR PARA BUSCA"):
        st.session_state.etapa = 'busca'; st.rerun()

