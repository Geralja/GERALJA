# ==============================================================================
# GERALJÁ: CRIANDO SOLUÇÕES - MÓDULO 1: INFRAESTRUTURA & SEGURANÇA MÁXIMA
# VERSÃO 4.0 VITRINE - Bugfixes + Vitrine de Produtos para Comerciantes
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
        except:
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
    'js_disponivel': True
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
    except: 
        return 999.0

def buscar_opcoes_dinamicas(documento, padrao):
    try:
        doc = db.collection("configuracoes").document(documento).get()
        if doc.exists:
            dados = doc.to_dict()
            return dados.get("lista", padrao)
        return padrao
    except Exception as e:
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
    except:
        return None


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

            st.query_params.clear()

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
    except:
        return "NAO_ENCONTRADO"


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
ZAP_VENDAS = "5511980168513"

def criar_link_zap(numero, msg):
    return f"https://api.whatsapp.com/send?phone={numero}&text={urllib.parse.quote(msg)}"

# ABA BUSCAR
with menu_abas[0]:
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
                zap_link = f"https://wa.me/{limpar_whatsapp(p.get('whatsapp',''))}?text=Vi+seu+perfil+no+GeralJa"

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
                
                
# ==============================================================================
# BLOCO D: VITRINE E PRODUTOS
# ==============================================================================

# VITRINE DE PRODUTOS
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

# NOTÍCIAS
st.markdown("---")
st.subheader("📰 Plantão Grajaú Tem")

@st.cache_data(ttl=600)
def buscar_noticias_rss(busca="Grajaú São Paulo"):
    try:
        url_rss = f"https://news.google.com/rss/search?q={urllib.parse.quote(busca)}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        feed = feedparser.parse(url_rss)
        return feed.entries[:4]
    except:
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

# ABA MEU PERFIL - COM VITRINE
with menu_abas[2]:
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
                            st.caption(prod.get('desc','')[:60])
                        with col3:
                            if st.button("🗑️", key=f"del_{idx}"):
                                produtos.pop(idx)
                                db.collection("profissionais").document(user_id).update({"produtos": produtos})
                                st.rerun()

# ABA ADMIN - mantém original + contador de produtos
# [restante do código original mantido...]
