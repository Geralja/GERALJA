# ==============================================================================
# GERALJÁ: CRIANDO SOLUÇÕES - MÓDULO INTEGRADO & SEGURANÇA MÁXIMA
# VERSÃO 5.0 SOCIAL CONSOLIDADA - Perfil Moderno + Vitrine Completa + Correções
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

# --- BIBLIOTECAS DE IA E BUSCA ---
from groq import Groq
from fuzzywuzzy import process
from urllib.parse import quote
import google.generativeai as genai
from google_auth_oauthlib.flow import Flow

# --- COMPONENTES JS COM FALLBACK SEGURO ---
streamlit_js_eval = None
get_geolocation = None
try:
    from streamlit_js_eval import streamlit_js_eval, get_geolocation
except ImportError:
    pass
except Exception:
    pass

# --- CONFIGURAÇÃO PÁGINA ---
st.set_page_config(
    page_title="GeralJá | Criando Soluções",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- INICIALIZAÇÃO DE ESTADOS DA SESSÃO ---
for key, default in {
    'modo_noite': False,
    'tema_claro': False,
    'auth': False,
    'user_id': None,
    'admin_logado': False,
    'minha_lat': -23.5505,
    'minha_lon': -46.6333,
    'security_check': False,
    'js_disponivel': True,
    'pre_cadastro': None
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# --- DETECÇÃO MODO DIA/NOITE AUTOMÁTICO ---
if streamlit_js_eval and not st.session_state.get('theme_checked', False):
    try:
        prefers_dark = streamlit_js_eval(js_expressions="window.matchMedia('(prefers-color-scheme: dark)').matches", key="theme_detect")
        if prefers_dark is not None:
            st.session_state.modo_noite = bool(prefers_dark)
            st.session_state.theme_checked = True
    except Exception:
        pass

# --- CSS RESPONSIVO & DESIGN SOCIAL ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .main .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
    #MainMenu, footer, header { visibility: hidden; }
    
    /* HEADER PRINCIPAL */
    .header-container { 
        background: linear-gradient(135deg, #0047AB 0%, #FF8C00 100%); 
        padding: 25px 15px; 
        border-radius: 0 0 25px 25px; 
        text-align: center; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.15); 
        margin-bottom: 20px;
        margin-top: -1rem;
    }
    .logo-azul { color: #FFFFFF; font-weight: 900; font-size: 38px; letter-spacing: -1px; text-shadow: 1px 1px 3px rgba(0,0,0,0.2); }
    .logo-laranja { color: #FFD700; font-weight: 900; font-size: 38px; letter-spacing: -1px; text-shadow: 1px 1px 3px rgba(0,0,0,0.2); }
    .sub-logo { color: #FFFFFF; font-weight: 600; font-size: 13px; opacity: 0.95; letter-spacing: 1px; }
    
    /* CARDS E PRODUTOS */
    .produto-card { 
        background: #ffffff; 
        border-radius: 12px; 
        padding: 12px; 
        margin: 8px 0; 
        border: 1px solid #e9ecef; 
        color: #333;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    /* ESTILO REDE SOCIAL PARA PERFIL */
    .social-profile-header {
        background: linear-gradient(to bottom, #0047AB, #002D6B);
        height: 120px;
        border-radius: 20px 20px 0 0;
        position: relative;
        margin-bottom: 60px;
    }
    .social-profile-avatar {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        border: 4px solid white;
        position: absolute;
        bottom: -50px;
        left: 20px;
        object-fit: cover;
        background: #eee;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    
    @media (max-width: 640px) {
        .header-container { padding: 15px 10px; margin-bottom: 10px; }
        .logo-azul, .logo-laranja { font-size: 30px; }
        .stButton button { width: 100%; }
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# BLOCO A: MOTOR GLOBAL E CONEXÃO BANCO
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

# CONFIGURAÇÃO DE CHAVES E CLIENTES IA
client_groq = None
try:
    FB_ID = st.secrets.get("FB_CLIENT_ID", "")
    FB_SECRET = st.secrets.get("FB_CLIENT_SECRET", "")
    FIREBASE_API_KEY = st.secrets.get("FIREBASE_API_KEY", "")
    REDIRECT_URI = st.secrets.get("google_auth", {}).get("redirect_uri", "https://geralja-zxiaj2ot56fuzgcz7xhcks.streamlit.app/")
    
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    if "GROQ_API_KEY" in st.secrets:
        client_groq = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error(f"⚠️ Atenção ao carregar Secrets: {e}")

# BANCO FIREBASE MASTER
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
                st.error("⚠️ Configuração 'firebase.base64' não encontrada nos Secrets.")
                st.stop()
        except Exception as e:
            st.error(f"❌ FALHA CONEXÃO FIREBASE: {e}")
            st.stop()
    return firebase_admin.get_app()

app_engine = conectar_banco_master()
db = firestore.client()

# ==============================================================================
# BLOCO B: FUNÇÕES AUXILIARES SEGURAS (CORREÇÕES DE LINHA)
# ==============================================================================

def limpar_whatsapp(numero):
    if not numero: return ""
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
        if None in [lat1, lon1, lat2, lon2]: return 999.0
        lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return round(R * c, 1)
    except Exception:
        return 999.0

def safe_image_src(valor):
    """Trata imagens base64 e URLs externas sem quebrar renderização"""
    if not valor:
        return "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    v = str(valor).strip()
    if v.startswith("http://") or v.startswith("https://") or v.startswith("data:image"):
        return v
    return f"data:image/jpeg;base64,{v}"

def otimizar_imagem_admin(imagem_upload):
    """Processa upload e otimiza tamanho mantendo qualidade"""
    try:
        img = Image.open(imagem_upload)
        if img.mode in ("RGBA", "P"):
            img = img.convert('RGB')
        img.thumbnail((800, 800))
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=80)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception:
        return None

def processar_ia_avancada(texto):
    if not texto: return "Outro (Personalizado)"
    t_clean = normalizar(texto)
    
    for chave, categoria in CONCEITOS_EXPANDIDOS.items():
        if re.search(rf"\b{re.escape(normalizar(chave))}\b", t_clean):
            return categoria
    
    for cat in CATEGORIAS_OFICIAIS:
        if normalizar(cat) in t_clean:
            return cat

    try:
        if client_groq:
            prompt = f"Classifique a busca '{texto}' exatamente em uma destas categorias: {CATEGORIAS_OFICIAIS}. Responda APENAS o nome exato da categoria."
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
        
    return "Outro (Personalizado)"

def criar_link_zap(numero, msg):
    num_limpo = limpar_whatsapp(numero)
    return f"https://api.whatsapp.com/send?phone={num_limpo}&text={urllib.parse.quote(msg)}"

# ==============================================================================
# BLOCO C: CONSTANTES E REGRAS
# ==============================================================================

PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
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
    "pizza": "Pizzaria", "pizzaria": "Pizzaria", "fome": "Pizzaria",
    "lanche": "Lanchonete", "hamburguer": "Hamburgueria", "burger": "Hamburgueria",
    "comida": "Restaurante", "almoco": "Restaurante", "marmita": "Restaurante",
    "doce": "Doceria", "acai": "Açaí", "sorvete": "Sorveteria", "cerveja": "Adega",
    "roupa": "Loja de Roupas", "sapato": "Calçados", "remedio": "Farmácia",
    "cabelo": "Barbearia/Salão", "unha": "Manicure/Pedicure", "celular": "Assistência Técnica",
    "vazamento": "Encanador", "cano": "Encanador", "curto": "Eletricista", "luz": "Eletricista",
    "pintar": "Pintor", "reforma": "Pedreiro", "chave": "Chaveiro", "carro": "Mecânico",
    "pneu": "Borracheiro", "frete": "Freteiro", "mudanca": "Freteiro", "faxina": "Diarista"
}

# ==============================================================================
# BLOCO D: CABEÇALHO E LOGIN GOOGLE
# ==============================================================================

# OAuth Google Flow
query_params = st.query_params
if "code" in query_params:
    try:
        g_auth = st.secrets.get("google_auth", {})
        flow = Flow.from_client_config(
            {"web": {
                "client_id": g_auth.get("client_id"),
                "client_secret": g_auth.get("client_secret"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI]
            }},
            scopes=["openid", "https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"],
            redirect_uri=REDIRECT_URI
        )
        code_val = query_params["code"]
        if isinstance(code_val, list): code_val = code_val[0]
        flow.fetch_token(code=code_val)
        session = flow.authorized_session()
        user_info = session.get('https://www.googleapis.com/oauth2/v2/userinfo').json()
        
        email_google = user_info.get("email")
        pro_ref = db.collection("profissionais").where("email", "==", email_google).limit(1).get()
        if pro_ref:
            st.session_state.auth = True
            st.session_state.user_id = pro_ref[0].id 
            st.toast(f"Bem-vindo de volta!")
        else:
            st.session_state.pre_cadastro = {
                "email": email_google,
                "nome": user_info.get("name"),
                "foto": user_info.get("picture")
            }
            st.toast("Complete seu cadastro para continuar!")
    except Exception as e:
        st.error(f"Falha na autenticação Google: {e}")

# BANNER CABEÇALHO
c_t1, c_t2 = st.columns([2, 8])
with c_t1:
    st.session_state.modo_noite = st.toggle("🌙 Modo Noite", value=st.session_state.modo_noite)

estilo_dinamico = f"""
<style>
    .stApp {{
        background-color: {"#0D1117" if st.session_state.modo_noite else "#F8F9FA"} !important;
        color: {"#FFFFFF" if st.session_state.modo_noite else "#1A1A1B"} !important;
    }}
</style>
"""
st.markdown(estilo_dinamico, unsafe_allow_html=True)

st.markdown('''
<div class="header-container">
    <span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span><br>
    <span class="sub-logo">CONECTANDO O GRAJAÚ E REGIÃO</span>
</div>
''', unsafe_allow_html=True)

# ==============================================================================
# BLOCO E: NAVEGAÇÃO E ABAS
# ==============================================================================

lista_abas = ["🔍 BUSCAR", "🚀 CADASTRAR", "👤 MEU PERFIL", "⭐ FEEDBACK"]

with st.sidebar:
    st.markdown("### 🔐 Acesso Restrito")
    comando = st.text_input("Código de Acesso", type="password", key="admin_key", label_visibility="collapsed", placeholder="Digite o código")
    if comando == "abracadabra":
        lista_abas.append("👑 ADMIN")
    elif comando == "financeiro2026":
        lista_abas.append("📊 FINANCEIRO")
    elif comando == "geralja_master":
        lista_abas.extend(["👑 ADMIN", "📊 FINANCEIRO"])

menu_abas = st.tabs(lista_abas)
abas_dict = {nome.split()[1].lower(): i for i, nome in enumerate(lista_abas)}

# ------------------------------------------------------------------------------
# 1. ABA BUSCAR
# ------------------------------------------------------------------------------
if 'buscar' in abas_dict:
    with menu_abas[abas_dict['buscar']]:
        st.markdown("### 🏙️ O que você procura hoje no Grajaú?")
        
        with st.expander("📍 Ajustar Minha Localização (GPS)", expanded=False):
            if get_geolocation:
                try:
                    loc = get_geolocation(component_key="geo_high_prec_v5") 
                    if loc and 'coords' in loc:
                        st.session_state.minha_lat = loc['coords']['latitude']
                        st.session_state.minha_lon = loc['coords']['longitude']
                        st.success(f"GPS Ativo (Precisão: {loc['coords'].get('accuracy', 0):.0f}m)")
                    else:
                        st.warning("GPS indisponível. Usando localização padrão do bairro.")
                except Exception:
                    st.warning("Recurso GPS indisponível no momento.")
            else:
                st.info("Informe sua busca. O sistema calculará as melhores opções.")

        minha_lat = st.session_state.minha_lat
        minha_lon = st.session_state.minha_lon

        c1, c2 = st.columns([3, 1])
        termo_busca = c1.text_input("Ex: 'Encanador', 'Pizzaria', 'Borracheiro'", key="main_search_v5")
        raio_km = c2.select_slider("Raio (KM)", options=[1, 3, 5, 10, 20, 50, 500], value=10)

        if termo_busca:
            with st.status("🔍 Localizando profissionais e comércios...", expanded=False) as status:
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
                status.update(label=f"Resultados para '{cat_ia}'!", state="complete")

            if not lista_ranking:
                st.warning(f"Nenhum parceiro encontrado para '{cat_ia}' neste raio. Tente aumentar a distância.")
            else:
                for p in lista_ranking:
                    f_perfil = safe_image_src(p.get('foto_url', ''))
                    is_elite = p['score_elite'] > 0
                    cor_borda = "#FFD700" if is_elite else "#0047AB"
                    zap_link = criar_link_zap(p.get('whatsapp',''), f"Olá {p.get('nome')}, vi seu anúncio no GeralJá!")

                    st.markdown(f"""
                    <div style="background:white; border-radius:15px; border-left:8px solid {cor_borda}; padding:15px; margin-bottom:15px; box-shadow:0 3px 10px rgba(0,0,0,0.08); color:#333;">
                        <div style="font-size:11px; color:#0047AB; font-weight:bold; margin-bottom:8px;">
                            📍 a {p['dist']:.1f} km {" | 🏆 DESTAQUE ELITE" if is_elite else ""}
                        </div>
                        <div style="display:flex; align-items:center; gap:15px;">
                            <img src="{f_perfil}" style="width:60px; height:60px; border-radius:50%; object-fit:cover; border:2px solid #ddd;">
                            <div>
                                <h4 style="margin:0; color:#0047AB;">{str(p.get('nome','')).upper()}</h4>
                                <p style="margin:4px 0 0 0; color:#555; font-size:13px;">{str(p.get('descricao',''))[:100]}</p>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Exibição de Produtos da Vitrine
                    produtos = p.get('produtos', [])
                    produtos_ativos = [pr for pr in produtos if pr.get('ativo', True)][:3]
                    if produtos_ativos and p.get('tipo_conta') == 'comerciante':
                        st.markdown("<div style='margin-top:10px; font-size:13px;'><b>🛍️ Produtos / Ofertas:</b></div>", unsafe_allow_html=True)
                        cols = st.columns(len(produtos_ativos))
                        for idx, prod in enumerate(produtos_ativos):
                            with cols[idx]:
                                st.image(safe_image_src(prod.get('foto_b64', '')), use_container_width=True)
                                st.markdown(f"<div class='produto-card'><b>{prod.get('nome','')}</b><br><span style='color:#25D366; font-weight:bold;'>R$ {prod.get('preco',0):.2f}</span></div>", unsafe_allow_html=True)
                                link_prod = criar_link_zap(p.get('whatsapp',''), f"Olá! Vi no GeralJá e tenho interesse em: {prod.get('nome','')}")
                                st.link_button("Pedir", link_prod, use_container_width=True)
                    
                    st.markdown(f"""
                        <a href="{zap_link}" target="_blank" style="display:block; background:#25D366; color:white; text-align:center; padding:10px; border-radius:10px; text-decoration:none; font-weight:bold; margin-top:10px;">💬 FALAR NO WHATSAPP</a>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📰 Plantão de Notícias Grajaú Tem")
        
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
            cols = st.columns(len(noticias))
            for i, n in enumerate(noticias):
                with cols[i]:
                    img = "https://placehold.co/300x200/0047AB/FFFFFF?text=Graja%C3%BA+Tem"
                    if 'media_content' in n and n.media_content:
                        img = n.media_content[0]['url']
                    fonte = n.source.get('title', 'Notícias') if hasattr(n, 'source') else 'Notícias'
                    st.markdown(f"""
                    <a href="{n.link}" target="_blank" style="text-decoration:none; color:inherit;">
                        <div style="border:1px solid #ddd; border-radius:10px; overflow:hidden; background:white; height:260px;">
                            <img src="{img}" style="width:100%; height:110px; object-fit:cover;">
                            <div style="padding:8px;">
                                <p style="font-size:12px; font-weight:bold; margin:0; color:#333;">{n.title[:75]}...</p>
                                <p style="font-size:10px; color:#777; margin-top:5px;">{fonte}</p>
                            </div>
                        </div>
                    </a>
                    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. ABA CADASTRAR
# ------------------------------------------------------------------------------
if 'cadastrar' in abas_dict:
    with menu_abas[abas_dict['cadastrar']]:
        st.header("🚀 Divulgue seu Trabalho ou Comércio")
        st.write("Faça parte da maior vitrine da região do Grajaú!")

        if st.session_state.auth:
            st.info("Você já está logado. Acesse a aba 'MEU PERFIL' para gerenciar sua conta.")
        else:
            with st.form("form_cadastro_geral"):
                email_pre = st.session_state.pre_cadastro.get('email', '') if st.session_state.pre_cadastro else ''
                nome_pre = st.session_state.pre_cadastro.get('nome', '') if st.session_state.pre_cadastro else ''
                foto_pre = st.session_state.pre_cadastro.get('foto', '') if st.session_state.pre_cadastro else ''

                nome = st.text_input("Nome Completo ou Nome do Negócio", value=nome_pre)
                email = st.text_input("E-mail principal", value=email_pre)
                whatsapp = st.text_input("WhatsApp (com DDD - apenas números)")
                area = st.selectbox("Categoria / Ramo de Atuação", CATEGORIAS_OFICIAIS)
                descricao = st.text_area("Descrição dos seus serviços/produtos (máx. 200 caracteres)", max_chars=200)
                foto_perfil = st.file_uploader("Foto de Perfil / Logotipo", type=['jpg', 'jpeg', 'png'])
                senha_acesso = st.text_input("Crie uma Senha para Acesso", type="password")
                termos = st.checkbox("Li e aceito os Termos de Uso do GeralJá")

                if st.form_submit_button("CADASTRAR E ENVIAR PARA ANÁLISE", use_container_width=True):
                    zap_limpo = limpar_whatsapp(whatsapp)
                    if not termos:
                        st.error("Por favor, aceite os termos de uso.")
                    elif not nome or not email or not zap_limpo or not senha_acesso:
                        st.error("Preencha todos os campos obrigatórios.")
                    else:
                        try:
                            foto_url = foto_pre
                            if foto_perfil:
                                foto_url = otimizar_imagem_admin(foto_perfil)
                            if not foto_url:
                                foto_url = "https://cdn-icons-png.flaticon.com/512/149/149071.png"

                            doc_ref = db.collection("profissionais").document(zap_limpo)
                            doc_ref.set({
                                "nome": nome,
                                "email": email,
                                "whatsapp": zap_limpo,
                                "senha": senha_acesso,
                                "area": area,
                                "descricao": descricao,
                                "foto_url": foto_url,
                                "aprovado": False,
                                "saldo": 5,
                                "cliques": 0,
                                "criado_em": datetime.now(fuso_br),
                                "lat": LAT_REF,
                                "lon": LON_REF,
                                "tipo_conta": "prestador",
                                "produtos": []
                            })
                            st.success("🎉 Cadastro enviado com sucesso! Aguarde aprovação.")
                            st.session_state.pre_cadastro = None
                            time.sleep(1.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao cadastrar: {e}")

# ------------------------------------------------------------------------------
# 3. ABA MEU PERFIL (ESTILO REDE SOCIAL + LOGIN LOCAL)
# ------------------------------------------------------------------------------
if 'perfil' in abas_dict:
    with menu_abas[abas_dict['perfil']]:
        
        # CASO NÃO ESTEJA LOGADO: FORMULÁRIO DE LOGIN
        if not st.session_state.auth:
            st.subheader("🔑 Acesso ao Painel do Parceiro")
            
            with st.form("form_login_local"):
                l_zap = st.text_input("WhatsApp Cadastrado (apenas números)")
                l_pw = st.text_input("Sua Senha", type="password")
                btn_logar = st.form_submit_button("ENTRAR NO PAINEL", use_container_width=True)

                if btn_logar:
                    zap_limpo = limpar_whatsapp(l_zap)
                    if not zap_limpo or not l_pw:
                        st.error("Informe seu WhatsApp e sua Senha.")
                    else:
                        try:
                            u = db.collection("profissionais").document(zap_limpo).get()
                            if u.exists:
                                dados_user = u.to_dict()
                                if str(dados_user.get('senha')) == str(l_pw):
                                    st.session_state.auth = True
                                    st.session_state.user_id = u.id
                                    st.success("Login efetuado com sucesso!")
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    st.error("Senha incorreta.")
                            else:
                                st.error("WhatsApp não encontrado. Faça seu cadastro primeiro.")
                        except Exception as e:
                            st.error(f"Erro ao acessar banco de dados: {e}")

        # CASO ESTEJA LOGADO: EXIBE PERFIL MODERNO COM REDE SOCIAL
        else:
            user_id = st.session_state.user_id
            doc_ref = db.collection("profissionais").document(user_id)
            user_data = doc_ref.get().to_dict() or {}

            # CAPA E AVATAR ESTILO REDE SOCIAL
            foto_perfil = safe_image_src(user_data.get('foto_url'))
            st.markdown(f"""
            <div class="social-profile-header">
                <img src="{foto_perfil}" class="social-profile-avatar">
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"### {user_data.get('nome', 'Parceiro').upper()}")
            st.caption(f"📍 {user_data.get('area', 'Prestador de Serviço')} | WhatsApp: {user_data.get('whatsapp', '')}")
            
            # ESTATÍSTICAS DO PARCEIRO
            m1, m2, m3 = st.columns(3)
            m1.metric("Saldo de Coins 🪙", f"{user_data.get('saldo', 0)}")
            m2.metric("Visualizações/Cliques 🚀", f"{user_data.get('cliques', 0)}")
            m3.metric("Status da Conta", "🟢 APROVADO" if user_data.get('aprovado') else "🟡 EM ANÁLISE")

            st.markdown("---")
            tab_vitrine, tab_config, tab_ajuda = st.tabs(["🛍️ MINHA VITRINE", "⚙️ MEUS DADOS", "❓ AJUDA"])
            
            with tab_vitrine:
                tipo_conta = user_data.get('tipo_conta', 'prestador')
                if tipo_conta != 'comerciante':
                    st.info("💡 Você está no modo Prestador. Ative o Modo Comerciante para cadastrar seus produtos na vitrine digital.")
                    if st.button("ATIVAR MODO COMERCIANTE GRATUITAMENTE", use_container_width=True):
                        doc_ref.update({"tipo_conta": "comerciante"})
                        st.success("Modo Comerciante Ativado!")
                        time.sleep(0.5)
                        st.rerun()
                else:
                    produtos = user_data.get('produtos', [])
                    
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
                                if st.button("🗑️", key=f"del_prod_{idx}"):
                                    produtos.pop(idx)
                                    doc_ref.update({"produtos": produtos})
                                    st.rerun()

                    st.markdown("---")
                    with st.expander("➕ ADICIONAR NOVO PRODUTO À VITRINE", expanded=False):
                        with st.form("form_novo_produto", clear_on_submit=True):
                            p_nome = st.text_input("Nome do Produto / Oferta")
                            p_preco = st.number_input("Preço (R$)", min_value=0.0, format="%.2f")
                            p_desc = st.text_area("Descrição do item", max_chars=150)
                            p_foto = st.file_uploader("Foto do Produto", type=['jpg', 'jpeg', 'png'])
                            
                            if st.form_submit_button("SALVAR PRODUTO", use_container_width=True):
                                if p_nome and p_preco > 0 and p_foto:
                                    foto_b64 = otimizar_imagem_admin(p_foto)
                                    if foto_b64:
                                        novo_item = {
                                            "nome": p_nome,
                                            "preco": float(p_preco),
                                            "desc": p_desc,
                                            "foto_b64": foto_b64,
                                            "ativo": True,
                                            "criado_em": datetime.now(fuso_br).isoformat()
                                        }
                                        produtos.append(novo_item)
                                        doc_ref.update({"produtos": produtos})
                                        st.success("Produto adicionado à vitrine!")
                                        time.sleep(0.5)
                                        st.rerun()
                                else:
                                    st.warning("Preencha o nome, valor e envie uma foto do produto.")

            with tab_config:
                with st.form("form_edit_perfil"):
                    n_nome = st.text_input("Nome de Exibição", value=user_data.get('nome', ''))
                    n_area = st.selectbox("Área de Atuação", CATEGORIAS_OFICIAIS, index=CATEGORIAS_OFICIAIS.index(user_data.get('area')) if user_data.get('area') in CATEGORIAS_OFICIAIS else 0)
                    n_desc = st.text_area("Bio / Descrição", value=user_data.get('descricao', ''))
                    n_foto = st.file_uploader("Trocar Foto de Perfil", type=['jpg', 'png', 'jpeg'])
                    
                    if st.form_submit_button("SALVAR ALTERAÇÕES", use_container_width=True):
                        upd = {"nome": n_nome, "area": n_area, "descricao": n_desc}
                        if n_foto:
                            img_b64 = otimizar_imagem_admin(n_foto)
                            if img_b64: upd["foto_url"] = img_b64
                        doc_ref.update(upd)
                        st.success("Perfil atualizado!")
                        time.sleep(0.5)
                        st.rerun()

            st.divider()
            if st.button("🚪 DESCONECTAR DO PAINEL", use_container_width=True):
                st.session_state.auth = False
                st.session_state.user_id = None
                st.rerun()

# ------------------------------------------------------------------------------
# 4. ABA FEEDBACK
# ------------------------------------------------------------------------------
if 'feedback' in abas_dict:
    with menu_abas[abas_dict['feedback']]:
        st.header("⭐ Envie seu Feedback")
        nota = st.slider("Nota para o GeralJá", 1, 5, 5)
        coment = st.text_area("Sua opinião ou sugestão:")
        if st.button("ENVIAR AVALIAÇÃO", use_container_width=True):
            st.success("Obrigado pelo apoio! Seu feedback é fundamental.")

# ------------------------------------------------------------------------------
# 5. ABA ADMIN (SECRETA)
# ------------------------------------------------------------------------------
if 'admin' in abas_dict:
    with menu_abas[abas_dict['admin']]:
        st.header("👑 Painel Administrativo Master")
        
        tab_adm1, tab_adm2 = st.tabs(["📋 APROVAR CADASTROS", "💎 GESTÃO DE CRÉDITOS"])
        
        with tab_adm1:
            st.subheader("Cadastros Pendentes")
            pendentes = db.collection("profissionais").where("aprovado", "==", False).stream()
            count = 0
            for doc in pendentes:
                count += 1
                d = doc.to_dict()
                with st.expander(f"📌 {d.get('nome')} - {d.get('area')}"):
                    st.write(f"**WhatsApp:** {d.get('whatsapp')}")
                    st.write(f"**Descrição:** {d.get('descricao')}")
                    col_a, col_b = st.columns(2)
                    if col_a.button("✅ Aprovar", key=f"ap_{doc.id}"):
                        db.collection("profissionais").document(doc.id).update({"aprovado": True})
                        st.success("Aprovado!")
                        st.rerun()
                    if col_b.button("🗑️ Recusar", key=f"rec_{doc.id}"):
                        db.collection("profissionais").document(doc.id).delete()
                        st.warning("Excluído.")
                        st.rerun()
            if count == 0:
                st.info("Nenhum cadastro pendente no momento.")

        with tab_adm2:
            st.subheader("Adicionar GeralCoins")
            profs_list = db.collection("profissionais").stream()
            dict_profs = {p.to_dict().get('nome', p.id): p.id for p in profs_list}
            if dict_profs:
                p_sel = st.selectbox("Selecione o Profissional", list(dict_profs.keys()))
                qtd_coins = st.number_input("Quantidade de Moedas", min_value=1, value=10)
                if st.button("Adicionar Moedas"):
                    p_id = dict_profs[p_sel]
                    ref = db.collection("profissionais").document(p_id)
                    s_atual = ref.get().to_dict().get('saldo', 0)
                    ref.update({"saldo": s_atual + qtd_coins, "verificado": True})
                    st.success(f"{qtd_coins} Moedas adicionadas ao parceiro {p_sel}!")

# ------------------------------------------------------------------------------
# 6. ABA FINANCEIRO (SECRETA)
# ------------------------------------------------------------------------------
if 'financeiro' in abas_dict:
    with menu_abas[abas_dict['financeiro']]:
        st.header("📊 Tabela Comercial Grajaú Tem")
        st.markdown("""
        ### Pacotes Comerciais Vigentes
        * ** Vitrine de Ofertas (Carrossel Diário):** R$ 100 (Avulso) | R$ 600 (Mensal - 8 inserções)
        * **🥉 Bronze:** 1 post = R$ 150
        * **🥈 Prata:** 3 posts = R$ 400
        * **🥇 Ouro:** 10 posts = R$ 700
        * **📻 Rádio Grajaú Tem:** R$ 300/mês
        """)

# ==============================================================================
# RODAPÉ INSTITUCIONAL
# ==============================================================================
st.markdown("<br><hr>", unsafe_allow_html=True)
c_f1, c_f2 = st.columns([3, 1])
with c_f1:
    st.caption("© 2026 GeralJá & Grajaú Tem — Conectando moradores, profissionais e oportunidades na região.")
with c_f2:
    st.caption("🚀 Versão 5.0 Consolidada")
