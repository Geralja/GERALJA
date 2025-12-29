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
import re
import math
import datetime
import random

# ==============================================================================
# 1. SETUP DE AMBIENTE E IA
# ==============================================================================
st.set_page_config(page_title="GeralJá SP Gold", page_icon="🏆", layout="centered")

@st.cache_resource
def setup_ia_core():
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')
    nltk.download('omw-1.4')
    nltk.download('punkt_tab')
setup_ia_core()

# ==============================================================================
# 2. CONEXÃO FIREBASE (BLINDADA)
# ==============================================================================
@st.cache_resource
def connect_db():
    if not firebase_admin._apps:
        try:
            b64_key = st.secrets["FIREBASE_BASE64"]
            decoded_json = base64.b64decode(b64_key).decode("utf-8")
            cred_dict = json.loads(decoded_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Erro Crítico de Conexão: {e}")
            st.stop()
    return firestore.Client.from_service_account_info(json.loads(base64.b64decode(st.secrets["FIREBASE_BASE64"]).decode("utf-8")))

db = connect_db()

# ==============================================================================
# 3. CONSTANTES E NOVAS REGRAS
# ==============================================================================
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ACESSO_ADMIN = "mumias"
TAXA_CONTATO = 1
BONUS_WELCOME = 5
LAT_SP_REF, LON_SP_REF = -23.5505, -46.6333

CATEGORIAS_RAPIDAS = ["Encanador", "Eletricista", "Diarista", "Pintor", "Mecânico", "Pedreiro", "Manicure", "Montador"]

# ==============================================================================
# 4. NOVAS FUNÇÕES EXCLUSIVAS
# ==============================================================================

def gerar_audio_convite(nome_pro):
    """Nova Função: Gera áudio para aumentar conversão"""
    texto = f"Olá! Eu sou o {nome_pro}. Clique no botão abaixo para falar comigo agora pelo WhatsApp!"
    tts = gTTS(text=texto, lang='pt', tld='com.br')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    return fp

def obter_selo_vibrante(p_data):
    """Nova Função: Sistema de Gamificação e Selos"""
    saldo = p_data.get('saldo', 0)
    rating = p_data.get('rating', 5.0)
    if saldo > 50 and rating >= 4.8:
        return '<span style="background:linear-gradient(90deg, #FFD700, #FFA500); color:black; padding:2px 8px; border-radius:5px; font-size:10px; font-weight:900;">🏆 ELITE SP</span>'
    if p_data.get('aprovado'):
        return '<span style="background:#0047AB; color:white; padding:2px 8px; border-radius:5px; font-size:10px; font-weight:900;">✅ VERIFICADO</span>'
    return ""

def calcular_km_sp(lat1, lon1, lat2, lon2):
    R = 6371 
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)

def busca_inteligente_robusta(busca, stream):
    if not busca: return []
    lista = list(stream)
    tokens = word_tokenize(busca.lower())
    stop = set(stopwords.words('portuguese'))
    lem = WordNetLemmatizer()
    termos = [lem.lemmatize(t) for t in tokens if t not in stop]
    
    resultados = []
    for doc in lista:
        d = doc.to_dict()
        d['doc_id'] = doc.id
        score = 0
        txt_total = f"{d.get('area','')} {d.get('nome','')} {d.get('localizacao','')}".lower()
        for t in termos:
            score += fuzz.partial_ratio(t, txt_total) * 2
        score += min(d.get('saldo', 0), 20)
        if score > 40: resultados.append({'pro': d, 'score': score})
    return sorted(resultados, key=lambda x: x['score'], reverse=True)

# ==============================================================================
# 5. ESTILO E INTERFACE
# ==============================================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap');
    * { font-family: 'Montserrat', sans-serif; }
    .card-vazado { background: white; border-radius: 20px; padding: 15px; margin-bottom: 12px; border-left: 8px solid #FF8C00; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    .btn-wpp { background: #25D366; color: white !important; padding: 12px; border-radius: 12px; text-decoration: none; display: block; text-align: center; font-weight: 900; margin-top: 10px; }
    .avatar-pro { width: 70px; height: 70px; border-radius: 50%; object-fit: cover; border: 3px solid #eee; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<center><h1 style="color:#0047AB; margin-bottom:0;">GERAL<span style="color:#FF8C00;">JÁ</span></h1><p style="letter-spacing:5px;">SÃO PAULO CAPITAL</p></center>', unsafe_allow_html=True)

UI_ABAS = st.tabs(["🔎 BUSCAR", "🚀 CATEGORIAS", "👤 MINHA CONTA", "📝 CADASTRAR", "🔑 ADMIN"])

# ------------------------------------------------------------------------------
# ABA 1: BUSCA INTELIGENTE
# ------------------------------------------------------------------------------
with UI_ABAS[0]:
    termo = st.text_input("O que você busca em SP?", placeholder="Ex: Preciso de alguém para consertar meu cano", key="main_search")
    if termo:
        query = db.collection("profissionais").where("aprovado", "==", True).stream()
        res = busca_inteligente_robusta(termo, query)
        if not res: st.info("Nenhum profissional exato encontrado. Tente a aba Categorias!")
        else:
            for item in res:
                p = item['pro']
                dist = calcular_km_sp(LAT_SP_REF, LON_SP_REF, p.get('lat', LAT_SP_REF), p.get('lon', LON_SP_REF))
                selo = obter_selo_vibrante(p)
                
                st.markdown(f"""
                <div class="card-vazado">
                    <div style="display:flex; align-items:center;">
                        <img src="{p.get('foto_url') or 'https://via.placeholder.com/100'}" class="avatar-pro">
                        <div style="margin-left:15px;">
                            {selo} <br>
                            <b style="font-size:18px;">{p.get('nome','').upper()}</b><br>
                            <small>📍 {dist}km do Centro | ⭐ {p.get('rating', 5.0)}</small>
                        </div>
                    </div>
                    <p style="margin-top:10px; font-size:14px; color:#444;"><b>Área:</b> {p.get('area','Serviços')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if p.get('saldo', 0) >= TAXA_CONTATO:
                    if st.button(f"FALAR COM {p.get('nome','').split()[0]}", key=f"btn_{p['doc_id']}"):
                        db.collection("profissionais").document(p['doc_id']).update({"saldo": firestore.Increment(-TAXA_CONTATO), "cliques": firestore.Increment(1)})
                        st.audio(gerar_audio_convite(p.get('nome','')), format="audio/mp3")
                        st.markdown(f'<a href="https://wa.me/55{p.get("whatsapp")}?text=Vi seu perfil no GeralJá!" class="btn-wpp">ABRIR WHATSAPP</a>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# ABA 2: CATEGORIAS RÁPIDAS (NOVA FUNÇÃO)
# ------------------------------------------------------------------------------
with UI_ABAS[1]:
    st.subheader("Explore por Categoria")
    cols = st.columns(2)
    for i, cat in enumerate(CATEGORIAS_RAPIDAS):
        if cols[i % 2].button(f"🛠️ {cat}", use_container_width=True):
            st.session_state.main_search = cat # Tenta injetar na busca

# ------------------------------------------------------------------------------
# ABA 3: PERFIL DO PROFISSIONAL
# ------------------------------------------------------------------------------
with UI_ABAS[2]:
    st.subheader("Login do Parceiro")
    col_a, col_b = st.columns(2)
    z_log = col_a.text_input("WhatsApp", key="log_z")
    p_log = col_b.text_input("Senha", type="password", key="log_p")
    if z_log and p_log:
        doc = db.collection("profissionais").document(z_log).get()
        if doc.exists and doc.to_dict().get('senha') == p_log:
            d = doc.to_dict()
            st.success(f"Logado: {d.get('nome')}")
            col1, col2, col3 = st.columns(3)
            col1.metric("Moedas", d.get('saldo', 0))
            col2.metric("Cliques", d.get('cliques', 0))
            col3.metric("Status", "Ativo" if d.get('aprovado') else "Pendente")
            
            st.divider()
            st.write("💰 **Recarga de Moedas via PIX**")
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={PIX_OFICIAL}")
            st.code(f"Chave PIX: {PIX_OFICIAL}")
            st.info("Envie o comprovante para o admin após o pagamento.")
        else: st.error("Acesso negado.")

# ------------------------------------------------------------------------------
# ABA 4: CADASTRO
# ------------------------------------------------------------------------------
with UI_ABAS[3]:
    st.subheader("Cadastre-se Gratuitamente")
    with st.form("reg_form"):
        f_nome = st.text_input("Nome/Empresa")
        f_zap = st.text_input("WhatsApp (Ex: 11999998888)")
        f_pass = st.text_input("Crie uma Senha", type="password")
        f_desc = st.text_area("Descreva seu serviço")
        if st.form_submit_button("CRIAR CONTA"):
            if len(f_zap) >= 11:
                # Classificação automática por IA simples (regex)
                area_ia = "Especialista"
                for k in ["pintar", "cano", "limpeza", "unha"]: 
                    if k in f_desc.lower(): area_ia = k.capitalize()
                
                db.collection("profissionais").document(f_zap).set({
                    "nome": f_nome, "whatsapp": f_zap, "senha": f_pass, "area": area_ia,
                    "saldo": BONUS_WELCOME, "aprovado": False, "cliques": 0, "rating": 5.0,
                    "lat": LAT_SP_REF + random.uniform(-0.05, 0.05), "lon": LON_SP_REF + random.uniform(-0.05, 0.05)
                })
                st.success("Cadastro enviado! Notifique o Admin.")
                st.markdown(f'<a href="https://wa.me/{ZAP_ADMIN}?text=Quero ser aprovado no GeralJá: {f_nome}">AVISAR ADMIN</a>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# ABA 5: ADMIN MASTER
# ------------------------------------------------------------------------------
with UI_ABAS[4]:
    senha_adm = st.text_input("Senha Master", type="password")
    if senha_adm == CHAVE_ACESSO_ADMIN:
        profs = db.collection("profissionais").stream()
        for p_doc in profs:
            d = p_doc.to_dict()
            with st.expander(f"{d.get('nome')} | {d.get('area')} | 💰{d.get('saldo')}"):
                st.write(f"ZAP: {d.get('whatsapp')}")
                if st.button("APROVAR ✅", key=f"ok_{p_doc.id}"):
                    db.collection("profissionais").document(p_doc.id).update({"aprovado": True})
                    st.rerun()
                if st.button("DELETAR 🗑️", key=f"del_{p_doc.id}"):
                    db.collection("profissionais").document(p_doc.id).delete()
                    st.rerun()

st.markdown("<br><hr><center><small>GeralJá SP v10.5 | Built with ❤️ for São Paulo Professionals</small></center>", unsafe_allow_html=True)



