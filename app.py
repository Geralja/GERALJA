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
import json
import base64
import re
import math
import datetime
import random

# ==============================================================================
# 1. ARQUITETURA DE SISTEMA E SETUP DE IA
# ==============================================================================
st.set_page_config(
    page_title="GeralJá | Profissionais de São Paulo",
    page_icon="🛠️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

@st.cache_resource
def setup_nltk():
    try:
        nltk.download('punkt')
        nltk.download('stopwords')
        nltk.download('wordnet')
        nltk.download('omw-1.4')
        nltk.download('punkt_tab')
    except:
        pass

setup_nltk()

# ==============================================================================
# 2. CAMADA DE PERSISTÊNCIA: CONEXÃO FIREBASE
# ==============================================================================
@st.cache_resource
def inicializar_infraestrutura_dados():
    if not firebase_admin._apps:
        try:
            b64_key = st.secrets["FIREBASE_BASE64"]
            decoded_json = base64.b64decode(b64_key).decode("utf-8")
            cred_dict = json.loads(decoded_json)
            credenciais = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(credenciais)
        except Exception as e:
            st.error(f"⚠️ Erro de Infraestrutura: {e}")
            st.stop()
    return firestore.Client.from_service_account_info(json.loads(base64.b64decode(st.secrets["FIREBASE_BASE64"]).decode("utf-8")))

db = inicializar_infraestrutura_dados()

# ==============================================================================
# 3. CONSTANTES E REGRAS DE NEGÓCIO
# ==============================================================================
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ACESSO_ADMIN = "mumias"
TAXA_CONTATO = 1
BONUS_WELCOME = 5
LAT_SP_REF = -23.5505
LON_SP_REF = -46.6333

# ==============================================================================
# 4. MOTOR DE INTELIGÊNCIA ARTIFICIAL E GEOLOCALIZAÇÃO
# ==============================================================================
def calcular_km_sp(lat1, lon1, lat2, lon2):
    R = 6371 
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)

CONCEITOS_SERVICOS = {
    "vazamento": "Encanador", "cano": "Encanador", "chuveiro": "Eletricista",
    "fio": "Eletricista", "pintar": "Pintor", "reforma": "Pedreiro",
    "faxina": "Diarista", "móvel": "Montador", "unha": "Manicure", "carro": "Mecânico"
}

def processar_servico_ia(texto):
    if not texto: return "Ajudante Geral"
    t = texto.lower()
    for k, v in CONCEITOS_SERVICOS.items():
        if k in t: return v
    return "Especialista"

def busca_inteligente_robusta(busca, profissionais_stream):
    if not busca: return []
    lista_profs = list(profissionais_stream)
    tokens = word_tokenize(busca.lower())
    stop_words = set(stopwords.words('portuguese'))
    lemmatizer = WordNetLemmatizer()
    termos = [lemmatizer.lemmatize(t) for t in tokens if t not in stop_words]
    
    res = []
    for p in lista_profs:
        d = p.to_dict()
        d['doc_id'] = p.id
        score = 0
        area, nome = str(d.get('area','')).lower(), str(d.get('nome','')).lower()
        for t in termos:
            score += fuzz.partial_ratio(t, area) * 3
            score += fuzz.partial_ratio(t, nome) * 1
        score += min(d.get('saldo', 0) / 2, 30) # Boost por saldo
        if score > 50: res.append({'profissional': d, 'score': score})
    return sorted(res, key=lambda x: x['score'], reverse=True)

# ==============================================================================
# 5. DESIGN CSS CUSTOMIZADO
# ==============================================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap');
    * { font-family: 'Montserrat', sans-serif; }
    .txt-azul { color: #0047AB; font-size: 50px; font-weight: 900; }
    .txt-laranja { color: #FF8C00; font-size: 50px; font-weight: 900; }
    .card-vazado { 
        background: white; border-radius: 20px; padding: 20px; margin-bottom: 15px;
        border-left: 10px solid #0047AB; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        display: flex; align-items: center;
    }
    .avatar-pro { width: 80px; height: 80px; border-radius: 50%; object-fit: cover; margin-right: 20px; }
    .btn-wpp { 
        background: #25D366; color: white !important; padding: 10px; 
        border-radius: 10px; text-decoration: none; display: block; text-align: center; font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 6. INTERFACE PRINCIPAL (ABAS)
# ==============================================================================
st.markdown('<center><span class="txt-azul">GERAL</span><span class="txt-laranja">JÁ</span><p style="margin-top:-20px; letter-spacing:5px;">SÃO PAULO</p></center>', unsafe_allow_html=True)

UI_ABAS = st.tabs(["🔍 BUSCAR", "👤 MINHA CONTA", "📝 CADASTRAR", "🔑 ADMIN"])

# ABA 1: BUSCA
with UI_ABAS[0]:
    busca = st.text_input("O que você precisa hoje?", placeholder="Ex: Encanador para pia")
    if busca:
        query = db.collection("profissionais").where("aprovado", "==", True).stream()
        resultados = busca_inteligente_robusta(busca, query)
        
        if not resultados:
            st.warning("Nenhum profissional encontrado para este termo.")
        else:
            for r in resultados:
                p = r['profissional']
                dist = calcular_km_sp(LAT_SP_REF, LON_SP_REF, p.get('lat', LAT_SP_REF), p.get('lon', LON_SP_REF))
                img = p.get('foto_url') or "https://via.placeholder.com/100"
                
                st.markdown(f"""
                <div class="card-vazado">
                    <img src="{img}" class="avatar-pro">
                    <div style="flex-grow:1">
                        <small>📍 {dist}km de distância</small>
                        <h4 style="margin:0">{p['nome']}</h4>
                        <p style="margin:0; color:#666;"><b>{p['area']}</b> - {p.get('localizacao', 'SP')}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if p.get('saldo', 0) >= TAXA_CONTATO:
                    if st.button(f"CONTATAR {p['nome'].split()[0].upper()}", key=f"c_{p['doc_id']}"):
                        db.collection("profissionais").document(p['doc_id']).update({
                            "saldo": firestore.Increment(-TAXA_CONTATO),
                            "cliques": firestore.Increment(1)
                        })
                        st.markdown(f'<a href="https://wa.me/55{p["whatsapp"]}?text=Vi você no GeralJá" class="btn-wpp">ABRIR WHATSAPP</a>', unsafe_allow_html=True)

# ABA 2: LOGIN PROFISSIONAL
with UI_ABAS[1]:
    st.subheader("Acesso do Parceiro")
    col1, col2 = st.columns(2)
    z_log = col1.text_input("WhatsApp", key="l_z")
    p_log = col2.text_input("Senha", type="password", key="l_p")
    
    if z_log and p_log:
        doc = db.collection("profissionais").document(z_log).get()
        if doc.exists and doc.to_dict()['senha'] == p_log:
            d = doc.to_dict()
            st.success(f"Bem-vindo, {d['nome']}!")
            st.metric("Seu Saldo", f"{d.get('saldo', 0)} moedas")
            
            # Recarga PIX interna
            st.divider()
            st.write("### 💰 Recarregar Moedas")
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={PIX_OFICIAL}")
            st.code(f"PIX: {PIX_OFICIAL}")
            st.markdown(f'<a href="https://wa.me/{ZAP_ADMIN}?text=Fiz o PIX para {z_log}" class="btn-wpp">ENVIAR COMPROVANTE</a>', unsafe_allow_html=True)
        else:
            st.error("Dados incorretos")

# ABA 3: CADASTRO
with UI_ABAS[2]:
    with st.form("reg"):
        n = st.text_input("Nome/Empresa")
        w = st.text_input("WhatsApp (com DDD)")
        s = st.text_input("Senha", type="password")
        b = st.text_input("Bairro")
        desc = st.text_area("Descrição dos seus serviços")
        if st.form_submit_button("CADASTRAR"):
            area = processar_servico_ia(desc)
            db.collection("profissionais").document(w).set({
                "nome": n, "whatsapp": w, "senha": s, "area": area,
                "localizacao": b, "saldo": BONUS_WELCOME, "aprovado": False,
                "lat": LAT_SP_REF + random.uniform(-0.05, 0.05),
                "lon": LON_SP_REF + random.uniform(-0.05, 0.05),
                "cliques": 0, "rating": 5.0
            })
            st.success("Cadastro realizado! Aguarde a aprovação do admin.")
            st.balloons()

# ABA 4: ADMIN
with UI_ABAS[3]:
    adm = st.text_input("Senha Admin", type="password")
    if adm == CHAVE_ACESSO_ADMIN:
        profs = db.collection("profissionais").stream()
        for p in profs:
            d = p.to_dict()
            with st.expander(f"{d['nome']} ({'✅' if d['aprovado'] else '⏳'})"):
                st.write(f"Zap: {d['whatsapp']} | Saldo: {d['saldo']}")
                if not d['aprovado']:
                    if st.button("APROVAR", key=f"ap_{p.id}"):
                        db.collection("profissionais").document(p.id).update({"aprovado": True})
                        st.rerun()
                if st.button("EXCLUIR", key=f"ex_{p.id}"):
                    db.collection("profissionais").document(p.id).delete()
                    st.rerun()

st.markdown("<br><center><small>GeralJá SP v10.0 | 2025</small></center>", unsafe_allow_html=True)














