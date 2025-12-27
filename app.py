import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
import datetime
import random

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="GeralJá | Grajaú", page_icon="⚡", layout="centered")

# --- CONEXÃO FIREBASE (SISTEMA ANTI-ERRO) ---
db = None

if not firebase_admin._apps:
    try:
        # Lê o segredo como texto bruto para evitar erros de formatação TOML
        raw_data = st.secrets["CHAVE_BRUTA"].strip()
        info_chave = json.loads(raw_data)
        
        cred = credentials.Certificate(info_chave)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
    except Exception as e:
        st.error(f"⚠️ Erro de Conexão: {e}")
else:
    db = firestore.client()

# --- FUNÇÕES DE APOIO ---
def criar_link_zap(numero, mensagem):
    n = "".join(filter(str.isdigit, numero))
    return f"https://wa.me/55{n}?text={mensagem.replace(' ', '%20')}"

# --- ESTADO DO APP ---
if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'
CHAVE_PIX = "09be938c-ee95-469f-b221-a3beea63964b"

# --- DESIGN CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    .azul { color: #0047AB; font-size: 40px; font-weight: 900; }
    .laranja { color: #FF8C00; font-size: 40px; font-weight: 900; }
    div.stButton > button { border-radius: 8px; font-weight: bold; width: 100%; height: 45px; }
    .card-social { background: #f8f9fa; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #0047AB; }
    .card-prof { background: #ffffff; padding: 20px; border-radius: 15px; border: 1px solid #eee; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO ---
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

# --- LÓGICA DE TELAS ---

if db is None:
    st.warning("Aguardando conexão com o banco de dados...")

# TELA: BUSCA
elif st.session_state.etapa == 'busca':
    st.subheader("O que você procura no Grajaú?")
    servico = st.selectbox("Escolha uma categoria", ["", "Pintor", "Eletricista", "Encanador", "Diarista", "Mecânico"])
    
    if servico:
        docs = db.collection("profissionais").where("profissao", "==", servico).stream()
        encontrou = False
        for d in docs:
            encontrou = True
            info = d.to_dict()
            with st.container():
                st.markdown(f"""
                <div class="card-prof">
                    <h3>{info['nome']}</h3>
                    <p>📍 Atende no bairro | <b>{info['status']}</b></p>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Ver Contato de {info['nome']}", key=d.id):
                    st.session_state.etapa = 'pagamento'; st.rerun()
                st.write("")
        if not encontrou:
            st.info("Ainda não temos profissionais nesta categoria. Seja o primeiro a se cadastrar!")

# TELA: MURAL SOCIAL
elif st.session_state.etapa == 'social':
    st.subheader("👥 Mural da Comunidade")
    with st.form("mural_form", clear_on_submit=True):
        msg = st.text_area("O que está rolando no bairro?")
        if st.form_submit_button("Postar no Mural"):
            if msg:
                db.collection("mural").add({"msg": msg, "data": datetime.datetime.now()})
                st.success("Postado!")
                st.rerun()
    
    posts = db.collection("mural").order_by("data", direction=firestore.Query.DESCENDING).limit(10).stream()
    for p in posts:
        st.markdown(f'<div class="card-social">{p.to_dict()["msg"]}</div>', unsafe_allow_html=True)

# TELA: CADASTRO
elif st.session_state.etapa == 'cadastro':
    st.subheader("👷 Cadastre seus serviços")
    nome = st.text_input("Seu Nome")
    area = st.selectbox("Sua Profissão", ["Pintor", "Eletricista", "Encanador", "Diarista", "Mecânico"])
    zap = st.text_input("WhatsApp (ex: 11988887777)")
    
    if st.button("FINALIZAR CADASTRO"):
        if nome and zap:
            cod_verif = str(random.randint(1000, 9999))
            db.collection("profissionais").document(zap).set({
                "nome": nome, "profissao": area, "status": "Verificado ✔️", "data": datetime.datetime.now()
            })
            st.balloons()
            st.success("Cadastro realizado com sucesso no Firebase!")
        else:
            st.error("Preencha todos os campos!")

# TELA: PAGAMENTO
elif st.session_state.etapa == 'pagamento':
    st.subheader("💳 Liberação de Contato")
    st.write("Para manter o projeto GeralJá e verificar os profissionais, cobramos uma taxa única de R$ 25,00.")
    st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={CHAVE_PIX}")
    st.code(CHAVE_PIX, language="text")
    if st.button("JÁ PAGUEI / VOLTAR"):
        st.session_state.etapa = 'busca'; st.rerun()

# TELA: ADMIN
elif st.session_state.etapa == 'admin':
    st.subheader("📊 Painel Administrativo")
    senha = st.text_input("Senha de Acesso", type="password")
    if senha == "admin777":
        total_profs = len(list(db.collection("profissionais").stream()))
        st.metric("Profissionais Cadastrados", total_profs)
        if st.button("Limpar Mural (Cuidado)"):
            st.warning("Função de limpeza em manutenção.")
