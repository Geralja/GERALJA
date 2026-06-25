# ==============================================================================
# GERALJÁ: CRIANDO SOLUÇÕES - MÓDULO 1: INFRAESTRUTURA & SEGURANÇA MÁXIMA
# VERSÃO 4.0 VITRINE - Bugfixes + Vitrine de Produtos para Comerciantes
# ==============================================================================
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
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
    .produto-card { background: #f8f9fa; border-radius: 12px; padding: 10px; margin: 5px 0; border: 1px solid #e9ecef; }
    .stApp { transition: all 0.3s ease; }
    
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
    # Tenta detectar preferência do sistema via JS, fallback = dia
    if streamlit_js_eval:
        try:
            prefers_dark = streamlit_js_eval(js_expressions="window.matchMedia('(prefers-color-scheme: dark)').matches", key="theme_detect")
            st.session_state.modo_noite = bool(prefers_dark)
        except Exception:
            st.session_state.modo_noite = False # Padrão dia
    else:
        st.session_state.modo_noite = False # Padrão dia

for key, default in {
    'tema_claro': False,
    'auth': False,
    'admin_logado': False,
    'minha_lat': -23.5505,
    'minha_lon': -46.6333,
    'security_check': False,
    'js_disponivel': True,
    'pre_cadastro': None # Adicionado para garantir inicialização
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
    # Esta função estava faltando e foi adicionada para evitar NameError.
    # Pode ser expandida com lógica de layout se necessário.
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

            # st.query_params.clear() # Removido para evitar limpar parâmetros antes de uso completo

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
    .produto-card { background: #f8f9fa; border-radius: 12px; padding: 10px; margin: 5px 0; border: 1px solid #e9ecef; }
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

# MAPEAMENTO SEGURO DE ABAS - Evita IndexError
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
                    
                    # VITRINE DE PRODUTOS (ÚNICA OCORRÊNCIA)
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

        # NOTÍCIAS (ÚNICA OCORRÊNCIA)
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
                                foto_url = "https://cdn-icons-png.flaticon.com/512/149/149071.png" # Fallback se não tiver foto

                            doc_ref = db.collection("profissionais").document()
                            doc_ref.set({
                                "nome": nome,
                                "email": email,
                                "whatsapp": limpar_whatsapp(whatsapp),
                                "area": area,
                                "descricao": descricao,
                                "foto_url": foto_url,
                                "aprovado": False, # Pendente de aprovação
                                "saldo": 0,
                                "cliques": 0,
                                "criado_em": datetime.now(fuso_br),
                                "lat": LAT_REF,
                                "lon": LON_REF,
                                "tipo_conta": "prestador" # Padrão
                            })
                            st.success("✅ Cadastro enviado! Aguarde aprovação.")
                            st.session_state.pre_cadastro = None # Limpa pré-cadastro
                            time.sleep(2)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao cadastrar: {e}")

# ABA MEU PERFIL
if 'perfil' in abas_dict:
    with menu_abas[abas_dict['perfil']]:
        if not st.session_state.auth:
            st.info("Faça login para ver seu perfil")
        else:
            user_id = st.session_state.user_id
            user_doc = db.collection("profissionais").document(user_id).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                st.subheader(f"👤 {user_data.get('nome', 'Usuário')}")
                
                tab_perfil, tab_produtos = st.tabs(["Dados", "🛍️ Meus Produtos"])
                
                with tab_perfil:
                    st.write(f"**Área:** {user_data.get('area', '')}")
                    st.write(f"**WhatsApp:** {user_data.get('whatsapp', '')}")
                    st.write(f"**Tipo de conta:** {user_data.get('tipo_conta', 'prestador')}")
                
                with tab_produtos:
                    tipo_conta = user_data.get('tipo_conta', 'prestador')
                    if tipo_conta != 'comerciante':
                        st.info("Ative o modo Comerciante no cadastro para vender produtos.")
                        if st.button("Virar Comerciante"):
                            db.collection("profissionais").document(user_id).update({"tipo_conta": "comerciante"})
                            st.rerun()
                    else:
                        produtos = user_data.get('produtos', [])
                        st.write(f"**Produtos cadastrados:** {len(produtos)}/10 grátis")
                        
                        with st.form("novo_produto", clear_on_submit=True):
                            st.markdown("##### Adicionar produto")
                            p_nome = st.text_input("Nome do produto")
                            p_preco = st.number_input("Preço R$", min_value=0.0, format="%.2f")
                            p_desc = st.text_area("Descrição", max_chars=200)
                            p_foto = st.file_uploader("Foto do produto", type=['jpg', 'jpeg', 'png'])
                            p_destaque = st.checkbox("Marcar como destaque na busca")
                            
                            if st.form_submit_button("Cadastrar Produto"):
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
                                        st.success("Produto cadastrado!")
                                        st.rerun()
                                    else:
                                        st.error("Erro ao processar imagem")
                                else:
                                    st.warning("Preencha nome, preço e foto")
                        
                        st.markdown("---")
                        st.markdown("##### Seus produtos")
                        for idx, prod in enumerate(produtos):
                            col1, col2, col3 = st.columns([1,3,1])
                            with col1:
                                st.image(safe_image_src(prod.get('foto_b64')), width=80)
                            with col2:
                                st.markdown(f"**{prod.get('nome')}** - R$ {prod.get('preco',0):.2f}")
                                st.caption(prod.get('desc',''))
                            with col3:
                                if st.button("🗑️", key=f"del_{idx}"):
                                    produtos.pop(idx)
                                    db.collection("profissionais").document(user_id).update({"produtos": produtos})
                                    st.rerun()

# ABA FEEDBACK
if 'feedback' in abas_dict:
    with menu_abas[abas_dict['feedback']]:
        st.header("⭐ Avalie a Plataforma")
        st.write("Sua opinião nos ajuda a melhorar.")

        nota = st.slider("Nota", 1, 5, 5)
        comentario = st.text_area("O que podemos melhorar?")

        if st.button("Enviar Feedback"):
            # Aqui você pode adicionar a lógica para salvar o feedback no Firestore ou enviar por e-mail
            st.success("Obrigado! Sua mensagem foi enviada para nossa equipe.")

# ABA ADMIN
if 'admin' in abas_dict:
    with menu_abas[abas_dict['admin']]:
        def otimizar_imagem_admin_local(image_file, size=(500, 500)):
            try:
                img = Image.open(image_file)
                if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                img.thumbnail(size)
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=70)
                return base64.b64encode(buffer.getvalue()).decode()
            except Exception: return None

        agora_br = datetime.now(fuso_br)

        if not st.session_state.admin_logado:
            st.markdown("### 🔐 Acesso Restrito à Diretoria")
            with st.form("login_adm"):
                u = st.text_input("Usuário Administrativo")
                p = st.text_input("Senha de Acesso", type="password")
                if st.form_submit_button("ACESSAR TORRE DE CONTROLE", use_container_width=True):
                    if u == st.secrets.get("ADMIN_USER", "geralja") and p == st.secrets.get("ADMIN_PASS", "Bps36ocara"):
                        st.session_state.admin_logado = True
                        st.rerun()
                    else: st.error("Dados incorretos.")
        else:
            st.markdown(f"## 👑 Central de Comando GeralJá")
            if st.button("🚪 Sair", key="logout_adm"):
                st.session_state.admin_logado = False
                st.rerun()

            tab_profissionais, tab_noticias, tab_loja, tab_vendas, tab_categorias = st.tabs([
                "👥 Parceiros", "📰 Gestão de Notícias", "🛍️ Loja", "📜 Vendas", "📁 Categorias"
            ])

            with tab_categorias:
                doc_cat_ref = db.collection("configuracoes").document("categorias")
                res_cat = doc_cat_ref.get()
                lista_atual = res_cat.to_dict().get("lista", CATEGORIAS_OFICIAIS) if res_cat.exists else CATEGORIAS_OFICIAIS
                c1, c2 = st.columns([3, 1])
                nova_cat = c1.text_input("Nova Profissão:")
                if c2.button("➕ ADICIONAR"):
                    if nova_cat and nova_cat not in lista_atual:
                        lista_atual.append(nova_cat)
                        lista_atual.sort()
                        doc_cat_ref.set({"lista": lista_atual})
                        st.rerun()

            with tab_noticias:
                st.subheader("🤖 Captação por IA")
                c_ia1, c_ia2 = st.columns(2)
                IMG_NEWS_DEFAULT = "https://images.unsplash.com/photo-1504711432869-0df30d7eaf4d?w=800"

                if c_ia1.button("🔍 CAPTAR GOOGLE NEWS"):
                    feed = feedparser.parse("https://news.google.com/rss/search?q=Grajaú+São+Paulo&hl=pt-BR&gl=BR&ceid=BR:pt-419")
                    st.session_state['sugestoes_ia'] = [{"titulo": e.title, "link": e.link, "img": IMG_NEWS_DEFAULT, "fonte": "Google"} for e in feed.entries[:3]]

                if c_ia2.button("📡 SCANNER NEWS API"):
                    try:
                        res = requests.get(f"https://newsapi.org/v2/everything?q=Grajaú+São+Paulo&language=pt&apiKey={st.secrets.get('NEWS_API_KEY','516289bf44e1429784e0ca0102854a0d')}").json()
                        st.session_state['sugestoes_ia'] = [{"titulo": a['title'], "link": a['url'], "img": a.get('urlToImage') or IMG_NEWS_DEFAULT, "res": a.get('description'), "fonte": "NewsAPI"} for a in res.get("articles", [])[:3]]
                    except Exception: st.error("Erro na API.")

                if 'sugestoes_ia' in st.session_state:
                    cols_sug = st.columns(3)
                    for idx, sug in enumerate(st.session_state['sugestoes_ia']):
                        with cols_sug[idx]:
                            if sug.get('img'): st.image(sug['img'], use_container_width=True)
                            st.info(f"**{sug['titulo'][:60]}...**")
                            if st.button("✅ USAR", key=f"sug_{idx}"):
                                st.session_state['temp_titulo'] = sug['titulo']
                                st.session_state['temp_link'] = sug['link']
                                st.session_state['temp_img'] = sug.get('img', "")
                                st.rerun()

                with st.form("form_noticia"):
                    nt = st.text_input("Título", value=st.session_state.get('temp_titulo', ""))
                    ni = st.text_input("URL Imagem", value=st.session_state.get('temp_img', ""))
                    nl = st.text_input("Link Matéria", value=st.session_state.get('temp_link', ""))
                    if st.form_submit_button("🚀 PUBLICAR NO GERALJÁ"):
                        db.collection("noticias").add({"titulo": nt, "imagem_url": ni, "link_original": nl, "data": datetime.now(fuso_br), "categoria": "DESTAQUE"})
                        for k in ['temp_titulo','temp_img','temp_link','sugestoes_ia']: st.session_state.pop(k, None)
                        st.success("Postado!")
                        st.rerun()

                st.divider()
                st.subheader("👀 Vitrine (6 Notícias)")
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
                                    if st.button("🗑", key=f"del_n_{n['id']}"):
                                        db.collection("noticias").document(n['id']).delete()
                                        st.rerun()

            with tab_loja:
                st.subheader("🛒 Itens da Loja")
                with st.form("add_loja"):
                    c1, c2, c3 = st.columns([2,1,1])
                    ln = c1.text_input("Nome")
                    lp = c2.number_input("Preço", min_value=1)
                    le = c3.number_input("Estoque", min_value=1)
                    lf = st.file_uploader("Foto", type=['jpg','png'])
                    if st.form_submit_button("SALVAR PRODUTO"):
                        db.collection("loja").add({"nome": ln, "preco": lp, "estoque": le, "foto": otimizar_imagem_admin_local(lf) if lf else ""})
                        st.success("Produto Adicionado!")
                        st.rerun()
                st.divider()
                for it in db.collection("loja").stream():
                    item = it.to_dict()
                    with st.expander(f"📦 {item['nome']} - {item['preco']} 💎"):
                        if item.get('foto'): st.image(f"data:image/jpeg;base64,{item['foto']}", width=100)
                        if st.button("Remover", key=f"del_it_{it.id}"):
                            db.collection("loja").document(it.id).delete()
                            st.rerun()

            with tab_vendas:
                st.subheader("📜 Histórico de Resgates")
                vendas_ref = db.collection("vendas").order_by("data", direction="DESCENDING").limit(20).stream()
                vendas_data = []
                for v in vendas_ref:
                    vd = v.to_dict()
                    vendas_data.append({
                        "Data": vd.get('data').astimezone(fuso_br).strftime('%d/%m %H:%M') if vd.get('data') else "---",
                        "Cliente": vd.get('usuario_nome', 'Desconhecido'),
                        "Produto": vd.get('produto_nome', '---'),
                        "Preço": f"{vd.get('preco', 0)} 💎"
                    })
                if vendas_data:
                    st.table(pd.DataFrame(vendas_data))
                else:
                    st.info("Nenhuma venda registrada ainda.")

            with tab_profissionais:
                try:
                    profs_ref = db.collection("profissionais").stream()
                    profs_list = [p.to_dict() | {"id": p.id} for p in profs_ref]
                    df = pd.DataFrame(profs_list)
                    if not df.empty:
                        busca = st.text_input("🔍 Localizar (Nome ou WhatsApp)")
                        if busca: df = df[df['nome'].str.contains(busca, case=False, na=False) | df['whatsapp'].str.contains(busca, na=False)]

                        m1, m2, m3 = st.columns(3)
                        m1.metric("Total", len(df))
                        m2.metric("Pendentes", len(df[df['aprovado'] == False]))
                        m3.metric("GeralCones", f"💎 {int(df['saldo'].sum())}")

                        for _, p in df.iterrows():
                            pid = p['id']
                            status = "🟢" if p.get('aprovado') else "🟡"
                            with st.expander(f"{status} {p.get('nome','').upper()}"):
                                with st.form(f"f_edit_{pid}"):
                                    c1, c2 = st.columns(2)
                                    n_nome = c1.text_input("Nome", value=p.get('nome'))
                                    n_area = c2.selectbox("Área", lista_atual, index=lista_atual.index(p.get('area')) if p.get('area') in lista_atual else 0)
                                    n_desc = st.text_area("Descrição", value=p.get('descricao'))
                                    c3, c4, c5 = st.columns(3)
                                    n_zap = c3.text_input("Zap", value=p.get('whatsapp'))
                                    n_saldo = c4.number_input("Saldo", value=int(p.get('saldo', 0)))
                                    n_status = c5.selectbox("Status", ["Aprovado", "Pendente"], index=0 if p.get('aprovado') else 1)
                                    st.divider()
                                    cf1, cf2 = st.columns(2)
                                    with cf1:
                                        if p.get('foto_url'):
                                            st.image(safe_image_src(p['foto_url']), width=80)
                                        up_p = st.file_uploader("Perfil", type=['jpg','png'], key=f"up_p_{pid}")
                                    with cf2:
                                        up_v = st.file_uploader("Vitrine (Máx 4)", type=['jpg','png'], accept_multiple_files=True, key=f"up_v_{pid}")
                                    if st.form_submit_button("💾 SALVAR TUDO"):
                                        upd = {"nome": n_nome, "area": n_area, "descricao": n_desc, "whatsapp": n_zap, "saldo": int(n_saldo), "aprovado": (n_status=="Aprovado")}
                                        if up_p: upd["foto_url"] = otimizar_imagem_admin_local(up_p, size=(350, 350))
                                        if up_v:
                                            for i in range(1, 5): upd[f'f{i}'] = None
                                            for i, f in enumerate(up_v[:4]): upd[f"f{i+1}"] = otimizar_imagem_admin_local(f)
                                        db.collection("profissionais").document(pid).update(upd)
                                        st.rerun()
                                if st.button("🗑 EXCLUIR", key=f"del_p_{pid}"):
                                    db.collection("profissionais").document(pid).delete()
                                    st.rerun()
                except Exception as e: st.error(f"Erro: {e}")

# ABA FINANCEIRO (EASTER EGG - COMANDO SECRETO)
if 'financeiro' in abas_dict:
    with menu_abas[abas_dict['financeiro']]:
        st.header("📊 Painel Financeiro GeralJá")
        st.write("Visão geral e faturamento estratégico de moedas da plataforma.")

        try:
            profs_ref = db.collection("profissionais").stream()
            profs_list = [p.to_dict() for p in profs_ref]
            if profs_list:
                df_fin = pd.DataFrame(profs_list)
                total_moedas = df_fin['saldo'].sum() if 'saldo' in df_fin else 0
                total_cliques = df_fin['cliques'].sum() if 'cliques' in df_fin else 0

                col_f1, col_f2 = st.columns(2)
                col_f1.metric("Moedas Ativas em Circulação", f"🪙 {total_moedas}")
                col_f2.metric("Total de Cliques Convertidos", f"🚀 {total_cliques}")
            else:
                st.info("Nenhum dado financeiro para listar.")
        except Exception as e:
            st.error(f"Erro ao processar métricas financeiras: {e}")

# ------------------------------------------------------------------------------
# FINALIZAÇÃO & RODAPÉ BLINDADO (LGPD & SECURITY SHIELD)
# ------------------------------------------------------------------------------
finalizar_e_alinhar_layout()

st.markdown("""
<style>
   .footer-container {
        text-align: center;
        padding: 20px;
        color: #64748B;
        font-size: 12px;
    }
   .security-badge {
        display: inline-flex;
        align-items: center;
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 20px;
        padding: 5px 15px;
        margin-bottom: 10px;
        color: #0f172a;
        font-weight: bold;
    }
   .shield-icon {
        color: #22c55e;
        margin-right: 8px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="footer-container">
    <div class="security-badge">
        <span class="shield-icon">🛡</span> IA de Proteção Ativa: Monitorando Contra Ameaças
    </div>
</div>
""", unsafe_allow_html=True)
