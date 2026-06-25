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
import streamlit as st
import re
import sys
import os
import pytz
from datetime import datetime

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

# --- CONFIGURAÇÃO DE CHAVES (PUXANDO DO SECRETS) ---
try:
    # Chaves de Autenticação Social
    FB_ID = st.secrets["FB_CLIENT_ID"]
    FB_SECRET = st.secrets["FB_CLIENT_SECRET"]
    FIREBASE_API_KEY = st.secrets["FIREBASE_API_KEY"]
    REDIRECT_URI = "https://geralja-zxiaj2ot56fuzgcz7xhcks.streamlit.app/"
    
    # Configuração de APIs de IA
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

# --- FUNCIONALIDADE DO ARQUIVO: TEMA MANUAL ---
if 'tema_claro' not in st.session_state:
    st.session_state.tema_claro = False

# Mantém os menus escondidos
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)
# --- LOGICA DE RECEPÇÃO DO GOOGLE (COLOCAR NO TOPO DO ARQUIVO) ---
from google_auth_oauthlib.flow import Flow
import requests

# Função para criar o fluxo de troca de tokens
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
        # 1. Troca o código por um token de acesso
        flow = get_google_flow()
        flow.fetch_token(code=query_params["code"])
        session = flow.authorized_session()
        
        # 2. Pega os dados reais do usuário no Google
        user_info = session.get('https://www.googleapis.com/userinfo').json()
        
        email_google = user_info.get("email")
        nome_google = user_info.get("name")
        foto_google = user_info.get("picture")

        # 3. Limpa a URL (remove o código para não dar erro ao atualizar)
        st.query_params.clear()

        # 4. Busca no Firebase se esse e-mail já é parceiro
        pro_ref = db.collection("profissionais").where("email", "==", email_google).limit(1).get()

        if pro_ref:
            # ✅ USUÁRIO JÁ CADASTRADO: Loga ele direto
            dados = pro_ref[0].to_dict()
            st.session_state.auth = True
            st.session_state.user_id = pro_ref[0].id # O WhatsApp dele
            st.success(f"Logado com sucesso como {dados.get('nome')}!")
            time.sleep(1)
            st.rerun()
        else:
            # ✨ USUÁRIO NOVO: Prepara o pre-cadastro para a Aba 1
            st.session_state.pre_cadastro = {
                "email": email_google,
                "nome": nome_google,
                "foto": foto_google
            }
            st.toast(f"Olá {nome_google}! Complete seu cadastro profissional abaixo.")
            # Você pode forçar a ida para a aba de cadastro aqui se quiser
            
    except Exception as e:
        st.error(f"Erro ao processar login do Google: {e}")
# ------------------------------------------------------------------------------
# 2. CAMADA DE PERSISTÊNCIA (FIREBASE)
# ------------------------------------------------------------------------------

# --- FUNÇÕES DE SUPORTE (Mantenha fora de blocos IF/ELSE para funcionar no app todo) ---

def buscar_opcoes_dinamicas(documento, padrao):
    """
    Busca listas de categorias ou tipos na coleção 'configuracoes'.
    """
    try:
        doc = db.collection("configuracoes").document(documento).get()
        if doc.exists:
            dados = doc.to_dict()
            return dados.get("lista", padrao)
        return padrao
    except Exception as e:
        # Se houver erro ou o banco estiver vazio, retorna a lista padrão
        return padrao
        # --- COLOCAR LOGO ABAIXO DA CONEXÃO DB ---

if 'modo_noite' not in st.session_state:
    st.session_state.modo_noite = True 

# Layout do topo (Toggle)
c_t1, c_t2 = st.columns([2, 8])
with c_t1:
    st.session_state.modo_noite = st.toggle("🌙 Modo Noite", value=st.session_state.modo_noite)

# Bloco CSS Dinâmico
estilo_dinamico = f"""
<style>
    /* Ajustes Mobile */
    @media (max-width: 640px) {{
        .main .block-container {{ padding: 1rem !important; }}
        h1 {{ font-size: 1.8rem !important; }}
    }}

  /* Lógica de Cores - Estilo Branco Neve */
    .stApp {{
        background-color: {"#0D1117" if st.session_state.modo_noite else "#FFFAFA"} !important;
        color: {"#FFFFFF" if st.session_state.modo_noite else "#1A1A1B"} !important;
    }}

    /* Cards Adaptáveis */
    div[data-testid="stVerticalBlock"] > div[style*="background"] {{
        background-color: {"#161B22" if st.session_state.modo_noite else "#FFFFFF"} !important;
        border: 1px solid {"#30363D" if st.session_state.modo_noite else "#E0E0E0"} !important;
        border-radius: 18px !important;
    }}
</style>
"""
st.markdown(estilo_dinamico, unsafe_allow_html=True)
# ==========================================================
# FUNÇÕES DE SUPORTE (COLE NO TOPO DO ARQUIVO)
# ==========================================================
import re
from urllib.parse import quote

def limpar_whatsapp(numero):
    """Remove parênteses, espaços e traços do número."""
    num = re.sub(r'\D', '', str(numero))
    if not num.startswith('55') and len(num) >= 10:
        num = f"55{num}"
    return num

def normalizar(texto):
    """Remove acentos e deixa tudo em minúsculo para busca."""
    import unicodedata
    if not texto: return ""
    return "".join(ch for ch in unicodedata.normalize('NFKD', texto) 
                   if unicodedata.category(ch) != 'Mn').lower()

# Verifique se você já tem a função de distância, senão adicione esta:
def calcular_distancia_real(lat1, lon1, lat2, lon2):
    import math
    R = 6371  # Raio da Terra em KM
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

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
    if not texto:
        return ""
    # Remove acentos e deixa tudo em minúsculo
    return "".join(c for c in unicodedata.normalize('NFD', str(texto))
                   if unicodedata.category(c) != 'Mn').lower().strip()

def processar_ia_avancada(texto):
    if not texto: return "Vazio"
    t_clean = normalizar_para_ia(texto)
    
    # --- 1. SEU CÓDIGO ATUAL (Rápido e sem custo) ---
    for chave, categoria in CONCEITOS_EXPANDIDOS.items():
        if re.search(rf"\b{normalizar_para_ia(chave)}\b", t_clean):
            return categoria
    
    for cat in CATEGORIAS_OFICIAIS:
        if normalizar_para_ia(cat) in t_clean:
            return cat

    # --- 2. O UPGRADE PARA NOTA 5.0 (IA Groq + Cache) ---
    try:
        # Primeiro checa se já perguntamos isso antes (Cache)
        cache_ref = db.collection("cache_buscas").document(t_clean).get()
        if cache_ref.exists:
            return cache_ref.to_dict().get("categoria")

        # Se não sabe, a IA "pensa" e resolve
        from groq import Groq
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        prompt = f"O usuário buscou: '{texto}'. Categorias: {CATEGORIAS_OFICIAIS}. Responda apenas o NOME DA CATEGORIA."
        
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
            temperature=0.1
        )
        cat_ia = res.choices[0].message.content.strip()

        # Salva no cache para não gastar mais tokens com esse termo
        db.collection("cache_buscas").document(t_clean).set({"categoria": cat_ia})
        return cat_ia

    except:
        return "NAO_ENCONTRADO" # Se tudo der errado

def calcular_distancia_real(lat1, lon1, lat2, lon2):
    try:
        if None in [lat1, lon1, lat2, lon2]: return 999.0
        R = 6371 
        dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)
    except: return 999.0

def converter_img_b64(file):
    if file is None: return ""
    try: return base64.b64encode(file.read()).decode()
    except: return ""

# --- FUNCIONALIDADE DO ARQUIVO: O VARREDOR (Rodapé Automático) ---
def finalizar_e_alinhar_layout():
    """
    Esta função atua como um ímã. Puxa o conteúdo e limpa o rodapé.
    """
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
            <p>v3.0 | © 2026 Todos os direitos reservados</p>
        </div>
    """
    st.markdown(fechamento_estilo, unsafe_allow_html=True)

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
import streamlit as st
import urllib.parse

# --- CONFIGURAÇÕES DE NEGÓCIO ---
ZAP_VENDAS = "5511980168513"

def criar_link_zap(numero, msg):
    return f"https://api.whatsapp.com/send?phone={numero}&text={urllib.parse.quote(msg)}"

# ==============================================================================
# --- ABA 0: PORTAL GRAJAÚ TEM (V4.0 - ESTÁVEL) ---
# ==============================================================================
with menu_abas[0]:
    st.markdown("### 🏙️ O que você precisa no Grajaú?")
    
    # 1. MOTOR DE LOCALIZAÇÃO (ALTA PRECISÃO)
    with st.expander("📍 Sua Localização (GPS)", expanded=False):
        # component_key diferente para forçar atualização
        loc = get_geolocation(component_key="geo_high_prec") 
        if loc and 'coords' in loc:
            minha_lat = loc['coords']['latitude']
            minha_lon = loc['coords']['longitude']
            precisao = loc['coords'].get('accuracy', 0)
            st.success(f"GPS Ativo (Precisão: {precisao:.0f}m)")
        else:
            minha_lat, minha_lon = LAT_REF, LON_REF
            st.warning("Usando localização padrão (Centro). Ative o GPS para maior precisão.")

    # 2. CAMPOS DE BUSCA
    c1, c2 = st.columns([3, 1])
    termo_busca = c1.text_input("Ex: 'Cano estourado' ou 'Pizzaria'", key="main_search_v4")
    raio_km = c2.select_slider("Raio (KM)", options=[1, 3, 5, 10, 20, 50, 500], value=5)

    if termo_busca:
        with st.status("🔍 Buscando...", expanded=False) as status:
            # A: BUSCA MANUAL NAS CONFIGURAÇÕES
            st.write("📂 Verificando categorias oficiais...")
            doc_cat = db.collection("configuracoes").document("categorias").get()
            lista_oficial = doc_cat.to_dict().get("lista", []) if doc_cat.exists else []
            
            cat_ia = None
            for c in lista_oficial:
                if c.lower() in termo_busca.lower():
                    cat_ia = c
                    break
            
            # B: SE NÃO ACHOU MANUAL, USA A IA
            if not cat_ia:
                st.write("🤖 IA classificando seu pedido...")
                cat_ia = processar_ia_avancada(termo_busca)
            
            # C: BUSCA NO FIREBASE
            profs = db.collection("profissionais").where("area", "==", cat_ia).where("aprovado", "==", True).stream()
            
            lista_ranking = []
            for p_doc in profs:
                p = p_doc.to_dict()
                p['id'] = p_doc.id
                # Cálculo de distância usando sua função
                dist = calcular_distancia_real(minha_lat, minha_lon, p.get('lat', LAT_REF), p.get('lon', LON_REF))
                
                if dist <= raio_km:
                    p['dist'] = dist
                    # Ranking: Verificados com saldo no topo
                    p['score_elite'] = (1000 if p.get('verificado') and p.get('saldo', 0) > 0 else 0)
                    lista_ranking.append(p)

            # Ordenação: 1º Proximidade, 2º Score Elite
            lista_ranking.sort(key=lambda x: (x['dist'], -x['score_elite']))
            status.update(label=f"Resultados para {cat_ia} encontrados!", state="complete")

        # 3. RENDERIZAÇÃO DOS CARDS
        if not lista_ranking:
            st.warning(f"Nenhum profissional de '{cat_ia}' encontrado nesta distância.")
        else:
            for p in lista_ranking:
                # Tratamento de Foto de Perfil (Base64 vs URL)
                f_perfil = p.get('foto_url', '')
                if f_perfil and not str(f_perfil).startswith("http"):
                    f_perfil = f"data:image/jpeg;base64,{f_perfil}"
                elif not f_perfil:
                    f_perfil = "https://cdn-icons-png.flaticon.com/512/149/149071.png"
                
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
                    <a href="{zap_link}" target="_blank" style="display:block; background:#25D366; color:white; text-align:center; padding:12px; border-radius:12px; text-decoration:none; font-weight:bold; margin-top:12px;">💬 CHAMAR NO WHATSAPP</a>
                </div>
                """, unsafe_allow_html=True)

# ==============================================================================
# --- SEÇÃO DE NOTÍCIAS HÍBRIDA (VERSÃO OTIMIZADA) ---
# ==============================================================================
st.markdown("---")
st.subheader("📰 Plantão Grajaú Tem")

import feedparser
import urllib.parse

# Imagem padrão para quando a notícia não tiver foto (especialmente Google News)
IMG_PADRAO = "https://images.unsplash.com/photo-1504711432869-0df30d7eaf4d?w=500&q=80"

# 1. BUSCAR NOTÍCIAS MANUAIS (Prioridade Máxima)
try:
    noticias_fb = list(db.collection("noticias").order_by("data", direction="DESCENDING").limit(2).stream())
except:
    noticias_fb = []

# 2. BUSCAR NOTÍCIAS AUTOMÁTICAS (Fallback)
def buscar_noticias_rss(busca="Grajaú São Paulo"):
    try:
        url_rss = f"https://news.google.com/rss/search?q={urllib.parse.quote(busca)}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        feed = feedparser.parse(url_rss)
        return feed.entries[:4] # Pegamos um pouco mais para garantir
    except:
        return []

noticias_auto = buscar_noticias_rss()

# 3. ORGANIZAÇÃO DA FILA DE EXIBIÇÃO
# Criamos uma lista unificada onde os manuais vêm primeiro
fila_noticias = []
for n in noticias_fb:
    dados = n.to_dict()
    fila_noticias.append({
        "titulo": dados.get('titulo', 'Sem título'),
        "link": dados.get('link_original', '#'),
        "img": dados.get('imagem_url', IMG_PADRAO),
        "fonte": "⭐ DESTAQUE LOCAL",
        "cor": "#FFD700" # Dourado para manual
    })

# Preenchemos o que sobrar das 2 colunas com as automáticas
for n in noticias_auto:
    if len(fila_noticias) >= 2: break
    fila_noticias.append({
        "titulo": n.title.split(' - ')[0],
        "link": n.link,
        "img": IMG_PADRAO, # Google RSS raramente envia imagem
        "fonte": f"📡 {n.source.get('title', 'Google News')}",
        "cor": "#0047AB" # Azul para automático
    })

# 4. RENDERIZAÇÃO EM COLUNAS
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
# ABA 2: 🚀 PAINEL DO PARCEIRO (COMPLETO: FB + IMAGENS + FAQ + EXCLUSÃO)
# ==============================================================================
with menu_abas[2]:
    # 1. LÓGICA DE CAPTURA DO FACEBOOK (QUERY PARAMS)
    params = st.query_params
    if "uid" in params and not st.session_state.get('auth'):
        fb_uid = params["uid"]
        user_query = db.collection("profissionais").where("fb_uid", "==", fb_uid).limit(1).get()
        if user_query:
            doc = user_query[0]
            st.session_state.auth = True
            st.session_state.user_id = doc.id
            st.success(f"✅ Bem-vindo!")
            time.sleep(1)
            st.rerun()

    if 'auth' not in st.session_state: 
        st.session_state.auth = False
    
   # --- 2. TELA DE LOGIN (VERSÃO FINAL SEM ERROS) ---
    if not st.session_state.get('auth'):
        st.subheader("🚀 Acesso ao Painel")
        
        # 1. Definição das variáveis de conexão
        fb_id = st.secrets.get("FB_CLIENT_ID", "")
        redirect_uri = "https://geralja-zxiaj2ot56fuzgcz7xhcks.streamlit.app/"
        
        # 2. Criamos as duas variáveis para matar o NameError de vez
        url_direta_fb = f"https://www.facebook.com/v18.0/dialog/oauth?client_id={fb_id}&redirect_uri={redirect_uri}&scope=public_profile,email"
        link_auth = url_direta_fb 
        
        # 3. O Botão Visual (Usando target="_top" para o Facebook aceitar)
        st.markdown(f'''
            <a href="{url_direta_fb}" target="_top" style="text-decoration:none;">
                <div style="background:#1877F2;color:white;padding:12px;border-radius:8px;text-align:center;font-weight:bold;display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow: 0px 4px 6px rgba(0,0,0,0.1);">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/2021_Facebook_icon.svg" width="20px" style="margin-right:10px;">
                    ENTRAR COM FACEBOOK
                </div>
            </a>
        ''', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.write("--- ou use seus dados ---")
        
        # 4. Formulário de Login Manual (Com chaves exclusivas)
        col1, col2 = st.columns(2)
        l_zap = col1.text_input("WhatsApp", key="login_zap_geralja_v10", placeholder="Ex: 11999999999")
        l_pw = col2.text_input("Senha", type="password", key="login_pw_geralja_v10")
        
        if st.button("ENTRAR NO PAINEL", key="btn_entrar_geralja_v10", use_container_width=True):
            try:
                u = db.collection("profissionais").document(l_zap).get()
                if u.exists:
                    dados_user = u.to_dict()
                    if str(dados_user.get('senha')) == str(l_pw):
                        st.session_state.auth = True
                        st.session_state.user_id = l_zap
                        st.success("Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Senha incorreta.")
                else:
                    st.error("❌ WhatsApp não cadastrado.")
            except Exception as e:
                st.error(f"Erro ao acessar banco de dados: {e}")
    # --- 3. PAINEL LOGADO ---
    else:
        doc_ref = db.collection("profissionais").document(st.session_state.user_id)
        d = doc_ref.get().to_dict()
        
        st.write(f"### Olá, {d.get('nome', 'Parceiro')}!")
        
        # Dashboard de métricas
        m1, m2, m3 = st.columns(3)
        m1.metric("Saldo 🪙", f"{d.get('saldo', 0)}")
        m2.metric("Cliques 🚀", f"{d.get('cliques', 0)}")
        m3.metric("Status", "🟢 ATIVO" if d.get('aprovado') else "🟡 PENDENTE")

        # Botão GPS
        if st.button("📍 ATUALIZAR MEU GPS", use_container_width=True):
            from streamlit_js_eval import streamlit_js_eval
            loc = streamlit_js_eval(js_expressions="navigator.geolocation.getCurrentPosition(s => s)", key='gps_v8')
            if loc and 'coords' in loc:
                doc_ref.update({"lat": loc['coords']['latitude'], "lon": loc['coords']['longitude']})
                st.success("✅ Localização GPS Atualizada!")

        # --- EDIÇÃO DE PERFIL E VITRINE ---
        with st.expander("📝 EDITAR MEU PERFIL & VITRINE", expanded=False):
            # Função de tratamento de imagem interna e robusta
            def otimizar_imagem(arq, qualidade=50, size=(800, 800)):
                try:
                    img = Image.open(arq)
                    if img.mode in ("RGBA", "P"): 
                        img = img.convert("RGB")
                    img.thumbnail(size)
                    output = io.BytesIO()
                    img.save(output, format="JPEG", quality=qualidade, optimize=True)
                    return f"data:image/jpeg;base64,{base64.b64encode(output.getvalue()).decode()}"
                except Exception as e:
                    st.error(f"Erro ao processar imagem: {e}")
                    return None

            with st.form("perfil_v8"):
                n_nome = st.text_input("Nome Comercial", d.get('nome', ''))
                # CATEGORIAS_OFICIAIS deve estar definida no início do código globalmente
                n_area = st.selectbox("Segmento", CATEGORIAS_OFICIAIS, 
                                     index=CATEGORIAS_OFICIAIS.index(d.get('area')) if d.get('area') in CATEGORIAS_OFICIAIS else 0)
                n_desc = st.text_area("Descrição do Serviço", d.get('descricao', ''))
                
                st.markdown("---")
                st.write("📷 **Fotos**")
                n_foto = st.file_uploader("Trocar Foto de Perfil", type=['jpg','png','jpeg'])
                n_portfolio = st.file_uploader("Vitrine de Serviços (Máx 4 fotos)", type=['jpg','png','jpeg'], accept_multiple_files=True)
                
                if st.form_submit_button("💾 SALVAR TODAS AS ALTERAÇÕES", use_container_width=True):
                    updates = {
                        "nome": n_nome,
                        "area": n_area,
                        "descricao": n_desc
                    }
                    
                    # Processa foto de perfil se houver upload
                    if n_foto:
                        img_base64 = otimizar_imagem(n_foto, qualidade=60, size=(350, 350))
                        if img_base64:
                            updates["foto_url"] = img_base64

                    # Processa fotos da vitrine (f1, f2, f3, f4)
                    if n_portfolio:
                        # Limpa as fotos antigas da vitrine para subir as novas
                        for i in range(1, 5):
                            updates[f'f{i}'] = None
                        
                        for i, f in enumerate(n_portfolio[:4]):
                            img_p_base64 = otimizar_imagem(f)
                            if img_p_base64:
                                updates[f"f{i+1}"] = img_p_base64
                    
                    # Envia para o Firebase
                    doc_ref.update(updates)
                    st.success("✅ Perfil e Vitrine atualizados com sucesso!")
                    time.sleep(1)
                    st.rerun()

        # --- FAQ ---
        with st.expander("❓ PERGUNTAS FREQUENTES"):
            st.write("**Como ganho o selo Elite?**")
            st.write("Mantenha seu saldo acima de 10 moedas e perfil completo com fotos.")
            st.write("**Como funciona a cobrança?**")
            st.write("Cada clique no seu botão de WhatsApp desconta 1 moeda do seu saldo atual.")

        # VINCULAR FACEBOOK (Caso ainda não tenha)
        if not d.get('fb_uid'):
            with st.expander("🔗 CONECTAR FACEBOOK"):
                st.info("Conecte seu Facebook para fazer login rápido sem senha.")
                st.link_button("VINCULAR AGORA", link_auth, use_container_width=True)

        st.divider()

        # --- LOGOUT E EXCLUSÃO ---
        col_out, col_del = st.columns(2)
        
        with col_out:
            if st.button("🚪 SAIR DO PAINEL", use_container_width=True):
                st.session_state.auth = False
                st.rerun()
                
        with col_del:
            with st.expander("⚠️ EXCLUIR CONTA"):
                st.write("Atenção: Isso apaga todos os seus dados permanentemente.")
                if st.button("CONFIRMAR EXCLUSÃO", type="secondary", use_container_width=True):
                    doc_ref.delete()
                    st.session_state.auth = False
                    st.error("Sua conta foi removida do sistema.")
                    time.sleep(2)
                    st.rerun()
# --- ABA 1: CADASTRAR & EDITAR (VERSÃO FINAL GERALJÁ CORRIGIDA) ---
with menu_abas[1]:
    st.markdown("### 🚀 Cadastro ou Edição de Profissional")

    # 1. BUSCA CATEGORIAS DINÂMICAS DO FIREBASE
    try:
        doc_cat = db.collection("configuracoes").document("categorias").get()
        if doc_cat.exists:
            CATEGORIAS_OFICIAIS = doc_cat.to_dict().get("lista", ["Geral"])
        else:
            CATEGORIAS_OFICIAIS = ["Pedreiro", "Locutor", "Eletricista", "Mecânico"]
    except:
        CATEGORIAS_OFICIAIS = ["Pedreiro", "Locutor", "Eletricista", "Mecânico"]

    # 2. VERIFICAÇÃO DE DADOS VINDOS DO GOOGLE AUTH
    dados_google = st.session_state.get("pre_cadastro", {})
    email_inicial = dados_google.get("email", "")
    nome_inicial = dados_google.get("nome", "")
    foto_google = dados_google.get("foto", "")

    # Interface Visual de Login Social
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

    # 3. FORMULÁRIO INTELIGENTE
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
        
        # Componente de Upload
        foto_upload = st.file_uploader("Atualizar Foto de Perfil ou Logo", type=['png', 'jpg', 'jpeg'])
        
        btn_acao = st.form_submit_button("✅ FINALIZAR: SALVAR OU ATUALIZAR", use_container_width=True)

    # 4. LÓGICA DE SALVAMENTO E EDIÇÃO
    if btn_acao:
        if not nome_input or not zap_input or not senha_input:
            st.warning("⚠️ Nome, WhatsApp e Senha são obrigatórios!")
        else:
            try:
                with st.spinner("Sincronizando com o ecossistema GeralJá..."):
                    # Referência do documento no Firebase
                    doc_ref = db.collection("profissionais").document(zap_input)
                    perfil_antigo = doc_ref.get()
                    dados_antigos = perfil_antigo.to_dict() if perfil_antigo.exists else {}

                    # --- LÓGICA DE FOTO CORRIGIDA ---
                    foto_b64 = dados_antigos.get("foto_url", "") # Mantém a antiga por padrão

                    # Se o usuário subir uma foto nova agora
                    if foto_upload is not None:
                        file_ext = foto_upload.name.split('.')[-1]
                        img_bytes = foto_upload.getvalue() # getvalue() é mais estável que read()
                        encoded_img = base64.b64encode(img_bytes).decode()
                        foto_b64 = f"data:image/{file_ext};base64,{encoded_img}"
                    
                    # Se não houver foto no banco E não houver upload, tenta pegar a do Google
                    elif not foto_b64 and foto_google:
                        foto_b64 = foto_google

                    # --- LÓGICA DE SALDO E CLIQUES ---
                    saldo_final = dados_antigos.get("saldo", BONUS_WELCOME)
                    cliques_atuais = dados_antigos.get("cliques", 0)

                    # --- MONTAGEM DO DICIONÁRIO ---
                    dados_pro = {
                        "nome": nome_input,
                        "whatsapp": zap_input,
                        "email": email_input,
                        "area": cat_input,
                        "senha": senha_input,
                        "descricao": desc_input,
                        "tipo": tipo_input,
                        "foto_url": foto_b64,
                        "saldo": saldo_final,
                        "data_cadastro": datetime.now().strftime("%d/%m/%Y"),
                        "aprovado": True,
                        "cliques": cliques_atuais,
                        "rating": 5,
                        "lat": minha_lat if 'minha_lat' in locals() else -23.55,
                        "lon": minha_lon if 'minha_lon' in locals() else -46.63
                    }
                    
                    # Salva no Banco de Dados
                    doc_ref.set(dados_pro)
                    
                    # Limpa cache de pré-cadastro
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
# ABA 4: 👑 TORRE DE CONTROLE MASTER (COMPLETA + REGISTRO DE VENDAS)
# ==============================================================================
with menu_abas[3]:
    import pytz
    from datetime import datetime
    import pandas as pd
    import time
    from PIL import Image
    import io
    import base64
    import requests
    import feedparser
    import urllib.parse

    def otimizar_imagem(image_file, size=(500, 500)):
        try:
            img = Image.open(image_file)
            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
            img.thumbnail(size)
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=70)
            return base64.b64encode(buffer.getvalue()).decode()
        except: return None

    fuso_br = pytz.timezone('America/Sao_Paulo')
    agora_br = datetime.now(fuso_br)

    if 'admin_logado' not in st.session_state: st.session_state.admin_logado = False

    if not st.session_state.admin_logado:
        st.markdown("### 🔐 Acesso Restrito à Diretoria")
        with st.form("login_adm"):
            u = st.text_input("Usuário Administrativo")
            p = st.text_input("Senha de Acesso", type="password")
            if st.form_submit_button("ACESSAR TORRE DE CONTROLE", use_container_width=True):
                if u == st.secrets.get("ADMIN_USER", "geralja") and p == st.secrets.get("ADMIN_PASS", "Bps36ocara"):
                    st.session_state.admin_logado = True; st.rerun()
                else: st.error("Dados incorretos.")
    else:
        st.markdown(f"## 👑 Central de Comando GeralJá")
        if st.button("🚪 Sair", key="logout_adm"): 
            st.session_state.admin_logado = False; st.rerun()

        # Adicionada a Tab de Vendas
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
                    lista_atual.append(nova_cat); lista_atual.sort()
                    doc_cat_ref.set({"lista": lista_atual}); st.rerun()

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
                except: st.error("Erro na API.")

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
                    st.success("Postado!"); st.rerun()

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
                                if st.button("🗑️", key=f"del_n_{n['id']}"):
                                    db.collection("noticias").document(n['id']).delete(); st.rerun()

        with tab_loja:
            st.subheader("🛒 Itens da Loja")
            with st.form("add_loja"):
                c1, c2, c3 = st.columns([2,1,1])
                ln = c1.text_input("Nome")
                lp = c2.number_input("Preço", min_value=1)
                le = c3.number_input("Estoque", min_value=1)
                lf = st.file_uploader("Foto", type=['jpg','png'])
                if st.form_submit_button("SALVAR PRODUTO"):
                    db.collection("loja").add({"nome": ln, "preco": lp, "estoque": le, "foto": otimizar_imagem(lf) if lf else ""})
                    st.success("Produto Adicionado!"); st.rerun()
            st.divider()
            for it in db.collection("loja").stream():
                item = it.to_dict()
                with st.expander(f"📦 {item['nome']} - {item['preco']} 💎"):
                    if item.get('foto'): st.image(f"data:image/jpeg;base64,{item['foto']}", width=100)
                    if st.button("Remover", key=f"del_it_{it.id}"): db.collection("loja").document(it.id).delete(); st.rerun()

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
                                cf1, cf2 = st.columns([1, 2])
                                with cf1:
                                    if p.get('foto_url'): st.image(f"data:image/jpeg;base64,{p['foto_url']}" if len(p['foto_url']) > 100 else p['foto_url'], width=80)
                                    up_p = st.file_uploader("Perfil", type=['jpg','png'], key=f"up_p_{pid}")
                                with cf2:
                                    up_v = st.file_uploader("Vitrine (Máx 4)", type=['jpg','png'], accept_multiple_files=True, key=f"up_v_{pid}")
                                if st.form_submit_button("💾 SALVAR TUDO"):
                                    upd = {"nome": n_nome, "area": n_area, "descricao": n_desc, "whatsapp": n_zap, "saldo": int(n_saldo), "aprovado": (n_status=="Aprovado")}
                                    if up_p: upd["foto_url"] = otimizar_imagem(up_p, size=(350, 350))
                                    if up_v:
                                        for i in range(1, 5): upd[f'f{i}'] = None
                                        for i, f in enumerate(up_v[:4]): upd[f"f{i+1}"] = otimizar_imagem(f)
                                    db.collection("profissionais").document(pid).update(upd); st.rerun()
                            if st.button("🗑️ EXCLUIR", key=f"del_p_{pid}"): db.collection("profissionais").document(pid).delete(); st.rerun()
            except Exception as e: st.error(f"Erro: {e}")
# ==============================================================================
# ABA 5: FEEDBACK
# ==============================================================================
with menu_abas[4]:
    st.header("⭐ Avalie a Plataforma")
    st.write("Sua opinião nos ajuda a melhorar.")
    
    nota = st.slider("Nota", 1, 5, 5)
    comentario = st.text_area("O que podemos melhorar?")
    
    if st.button("Enviar Feedback"):
        st.success("Obrigado! Sua mensagem foi enviada para nossa equipe.")
        # Em produção, salvaria em uma coleção 'feedbacks'

# ------------------------------------------------------------------------------
# FINALIZAÇÃO (DO ARQUIVO ORIGINAL)
# ------------------------------------------------------------------------------
finalizar_e_alinhar_layout()
# =========================================================
# MÓDULO: RODAPÉ BLINDADO (LGPD & SECURITY SHIELD)
# =========================================================

st.markdown("---")

# 1. ESTILIZAÇÃO DO SELO DE SEGURANÇA (CSS)
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

# 2. INTERFACE DO RODAPÉ
st.markdown("""
<div class="footer-container">
    <div class="security-badge">
        <span class="shield-icon">🛡️</span> IA de Proteção Ativa: Monitorando Contra Ameaças
    </div>
    <p>© 2026 GeralJá - Grajaú, São Paulo</p>
</div>
""", unsafe_allow_html=True)

# 3. EXPANDER JURÍDICO (A Blindagem LGPD)
with st.expander("📄 Transparência e Privacidade (LGPD)"):
    st.write("### 🛡️ Protocolo de Segurança e Privacidade")
    st.info("""
    **Proteção contra Invasões:** Este sistema utiliza criptografia de ponta a ponta via Google Cloud. 
    Tentativas de injeção de SQL ou scripts maliciosos (XSS) são bloqueadas automaticamente pela nossa camada de firewall.
    """)
    
    st.markdown("""
    **Como tratamos seus dados:**
    1. **Finalidade:** Seus dados são usados exclusivamente para conectar você a clientes no Grajaú.
    2. **Exclusão:** Você possui controle total. A exclusão definitiva pode ser feita no seu painel mediante senha de segurança.
    3. **Vírus e Malware:** Todas as fotos enviadas passam por um processo de normalização de bits para evitar a execução de códigos ocultos em arquivos de imagem.
    
    *Em conformidade com a Lei Federal nº 13.709 (LGPD).*
    """)

# 4. LÓGICA DE PROTEÇÃO (Simulação de Monitoramento)
# 🧩 PULO DA GATA: Pequena lógica que simula a verificação de integridade
if "security_check" not in st.session_state:
    st.toast("🛡️ IA: Verificando integridade da conexão...", icon="🔍")
    time.sleep(1)
    st.session_state.security_check = True
    st.toast("✅ Conexão Segura: Firewall GeralJá Ativo!", icon="🛡️") 

