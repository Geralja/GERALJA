# ==============================================================================
# GERALJÁ: SISTEMA INTEGRADO MASTER (BRASIL ELITE EDITION - SOCIAL VITRINE)
# ==============================================================================
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import math
import re
import time
import pytz
import requests
import pandas as pd
import unicodedata
import io
from PIL import Image
from datetime import datetime
from urllib.parse import quote

# Tenta importar streamlit_js_eval de forma segura
try:
    from streamlit_js_eval import streamlit_js_eval, get_geolocation
except ImportError:
    streamlit_js_eval = None
    get_geolocation = None

# ------------------------------------------------------------------------------
# 1. CONFIGURAÇÃO ÚNICA DE AMBIENTE E PERFORMANCE
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="GeralJá | Soluções Locais",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Oculta menus nativos do Streamlit
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. MODO TEMA (ESCURO / CLARO ADAPTÁVEL)
# ------------------------------------------------------------------------------
if 'modo_noite' not in st.session_state:
    st.session_state.modo_noite = True

c_t1, c_t2 = st.columns([3, 7])
with c_t1:
    st.session_state.modo_noite = st.toggle("🌙 Modo Escuro / ☀️ Modo Claro", value=st.session_state.modo_noite)

estilo_dinamico = f"""
<style>
    @media (max-width: 640px) {{
        .main .block-container {{ padding: 0.8rem !important; }}
        h1 {{ font-size: 1.6rem !important; }}
    }}
    .stApp {{
        background-color: {"#0D1117" if st.session_state.modo_noite else "#F8FAFC"} !important;
        color: {"#FFFFFF" if st.session_state.modo_noite else "#0F172A"} !important;
    }}
    div[data-testid="stVerticalBlock"] > div[style*="background"] {{
        background-color: {"#161B22" if st.session_state.modo_noite else "#FFFFFF"} !important;
        border: 1px solid {"#30363D" if st.session_state.modo_noite else "#E2E8F0"} !important;
        border-radius: 20px !important;
    }}
</style>
"""
st.markdown(estilo_dinamico, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 3. COMPRESSÃO DE IMAGENS PIL & FALLBACK SVG
# ------------------------------------------------------------------------------
AVATAR_PADRAO_SVG = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%230047AB'><path d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z'/></svg>"

def otimizar_e_converter_b64(file_upload, max_largura=400, qualidade=70):
    """ Redimensiona e comprime a foto para ~30KB mantendo alta qualidade visual """
    if file_upload is None:
        return ""
    try:
        img = Image.open(file_upload)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        if img.width > max_largura or img.height > max_largura:
            img.thumbnail((max_largura, max_largura))
        
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=qualidade, optimize=True)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception:
        return ""

# ------------------------------------------------------------------------------
# 4. CAMADA DE PERSISTÊNCIA (FIREBASE & SECRETS)
# ------------------------------------------------------------------------------
@st.cache_resource
def conectar_banco_master():
    if not firebase_admin._apps:
        try:
            b64_key = None
            if "firebase" in st.secrets and "base64" in st.secrets["firebase"]:
                b64_key = st.secrets["firebase"]["base64"]
            elif "FIREBASE_BASE64" in st.secrets:
                b64_key = st.secrets["FIREBASE_BASE64"]

            if b64_key:
                decoded_json = base64.b64decode(b64_key).decode("utf-8")
                cred_dict = json.loads(decoded_json)
                cred = credentials.Certificate(cred_dict)
                return firebase_admin.initialize_app(cred)
            else:
                st.error("⚠️ Chave Base64 do Firebase não encontrada no Secrets.")
                st.stop()
        except Exception as e:
            st.error(f"❌ FALHA NA INFRAESTRUTURA FIREBASE: {e}")
            st.stop()
    return firebase_admin.get_app()

app_engine = conectar_banco_master()
db = firestore.client()

# Autenticação Externa (Opcional via Secrets)
FB_CLIENT_ID = st.secrets.get("FB_CLIENT_ID", "")
FB_CLIENT_SECRET = st.secrets.get("FB_CLIENT_SECRET", "")
FIREBASE_API_KEY = st.secrets.get("FIREBASE_API_KEY", "")
HANDLER_URL = "https://geralja-5bb49.firebaseapp.com/__/auth/handler"

# ------------------------------------------------------------------------------
# 5. POLÍTICAS E CONSTANTES
# ------------------------------------------------------------------------------
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ADMIN = "mumias"
BONUS_WELCOME = 20
LAT_REF = -23.5505
LON_REF = -46.6333

CATEGORIAS_OFICIAIS = [
    "Academia", "Acompanhante de Idosos", "Açougue", "Adega", "Adestrador de Cães", "Advocacia", "Agropecuária", 
    "Ajudante Geral", "Animador de Festas", "Arquiteto(a)", "Armarinho/Aviamentos", "Assistência Técnica", 
    "Aulas Particulares", "Auto Elétrica", "Auto Peças", "Babá (Nanny)", "Banho e Tosa", "Barbearia/Salão", 
    "Bazar", "Borracheiro", "Cabeleireiro(a)", "Cafeteria", "Calçados", "Calhas e Rufos", "Carreto", 
    "Celulares", "Chaveiro", "Churrascaria", "Clínica Médica", "Comida Japonesa", "Confeiteiro(a)", 
    "Contabilidade", "Costureira / Alfaiate", "Cuidador de Idosos", "Dedetização", "Desentupidora",
    "Diarista / Faxineira", "Doceria", "Eletrodomésticos", "Eletricista", "Eletrônicos", "Encanador", 
    "Escola Infantil", "Estética Automotiva", "Estética Facial", "Farmácia", "Fisioterapia", 
    "Fitness", "Floricultura", "Fotógrafo(a)", "Freteiro", "Funilaria e Pintura", 
    "Gesseiro", "Guincho 24h", "Hamburgueria", "Hortifruti", "Idiomas", "Imobiliária", 
    "Informática", "Jardineiro", "Joalheria", "Lanchonete", "Lava Jato", "Limpeza de Estofados", 
    "Loja de Roupas", "Loja de Variedades", "Madeireira", "Manicure e Pedicure", "Marceneiro", 
    "Marmoraria", "Material de Construção", "Mecânico", "Montador de Móveis", "Motoboy/Entregas", 
    "Móveis", "Moto Peças", "Nutricionista", "Odontologia", "Ótica", "Outro (Personalizado)", "Padaria", 
    "Papelaria", "Pastelaria", "Pedreiro", "Pet Shop", "Pintor", "Piscineiro", "Pizzaria", 
    "Psicologia", "Reforço Escolar", "Refrigeração", "Relojoaria", "Seguros", "Serralheiro", "Som e Alarme", 
    "Sorveteria", "Tatuagem/Piercing", "Técnico de Fogão", "Técnico de Lavadora", 
    "Telhadista", "TI", "Tintas", "Veterinário", "Vidraceiro"
]

CONCEITOS_EXPANDIDOS = {
    # Alimentação e Gastronomia
    "pizza": "Pizzaria", "pizzaria": "Pizzaria", "fome": "Pizzaria", "massa": "Pizzaria", "calzone": "Pizzaria",
    "lanche": "Lanchonete", "hamburguer": "Lanchonete", "burger": "Lanchonete", "x-tudo": "Lanchonete", "hot dog": "Lanchonete", "salgado": "Lanchonete", "coxinha": "Lanchonete", "pastel": "Pastelaria",
    "comida": "Restaurante", "almoco": "Restaurante", "marmita": "Restaurante", "jantar": "Restaurante", "churrasco": "Churrascaria", "espetinho": "Churrascaria", "sushi": "Comida Japonesa", "japonesa": "Comida Japonesa",
    "doce": "Doceria", "bolo": "Confeiteiro(a)", "festa": "Confeiteiro(a)", "sobremesa": "Doceria",
    "pao": "Padaria", "padaria": "Padaria", "cafe": "Cafeteria", "cafeteria": "Cafeteria",
    "acai": "Açaí", "sorvete": "Sorveteria", "picole": "Sorveteria",
    "cerveja": "Adega", "bebida": "Adega", "gelo": "Adega", "adega": "Adega", "vinho": "Adega", "vodka": "Adega",

    # Varejo e Serviços
    "roupa": "Loja de Roupas", "moda": "Loja de Roupas", "boutique": "Loja de Roupas", "brecho": "Loja de Roupas",
    "sapato": "Calçados", "tenis": "Calçados", "chinelo": "Calçados", "sandalia": "Calçados",
    "presente": "Loja de Variedades", "utilidades": "Loja de Variedades", "bazar": "Bazar",
    "relogio": "Relojoaria", "joia": "Joalheria", "otica": "Ótica", "oculos": "Ótica",

    # Saúde e Beleza
    "remedio": "Farmácia", "farmacia": "Farmácia", "drogaria": "Farmácia",
    "cabelo": "Barbearia/Salão", "barba": "Barbearia/Salão", "corte": "Barbearia/Salão", "unha": "Manicure e Pedicure", "manicure": "Manicure e Pedicure", "sobrancelha": "Estética Facial", "maquiagem": "Estética Facial",
    "academia": "Fitness", "treino": "Fitness", "musculacao": "Fitness",
    "dentista": "Odontologia", "dente": "Odontologia", "medico": "Clínica Médica",

    # Tecnologia e Manutenção
    "celular": "Assistência Técnica", "iphone": "Assistência Técnica", "tela": "Assistência Técnica", "carregador": "Assistência Técnica",
    "computador": "TI", "notebook": "TI", "formatar": "TI", "wifi": "TI", "pc": "TI", "impressora": "TI",
    "geladeira": "Refrigeração", "ar condicionado": "Refrigeração", "fogao": "Técnico de Fogão", "lavadora": "Técnico de Lavadora",
    "tv": "Eletrônicos", "som": "Som e Alarme",

    # Pets
    "pet": "Pet Shop", "racao": "Pet Shop", "cachorro": "Pet Shop", "gato": "Pet Shop", "banho e tosa": "Banho e Tosa", "veterinario": "Veterinário",

    # Serviços Técnicos e Obras
    "vazamento": "Encanador", "cano": "Encanador", "desentupir": "Desentupidora", "esgoto": "Desentupidora",
    "curto": "Eletricista", "fiacao": "Eletricista", "luz": "Eletricista", "chuveiro": "Eletricista", "tomada": "Eletricista",
    "pintar": "Pintor", "pintura": "Pintor", "parede": "Pintor",
    "reforma": "Pedreiro", "piso": "Pedreiro", "azulejo": "Pedreiro", "obra": "Pedreiro", "tijolo": "Pedreiro",
    "gesso": "Gesseiro", "drywall": "Gesseiro", "telhado": "Telhadista", "calha": "Calhas e Rufos",
    "solda": "Serralheiro", "portao": "Serralheiro", "vidro": "Vidraceiro", "box": "Vidraceiro", "chave": "Chaveiro",

    # Automotivo
    "carro": "Mecânico", "motor": "Mecânico", "oficina": "Mecânico", "pneu": "Borracheiro", "estepe": "Borracheiro",
    "guincho": "Guincho 24h", "reboque": "Guincho 24h", "lavajato": "Lava Jato", "polimento": "Estética Automotiva",

    # Logística e Lar
    "frete": "Freteiro", "mudanca": "Freteiro", "carreto": "Carreto", "montar": "Montador de Móveis", "armario": "Montador de Móveis",
    "faxina": "Diarista / Faxineira", "limpeza": "Diarista / Faxineira", "estofado": "Limpeza de Estofados",
    "jardim": "Jardineiro", "piscina": "Piscineiro", "ajudante": "Ajudante Geral"
}

# ------------------------------------------------------------------------------
# 6. UTILITÁRIOS E FUNÇÕES AUXILIARES
# ------------------------------------------------------------------------------
def limpar_whatsapp(numero):
    num = re.sub(r'\D', '', str(numero))
    if not num.startswith('55') and len(num) >= 10:
        num = f"55{num}"
    return num

def normalizar_para_ia(texto):
    if not texto: return ""
    return "".join(c for c in unicodedata.normalize('NFD', str(texto)) 
                   if unicodedata.category(c) != 'Mn').lower().strip()

def processar_ia_avancada(texto):
    if not texto: return "Vazio"
    t_clean = normalizar_para_ia(texto)
    for chave, categoria in CONCEITOS_EXPANDIDOS.items():
        if re.search(rf"\b{normalizar_para_ia(chave)}\b", t_clean):
            return categoria
    for cat in CATEGORIAS_OFICIAIS:
        if normalizar_para_ia(cat) in t_clean:
            return cat
    return "NAO_ENCONTRADO"

def calcular_distancia_real(lat1, lon1, lat2, lon2):
    try:
        if None in [lat1, lon1, lat2, lon2]: return 999.0
        R = 6371 
        dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)
    except: return 999.0

def buscar_opcoes_dinamicas(documento, padrao):
    try:
        doc = db.collection("configuracoes").document(documento).get()
        if doc.exists:
            return doc.to_dict().get("lista", padrao)
        return padrao
    except:
        return padrao

def obter_coords_google(endereco):
    api_key = st.secrets.get("GOOGLE_MAPS_API_KEY", None)
    if not api_key: return None, None, None
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={quote(endereco)}&key={api_key}"
    try:
        res = requests.get(url).json()
        if res.get('status') == 'OK':
            loc = res['results'][0]['geometry']['location']
            end_formatado = res['results'][0]['formatted_address']
            return loc['lat'], loc['lng'], end_formatado
    except: pass
    return None, None, None

def guardia_escanear_e_corrigir():
    status_log = []
    try:
        profs = db.collection("profissionais").stream()
        for p_doc in profs:
            dados = p_doc.to_dict()
            id_pro = p_doc.id
            correcoes = {}
            if not dados.get('area'): correcoes['area'] = "Ajudante Geral"
            if not dados.get('descricao'): correcoes['descricao'] = "Profissional cadastrado no GeralJá."
            if dados.get('saldo') is None: correcoes['saldo'] = 0
            if dados.get('lat') is None or dados.get('lon') is None:
                correcoes['lat'] = LAT_REF
                correcoes['lon'] = LON_REF
            if correcoes:
                db.collection("profissionais").document(id_pro).update(correcoes)
                status_log.append(f"✅ Corrigido: {id_pro}")
        return status_log if status_log else ["SISTEMA ÍNTEGRO: Nenhum erro encontrado."]
    except Exception as e:
        return [f"❌ Erro no Scanner: {e}"]

def scan_virus_e_scripts():
    alertas = []
    profs = db.collection("profissionais").stream()
    padroes_perigosos = [r"<script>", r"javascript:", r"DROP TABLE", r"OR 1=1"]
    for p_doc in profs:
        dados = p_doc.to_dict()
        conteudo = str(dados.get('nome', '')) + str(dados.get('descricao', ''))
        for padrao in padroes_perigosos:
            if re.search(padrao, conteudo, re.IGNORECASE):
                alertas.append(f"⚠️ PERIGO: Script em ID {p_doc.id}")
                db.collection("profissionais").document(p_doc.id).update({"aprovado": False})
    return alertas if alertas else ["LIMPO: Nenhum script malicioso detectado."]

def finalizar_e_alinhar_layout():
    st.write("---")
    st.markdown("""
        <style>
            .footer-clean { text-align: center; padding: 25px 10px; opacity: 0.85; font-size: 0.85rem; width: 100%; color: gray; }
            .security-badge { display: inline-flex; align-items: center; background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 20px; padding: 6px 18px; margin-bottom: 12px; color: #0f172a; font-weight: bold; }
        </style>
        <div class="footer-clean">
            <div class="security-badge"><span style="color:#22c55e; margin-right:8px;">🛡️</span> Proteção Ativa GeralJá</div>
            <p>🎯 <b>GeralJá</b> - Conectando você aos melhores profissionais da sua região.</p>
            <p>© 2026 Todos os direitos reservados</p>
        </div>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 7. CABEÇALHO VISUAL
# ------------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .header-container { background: linear-gradient(135deg, #FFFFFF 0%, #F1F5F9 100%); padding: 28px 15px; border-radius: 0 0 35px 35px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.06); border-bottom: 5px solid #FF8C00; margin-bottom: 25px; }
    .logo-azul { color: #0047AB; font-weight: 800; font-size: 42px; letter-spacing: -1.5px; }
    .logo-laranja { color: #FF8C00; font-weight: 800; font-size: 42px; letter-spacing: -1.5px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-container"><span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span><br><small style="color:#64748B; font-weight:700; letter-spacing:1px;">VITRINE SOCIAL & SERVIÇOS DA SUA REGIÃO</small></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 8. NAVEGAÇÃO E ABAS
# ------------------------------------------------------------------------------
lista_abas = ["🔍 BUSCAR & VITRINE", "🚀 CADASTRAR", "👤 MEU PERFIL", "👑 ADMIN", "⭐ FEEDBACK"]
comando = st.sidebar.text_input("Comando Secreto", type="password")
if comando == "abracadabra":
    lista_abas.append("📊 FINANCEIRO")

menu_abas = st.tabs(lista_abas)

# ==============================================================================
# ABA 1: BUSCA + VITRINE SOCIAL HÍBRIDA (INSTAGRAM + ORKUT + FACEBOOK)
# ==============================================================================
with menu_abas[0]:
    st.markdown("### 🏙️ Quem você procura no seu bairro hoje?")
    
    # Motor de GPS
    with st.expander("📍 Sua Localização (GPS)", expanded=False):
        minha_lat, minha_lon = LAT_REF, LON_REF
        if get_geolocation:
            loc = get_geolocation()
            if loc and 'coords' in loc:
                minha_lat, minha_lon = loc['coords']['latitude'], loc['coords']['longitude']
                st.success("Localização GPS ativada!")
            else:
                st.warning("GPS não detectado. Usando localização padrão.")
        else:
            st.info("Usando coordenadas padrão.")

    c1, c2 = st.columns([3, 1])
    termo_busca = c1.text_input("Ex: 'Chaveiro', 'Pizza', 'Diarista', 'Mecânico'", key="main_search")
    raio_km = c2.select_slider("Raio (KM)", options=[1, 3, 5, 10, 20, 50, 100, 500], value=15)

    # ESTILIZAÇÃO COMPLETA DE REDE SOCIAL (INSTAGRAM + ORKUT + FACEBOOK)
    st.markdown("""
    <style>
        .feed-card {
            background: #ffffff;
            border-radius: 22px;
            border: 1px solid #e2e8f0;
            padding: 20px;
            margin-bottom: 25px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
            transition: transform 0.2s ease;
        }
        .feed-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 15px;
        }
        .user-info-group {
            display: flex;
            align-items: center;
            gap: 14px;
        }
        /* Borda estilo Instagram Story */
        .story-ring {
            background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888);
            padding: 3px;
            border-radius: 50%;
            display: inline-block;
        }
        .story-ring-elite {
            background: linear-gradient(45deg, #FFD700, #FFA500, #FF8C00);
            padding: 3px;
            border-radius: 50%;
            display: inline-block;
        }
        .foto-avatar {
            width: 65px;
            height: 65px;
            border-radius: 50%;
            object-fit: cover;
            border: 2px solid white;
            background-color: #f1f5f9;
            display: block;
        }
        .user-title-box h3 {
            margin: 0;
            font-size: 18px;
            font-weight: 800;
            color: #0f172a;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .badge-cat {
            background: #e0f2fe;
            color: #0369a1;
            font-weight: 700;
            font-size: 12px;
            padding: 4px 10px;
            border-radius: 12px;
            display: inline-block;
            margin-top: 4px;
        }
        .badge-elite {
            background: #fef3c7;
            color: #b45309;
            font-weight: 800;
            font-size: 11px;
            padding: 4px 8px;
            border-radius: 10px;
            border: 1px solid #fde68a;
        }
        /* Selos no estilo Orkut */
        .orkut-pills {
            display: flex;
            gap: 8px;
            margin: 12px 0;
            font-size: 12px;
            font-weight: 700;
        }
        .pill-orkut {
            background: #f1f5f9;
            color: #475569;
            padding: 4px 10px;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }
        .pill-faisca {
            background: #fff7ed;
            color: #c2410c;
            border: 1px solid #ffedd5;
        }
        /* Carrossel Estilo Instagram Feed */
        .insta-gallery {
            display: flex;
            gap: 12px;
            overflow-x: auto;
            scroll-snap-type: x mandatory;
            padding: 8px 0 14px 0;
            scrollbar-width: none;
        }
        .insta-gallery::-webkit-scrollbar { display: none; }
        .gallery-item {
            flex: 0 0 220px;
            height: 270px;
            border-radius: 16px;
            overflow: hidden;
            position: relative;
            cursor: pointer;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }
        .gallery-item img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s;
        }
        .gallery-item:hover img {
            transform: scale(1.05);
        }
        /* Botão Ação WhatsApp Facebook/Instagram */
        .btn-social-zap {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            background: #25D366;
            color: white !important;
            text-align: center;
            padding: 14px;
            border-radius: 14px;
            font-weight: 800;
            font-size: 16px;
            text-decoration: none;
            margin-top: 15px;
            box-shadow: 0 4px 14px rgba(37, 211, 102, 0.3);
            transition: background 0.2s;
        }
        .btn-social-zap:hover { background: #1eb956; }
    </style>

    <script>
    function abrirModalInsta(src, link) {
        var m = document.getElementById('modalFeed');
        if (m) {
            document.getElementById('imgModalBox').src = src;
            document.getElementById('linkZapModalFeed').href = link;
            m.style.display = 'flex';
        }
    }
    function fecharModalInsta() {
        var m = document.getElementById('modalFeed');
        if (m) m.style.display = 'none';
    }
    </script>
    """, unsafe_allow_html=True)

    if termo_busca:
        cat_ia = processar_ia_avancada(termo_busca)
        st.info(f"✨ Inteligência GeralJá: Buscando por **{cat_ia}** em sua região...")

        profs = db.collection("profissionais").where("area", "==", cat_ia).where("aprovado", "==", True).stream()
        
        lista_ranking = []
        for p_doc in profs:
            p = p_doc.to_dict()
            p['id'] = p_doc.id
            dist = calcular_distancia_real(minha_lat, minha_lon, p.get('lat', LAT_REF), p.get('lon', LON_REF))
            
            if dist <= raio_km:
                p['dist'] = dist
                score = 0
                score += 500 if p.get('verificado') else 0
                score += (p.get('saldo', 0) * 10)
                score += (p.get('rating', 5) * 20)
                p['score_elite'] = score
                lista_ranking.append(p)

        lista_ranking.sort(key=lambda x: (-x['score_elite'], x['dist']))

        if not lista_ranking:
            st.markdown(f"""
            <div style="background-color: #FFF4E5; padding: 22px; border-radius: 18px; border-left: 6px solid #FF8C00; margin-top: 15px;">
                <h4 style="color: #856404; margin:0;">🔍 Nenhuma opção encontrada exatamente para esse raio.</h4>
                <p style="color: #856404; margin: 6px 0 0 0;">Seja o primeiro parceiro desse segmento no GeralJá!</p>
            </div>
            """, unsafe_allow_html=True)
            link_share = f"https://wa.me/?text={quote('Olá! Procurei por ' + cat_ia + ' no GeralJá e ainda não achei na nossa região. Cadastre-se gratis: https://geralja.com.br')}"
            st.markdown(f'<a href="{link_share}" target="_blank" style="text-decoration:none;"><div style="background:#22C55E; color:white; padding:14px; border-radius:12px; text-align:center; font-weight:bold; margin-top:12px;">📲 CONVIDAR UM AMIGO NO WHATSAPP</div></a>', unsafe_allow_html=True)
        else:
            for p in lista_ranking:
                is_elite = p.get('verificado') and p.get('saldo', 0) > 0
                zap_limpo = limpar_whatsapp(p['id'])
                msg_zap = quote(f"Olá {p.get('nome')}, vi seu perfil na Vitrine do GeralJá!")
                link_zap = f"https://api.whatsapp.com/send?phone={zap_limpo}&text={msg_zap}"
                
                # Trata Foto de Perfil com Fallback SVG para não quebrar nunca
                foto_p = p.get('foto_url')
                if not foto_p or len(str(foto_p)) < 50:
                    foto_p = AVATAR_PADRAO_SVG

                # Coleta Galeria do Portfólio (portfolio_imgs ou f1..f10)
                fotos_lista = p.get('portfolio_imgs', [])
                if not fotos_lista:
                    for i in range(1, 11):
                        f_data = p.get(f'f{i}')
                        if f_data and len(str(f_data)) > 50:
                            fotos_lista.append(f_data)

                fotos_html = ""
                for img_item in fotos_lista[:6]:
                    src = img_item if str(img_item).startswith("data") else f"data:image/jpeg;base64,{img_item}"
                    fotos_html += f'<div class="gallery-item" onclick="abrirModalInsta(\'{src}\', \'{link_zap}\')"><img src="{src}"></div>'

                ring_class = "story-ring-elite" if is_elite else "story-ring"
                
                # Renderiza Card Estilo Rede Social
                st.markdown(f"""
                <div class="feed-card">
                    <div class="feed-header">
                        <div class="user-info-group">
                            <div class="{ring_class}">
                                <img src="{foto_p}" class="foto-avatar">
                            </div>
                            <div class="user-title-box">
                                <h3>{p.get('nome','').upper()} {"☑️" if p.get('verificado') else ""}</h3>
                                <span class="badge-cat">{p.get('area')}</span>
                            </div>
                        </div>
                        <div>
                            {"<span class='badge-elite'>⭐ DESTAQUE</span>" if is_elite else ""}
                        </div>
                    </div>

                    <div style="font-size: 13.5px; color: #334155; line-height: 1.5; margin: 10px 0;">
                        {p.get('descricao','')}
                    </div>

                    <!-- Pílulas Estilo Orkut (Confiável / Legal / Recomendado) -->
                    <div class="orkut-pills">
                        <span class="pill-orkut">📍 {p['dist']:.1f} km</span>
                        <span class="pill-orkut pill-faisca">🔥 100% Confiável</span>
                        <span class="pill-orkut">⭐ {p.get('rating', 5.0)}/5</span>
                        <span class="pill-orkut">👀 {p.get('cliques', 0)} visitas</span>
                    </div>

                    {"<div class='insta-gallery'>" + fotos_html + "</div>" if fotos_html else ""}

                    <a href="{link_zap}" target="_blank" class="btn-social-zap">
                        💬 CHAMAR NO WHATSAPP AGORA
                    </a>
                </div>
                """, unsafe_allow_html=True)

                # Incrementa visitas no banco
                db.collection("profissionais").document(p['id']).update({"cliques": p.get('cliques', 0) + 1})

            # Estrutura do Modal Insta/Social em Tela Cheia
            st.markdown("""
            <div id="modalFeed" style="display:none; position:fixed; z-index:9999; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.92); align-items:center; justify-content:center; flex-direction:column; padding:15px;">
                <span onclick="fecharModalInsta()" style="position:absolute; top:20px; right:30px; color:white; font-size:42px; cursor:pointer; font-weight:bold;">&times;</span>
                <img id="imgModalBox" style="max-width:92%; max-height:72%; border-radius:16px; border: 3px solid #fff; object-fit:contain;">
                <a id="linkZapModalFeed" href="#" target="_blank" style="margin-top:20px; background:#25D366; color:white; padding:16px 36px; border-radius:30px; text-decoration:none; font-weight:800; font-size:16px;">
                    ✅ ENTRAR EM CONTATO PELO WHATSAPP
                </a>
            </div>
            """, unsafe_allow_html=True)

# ==============================================================================
# ABA 2: CADASTRAR (NOVO REGISTRO COM COMPRESSÃO PIL)
# ==============================================================================
with menu_abas[1]:
    st.markdown("### 🚀 Cadastro de Novo Parceiro")
    
    cats_dinamicas = buscar_opcoes_dinamicas("categorias", CATEGORIAS_OFICIAIS)
    
    with st.form("form_novo_profissional"):
        col_id1, col_id2 = st.columns(2)
        nome_input = col_id1.text_input("Nome do Profissional ou Empresa", placeholder="Ex: João Mecânico")
        zap_input = col_id2.text_input("WhatsApp (Apenas Números)", placeholder="Ex: 11991853488")
        
        col_id3, col_id4 = st.columns(2)
        categoria_input = col_id3.selectbox("Área Principal de Atuação", sorted(cats_dinamicas))
        senha_input = col_id4.text_input("Senha de Acesso ao Painel", type="password")
        
        endereco_input = st.text_input("Endereço de Atendimento (Rua, Bairro, Cidade)", placeholder="Ex: Av. Interlagos, 1000 - São Paulo")
        descricao_input = st.text_area("Descrição detalhada dos seus serviços")
        
        col_t1, col_t2 = st.columns(2)
        tipo_input = col_t1.radio("Tipo de Perfil", ["👨‍🔧 Autônomo / Profissional", "🏢 Comércio / Loja"], horizontal=True)
        foto_upload = col_t2.file_uploader("Foto do Perfil (JPG ou PNG)", type=['jpg', 'jpeg', 'png'])

        btn_finalizar = st.form_submit_button("✅ CONCLUIR E ATIVAR PERFIL", use_container_width=True)

    if btn_finalizar:
        if not nome_input or not zap_input or not senha_input:
            st.error("⚠️ Nome, WhatsApp e Senha são obrigatórios!")
        else:
            try:
                zap_id = limpar_whatsapp(zap_input)
                doc_ref = db.collection("profissionais").document(zap_id)
                doc_existente = doc_ref.get()

                # Processa Geocodificação
                lat_salvar, lon_salvar = LAT_REF, LON_REF
                end_oficial = endereco_input
                if endereco_input:
                    g_lat, g_lon, g_end = obter_coords_google(endereco_input)
                    if g_lat and g_lon:
                        lat_salvar, lon_salvar, end_oficial = g_lat, g_lon, g_end

                # Compressão PIL da Foto de Perfil
                foto_final = ""
                if foto_upload:
                    b64_img = otimizar_e_converter_b64(foto_upload, max_largura=350, qualidade=70)
                    foto_final = f"data:image/jpeg;base64,{b64_img}"
                elif doc_existente.exists:
                    foto_final = doc_existente.to_dict().get("foto_url", "")

                saldo_atual = doc_existente.to_dict().get("saldo", BONUS_WELCOME) if doc_existente.exists else BONUS_WELCOME

                novo_pro = {
                    "nome": nome_input,
                    "area": categoria_input,
                    "descricao": descricao_input,
                    "senha": senha_input,
                    "tipo": tipo_input,
                    "whatsapp": zap_id,
                    "endereco_digitado": endereco_input,
                    "endereco_oficial": end_oficial,
                    "foto_url": foto_final,
                    "saldo": saldo_atual,
                    "aprovado": True,
                    "verificado": False,
                    "cliques": doc_existente.to_dict().get("cliques", 0) if doc_existente.exists else 0,
                    "rating": 5.0,
                    "lat": lat_salvar,
                    "lon": lon_salvar,
                    "data_cadastro": datetime.now().strftime("%d/%m/%Y")
                }

                doc_ref.set(novo_pro)
                st.balloons()
                st.success(f"🎉 Cadastro realizado com sucesso! Você recebeu {saldo_atual} moedas de bônus.")
            except Exception as e:
                st.error(f"❌ Erro ao salvar cadastro: {e}")

# ==============================================================================
# ABA 3: MEU PERFIL (PAINEL DO PARCEIRO COM PIL EM FOTOS)
# ==============================================================================
with menu_abas[2]:
    # Checagem Auth Facebook
    params = st.query_params
    if "uid" in params and not st.session_state.get('auth'):
        fb_uid = params["uid"]
        user_query = db.collection("profissionais").where("fb_uid", "==", fb_uid).limit(1).get()
        if user_query:
            doc = user_query[0]
            st.session_state.auth = True
            st.session_state.user_id = doc.id
            st.success("✅ Autenticado via Facebook!")
            st.rerun()

    if 'auth' not in st.session_state: st.session_state.auth = False

    if not st.session_state.get('auth'):
        st.subheader("🚀 Acesso ao Painel do Parceiro")
        
        if FIREBASE_API_KEY:
            link_auth = f"{HANDLER_URL}?apiKey={FIREBASE_API_KEY}&providerId=facebook.com"
            st.markdown(f"""
                <a href="{link_auth}" target="_self" style="text-decoration: none;">
                    <div style="background-color: #1877F2; color: white; padding: 12px; border-radius: 12px; text-align: center; font-weight: bold; margin-bottom: 15px;">
                        🔵 ENTRAR COM FACEBOOK
                    </div>
                </a>
            """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        l_zap = col1.text_input("WhatsApp Cadastrado", key="login_zap")
        l_pw = col2.text_input("Sua Senha", type="password", key="login_pw")

        if st.button("ENTRAR NO PAINEL", use_container_width=True):
            zap_format = limpar_whatsapp(l_zap)
            u = db.collection("profissionais").document(zap_format).get()
            if u.exists and u.to_dict().get('senha') == l_pw:
                st.session_state.auth, st.session_state.user_id = True, zap_format
                st.rerun()
            else:
                st.error("Credenciais inválidas. Verifique seus dados.")
    else:
        doc_ref = db.collection("profissionais").document(st.session_state.user_id)
        d = doc_ref.get().to_dict() or {}

        st.write(f"### Olá, {d.get('nome', 'Parceiro')}!")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Saldo de Moedas 🪙", f"{d.get('saldo', 0)}")
        m2.metric("Visitas ao Perfil 🚀", f"{d.get('cliques', 0)}")
        m3.metric("Status no Sistema", "🟢 ATIVO" if d.get('aprovado') else "🟡 PENDENTE")

        if st.button("📍 Atualizar Minha Localização via GPS", use_container_width=True):
            if get_geolocation:
                loc = get_geolocation()
                if loc and 'coords' in loc:
                    doc_ref.update({"lat": loc['coords']['latitude'], "lon": loc['coords']['longitude']})
                    st.success("✅ Localização GPS atualizada no banco!")
                else: st.info("Buscando GPS...")

        st.divider()

        with st.expander("💎 ADQUIRIR MOEDAS E DESTAQUE (PIX)"):
            st.warning(f"Chave PIX Oficial: {PIX_OFICIAL}")
            c1, c2, c3 = st.columns(3)
            if c1.button("10 Moedas (R$ 10)"): st.code(PIX_OFICIAL)
            if c2.button("50 Moedas (R$ 45)"): st.code(PIX_OFICIAL)
            if c3.button("100 Moedas (R$ 80)"): st.code(PIX_OFICIAL)
            st.link_button("📲 ENVIAR COMPROVANTE WHATSAPP", f"https://api.whatsapp.com/send?phone={ZAP_ADMIN}&text=Comprovante%20PIX%20do%20usuario%20{st.session_state.user_id}", use_container_width=True)

        with st.expander("📸 ATUALIZAR FOTOS E VITRINE SOCIAL", expanded=True):
            with st.form("form_edit_perfil"):
                n_nome = st.text_input("Nome de Exibição", d.get('nome', ''))
                
                cats = buscar_opcoes_dinamicas("categorias", CATEGORIAS_OFICIAIS)
                idx_cat = cats.index(d.get('area')) if d.get('area') in cats else 0
                n_area = st.selectbox("Categoria Principal", sorted(cats), index=idx_cat)

                n_desc = st.text_area("Descrição do Perfil / Serviços", d.get('descricao', ''))
                
                n_foto = st.file_uploader("Trocar Foto do Perfil", type=['jpg','png','jpeg'])
                n_portfolio = st.file_uploader("Fotos do Portfólio / Vitrine (Até 4)", type=['jpg','png','jpeg'], accept_multiple_files=True)

                if st.form_submit_button("SALVAR ALTERAÇÕES", use_container_width=True):
                    up = {"nome": n_nome, "area": n_area, "descricao": n_desc}
                    
                    # Otimização PIL na atualização de perfil
                    if n_foto:
                        b64_p = otimizar_e_converter_b64(n_foto, max_largura=350, qualidade=70)
                        up["foto_url"] = f"data:image/jpeg;base64,{b64_p}"
                    
                    if n_portfolio:
                        port_imgs = []
                        for f in n_portfolio[:4]:
                            b64_port = otimizar_e_converter_b64(f, max_largura=600, qualidade=70)
                            port_imgs.append(f"data:image/jpeg;base64,{b64_port}")
                        up["portfolio_imgs"] = port_imgs

                    doc_ref.update(up)
                    st.success("✅ Perfil e galeria atualizados com sucesso!")
                    time.sleep(1)
                    st.rerun()

        if st.button("SAIR DA CONTA", use_container_width=True):
            st.session_state.auth = False
            st.rerun()

# ==============================================================================
# ABA 4: ADMIN / MASTER CONTROL
# ==============================================================================
with menu_abas[3]:
    st.markdown("## 👑 Terminal Master GeralJá")
    access_adm = st.text_input("Senha Master de Autoridade", type="password", key="auth_master")

    if access_adm == CHAVE_ADMIN:
        st.success("🔓 Painel Master Desbloqueado.")
        
        todos_profs_docs = list(db.collection("profissionais").stream())
        profs_data = [p.to_dict() | {"id": p.id} for p in todos_profs_docs]
        lista_pendentes = [p for p in profs_data if not p.get('aprovado')]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Parceiros", len(profs_data))
        c2.metric("Cliques Acumulados", sum(p.get('cliques', 0) for p in profs_data))
        c3.metric("Moedas em Circulação", f"💎 {sum(p.get('saldo', 0) for p in profs_data)}")
        c4.metric("Pendentes Aprovação", len(lista_pendentes))

        st.divider()

        t_gestao, t_aprova, t_expand, t_seguranca = st.tabs([
            "👥 PARCEIROS", "🆕 FILA DE APROVAÇÃO", "⚙️ CATEGORIAS", "🛡️ SEGURANÇA IA"
        ])

        with t_gestao:
            busca_p = st.text_input("🔍 Localizar por Nome ou Telefone", placeholder="Digite para filtrar...")
            for p in profs_data:
                pid = p['id']
                nome_p = p.get('nome', 'Sem Nome').upper()
                if not busca_p or busca_p.lower() in nome_p.lower() or busca_p in pid:
                    status_cor = "🟢" if p.get('aprovado') else "🔴"
                    elite_tag = "⭐" if p.get('verificado') else ""
                    with st.expander(f"{status_cor} {elite_tag} {nome_p} ({pid})"):
                        col_adm1, col_adm2 = st.columns(2)
                        with col_adm1:
                            st.write(f"**Área:** {p.get('area')}")
                            st.write(f"**Saldo:** {p.get('saldo', 0)} moedas")
                            st.write(f"**Senha:** `{p.get('senha')}`")
                            
                            is_ver = p.get('verificado', False)
                            if st.button(f"{'⚪ REMOVER SELO ELITE' if is_ver else '🌟 CONCEDER SELO ELITE'}", key=f"v_{pid}"):
                                db.collection("profissionais").document(pid).update({"verificado": not is_ver})
                                st.rerun()

                        with col_adm2:
                            val_m = st.number_input("Ajustar Moedas", 1, 500, 10, key=f"m_{pid}")
                            c_b1, c_b2 = st.columns(2)
                            if c_b1.button("➕ CREDITAR", key=f"add_{pid}"):
                                db.collection("profissionais").document(pid).update({"saldo": p.get('saldo', 0) + val_m})
                                st.rerun()
                            if c_b2.button("➖ DEBITAR", key=f"sub_{pid}"):
                                db.collection("profissionais").document(pid).update({"saldo": max(0, p.get('saldo', 0) - val_m)})
                                st.rerun()

                            if st.button("🗑️ BANIR PERFIL", key=f"del_{pid}", type="primary"):
                                db.collection("profissionais").document(pid).delete()
                                st.rerun()

        with t_aprova:
            if not lista_pendentes:
                st.info("Nenhum cadastro pendente de aprovação.")
            else:
                for p in lista_pendentes:
                    pid = p['id']
                    st.warning(f"PENDENTE: {p.get('nome')} | {p.get('area')} | Tel: {pid}")
                    if st.button("✅ APROVAR PERFIL", key=f"ok_{pid}"):
                        db.collection("profissionais").document(pid).update({"aprovado": True})
                        st.success("Aprovado com sucesso!")
                        st.rerun()

        with t_expand:
            n_cat_nova = st.text_input("Nova Categoria Profissional")
            if st.button("➕ Adicionar Categoria"):
                if n_cat_nova:
                    cats_atuais = buscar_opcoes_dinamicas("categorias", CATEGORIAS_OFICIAIS)
                    if n_cat_nova not in cats_atuais:
                        cats_atuais.append(n_cat_nova)
                        db.collection("configuracoes").document("categorias").set({"lista": cats_atuais})
                        st.success(f"Categoria '{n_cat_nova}' adicionada com sucesso!")
                        time.sleep(1)
                        st.rerun()

        with t_seguranca:
            st.markdown("#### 🛡️ Varredura e Correção do Banco")
            col_s1, col_s2 = st.columns(2)
            if col_s1.button("🔍 SCANNER DE SCRIPTS/INJEÇÃO", use_container_width=True):
                r_scripts = scan_virus_e_scripts()
                for r in r_scripts: st.write(r)
            
            if col_s2.button("🛠️ EXECUTAR AUTO-CURA NO BANCO", use_container_width=True):
                r_cura = guardia_escanear_e_corrigir()
                for c in r_cura: st.write(c)

    elif access_adm != "":
        st.error("🚨 Senha Incorreta!")

# ==============================================================================
# ABA 5: FEEDBACK
# ==============================================================================
with menu_abas[4]:
    st.header("⭐ Avalie a Experiência no GeralJá")
    nota_usr = st.slider("Qual nota você dá para o GeralJá?", 1, 5, 5)
    comentario_usr = st.text_area("Deixe seu comentário ou sugestão")
    
    if st.button("Enviar Avaliação", type="primary"):
        db.collection("feedbacks").add({
            "nota": nota_usr,
            "comentario": comentario_usr,
            "data": datetime.now()
        })
        st.success("Obrigado pelo seu feedback!")

# ==============================================================================
# ABA OPCIONAL: FINANCEIRO
# ==============================================================================
if "📊 FINANCEIRO" in lista_abas and len(menu_abas) > 5:
    with menu_abas[5]:
        st.header("📊 Painel Financeiro e Tráfego")
        profs_all = list(db.collection("profissionais").stream())
        df_fin = pd.DataFrame([p.to_dict() for p in profs_all])
        if not df_fin.empty:
            st.dataframe(df_fin[['nome', 'whatsapp', 'saldo', 'cliques', 'data_cadastro']])

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
            A maior vitrine da região: conectando moradores, profissionais e oportunidades.
        </p>
        <div style="margin-top: 8px;">
            <span style="background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 20px; padding: 4px 12px; color: #0f172a; font-size: 11px; font-weight: bold;">
                🛡️ Sistema com Proteção Ativa e IA Integrada
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
