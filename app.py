# ==============================================================================
# GERALJÁ: CRIANDO SOLUÇÕES - MÓDULO INTEGRADO & TURBINADO
# VERSÃO 6.0 ELITE SOCIAL - Grajaú Tem + Vitrine de Ofertas + Rádio Ao Vivo
# ==============================================================================
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import math
import re
import time
import io
import pandas as pd
from datetime import datetime 
import pytz
import unicodedata
import requests
import feedparser
import urllib.parse
from urllib.parse import quote
from PIL import Image

# --- BIBLIOTECAS NÍVEL 6.0 ---
try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    from fuzzywuzzy import process
except ImportError:
    process = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from google_auth_oauthlib.flow import Flow
except ImportError:
    Flow = None

# --- TENTA IMPORTAR COMPONENTES JS COM FALLBACK SEGURO ---
streamlit_js_eval = None
get_geolocation = None
try:
    from streamlit_js_eval import streamlit_js_eval, get_geolocation
except ImportError:
    pass
except Exception:
    pass

# --- CONFIGURAÇÃO DE PÁGINA (DEVE SER O PRIMEIRO COMANDO STREAMLIT) ---
st.set_page_config(
    page_title="GeralJá | Criando Soluções — Grajaú Tem",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS RESPONSIVO E MODO DIA/NOITE ADAPTÁVEL ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .main .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
    #MainMenu, footer, header { visibility: hidden; }
    
    /* HEADER COMPACTO E IMPACTANTE */
    .header-container { 
        background: linear-gradient(135deg, #0047AB 0%, #FF8C00 100%); 
        padding: 22px 15px; 
        border-radius: 0 0 25px 25px; 
        text-align: center; 
        box-shadow: 0 4px 20px rgba(0,0,0,0.15); 
        margin-bottom: 15px;
        margin-top: -1rem;
    }
    .logo-azul { color: #FFFFFF; font-weight: 900; font-size: 38px; letter-spacing: -1px; text-shadow: 1px 1px 3px rgba(0,0,0,0.3); }
    .logo-laranja { color: #FFD700; font-weight: 900; font-size: 38px; letter-spacing: -1px; text-shadow: 1px 1px 3px rgba(0,0,0,0.3); }
    .sub-logo { color: #FFFFFF; font-weight: 600; font-size: 13px; opacity: 0.95; letter-spacing: 0.5px; }
    
    /* PLAYER RÁDIO GRAJAÚ TEM */
    .radio-player-bar {
        background: linear-gradient(90deg, #1e293b, #0f172a);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 12px 20px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 10px;
        color: white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    /* BANNER VITRINE DE OFERTAS */
    .vitrine-banner {
        background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
        color: white;
        padding: 15px;
        border-radius: 16px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(220, 38, 38, 0.25);
    }
    
    /* CARDS RESPONSIVOS E PRODUTOS */
    .produto-card { background: #f8f9fa; border-radius: 12px; padding: 10px; margin: 5px 0; border: 1px solid #e9ecef; color: #333; }
    .stApp { transition: all 0.3s ease; }
    
    /* ESTILO REDE SOCIAL PARA PERFIL */
    .social-profile-header {
        background: linear-gradient(to bottom, #0047AB, #002D6B);
        height: 130px;
        border-radius: 20px 20px 0 0;
        position: relative;
        margin-bottom: 60px;
    }
    .social-profile-avatar {
        width: 110px;
        height: 110px;
        border-radius: 50%;
        border: 5px solid white;
        position: absolute;
        bottom: -55px;
        left: 20px;
        object-fit: cover;
        background: #eee;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    .social-profile-info {
        padding: 0 20px;
        margin-top: -10px;
    }
    .social-name { font-size: 24px; font-weight: 900; margin: 0; }
    .social-tag { font-size: 14px; color: #666; margin-bottom: 10px; }
    .social-bio { font-size: 15px; margin-bottom: 15px; line-height: 1.4; }
    .social-stats { display: flex; gap: 20px; margin-bottom: 20px; border-top: 1px solid #eee; border-bottom: 1px solid #eee; padding: 10px 0; }
    .stat-item { text-align: center; }
    .stat-value { font-weight: 900; font-size: 18px; display: block; }
    .stat-label { font-size: 12px; color: #888; text-transform: uppercase; }
    
    /* MODO NOITE ADAPTATION */
    .dark-mode .social-profile-header { background: linear-gradient(to bottom, #1e3a8a, #0f172a); }
    .dark-mode .social-profile-avatar { border-color: #0D1117; }
    .dark-mode .social-tag { color: #aaa; }
    .dark-mode .social-stats { border-color: #333; }
    .dark-mode .produto-card { background: #1f2937; border-color: #374151; color: #fff; }

    /* MOBILE FIRST */
    @media (max-width: 640px) {
        .header-container { padding: 15px 10px; margin-bottom: 10px; }
        .logo-azul, .logo-laranja { font-size: 30px; }
        h1 { font-size: 1.5rem !important; }
        .stButton button { width: 100%; }
        .radio-player-bar { flex-direction: column; text-align: center; }
    }
</style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO DE ESTADOS SEGUROS ---
if 'modo_noite' not in st.session_state:
    if streamlit_js_eval:
        try:
            prefers_dark = streamlit_js_eval(js_expressions="window.matchMedia('(prefers-color-scheme: dark)').matches", key="theme_detect")
            st.session_state.modo_noite = bool(prefers_dark)
        except Exception:
            st.session_state.modo_noite = False
    else:
        st.session_state.modo_noite = False

for key, default in {
    'tema_claro': False,
    'auth': False,
    'admin_logado': False,
    'minha_lat': -23.5505,
    'minha_lon': -46.6333,
    'security_check': False,
    'js_disponivel': True,
    'pre_cadastro': None,
    'user_id': None,
    'busca_rapida': ""
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ==============================================================================
# BLOCO A: CONFIGURAÇÃO E INICIALIZAÇÃO
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. MOTOR GLOBAL
# ------------------------------------------------------------------------------
class GeralJaEngine:
    def __init__(self):
        self.fuso = pytz.timezone('America/Sao_Paulo')
    
    def sanitizar(self, codigo_bruto):
        """Mata caracteres fantasmas mantendo acentos PT-BR"""
        if not codigo_bruto: return ""
        limpo = codigo_bruto.replace('\u00a0', ' ').replace('\xa0', ' ')
        return ''.join(ch for ch in limpo if ch in '\n\t\r' or ord(ch) >= 32)

    def injetar_modulo(self, nome_arquivo, conteudo):
        conteudo_limpo = self.sanitizar(conteudo)
        try:
            with open(f"{nome_arquivo}.py", "w", encoding="utf-8") as f:
                f.write(conteudo_limpo)
            return True, f"✅ Módulo {nome_arquivo} instalado e saneado!"
        except Exception as e:
            return False, f"❌ Falha na instalação: {str(e)}"

engine = GeralJaEngine()
fuso_br = engine.fuso

# ------------------------------------------------------------------------------
# 2. CONFIGURAÇÃO DE CHAVES E SERVIÇOS AI
# ------------------------------------------------------------------------------
client_groq = None
try:
    FB_ID = st.secrets.get("FB_CLIENT_ID", "")
    FB_SECRET = st.secrets.get("FB_CLIENT_SECRET", "")
    FIREBASE_API_KEY = st.secrets.get("FIREBASE_API_KEY", "")
    REDIRECT_URI = st.secrets.get("google_auth", {}).get("redirect_uri", "https://geralja-zxiaj2ot56fuzgcz7xhcks.streamlit.app/")
    
    if "GEMINI_API_KEY" in st.secrets and genai:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    if "GROQ_API_KEY" in st.secrets and Groq:
        client_groq = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error(f"⚠️ Erro ao carregar Secrets: {e}")
    st.stop()

HANDLER_URL = "https://geralja-5bb49.firebaseapp.com/__/auth/handler"

# ------------------------------------------------------------------------------
# 3. CONEXÃO FIREBASE
# ------------------------------------------------------------------------------
@st.cache_resource
def conectar_banco_master():
    if not firebase_admin._apps:
        try:
            if "firebase" in st.secrets and "base64" in st.secrets["firebase"]:
                b64_key = st.secrets["firebase"]["base64"]
                decoded_json = base64.b64decode(b64_key).decode("utf-8")
                cred_dict = json.loads(decoded_json)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
            else:
                st.error("⚠️ Configuração 'firebase.base64' não encontrada.")
                st.stop()
        except Exception as e:
            st.error(f"❌ FALHA FIREBASE: {e}")
            st.stop()
    return firebase_admin.get_app()

app_engine = conectar_banco_master()
db = firestore.client()

# ------------------------------------------------------------------------------
# 4. FUNÇÕES AUXILIARES
# ------------------------------------------------------------------------------
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
        if None in [lat1, lon1, lat2, lon2]: 
            return 999.0
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return round(R * c, 1)
    except Exception:
        return 999.0

def buscar_opcoes_dinamicas(documento, padrao):
    try:
        doc = db.collection("configuracoes").document(documento).get()
        if doc.exists:
            dados = doc.to_dict()
            return dados.get("lista", padrao)
        return padrao
    except Exception:
        return padrao

def safe_image_src(valor):
    """Evita duplo prefixo data:image e garante fallback"""
    if not valor:
        return "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    v = str(valor)
    if v.startswith("http") or v.startswith("data:image"):
        return v
    return f"data:image/jpeg;base64,{v}"

def otimizar_imagem_admin(imagem_upload, size=(800, 800)):
    try:
        img = Image.open(imagem_upload)
        if img.mode in ("RGBA", "P"):
            img = img.convert('RGB')
        img.thumbnail(size)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=80)
        return base64.b64encode(buffer.getvalue()).decode()
    except Exception:
        return None

def normalizar_para_ia(texto):
    if not texto: return ""
    return "".join(c for c in unicodedata.normalize('NFD', str(texto))
                   if unicodedata.category(c) != 'Mn').lower().strip()

def processar_ia_avancada(texto):
    """Classificador Inteligente Multimodelos (Groq Llama-3 + Gemini 1.5 Flash Fallback)"""
    if not texto: return "Vazio"
    t_clean = normalizar_para_ia(texto)
    
    # 1. Verificação por Dicionário Rápido de Conceitos
    for chave, categoria in CONCEITOS_EXPANDIDOS.items():
        if re.search(rf"\b{re.escape(normalizar_para_ia(chave))}\b", t_clean):
            return categoria
    
    # 2. Verificação de Correspondência Direta com Categorias
    for cat in CATEGORIAS_OFICIAIS:
        if normalizar_para_ia(cat) in t_clean:
            return cat

    try:
        # 3. Consulta em Cache do Firestore
        cache_ref = db.collection("cache_buscas").document(t_clean).get()
        if cache_ref.exists:
            return cache_ref.to_dict().get("categoria")

        cat_ia = None

        # 4. Primeira Opção: Groq (Llama-3)
        if client_groq:
            try:
                prompt = f"O usuário buscou: '{texto}'. As categorias permitidas são: {CATEGORIAS_OFICIAIS}. Responda APENAS O NOME DA CATEGORIA exata da lista. Se nada se encaixar, responda Outro (Personalizado)."
                res = client_groq.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama3-8b-8192",
                    temperature=0.1
                )
                cat_ia = res.choices[0].message.content.strip()
            except Exception:
                cat_ia = None

        # 5. Segunda Opção (Fallback): Google Gemini AI
        if not cat_ia and genai:
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"O usuário buscou no app de serviços: '{texto}'. Categorias: {CATEGORIAS_OFICIAIS}. Retorne apenas a categoria idêntica da lista."
                response = model.generate_content(prompt)
                cat_ia = response.text.strip()
            except Exception:
                cat_ia = None

        if cat_ia and cat_ia in CATEGORIAS_OFICIAIS:
            db.collection("cache_buscas").document(t_clean).set({"categoria": cat_ia})
            return cat_ia

        return "Outro (Personalizado)"
    except Exception:
        return "NAO_ENCONTRADO"

def criar_link_zap(numero, msg):
    return f"https://api.whatsapp.com/send?phone={numero}&text={urllib.parse.quote(msg)}"

def registrar_clique_parceiro(doc_id):
    """Contabiliza clique no perfil do parceiro"""
    try:
        ref = db.collection("profissionais").document(doc_id)
        ref.update({"cliques": firestore.Increment(1)})
    except Exception:
        pass

# ==============================================================================
# BLOCO B: CONSTANTES E AUTENTICAÇÃO OAUTH GOOGLE/FB
# ==============================================================================
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
ZAP_VENDAS_1 = "5511980168513"
ZAP_VENDAS_2 = "5511991853488"
CHAVE_ADMIN = "mumias"
LAT_REF = -23.5505
LON_REF = -46.6333
BONUS_WELCOME = 20

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
    "doce": "Doceria", "acai": "Açaí", "sorvete": "Sorveteria", "cerveja": "Adega", "bebida": "Adega",
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

# --- LOGIN GOOGLE FLOW ---
def get_google_flow():
    if not Flow: return None
    g_auth = st.secrets.get("google_auth", {})
    client_id = g_auth.get("client_id")
    client_secret = g_auth.get("client_secret")
    redirect_uri = g_auth.get("redirect_uri", REDIRECT_URI)
    if not client_id or not client_secret:
        return None
    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri]
        }
    }
    return Flow.from_client_config(
        client_config,
        scopes=["openid", "https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"],
        redirect_uri=redirect_uri
    )

query_params = st.query_params
if "code" in query_params:
    try:
        flow = get_google_flow()
        if flow:
            code_val = query_params["code"]
            if isinstance(code_val, list): code_val = code_val[0]
            flow.fetch_token(code=code_val)
            session = flow.authorized_session()
            user_info = session.get('https://www.googleapis.com/oauth2/v2/userinfo').json()
            
            email_google = user_info.get("email")
            nome_google = user_info.get("name")
            foto_google = user_info.get("picture")

            pro_ref = db.collection("profissionais").where("email", "==", email_google).limit(1).get()
            if pro_ref:
                dados = pro_ref[0].to_dict()
                st.session_state.auth = True
                st.session_state.user_id = pro_ref[0].id 
                st.success(f"Logado como {dados.get('nome')}!")
                time.sleep(1)
                st.rerun()
            else:
                st.session_state.pre_cadastro = {
                    "email": email_google,
                    "nome": nome_google,
                    "foto": foto_google
                }
                st.toast(f"Olá {nome_google}! Complete seu cadastro.")
    except Exception as e:
        st.error(f"Erro login Google: {e}")

# Checagem de login via parâmetro UID (Facebook/Redes Sociais)
if "uid" in query_params and not st.session_state.auth:
    fb_uid = query_params["uid"]
    if isinstance(fb_uid, list): fb_uid = fb_uid[0]
    user_query = db.collection("profissionais").where("fb_uid", "==", fb_uid).limit(1).get()
    if user_query:
        doc = user_query[0]
        st.session_state.auth = True
        st.session_state.user_id = doc.id
        st.success("✅ Autenticação realizada via Rede Social!")
        time.sleep(0.5)
        st.rerun()

# Layout topo
c_t1, c_t2 = st.columns([2, 8])
with c_t1:
    st.session_state.modo_noite = st.toggle("🌙 Modo Noite", value=st.session_state.modo_noite)

estilo_dinamico = f"""
<style>
    .stApp {{
        background-color: {"#0D1117" if st.session_state.modo_noite else "#FFFAFA"} !important;
        color: {"#FFFFFF" if st.session_state.modo_noite else "#1A1A1B"} !important;
    }}
    {'body.dark-mode' if st.session_state.modo_noite else ''}
</style>
"""
st.markdown(estilo_dinamico, unsafe_allow_html=True)

# Header Banner Oficial
st.markdown("""
<div class="header-container">
    <span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span><br>
    <span class="sub-logo">A MAIOR VITRINE DA REGIÃO DO GRAJAÚ | 20M+ VIEWS/MÊS</span>
</div>
""", unsafe_allow_html=True)

# Player de Rádio Web Ao Vivo da Rádio Grajaú Tem
st.markdown("""
<div class="radio-player-bar">
    <div style="display: flex; align-items: center; gap: 10px;">
        <span style="font-size: 24px;">📻</span>
        <div>
            <strong style="font-size: 15px;">Rádio Grajaú Tem — Ao Vivo</strong><br>
            <span style="font-size: 11px; opacity: 0.8;">Música, Notícias Locais e Prestação de Serviço 24h</span>
        </div>
    </div>
    <audio controls style="height: 38px; outline: none;">
        <source src="https://stream.zeno.fm/f322442407" type="audio/mpeg">
        Seu navegador não suporta reprodução de áudio.
    </audio>
</div>
""", unsafe_allow_html=True)

# Configuração de Abas Principal
lista_abas = ["🔍 BUSCAR", "📢 ANUNCIE CONOSCO", "🚀 CADASTRAR", "👤 MEU PERFIL", "⭐ FEEDBACK"]

# ADMIN ESCONDIDO - Liberado via comando secreto no menu lateral
with st.sidebar:
    st.markdown("### 🔐 Acesso Administrativo")
    comando = st.text_input("Código de Acesso", type="password", key="admin_key", placeholder="Digite o código")
    if comando in ["abracadabra", "geralja_master", "mumias"]:
        if "👑 ADMIN" not in lista_abas: lista_abas.append("👑 ADMIN")
    if comando in ["financeiro2026", "geralja_master"]:
        if "📊 FINANCEIRO" not in lista_abas: lista_abas.append("📊 FINANCEIRO")

menu_abas = st.tabs(lista_abas)

# MAPEAMENTO SEGURO DE ABAS
abas_dict = {}
for i, nome in enumerate(lista_abas):
    if "BUSCAR" in nome: abas_dict['buscar'] = i
    elif "ANUNCIE" in nome: abas_dict['anuncie'] = i
    elif "CADASTRAR" in nome: abas_dict['cadastrar'] = i
    elif "MEU PERFIL" in nome: abas_dict['perfil'] = i
    elif "ADMIN" in nome: abas_dict['admin'] = i
    elif "FEEDBACK" in nome: abas_dict['feedback'] = i
    elif "FINANCEIRO" in nome: abas_dict['financeiro'] = i

# ==============================================================================
# ABA 1: 🔍 BUSCAR
# ==============================================================================
if 'buscar' in abas_dict:
    with menu_abas[abas_dict['buscar']]:
        st.markdown("### 🏙️ O que você procura no Grajaú agora?")
        
        # Atalhos Rápidos
        st.caption("⚡ Atalhos rápidos de busca:")
        col_a1, col_a2, col_a3, col_a4, col_a5, col_a6 = st.columns(6)
        if col_a1.button("🍕 Pizzaria", use_container_width=True): st.session_state.busca_rapida = "Pizzaria"
        if col_a2.button("🔧 Encanador", use_container_width=True): st.session_state.busca_rapida = "Encanador"
        if col_a3.button("⚡ Eletricista", use_container_width=True): st.session_state.busca_rapida = "Eletricista"
        if col_a4.button("💈 Barbearia", use_container_width=True): st.session_state.busca_rapida = "Barbearia/Salão"
        if col_a5.button("🍔 Lanche", use_container_width=True): st.session_state.busca_rapida = "Lanchonete"
        if col_a6.button("📱 Celulares", use_container_width=True): st.session_state.busca_rapida = "Assistência Técnica"

        with st.expander("📍 Ajustar Localização GPS", expanded=False):
            if get_geolocation:
                try:
                    loc = get_geolocation(component_key="geo_high_prec") 
                    if loc and 'coords' in loc:
                        st.session_state.minha_lat = loc['coords']['latitude']
                        st.session_state.minha_lon = loc['coords']['longitude']
                        precisao = loc['coords'].get('accuracy', 0)
                        st.session_state.js_disponivel = True
                        st.success(f"GPS Sinal OK (Precisão: {precisao:.0f}m)")
                    else:
                        st.session_state.js_disponivel = False
                        st.warning("GPS indisponível no momento. Usando centro de referência do Grajaú.")
                except Exception:
                    st.session_state.js_disponivel = False
                    st.warning("Usando localização padrão do bairro.")
            else:
                st.session_state.js_disponivel = False
                st.info("Informe seu serviço desejado abaixo.")

        minha_lat = st.session_state.minha_lat
        minha_lon = st.session_state.minha_lon

        val_busca_def = st.session_state.get('busca_rapida', "")
        
        c1, c2 = st.columns([3, 1])
        termo_busca = c1.text_input("Digite o que precisa (Ex: 'Vazamento de água', 'Pastelaria')", value=val_busca_def, key="main_search_v6")
        raio_km = c2.select_slider("Raio max (KM)", options=[1, 3, 5, 10, 20, 50, 500], value=5)

        if termo_busca:
            st.session_state.busca_rapida = ""
            with st.status("🔍 Identificando os melhores profissionais...", expanded=False) as status:
                doc_cat = db.collection("configuracoes").document("categorias").get()
                lista_oficial = doc_cat.to_dict().get("lista", CATEGORIAS_OFICIAIS) if doc_cat.exists else CATEGORIAS_OFICIAIS
                
                cat_ia = next((c for c in lista_oficial if c.lower() in termo_busca.lower()), None)
                
                if not cat_ia:
                    st.write("🤖 Processando classificação via Inteligência Artificial...")
                    cat_ia = processar_ia_avancada(termo_busca)
                
                profs = db.collection("profissionais").where("area", "==", cat_ia).where("aprovado", "==", True).stream()
                
                lista_ranking = []
                for p_doc in profs:
                    p = p_doc.to_dict()
                    p['id'] = p_doc.id
                    dist = calcular_distancia_real(minha_lat, minha_lon, p.get('lat', LAT_REF), p.get('lon', LON_REF))
                    
                    if dist <= raio_km:
                        p['dist'] = dist
                        p['score_elite'] = (1000 if p.get('verificado') and p.get('saldo', 0) > 0 else 0)
                        lista_ranking.append(p)

                lista_ranking.sort(key=lambda x: (x['dist'], -x['score_elite']))
                status.update(label=f"Resultados para categoria: **{cat_ia}**", state="complete")

            if not lista_ranking:
                st.warning(f"Nenhum parceiro de '{cat_ia}' localizado no raio de {raio_km}km.")
                st.info("💡 Se você presta este serviço no Grajaú, cadastre-se na aba **🚀 CADASTRAR** e apareça para os clientes!")
            else:
                for p in lista_ranking:
                    f_perfil = safe_image_src(p.get('foto_url', ''))
                    is_elite = p['score_elite'] > 0
                    cor_borda = "#FFD700" if is_elite else "#0047AB"
                    zap_num = limpar_whatsapp(p.get('whatsapp',''))
                    zap_link = criar_link_zap(zap_num, f"Olá {p.get('nome','')}! Encontrei seu contato no aplicativo GeralJá e gostaria de informações.")

                    st.markdown(f"""
                    <div style="background:white; border-radius:18px; border-left:8px solid {cor_borda}; padding:15px; margin-bottom:15px; box-shadow:0 4px 12px rgba(0,0,0,0.08); color:black;">
                        <div style="font-size:11px; color:#0047AB; font-weight:bold; margin-bottom:8px; display:flex; justify-content:space-between;">
                            <span>📍 Distância: {p['dist']:.1f} km</span>
                            <span>{"🏆 PARCEIRO ELITE VITRINE" if is_elite else "✅ VERIFICADO"}</span>
                        </div>
                        <div style="display:flex; align-items:center; gap:14px;">
                            <img src="{f_perfil}" style="width:60px; height:60px; border-radius:50%; object-fit:cover; border:2px solid #ddd;">
                            <div>
                                <h4 style="margin:0; color:#1e3a8a; font-size:18px;">{str(p.get('nome','')).upper()}</h4>
                                <p style="margin:3px 0 0 0; color:#555; font-size:13px; line-height:1.3;">{str(p.get('descricao',''))[:130]}</p>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    produtos = p.get('produtos', [])
                    produtos_ativos = [pr for pr in produtos if pr.get('ativo', True)][:3]
                    if produtos_ativos and p.get('tipo_conta') == 'comerciante':
                        st.markdown("<div style='margin-top:12px; color:#222; font-size:13px;'><b>🛍️ Ofertas em Destaque no Perfil:</b></div>", unsafe_allow_html=True)
                        cols = st.columns(len(produtos_ativos))
                        for idx, prod in enumerate(produtos_ativos):
                            with cols[idx]:
                                st.image(safe_image_src(prod.get('foto_b64', '')), use_container_width=True)
                                st.markdown(f"<div class='produto-card'><b>{prod.get('nome','')}</b><br>R$ {prod.get('preco',0):.2f}</div>", unsafe_allow_html=True)
                                link_prod = criar_link_zap(zap_num, f"Olá! Vi no GeralJá e tenho interesse em adquirir: {prod.get('nome','')}")
                                if st.link_button("Pedir no Zap", link_prod, use_container_width=True):
                                    registrar_clique_parceiro(p['id'])
                    
                    if st.link_button(f"💬 CHAMAR {str(p.get('nome','')).upper()} NO WHATSAPP", zap_link, use_container_width=True):
                        registrar_clique_parceiro(p['id'])
                    
                    st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📰 Plantão de Notícias Locais — Grajaú Tem")
        
        @st.cache_data(ttl=900)
        def buscar_noticias_rss(busca="Grajaú São Paulo"):
            try:
                url_rss = f"https://news.google.com/rss/search?q={urllib.parse.quote(busca)}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
                feed = feedparser.parse(url_rss)
                return feed.entries[:4]
            except Exception:
                return []
        
        noticias = buscar_noticias_rss()
        if noticias:
            cols = st.columns(len(noticias))
            for i, n in enumerate(noticias):
                with cols[i]:
                    img = "https://images.unsplash.com/photo-1504711432869-0df30d7eaf4d?w=400"
                    if hasattr(n, 'media_content') and n.media_content:
                        img = n.media_content[0]['url']
                    fonte = n.source.get('title', 'Grajaú Tem') if hasattr(n, 'source') else 'Notícias Locais'
                    tempo_leitura = max(1, len(n.title) // 40)

                    st.markdown(f"""
                    <a href="{n.link}" target="_blank" style="text-decoration:none; color:inherit;">
                        <div style="border:1px solid #E2E8F0; border-radius:12px; overflow:hidden; height:310px; background:white; transition: transform 0.2s; color:#1A202C;">
                            <img src="{img}" style="width:100%; height:120px; object-fit:cover;">
                            <div style="padding:10px;">
                                <span style="background:#EDF2F7; padding:2px 6px; border-radius:4px; font-size:10px; font-weight:bold; color:#4A5568;">⏱️ {tempo_leitura} min lida</span>
                                <p style="font-size:12px; font-weight:700; margin-top:6px; line-height:1.3; color:#1A202C;">{n.title[:75]}...</p>
                                <p style="font-size:10px; color:#718096; margin-top:8px;">📍 {fonte}</p>
                            </div>
                        </div>
                    </a>
                    """, unsafe_allow_html=True)
        else:
            st.info("📢 Trânsito e serviços fluindo normalmente na região do Grajaú.")

# ==============================================================================
# ABA NOVA: 📢 ANUNCIE CONOSCO (VITRINE DE OFERTAS GRAJAÚ TEM)
# ==============================================================================
if 'anuncie' in abas_dict:
    with menu_abas[abas_dict['anuncie']]:
        st.markdown("## 🔴 Vitrine de Ofertas & Pacotes Comerciais")
        st.write("Conecte sua empresa a **mais de 20 milhões de visualizações/mês** no Grajaú e Região!")
        
        st.info("🚀 **Maior Vitrine da Região:** 539 mil seguidores engajados. Alcance clientes novos todos os dias!")

        c_v1, c_v2 = st.columns(2)

        with c_v1:
            st.markdown("""
            <div style="background:#FFF5F5; border:2px solid #E53E3E; padding:18px; border-radius:15px; margin-bottom:15px; color:#111;">
                <h3 style="color:#C53030; margin-top:0;">🔴 Vitrine de Ofertas (Giro Diário)</h3>
                <p style="font-size:14px;">Seu anúncio no carrossel diário de notícias, trânsito e clima visualizado por toda a comunidade.</p>
                <hr>
                <p><b>Unitário:</b> 1 Dia = <b>R$ 100</b></p>
                <p><b>Mensal:</b> 8 Inserções/Mês = <b>R$ 600</b> <span style="background:#FEB2B2; padding:2px 6px; border-radius:4px; font-size:12px; font-weight:bold;">Melhor Custo-Benefício 💰</span></p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div style="background:#F0FDF4; border:2px solid #16A34A; padding:18px; border-radius:15px; color:#111;">
                <h3 style="color:#15803D; margin-top:0;">📻 Rádio Grajaú Tem</h3>
                <p style="font-size:14px;">Anúncios em áudio na programação 24h da rádio com maior alcance local.</p>
                <hr>
                <p><b>Mensal:</b> R$ 300 / mês</p>
            </div>
            """, unsafe_allow_html=True)

        with c_v2:
            st.markdown("""
            <div style="background:#F8FAFC; border:2px solid #0047AB; padding:18px; border-radius:15px; color:#111;">
                <h3 style="color:#0047AB; margin-top:0;">📱 Postagens Avulsas & Reels</h3>
                <p style="font-size:14px;">Publicações exclusivas no Instagram e Facebook da maior vitrine comercial.</p>
                <hr>
                <p>🥉 <b>Pacote Bronze:</b> 1 Post = <b>R$ 150</b></p>
                <p>🥈 <b>Pacote Prata:</b> 3 Posts = <b>R$ 400</b></p>
                <p>🥇 <b>Pacote Ouro:</b> 10 Posts = <b>R$ 700</b></p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 🔥 Pronto para vender mais essa semana?")
        
        c_zap1, c_zap2 = st.columns(2)
        link_zap1 = criar_link_zap(ZAP_VENDAS_1, "Olá! Quero anunciar minha marca na Vitrine de Ofertas do Grajaú Tem!")
        link_zap2 = criar_link_zap(ZAP_VENDAS_2, "Olá! Tenho interesse nos pacotes comerciais do Grajaú Tem!")

        with c_zap1:
            st.link_button("👉 FECHAR VIA WHATSAPP (11) 98016-8513", link_zap1, use_container_width=True)
        with c_zap2:
            st.link_button("👉 FECHAR VIA WHATSAPP (11) 99185-3488", link_zap2, use_container_width=True)

# ==============================================================================
# ABA 2: 🚀 CADASTRAR OU EDITAR
# ==============================================================================
if 'cadastrar' in abas_dict:
    with menu_abas[abas_dict['cadastrar']]:
        st.header("🚀 Cadastre-se ou Atualize seu Perfil Comercial")
        st.write("Esteja presente onde os moradores do Grajaú procuram produtos e serviços diariamente!")

        dados_google = st.session_state.get("pre_cadastro", {})
        email_inicial = dados_google.get("email", "")
        nome_inicial = dados_google.get("nome", "")
        foto_google = dados_google.get("foto", "")

        st.markdown("##### Entre rápido com suas redes sociais:")
        col_soc1, col_soc2 = st.columns(2)

        g_auth = st.secrets.get("google_auth", {})
        g_id = g_auth.get("client_id")
        g_uri = g_auth.get("redirect_uri", REDIRECT_URI)

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
                st.caption("⚠️ OAuth Google não configurado")

        with col_soc2:
            fb_id_soc = st.secrets.get("FB_CLIENT_ID", "")
            if fb_id_soc:
                st.markdown(f'''
                    <a href="https://www.facebook.com/v18.0/dialog/oauth?client_id={fb_id_soc}&redirect_uri={g_uri}&scope=public_profile,email" target="_self" style="text-decoration:none;">
                        <div style="display:flex; align-items:center; justify-content:center; border-radius:8px; padding:8px; background:#1877F2;">
                            <img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/2021_Facebook_icon.svg" width="18px" style="margin-right:10px;">
                            <span style="color:white; font-weight:bold; font-size:14px;">Facebook</span>
                        </div>
                    </a>
                ''', unsafe_allow_html=True)
            else:
                st.caption("⚠️ OAuth Facebook não configurado")

        st.markdown("<br>", unsafe_allow_html=True)

        doc_cat = db.collection("configuracoes").document("categorias").get()
        lista_cats = doc_cat.to_dict().get("lista", CATEGORIAS_OFICIAIS) if doc_cat.exists else CATEGORIAS_OFICIAIS

        with st.form("form_profissional_completo"):
            st.caption("💡 Se você já possui cadastro, informe seu WhatsApp para atualizar suas informações.")

            col1, col2 = st.columns(2)
            nome_input = col1.text_input("Nome Profissional ou da Empresa", value=nome_inicial)
            zap_input = col2.text_input("WhatsApp (com DDD)", help="Ex: 11980168513")

            email_input = st.text_input("E-mail Principial", value=email_inicial)

            col3, col4 = st.columns(2)
            cat_input = col3.selectbox("Especialidade Principal", lista_cats)
            senha_input = col4.text_input("Crie sua Senha de Acesso", type="password")

            desc_input = st.text_area("Descrição do seu Trabalho ou Produtos (máx. 400 caracteres)", max_chars=400)
            tipo_input = st.radio("Tipo de Cadastro", ["👨‍🔧 Prestador de Serviços", "🏢 Comércio / Loja / Restaurante"], horizontal=True)

            foto_upload = st.file_uploader("Foto de Perfil ou Logomarca", type=['png', 'jpg', 'jpeg'])
            termos_check = st.checkbox("Concordo com os Termos de Uso e Política de Privacidade do GeralJá", value=True)

            # Indicador de Preenchimento
            campos_p = sum([bool(nome_input), bool(zap_input), bool(email_input), bool(desc_input), bool(senha_input)])
            percentual = (campos_p / 5) * 100
            st.progress(percentual / 100)
            st.caption(f"Completaço do perfil: **{int(percentual)}%**")

            btn_salvar = st.form_submit_button("✅ SALVAR / CONCLUIR MEU CADASTRO", use_container_width=True)

        if btn_salvar:
            zap_limpo = limpar_whatsapp(zap_input)
            
            if not termos_check:
                st.error("⚠️ Você precisa aceitar os termos de uso.")
            elif not nome_input or not zap_limpo or not senha_input or not desc_input:
                st.warning("⚠️ Nome, WhatsApp, Senha e Descrição são dados obrigatórios!")
            else:
                try:
                    with st.spinner("Salvando cadastro no GeralJá..."):
                        doc_ref = db.collection("profissionais").document(zap_limpo)
                        perfil_antigo = doc_ref.get()
                        dados_antigos = perfil_antigo.to_dict() if perfil_antigo.exists else {}

                        foto_b64 = dados_antigos.get("foto_url", "")

                        if foto_upload is not None:
                            foto_b64 = safe_image_src(otimizar_imagem_admin(foto_upload))
                        elif not foto_b64 and foto_google:
                            foto_b64 = foto_google
                        elif not foto_b64:
                            foto_b64 = "https://cdn-icons-png.flaticon.com/512/149/149071.png"

                        saldo_final = dados_antigos.get("saldo", BONUS_WELCOME)
                        cliques_atuais = dados_antigos.get("cliques", 0)
                        tipo_conta_salvar = "comerciante" if "Comércio" in tipo_input else "prestador"

                        dados_pro = {
                            "nome": nome_input,
                            "whatsapp": zap_limpo,
                            "email": email_input,
                            "area": cat_input,
                            "senha": senha_input,
                            "descricao": desc_input,
                            "tipo": tipo_input,
                            "tipo_conta": dados_antigos.get("tipo_conta", tipo_conta_salvar),
                            "produtos": dados_antigos.get("produtos", []),
                            "foto_url": foto_b64,
                            "saldo": saldo_final,
                            "data_cadastro": dados_antigos.get("data_cadastro", datetime.now(fuso_br).strftime("%d/%m/%Y")),
                            "aprovado": True,
                            "cliques": cliques_atuais,
                            "rating": dados_antigos.get("rating", 5),
                            "lat": st.session_state.get('minha_lat', LAT_REF),
                            "lon": st.session_state.get('minha_lon', LON_REF)
                        }

                        doc_ref.set(dados_pro)

                        st.session_state.auth = True
                        st.session_state.user_id = zap_limpo
                        st.session_state.pre_cadastro = None

                        st.balloons()
                        if perfil_antigo.exists:
                            st.success(f"✅ Perfil de {nome_input} atualizado com sucesso!")
                        else:
                            st.success(f"🎊 Bem-vindo(a)! Você ganhou {BONUS_WELCOME} GeralCoins de bônus inicial!")
                        time.sleep(1.5)
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Erro ao salvar cadastro: {e}")

# ==============================================================================
# ABA 3: 👤 MEU PERFIL / PAINEL DO PARCEIRO
# ==============================================================================
if 'perfil' in abas_dict:
    with menu_abas[abas_dict['perfil']]:
        if not st.session_state.auth:
            st.subheader("🚀 Painel do Parceiro GeralJá")
            
            fb_id = st.secrets.get("FB_CLIENT_ID", "")
            g_uri = st.secrets.get("google_auth", {}).get("redirect_uri", REDIRECT_URI)
            if fb_id:
                url_direta_fb = f"https://www.facebook.com/v18.0/dialog/oauth?client_id={fb_id}&redirect_uri={g_uri}&scope=public_profile,email"
                st.markdown(f'''
                    <a href="{url_direta_fb}" target="_top" style="text-decoration:none;">
                        <div style="background:#1877F2;color:white;padding:12px;border-radius:8px;text-align:center;font-weight:bold;display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow: 0px 4px 6px rgba(0,0,0,0.1);">
                            <img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/2021_Facebook_icon.svg" width="20px" style="margin-right:10px;">
                            ENTRAR COM FACEBOOK
                        </div>
                    </a>
                ''', unsafe_allow_html=True)

            st.markdown("<p style='text-align:center; margin-top:15px; color:#666;'>— ou entre com WhatsApp e Senha —</p>", unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            l_zap = col1.text_input("WhatsApp Cadastrado", key="login_zap_geralja_v10", placeholder="Ex: 11980168513")
            l_pw = col2.text_input("Senha", type="password", key="login_pw_geralja_v10")

            if st.button("ENTRAR NO PERFIL", key="btn_entrar_geralja_v10", use_container_width=True):
                try:
                    zap_busca = limpar_whatsapp(l_zap)
                    u = db.collection("profissionais").document(zap_busca).get()
                    if u.exists:
                        dados_user = u.to_dict()
                        if str(dados_user.get('senha')) == str(l_pw):
                            st.session_state.auth = True
                            st.session_state.user_id = u.id
                            st.success("Acesso liberado!")
                            st.rerun()
                        else: 
                            st.error("❌ Senha incorreta.")
                    else: 
                        st.error("❌ WhatsApp não encontrado.")
                except Exception as e: 
                    st.error(f"Erro ao acessar banco: {e}")
        else:
            user_id = st.session_state.user_id
            user_doc = db.collection("profissionais").document(user_id).get()
            
            if user_doc.exists:
                user_data = user_doc.to_dict()
                
                # HEADER SOCIAL
                foto_perfil = safe_image_src(user_data.get('foto_url', ''))
                modo_noite_class = "dark-mode" if st.session_state.modo_noite else ""
                
                st.markdown(f"""
                <div class="{modo_noite_class}">
                    <div class="social-profile-header">
                        <img src="{foto_perfil}" class="social-profile-avatar">
                    </div>
                    <div class="social-profile-info">
                        <h1 class="social-name">{user_data.get('nome', 'Usuário')} {'✅' if user_data.get('verificado') or user_data.get('aprovado') else ''}</h1>
                        <p class="social-tag">@{normalizar(user_data.get('nome', 'user')).replace(' ', '')} • {user_data.get('area', 'Profissional')}</p>
                        <p class="social-bio">{user_data.get('descricao', 'Sem descrição cadastrada.')}</p>
                        
                        <div class="social-stats">
                            <div class="stat-item">
                                <span class="stat-value">{user_data.get('cliques', 0)}</span>
                                <span class="stat-label">Contatos Recebidos</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-value">🪙 {user_data.get('saldo', 0)}</span>
                                <span class="stat-label">GeralCoins</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-value">{'🟢 ONLINE' if user_data.get('aprovado') else '🟡 PENDENTE'}</span>
                                <span class="stat-label">Status</span>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # ABAS INTERNAS
                tab_vitrine, tab_config, tab_ajuda = st.tabs(["🛍️ MINHA VITRINE COMERCIAL", "⚙️ EDITAR DADOS", "❓ AJUDA E RECARGA"])
                
                with tab_vitrine:
                    tipo_conta = user_data.get('tipo_conta', 'prestador')
                    if tipo_conta != 'comerciante':
                        st.info("💡 Ative o modo Comerciante para adicionar produtos e montar sua vitrine virtual.")
                        if st.button("ATIVAR MODO COMERCIANTE", use_container_width=True):
                            db.collection("profissionais").document(user_id).update({"tipo_conta": "comerciante"})
                            st.success("Modo Comerciante ativado!")
                            time.sleep(1)
                            st.rerun()
                    else:
                        produtos = user_data.get('produtos', [])
                        limite_max = 10
                        st.markdown(f"**Produtos cadastrados:** `{len(produtos)} / {limite_max}`")

                        if len(produtos) >= limite_max:
                            st.warning("⚠️ Limite máximo de 10 produtos atingido.")
                        else:
                            with st.expander("➕ PUBLICAR PRODUTO NA VITRINE", expanded=False):
                                with st.form("novo_produto_social", clear_on_submit=True):
                                    p_nome = st.text_input("Nome do Produto / Oferta")
                                    c1, c2 = st.columns(2)
                                    p_preco = c1.number_input("Preço (R$)", min_value=0.0, format="%.2f")
                                    p_foto = c2.file_uploader("Foto do Produto", type=['jpg', 'jpeg', 'png'])
                                    p_desc = st.text_area("Descrição rápida", max_chars=150)
                                    p_destaque = st.checkbox("Destacar produto no topo")
                                    
                                    if st.form_submit_button("PUBLICAR NA VITRINE", use_container_width=True):
                                        if p_nome and p_preco > 0 and p_foto:
                                            foto_b64 = otimizar_imagem_admin(p_foto, size=(400, 400))
                                            if foto_b64:
                                                novo_prod = {
                                                    "nome": p_nome,
                                                    "preco": float(p_preco),
                                                    "desc": p_desc,
                                                    "foto_b64": foto_b64,
                                                    "ativo": True,
                                                    "destaque": p_destaque,
                                                    "criado_em": datetime.now(fuso_br).isoformat()
                                                }
                                                produtos.append(novo_prod)
                                                db.collection("profissionais").document(user_id).update({"produtos": produtos})
                                                st.success("Produto adicionado com sucesso!")
                                                time.sleep(1)
                                                st.rerun()
                                        else:
                                            st.warning("Informe o nome, preço e insira uma foto.")

                        st.markdown("---")
                        if produtos:
                            st.markdown("#### Produtos Cadastrados")
                            for idx, prod in enumerate(produtos):
                                c_img, c_txt, c_btn = st.columns([1, 3, 1])
                                with c_img:
                                    st.image(safe_image_src(prod.get('foto_b64')), width=70)
                                with c_txt:
                                    st.markdown(f"**{prod.get('nome')}** — `R$ {prod.get('preco', 0):.2f}`")
                                    st.caption(prod.get('desc', ''))
                                with c_btn:
                                    if st.button("🗑️ Deletar", key=f"del_prod_soc_{idx}"):
                                        produtos.pop(idx)
                                        db.collection("profissionais").document(user_id).update({"produtos": produtos})
                                        st.rerun()

                with tab_config:
                    st.markdown("#### Configurações de Perfil")
                    with st.form("edit_perfil_social"):
                        n_nome = st.text_input("Nome", value=user_data.get('nome', ''))
                        
                        doc_cat = db.collection("configuracoes").document("categorias").get()
                        cats_atuais = doc_cat.to_dict().get("lista", CATEGORIAS_OFICIAIS) if doc_cat.exists else CATEGORIAS_OFICIAIS
                        idx_area = cats_atuais.index(user_data.get('area')) if user_data.get('area') in cats_atuais else 0
                        
                        n_area = st.selectbox("Área de Atuação", cats_atuais, index=idx_area)
                        n_zap = st.text_input("WhatsApp", value=user_data.get('whatsapp', ''))
                        n_senha = st.text_input("Senha", type="password", value=user_data.get('senha', ''))
                        n_desc = st.text_area("Apresentação", value=user_data.get('descricao', ''))
                        n_foto = st.file_uploader("Trocar Foto de Perfil", type=['jpg', 'png', 'jpeg'])
                        
                        if st.form_submit_button("SALVAR DADOS", use_container_width=True):
                            upd = {
                                "nome": n_nome, 
                                "area": n_area, 
                                "whatsapp": limpar_whatsapp(n_zap), 
                                "senha": n_senha,
                                "descricao": n_desc
                            }
                            if n_foto:
                                img_b64 = otimizar_imagem_admin(n_foto)
                                if img_b64: upd["foto_url"] = img_b64
                            db.collection("profissionais").document(user_id).update(upd)
                            st.success("Perfil atualizado!")
                            time.sleep(1)
                            st.rerun()
                    
                    st.divider()
                    if st.button("🚪 DESCONECTAR DA CONTA", use_container_width=True, type="secondary"):
                        st.session_state.auth = False
                        st.session_state.user_id = None
                        st.rerun()

                with tab_ajuda:
                    st.markdown("#### Suporte e GeralCoins")
                    st.info("💡 Mantenha seu saldo de moedas positivo para ganhar destaque nas buscas!")
                    st.link_button("💬 RECARREGAR SALDO VIA WHATSAPP", criar_link_zap(ZAP_ADMIN, f"Olá, sou {user_data.get('nome')} e quero recarregar meu saldo de GeralCoins."))

# ==============================================================================
# ABA 4: ⭐ FEEDBACK
# ==============================================================================
if 'feedback' in abas_dict:
    with menu_abas[abas_dict['feedback']]:
        st.header("⭐ Avalie o Aplicativo GeralJá")
        st.write("Sua opinião nos ajuda a evoluir a plataforma no Grajaú!")
        
        with st.form("form_feedback"):
            nome_fb = st.text_input("Seu Nome (Opcional)")
            nota = st.select_slider("Nota para o App", options=[1, 2, 3, 4, 5], value=5)
            comentario = st.text_area("O que você mais gostou ou o que podemos melhorar?")
            
            if st.form_submit_button("ENVIAR AVALIAÇÃO", use_container_width=True):
                if comentario:
                    db.collection("feedbacks").add({
                        "nome": nome_fb or "Anônimo",
                        "nota": nota,
                        "comentario": comentario,
                        "data": datetime.now(fuso_br)
                    })
                    st.success("🎉 Obrigado pelo seu feedback!")
                else:
                    st.warning("Escreva um breve comentário antes de enviar.")

# ==============================================================================
# ABA 5: 👑 ADMIN (PAINEL ADMINISTRATIVO DIRETORIA)
# ==============================================================================
if 'admin' in abas_dict:
    with menu_abas[abas_dict['admin']]:
        if not st.session_state.admin_logado:
            st.markdown("### 🔐 Central Administrativa GeralJá & Grajaú Tem")
            with st.form("login_adm"):
                u = st.text_input("Usuário")
                p = st.text_input("Senha", type="password")
                if st.form_submit_button("AUTENTICAR DIRETORIA", use_container_width=True):
                    if u == st.secrets.get("ADMIN_USER", "geralja") and p == st.secrets.get("ADMIN_PASS", "Bps36ocara"):
                        st.session_state.admin_logado = True
                        st.success("Acesso administrativo ativado!")
                        st.rerun()
                    else: 
                        st.error("Credenciais inválidas.")
        else:
            st.markdown("## 👑 Painel de Controle GeralJá & Grajaú Tem")
            if st.button("🚪 Encerrar Sessão Admin", type="primary"):
                st.session_state.admin_logado = False
                st.rerun()

            tab_profissionais, tab_noticias, tab_loja, tab_vendas, tab_categorias = st.tabs([
                "👥 Parceiros", "📰 Gestão de Notícias", "🛍️ Loja Recompensas", "📜 Histórico Vendas", "📁 Categorias"
            ])

            with tab_categorias:
                st.subheader("Configuração de Ramos e Profissões")
                doc_cat_ref = db.collection("configuracoes").document("categorias")
                res_cat = doc_cat_ref.get()
                lista_atual = res_cat.to_dict().get("lista", CATEGORIAS_OFICIAIS) if res_cat.exists else CATEGORIAS_OFICIAIS
                
                c1, c2 = st.columns([3, 1])
                nova_cat = c1.text_input("Nova Categoria de Serviço:")
                if c2.button("➕ ADICIONAR", use_container_width=True):
                    if nova_cat and nova_cat not in lista_atual:
                        lista_atual.append(nova_cat)
                        lista_atual.sort()
                        doc_cat_ref.set({"lista": lista_atual})
                        st.success(f"Categoria '{nova_cat}' adicionada!")
                        st.rerun()

                st.write("Categorias ativas:", lista_atual)

            with tab_noticias:
                st.subheader("📡 Scanner de Notícias Automatizado")
                c_ia1, c_ia2 = st.columns(2)
                IMG_NEWS_DEFAULT = "https://images.unsplash.com/photo-1504711432869-0df30d7eaf4d?w=800"
                
                if c_ia1.button("🔍 SCANNER GOOGLE NEWS (GRAJAÚ)", use_container_width=True):
                    feed = feedparser.parse("https://news.google.com/rss/search?q=Grajaú+São+Paulo&hl=pt-BR&gl=BR&ceid=BR:pt-419")
                    st.session_state['sugestoes_ia'] = [{"titulo": e.title, "link": e.link, "img": IMG_NEWS_DEFAULT, "fonte": "Google News"} for e in feed.entries[:3]]
                    st.success("Notícias capturadas!")

                if c_ia2.button("📡 SCANNER VIA NEWS API", use_container_width=True):
                    try:
                        chave = st.secrets.get('NEWS_API_KEY', '516289bf44e1429784e0ca0102854a0d')
                        api_url = f"https://newsapi.org/v2/everything?q=Grajaú+São+Paulo&language=pt&apiKey={chave}"
                        res = requests.get(api_url).json()
                        st.session_state['sugestoes_ia'] = [
                            {
                                "titulo": art['title'], 
                                "link": art['url'], 
                                "img": art.get('urlToImage') or IMG_NEWS_DEFAULT, 
                                "fonte": art.get('source', {}).get('name', 'NewsAPI')
                            } for art in res.get("articles", [])[:3]
                        ]
                        st.success("Matérias mineradas!")
                    except Exception as e: 
                        st.error(f"Falha na API: {e}")

                if 'sugestoes_ia' in st.session_state:
                    cols_sug = st.columns(len(st.session_state['sugestoes_ia']))
                    for idx, sug in enumerate(st.session_state['sugestoes_ia']):
                        with cols_sug[idx]:
                            if sug.get('img'): st.image(sug['img'], use_container_width=True)
                            st.info(f"**{sug['titulo'][:60]}...**")
                            if st.button("✅ USAR", key=f"sug_adm_{idx}"):
                                st.session_state['temp_titulo'] = sug['titulo']
                                st.session_state['temp_link'] = sug['link']
                                st.session_state['temp_img'] = sug.get('img', "")
                                st.rerun()

                with st.form("form_noticia_adm"):
                    nt = st.text_input("Título", value=st.session_state.get('temp_titulo', ""))
                    ni = st.text_input("URL Imagem Capa", value=st.session_state.get('temp_img', ""))
                    nl = st.text_input("Link Completo", value=st.session_state.get('temp_link', ""))
                    
                    if st.form_submit_button("🚀 PUBLICAR NO FEED"):
                        if nt and nl:
                            db.collection("noticias").add({
                                "titulo": nt, 
                                "imagem_url": ni or IMG_NEWS_DEFAULT, 
                                "link_original": nl, 
                                "data": datetime.now(fuso_br), 
                                "categoria": "DESTAQUE"
                            })
                            for k in ['temp_titulo','temp_img','temp_link','sugestoes_ia']: 
                                st.session_state.pop(k, None)
                            st.success("Notícia publicada!")
                            st.rerun()

                st.divider()
                st.subheader("👀 Notícias no Feed")
                noticias_ref = db.collection("noticias").order_by("data", direction="DESCENDING").limit(6).stream()
                lista_n = [n.to_dict() | {"id": n.id} for n in noticias_ref]
                if lista_n:
                    for i in range(0, len(lista_n), 3):
                        cols = st.columns(3)
                        for j in range(3):
                            if i + j < len(lista_n):
                                n = lista_n[i + j]
                                with cols[j]:
                                    st.markdown(f'<div style="height:110px;overflow:hidden;border-radius:8px;background:#eee;"><img src="{n.get("imagem_url","")}" style="width:100%;height:100%;object-fit:cover;"></div>', unsafe_allow_html=True)
                                    st.caption(f"**{n.get('titulo')[:40]}...**")
                                    if st.button("🗑 Deletar", key=f"del_not_{n['id']}"):
                                        db.collection("noticias").document(n['id']).delete()
                                        st.rerun()

            with tab_loja:
                st.subheader("🛒 Itens da Loja Recompensas")
                with st.form("add_loja_form"):
                    c1, c2, c3 = st.columns([2,1,1])
                    ln = c1.text_input("Item")
                    lp = c2.number_input("Preço (GeralCoins)", min_value=1, value=10)
                    le = c3.number_input("Estoque", min_value=1, value=5)
                    lf = st.file_uploader("Banner", type=['jpg','png'])
                    
                    if st.form_submit_button("SALVAR ITEM"):
                        img_loja_b64 = otimizar_imagem_admin(lf) if lf else ""
                        db.collection("loja").add({
                            "nome": ln, 
                            "preco": lp, 
                            "estoque": le, 
                            "foto": img_loja_b64,
                            "data": datetime.now(fuso_br)
                        })
                        st.success("Item publicado!")
                        st.rerun()

                st.divider()
                itens_loja = db.collection("loja").stream()
                for item_doc in itens_loja:
                    it = item_doc.to_dict()
                    c_item1, c_item2, c_item3 = st.columns([1, 3, 1])
                    with c_item1:
                        if it.get('foto'):
                            st.image(safe_image_src(it.get('foto')), width=60)
                    with c_item2:
                        st.markdown(f"**{it.get('nome')}** — Preço: `{it.get('preco')} GeralCoins` | Estoque: `{it.get('estoque')} un`")
                    with c_item3:
                        if st.button("🗑️ Deletar", key=f"del_loja_{item_doc.id}"):
                            db.collection("loja").document(item_doc.id).delete()
                            st.rerun()

            with tab_vendas:
                st.subheader("📜 Resgates de Prêmios")
                vendas_ref = db.collection("vendas").order_by("data", direction="DESCENDING").limit(20).stream()
                vendas_data = []
                for v in vendas_ref:
                    vd = v.to_dict()
                    vendas_data.append({
                        "Data": vd.get('data').astimezone(fuso_br).strftime('%d/%m %H:%M') if vd.get('data') else "---",
                        "Cliente": vd.get('usuario_nome', 'Anônimo'),
                        "Produto": vd.get('produto_nome', '---'),
                        "Preço": f"{vd.get('preco', 0)} 🪙"
                    })
                if vendas_data: 
                    st.table(pd.DataFrame(vendas_data))
                else: 
                    st.info("Nenhum resgate efetuado ainda.")

            with tab_profissionais:
                try:
                    profs_ref = db.collection("profissionais").stream()
                    profs_list = [p.to_dict() | {"id": p.id} for p in profs_ref]
                    df = pd.DataFrame(profs_list)
                    
                    if not df.empty:
                        busca = st.text_input("🔍 Localizar parceiro (Nome ou WhatsApp)")
                        if busca: 
                            df = df[df['nome'].str.contains(busca, case=False, na=False) | df['whatsapp'].str.contains(busca, na=False)]
                        
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Parceiros Cadastrados", len(df))
                        m2.metric("Aguardando Aprovação", len(df[df['aprovado'] == False]) if 'aprovado' in df else 0)
                        m3.metric("Moedas Ativas", f"🪙 {int(df['saldo'].sum()) if 'saldo' in df else 0}")
                        
                        doc_cat = db.collection("configuracoes").document("categorias").get()
                        cats_adm = doc_cat.to_dict().get("lista", CATEGORIAS_OFICIAIS) if doc_cat.exists else CATEGORIAS_OFICIAIS

                        for _, p in df.iterrows():
                            pid = p['id']
                            status = "🟢" if p.get('aprovado') else "🟡"
                            with st.expander(f"{status} {str(p.get('nome','')).upper()} ({p.get('area', 'Geral')})"):
                                with st.form(f"f_edit_adm_{pid}"):
                                    c1, c2 = st.columns(2)
                                    n_nome = c1.text_input("Nome", value=p.get('nome',''))
                                    
                                    idx_c = cats_adm.index(p.get('area')) if p.get('area') in cats_adm else 0
                                    n_area = c2.selectbox("Área", cats_adm, index=idx_c)
                                    n_desc = st.text_area("Descrição", value=p.get('descricao',''))
                                    
                                    c3, c4, c5 = st.columns(3)
                                    n_zap = c3.text_input("WhatsApp", value=p.get('whatsapp',''))
                                    n_saldo = c4.number_input("Saldo GeralCoins", value=int(p.get('saldo', 0)))
                                    n_status = c5.selectbox("Status Conta", ["Aprovado", "Pendente"], index=0 if p.get('aprovado') else 1)
                                    
                                    if st.form_submit_button("💾 SALVAR DADOS DO PARCEIRO"):
                                        upd = {
                                            "nome": n_nome, 
                                            "area": n_area, 
                                            "descricao": n_desc, 
                                            "whatsapp": limpar_whatsapp(n_zap), 
                                            "saldo": int(n_saldo), 
                                            "aprovado": (n_status == "Aprovado")
                                        }
                                        db.collection("profissionais").document(pid).update(upd)
                                        st.success("Alterações salvas!")
                                        st.rerun()

                                if st.button("🗑 EXCLUIR CADASTRO", key=f"del_pro_adm_{pid}"):
                                    db.collection("profissionais").document(pid).delete()
                                    st.rerun()
                    else:
                        st.info("Nenhum profissional cadastrado.")
                except Exception as e: 
                    st.error(f"Erro ao listar profissionais: {e}")

# ==============================================================================
# ABA 6: 📊 FINANCEIRO
# ==============================================================================
if 'financeiro' in abas_dict:
    with menu_abas[abas_dict['financeiro']]:
        st.header("📊 Métricas do Ecossistema GeralJá & Grajaú Tem")
        try:
            profs_ref = db.collection("profissionais").stream()
            profs_list = [p.to_dict() for p in profs_ref]
            if profs_list:
                df_fin = pd.DataFrame(profs_list)
                total_moedas = df_fin['saldo'].sum() if 'saldo' in df_fin else 0
                total_cliques = df_fin['cliques'].sum() if 'cliques' in df_fin else 0
                
                col_f1, col_f2 = st.columns(2)
                col_f1.metric("Moedas GeralCoins Ativas", f"🪙 {int(total_moedas)}")
                col_f2.metric("Total de Clientes Direcionados", f"🚀 {int(total_cliques)} contatos")
            else: 
                st.info("Sem movimentações registradas.")
        except Exception as e: 
            st.error(f"Erro ao carregar dados financeiro: {e}")

# ==============================================================================
# RODAPÉ INSTITUCIONAL UNIFICADO
# ==============================================================================
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")

col_foot1, col_foot2 = st.columns([3, 1])

with col_foot1:
    st.markdown("""
    <div>
        <p style='font-size: 14px; color: #64748B; margin: 0;'>
            © 2026 <b>GeralJá</b> & <b>Grajaú Tem</b> — Todos os direitos reservados.
        </p>
        <p style='font-size: 12px; color: #94A3B8; margin: 4px 0 0 0;'>
            A maior vitrine da região: conectando moradores, comerciantes e prestadores de serviço.
        </p>
        <div style="margin-top: 8px;">
            <span style="background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 20px; padding: 4px 12px; color: #0f172a; font-size: 11px; font-weight: bold;">
                🛡️ Plataforma com IA Multimodelos & Rádio Ao Vivo
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_foot2:
    st.markdown("""
    <div style='text-align: right; margin-top: 5px;'>
        <a href='https://geralja.com.br' target='_blank' style='text-decoration: none; color: #0047AB; font-weight: 700; font-size: 14px;'>
            geralja.com.br 🚀
        </a>
    </div>
    """, unsafe_allow_html=True)
