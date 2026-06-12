# ==============================================================================
# GERALJÁ: CRIANDO SOLUÇÕES - MÓDULO 1: INFRAESTRUTURA
# ==============================================================================
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import math
import re
import time
import pandas as pd
from datetime import datetime 
import pytz
import unicodedata
import requests
import sys
import os
from PIL import Image
import io

# --- CONFIGURAÇÃO DE AMBIENTE E PERFORMANCE ---
st.set_page_config(
    page_title="GeralJá | Criando Soluções",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CONFIGURAÇÃO DE ALTO NÍVEL ---
class GeralJaEngine:
    def __init__(self):
        self.fuso = pytz.timezone('America/Sao_Paulo')
    
    def sanitizar(self, codigo_bruto):
        """Mata caracteres fantasmas e lixo de codificação instantaneamente"""
        if not codigo_bruto: return ""
        limpo = codigo_bruto.replace('\u00a0', ' ').replace('\xa0', ' ')
        return re.sub(r'[^\x20-\x7E\n\t\r]', '', limpo)

    def injetar_modulo(self, nome_arquivo, conteudo):
        """Instala novos códigos no servidor de forma independente"""
        conteudo_limpo = self.sanitizar(conteudo)
        try:
            with open(f"{nome_arquivo}.py", "w", encoding="utf-8") as f:
                f.write(conteudo_limpo)
            return True, f"✅ Módulo {nome_arquivo} instalado e saneado!"
        except Exception as e:
            return False, f"❌ Falha na instalação: {str(e)}"

# Inicializa o Motor Global
engine = GeralJaEngine()
fuso_br = engine.fuso

# --- BIBLIOTECAS NÍVEL 5.0 ---
from groq import Groq                 # Para a IA avançada
from fuzzywuzzy import process       # Para buscas com erros de digitação
from urllib.parse import quote       # Para links de WhatsApp seguros
import google.generativeai as genai  # IA Gemini
from google_auth_oauthlib.flow import Flow # Login Google

# --- TENTA IMPORTAR COMPONENTES JS (EVITA QUEBRA SE NÃO INSTALADO) ---
try:
    from streamlit_js_eval import streamlit_js_eval, get_geolocation
except ImportError:
    pass

# --- CONFIGURAÇÃO DE CHAVES (PUXANDO DO SECRETS) ---
try:
    FB_ID = st.secrets["FB_CLIENT_ID"]
    FB_SECRET = st.secrets["FB_CLIENT_SECRET"]
    FIREBASE_API_KEY = st.secrets["FIREBASE_API_KEY"]
    REDIRECT_URI = "https://geralja-zxiaj2ot56fuzgcz7xhcks.streamlit.app/"
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    client_groq = Groq(api_key=st.secrets["GROQ_API_KEY"])
    
except Exception as e:
    st.error(f"⚠️ Erro Crítico: Verifique o arquivo 'Secrets' no Streamlit. ({e})")
    st.stop()

# URLs de Suporte
HANDLER_URL = "https://geralja-5bb49.firebaseapp.com/__/auth/handler"

# ------------------------------------------------------------------------------
# 2. CONEXÃO COM O BANCO DE DADOS (FIREBASE)
# ------------------------------------------------------------------------------
@st.cache_resource
def conectar_banco_master():
    """Inicializa o Firebase apenas uma vez por sessão"""
    if not firebase_admin._apps:
        try:
            if "firebase" in st.secrets and "base64" in st.secrets["firebase"]:
                b64_key = st.secrets["firebase"]["base64"]
                decoded_json = base64.b64decode(b64_key).decode("utf-8")
                cred_dict = json.loads(decoded_json)
                cred = credentials.Certificate(cred_dict)
                return firebase_admin.initialize_app(cred)
            else:
                st.error("⚠️ Configuração 'firebase.base64' não encontrada no Secrets.")
                st.stop()
        except Exception as e:
            st.error(f"❌ FALHA NA INFRAESTRUTURA FIREBASE: {e}")
            st.stop()
    return firebase_admin.get_app()

app_engine = conectar_banco_master()
db = firestore.client()

if 'tema_claro' not in st.session_state:
    st.session_state.tema_claro = False

# Mantém os menus originais do Streamlit ocultos para visual limpo
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- LOGICA DE RECEPÇÃO DO GOOGLE ---
def get_google_flow():
    g_auth = st.secrets["google_auth"]
    client_config = {
        "web": {
            "client_id": g_auth["client_id"],
            "client_secret": g_auth["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [g_auth["redirect_uri"]]
        }
    }
    return Flow.from_client_config(
        client_config,
        scopes=["openid", "https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"],
        redirect_uri=g_auth["redirect_uri"]
    )

query_params = st.query_params
if "code" in query_params:
    try:
        flow = get_google_flow()
        flow.fetch_token(code=query_params["code"])
        session = flow.authorized_session()
        user_info = session.get('https://www.googleapis.com/userinfo').json()
        
        email_google = user_info.get("email")
        nome_google = user_info.get("name")
        foto_google = user_info.get("picture")

        st.query_params.clear()

        pro_ref = db.collection("profissionais").where("email", "==", email_google).limit(1).get()

        if pro_ref:
            dados = pro_ref[0].to_dict()
            st.session_state.auth = True
            st.session_state.user_id = pro_ref[0].id
            st.success(f"Logado com sucesso como {dados.get('nome')}!")
            time.sleep(1)
            st.rerun()
        else:
            st.session_state.pre_cadastro = {
                "email": email_google,
                "nome": nome_google,
                "foto": foto_google
            }
            st.toast(f"Olá {nome_google}! Complete seu cadastro profissional abaixo.")
            
    except Exception as e:
        st.error(f"Erro ao processar login do Google: {e}")

# --- TEMA DINÂMICO CONFIGURAÇÃO ---
if 'modo_noite' not in st.session_state:
    st.session_state.modo_noite = True 

c_t1, c_t2 = st.columns([2, 8])
with c_t1:
    st.session_state.modo_noite = st.toggle("🌙 Modo Noite", value=st.session_state.modo_noite)

# Bloco CSS Avançado (Injeta Design System Moderno de Rede Social)
estilo_dinamico = f"""
<style>
    @media (max-width: 640px) {{
        .main .block-container {{ padding: 1rem !important; }}
        h1 {{ font-size: 1.8rem !important; }}
    }}

    .stApp {{
        background-color: {"#0D1117" if st.session_state.modo_noite else "#F8FAFC"} !important;
        color: {"#FFFFFF" if st.session_state.modo_noite else "#1A1A1B"} !important;
    }}

    div[data-testid="stVerticalBlock"] > div[style*="background"] {{
        background-color: {"#161B22" if st.session_state.modo_noite else "#FFFFFF"} !important;
        border: 1px solid {"#30363D" if st.session_state.modo_noite else "#E2E8F0"} !important;
        border-radius: 18px !important;
    }}

    /* --- CSS DA VITRINE ESTILO REDE SOCIAL --- */
    .social-feed-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 24px;
        padding: 15px 0;
    }}
    
    .social-card {{
        background: {"#161B22" if st.session_state.modo_noite else "#FFFFFF"};
        border: 1px solid {"#30363D" if st.session_state.modo_noite else "#E2E8F0"};
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0 10px 25px rgba(0,0,0,{"0.3" if st.session_state.modo_noite else "0.05"});
        transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.3s ease;
        display: flex;
        flex-direction: column;
        height: 100%;
        position: relative;
    }}
    
    .social-card:hover {{
        transform: translateY(-6px);
        box-shadow: 0 16px 35px rgba(0,0,0,{"0.5" if st.session_state.modo_noite else "0.12"});
    }}
    
    .social-banner {{
        height: 85px;
        background: linear-gradient(135deg, #0047AB, #FF8C00);
        position: relative;
    }}
    
    .social-avatar-container {{
        position: absolute;
        bottom: -25px;
        left: 20px;
    }}
    
    .social-avatar {{
        width: 65px;
        height: 65px;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid {"#161B22" if st.session_state.modo_noite else "#FFFFFF"};
        background: #eee;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
    }}
    
    .social-badge-elite {{
        position: absolute;
        top: 15px;
        right: 15px;
        background: linear-gradient(135deg, #FFD700, #FFA500);
        color: #000000 !important;
        font-size: 10px;
        font-weight: 900;
        padding: 4px 10px;
        border-radius: 30px;
        text-transform: uppercase;
        box-shadow: 0 2px 8px rgba(255,215,0,0.4);
        letter-spacing: 0.5px;
    }}
    
    .social-card-content {{
        padding: 35px 20px 20px 20px;
        flex-grow: 1;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }}
    
    .social-pro-title {{
        font-size: 18px;
        font-weight: 800;
        margin: 0 0 4px 0;
        color: {"#FFFFFF" if st.session_state.modo_noite else "#0F172A"};
        letter-spacing: -0.5px;
    }}
    
    .social-pro-tag {{
        display: inline-block;
        font-size: 11px;
        font-weight: 700;
        color: #FF8C00;
        background: rgba(255, 140, 0, 0.12);
        padding: 2px 8px;
        border-radius: 6px;
        margin-bottom: 12px;
    }}
    
    .social-desc {{
        font-size: 13px;
        line-height: 1.5;
        color: {"#8B949E" if st.session_state.modo_noite else "#475569"};
        margin: 0 0 15px 0;
        height: 60px;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
    }}
    
    .social-metrics {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-top: 1px solid {"#30363D" if st.session_state.modo_noite else "#F1F5F9"};
        padding-top: 12px;
        margin-bottom: 15px;
        font-size: 12px;
    }}
    
    .social-dist {{
        color: #0047AB;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 4px;
    }}
    
    .social-stars {{
        color: #FFB800;
        font-weight: bold;
    }}
    
    .social-action-btn {{
        display: block;
        background: #25D366;
        color: white !important;
        text-align: center;
        padding: 12px;
        border-radius: 14px;
        text-decoration: none !important;
        font-weight: 800;
        font-size: 13px;
        transition: background 0.2s, transform 0.1s;
        box-shadow: 0 4px 12px rgba(37, 211, 102, 0.2);
    }}
    
    .social-action-btn:hover {{
        background: #20ba5a;
        transform: scale(1.02);
    }}
</style>
"""
st.markdown(estilo_dinamico, unsafe_allow_html=True)

# --- FUNÇÕES DE SUPORTE MASTER ---
def buscar_opcoes_dinamicas(documento, padrao):
    try:
        doc = db.collection("configuracoes").document(documento).get()
        if doc.exists:
            return doc.to_dict().get("lista", padrao)
        return padrao
    except:
        return padrao

def limpar_whatsapp(numero):
    num = re.sub(r'\D', '', str(numero))
    if not num.startswith('55') and len(num) >= 10:
        num = f"55{num}"
    return num

def normalizar(texto):
    if not texto: return ""
    return "".join(ch for ch in unicodedata.normalize('NFKD', texto) 
                   if unicodedata.category(ch) != 'Mn').lower()

def calcular_distancia_real(lat1, lon1, lat2, lon2):
    try:
        if None in [lat1, lon1, lat2, lon2]: return 999.0
        R = 6371 
        dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)
    except: return 999.0

def normalizar_para_ia(texto):
    if not texto: return ""
    return "".join(c for c in unicodedata.normalize('NFD', str(texto))
                   if unicodedata.category(c) != 'Mn').lower().strip()

def processar_ia_avancada(texto):
    if not texto: return "Vazio"
    t_clean = normalizar_para_ia(texto)
    
    for chave, categoria in CONCEITOS_EXPANDIDOS.items():
        if re.search(rf"\b{normalizar_para_ia(chave)}\b", t_clean):
            return category
    
    for cat in CATEGORIAS_OFICIAIS:
        if normalizar_para_ia(cat) in t_clean:
            return cat

    try:
        cache_ref = db.collection("cache_buscas").document(t_clean).get()
        if cache_ref.exists:
            return cache_ref.to_dict().get("categoria")

        prompt = f"O usuário buscou: '{texto}'. Categorias: {CATEGORIAS_OFICIAIS}. Responda apenas o NOME DA CATEGORIA."
        
        res = client_groq.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
            temperature=0.1
        )
        cat_ia = res.choices[0].message.content.strip()
        db.collection("cache_buscas").document(t_clean).set({"categoria": cat_ia})
        return cat_ia
    except:
        return "NAO_ENCONTRADO"

def converter_img_b64(file):
    if file is None: return ""
    try: return base64.b64encode(file.read()).decode()
    except: return ""

def finalizar_e_alinhar_layout():
    st.write("---")
    fechamento_estilo = f"""
        <style>
            .main .block-container {{ padding_bottom: 5rem !important; }}
            .footer-clean {{
                text-align: center;
                padding: 20px;
                opacity: 0.7;
                font-size: 0.8rem;
                width: 100%;
                color: gray;
            }}
        </style>
        <div class="footer-clean">
            <p>🎯 <b>GeralJá</b> - Sistema de Inteligência Local</p>
            <p>Conectando quem precisa com quem sabe fazer.</p>
            <p>v3.0 | © 2026 Todos os direitos reservados</p>
        </div>
    """
    st.markdown(fechamento_estilo, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 3. POLÍTICAS E CONSTANTES
# ------------------------------------------------------------------------------
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ADMIN = "mumias"
LAT_REF = -23.5505
LON_REF = -46.6333

CATEGORIAS_OFICIAIS = [
    "Encanador", "Eletricista", "Pintor", "Pedreiro", "Gesseiro", "Telhadista", 
    "Serralheiro", "Vidraceiro", "Marceneiro", "Marmoraria", "Calhas e Rufos", 
    "Dedetização", "Desentupidora", "Piscineiro", "Jardineiro", "Limpeza de Estofados",
    "Mecânico", "Borracheiro", "Guincho 24h", "Estética Automotiva", "Lava Jato", 
    "Auto Elétrica", "Funilaria e Pintura", "Som e Alarme", "Moto Peças", "Auto Peças",
    "Loja de Roupas", "Calçados", "Loja de Variedades", "Relojoaria", "Joalheria", 
    "Ótica", "Armarinho/Aviamentos", "Papelaria", "Floricultura", "Bazar", 
    "Material de Construção", "Tintas", "Madeireira", "Móveis", "Eletrodomésticos",
    "Pizzaria", "Lanchonete", "Restaurante", "Confeitaria", "Padaria", "Açaí", 
    "Sorveteria", "Adega", "Doceria", "Hortifruti", "Açougue", "Pastelaria", 
    "Churrascaria", "Hamburgueria", "Comida Japonesa", "Cafeteria",
    "Farmácia", "Barbearia/Salão", "Manicure/Pedicure", "Estética Facial", 
    "Tatuagem/Piercing", "Fitness", "Academia", "Fisioterapia", "Odontologia", 
    "Clínica Médica", "Psicologia", "Nutricionista", "TI", "Assistência Técnica", 
    "Celulares", "Informática", "Refrigeração", "Técnico de Fogão", "Técnico de Lavadora", 
    "Eletrônicos", "Chaveiro", "Montador", "Freteiro", "Carreto", "Motoboy/Entregas",
    "Pet Shop", "Veterinário", "Banho e Tosa", "Adestrador", "Agropecuária",
    "Aulas Particulares", "Escola Infantil", "Reforço Escolar", "Idiomas", 
    "Advocacia", "Contabilidade", "Imobiliária", "Seguros", "Ajudante Geral", 
    "Diarista", "Cuidador de Idosos", "Babá", "Outro (Personalizado)"
]

CONCEITOS_EXPANDIDOS = {
    "pizza": "Pizzaria", "pizzaria": "Pizzaria", "fome": "Pizzaria", "massa": "Pizzaria",
    "lanche": "Lanchonete", "hamburguer": "Lanchonete", "burger": "Lanchonete", "salgado": "Lanchonete",
    "comida": "Restaurante", "almoco": "Restaurante", "marmita": "Restaurante", "jantar": "Restaurante",
    "doce": "Confeitaria", "bolo": "Confeitaria", "pao": "Padaria", "padaria": "Padaria",
    "acai": "Açaí", "sorvete": "Sorveteria", "cerveja": "Adega", "bebida": "Adega",
    "roupa": "Loja de Roupas", "moda": "Loja de Roupas", "sapato": "Calçados", "tenis": "Calçados",
    "presente": "Loja de Variedades", "relogio": "Relojoaria", "joia": "Joalheria",
    "remedio": "Farmácia", "farmacia": "Farmácia", "cabelo": "Barbearia/Salão", "unha": "Barbearia/Salão",
    "celular": "Assistência Técnica", "iphone": "Assistência Técnica", "computador": "TI", "pc": "TI",
    "geladeira": "Refrigeração", "ar condicionado": "Refrigeração", "fogao": "Técnico de Fogão",
    "tv": "Eletrônicos", "pet": "Pet Shop", "racao": "Pet Shop", "cachorro": "Pet Shop",
    "vazamento": "Encanador", "cano": "Encanador", "curto": "Eletricista", "luz": "Eletricista",
    "pintar": "Pintor", "parede": "Pintor", "reforma": "Pedreiro", "piso": "Pedreiro",
    "telhado": "Telhadista", "solda": "Serralheiro", "vidro": "Vidraceiro", "chave": "Chaveiro",
    "carro": "Mecânico", "motor": "Mecânico", "pneu": "Borracheiro", "guincho": "Guincho 24h",
    "frete": "Freteiro", "mudanca": "Freteiro", "faxina": "Diarista", "limpeza": "Diarista",
    "jardim": "Jardineiro", "piscina": "Piscineiro"
}

# ------------------------------------------------------------------------------
# 5. DESIGN SYSTEM BASE
# ------------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .header-container { background: white; padding: 40px 20px; border-radius: 0 0 50px 50px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.05); border-bottom: 8px solid #FF8C00; margin-bottom: 25px; }
    .logo-azul { color: #0047AB; font-weight: 900; font-size: 50px; letter-spacing: -2px; }
    .logo-laranja { color: #FF8C00; font-weight: 900; font-size: 50px; letter-spacing: -2px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-container"><span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span><br><small style="color:#64748B; font-weight:700;">BRASIL ELITE EDITION</small></div>', unsafe_allow_html=True)

lista_abas = ["🔍 BUSCAR", "🚀 CADASTRAR", "👤 MEU PERFIL", "👑 ADMIN", "⭐ FEEDBACK"]
comando = st.sidebar.text_input("Comando Secreto", type="password")
if comando == "abracadabra":
    lista_abas.append("📊 FINANCEIRO")

menu_abas = st.tabs(lista_abas)
ZAP_VENDAS = "5511980168513"

def criar_link_zap(numero, msg):
    return f"https://api.whatsapp.com/send?phone={numero}&text={quote(msg)}"

# ==============================================================================
# --- ABA 0: PORTAL GRAJAÚ TEM (VITRINE ESTILO REDE SOCIAL CORRIGIDA) ---
# ==============================================================================
with menu_abas[0]:
    st.markdown("### 🏙️ O que você precisa no Grajaú?")
    
    with st.expander("📍 Sua Localização (GPS)", expanded=False):
        loc = get_geolocation(component_key="geo_high_prec") 
        if loc and 'coords' in loc:
            minha_lat = loc['coords']['latitude']
            minha_lon = loc['coords']['longitude']
            precisao = loc['coords'].get('accuracy', 0)
            st.success(f"GPS Ativo (Precisão: {precisao:.0f}m)")
        else:
            minha_lat, minha_lon = LAT_REF, LON_REF
            st.warning("Usando localização padrão (Centro). Ative o GPS para maior precisão.")

    c1, c2 = st.columns([3, 1])
    termo_busca = c1.text_input("Ex: 'Cano estourado' ou 'Pizzaria'", key="main_search_v4")
    raio_km = c2.select_slider("Raio (KM)", options=[1, 3, 5, 10, 20, 50, 500], value=5)

    # --- ENGENHARIA DE CARREGAMENTO AUTOMÁTICO DA VITRINE ---
    with st.spinner("Carregando vitrine de profissionais..."):
        doc_cat = db.collection("configuracoes").document("categorias").get()
        lista_oficial = doc_cat.to_dict().get("lista", CATEGORIAS_OFICIAIS) if doc_cat.exists else CATEGORIAS_OFICIAIS
        
        profs_fluxo = db.collection("profissionais").where("aprovado", "==", True).stream()
        lista_ranking = []
        
        cat_ia = None
        if termo_busca:
            for c in lista_oficial:
                if c.lower() in termo_busca.lower():
                    cat_ia = c
                    break
            if not cat_ia:
                cat_ia = processar_ia_avancada(termo_busca)

        for p_doc in profs_fluxo:
            p = p_doc.to_dict()
            p['id'] = p_doc.id
            dist = calcular_distancia_real(minha_lat, minha_lon, p.get('lat', LAT_REF), p.get('lon', LON_REF))
            
            if dist <= raio_km:
                p['dist'] = dist
                p['score_elite'] = (1000 if p.get('verificado') and p.get('saldo', 0) > 0 else 0)
                
                if termo_busca:
                    t_norm = normalizar(termo_busca)
                    n_norm = normalizar(p.get('nome', ''))
                    a_norm = normalizar(p.get('area', ''))
                    d_norm = normalizar(p.get('descricao', ''))
                    
                    if (t_norm in n_norm) or (t_norm in a_norm) or (t_norm in d_norm) or (cat_ia and p.get('area') == cat_ia):
                        lista_ranking.append(p)
                else:
                    lista_ranking.append(p)

        lista_ranking.sort(key=lambda x: (-x['score_elite'], x['dist']))

    if not lista_ranking:
        st.warning("Nenhum profissional encontrado nesta área ou distância no momento.")
    else:
        html_cards = '<div class="social-feed-grid">'
        
        for p in lista_ranking:
            f_perfil = p.get('foto_url', '')
            if f_perfil and not str(f_perfil).startswith("http"):
                f_perfil = f"data:image/jpeg;base64,{f_perfil}"
            elif not f_perfil:
                f_perfil = "https://cdn-icons-png.flaticon.com/512/149/149071.png"
            
            is_elite = p['score_elite'] > 0
            badge_html = '<span class="social-badge-elite">🏆 ELITE</span>' if is_elite else ''
            zap_link = f"https://wa.me/{limpar_whatsapp(p.get('whatsapp',''))}?text=Vi+seu+perfil+no+GeralJa"
            
            html_cards += f"""
            <div class="social-card">
                <div class="social-banner">
                    {badge_html}
                    <div class="social-avatar-container">
                        <img src="{f_perfil}" class="social-avatar">
                    </div>
                </div>
                <div class="social-card-content">
                    <div>
                        <h4 class="social-pro-title">{str(p.get('nome','')).upper()}</h4>
                        <span class="social-pro-tag">{p.get('area', 'Profissional')}</span>
                        <p class="social-desc">{str(p.get('descricao',''))}</p>
                    </div>
                    <div>
                        <div class="social-metrics">
                            <span class="social-dist">📍 <b>{p['dist']:.1f} km</b> de você</span>
                            <span class="social-stars">⭐⭐⭐⭐⭐ {p.get('rating', '5.0')}</span>
                        </div>
                        <a href="{zap_link}" target="_blank" class="social-action-btn">💬 CONTACTAR PARCEIRO</a>
                    </div>
                </div>
            </div>
            """
            
        html_cards += '</div>'
        st.markdown(html_cards, unsafe_allow_html=True)

# ==============================================================================
# --- SEÇÃO DE NOTÍCIAS HÍBRIDA (CORRIGIDO PARA MODO ESCURO) ---
# ==============================================================================
st.markdown("---")
st.subheader("📰 Plantão Grajaú Tem")

import feedparser

IMG_PADRAO = "https://images.unsplash.com/photo-1504711432869-0df30d7eaf4d?w=500&q=80"

try:
    noticias_fb = list(db.collection("noticias").order_by("data", direction="DESCENDING").limit(2).stream())
except:
    noticias_fb = []

def buscar_noticias_rss(busca="Grajaú São Paulo"):
    try:
        url_rss = f"https://news.google.com/rss/search?q={quote(busca)}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        feed = feedparser.parse(url_rss)
        return feed.entries[:4]
    except:
        return []

noticias_auto = buscar_noticias_rss()

fila_noticias = []
for n in noticias_fb:
    dados = n.to_dict()
    fila_noticias.append({
        "titulo": dados.get('titulo', 'Sem título'),
        "link": dados.get('link_original', '#'),
        "img": dados.get('imagem_url', IMG_PADRAO),
        "fonte": "⭐ DESTAQUE LOCAL",
        "cor": "#FFD700"
    })

for n in noticias_auto:
    if len(fila_noticias) >= 2: break
    fila_noticias.append({
        "titulo": n.title.split(' - ')[0],
        "link": n.link,
        "img": IMG_PADRAO,
        "fonte": f"📡 {n.source.get('title', 'Google News')}",
        "cor": "#0047AB"
    })

if fila_noticias:
    cols = st.columns(2)
    # Variáveis de cor dinâmicas para o card de notícias respeitar o Modo Escuro
    bg_card_noticia = "#161B22" if st.session_state.modo_noite else "#FFFFFF"
    txt_card_noticia = "#FFFFFF" if st.session_state.modo_noite else "#1A1A1A"
    border_card_noticia = "#30363D" if st.session_state.modo_noite else "#E2E8F0"

    for i, noticia in enumerate(fila_noticias):
        with cols[i]:
            st.markdown(f"""
                <a href="{noticia['link']}" target="_blank" style="text-decoration:none; color:inherit;">
                    <div style="background:{bg_card_noticia}; border: 1px solid {border_card_noticia}; border-radius:15px; margin-bottom:20px; box-shadow:0 4px 12px rgba(0,0,0,0.08); overflow:hidden; border-bottom: 5px solid {noticia['cor']}; height: 320px;">
                        <div style="height:150px; background-image: url('{noticia['img']}'); background-size:cover; background-position:center;"></div>
                        <div style="padding:15px;">
                            <span style="background:{noticia['cor']}22; color:{noticia['cor']}; font-size:10px; font-weight:bold; padding:3px 10px; border-radius:50px;">
                                {noticia['fonte']}
                            </span>
                            <h4 style="margin:12px 0 8px 0; color:{txt_card_noticia}; font-size:15px; line-height:1.3; height: 60px; overflow: hidden;">
                                {noticia['titulo'][:85]}{'...' if len(noticia['titulo']) > 85 else ''}
                            </h4>
                            <div style="color:{noticia['cor']}; font-weight:bold; font-size:12px; margin-top:10px;">Ler matéria completa →</div>
                        </div>
                    </div>
                </a>
            """, unsafe_allow_html=True)
else:
    st.info("Aguardando novas atualizações da região.")

# ==============================================================================
# ABA 1: 🚀 CADASTRAR & EDITAR (COMPLETADO E CORRIGIDO)
# ==============================================================================
with menu_abas[1]:
    st.markdown("### 🚀 Cadastro ou Edição de Profissional")

    try:
        doc_cat = db.collection("configuracoes").document("categorias").get()
        if doc_cat.exists:
            CATEGORIAS_OFICIAIS = doc_cat.to_dict().get("lista", ["Geral"])
        else:
            CATEGORIAS_OFICIAIS = ["Pedreiro", "Locutor", "Eletricista", "Mecânico"]
    except:
        CATEGORIAS_OFICIAIS = ["Pedreiro", "Locutor", "Eletricista", "Mecânico"]

    dados_google = st.session_state.get("pre_cadastro", {})
    email_inicial = dados_google.get("email", "")
    nome_inicial = dados_google.get("nome", "")
    foto_google = dados_google.get("foto", "")

    st.markdown("##### Entre rápido com:")
    col_soc1, col_soc2 = st.columns(2)
    
    g_auth = st.secrets.get("google_auth", {})
    g_id = g_auth.get("client_id")
    g_uri = g_auth.get("redirect_uri", "https://geralja-zxiaj2ot56fuzgcz7xhcks.streamlit.app/")

    with col_soc1:
        if g_id:
            url_google = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={g_id}&response_type=code&scope=openid%20profile%20email&redirect_uri={g_uri}"
            st.markdown(f'''
                <a href="{url_google}" target="_self" style="text-decoration:none;">
                    <div style="display:flex; align-items:center; justify-content:center; border:1px solid #dadce0; border-radius:8px; padding:8px; background:white;">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/5/53/Google_%22G%22_Logo.svg" width="18px" style="margin-right:10px;">
                        <span style="color:#3c4043; font-weight:bold; font-size:14px;">Google</span>
                    </div>
                </a>
            ''', unsafe_allow_html=True)
        else:
            st.caption("⚠️ Google Auth não configurado")

    with col_soc2:
        fb_id = st.secrets.get("FB_CLIENT_ID", "")
        st.markdown(f'''
            <a href="https://www.facebook.com/v18.0/dialog/oauth?client_id={fb_id}&redirect_uri={g_uri}&scope=public_profile,email" target="_self" style="text-decoration:none;">
                <div style="display:flex; align-items:center; justify-content:center; border-radius:8px; padding:8px; background:#1877F2;">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/2021_Facebook_icon.svg" width="18px" style="margin-right:10px;">
                    <span style="color:white; font-weight:bold; font-size:14px;">Facebook</span>
                </div>
            </a>
        ''', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    BONUS_WELCOME = 20 

    with st.form("form_profissional", clear_on_submit=False):
        st.caption("DICA: Se você já tem cadastro, use o mesmo WhatsApp para editar seus dados.")
        
        col1, col2 = st.columns(2)
        nome_input = col1.text_input("Nome do Profissional ou Loja", value=nome_inicial)
        zap_input = col2.text_input("WhatsApp (DDD + Número sem espaços)")
        
        email_input = st.text_input("E-mail (Para login via Google)", value=email_inicial)
        
        col3, col4 = st.columns(2)
        cat_input = col3.selectbox("Selecione sua Especialidade Principal", CATEGORIAS_OFICIAIS)
        senha_input = col4.text_input("Sua Senha de Acesso", type="password")
        
        desc_input = st.text_area("Descrição Completa (Serviços, Horários, Diferenciais)")
        tipo_input = st.radio("Tipo", ["👨‍🔧 Profissional Autônomo", "🏢 Comércio/Loja"], horizontal=True)
        
        foto_upload = st.file_uploader("Atualizar Foto de Perfil ou Logo", type=['png', 'jpg', 'jpeg'])
        
        btn_acao = st.form_submit_button("✅ FINALIZAR: SALVAR OU ATUALIZAR", use_container_width=True)

    if btn_acao:
        if not nome_input or not zap_input or not senha_input:
            st.warning("⚠️ Nome, WhatsApp e Senha são obrigatórios!")
        else:
            zap_limpo = limpar_whatsapp(zap_input)
            try:
                with st.spinner("Sincronizando com o ecossistema GeralJá..."):
                    # Processamento de imagem se houver upload
                    foto_b64 = ""
                    if foto_upload is not None:
                        foto_b64 = converter_img_b64(foto_upload)
                    elif foto_google:
                        foto_b64 = foto_google

                    # Verifica se o documento já existe
                    doc_ref = db.collection("profissionais").document(zap_limpo)
                    doc_existente = doc_ref.get()

                    dados_salvar = {
                        "nome": nome_input,
                        "whatsapp": zap_limpo,
                        "email": email_input,
                        "area": cat_input,
                        "senha": senha_input, # Idealmente aplicar hash por segurança no futuro
                        "descricao": desc_input,
                        "tipo": tipo_input,
                        "lat": LAT_REF, # Fallback padrão
                        "lon": LON_REF, # Fallback padrão
                        "aprovado": True, # Definição inicial automática
                        "verificado": False,
                        "rating": "5.0",
                        "timestamp_atualizacao": datetime.now(fuso_br)
                    }

                    if foto_b64:
                        dados_salvar["foto_url"] = foto_b64

                    if doc_existente.exists:
                        # Modo Edição: valida a senha enviada
                        dados_atuais = doc_existente.to_dict()
                        if dados_atuais.get("senha") == senha_input:
                            doc_ref.update(dados_salvar)
                            st.success("🔄 Seus dados profissionais foram atualizados com sucesso!")
                        else:
                            st.error("❌ Senha incorreta! Digite a senha cadastrada anteriormente para este número para autorizar mudanças.")
                    else:
                        # Modo Novo Cadastro: ganha o bônus inicial
                        dados_salvar["saldo"] = BONUS_WELCOME
                        dados_salvar["aprovado"] = True
                        doc_ref.set(dados_salvar)
                        st.success(f"🎉 Cadastro realizado com sucesso! Você ganhou R$ {BONUS_WELCOME} de bônus de boas-vindas!")
                    
                    time.sleep(1.5)
                    st.rerun()

            except Exception as e:
                st.error(f"❌ Erro ao salvar dados no ecossistema: {e}")

# Renderiza fechamento e rodapé padrão do app
finalizar_e_alinhar_layout()
