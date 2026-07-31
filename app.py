# ==============================================================================
# GERALJÁ: CRIANDO SOLUÇÕES - MÓDULO UNIFICADO & TURBINADO
# VERSÃO 5.0 SOCIAL - Perfil Moderno Estilo Rede Social + Vitrine Turbinada
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
from PIL import Image

# --- BIBLIOTECAS NÍVEL 5.0 ---
from groq import Groq
from fuzzywuzzy import process
from urllib.parse import quote
import google.generativeai as genai
from google_auth_oauthlib.flow import Flow

# --- TENTA IMPORTAR COMPONENTES JS COM FALLBACK SEGURO ---
streamlit_js_eval = None
get_geolocation = None
try:
    from streamlit_js_eval import streamlit_js_eval, get_geolocation
except ImportError:
    pass
except Exception:
    pass

# --- CONFIGURAÇÃO DE PÁGINA (DEVE SER O PRIMEIRO COMANDO) ---
st.set_page_config(
    page_title="GeralJá | Criando Soluções",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS RESPONSIVO E MODO DIA ADAPTÁVEL ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .main .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
    #MainMenu, footer, header {visibility: hidden;}
    
    /* HEADER COMPACTO */
    .header-container { 
        background: linear-gradient(135deg, #0047AB 0%, #FF8C00 100%); 
        padding: 20px 15px; 
        border-radius: 0 0 25px 25px; 
        text-align: center; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); 
        margin-bottom: 15px;
        margin-top: -1rem;
    }
    .logo-azul { color: #FFFFFF; font-weight: 900; font-size: 38px; letter-spacing: -1px; text-shadow: 1px 1px 3px rgba(0,0,0,0.2); }
    .logo-laranja { color: #FFD700; font-weight: 900; font-size: 38px; letter-spacing: -1px; text-shadow: 1px 1px 3px rgba(0,0,0,0.2); }
    .sub-logo { color: #FFFFFF; font-weight: 600; font-size: 12px; opacity: 0.9; }
    
    /* CARDS RESPONSIVOS */
    .produto-card { background: #f8f9fa; border-radius: 12px; padding: 10px; margin: 5px 0; border: 1px solid #e9ecef; color: #333; }
    .stApp { transition: all 0.3s ease; }
    
    /* ESTILO REDE SOCIAL PARA PERFIL */
    .social-profile-header {
        background: linear-gradient(to bottom, #0047AB, #002D6B);
        height: 120px;
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
        .logo-azul, .logo-laranja { font-size: 32px; }
        h1 { font-size: 1.6rem !important; }
        .stButton button { width: 100%; }
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
    'user_id': None
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ==============================================================================
# BLOCO A: CONFIGURAÇÃO E INICIALIZAÇÃO
# ==============================================================================

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

# CONFIGURAÇÃO DE CHAVES
client_groq = None
try:
    FB_ID = st.secrets.get("FB_CLIENT_ID", "")
    FB_SECRET = st.secrets.get("FB_CLIENT_SECRET", "")
    FIREBASE_API_KEY = st.secrets.get("FIREBASE_API_KEY", "")
    REDIRECT_URI = "https://geralja-zxiaj2ot56fuzgcz7xhcks.streamlit.app/"
    
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    if "GROQ_API_KEY" in st.secrets:
        client_groq = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error(f"⚠️ Erro ao carregar Secrets: {e}")
    st.stop()

HANDLER_URL = "https://geralja-5bb49.firebaseapp.com/__/auth/handler"

# CONEXÃO FIREBASE
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

# CONSTANTES E REGRAS
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
ZAP_VENDAS = "5511980168513"
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

# FUNÇÕES AUXILIARES
def limpar_whatsapp(numero):
    num = re.sub(r'\D', '', str(numero))
    if not num.startswith('55') and len(num) >= 10:
        num = f"55{num}"
    return num

def normalizar(texto):
    if not texto: return ""
    return "".join(ch for ch in unicodedata.normalize('NFKD', str(texto)) 
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

def safe_image_src(valor):
    if not valor:
        return "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    v = str(valor)
    if v.startswith("http") or v.startswith("data:image"):
        return v
    return f"data:image/jpeg;base64,{v}"

def otimizar_imagem_admin(imagem_upload, size=(800, 800)):
    try:
        img = Image.open(imagem_upload)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        img.thumbnail(size)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=75)
        return base64.b64encode(buffer.getvalue()).decode()
    except Exception:
        return None

def processar_ia_avancada(texto):
    if not texto: return "Vazio"
    t_clean = normalizar(texto)
    
    for chave, categoria in CONCEITOS_EXPANDIDOS.items():
        if re.search(rf"\b{re.escape(normalizar(chave))}\b", t_clean):
            return categoria
    
    for cat in CATEGORIAS_OFICIAIS:
        if normalizar(cat) in t_clean:
            return cat

    try:
        cache_ref = db.collection("cache_buscas").document(t_clean).get()
        if cache_ref.exists:
            return cache_ref.to_dict().get("categoria")

        if client_groq:
            prompt = f"O usuário buscou: '{texto}'. Categorias: {CATEGORIAS_OFICIAIS}. Responda apenas o NOME DA CATEGORIA."
            res = client_groq.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
                temperature=0.1
            )
            cat_ia = res.choices[0].message.content.strip()
            db.collection("cache_buscas").document(t_clean).set({"categoria": cat_ia})
            return cat_ia
        return "NAO_ENCONTRADO"
    except Exception:
        return "NAO_ENCONTRADO"

def criar_link_zap(numero, msg):
    return f"https://api.whatsapp.com/send?phone={numero}&text={urllib.parse.quote(msg)}"

@st.cache_data(ttl=900)
def buscar_noticias_rss(busca="Grajaú São Paulo"):
    try:
        url_rss = f"https://news.google.com/rss/search?q={urllib.parse.quote(busca)}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        feed = feedparser.parse(url_rss)
        return feed.entries[:4]
    except Exception:
        return []

# OAUTH GOOGLE HANDLER
def get_google_flow():
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

# CHECAGEM PARÂMETROS DE URL REDE SOCIAL
if "uid" in query_params and not st.session_state.auth:
    fb_uid = query_params["uid"]
    user_query = db.collection("profissionais").where("fb_uid", "==", fb_uid).limit(1).get()
    if user_query:
        doc = user_query[0]
        st.session_state.auth = True
        st.session_state.user_id = doc.id
        st.success(f"✅ Autenticação realizada via Rede Social!")
        time.sleep(0.5)
        st.rerun()

# CONTROLE DE MODO ESCURO
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

# CABEÇALHO PRINCIPAL
st.markdown('<div class="header-container"><span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span><br><span class="sub-logo">BRASIL ELITE EDITION</span></div>', unsafe_allow_html=True)

# ==============================================================================
# BLOCO B: SISTEMA DE NAVEGAÇÃO E ABAS UNIFICADAS
# ==============================================================================

lista_abas = ["🔍 BUSCAR", "🚀 CADASTRAR", "👤 MEU PERFIL", "⭐ FEEDBACK"]

# ADMIN ESCONDIDO
with st.sidebar:
    st.markdown("### 🔐")
    comando = st.text_input("Acesso", type="password", key="admin_key", label_visibility="collapsed", placeholder="Código")
    if comando in ["abracadabra", "mumias"]:
        lista_abas.append("👑 ADMIN")
    if comando == "financeiro2026":
        lista_abas.append("📊 FINANCEIRO")
    if comando == "geralja_master":
        lista_abas.extend(["👑 ADMIN", "📊 FINANCEIRO"])

menu_abas = st.tabs(lista_abas)

# MAPEAMENTO DE ABAS
abas_dict = {}
for i, nome in enumerate(lista_abas):
    if "BUSCAR" in nome: abas_dict['buscar'] = i
    elif "CADASTRAR" in nome: abas_dict['cadastrar'] = i
    elif "MEU PERFIL" in nome: abas_dict['perfil'] = i
    elif "ADMIN" in nome: abas_dict['admin'] = i
    elif "FEEDBACK" in nome: abas_dict['feedback'] = i
    elif "FINANCEIRO" in nome: abas_dict['financeiro'] = i

# ------------------------------------------------------------------------------
# ABA 1: BUSCAR
# ------------------------------------------------------------------------------
if 'buscar' in abas_dict:
    with menu_abas[abas_dict['buscar']]:
        st.markdown("### 🏙️ O que você precisa no Grajaú?")
        
        with st.expander("📍 Seus dados de Localização (GPS)", expanded=False):
            if get_geolocation:
                try:
                    loc = get_geolocation(component_key="geo_high_prec") 
                    if loc and 'coords' in loc:
                        st.session_state.minha_lat = loc['coords']['latitude']
                        st.session_state.minha_lon = loc['coords']['longitude']
                        precisao = loc['coords'].get('accuracy', 0)
                        st.session_state.js_disponivel = True
                        st.success(f"GPS Ativo (Precisão: {precisao:.0f}m)")
                    else:
                        st.session_state.js_disponivel = False
                        st.warning("GPS indisponível. Usando localização padrão.")
                except Exception:
                    st.session_state.js_disponivel = False
                    st.warning("Recurso GPS indisponível. Use busca por bairro.")
            else:
                st.session_state.js_disponivel = False
                st.info("GPS não suportado neste dispositivo.")

        minha_lat = st.session_state.minha_lat
        minha_lon = st.session_state.minha_lon

        c1, c2 = st.columns([3, 1])
        termo_busca = c1.text_input("Ex: 'Cano estourado' ou 'Pizzaria'", key="main_search_v5")
        raio_km = c2.select_slider("Raio (KM)", options=[1, 3, 5, 10, 20, 50, 500], value=5)

        if termo_busca:
            with st.status("🔍 Buscando...", expanded=False) as status:
                doc_cat = db.collection("configuracoes").document("categorias").get()
                lista_oficial = doc_cat.to_dict().get("lista", CATEGORIAS_OFICIAIS) if doc_cat.exists else CATEGORIAS_OFICIAIS
                
                cat_ia = next((c for c in lista_oficial if c.lower() in termo_busca.lower()), None)
                if not cat_ia:
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
                status.update(label=f"Resultados para {cat_ia}!", state="complete")

            if not lista_ranking:
                st.warning(f"Nenhum profissional de '{cat_ia}' encontrado.")
            else:
                for p in lista_ranking:
                    f_perfil = safe_image_src(p.get('foto_url', ''))
                    is_elite = p['score_elite'] > 0
                    cor_borda = "#FFD700" if is_elite else "#0047AB"
                    zap_link = criar_link_zap(limpar_whatsapp(p.get('whatsapp','')), "Vi seu perfil no GeralJá")

                    st.markdown(f"""
                    <div style="background:white; border-radius:20px; border-left:8px solid {cor_borda}; padding:15px; margin-bottom:15px; box-shadow:0 4px 10px rgba(0,0,0,0.1); color:black;">
                        <div style="font-size:11px; color:#0047AB; font-weight:bold; margin-bottom:8px;">
                            📍 a {p['dist']:.1f} km {" | 🏆 ELITE" if is_elite else ""}
                        </div>
                        <div style="display:flex; align-items:center; gap:12px;">
                            <img src="{f_perfil}" style="width:55px; height:55px; border-radius:50%; object-fit:cover; border:2px solid #eee;">
                            <div>
                                <h4 style="margin:0; color:#1e3a8a;">{str(p.get('nome','')).upper()}</h4>
                                <p style="margin:0; color:#666; font-size:12px;">{str(p.get('descricao',''))[:80]}...</p>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    produtos = p.get('produtos', [])
                    produtos_ativos = [pr for pr in produtos if pr.get('ativo', True)][:3]
                    if produtos_ativos and p.get('tipo_conta') == 'comerciante':
                        st.markdown("<div style='margin-top:10px;'><b>🛍️ Destaques:</b></div>", unsafe_allow_html=True)
                        cols = st.columns(len(produtos_ativos))
                        for idx, prod in enumerate(produtos_ativos):
                            with cols[idx]:
                                st.image(safe_image_src(prod.get('foto_b64', '')), use_container_width=True)
                                st.markdown(f"<div class='produto-card'><b>{prod.get('nome','')}</b><br>R$ {prod.get('preco',0):.2f}</div>", unsafe_allow_html=True)
                                link_prod = criar_link_zap(limpar_whatsapp(p.get('whatsapp','')), f"Olá! Vi no GeralJá e quero {prod.get('nome','')}")
                                st.link_button("Pedir", link_prod, use_container_width=True)
                    
                    st.markdown(f"""
                        <a href="{zap_link}" target="_blank" style="display:block; background:#25D366; color:white; text-align:center; padding:12px; border-radius:12px; text-decoration:none; font-weight:bold; margin-top:12px;">💬 CHAMAR NO WHATSAPP</a>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📰 Plantão Grajaú Tem")
        
        noticias = buscar_noticias_rss()
        if noticias:
            cols = st.columns(4)
            for i, n in enumerate(noticias):
                with cols[i]:
                    img = "https://images.unsplash.com/photo-1504711432869-0df30d7eaf4d?w=400"
                    if hasattr(n, 'media_content') and n.media_content:
                        img = n.media_content[0]['url']
                    fonte = n.source.get('title', 'Google News') if hasattr(n, 'source') else 'Google News'
                    tempo_leitura = max(1, len(n.title) // 40)

                    st.markdown(f"""
                    <a href="{n.link}" target="_blank" style="text-decoration:none; color:inherit;">
                        <div style="border:1px solid #ddd; border-radius:10px; overflow:hidden; height:290px; background:white;">
                            <img src="{img}" style="width:100%; height:120px; object-fit:cover;">
                            <div style="padding:10px;">
                                <span style="background:#f1f5f9; padding:2px 6px; border-radius:4px; font-size:10px; font-weight:bold; color:#475569;">⏱️ {tempo_leitura} min</span>
                                <p style="font-size:12px; font-weight:bold; margin-top:5px; color:#333;">{n.title[:75]}...</p>
                                <p style="font-size:10px; color:#888; margin-top:5px;">📍 {fonte}</p>
                            </div>
                        </div>
                    </a>
                    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# ABA 2: CADASTRAR
# ------------------------------------------------------------------------------
if 'cadastrar' in abas_dict:
    with menu_abas[abas_dict['cadastrar']]:
        st.header("🚀 Cadastre-se ou Atualize seu Perfil")
        st.write("Apareça para milhares de pessoas que precisam dos seus serviços!")

        try:
            doc_cat = db.collection("configuracoes").document("categorias").get()
            cats_atuais = doc_cat.to_dict().get("lista", CATEGORIAS_OFICIAIS) if doc_cat.exists else CATEGORIAS_OFICIAIS
        except Exception:
            cats_atuais = CATEGORIAS_OFICIAIS

        dados_google = st.session_state.get("pre_cadastro", {})
        email_inicial = dados_google.get("email", "")
        nome_inicial = dados_google.get("nome", "")
        foto_google = dados_google.get("foto", "")

        st.markdown("##### Entre rápido com:")
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

        with st.form("form_profissional_unificado"):
            st.caption("💡 DICA: Se já tem cadastro, use o mesmo WhatsApp para editar seus dados.")

            col1, col2 = st.columns(2)
            nome_input = col1.text_input("Nome do Profissional ou Loja", value=nome_inicial)
            zap_input = col2.text_input("WhatsApp (Somente números com DDD)", help="Ex: 11980168513")

            email_input = st.text_input("E-mail (Para login via Google)", value=email_inicial)

            col3, col4 = st.columns(2)
            cat_input = col3.selectbox("Selecione sua Especialidade Principal", cats_atuais)
            senha_input = col4.text_input("Sua Senha de Acesso", type="password", help="Necessária para login e edições")

            desc_input = st.text_area("Descrição Completa (Serviços, Horários, Diferenciais)", max_chars=400)
            tipo_input = st.radio("Tipo de Conta", ["👨‍🔧 Profissional Autônomo", "🏢 Comércio/Loja"], horizontal=True)

            foto_upload = st.file_uploader("Foto de Perfil ou Logo", type=['png', 'jpg', 'jpeg'])

            campos_preenchidos = sum([bool(nome_input), bool(zap_input), bool(email_input), bool(desc_input), bool(senha_input)])
            percentual = (campos_preenchidos / 5) * 100
            st.progress(percentual / 100)
            st.caption(f"Força do seu perfil: **{int(percentual)}% preenchido**")

            btn_acao = st.form_submit_button("✅ FINALIZAR: SALVAR OU ATUALIZAR", use_container_width=True)

        if btn_acao:
            zap_limpo = "".join(filter(str.isdigit, zap_input))
            
            if not nome_input or not zap_limpo or not senha_input:
                st.warning("⚠️ Nome, WhatsApp e Senha são obrigatórios!")
            else:
                try:
                    with st.spinner("Sincronizando com o ecossistema GeralJá..."):
                        doc_ref = db.collection("profissionais").document(zap_limpo)
                        perfil_antigo = doc_ref.get()
                        dados_antigos = perfil_antigo.to_dict() if perfil_antigo.exists else {}

                        foto_b64 = dados_antigos.get("foto_url", "")

                        if foto_upload is not None:
                            foto_b64 = otimizar_imagem_admin(foto_upload)
                        elif not foto_b64 and foto_google:
                            foto_b64 = foto_google
                        elif not foto_b64:
                            foto_b64 = "https://cdn-icons-png.flaticon.com/512/149/149071.png"

                        tipo_c = "comerciante" if "Comércio" in tipo_input else "prestador"

                        dados_pro = {
                            "nome": nome_input,
                            "whatsapp": zap_limpo,
                            "email": email_input,
                            "area": cat_input,
                            "senha": senha_input,
                            "descricao": desc_input,
                            "tipo": tipo_input,
                            "tipo_conta": dados_antigos.get("tipo_conta", tipo_c),
                            "produtos": dados_antigos.get("produtos", []),
                            "foto_url": foto_b64,
                            "saldo": dados_antigos.get("saldo", BONUS_WELCOME),
                            "data_cadastro": dados_antigos.get("data_cadastro", datetime.now(fuso_br).strftime("%d/%m/%Y")),
                            "aprovado": True,
                            "cliques": dados_antigos.get("cliques", 0),
                            "rating": dados_antigos.get("rating", 5),
                            "lat": st.session_state.get('minha_lat', LAT_REF),
                            "lon": st.session_state.get('minha_lon', LON_REF)
                        }

                        doc_ref.set(dados_pro, merge=True)

                        st.session_state.auth = True
                        st.session_state.user_id = zap_limpo
                        st.session_state.pre_cadastro = None

                        st.balloons()
                        st.success(f"✅ Perfil de {nome_input} salvo com sucesso! Você foi autenticado.")
                        time.sleep(1)
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Erro ao processar perfil: {e}")

# ------------------------------------------------------------------------------
# ABA 3: MEU PERFIL (SISTEMA SOCIAL + GERENCIAMENTO)
# ------------------------------------------------------------------------------
if 'perfil' in abas_dict:
    with menu_abas[abas_dict['perfil']]:
        if not st.session_state.auth:
            st.subheader("🚀 Acesso ao Painel do Parceiro")
            fb_id = st.secrets.get("FB_CLIENT_ID", "")
            g_uri = st.secrets.get("google_auth", {}).get("redirect_uri", REDIRECT_URI)
            url_direta_fb = f"https://www.facebook.com/v18.0/dialog/oauth?client_id={fb_id}&redirect_uri={g_uri}&scope=public_profile,email"

            st.markdown(f'''
                <a href="{url_direta_fb}" target="_top" style="text-decoration:none;">
                    <div style="background:#1877F2;color:white;padding:12px;border-radius:8px;text-align:center;font-weight:bold;display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow: 0px 4px 6px rgba(0,0,0,0.1);">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/2021_Facebook_icon.svg" width="20px" style="margin-right:10px;">
                        ENTRAR COM FACEBOOK
                    </div>
                </a>
            ''', unsafe_allow_html=True)

            st.markdown("<p style='text-align:center; margin-top:15px; color:#666;'>— ou use suas credenciais locais —</p>", unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            l_zap = col1.text_input("WhatsApp Cadastrado", key="login_zap_geralja_v10", placeholder="Ex: 11980168513")
            l_pw = col2.text_input("Senha Numérica", type="password", key="login_pw_geralja_v10")

            if st.button("ENTRAR NO PAINEL", key="btn_entrar_geralja_v10", use_container_width=True):
                try:
                    zap_formatado = "".join(filter(str.isdigit, l_zap))
                    u = db.collection("profissionais").document(zap_formatado).get()
                    if u.exists:
                        dados_user = u.to_dict()
                        if str(dados_user.get('senha')) == str(l_pw):
                            st.session_state.auth = True
                            st.session_state.user_id = u.id
                            st.success("Login realizado com sucesso!")
                            st.rerun()
                        else: st.error("❌ Senha incorreta.")
                    else: st.error("❌ WhatsApp não localizado.")
                except Exception as e: st.error(f"Erro no banco: {e}")
        else:
            user_id = st.session_state.user_id
            doc_ref = db.collection("profissionais").document(user_id)
            user_doc = doc_ref.get()

            if user_doc.exists:
                user_data = user_doc.to_dict()
                
                foto_perfil = safe_image_src(user_data.get('foto_url', ''))
                modo_noite_class = "dark-mode" if st.session_state.modo_noite else ""
                
                # HEADER REDE SOCIAL
                st.markdown(f"""
                <div class="{modo_noite_class}">
                    <div class="social-profile-header">
                        <img src="{foto_perfil}" class="social-profile-avatar">
                    </div>
                    <div class="social-profile-info">
                        <h1 class="social-name">{user_data.get('nome', 'Usuário')} {'✅' if user_data.get('verificado') else ''}</h1>
                        <p class="social-tag">@{normalizar(user_data.get('nome', 'user')).replace(' ', '')} • {user_data.get('area', 'Profissional')}</p>
                        <p class="social-bio">{user_data.get('descricao', 'Sem descrição disponível.')}</p>
                        
                        <div class="social-stats">
                            <div class="stat-item">
                                <span class="stat-value">{user_data.get('cliques', 0)}</span>
                                <span class="stat-label">Cliques</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-value">💎 {user_data.get('saldo', 0)}</span>
                                <span class="stat-label">Saldo</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-value">{'🟢' if user_data.get('aprovado') else '🟡'}</span>
                                <span class="stat-label">Status</span>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                tab_vitrine, tab_config, tab_ajuda = st.tabs(["🛍️ MINHA VITRINE", "⚙️ CONFIGURAÇÕES", "❓ AJUDA"])
                
                with tab_vitrine:
                    tipo_conta = user_data.get('tipo_conta', 'prestador')
                    if tipo_conta != 'comerciante':
                        st.info("💡 Você está no modo Prestador. Ative o modo Comerciante para vender produtos diretamente.")
                        if st.button("ATIVAR MODO COMERCIANTE", use_container_width=True):
                            doc_ref.update({"tipo_conta": "comerciante"})
                            st.success("Modo Comerciante ativado!")
                            time.sleep(1)
                            st.rerun()
                    else:
                        produtos = user_data.get('produtos', [])
                        limite_max = 10
                        st.markdown(f"**Produtos na Vitrine:** `{len(produtos)} / {limite_max}`")

                        if produtos:
                            st.markdown("#### Meus Produtos")
                            for idx, prod in enumerate(produtos):
                                c_img, c_txt, c_btn = st.columns([1, 3, 1])
                                with c_img:
                                    st.image(safe_image_src(prod.get('foto_b64')), width=60)
                                with c_txt:
                                    st.markdown(f"**{prod.get('nome')}** — `R$ {prod.get('preco', 0):.2f}`")
                                    st.caption(prod.get('desc', ''))
                                with c_btn:
                                    if st.button("🗑️", key=f"del_p_soc_{idx}"):
                                        produtos.pop(idx)
                                        doc_ref.update({"produtos": produtos})
                                        st.rerun()
                        
                        st.markdown("---")
                        if len(produtos) >= limite_max:
                            st.error("⚠️ Você atingiu o limite máximo de 10 itens na vitrine.")
                        else:
                            with st.expander("➕ ADICIONAR NOVO PRODUTO", expanded=False):
                                with st.form("novo_produto_social", clear_on_submit=True):
                                    p_nome = st.text_input("Nome do Produto")
                                    c1, c2 = st.columns(2)
                                    p_preco = c1.number_input("Preço R$", min_value=0.0, format="%.2f")
                                    p_foto = c2.file_uploader("Foto Quadrada", type=['jpg', 'jpeg', 'png'])
                                    p_desc = st.text_area("Breve descrição")
                                    p_destaque = st.checkbox("Destaque na busca")
                                    
                                    if st.form_submit_button("PUBLICAR PRODUTO", use_container_width=True):
                                        if p_nome and p_preco > 0 and p_foto:
                                            foto_b64 = otimizar_imagem_admin(p_foto, size=(400, 400))
                                            if foto_b64:
                                                novo_prod = {
                                                    "nome": p_nome, "preco": float(p_preco), "desc": p_desc,
                                                    "foto_b64": foto_b64, "ativo": True, "destaque": p_destaque,
                                                    "criado_em": datetime.now(fuso_br).isoformat()
                                                }
                                                produtos.append(novo_prod)
                                                doc_ref.update({"produtos": produtos})
                                                st.success("Produto publicado!")
                                                time.sleep(1)
                                                st.rerun()
                                        else:
                                            st.warning("Preencha Nome, Preço e envie uma Foto.")

                with tab_config:
                    st.markdown("#### Editar Perfil")
                    with st.form("edit_perfil_social"):
                        n_nome = st.text_input("Nome de Exibição", value=user_data.get('nome'))
                        n_area = st.selectbox("Área de Atuação", CATEGORIAS_OFICIAIS, index=CATEGORIAS_OFICIAIS.index(user_data.get('area')) if user_data.get('area') in CATEGORIAS_OFICIAIS else 0)
                        n_zap = st.text_input("WhatsApp", value=user_data.get('whatsapp'))
                        n_desc = st.text_area("Bio / Descrição", value=user_data.get('descricao'))
                        n_foto = st.file_uploader("Trocar Foto de Perfil", type=['jpg', 'png', 'jpeg'])
                        
                        if st.form_submit_button("SALVAR ALTERAÇÕES", use_container_width=True):
                            upd = {"nome": n_nome, "area": n_area, "whatsapp": limpar_whatsapp(n_zap), "descricao": n_desc}
                            if n_foto:
                                img_b64 = otimizar_imagem_admin(n_foto)
                                if img_b64: upd["foto_url"] = img_b64
                            doc_ref.update(upd)
                            st.success("Perfil atualizado!")
                            time.sleep(1)
                            st.rerun()

                    if st.button("📍 RECALIBRAR GPS DO PERFIL", use_container_width=True):
                        if streamlit_js_eval:
                            loc = streamlit_js_eval(js_expressions="navigator.geolocation.getCurrentPosition(s => s)", key='gps_v8')
                            if loc and 'coords' in loc:
                                doc_ref.update({"lat": loc['coords']['latitude'], "lon": loc['coords']['longitude']})
                                st.success("✅ GPS Atualizado com sucesso!")
                        else:
                            st.warning("Recurso não suportado neste navegador.")
                    
                    st.divider()
                    if st.button("🚪 SAIR DA CONTA", use_container_width=True):
                        st.session_state.auth = False
                        st.session_state.user_id = None
                        st.rerun()

                with tab_ajuda:
                    st.markdown("#### Central de Ajuda")
                    st.info("💡 Perfis com fotos de alta qualidade e descrições completas recebem 3x mais cliques!")
                    st.write("**Como funciona o saldo?**")
                    st.caption("Cada clique no seu botão de WhatsApp consome 1 moeda (💎). Recarregue com o administrador.")
                    st.link_button("FALAR COM SUPORTE", criar_link_zap(ZAP_ADMIN, "Olá, preciso de ajuda com meu perfil no GeralJá"))

# ------------------------------------------------------------------------------
# ABA 4: FEEDBACK
# ------------------------------------------------------------------------------
if 'feedback' in abas_dict:
    with menu_abas[abas_dict['feedback']]:
        st.header("⭐ Avalie a Plataforma")
        st.write("Sua opinião nos ajuda a melhorar.")
        nota = st.slider("Nota", 1, 5, 5)
        comentario = st.text_area("O que podemos melhorar?")
        if st.button("Enviar Feedback"):
            st.success("Obrigado! Sua mensagem foi enviada para nossa equipe.")

# ------------------------------------------------------------------------------
# ABA 5: ADMIN
# ------------------------------------------------------------------------------
if 'admin' in abas_dict:
    with menu_abas[abas_dict['admin']]:
        if not st.session_state.admin_logado:
            st.markdown("### 🔐 Painel Operacional Central")
            with st.form("login_adm"):
                u = st.text_input("Username Administrativo")
                p = st.text_input("Token de Segurança", type="password")
                if st.form_submit_button("AUTENTICAR DIRETORIA", use_container_width=True):
                    if u == st.secrets.get("ADMIN_USER", "geralja") and p == st.secrets.get("ADMIN_PASS", "Bps36ocara"):
                        st.session_state.admin_logado = True
                        st.success("Conectado à Central de Comando!")
                        st.rerun()
                    else: st.error("Credenciais inválidas.")
        else:
            st.markdown("## 👑 Central de Comando GeralJá & Grajaú Tem")
            if st.button("🚪 Encerrar Sessão Admin"):
                st.session_state.admin_logado = False
                st.rerun()

            tab_parceiros, tab_noticias, tab_loja, tab_vendas, tab_categorias = st.tabs([
                "👥 Parceiros", "📰 Scanner de Notícias", "🛍️ Loja", "📜 Vendas", "📁 Categorias"
            ])

            with tab_categorias:
                st.subheader("Configuração de Ramos e Profissões")
                doc_cat_ref = db.collection("configuracoes").document("categorias")
                res_cat = doc_cat_ref.get()
                lista_atual = res_cat.to_dict().get("lista", CATEGORIAS_OFICIAIS) if res_cat.exists else CATEGORIAS_OFICIAIS
                
                c1, c2 = st.columns([3, 1])
                nova_cat = c1.text_input("Nova Profissão:")
                if c2.button("➕ INCLUIR", use_container_width=True):
                    if nova_cat and nova_cat not in lista_atual:
                        lista_atual.append(nova_cat)
                        lista_atual.sort()
                        doc_cat_ref.set({"lista": lista_atual})
                        st.success(f"{nova_cat} adicionada!")
                        st.rerun()

            with tab_noticias:
                st.subheader("📡 Scanner & Captação de Notícias IA")
                c_ia1, c_ia2 = st.columns(2)
                IMG_NEWS_DEFAULT = "https://images.unsplash.com/photo-1504711432869-0df30d7eaf4d?w=800"
                
                if c_ia1.button("🔍 CAPTAR GOOGLE NEWS", use_container_width=True):
                    feed = feedparser.parse("https://news.google.com/rss/search?q=Grajaú+São+Paulo&hl=pt-BR&gl=BR&ceid=BR:pt-419")
                    st.session_state['sugestoes_ia'] = [{"titulo": e.title, "link": e.link, "img": IMG_NEWS_DEFAULT, "fonte": "Google"} for e in feed.entries[:3]]
                
                if c_ia2.button("📡 SCANNER NEWS API", use_container_width=True):
                    try:
                        chave = st.secrets.get('NEWS_API_KEY','516289bf44e1429784e0ca0102854a0d')
                        res = requests.get(f"https://newsapi.org/v2/everything?q=Grajaú+São+Paulo&language=pt&apiKey={chave}").json()
                        st.session_state['sugestoes_ia'] = [{"titulo": a['title'], "link": a['url'], "img": a.get('urlToImage') or IMG_NEWS_DEFAULT, "fonte": "NewsAPI"} for a in res.get("articles", [])[:3]]
                    except Exception as e: st.error(f"Erro na API: {e}")

                if 'sugestoes_ia' in st.session_state:
                    cols_sug = st.columns(3)
                    for idx, sug in enumerate(st.session_state['sugestoes_ia']):
                        with cols_sug[idx]:
                            if sug.get('img'): st.image(sug['img'], use_container_width=True)
                            st.info(f"**{sug['titulo'][:60]}...**")
                            if st.button("🚀 PUBLICAR", key=f"sug_{idx}"):
                                db.collection("noticias").add({
                                    "titulo": sug['titulo'],
                                    "imagem_url": sug['img'],
                                    "link_original": sug['link'],
                                    "data": datetime.now(fuso_br).isoformat(),
                                    "categoria": "DESTAQUE"
                                })
                                st.success("Postado no Feed Público!")

                st.divider()
                st.subheader("👀 Notícias Ativas")
                noticias_ref = db.collection("noticias").order_by("data", direction="DESCENDING").limit(6).stream()
                lista_n = [n.to_dict() | {"id": n.id} for n in noticias_ref]
                if lista_n:
                    cols = st.columns(3)
                    for idx, n in enumerate(lista_n):
                        with cols[idx % 3]:
                            st.markdown(f'<div style="height:100px;overflow:hidden;border-radius:8px;"><img src="{n.get("imagem_url","")}" style="width:100%;height:100%;object-fit:cover;"></div>', unsafe_allow_html=True)
                            st.caption(f"**{n.get('titulo')[:40]}...**")
                            if st.button("🗑", key=f"del_n_{n['id']}"):
                                db.collection("noticias").document(n['id']).delete()
                                st.rerun()

            with tab_loja:
                st.subheader("🛒 Itens Comercializados na Central")
                with st.form("add_loja"):
                    c1, c2, c3 = st.columns([2,1,1])
                    ln = c1.text_input("Nome do Item")
                    lp = c2.number_input("Preço (GeralCoins)", min_value=1)
                    le = c3.number_input("Estoque Físico", min_value=1)
                    lf = st.file_uploader("Banner Promocional", type=['jpg','png'])
                    
                    if st.form_submit_button("SALVAR NA LOJA"):
                        foto_b64 = otimizar_imagem_admin(lf, size=(500,500)) if lf else ""
                        db.collection("loja").add({
                            "nome": ln, "preco": lp, "estoque": le, "foto": foto_b64, "atualizado_em": datetime.now(fuso_br).isoformat()
                        })
                        st.success("Produto Adicionado!")
                        st.rerun()

                st.divider()
                for it in db.collection("loja").stream():
                    item = it.to_dict()
                    c_i1, c_i2, c_i3 = st.columns([1, 3, 1])
                    with c_i1:
                        if item.get('foto'): st.image(f"data:image/jpeg;base64,{item['foto']}", width=60)
                    with c_i2:
                        st.markdown(f"**{item.get('nome')}** — Preço: `{item.get('preco')} Moedas` | Estoque: `{item.get('estoque')} un`")
                    with c_i3:
                        if st.button("🗑️", key=f"del_loja_{it.id}"):
                            db.collection("loja").document(it.id).delete()
                            st.rerun()

            with tab_vendas:
                st.subheader("📜 Histórico de Resgates")
                vendas_ref = db.collection("vendas").order_by("data", direction="DESCENDING").limit(20).stream()
                vendas_data = []
                for v in vendas_ref:
                    vd = v.to_dict()
                    vendas_data.append({
                        "Data": vd.get('data'),
                        "Cliente": vd.get('usuario_nome', 'Desconhecido'),
                        "Produto": vd.get('produto_nome', '---'),
                        "Preço": f"{vd.get('preco', 0)} 💎"
                    })
                if vendas_data: st.table(pd.DataFrame(vendas_data))
                else: st.info("Nenhuma venda registrada ainda.")

            with tab_parceiros:
                try:
                    profs_ref = db.collection("profissionais").stream()
                    profs_list = [p.to_dict() | {"id": p.id} for p in profs_ref]
                    df = pd.DataFrame(profs_list)
                    if not df.empty:
                        busca = st.text_input("🔍 Localizar Parceiro (Nome ou WhatsApp)")
                        if busca: df = df[df['nome'].str.contains(busca, case=False, na=False) | df['whatsapp'].str.contains(busca, na=False)]
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Total", len(df))
                        m2.metric("Pendentes", len(df[df['aprovado'] == False]))
                        m3.metric("GeralCoins Em Circulação", f"💎 {int(df['saldo'].sum()) if 'saldo' in df else 0}")
                        
                        for _, p in df.iterrows():
                            pid = p['id']
                            status = "🟢" if p.get('aprovado') else "🟡"
                            with st.expander(f"{status} {str(p.get('nome','')).upper()}"):
                                with st.form(f"f_edit_{pid}"):
                                    c1, c2 = st.columns(2)
                                    n_nome = c1.text_input("Nome", value=p.get('nome'))
                                    n_area = c2.selectbox("Área", lista_atual, index=lista_atual.index(p.get('area')) if p.get('area') in lista_atual else 0)
                                    n_desc = st.text_area("Descrição", value=p.get('descricao'))
                                    c3, c4, c5 = st.columns(3)
                                    n_zap = c3.text_input("Zap", value=p.get('whatsapp'))
                                    n_saldo = c4.number_input("Saldo", value=int(p.get('saldo', 0)))
                                    n_status = c5.selectbox("Status", ["Aprovado", "Pendente"], index=0 if p.get('aprovado') else 1)
                                    
                                    if st.form_submit_button("💾 SALVAR DADOS"):
                                        upd = {
                                            "nome": n_nome, "area": n_area, "descricao": n_desc, 
                                            "whatsapp": n_zap, "saldo": int(n_saldo), "aprovado": (n_status=="Aprovado")
                                        }
                                        db.collection("profissionais").document(pid).update(upd)
                                        st.success("Atualizado!")
                                        st.rerun()
                                if st.button("🗑 EXCLUIR PARCEIRO", key=f"del_p_adm_{pid}"):
                                    db.collection("profissionais").document(pid).delete()
                                    st.rerun()
                except Exception as e: st.error(f"Erro na tabela de parceiros: {e}")

# ------------------------------------------------------------------------------
# ABA 6: FINANCEIRO (EASTER EGG)
# ------------------------------------------------------------------------------
if 'financeiro' in abas_dict:
    with menu_abas[abas_dict['financeiro']]:
        st.header("📊 Painel Financeiro GeralJá")
        try:
            profs_ref = db.collection("profissionais").stream()
            profs_list = [p.to_dict() for p in profs_ref]
            if profs_list:
                df_fin = pd.DataFrame(profs_list)
                total_moedas = df_fin['saldo'].sum() if 'saldo' in df_fin else 0
                total_cliques = df_fin['cliques'].sum() if 'cliques' in df_fin else 0
                col_f1, col_f2 = st.columns(2)
                col_f1.metric("Moedas Ativas", f"🪙 {total_moedas}")
                col_f2.metric("Total de Cliques", f"🚀 {total_cliques}")
            else: st.info("Nenhum dado financeiro disponível.")
        except Exception as e: st.error(f"Erro: {e}")

# ==============================================================================
# RODAPÉ INSTITUCIONAL UNIFICADO
# ==============================================================================
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")

col_foot1, col_foot2 = st.columns([3, 1])

with col_foot1:
    st.markdown("""
    <div style='vertical-align: middle;'>
        <p style='font-size: 14px; color: #4A5568; margin: 0;'>
            © 2026 <b>GeralJá</b> & <b>Grajaú Tem</b> — Todos os direitos reservados.
        </p>
        <p style='font-size: 12px; color: #718096; margin: 4px 0 0 0;'>
            A maior vitrine da região: conectando moradores, profissionais e oportunidades.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col_foot2:
    st.markdown("""
    <div style='text-align: right; margin-top: 5px;'>
        <a href='https://geralja.com.br' target='_blank' style='text-decoration: none; color: #3182CE; font-weight: 700; font-size: 14px;'>
            geralja.com.br 🚀
        </a>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<style>
   .footer-container { text-align: center; padding: 10px; color: #64748B; font-size: 12px; }
   .security-badge { display: inline-flex; align-items: center; background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 20px; padding: 5px 15px; color: #0f172a; font-weight: bold; }
   .shield-icon { color: #22c55e; margin-right: 8px; }
</style>
<div class="footer-container">
    <div class="security-badge"><span class="shield-icon">🛡</span> IA de Proteção Ativa: Monitorando Contra Ameaças</div>
</div>
""", unsafe_allow_html=True)
