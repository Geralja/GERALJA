# ==============================================================================
# GERALJÁ SP - SISTEMA DE GESTÃO DE SERVIÇOS PROFISSIONAIS (EDITION 2025)
# VERSÃO: 12.0 GOLD | LINHAS: 600+ | STATUS: ENTERPRISE READY
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
import re
import math
import datetime
import random
import time

# ------------------------------------------------------------------------------
# 1. CONFIGURAÇÕES DE NÚCLEO E UI (LINHAS 30-70)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="GeralJá | Sistema Integrado de Profissionais SP",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

@st.cache_resource
def startup_engine():
    """Inicialização pesada de pacotes NLTK para IA"""
    try:
        nltk.download('punkt')
        nltk.download('stopwords')
        nltk.download('wordnet')
        nltk.download('omw-1.4')
        nltk.download('punkt_tab')
        return True
    except Exception:
        return False

startup_engine()

# ------------------------------------------------------------------------------
# 2. CAMADA DE INFRAESTRUTURA DE DADOS (LINHAS 71-130)
# ------------------------------------------------------------------------------
@st.cache_resource
def get_db_connection():
    """Conexão blindada com o Firebase Firestore"""
    if not firebase_admin._apps:
        try:
            b64_key = st.secrets["FIREBASE_BASE64"]
            decoded_json = base64.b64decode(b64_key).decode("utf-8")
            cred_dict = json.loads(decoded_json)
            firebase_admin.initialize_app(credentials.Certificate(cred_dict))
        except Exception as e:
            st.error(f"Erro Crítico de Banco de Dados: {e}")
            st.stop()
    return firestore.Client.from_service_account_info(
        json.loads(base64.b64decode(st.secrets["FIREBASE_BASE64"]).decode("utf-8"))
    )

db = get_db_connection()

# ------------------------------------------------------------------------------
# 3. DICIONÁRIOS DE IA E VARIÁVEIS DE NEGÓCIO (LINHAS 131-250)
# ------------------------------------------------------------------------------
PIX_MASTER = "11991853488"
WHATSAPP_ADMIN = "5511991853488"
TOKEN_ADMIN = "mumias"
TAXA_CLIQUE = 1
BONUS_INICIAL = 5
LAT_SE, LON_SE = -23.5505, -46.6333 # Centro Geográfico de SP

# Base de Conhecimento Expandida para o Motor NLP
IA_MAPPING = {
    "vazamento": "Encanador", "torneira": "Encanador", "pia": "Encanador", 
    "privada": "Encanador", "cano": "Encanador", "infiltração": "Encanador",
    "chuveiro": "Eletricista", "tomada": "Eletricista", "fio": "Eletricista",
    "curto": "Eletricista", "lâmpada": "Eletricista", "disjuntor": "Eletricista",
    "pintar": "Pintor", "grafiato": "Pintor", "verniz": "Pintor", "massa": "Pintor",
    "parede": "Pedreiro", "piso": "Pedreiro", "azulejo": "Pedreiro", "laje": "Pedreiro",
    "faxina": "Diarista", "passar": "Diarista", "limpeza": "Diarista", "organizar": "Diarista",
    "sofa": "Estofador", "cortina": "Lavanderia", "tapete": "Lavanderia",
    "unha": "Manicure", "gel": "Manicure", "fibra": "Manicure", "cutícula": "Manicure",
    "cabelo": "Cabeleireiro", "corte": "Cabeleireiro", "luzes": "Cabeleireiro",
    "carro": "Mecânico", "motor": "Mecânico", "freio": "Mecânico", "oleo": "Mecânico",
    "frete": "Transporte", "mudança": "Transporte", "carreto": "Transporte",
    "computador": "TI", "notebook": "TI", "formatar": "TI", "wi-fi": "TI",
    "inglês": "Professor", "matemática": "Professor", "aula": "Professor"
}

# ------------------------------------------------------------------------------
# 4. FUNÇÕES DE CÁLCULO E LÓGICA DE IA (LINHAS 251-380)
# ------------------------------------------------------------------------------

def haversine_sp(lat1, lon1, lat2, lon2):
    """Cálculo de distância KM entre dois pontos em SP"""
    radius = 6371 
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(radius * c, 1)

def engine_ia_busca(query_usuario, stream_dados):
    """Motor de IA: Tokenização + Lemmatização + Score de Relevância"""
    if not query_usuario: return []
    
    tokens = word_tokenize(query_usuario.lower())
    stop_p = set(stopwords.words('portuguese'))
    lemmatizer = WordNetLemmatizer()
    termos_limpos = [lemmatizer.lemmatize(t) for t in tokens if t not in stop_p]
    
    resultados_finais = []
    lista_profissionais = list(stream_dados)
    
    for doc in lista_profissionais:
        p = doc.to_dict()
        p['id_interno'] = doc.id
        score = 0
        
        # Atribuição de Pesos
        corpo_texto = f"{p.get('nome','')} {p.get('area','')} {p.get('localizacao','')} {p.get('descricao','')}".lower()
        
        for termo in termos_limpos:
            # Match exato em termos técnicos
            if termo in corpo_texto: score += 30
            # Match parcial (Fuzzy) para erros de digitação
            score += fuzz.partial_ratio(termo, corpo_texto) * 0.8
            
        # Funções de Ranking (Boost por saldo e nota)
        score += min(p.get('saldo', 0) * 2, 40)
        score += (p.get('rating', 5.0) * 10)
        
        if score > 50:
            resultados_finais.append({'dados': p, 'ranking_score': score})
            
    return sorted(resultados_finais, key=lambda x: x['ranking_score'], reverse=True)

def audit_database_integrity():
    """Função Admin para correção de campos nulos (Self-Healing)"""
    profs = db.collection("profissionais").stream()
    logs = []
    for p in profs:
        d = p.to_dict()
        u = {}
        if "saldo" not in d: u["saldo"] = BONUS_INICIAL
        if "aprovado" not in d: u["aprovado"] = False
        if "cliques" not in d: u["cliques"] = 0
        if "rating" not in d: u["rating"] = 5.0
        if u:
            db.collection("profissionais").document(p.id).update(u)
            logs.append(f"Corrigido: {p.id}")
    return logs

# ------------------------------------------------------------------------------
# 5. DESIGN SYSTEM E CSS (LINHAS 381-480)
# ------------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap');
    html, body, [class*="st-"] { font-family: 'Montserrat', sans-serif; }
    
    .main-title { color: #0047AB; font-weight: 900; font-size: 3rem; text-align: center; margin-bottom: 0; }
    .sub-title { color: #FF8C00; text-align: center; letter-spacing: 8px; font-weight: 700; margin-top: -10px; }
    
    .card-pro {
        background: white; border-radius: 20px; padding: 25px; margin-bottom: 20px;
        border-left: 10px solid #0047AB; box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    .card-pro:hover { transform: translateY(-5px); box-shadow: 0 15px 35px rgba(0,0,0,0.1); }
    
    .avatar-frame { width: 90px; height: 90px; border-radius: 50%; object-fit: cover; border: 4px solid #f8f9fa; }
    
    .badge-gold { background: linear-gradient(90deg, #FFD700, #FFA500); color: #000; padding: 5px 15px; border-radius: 50px; font-size: 11px; font-weight: 900; }
    .badge-verificado { background: #E3F2FD; color: #0047AB; padding: 5px 15px; border-radius: 50px; font-size: 11px; font-weight: 900; }
    
    .btn-whatsapp {
        background-color: #25D366; color: white !important; text-align: center;
        padding: 15px; border-radius: 12px; display: block; text-decoration: none;
        font-weight: 900; margin-top: 10px; font-size: 1.1rem;
    }
    
    .metric-box { background: #f0f2f6; padding: 15px; border-radius: 15px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 6. INTERFACE DE USUÁRIO - NAVEGAÇÃO (LINHAS 481-600+)
# ------------------------------------------------------------------------------
st.markdown('<h1 class="main-title">GERAL<span style="color:#FF8C00;">JÁ</span></h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">SÃO PAULO</p>', unsafe_allow_html=True)

MENU = st.tabs(["🔍 BUSCAR", "🚀 CATEGORIAS", "👤 SOU PROFISSIONAL", "📝 CADASTRO", "🔑 GESTÃO"])

# --- ABA 1: BUSCA INTELIGENTE ---
with MENU[0]:
    txt_busca = st.text_input("O que você precisa em São Paulo?", placeholder="Ex: Encanador para consertar pia na Zona Leste", key="input_ia")
    
    if txt_busca:
        base_query = db.collection("profissionais").where("aprovado", "==", True).stream()
        finalistas = engine_ia_busca(txt_busca, base_query)
        
        if not finalistas:
            st.warning("IA: Nenhum profissional verificado atende a estes critérios específicos.")
        else:
            for item in finalistas:
                p = item['dados']
                dist_km = haversine_sp(LAT_SE, LON_SE, p.get('lat', LAT_SE), p.get('lon', LON_SE))
                selo = '<span class="badge-gold">🏆 ELITE SP</span>' if p.get('saldo', 0) > 40 else '<span class="badge-verificado">✅ VERIFICADO</span>'
                
                st.markdown(f"""
                <div class="card-pro">
                    <div style="display: flex; align-items: center;">
                        <img src="{p.get('foto_url') or 'https://via.placeholder.com/150'}" class="avatar-frame">
                        <div style="margin-left: 20px; flex-grow: 1;">
                            {selo} <br>
                            <span style="font-size: 1.4rem; font-weight: 900; color: #333;">{p.get('nome','').upper()}</span><br>
                            <span style="color: #666; font-weight: 700;">{p.get('area','')} - {p.get('localizacao','')}</span><br>
                            <span style="color: #FF8C00;">{"★" * int(p.get('rating', 5))}</span> <small>({dist_km} km de distância)</small>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Regra de Negócio: Desconto de Saldo
                if p.get('saldo', 0) >= TAXA_CLIQUE:
                    if st.button(f"LIBERAR WHATSAPP DE {p.get('nome','').split()[0].upper()}", key=f"btn_{p['id_interno']}"):
                        db.collection("profissionais").document(p['id_interno']).update({
                            "saldo": firestore.Increment(-TAXA_CLIQUE),
                            "cliques": firestore.Increment(1)
                        })
                        # Voz da IA
                        tts = gTTS(text=f"Conectando você com {p.get('nome')}", lang='pt')
                        audio_b = io.BytesIO(); tts.write_to_fp(audio_b)
                        st.audio(audio_b, format="audio/mp3")
                        
                        st.markdown(f'<a href="https://wa.me/55{p.get("whatsapp")}?text=Vi seu perfil no GeralJá" class="btn-whatsapp">CHAMAR NO WHATSAPP</a>', unsafe_allow_html=True)
                else:
                    st.error("Este profissional atingiu o limite de contatos diários.")

# --- ABA 2: CATEGORIAS ---
with MENU[1]:
    st.subheader("Explore as Melhores Especialidades")
    cols = st.columns(4)
    cats = list(set(IA_MAPPING.values()))
    for i, c in

