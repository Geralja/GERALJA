# ==============================================================================
# GERALJÁ 6.0 - SISTEMA COMPLETO GRAJAÚ TEM (INTEGRADO)
# Versão: Mantém todas as funcionalidades originais + melhorias visuais e publicação
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

# --- CONFIGURAÇÃO DE PÁGINA ---
st.set_page_config(
    page_title="Grajaú Tem | Portal Oficial",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS INTEGRADO GRAJAÚ TEM + RESPONSIVO ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .main .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
    #MainMenu, footer, header {visibility: hidden;}
    
    .header-container { 
        background: linear-gradient(135deg, #0047AB 0%, #FF8C00 100%); 
        padding: 30px 20px; 
        border-radius: 0 0 35px 35px; 
        text-align: center; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.2); 
        margin-bottom: 20px;
        margin-top: -1rem;
        color: white;
    }
    .logo-principal { font-weight: 900; font-size: 48px; letter-spacing: -1px; text-shadow: 1px 1px 3px rgba(0,0,0,0.3); }
    .logo-azul { color: #FFFFFF; }
    .logo-laranja { color: #FFD700; }
    .sub-logo { font-weight: 600; font-size: 14px; opacity: 0.95; margin-top: 5px; }
    
    .produto-card { background: #f8f9fa; border-radius: 12px; padding: 10px; margin: 5px 0; border: 1px solid #e9ecef; color: #333; }
    .social-profile-header { background: linear-gradient(to bottom, #0047AB, #002D6B); height: 120px; border-radius: 20px 20px 0 0; position: relative; margin-bottom: 60px; }
    .social-profile-avatar { width: 110px; height: 110px; border-radius: 50%; border: 5px solid white; position: absolute; bottom: -55px; left: 20px; object-fit: cover; background: #eee; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }
    
    @media (max-width: 640px) {
        .logo-principal { font-size: 36px; }
        .header-container { padding: 20px 15px; }
        .stButton button { width: 100%; }
    }
</style>
""", unsafe_allow_html=True)

# --- CABEÇALHO ---
st.markdown("""
<div class="header-container">
    <div class="logo-principal"><span class="logo-azul">GRAJAÚ</span> <span class="logo-laranja">TEM</span></div>
    <div class="sub-logo">O portal de serviços da sua região - by GeralJá</div>
</div>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO DE ESTADOS ---
if 'modo_noite' not in st.session_state:
    st.session_state.modo_noite = False
for key, default in {
    'tema_claro': False, 'auth': False, 'admin_logado': False,
    'minha_lat': -23.5505, 'minha_lon': -46.6333,
    'security_check': False, 'js_disponivel': True, 'pre_cadastro': None
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# --- MOTOR GLOBAL ---
class GeralJaEngine:
    def __init__(self):
        self.fuso = pytz.timezone('America/Sao_Paulo')
    def sanitizar(self, codigo_bruto):
        if not codigo_bruto: return ""
        limpo = codigo_bruto.replace('\u00a0', ' ').replace('\xa0', ' ')
        return ''.join(ch for ch in limpo if ch in '\n\t\r' or ord(ch) >= 32)

engine = GeralJaEngine()
fuso_br = engine.fuso

# --- CONFIGURAÇÃO DE CHAVES ---
client_groq = None
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    if "GROQ_API_KEY" in st.secrets:
        client_groq = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error(f"Erro ao carregar Secrets: {e}")

# --- CONEXÃO FIREBASE ---
@st.cache_resource
def conectar_banco_master():
    if not firebase_admin._apps:
        try:
            b64_key = st.secrets["firebase"]["base64"]
            cred_dict = json.loads(base64.b64decode(b64_key).decode("utf-8"))
            firebase_admin.initialize_app(credentials.Certificate(cred_dict))
        except Exception as e:
            st.error(f"FALHA FIREBASE: {e}")
            st.stop()
    return firebase_admin.get_app()

app_engine = conectar_banco_master()
db = firestore.client()

# --- FUNÇÕES AUXILIARES ---
def limpar_whatsapp(numero):
    num = re.sub(r'\D', '', str(numero))
    if not num.startswith('55') and len(num) >= 10:
        num = f"55{num}"
    return num

def normalizar(texto):
    if not texto: return ""
    return "".join(ch for ch in unicodedata.normalize('NFKD', texto) if unicodedata.category(ch) != 'Mn').lower()

def calcular_distancia_real(lat1, lon1, lat2, lon2):
    try:
        if None in [lat1, lon1, lat2, lon2]: return 999.0
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return round(R * c, 1)
    except: return 999.0

def buscar_opcoes_dinamicas(documento, padrao):
    try:
        doc = db.collection("configuracoes").document(documento).get()
        if doc.exists:
            return doc.to_dict().get("lista", padrao)
        return padrao
    except: return padrao

def safe_image_src(valor):
    if not valor: return "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    v = str(valor)
    if v.startswith("http") or v.startswith("data:image"): return v
    return f"data:image/jpeg;base64,{v}"

def otimizar_imagem_admin(imagem_upload):
    try:
        img = Image.open(imagem_upload)
        if img.mode == 'RGBA': img = img.convert('RGB')
        img.thumbnail((800, 800))
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=80)
        return base64.b64encode(buffer.getvalue()).decode()
    except: return None

def normalizar_para_ia(texto):
    if not texto: return ""
    return "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn').lower().strip()

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
        if client_groq:
            prompt = f"O usuário buscou: '{texto}'. Categorias: {CATEGORIAS_OFICIAIS}. Responda apenas o NOME DA CATEGORIA."
            res = client_groq.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama3-8b-8192", temperature=0.1)
            return res.choices[0].message.content.strip()
        return "NAO_ENCONTRADO"
    except: return "NAO_ENCONTRADO"

def criar_link_zap(numero, msg):
    return f"https://api.whatsapp.com/send?phone={numero}&text={urllib.parse.quote(msg)}"

def finalizar_e_alinhar_layout():
    st.write("")

# --- NOVAS FUNÇÕES 6.0 ---
def publicar_noticia_local(titulo, texto, foto_upload):
    try:
        foto_b64 = otimizar_imagem_admin(foto_upload)
        if not foto_b64: return False
        db.collection("noticias_locais").add({
            "titulo": titulo, "texto": texto, "foto_b64": foto_b64,
            "data_criacao": datetime.now(fuso_br), "ativo": True
        })
        return True
    except: return False

def processar_link_universal(url):
    try:
        return {"titulo": f"Produto de {urllib.parse.urlparse(url).netloc}", "link": url, "sucesso": True}
    except: return {"titulo": "Link inválido", "sucesso": False}

# --- CONSTANTES ---
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
    "pizza": "Pizzaria", "pizzaria": "Pizzaria", "lanche": "Lanchonete", "hamburguer": "Lanchonete",
    "comida": "Restaurante", "doce": "Doceria", "acai": "Açaí", "sorvete": "Sorveteria",
    "cerveja": "Adega", "roupa": "Loja de Roupas", "sapato": "Calçados", "remedio": "Farmácia",
    "cabelo": "Barbearia/Salão", "celular": "Assistência Técnica", "computador": "TI",
    "geladeira": "Refrigeração", "vazamento": "Encanador", "cano": "Encanador",
    "curto": "Eletricista", "pintar": "Pintor", "reforma": "Pedreiro", "telhado": "Telhadista",
    "carro": "Mecânico", "pneu": "Borracheiro", "frete": "Freteiro", "faxina": "Diarista"
}

# --- ABAS ---
lista_abas = ["🔍 BUSCAR", "🚀 CADASTRAR", "👤 MEU PERFIL", "⭐ FEEDBACK"]
with st.sidebar:
    comando = st.text_input("Código", type="password", placeholder="Acesso admin")
    if comando in ["abracadabra", "geralja_master"]:
        lista_abas.append("👑 ADMIN")
    if comando in ["financeiro2026", "geralja_master"]:
        lista_abas.append("📊 FINANCEIRO")

menu_abas = st.tabs(lista_abas)
abas_dict = {nome.split()[1].lower(): i for i, nome in enumerate(lista_abas)}

# ABA BUSCAR
with menu_abas[0]:
    st.markdown("### O que você procura no Grajaú hoje?")
    
    # Notícias locais
    noticias_locais = db.collection("noticias_locais").where("ativo", "==", True).order_by("data_criacao", direction=firestore.Query.DESCENDING).limit(3).stream()
    for n in noticias_locais:
        d = n.to_dict()
        st.info(f"🚨 **{d.get('titulo')}** — {d.get('texto')[:100]}...")
    
    c1, c2 = st.columns([3,1])
    termo_busca = c1.text_input("Buscar", placeholder="Ex: pizzaria, encanador")
    raio_km = c2.select_slider("Raio", [1,3,5,10,20,50], value=5)
    
    if termo_busca:
        cat_ia = processar_ia_avancada(termo_busca)
        profs = db.collection("profissionais").where("area", "==", cat_ia).where("aprovado", "==", True).stream()
        for p_doc in profs:
            p = p_doc.to_dict()
            dist = calcular_distancia_real(st.session_state.minha_lat, st.session_state.minha_lon, p.get('lat', LAT_REF), p.get('lon', LON_REF))
            if dist <= raio_km:
                st.markdown(f"**{p.get('nome')}** — {dist}km — {p.get('descricao','')[:60]}")
                st.link_button("WhatsApp", criar_link_zap(limpar_whatsapp(p.get('whatsapp','')), "Olá, vi no Grajaú Tem"))

# ABA CADASTRAR
with menu_abas[1]:
    st.header("Cadastre seu negócio")
    with st.form("cadastro"):
        nome = st.text_input("Nome")
        whatsapp = st.text_input("WhatsApp")
        area = st.selectbox("Área", CATEGORIAS_OFICIAIS)
        descricao = st.text_area("Descrição")
        link_import = st.text_input("Importar vitrine (link Shopee/Insta)")
        if st.form_submit_button("Cadastrar"):
            if link_import:
                processar_link_universal(link_import)
            db.collection("profissionais").add({"nome": nome, "whatsapp": limpar_whatsapp(whatsapp), "area": area, "descricao": descricao, "aprovado": False, "criado_em": datetime.now(fuso_br)})
            st.success("Cadastro enviado!")

# ABA PERFIL
with menu_abas[2]:
    st.info("Faça login para gerenciar seu perfil")

# ABA FEEDBACK
with menu_abas[3]:
    st.slider("Nota", 1,5,5)
    st.text_area("Comentário")
    if st.button("Enviar"): st.success("Obrigado!")

# ABA ADMIN
if "👑 ADMIN" in lista_abas:
    with menu_abas[lista_abas.index("👑 ADMIN")]:
        st.header("Painel Admin")
        tab1, tab2 = st.tabs(["Validar", "Publicar Notícia"])
        with tab1:
            pendentes = db.collection("profissionais").where("aprovado", "==", False).stream()
            for doc in pendentes:
                d = doc.to_dict()
                if st.button(f"Aprovar {d.get('nome')}", key=doc.id):
                    db.collection("profissionais").document(doc.id).update({"aprovado": True})
        with tab2:
            with st.form("noticia"):
                t = st.text_input("Título")
                txt = st.text_area("Texto")
                foto = st.file_uploader("Foto")
                if st.form_submit_button("Publicar"):
                    if publicar_noticia_local(t, txt, foto):
                        st.success("Publicado!")

# RODAPÉ
st.markdown("---")
st.caption("© 2026 Grajaú Tem | GeralJá 6.0")
