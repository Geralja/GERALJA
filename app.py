# ==============================================================================
# GERALJÁ: CRIANDO SOLUÇÕES - MÓDULO 1: INFRAESTRUTURA & SEGURANÇA MÁXIMA
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
# --- DETECÇÃO DE MODO DIA/NOITE ADAPTÁVEL ---
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
    'pre_cadastro': None
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        @media (max-width: 640px) {
            .main .block-container { padding: 1rem !important; }
            h1 { font-size: 1.8rem !important; }
        }
    </style>
""", unsafe_allow_html=True)

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
# 2. CONFIGURAÇÃO DE CHAVES
# ------------------------------------------------------------------------------
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

def otimizar_imagem_admin(imagem_upload):
    try:
        img = Image.open(imagem_upload)
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        img.thumbnail((800, 800))
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
    if not texto: return "Vazio"
    t_clean = normalizar_para_ia(texto)
    
    for chave, categoria in CONCEITOS_EXPANDIDOS.items():
        if re.search(rf"\b{re.escape(normalizar_para_ia(chave))}\b", t_clean):
            return categoria
    
    for cat in CATEGORIAS_OFICIAIS:
        if normalizar_para_ia(cat) in t_clean:
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

def finalizar_e_alinhar_layout():
    pass

# ==============================================================================
# BLOCO B: AUTENTICAÇÃO E LOGIN
# ==============================================================================

# ------------------------------------------------------------------------------
# 5. LOGIN GOOGLE
# ------------------------------------------------------------------------------
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

# ------------------------------------------------------------------------------
# 6. CONSTANTES E IA
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

# ==============================================================================
# BLOCO C: INTERFACE PRINCIPAL E ABAS
# ==============================================================================

# DESIGN
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .header-container { background: white; padding: 40px 20px; border-radius: 0 0 50px 50px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.05); border-bottom: 8px solid #FF8C00; margin-bottom: 25px; }
    .logo-azul { color: #0047AB; font-weight: 900; font-size: 50px; letter-spacing: -2px; }
    .logo-laranja { color: #FF8C00; font-weight: 900; font-size: 50px; letter-spacing: -2px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-container"><span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span><br><span class="sub-logo">BRASIL ELITE EDITION</span></div>', unsafe_allow_html=True)

lista_abas = ["🔍 BUSCAR", "🚀 CADASTRAR", "👤 MEU PERFIL", "⭐ FEEDBACK"]

# ADMIN ESCONDIDO - Só aparece com comando secreto
with st.sidebar:
    st.markdown("### 🔐")
    comando = st.text_input("Acesso", type="password", key="admin_key", label_visibility="collapsed", placeholder="Código")
    if comando == "abracadabra":
        lista_abas.append("👑 ADMIN")
    if comando == "financeiro2026":
        lista_abas.append("📊 FINANCEIRO")
    if comando == "geralja_master":
        lista_abas.extend(["👑 ADMIN", "📊 FINANCEIRO"])

menu_abas = st.tabs(lista_abas)

# MAPEAMENTO SEGURO DE ABAS
abas_dict = {}
for i, nome in enumerate(lista_abas):
    if "BUSCAR" in nome: abas_dict['buscar'] = i
    elif "CADASTRAR" in nome: abas_dict['cadastrar'] = i
    elif "MEU PERFIL" in nome: abas_dict['perfil'] = i
    elif "ADMIN" in nome: abas_dict['admin'] = i
    elif "FEEDBACK" in nome: abas_dict['feedback'] = i
    elif "FINANCEIRO" in nome: abas_dict['financeiro'] = i

ZAP_VENDAS = "5511980168513"

# ABA BUSCAR
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
                        st.warning("GPS indisponível. Usando localização padrão. Ative a localização no navegador.")
                except Exception:
                    st.session_state.js_disponivel = False
                    st.warning("Recurso JavaScript indisponível. Use busca manual por bairro.")
            else:
                st.session_state.js_disponivel = False
                st.info("GPS não suportado neste dispositivo. Informe seu bairro manualmente.")

        minha_lat = st.session_state.minha_lat
        minha_lon = st.session_state.minha_lon

        c1, c2 = st.columns([3, 1])
        termo_busca = c1.text_input("Ex: 'Cano estourado' ou 'Pizzaria'", key="main_search_v5")
        raio_km = c2.select_slider("Raio (KM)", options=[1, 3, 5, 10, 20, 50, 500], value=5)

        if termo_busca:
            with st.status("🔍 Buscando...", expanded=False) as status:
                doc_cat = db.collection("configuracoes").document("categorias").get()
                lista_oficial = doc_cat.to_dict().get("lista", []) if doc_cat.exists else []
                
                cat_ia = next((c for c in lista_oficial if c.lower() in termo_busca.lower()), None)
                
                if not cat_ia:
                    st.write("🤖 IA classificando...")
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
                    zap_link = criar_link_zap(limpar_whatsapp(p.get('whatsapp','')), "Vi seu perfil no GeralJa")

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
                                link_prod = criar_link_zap(limpar_whatsapp(p.get('whatsapp','')), f"Olá! Vi no GeralJá e quero 1x {prod.get('nome','')}")
                                st.link_button("Pedir", link_prod, use_container_width=True)
                    
                    st.markdown(f"""
                        <a href="{zap_link}" target="_blank" style="display:block; background:#25D366; color:white; text-align:center; padding:12px; border-radius:12px; text-decoration:none; font-weight:bold; margin-top:12px;">💬 CHAMAR NO WHATSAPP</a>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📰 Plantão Grajaú Tem")
        
        @st.cache_data(ttl=600)
        def buscar_noticias_rss(busca="Grajaú São Paulo"):
            try:
                url_rss = f"https://news.google.com/rss/search?q={urllib.parse.quote(busca)}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
                feed = feedparser.parse(url_rss)
                return feed.entries[:4]
            except Exception:
                return []
        
        noticias = buscar_noticias_rss()
        if noticias:
            cols = st.columns(4)
            for i, n in enumerate(noticias):
                with cols[i]:
                    img = "https://placehold.co/300x200/0047AB/FFFFFF?text=GeralJá"
                    if 'media_content' in n and n.media_content:
                        img = n.media_content[0]['url']
                    fonte = n.source.get('title', 'Google News') if hasattr(n, 'source') else 'Google News'
                    st.markdown(f"""
                    <a href="{n.link}" target="_blank" style="text-decoration:none; color:inherit;">
                        <div style="border:1px solid #ddd; border-radius:10px; overflow:hidden; height:280px; background:white;">
                            <img src="{img}" style="width:100%; height:120px; object-fit:cover;">
                            <div style="padding:10px;">
                                <p style="font-size:12px; font-weight:bold; margin:0; color:#333;">{n.title[:80]}...</p>
                                <p style="font-size:10px; color:#888; margin-top:8px;">{fonte}</p>
                            </div>
                        </div>
                    </a>
                    """, unsafe_allow_html=True)

# ABA CADASTRAR
if 'cadastrar' in abas_dict:
    with menu_abas[abas_dict['cadastrar']]:
        st.header("🚀 Cadastre-se como Profissional")
        st.write("Apareça para milhares de pessoas que precisam do seu serviço!")

        if st.session_state.auth:
            st.info("Você já está logado. Acesse 'Meu Perfil' para gerenciar.")
        else:
            with st.form("cadastro_profissional"):
                email_pre = st.session_state.pre_cadastro.get('email', '') if st.session_state.pre_cadastro else ''
                nome_pre = st.session_state.pre_cadastro.get('nome', '') if st.session_state.pre_cadastro else ''
                foto_pre = st.session_state.pre_cadastro.get('foto', '') if st.session_state.pre_cadastro else ''

                nome = st.text_input("Seu Nome Completo ou Nome Comercial", value=nome_pre)
                email = st.text_input("Seu Melhor E-mail", value=email_pre)
                whatsapp = st.text_input("WhatsApp (apenas números com DDD)")
                area = st.selectbox("Sua Área de Atuação", CATEGORIAS_OFICIAIS)
                descricao = st.text_area("Descreva seus serviços ou produtos (máx. 200 caracteres)", max_chars=200)
                foto_perfil = st.file_uploader("Foto de Perfil (opcional)", type=['jpg', 'jpeg', 'png'])
                termos = st.checkbox("Concordo com os Termos de Uso e Política de Privacidade")

                if st.form_submit_button("CADASTRAR AGORA"):
                    if not termos:
                        st.error("Você deve concordar com os Termos de Uso.")
                    elif not nome or not email or not whatsapp or not area or not descricao:
                        st.error("Por favor, preencha todos os campos obrigatórios.")
                    else:
                        try:
                            foto_url = foto_pre
                            if foto_perfil:
                                foto_url = otimizar_imagem_admin(foto_perfil)
                            elif not foto_url:
                                foto_url = "https://cdn-icons-png.flaticon.com/512/149/149071.png"

                            doc_ref = db.collection("profissionais").document()
                            doc_ref.set({
                                "nome": nome, "email": email, "whatsapp": limpar_whatsapp(whatsapp),
                                "area": area, "descricao": descricao, "foto_url": foto_url,
                                "aprovado": False, "saldo": 0, "cliques": 0,
                                "criado_em": datetime.now(fuso_br), "lat": LAT_REF, "lon": LON_REF,
                                "tipo_conta": "prestador"
                            })
                            st.success("✅ Cadastro enviado! Aguarde aprovação.")
                            st.session_state.pre_cadastro = None
                            time.sleep(2)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao cadastrar: {e}")

# ABA MEU PERFIL (TURBINADA - ESTILO REDE SOCIAL)
if 'perfil' in abas_dict:
    with menu_abas[abas_dict['perfil']]:
        if not st.session_state.auth:
            st.info("Faça login para ver seu perfil")
        else:
            user_id = st.session_state.user_id
            user_doc = db.collection("profissionais").document(user_id).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                
                # HEADER ESTILO REDE SOCIAL
                foto_perfil = safe_image_src(user_data.get('foto_url', ''))
                modo_noite_class = "dark-mode" if st.session_state.modo_noite else ""
                
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
                
                # ABAS INTERNAS MODERNAS
                tab_vitrine, tab_config, tab_ajuda = st.tabs(["🛍️ MINHA VITRINE", "⚙️ CONFIGURAÇÕES", "❓ AJUDA"])
                
                with tab_vitrine:
                    tipo_conta = user_data.get('tipo_conta', 'prestador')
                    if tipo_conta != 'comerciante':
                        st.info("💡 Você está no modo Prestador. Ative o modo Comerciante para vender produtos diretamente.")
                        if st.button("ATIVAR MODO COMERCIANTE", use_container_width=True):
                            db.collection("profissionais").document(user_id).update({"tipo_conta": "comerciante"})
                            st.success("Modo Comerciante activated!")
                            time.sleep(1)
                            st.rerun()
                    else:
                        produtos = user_data.get('produtos', [])
                        
                        # Grid de Produtos Existentes
                        if produtos:
                            st.markdown("#### Meus Produtos")
                            cols = st.columns(2)
                            for idx, prod in enumerate(produtos):
                                with cols[idx % 2]:
                                    st.markdown(f"""
                                    <div class="produto-card">
                                        <div style="display:flex; gap:10px; align-items:center;">
                                            <img src="{safe_image_src(prod.get('foto_b64'))}" style="width:60px; height:60px; border-radius:8px; object-fit:cover;">
                                            <div style="flex:1;">
                                                <div style="font-weight:bold;">{prod.get('nome')}</div>
                                                <div style="color:#25D366; font-weight:900;">R$ {prod.get('preco',0):.2f}</div>
                                            </div>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    if st.button(f"Remover {prod.get('nome')}", key=f"del_p_{idx}", use_container_width=True):
                                        produtos.pop(idx)
                                        db.collection("profissionais").document(user_id).update({"produtos": produtos})
                                        st.rerun()
                        
                        st.markdown("---")
                        # Formulário de Adição Moderno
                        with st.expander("➕ ADICIONAR NOVO PRODUTO", expanded=False):
                            with st.form("novo_produto_social", clear_on_submit=True):
                                p_nome = st.text_input("Nome do Produto")
                                c1, c2 = st.columns(2)
                                p_preco = c1.number_input("Preço R$", min_value=0.0, format="%.2f")
                                p_foto = c2.file_uploader("Foto", type=['jpg', 'jpeg', 'png'])
                                p_desc = st.text_area("Breve descrição")
                                p_destaque = st.checkbox("Destaque na busca")
                                
                                if st.form_submit_button("PUBLICAR PRODUTO", use_container_width=True):
                                    if p_nome and p_preco > 0 and p_foto:
                                        foto_b64 = otimizar_imagem_admin(p_foto)
                                        if foto_b64:
                                            novo_prod = {
                                                "nome": p_nome,
                                                "preco": float(p_preco),
                                                "desc": p_desc,
                                                "foto_b64": foto_b64,
                                                "ativo": True,
                                                "destaque": p_destaque,
                                                "criado_em": datetime.now(fuso_br)
                                            }
                                            produtos.append(novo_prod)
                                            db.collection("profissionais").document(user_id).update({"produtos": produtos})
                                            st.success("Produto publicado com sucesso!")
                                            time.sleep(1)
                                            st.rerun()
                                            
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
                                if img_b64:
                                    upd["foto_url"] = img_b64
                            db.collection("profissionais").document(user_id).update(upd)
                            st.success("Perfil atualizado!")
                            time.sleep(1)
                            st.rerun()
                    st.divider()
                    if st.button("🚪 SAIR DA CONTA", use_container_width=True):
                        st.session_state.auth = False
                        st.rerun()
                        
                with tab_ajuda:
                    st.markdown("#### Central de Ajuda")
                    st.write("Dúvidas sobre como melhorar seu perfil?")
                    st.info("💡 Perfis com fotos de alta qualidade e descrições detalhadas recebem 3x mais cliques!")
                    st.write("**Como funciona o saldo?**")
                    st.caption("Cada clique no seu botão de WhatsApp consome 1 moeda (💎). Recarregue com o administrador.")
                    st.link_button("FALAR COM SUPORTE", criar_link_zap(ZAP_ADMIN, "Olá, preciso de ajuda com meu perfil no GeralJá"))

# ABA FEEDBACK
if 'feedback' in abas_dict:
    with menu_abas[abas_dict['feedback']]:
        st.header("⭐ Avalie a Plataforma")
        st.write("Sua opinião nos ajuda a melhorar.")
        nota = st.slider("Nota", 1, 5, 5)
        comentario = st.text_area("O que podemos melhorar?")
        if st.button("Enviar Feedback"):
            st.success("Obrigado! Sua mensagem foi enviada para nossa equipe.")

# ==============================================================================
# CONTINUAÇÃO: ABA ADMIN & COMPONENTES FINAIS
# ==============================================================================

            st.header("👑 Painel de Administração")
            
            # Sub-abas do Administrador
            tab_validar, tab_moedas, tab_gerenciar = st.tabs(["📋 VALIDAR CADASTROS", "💎 ADICIONAR CRÉDITOS", "🛠️ CONFIGURAÇÕES SISTEMA"])
            
            with tab_validar:
                st.subheader("Profissionais Pendentes de Aprovação")
                pendentes = db.collection("profissionais").where("aprovado", "==", False).stream()
                
                count_p = 0
                for doc in pendentes:
                    count_p += 1
                    dados = doc.to_dict()
                    with st.expander(f"📋 {dados.get('nome')} — {dados.get('area')}"):
                        st.write(f"**E-mail:** {dados.get('email')}")
                        st.write(f"**WhatsApp:** {dados.get('whatsapp')}")
                        st.write(f"**Descrição:** {dados.get('descricao')}")
                        
                        col_adm1, col_adm2 = st.columns(2)
                        if col_adm1.button("✅ Aprovar", key=f"aprov_{doc.id}"):
                            db.collection("profissionais").document(doc.id).update({"aprovado": True})
                            st.success("Cadastro aprovado!")
                            time.sleep(0.5)
                            st.rerun()
                            
                        if col_adm2.button("🗑️ Recusar / Eliminar", key=f"recus_{doc.id}"):
                            db.collection("profissionais").document(doc.id).delete()
                            st.warning("Cadastro eliminado do sistema.")
                            time.sleep(0.5)
                            st.rerun()
                if count_p == 0:
                    st.info("Nenhum profissional pendente de aprovação por agora.")
                    
            with tab_moedas:
                st.subheader("Gestão de Saldo (Moedas 💎)")
                todos_profs = db.collection("profissionais").stream()
                opcoes_profs = {doc.to_dict().get('nome'): doc.id for doc in todos_profs if doc.to_dict().get('nome')}
                
                if opcoes_profs:
                    prof_selecionado = st.selectbox("Selecione o Profissional", options=list(opcoes_profs.keys()))
                    moedas_add = st.number_input("Quantidade de Moedas a Adicionar", min_value=1, value=10)
                    verificar_check = st.checkbox("Tornar este perfil Selo Verificado 🏆?")
                    
                    if st.button("💎 Confirmar Créditos", use_container_width=True):
                        p_id = opcoes_profs[prof_selecionado]
                        p_ref = db.collection("profissionais").document(p_id)
                        p_atual = p_ref.get().to_dict()
                        
                        novo_saldo = p_atual.get('saldo', 0) + moedas_add
                        update_dict = {"saldo": novo_saldo}
                        if verificar_check:
                            update_dict["verificado"] = True
                            
                        p_ref.update(update_dict)
                        st.success(f"Adicionadas {moedas_add} moedas a {prof_selecionado}! Novo saldo: {novo_saldo}")
                else:
                    st.warning("Nenhum profissional cadastrado no sistema.")

            with tab_gerenciar:
                st.subheader("Configurações do Grajaú Tem / GeralJá")
                
                # Editor de Categorias Oficiais Dinâmicas
                st.markdown("#### Categorias Disponíveis no App")
                cat_doc = db.collection("configuracoes").document("categorias").get()
                lista_atual_cats = cat_doc.to_dict().get("lista", CATEGORIAS_OFICIAIS) if cat_doc.exists else CATEGORIAS_OFICIAIS
                
                novas_cats_texto = st.text_area("Categorias separadas por vírgula:", value=", ".join(lista_atual_cats))
                if st.button("💾 Salvar Categorias"):
                    nova_lista = [c.strip() for c in novas_cats_texto.split(",") if c.strip()]
                    db.collection("configuracoes").document("categorias").set({"lista": nova_lista})
                    st.success("Lista de categorias atualizada!")

# ==============================================================================
# ABA FINANCEIRO (ESCONDIDA)
# ==============================================================================
if 'financeiro' in abas_dict:
    with menu_abas[abas_dict['financeiro']]:
        st.header("📊 Painel Financeiro e Comercial")
        st.write("Visão geral de pacotes e faturamento simulado de anúncios.")
        
        col_f1, col_f2, col_f3 = st.columns(3)
        col_f1.metric("Vitrine Unitária", "R$ 100")
        col_f2.metric("Vitrine Mensal", "R$ 600")
        col_f3.metric("Rádio Grajaú Tem", "R$ 300/mês")
        
        st.markdown("#### 📦 Tabela de Pacotes Atuais")
        st.markdown("""
        - **🥉 Bronze:** 1 post = **R$ 150**
        - **🥈 Prata:** 3 posts = **R$ 400**
        - **🥇 Ouro:** 10 posts = **R$ 700**
        """)
        
        st.info("Para fechamento oficial de anúncios, use os contactos de vendas integrados no motor.")

# ==============================================================================
# --- MÓDULO LOJA DE PRODUTOS / MARKETPLACE GERAL ---
# ==============================================================================
st.markdown("<br>", unsafe_allow_html=True)
st.divider()
st.subheader("🏪 Vitrine Geral de Produtos da Região")

loja_itens = db.collection("loja").stream()
lista_loja = []
for it_doc in loja_itens:
    it_dados = it_doc.to_dict()
    it_dados['id'] = it_doc.id
    lista_loja.append(it_dados)

if not lista_loja:
    st.info("Nenhum item em destaque na vitrine comum neste momento.")
else:
    cols_loja = st.columns(4)
    for idx, item in enumerate(lista_loja):
        with cols_loja[idx % 4]:
            st.image(safe_image_src(item.get('foto_b64')), use_container_width=True)
            st.markdown(f"**{item.get('nome')}** — Preço: `{item.get('preco')} Moedas` | Estoque: `{item.get('estoque')} un`")
            
            # Botão de remoção se for Administrador logado
            if comando == "abracadabra" or comando == "geralja_master":
                if st.button("🗑️", key=f"del_loja_{item['id']}"):
                    db.collection("loja").document(item['id']).delete()
                    st.success("Item removido.")
                    time.sleep(0.5)
                    st.rerun()

# ==============================================================================
# --- RODAPÉ INSTITUCIONAL (FORA DE QUALQUER ABA) ---
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
    <div style='text-align: right;'>
        <span style='font-size: 12px; font-weight: bold; color: #FF8C00;'>Versão 5.0 Social</span>
    </div>
    """, unsafe_allow_html=True)
