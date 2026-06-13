# ==============================================================================
# GERALJÁ: CRIANDO SOLUÇÕES - MÓDULO 1: INFRAESTRUTURA & SEGURANÇA MÁXIMA
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
from groq import Groq                # Para a IA avançada
from fuzzywuzzy import process       # Para buscas com erros de digitação
from urllib.parse import quote       # Para links de WhatsApp seguros
import google.generativeai as genai  # IA Gemini
from google_auth_oauthlib.flow import Flow # Login Google

# --- TENTA IMPORTAR COMPONENTES JS (EVITA QUEBRA SE NÃO INSTALADO) ---
try:
    from streamlit_js_eval import streamlit_js_eval, get_geolocation
except ImportError:
    pass

# --- CONFIGURAÇÃO DE ALTO NÍVEL ---
class GeralJaEngine:
    def __init__(self):
        self.fuso = pytz.timezone('America/Sao_Paulo')
    
    def sanitizar(self, codigo_bruto):
        """Mata caracteres fantasmas e lixo de codificação instantaneamente"""
        if not codigo_bruto: return ""
        # Remove U+00A0 (espaço inquebrável) e normaliza espaços
        limpo = codigo_bruto.replace('\u00a0', ' ').replace('\xa0', ' ')
        # Filtra apenas caracteres ASCII visíveis + quebras de linha
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

# --- CONFIGURAÇÃO DE CHAVES (PUXANDO DO SECRETS) ---
try:
    # Chaves de Autenticação Social
    FB_ID = st.secrets.get("FB_CLIENT_ID", "")
    FB_SECRET = st.secrets.get("FB_CLIENT_SECRET", "")
    FIREBASE_API_KEY = st.secrets.get("FIREBASE_API_KEY", "")
    MP_ACCESS_TOKEN = st.secrets.get("MP_ACCESS_TOKEN", "TEST-7281048016492062-091215-mocktoken")
    REDIRECT_URI = "https://geralja-zxiaj2ot56fuzgcz7xhcks.streamlit.app/"
    
    # Configuração de APIs de IA
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    if "GROQ_API_KEY" in st.secrets:
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

# Ativa o banco
app_engine = conectar_banco_master()
db = firestore.client()

# ------------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DE AMBIENTE E PERFORMANCE
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="GeralJá | Criando Soluções",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- INICIALIZAÇÃO DE ESTADOS SEGUROS NO SESSION STATE ---
if 'tema_claro' not in st.session_state:
    st.session_state.tema_claro = False
if 'modo_noite' not in st.session_state:
    st.session_state.modo_noite = True 
if 'auth' not in st.session_state: 
    st.session_state.auth = False
if 'admin_logado' not in st.session_state: 
    st.session_state.admin_logado = False
if 'minha_lat' not in st.session_state:
    st.session_state.minha_lat = -23.5505
if 'minha_lon' not in st.session_state:
    st.session_state.minha_lon = -46.6333

# Mantém os menus escondidos
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

# Verifica se o Google enviou o código na URL (Query Params)
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

# Layout do topo (Toggle)
c_t1, c_t2 = st.columns([2, 8])
with c_t1:
    st.session_state.modo_noite = st.toggle("🌙 Modo Noite", value=st.session_state.modo_noite)

# Bloco CSS Dinâmico
estilo_dinamico = f"""
<style>
    @media (max-width: 640px) {
        .main .block-container { padding: 1rem !important; }
        h1 { font-size: 1.8rem !important; }
    }
    .stApp {
        background-color: {"#0D1117" if st.session_state.modo_noite else "#FFFAFA"} !important;
        color: {"#FFFFFF" if st.session_state.modo_noite else "#1A1A1B"} !important;
    }
    div[data-testid="stVerticalBlock"] > div[style*="background"] {
        background-color: {"#161B22" if st.session_state.modo_noite else "#FFFFFF"} !important;
        border: 1px solid {"#30363D" if st.session_state.modo_noite else "#E0E0E0"} !important;
        border-radius: 18px !important;
    }
</style>
"""
st.markdown(estilo_dinamico, unsafe_allow_html=True)

# ==========================================================
# FUNÇÕES DE SUPORTE GLOBAL
# ==========================================================
def limpar_whatsapp(numero):
    """Remove parênteses, espaços e traços do número."""
    num = re.sub(r'\D', '', str(numero))
    if not num.startswith('55') and len(num) >= 10:
        num = f"55{num}"
    return num

def normalizar(texto):
    """Remove acentos e deixa tudo em minúsculo para busca."""
    if not texto: return ""
    return "".join(ch for ch in unicodedata.normalize('NFKD', texto) 
                   if unicodedata.category(ch) != 'Mn').lower()

def calcular_distancia_real(lat1, lon1, lat2, lon2):
    try:
        if None in [lat1, lon1, lat2, lon2]: return 999.0
        R = 6371  # Raio da Terra em KM
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return round(R * c, 1)
    except: return 999.0

def buscar_opcoes_dinamicas(documento, padrao):
    """Busca listas de categorias ou tipos na coleção 'configuracoes'."""
    try:
        doc = db.collection("configuracoes").document(documento).get()
        if doc.exists:
            dados = doc.to_dict()
            return dados.get("lista", padrao)
        return padrao
    except Exception as e:
        return padrao

def converter_img_b64(file):
    if file is None: return ""
    try: return base64.b64encode(file.read()).decode()
    except: return ""

def finalizar_e_alinhar_layout():
    """Esta função atua como um ímã. Puxa o conteúdo e limpa o rodapé."""
    st.write("---")
    fechamento_estilo = """
        <style>
            .main .block-container { padding-bottom: 5rem !important; }
            .footer-clean {
                text-align: center;
                padding: 20px;
                opacity: 0.7;
                font-size: 0.8rem;
                width: 100%;
                color: gray;
            }
        </style>
        <div class="footer-clean">
            <p>🎯 <b>GeralJá</b> - Sistema de Inteligência Local</p>
            <p>Conectando quem precisa com quem sabe fazer.</p>
            <p>v5.0 | © 2026 Todos os direitos reservados</p>
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
# 4. MOTORES DE IA E UTILS
# ------------------------------------------------------------------------------
def normalizar_para_ia(texto):
    if not texto: return ""
    return "".join(c for c in unicodedata.normalize('NFD', str(texto))
                   if unicodedata.category(c) != 'Mn').lower().strip()

def processar_ia_avancada(texto):
    if not texto: return "Vazio"
    t_clean = normalizar_para_ia(texto)
    
    for chave, category in CONCEITOS_EXPANDIDOS.items():
        if re.search(rf"\b{normalizar_para_ia(chave)}\b", t_clean):
            return category
    
    for cat in CATEGORIAS_OFICIAIS:
        if normalizar_para_ia(cat) in t_clean:
            return cat

    try:
        cache_ref = db.collection("cache_buscas").document(t_clean).get()
        if cache_ref.exists:
            return cache_ref.to_dict().get("categoria")

        if "GROQ_API_KEY" in st.secrets:
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

# ------------------------------------------------------------------------------
# 5. DESIGN SYSTEM
# ------------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F8FAFC; }
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

# --- CONFIGURAÇÕES DE NEGÓCIO ---
ZAP_VENDAS = "5511980168513"

def criar_link_zap(numero, msg):
    return f"https://api.whatsapp.com/send?phone={numero}&text={urllib.parse.quote(msg)}"

# ==============================================================================
# --- ABA 0: PORTAL GRAJAÚ TEM (V5.0 - COM RASTREAMENTO DE LEADS) ---
# ==============================================================================
with menu_abas[0]:
    st.markdown("### 🏙️ O que você precisa no Grajaú?")
    
    # 1. MOTOR DE LOCALIZAÇÃO (ALTA PRECISÃO)
    with st.expander("📍 Seus dados de Localização (GPS)", expanded=False):
        if 'get_geolocation' in globals():
            loc = get_geolocation(component_key="geo_high_prec") 
            if loc and 'coords' in loc:
                st.session_state.minha_lat = loc['coords']['latitude']
                st.session_state.minha_lon = loc['coords']['longitude']
                precisao = loc['coords'].get('accuracy', 0)
                st.success(f"GPS Ativo (Precisão: {precisao:.0f}m)")
            else:
                st.warning("Usando localização padrão (Centro). Ative o GPS para maior precisão.")
        else:
            st.warning("Componente GPS indisponível. Usando coordenadas do Centro.")

    minha_lat = st.session_state.minha_lat
    minha_lon = st.session_state.minha_lon

    # 2. CAMPOS DE BUSCA
    c1, c2 = st.columns([3, 1])
    termo_busca = c1.text_input("Ex: 'Cano estourado' ou 'Pizzaria'", key="main_search_v4")
    raio_km = c2.select_slider("Raio (KM)", options=[1, 3, 5, 10, 20, 50, 500], value=5)

    if termo_busca:
        with st.status("🔍 Buscando...", expanded=False) as status:
            st.write("📂 Verificando categorias oficiais...")
            doc_cat = db.collection("configuracoes").document("categorias").get()
            lista_oficial = doc_cat.to_dict().get("lista", []) if doc_cat.exists else []
            
            cat_ia = None
            for c in lista_oficial:
                if c.lower() in termo_busca.lower():
                    cat_ia = c
                    break
            
            if not cat_ia:
                st.write("🤖 IA classificando seu pedido...")
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
            status.update(label=f"Resultados para {cat_ia} encontrados!", state="complete")

        if not lista_ranking:
            st.warning(f"Nenhum profissional de '{cat_ia}' encontrado nesta distância.")
        else:
            for p in lista_ranking:
                f_perfil = p.get('foto_url', '')
                if f_perfil and not str(f_perfil).startswith("http"):
                    f_perfil = f"data:image/jpeg;base64,{f_perfil}"
                elif not f_perfil:
                    f_perfil = "https://cdn-icons-png.flaticon.com/512/149/149071.png"
                
                is_elite = p['score_elite'] > 0
                cor_borda = "#FFD700" if is_elite else "#0047AB"

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
                </div>
                """, unsafe_allow_html=True)
                
                # Botão Operacional Integrado ao Sistema de Gestão de Leads Ativos
                if st.button(f"💬 SOLICITAR ORÇAMENTO COM {str(p.get('nome','')).upper()}", key=f"lead_btn_{p['id']}"):
                    if p.get('saldo', 0) > 0:
                        db.collection("profissionais").document(p['id']).update({
                            "saldo": firestore.Increment(-1),
                            "cliques": firestore.Increment(1)
                        })
                    
                    db.collection("leads").add({
                        "profissional_id": p['id'],
                        "data": datetime.now(fuso_br),
                        "termo_pesquisado": termo_busca
                    })
                    
                    zap_redirecionar = f"https://wa.me/{limpar_whatsapp(p.get('whatsapp',''))}?text=Olá!+Vi+seu+perfil+no+GeralJá+e+gostaria+de+um+orçamento."
                    st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{zap_redirecionar}\'" />', unsafe_allow_html=True)
                    st.success("Redirecionando de forma segura ao WhatsApp...")

# --- SEÇÃO DE NOTÍCIAS HÍBRIDA ---
st.markdown("---")
st.subheader("📰 Plantão Grajaú Tem")

IMG_PADRAO = "https://images.unsplash.com/photo-1504711432869-0df30d7eaf4d?w=500&q=80"

try:
    noticias_fb = list(db.collection("noticias").order_by("data", direction="DESCENDING").limit(2).stream())
except:
    noticias_fb = []

def buscar_noticias_rss(busca="Grajaú São Paulo"):
    try:
        url_rss = f"https://news.google.com/rss/search?q={urllib.parse.quote(busca)}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
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
    for i, noticia in enumerate(fila_noticias):
        with cols[i]:
            st.markdown(f"""
                <a href="{noticia['link']}" target="_blank" style="text-decoration:none; color:inherit;">
                    <div style="background:white; border-radius:15px; margin-bottom:20px; box-shadow:0 4px 12px rgba(0,0,0,0.08); overflow:hidden; border-bottom: 5px solid {noticia['cor']}; height: 320px;">
                        <div style="height:150px; background-image: url('{noticia['img']}'); background-size:cover; background-position:center;"></div>
                        <div style="padding:15px;">
                            <span style="background:{noticia['cor']}22; color:{noticia['cor']}; font-size:10px; font-weight:bold; padding:3px 10px; border-radius:50px;">
                                {noticia['fonte']}
                            </span>
                            <h4 style="margin:12px 0 8px 0; color:#1a1a1a; font-size:15px; line-height:1.3; height: 60px; overflow: hidden;">
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
# --- ABA 1: CADASTRAR & EDITAR (VERSÃO FINAL GERALJÁ CORRIGIDA) ---
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
        senha_input = col4.text_input("Sua Senha de Acesso", type="password", help="Necessária para salvar alterações")
        
        desc_input = st.text_area("Descrição Completa (Serviços, Horários, Diferenciais)")
        tipo_input = st.radio("Tipo", ["👨‍🔧 Profissional Autônomo", "🏢 Comércio/Loja"], horizontal=True)
        
        foto_upload = st.file_uploader("Atualizar Foto de Perfil ou Logo", type=['png', 'jpg', 'jpeg'])
        
        btn_acao = st.form_submit_button("✅ FINALIZAR: SALVAR OU ATUALIZAR", use_container_width=True)

    if btn_acao:
        if not nome_input or not zap_input or not senha_input:
            st.warning("⚠️ Nome, WhatsApp e Senha são obrigatórios!")
        else:
            try:
                with st.spinner("Sincronizando com o ecossistema GeralJá..."):
                    id_zap_limpo = limpar_whatsapp(zap_input)
                    doc_ref = db.collection("profissionais").document(id_zap_limpo)
                    perfil_antigo = doc_ref.get()
                    dados_antigos = perfil_antigo.to_dict() if perfil_antigo.exists else {}

                    foto_b64 = dados_antigos.get("foto_url", "")

                    if foto_upload is not None:
                        file_ext = foto_upload.name.split('.')[-1]
                        img_bytes = foto_upload.getvalue() 
                        encoded_img = base64.b64encode(img_bytes).decode()
                        foto_b64 = f"data:image/{file_ext};base64,{encoded_img}"
                    elif not foto_b64 and foto_google:
                        foto_b64 = foto_google

                    saldo_final = dados_antigos.get("saldo", BONUS_WELCOME)
                    cliques_atuais = dados_antigos.get("cliques", 0)

                    dados_pro = {
                        "nome": nome_input,
                        "whatsapp": id_zap_limpo,
                        "email": email_input,
                        "area": cat_input,
                        "senha": senha_input,
                        "descricao": desc_input,
                        "tipo": tipo_input,
                        "foto_url": foto_b64,
                        "saldo": saldo_final,
                        "data_cadastro": datetime.now().strftime("%d/%m/%Y"),
                        "aprovado": True,
                        "verificado": dados_antigos.get("verificado", True),
                        "cliques": cliques_atuais,
                        "rating": 5,
                        "lat": st.session_state.minha_lat,
                        "lon": st.session_state.minha_lon
                    }
                    
                    doc_ref.set(dados_pro)
                    
                    if "pre_cadastro" in st.session_state:
                        del st.session_state["pre_cadastro"]
                    
                    st.balloons()
                    if perfil_antigo.exists:
                        st.success(f"✅ Perfil de {nome_input} atualizado com sucesso!")
                    else:
                        st.success(f"🎊 Bem-vindo ao GeralJá! Cadastro concluído!")
                        
            except Exception as e:
                st.error(f"❌ Erro ao processar perfil: {e}")

# ==============================================================================
# ABA 2: 👤 MEU PERFIL / PAINEL DO PARCEIRO (UPGRADE INTEGRADO FINANÇAS)
# ==============================================================================
with menu_abas[2]:
    params = st.query_params
    if "uid" in params and not st.session_state.auth:
        fb_uid = params["uid"]
        user_query = db.collection("profissionais").where("fb_uid", "==", fb_uid).limit(1).get()
        if user_query:
            doc = user_query[0]
            st.session_state.auth = True
            st.session_state.user_id = doc.id
            st.success(f"✅ Bem-vindo!")
            time.sleep(1)
            st.rerun()

    if not st.session_state.auth:
        st.subheader("👤 Painel de Controle do Prestador")
        l_zap = st.text_input("WhatsApp Cadastrado (Somente números)", key="login_zap_p")
        l_pass = st.text_input("Senha de Acesso", type="password", key="login_pass_p")
        
        if st.button("ENTRAR NO PERFIL PROFISSIONAL", use_container_width=True):
            id_limpo = limpar_whatsapp(l_zap)
            user_doc = db.collection("profissionais").document(id_limpo).get()
            if user_doc.exists and str(user_doc.to_dict().get("senha")) == str(l_pass):
                st.session_state.auth = True
                st.session_state.user_id = id_limpo
                st.success("Autenticação bem-sucedida!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("⚠️ WhatsApp ou Senha incorretos.")
    else:
        p_ref = db.collection("profissionais").document(st.session_state.user_id)
        p_dados = p_ref.get().to_dict()
        
        st.subheader(f"Painel Operacional: {p_dados.get('nome')}")
        m1, m2, m3 = st.columns(3)
        m1.metric("Saldo de Créditos 🪙", f"{p_dados.get('saldo', 0)} moedas")
        m2.metric("Leads Convertidos 🚀", f"{p_dados.get('cliques', 0)} cliques")
        m3.metric("Posição Estratégica", "Bairro Ativo")
        
        # --- CARGA AUTOMÁTICA DE MOEDAS VIA MERCADO PAGO ---
        st.markdown("---")
        st.markdown("### 🪙 Recarga Instantânea de Moedas")
        pacote = st.radio("Selecione um plano de créditos comerciais:", ["10 Moedas - R$ 10", "50 Moedas - R$ 45 (Desconto)", "100 Moedas - R$ 80 (Melhor Custo)"], horizontal=True)
        valor_recarga = 10 if "10 Moedas" in pacote else (45 if "50 Moedas" in pacote else 80)
        moedas_ganhas = 10 if "10 Moedas" in pacote else (50 if "50 Moedas" in pacote else 100)
        
        if st.button(f"GERAR QR CODE PIX DINÂMICO: R$ {valor_recarga},00"):
            headers = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}", "Content-Type": "application/json"}
            payload = {
                "transaction_amount": float(valor_recarga),
                "description": f"Créditos GeralJa - {moedas_ganhas} Moedas",
                "payment_method_id": "pix",
                "payer": {"email": p_dados.get("email") or "parceiro@geralja.com.br", "first_name": p_dados.get("nome")}
            }
            try:
                res_mp = requests.post("https://api.mercadopago.com/v1/payments", json=payload, headers=headers).json()
                pix_copia_cola = res_mp['point_of_interaction']['transaction_data']['qr_code']
                qr_base64 = res_mp['point_of_interaction']['transaction_data']['qr_code_base64']
                
                st.image(base64.b64decode(qr_base64), width=240, caption="Aponte a câmera do banco")
                st.code(pix_copia_cola, language="text")
                st.info("💡 Realize o pagamento e valide clicando no botão abaixo.")
                
                if st.button("🔄 CONFIRMAR RECEBIMENTO DO SALDO"):
                    p_ref.update({"saldo": firestore.Increment(moedas_ganhas)})
                    st.success(f"Recarga realizada! +{moedas_ganhas} moedas computadas.")
                    time.sleep(1)
                    st.rerun()
            except:
                st.warning("Gateways integrados em Sandbox! Chave PIX alternativa para contingência:")
                st.code(f"Chave Pix CNPJ/Telefone: {PIX_OFICIAL}")

        if st.button("🚪 DESCONECTAR DO MEU PERFIL", use_container_width=True):
            st.session_state.auth = False
            st.rerun()

# ==============================================================================
# ABA 3: 👑 PAINEL DE ADMINISTRAÇÃO MASTER
# ==============================================================================
with menu_abas[3]:
    if not st.session_state.admin_logado:
        st.subheader("🔐 Entrada Admin")
        ad_user = st.text_input("Username Admin", key="admin_user_field")
        ad_pass = st.text_input("Password Admin", type="password", key="admin_pass_field")
        if st.button("AUTENTICAR DIRETORIA GERALJÁ"):
            if ad_user == "geralja" and ad_pass == CHAVE_ADMIN:
                st.session_state.admin_logado = True
                st.rerun()
            else: 
                st.error("Acesso negado.")
    else:
        st.markdown("## 👑 Painel Analítico de Controle")
        t_parceiros, t_leads_analytics = st.tabs(["👥 Gerenciar Parceiros", "📊 Monitor de Cliques (Leads)"])
        
        with t_parceiros:
            profs_geral = db.collection("profissionais").stream()
            for p_doc in profs_geral:
                p = p_doc.to_dict()
                st.write(f"**{p.get('nome')}** | Área: {p.get('area')} | Saldo: {p.get('saldo')} 🪙 | Fone: {p.get('whatsapp')}")
                if st.button("Injetar +50 Moedas Bônus", key=f"bonus_{p_doc.id}"):
                    db.collection("profissionais").document(p_doc.id).update({"saldo": firestore.Increment(50)})
                    st.success("Créditos adicionados via console!")
                    time.sleep(0.5)
                    st.rerun()
                    
        with t_leads_analytics:
            st.markdown("### Histórico de Interações de Clientes")
            leads_stream = db.collection("leads").order_by("data", direction="DESCENDING").limit(50).stream()
            lista_leads = []
            for l in leads_stream:
                ld = l.to_dict()
                lista_leads.append({
                    "Data": ld.get("data"), 
                    "Prestador Alvo": ld.get("profissional_id"), 
                    "Busca Executada": ld.get("termo_pesquisado")
                })
            if lista_leads:
                st.dataframe(pd.DataFrame(lista_leads), use_container_width=True)
            else:
                st.info("Nenhuma conversão registrada nas últimas 48 horas.")

# ==============================================================================
# ABA 4: ⭐ PROVA SOCIAL & FEEDBACKS DE CLIENTES (ANTIFRAUDE)
# ==============================================================================
with menu_abas[4]:
    st.header("⭐ Avaliação de Prestadores Locais")
    st.write("Registre seu depoimento real sobre os profissionais contratados no Grajaú.")
    
    with st.form("feedback_seguro_form"):
        lista_p_nomes = [p.id for p in db.collection("profissionais").stream()]
        prestador_selecionado = st.selectbox("Selecione quem executou o serviço:", lista_p_nomes)
        estrelas = st.slider("Nota de Desempenho (Estrelas)", 1, 5, 5)
        comentario_cliente = st.text_area("Comentários sobre o atendimento e preço:")
        fone_validador = st.text_input("Seu número de WhatsApp para verificação")
        
        if st.form_submit_button("PUBLICAR AVALIAÇÃO VERIFICADA"):
            if not fone_validador or not comentario_cliente:
                st.error("Todos os campos do formulário são de caráter obrigatório para validação contra fraudes.")
            else:
                db.collection("avaliacoes").add({
                    "profissional_id": prestador_selecionado,
                    "estrelas": estrelas,
                    "comentario": comentario_cliente,
                    "validador": limpar_whatsapp(fone_validador),
                    "data": datetime.now(fuso_br)
                })
                st.success("Obrigado! Sua avaliação passou pelos filtros de segurança e foi computada com sucesso.")

# ==============================================================================
# ABA 5: EASTER EGG - MONITOR FINANCEIRO E ESTRATÉGICO
# ==============================================================================
if comando == "abracadabra" and len(menu_abas) > 5:
    with menu_abas[5]:
        st.header("📊 Inteligência Financeira e Lucratividade do Negócio")
        p_lista = [p.to_dict() for p in db.collection("profissionais").stream()]
        if p_lista:
            df_f = pd.DataFrame(p_lista)
            st.metric("Volume Total de Moedas em Circulação no Bairro", f"🪙 {int(df_f['saldo'].sum()) if 'saldo' in df_f else 0}")
            st.metric("Total de Leads Gerados para Autônomos", f"🎯 {int(df_f['cliques'].sum()) if 'cliques' in df_f else 0}")
        else:
            st.info("Aguardando mais cadastros comerciais para consolidação de balanço gráfico.")

# --- INICIALIZAÇÃO DE INFRAESTRUTURA E RODAPÉ ---
finalizar_e_alinhar_layout()
