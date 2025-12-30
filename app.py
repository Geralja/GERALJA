import streamlit as st
import pandas as pd
from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from fuzzywuzzy import fuzz
from gtts import gTTS
import io
import json
import base64
import math
import random
import datetime

# ----------------------------------------------------------
# 1. SETUP E IA CORE (NLP)
# ----------------------------------------------------------
st.set_page_config(page_title="GeralJá | Próximo de Você", page_icon="📍", layout="wide")

@st.cache_resource
def setup_ia():
    try:
        nltk.download('punkt')
        nltk.download('stopwords')
        nltk.download('wordnet')
        nltk.download('omw-1.4')
        nltk.download('punkt_tab')
    except Exception as e:
        st.error(f"Erro ao baixar recursos NLTK: {e}")

setup_ia()

# ----------------------------------------------------------
# 2. CONEXÃO FIREBASE (Sua lógica de Secret preservada)
# ----------------------------------------------------------
@st.cache_resource
def init_db():
    if not firebase_admin._apps:
        try:
            b64_data = st.secrets["FIREBASE_BASE64"]
            json_data = base64.b64decode(b64_data).decode("utf-8")
            info_chave = json.loads(json_data)
            cred = credentials.Certificate(info_chave)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Erro de Conexão Firebase: {e}")
            st.stop()
    return firestore.Client()

db = init_db()

# ----------------------------------------------------------
# 3. LÓGICA DE PROCESSAMENTO DE TEXTO (IA)
# ----------------------------------------------------------
def inteligência_busca(texto_usuario, lista_profissoes):
    """
    Usa Tokenização, Stopwords e Fuzzy Matching para encontrar o serviço.
    """
    if not texto_usuario: return None
    
    # Normalização
    stop_words = set(stopwords.words('portuguese'))
    tokens = word_tokenize(texto_usuario.lower())
    filtrados = [w for w in tokens if w not in stop_words and len(w) > 2]
    
    # 1. Busca Exata nos Tokens
    for token in filtrados:
        for prof in lista_profissoes:
            if token in prof.lower():
                return prof
                
    # 2. Busca Fuzzy (Aproximada) se não achar exato
    melhor_match = None
    maior_score = 0
    for prof in lista_profissoes:
        score = fuzz.partial_ratio(texto_usuario.lower(), prof.lower())
        if score > 80 and score > maior_score:
            maior_score = score
            melhor_match = prof
            
    return melhor_match if melhor_match else "Ajudante Geral"

# ----------------------------------------------------------
# 4. CONFIGURAÇÕES E DESIGN
# ----------------------------------------------------------
PIX_CHAVE = "11991853488"
ZAP_ADMIN = "5511991853488"
VALOR_CLIQUE = 1
BONUS_INICIAL = 5

PROFISSÕES = sorted([
    "Eletricista", "Encanador", "Pintor", "Pedreiro", "Diarista", 
    "Mecânico", "Manicure", "Cabeleireiro", "Montador de Móveis",
    "Jardineiro", "Técnico de TI", "Freteiro", "Ajudante Geral"
])

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; }
    .card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 15px; border-left: 8px solid #0047AB; }
    .premium-header { text-align: center; padding: 20px; background: linear-gradient(90deg, #0047AB 0%, #FF8C00 100%); color: white; border-radius: 15px; margin-bottom: 25px; }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# 5. INTERFACE (UI)
# ----------------------------------------------------------
st.markdown('<div class="premium-header"><h1>GERALJÁ 📍</h1><p>Inteligência Artificial em Serviços</p></div>', unsafe_allow_html=True)

aba_busca, aba_perfil, aba_cadastro, aba_adm = st.tabs(["🔍 Busca Inteligente", "💼 Área do Profissional", "📝 Cadastro", "🛡️ Painel Admin"])

# --- ABA BUSCA ---
with aba_busca:
    pergunta = st.text_input("O que você precisa agora?", placeholder="Ex: meu chuveiro queimou ou preciso de limpeza")
    
    if pergunta:
        categoria = inteligência_busca(pergunta, PROFISSÕES)
        st.success(f"🤖 Entendi! Você está procurando por: **{categoria}**")
        
        # Busca no Firestore
        profs = db.collection("profissionais").where("area", "==", categoria).where("aprovado", "==", True).stream()
        
        count = 0
        for doc in profs:
            count += 1
            d = doc.to_dict()
            with st.container():
                st.markdown(f"""
                <div class="card">
                    <h4>{d['nome']}</h4>
                    <p>📍 {d.get('cidade', 'São Paulo')} | ⭐ {d.get('rating', 5.0)}</p>
                    <small>{d.get('descricao', '')}</small>
                </div>
                """, unsafe_allow_html=True)
                
                if d.get("saldo", 0) >= VALOR_CLIQUE:
                    if st.button(f"Falar com {d['nome'].split()[0]}", key=doc.id):
                        db.collection("profissionais").document(doc.id).update({"saldo": firestore.Increment(-VALOR_CLIQUE)})
                        st.markdown(f'<a href="https://wa.me/55{d["whatsapp"]}?text=Olá, vi seu perfil no GeralJá!" target="_blank" style="text-decoration:none;"><div style="background:#25D366; color:white; padding:10px; text-align:center; border-radius:10px; font-weight:bold;">ABRIR WHATSAPP</div></a>', unsafe_allow_html=True)
                else:
                    st.warning("Este profissional está sem saldo no momento.")

# --- ABA CADASTRO ---
with aba_cadastro:
    st.subheader("Faça parte da nossa rede")
    with st.form("cad_novo"):
        n = st.text_input("Nome")
        z = st.text_input("WhatsApp (DDD + Número)")
        s = st.text_input("Senha", type="password")
        a = st.selectbox("Sua Especialidade", PROFISSÕES)
        c = st.text_input("Sua Cidade")
        desc = st.text_area("Breve descrição do seu serviço")
        
        enviado = st.form_submit_button("CADASTRAR")
        if enviado and n and z:
            db.collection("profissionais").document(z).set({
                "nome": n, "whatsapp": z, "senha": s, "area": a, "cidade": c,
                "descricao": desc, "saldo": BONUS_INICIAL, "aprovado": False,
                "rating": 5.0, "data": datetime.datetime.now()
            })
            st.balloons()
            st.success("Cadastro enviado! Aguarde aprovação do administrador.")

# --- ABA ADMIN ---
with aba_adm:
    senha_adm = st.text_input("Acesso Master", type="password")
    if senha_adm == "mumias":
        st.write("### Profissionais Aguardando Aprovação")
        pendentes = db.collection("profissionais").where("aprovado", "==", False).stream()
        for p in pendentes:
            data = p.to_dict()
            col1, col2 = st.columns([3, 1])
            col1.write(f"**{data['nome']}** ({data['area']})")
            if col2.button("APROVAR", key=f"ap_{p.id}"):
                db.collection("profissionais").document(p.id).update({"aprovado": True})
                st.rerun()

# --- RODAPÉ ---
st.markdown("<br><hr><center>GeralJá v3.5 | 2025</center>", unsafe_allow_html=True)
