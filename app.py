  # ==============================================================================
# GERALJÁ: CRIANDO SOLUÇÕES - MÓDULO 1: INFRAESTRUTURA & SEGURANÇA MÁXIMA
# VERSÃO 5.1 COMPLETA E INTEGRAL - Correção de Imagens, Busca por Tolerância e Fix Line 647
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
from difflib import SequenceMatcher

# --- BIBLIOTECAS NÍVEL 5.0 ---
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

# --- CONFIGURAÇÃO DE PÁGINA ---
st.set_page_config(
    page_title="GeralJá | Criando Soluções",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS RESPONSIVO E MODO DIA/NOITE ADAPTÁVEL ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .main .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
    #MainMenu, footer, header { visibility: hidden; }
    
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
    .produto-card { background: #f8f9fa; border-radius: 12px; padding: 10px; margin: 5px 0; border: 1px solid #e9ecef; color: #333; text-align: center; }
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
    'pre_cadastro': {},
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
        if not codigo_bruto: return ""
        limpo = codigo_bruto.replace('\u00a0', ' ').replace('\xa0', ' ')
        return ''.join(ch for ch in limpo if ch in '\n\t\r' or ord(ch) >= 32)

engine = GeralJaEngine()
fuso_br = engine.fuso

# ------------------------------------------------------------------------------
# CONFIGURAÇÃO DE CHAVES
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

# ------------------------------------------------------------------------------
# CONEXÃO FIREBASE
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
# FUNÇÕES AUXILIARES E TRATAMENTO DE IMAGENS
# ------------------------------------------------------------------------------
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
    """Garante carregamento seguro de imagens Base64 ou URLs externas"""
    if not valor:
        return "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    v = str(valor).strip()
    if v.startswith("http://") or v.startswith("https://"):
        return v
    if v.startswith("data:image"):
        return v
    return f"data:image/jpeg;base64,{v}"

def otimizar_imagem_admin(imagem_upload, size=(600, 600)):
    """Compacta e converte imagem enviada para Base64 leve"""
    try:
        img = Image.open(imagem_upload)
        if img.mode in ("RGBA", "P"):
            img = img.convert('RGB')
        img.thumbnail(size)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=75)
        return base64.b64encode(buffer.getvalue()).decode()
    except Exception:
        return None

def similaridade_texto(a, b):
    return SequenceMatcher(None, normalizar(a), normalizar(b)).ratio()

def processar_ia_avancada(texto):
    """Busca inteligente com tolerância a erros de digitação (Fuzzy Match + IA)"""
    if not texto: return "Outro (Personalizado)"
    t_clean = normalizar(texto)
    
    # 1. Checagem em conceitos expandidos por palavras exatas ou parciais
    for chave, categoria in CONCEITOS_EXPANDIDOS.items():
        if normalizar(chave) in t_clean or t_clean in normalizar(chave):
            return categoria
            
    # 2. Tolerância a Erros de Digitação (Fuzzy Comparison)
    melhor_cat = None
    maior_score = 0.0
    
    for cat in CATEGORIAS_OFICIAIS:
        score = similaridade_texto(t_clean, cat)
        if score > maior_score:
            maior_score = score
            melhor_cat = cat

    for chave, categoria in CONCEITOS_EXPANDIDOS.items():
        score = similaridade_texto(t_clean, chave)
        if score > maior_score:
            maior_score = score
            melhor_cat = categoria

    if maior_score >= 0.55: # 55% de similaridade tolera erros como "eletricsta", "pisa"
        return melhor_cat

    # 3. Fallback para Groq IA se disponível
    try:
        if client_groq:
            prompt = f"O usuário buscou com possível erro de digitação: '{texto}'. Escolha a categoria exata mais próxima dentre estas: {CATEGORIAS_OFICIAIS}. Responda APENAS o nome da categoria."
            res = client_groq.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
                temperature=0.1
            )
            cat_ia = res.choices[0].message.content.strip()
            if cat_ia in CATEGORIAS_OFICIAIS:
                return cat_ia
    except Exception:
        pass
        
    return melhor_cat if melhor_cat else "Outro (Personalizado)"

def criar_link_zap(numero, msg):
    return f"https://api.whatsapp.com/send?phone={numero}&text={urllib.parse.quote(msg)}"

# ==============================================================================
# BLOCO B: CONSTANTES E AUTENTICAÇÃO
# ==============================================================================
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
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
    "pizza": "Pizzaria", "pizzaria": "Pizzaria", "pisa": "Pizzaria", "fome": "Pizzaria", "massa": "Pizzaria",
    "lanche": "Lanchonete", "hamburguer": "Lanchonete", "burger": "Lanchonete", "salgado": "Lanchonete",
    "comida": "Restaurante", "almoco": "Restaurante", "marmita": "Restaurante", "jantar": "Restaurante",
    "doce": "Doceria", "acai": "Açaí", "sorvete": "Sorveteria", "cerveja": "Adega", "bebida": "Adega",
    "roupa": "Loja de Roupas", "moda": "Loja de Roupas", "sapato": "Calçados", "tenis": "Calçados",
    "presente": "Loja de Variedades", "relogio": "Relojoaria", "joia": "Joalheria",
    "remedio": "Farmácia", "farmacia": "Farmácia", "cabelo": "Barbearia/Salão", "unha": "Barbearia/Salão",
    "celular": "Assistência Técnica", "iphone": "Assistência Técnica", "computador": "TI", "pc": "TI",
    "geladeira": "Refrigeração", "ar condicionado": "Refrigeração", "fogao": "Técnico de Fogão",
    "tv": "Eletrônicos", "pet": "Pet Shop", "racao": "Pet Shop", "cachorro": "Pet Shop",
    "vazamento": "Encanador", "cano": "Encanador", "curto": "Eletricista", "luz": "Eletricista", "eletricsta": "Eletricista",
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
</style>
"""
st.markdown(estilo_dinamico, unsafe_allow_html=True)

# Header Banner
st.markdown('<div class="header-container"><span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span><br><span class="sub-logo">BRASIL ELITE EDITION — GRAJAÚ TEM</span></div>', unsafe_allow_html=True)

# Configuração de Abas
lista_abas = ["🔍 BUSCAR", "🚀 CADASTRAR", "👤 MEU PERFIL", "⭐ FEEDBACK"]

with st.sidebar:
    st.markdown("### 🔐 Acesso Administrativo")
    comando = st.text_input("Código de Acesso", type="password", key="admin_key", placeholder="Digite o código")
    if comando in ["abracadabra", "geralja_master"]:
        if "👑 ADMIN" not in lista_abas: lista_abas.append("👑 ADMIN")
    if comando in ["financeiro2026", "geralja_master"]:
        if "📊 FINANCEIRO" not in lista_abas: lista_abas.append("📊 FINANCEIRO")

menu_abas = st.tabs(lista_abas)

abas_dict = {}
for i, nome in enumerate(lista_abas):
    if "BUSCAR" in nome: abas_dict['buscar'] = i
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
        st.markdown("### 🏙️ O que você precisa no Grajaú?")
        
        with st.expander("📍 Seus dados de Localização (GPS)", expanded=False):
            if get_geolocation:
                try:
                    loc = get_geolocation(component_key="geo_high_prec") 
                    if loc and 'coords' in loc:
                        st.session_state.minha_lat = loc['coords']['latitude']
                        st.session_state.minha_lon = loc['coords']['longitude']
                        st.success(f"GPS Ativo (Precisão: {loc['coords'].get('accuracy', 0):.0f}m)")
                    else:
                        st.warning("GPS indisponível. Usando localização padrão do bairro.")
                except Exception:
                    st.warning("Recurso GPS indisponível no navegador.")
            else:
                st.info("GPS não suportado neste dispositivo.")

        minha_lat = st.session_state.minha_lat
        minha_lon = st.session_state.minha_lon

        c1, c2 = st.columns([3, 1])
        termo_busca = c1.text_input("Ex: 'Cano estourado', 'eletricsta' ou 'Pizzaria'", key="main_search_v51")
        raio_km = c2.select_slider("Raio (KM)", options=[1, 3, 5, 10, 20, 50, 500], value=5)

        if termo_busca:
            with st.status("🔍 Buscando parceiros...", expanded=False) as status:
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
                status.update(label=f"Resultados encontrados para: **{cat_ia}**", state="complete")

            if not lista_ranking:
                st.warning(f"Nenhum profissional de '{cat_ia}' encontrado no raio de {raio_km}km.")
            else:
                for p in lista_ranking:
                    f_perfil = safe_image_src(p.get('foto_url', ''))
                    is_elite = p['score_elite'] > 0
                    cor_borda = "#FFD700" if is_elite else "#0047AB"
                    zap_num = limpar_whatsapp(p.get('whatsapp',''))
                    zap_link = criar_link_zap(zap_num, "Olá! Vi seu perfil no aplicativo GeralJá e gostaria de um orçamento.")

                    col_prof1, col_prof2 = st.columns([1, 4])
                    with col_prof1:
                        st.image(f_perfil, use_container_width=True)
                    with col_prof2:
                        st.markdown(f"### {str(p.get('nome','')).upper()} {'🏆 DESTAQUE ELITE' if is_elite else ''}")
                        st.caption(f"📍 a {p['dist']:.1f} km • Especialidade: **{p.get('area')}**")
                        st.write(p.get('descricao', ''))

                    # VITRINE DE PRODUTOS DO COMERCIANTE (RENDERIZAÇÃO NATIVA E SEGURA DE IMAGENS)
                    produtos = p.get('produtos', [])
                    produtos_ativos = [pr for pr in produtos if pr.get('ativo', True)][:4]
                    
                    if produtos_ativos and p.get('tipo_conta') == 'comerciante':
                        st.markdown("**🛍️ Produtos / Ofertas da Loja:**")
                        cols_prod = st.columns(min(len(produtos_ativos), 4))
                        for idx, prod in enumerate(produtos_ativos):
                            with cols_prod[idx]:
                                img_p = safe_image_src(prod.get('foto_b64', ''))
                                st.image(img_p, use_container_width=True)
                                st.markdown(f"<div class='produto-card'><b>{prod.get('nome','')}</b><br>R$ {prod.get('preco',0):.2f}</div>", unsafe_allow_html=True)
                                link_prod = criar_link_zap(zap_num, f"Olá! Vi no GeralJá e quero pedir 1x {prod.get('nome','')}")
                                st.link_button("Pedir no Zap", link_prod, use_container_width=True)

                    st.markdown(f'<a href="{zap_link}" target="_blank" style="display:block; background:#25D366; color:white; text-align:center; padding:10px; border-radius:10px; text-decoration:none; font-weight:bold; margin-bottom:20px;">💬 CHAMAR NO WHATSAPP</a>', unsafe_allow_html=True)
                    st.divider()

        st.markdown("---")
        st.subheader("📰 Plantão de Notícias Coletivas — Grajaú Tem")
        
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
                    fonte = n.source.get('title', 'Grajaú Tem') if hasattr(n, 'source') else 'Notícias Locais'
                    st.markdown(f"""
                    <a href="{n.link}" target="_blank" style="text-decoration:none; color:inherit;">
                        <div style="border:1px solid #E2E8F0; border-radius:12px; overflow:hidden; height:280px; background:white; padding:10px; color:#1A202C;">
                            <img src="{img}" style="width:100%; height:100px; object-fit:cover; border-radius:8px;">
                            <p style="font-size:12px; font-weight:700; margin-top:8px; line-height:1.3;">{n.title[:75]}...</p>
                            <p style="font-size:10px; color:#718096; margin-top:8px;">📍 {fonte}</p>
                        </div>
                    </a>
                    """, unsafe_allow_html=True)

# ==============================================================================
# ABA 2: 🚀 CADASTRAR OU EDITAR (FIX DA LINHA 647/DICIONÁRIO NULO)
# ==============================================================================
if 'cadastrar' in abas_dict:
    with menu_abas[abas_dict['cadastrar']]:
        st.header("🚀 Cadastre-se ou Atualize seu Perfil")
        st.write("Apareça para milhares de moradores do Grajaú e região!")

        # CORREÇÃO CRÍTICA LINHA 647: Evita AttributeError quando pre_cadastro for None
        dados_google = st.session_state.get("pre_cadastro") or {}
        email_inicial = dados_google.get("email", "") if isinstance(dados_google, dict) else ""
        nome_inicial = dados_google.get("nome", "") if isinstance(dados_google, dict) else ""
        foto_google = dados_google.get("foto", "") if isinstance(dados_google, dict) else ""

        doc_cat = db.collection("configuracoes").document("categorias").get()
        lista_cats = doc_cat.to_dict().get("lista", CATEGORIAS_OFICIAIS) if doc_cat.exists else CATEGORIAS_OFICIAIS

        with st.form("form_profissional_completo"):
            st.caption("💡 Se você já tem cadastro, informe seu mesmo WhatsApp para atualizar dados.")

            col1, col2 = st.columns(2)
            nome_input = col1.text_input("Nome Profissional ou Comercial", value=nome_inicial)
            zap_input = col2.text_input("WhatsApp (apenas números com DDD)", help="Ex: 11980168513")

            email_input = st.text_input("E-mail (Para login via Google)", value=email_inicial)

            col3, col4 = st.columns(2)
            cat_input = col3.selectbox("Sua Especialidade Principal", lista_cats)
            senha_input = col4.text_input("Sua Senha de Acesso", type="password")

            desc_input = st.text_area("Descrição dos Serviços/Produtos (máx. 400 caracteres)", max_chars=400)
            tipo_input = st.radio("Tipo de Conta", ["👨‍🔧 Profissional Autônomo / Prestador", "🏢 Comércio / Loja"], horizontal=True)

            foto_upload = st.file_uploader("Foto de Perfil ou Logo da Empresa", type=['png', 'jpg', 'jpeg'])
            termos_check = st.checkbox("Concordo com os Termos de Uso e Política de Privacidade do GeralJá", value=True)

            btn_salvar = st.form_submit_button("✅ SALVAR / CONCLUIR CADASTRO", use_container_width=True)

        if btn_salvar:
            zap_limpo = limpar_whatsapp(zap_input)
            
            if not termos_check:
                st.error("⚠️ Você precisa aceitar os termos de uso.")
            elif not nome_input or not zap_limpo or not senha_input or not desc_input:
                st.warning("⚠️ Nome, WhatsApp, Senha e Descrição são obrigatórios!")
            else:
                try:
                    with st.spinner("Gravando no banco de dados do GeralJá..."):
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
                            "saldo": dados_antigos.get("saldo", BONUS_WELCOME),
                            "data_cadastro": dados_antigos.get("data_cadastro", datetime.now(fuso_br).strftime("%d/%m/%Y")),
                            "aprovado": True,
                            "cliques": dados_antigos.get("cliques", 0),
                            "lat": st.session_state.get('minha_lat', LAT_REF),
                            "lon": st.session_state.get('minha_lon', LON_REF)
                        }

                        doc_ref.set(dados_pro)

                        st.session_state.auth = True
                        st.session_state.user_id = zap_limpo
                        st.session_state.pre_cadastro = {}

                        st.balloons()
                        st.success(f"✅ Perfil salvo com sucesso!")
                        time.sleep(1)
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Erro ao processar o cadastro: {e}")

# ==============================================================================
# ABA 3: 👤 MEU PERFIL / PAINEL DO PARCEIRO
# ==============================================================================
if 'perfil' in abas_dict:
    with menu_abas[abas_dict['perfil']]:
        if not st.session_state.auth:
            st.subheader("🚀 Acesso ao Painel do Parceiro")
            
            col1, col2 = st.columns(2)
            l_zap = col1.text_input("WhatsApp Cadastrado", key="login_zap_geralja_v10", placeholder="Ex: 11980168513")
            l_pw = col2.text_input("Senha", type="password", key="login_pw_geralja_v10")

            if st.button("ENTRAR NO PAINEL", key="btn_entrar_geralja_v10", use_container_width=True):
                try:
                    zap_busca = limpar_whatsapp(l_zap)
                    u = db.collection("profissionais").document(zap_busca).get()
                    if u.exists:
                        dados_user = u.to_dict()
                        if str(dados_user.get('senha')) == str(l_pw):
                            st.session_state.auth = True
                            st.session_state.user_id = u.id
                            st.success("Login realizado com sucesso!")
                            st.rerun()
                        else: 
                            st.error("❌ Senha incorreta.")
                    else: 
                        st.error("❌ WhatsApp não localizado no cadastro.")
                except Exception as e: 
                    st.error(f"Erro ao acessar banco: {e}")
        else:
            user_id = st.session_state.user_id
            user_doc = db.collection("profissionais").document(user_id).get()
            
            if user_doc.exists:
                user_data = user_doc.to_dict()
                foto_perfil = safe_image_src(user_data.get('foto_url', ''))
                
                col_u1, col_u2 = st.columns([1, 4])
                with col_u1:
                    st.image(foto_perfil, width=110)
                with col_u2:
                    st.markdown(f"## {user_data.get('nome', 'Usuário')} ✅")
                    st.caption(f"Especialidade: **{user_data.get('area')}** | Saldo: **🪙 {user_data.get('saldo',0)} GeralCoins**")
                    st.write(user_data.get('descricao', ''))

                tab_vitrine, tab_config = st.tabs(["🛍️ MINHA VITRINE COMERCIAL", "⚙️ CONFIGURAÇÕES"])
                
                with tab_vitrine:
                    tipo_conta = user_data.get('tipo_conta', 'prestador')
                    if tipo_conta != 'comerciante':
                        st.info("💡 Ative o Modo Comerciante para cadastrar e vender produtos.")
                        if st.button("ATIVAR MODO COMERCIANTE GRATUITAMENTE", use_container_width=True):
                            db.collection("profissionais").document(user_id).update({"tipo_conta": "comerciante"})
                            st.rerun()
                    else:
                        produtos = user_data.get('produtos', [])
                        
                        with st.expander("➕ ADICIONAR NOVO PRODUTO À VITRINE", expanded=True):
                            with st.form("novo_produto_form", clear_on_submit=True):
                                p_nome = st.text_input("Nome do Produto / Oferta")
                                c1, c2 = st.columns(2)
                                p_preco = c1.number_input("Preço (R$)", min_value=0.0, format="%.2f")
                                p_foto = c2.file_uploader("Foto do Produto", type=['jpg', 'jpeg', 'png'])
                                p_desc = st.text_area("Breve descrição", max_chars=150)
                                
                                if st.form_submit_button("PUBLICAR PRODUTO", use_container_width=True):
                                    if p_nome and p_preco > 0 and p_foto:
                                        foto_b64 = safe_image_src(otimizar_imagem_admin(p_foto, size=(400, 400)))
                                        novo_prod = {
                                            "nome": p_nome,
                                            "preco": float(p_preco),
                                            "desc": p_desc,
                                            "foto_b64": foto_b64,
                                            "ativo": True,
                                            "criado_em": datetime.now(fuso_br).isoformat()
                                        }
                                        produtos.append(novo_prod)
                                        db.collection("profissionais").document(user_id).update({"produtos": produtos})
                                        st.success("Produto cadastrado com sucesso!")
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.warning("Preencha o nome, um preço e envie uma foto.")

                        st.divider()
                        if produtos:
                            st.markdown("#### Seus Produtos Cadastrados")
                            for idx, prod in enumerate(produtos):
                                c_img, c_txt, c_btn = st.columns([1, 3, 1])
                                with c_img:
                                    st.image(safe_image_src(prod.get('foto_b64')), width=80)
                                with c_txt:
                                    st.markdown(f"**{prod.get('nome')}** — `R$ {prod.get('preco', 0):.2f}`")
                                    st.caption(prod.get('desc', ''))
                                with c_btn:
                                    if st.button("🗑️ Remover", key=f"del_prod_soc_{idx}"):
                                        produtos.pop(idx)
                                        db.collection("profissionais").document(user_id).update({"produtos": produtos})
                                        st.rerun()

                with tab_config:
                    if st.button("🚪 DESCONECTAR / SAIR", use_container_width=True):
                        st.session_state.auth = False
                        st.session_state.user_id = None
                        st.rerun()

# ==============================================================================
# ABA 4: ⭐ FEEDBACK
# ==============================================================================
if 'feedback' in abas_dict:
    with menu_abas[abas_dict['feedback']]:
        st.header("⭐ Avalie o Aplicativo GeralJá")
        with st.form("form_feedback"):
            nome_fb = st.text_input("Seu Nome (Opcional)")
            nota = st.select_slider("Nota", options=[1, 2, 3, 4, 5], value=5)
            comentario = st.text_area("O que você achou do app?")
            if st.form_submit_button("ENVIAR AVALIAÇÃO", use_container_width=True):
                if comentario:
                    db.collection("feedbacks").add({"nome": nome_fb or "Anônimo", "nota": nota, "comentario": comentario, "data": datetime.now(fuso_br)})
                    st.success("Obrigado pelo seu feedback!")

# ==============================================================================
# ABA 5: 👑 ADMIN
# ==============================================================================
if 'admin' in abas_dict:
    with menu_abas[abas_dict['admin']]:
        st.markdown("## 👑 Central Administradora GeralJá")
        st.info("Painel de controle ativo para moderação de parceiros e sistema.")

# RODAPÉ
st.markdown("---")
st.caption("© 2026 GeralJá & Grajaú Tem — Conectando o bairro e gerando oportunidades.")
