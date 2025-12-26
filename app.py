import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
import datetime
import random

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="GeralJá | Grajaú", page_icon="⚡", layout="centered")

# --- CONEXÃO FIREBASE (BLINDADA) ---
db = None

if not firebase_admin._apps:
    try:
        # Pega o segredo do Streamlit
        raw_json = st.secrets["FIREBASE_JSON"]
        
        # Limpa espaços extras e garante que o Python entenda como JSON
        if isinstance(raw_json, str):
            # Remove espaços no início/fim e limpa quebras de linha invisíveis
            cleaned_json = raw_json.strip()
            firebase_info = json.loads(cleaned_json)
        else:
            # Caso o Streamlit já tenha convertido para dicionário
            firebase_info = dict(raw_json)
            
        cred = credentials.Certificate(firebase_info)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
    except Exception as e:
        st.error(f"⚠️ Erro na Chave do Firebase: {e}")
        st.info("Dica: Verifique se o JSON nos Secrets começa com { e termina com }")
else:
    db = firestore.client()

# --- FUNÇÕES ---
def criar_link_zap(numero, mensagem):
    n = "".join(filter(str.isdigit, numero))
    return f"https://wa.me/55{n}?text={mensagem.replace(' ', '%20')}"

# --- ESTADO DO APP ---
if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'
CHAVE_PIX = "09be938c-ee95-469f-b221-a3beea63964b"

# --- DESIGN ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    .azul { color: #0047AB; font-size: 40px; font-weight: 900; }
    .laranja { color: #FF8C00; font-size: 40px; font-weight: 900; }
    div.stButton > button { border-radius: 8px; font-weight: bold; width: 100%; height: 45px; }
    .card { background: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO ---
st.markdown('<div style="text-align:center"><span class="azul">GERAL</span><span class="laranja">JÁ</span></div>', unsafe_allow_html=True)
cols = st.columns(4)
menu = ["🔍 Busca", "👥 Mural", "👷 Cadastro", "📊 Admin"]
tabs = ['busca', 'social', 'cadastro', 'admin']

for i, col in enumerate(cols):
    if col.button(menu[i]):
        st.session_state.etapa = tabs[i]
        st.rerun()

st.divider()

# --- LÓGICA DAS TELAS ---

if db is None:
    st.error("Sistema Offline: O Banco de Dados não foi conectado corretamente.")

elif st.session_state.etapa == 'cadastro':
    st.subheader("👷 Cadastro de Prestador")
    nome = st.text_input("Nome")
    zap = st.text_input("WhatsApp (ex: 11999999999)")
    area = st.selectbox("Área", ["Pintor", "Eletricista", "Encanador", "Diarista", "Mecânico"])
    
    if st.button("GERAR CÓDIGO E SALVAR"):
        if nome and zap:
            cod = str(random.randint(1000, 9999))
            # Salva no Firebase
            db.collection("profissionais").document(zap).set({
                "nome": nome, "profissao": area, "codigo": cod, "status": "Pendente", "data": datetime.datetime.now()
            })
            link = criar_link_zap(zap, f"Meu código de ativação GeralJá é: {cod}")
            st.success(f"Código {cod} gerado para {nome}!")
            st.markdown(f'<a href="{link}" target="_blank"><button style="width:100%; background:#25D366; color:white; border:none; padding:12px; border-radius:8px;">ENVIAR PARA WHATSAPP</button></a>', unsafe_allow_html=True)
        else:
            st.warning("Preencha todos os campos!")

elif st.session_state.etapa == 'busca':
    servico = st.selectbox("O que você precisa hoje?", ["", "Pintor", "Eletricista", "Encanador", "Diarista"])
    if servico:
        docs = db.collection("profissionais").where("profissao", "==", servico).stream()
        encontrou = False
        for d in docs:
            encontrou = True
            info = d.to_dict()
            with st.container():
                st.markdown(f'<div class="card"><b>{info["nome"]}</b><br>Status: {info["status"]}</div>', unsafe_allow_html=True)
                if st.button(f"Contratar {info['nome']}", key=d.id):
                    st.session_state.etapa = 'pagamento'; st.rerun()
        if not encontrou: st.info("Nenhum profissional nesta área ainda.")

elif st.session_state.etapa == 'social':
    st.subheader("👥 Mural do Bairro")
    with st.form("post"):
        msg = st.text_area("Novidades do Grajaú?")
        if st.form_submit_button("Postar"):
            if msg:
                db.collection("mural").add({"msg": msg, "data": datetime.datetime.now()})
                st.rerun()
    posts = db.collection("mural").order_by("data", direction=firestore.Query.DESCENDING).limit(5).stream()
    for p in posts:
        st.markdown(f'<div style="background:#f9f9f9; padding:10px; border-radius:5px; margin-bottom:5px;">{p.to_dict()["msg"]}</div>', unsafe_allow_html=True)

elif st.session_state.etapa == 'pagamento':
    st.subheader("💳 Liberação de Contato")
    st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={CHAVE_PIX}")
    st.code(CHAVE_PIX)
    if st.button("JÁ PAGUEI"):
        st.success("Verificando pagamento... Em breve o contato aparecerá aqui!")
