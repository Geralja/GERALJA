# ==============================================================================
# GERALJÁ - SISTEMA DE GESTÃO DE SERVIÇOS PROFISSIONAIS (EDITION 2025)
# VERSÃO: 12.0 GOLD | LINHAS: 600+ | STATUS: ENTERPRISE READY
# ==============================================================================

# ==============================================================================
# GERALJÁ - SISTEMA DE GEOLOCALIZAÇÃO E INTELIGÊNCIA LOCAL v14.0
# FOCO: FILTRAGEM POR PROXIMIDADE (GPS) E NECESSIDADE ESPECÍFICA
# ==============================================================================

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
# 1. SETUP E IA CORE
# ----------------------------------------------------------
st.set_page_config(page_title="GeralJá | Próximo de Você", page_icon="📍", layout="wide")

@st.cache_resource
def setup_ia():
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')
    nltk.download('omw-1.4')
    nltk.download('punkt_tab')

setup_ia()

# ----------------------------------------------------------
# 2. CONEXÃO FIREBASE
# ----------------------------------------------------------
@st.cache_resource
def get_db():
    if not firebase_admin._apps:
        b64_key = st.secrets["FIREBASE_BASE64"]
        decoded_json = base64.b64decode(b64_key).decode("utf-8")
        firebase_admin.initialize_app(credentials.Certificate(json.loads(decoded_json)))
    return firestore.Client.from_service_account_info(json.loads(base64.b64decode(st.secrets["FIREBASE_BASE64"]).decode("utf-8")))

db = get_db()

# ----------------------------------------------------------
# 3. FUNÇÕES GEOGRÁFICAS (A CHAVE DO SEU PEDIDO)
# ----------------------------------------------------------

def calcular_distancia(lat1, lon1, lat2, lon2):
    """Fórmula de Haversine para distância em KM"""
    if None in [lat1, lon1, lat2, lon2]: return 999
    R = 6371
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)

def motor_busca_local(busca, lat_cliente, lon_cliente, raio_max_km=25):
    """Filtra por necessidade E por distância"""
    if not busca: return []
    
    docs = db.collection("profissionais").where("aprovado", "==", True).stream()
    tokens = word_tokenize(busca.lower())
    lem = WordNetLemmatizer()
    termos = [lem.lemmatize(t) for t in tokens if t not in set(stopwords.words('portuguese'))]
    
    resultados = []
    for doc in docs:
        p = doc.to_dict()
        p['id'] = doc.id
        
        # 1. Cálculo da Distância
        dist = calcular_distancia(lat_cliente, lon_cliente, p.get('lat'), p.get('lon'))
        
        # 2. Score de Relevância (Necessidade)
        texto = f"{p.get('area','')} {p.get('nome','')} {p.get('descricao','')}".lower()
        match_score = 0
        for t in termos:
            match_score += fuzz.partial_ratio(t, texto)
            
        # 3. Filtro Rigoroso: Só entra se tiver match E estiver perto
        if match_score > 40 and dist <= raio_max_km:
            resultados.append({'dados': p, 'distancia': dist, 'score': match_score})
            
    # Ordena: Primeiro os mais perto, depois os com melhor match
    return sorted(resultados, key=lambda x: (x['distancia'], -x['score']))

# ----------------------------------------------------------
# 4. ESTILO CSS PREMIUM
# ----------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap');
    * { font-family: 'Montserrat', sans-serif; }
    .stApp { background-color: #f0f2f6; }
    .header { text-align: center; padding: 30px; background: white; border-bottom: 6px solid #FF8C00; border-radius: 0 0 30px 30px; }
    .card-pro { 
        background: white; border-radius: 20px; padding: 20px; margin-bottom: 15px;
        border-left: 10px solid #0047AB; box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        display: flex; align-items: center;
    }
    .avatar { width: 80px; height: 80px; border-radius: 50%; object-fit: cover; margin-right: 20px; }
    .distancia-tag { background: #E3F2FD; color: #0047AB; padding: 4px 10px; border-radius: 10px; font-weight: bold; font-size: 12px; }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# 5. INTERFACE PRINCIPAL
# ----------------------------------------------------------
st.markdown('<div class="header"><h1 style="color:#0047AB; margin:0;">GERAL<span style="color:#FF8C00;">JÁ</span></h1><p>SERVIÇOS PERTO DE VOCÊ</p></div>', unsafe_allow_html=True)

TABS = st.tabs(["🔎 BUSCAR AGORA", "👤 MEU PAINEL", "🔑 ADMIN"])

with TABS[0]:
    st.write("### 📍 Sua Localização")
    col_gps1, col_gps2 = st.columns(2)
    
    # Simulação de GPS (Em produção, o cliente digita ou o navegador fornece)
    lat_cliente = col_gps1.number_input("Sua Latitude (GPS)", value=-23.55, format="%.6f")
    lon_cliente = col_gps2.number_input("Sua Longitude (GPS)", value=-46.63, format="%.6f")
    
    st.divider()
    busca = st.text_input("O que você precisa?", placeholder="Ex: Encanador, Eletricista...")
    raio = st.slider("Raio de busca (km)", 1, 100, 20)
    
    if busca:
        resultados = motor_busca_local(busca, lat_cliente, lon_cliente, raio)
        
        if not resultados:
            st.error(f"Não encontramos profissionais de '{busca}' num raio de {raio}km.")
        else:
            st.success(f"Encontramos {len(resultados)} profissionais próximos!")
            for r in resultados:
                p = r['dados']
                st.markdown(f"""
                <div class="card-pro">
                    <img src="{p.get('foto_url') or 'https://via.placeholder.com/100'}" class="avatar">
                    <div style="flex-grow:1;">
                        <span class="distancia-tag">📍 {r['distancia']} km de você</span><br>
                        <b style="font-size:1.2rem;">{p.get('nome').upper()}</b><br>
                        <small>{p.get('area')} | ⭐ {p.get('rating')}</small>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"CONTATAR {p.get('nome').split()[0]}", key=f"btn_{p['id']}"):
                    if p.get('saldo', 0) > 0:
                        db.collection("profissionais").document(p['id']).update({"saldo": firestore.Increment(-1), "cliques": firestore.Increment(1)})
                        st.markdown(f'<a href="https://wa.me/55{p.get("whatsapp")}" style="background:#25D366; color:white; padding:15px; display:block; text-align:center; border-radius:10px; text-decoration:none; font-weight:bold;">ABRIR WHATSAPP</a>', unsafe_allow_html=True)
                    else:
                        st.warning("Este profissional atingiu o limite de contatos.")

with TABS[1]:
    # Página do Profissional (Dashboard)
    st.subheader("Acesso do Profissional")
    # ... (Aqui entra a lógica de login que já temos, focando no Dashboard)
    st.info("Logue para ver seu saldo e cliques.")

with TABS[2]:
    # Painel Administrativo
    if st.text_input("Chave Admin", type="password") == "mumias":
        st.write("### Gestão de Profissionais")
        docs = db.collection("profissionais").stream()
        for d in docs:
            data = d.to_dict()
            with st.expander(f"{data.get('nome')} - {data.get('saldo')} moedas"):
                if st.button("Aprovar ✅", key=f"ok_{d.id}"):
                    db.collection("profissionais").document(d.id).update({"aprovado": True})
                if st.button("Banir 🗑️", key=f"del_{d.id}"):
                    db.collection("profissionais").document(d.id).delete()

st.markdown("<br><hr><center><small>GeralJá v14.0 | Geolocalização Ativa</small></center>", unsafe_allow_html=True)
