# ==============================================================================
# GERALJÁ: SISTEMA INTEGRADO MASTER (CÓDIGO COMPLETO - REVISADO & EXPANDIDO)
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
import difflib
from PIL import Image
from datetime import datetime
from urllib.parse import quote

# Importação segura de geolocalização do Streamlit
try:
    from streamlit_js_eval import streamlit_js_eval, get_geolocation
except ImportError:
    streamlit_js_eval = None
    get_geolocation = None

# ------------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DE AMBIENTE E PERFORMANCE
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="GeralJá | Soluções Locais",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Oculta elementos padrão do Streamlit
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. GERENCIAMENTO DE TEMA (ESCURO / CLARO)
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
# 3. TRATAMENTO DE IMAGENS E FALLBACK SVG
# ------------------------------------------------------------------------------
AVATAR_PADRAO_SVG = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%230047AB'><path d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z'/></svg>"

def otimizar_e_converter_b64(file_upload, max_largura=400, qualidade=70):
    """ Otimiza fotos enviadas evitando ultrapassar limites de payload do Firebase """
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
# 4. CONEXÃO AO BANCO DE DADOS FIREBASE & CONFIGURAÇÕES STRIPE
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
                st.error("⚠️ Chave Base64 do Firebase não encontrada nos Secrets.")
                st.stop()
        except Exception as e:
            st.error(f"❌ FALHA NA INFRAESTRUTURA FIREBASE: {e}")
            st.stop()
    return firebase_admin.get_app()

app_engine = conectar_banco_master()
db = firestore.client()

# Links e Secrets do Stripe
STRIPE_PUBLIC_KEY = st.secrets.get("STRIPE_PUBLIC_KEY", "")
STRIPE_LINK_10 = st.secrets.get("STRIPE_LINK_10", "#")
STRIPE_LINK_50 = st.secrets.get("STRIPE_LINK_50", "#")
STRIPE_LINK_100 = st.secrets.get("STRIPE_LINK_100", "#")

# ------------------------------------------------------------------------------
# 5. CONSTANTES, DICIONÁRIOS E CONFIGURAÇÕES LOCAIS
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
    "pizza": "Pizzaria", "pizzaria": "Pizzaria", "fome": "Pizzaria", "massa": "Pizzaria",
    "lanche": "Lanchonete", "hamburguer": "Lanchonete", "burger": "Lanchonete", "salgado": "Lanchonete",
    "comida": "Restaurante", "marmita": "Restaurante", "churrasco": "Churrascaria", "sushi": "Comida Japonesa",
    "doce": "Doceria", "bolo": "Confeiteiro(a)", "pao": "Padaria", "cafe": "Cafeteria", "adega": "Adega", "cerveja": "Adega",
    "roupa": "Loja de Roupas", "sapato": "Calçados", "celular": "Assistência Técnica", "notebook": "TI",
    "cabelo": "Barbearia/Salão", "unha": "Manicure e Pedicure", "dentista": "Odontologia", "remedio": "Farmácia",
    "pet": "Pet Shop", "racao": "Pet Shop", "vet": "Veterinário", "vazamento": "Encanador", "curto": "Eletricista",
    "pintar": "Pintor", "pedreiro": "Pedreiro", "gesso": "Gesseiro", "carro": "Mecânico", "pneu": "Borracheiro",
    "frete": "Freteiro", "mudanca": "Freteiro", "faxina": "Diarista / Faxineira", "jardim": "Jardineiro"
}

# ------------------------------------------------------------------------------
# 6. UTILITÁRIOS E MOTOR DE BUSCA COM INTELIGÊNCIA FUZZY (TOLERANTE A ERROS)
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
    """
    Inteligência de Busca com Tolerância a Falhas e Erros de Digitação.
    1. Executa busca exata ou por palavra-chave no mapa de conceitos.
    2. Caso não encontre, aplica difflib (fuzzy matching) para encontrar a palavra
       ou categoria mais próxima em termos de semelhança gráfica/fonética.
    """
    if not texto: 
        return "Vazio"
    
    t_clean = normalizar_para_ia(texto)
    palavras = t_clean.split()
    
    # PASSO 1: Busca Exata ou Substring nos Conceitos
    for chave, categoria in CONCEITOS_EXPANDIDOS.items():
        if re.search(rf"\b{re.escape(normalizar_para_ia(chave))}\b", t_clean):
            return categoria
            
    # PASSO 2: Busca Exata nas Categorias Oficiais
    for cat in CATEGORIAS_OFICIAIS:
        if normalizar_para_ia(cat) in t_clean:
            return cat

    # PASSO 3: Algoritmo de Aproximação Fuzzy (Corretor para palavras com erros)
    chaves_norm = {normalizar_para_ia(k): k for k in CONCEITOS_EXPANDIDOS.keys()}
    cats_norm = {normalizar_para_ia(c): c for c in CATEGORIAS_OFICIAIS}
    
    lista_chaves = list(chaves_norm.keys())
    lista_cats = list(cats_norm.keys())

    for p in palavras:
        if len(p) < 3:
            continue # Ignora preposições/palavras curtas

        # Tenta aproximar com os conceitos expandidos (ex: "pisa" -> "pizza")
        match_chave = difflib.get_close_matches(p, lista_chaves, n=1, cutoff=0.62)
        if match_chave:
            chave_orig = chaves_norm[match_chave[0]]
            return CONCEITOS_EXPANDIDOS[chave_orig]

        # Tenta aproximar com o nome de alguma categoria oficial (ex: "mecanicoo" -> "Mecânico")
        match_cat = difflib.get_close_matches(p, lista_cats, n=1, cutoff=0.62)
        if match_cat:
            return cats_norm[match_cat[0]]

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

def finalizar_e_alinhar_layout():
    """ Rodapé Moderno, Responsivo e Visualmente Atraente """
    st.write("---")
    is_dark = st.session_state.get('modo_noite', True)
    bg_box = "#161B22" if is_dark else "#FFFFFF"
    text_main = "#F8FAFC" if is_dark else "#0F172A"
    text_sub = "#94A3B8" if is_dark else "#64748B"
    border_color = "#30363D" if is_dark else "#E2E8F0"
    
    st.markdown(f"""
        <style>
            .footer-card {{
                background-color: {bg_box};
                border: 1px solid {border_color};
                border-radius: 28px;
                padding: 35px 20px 25px 20px;
                margin-top: 40px;
                text-align: center;
                box-shadow: 0 12px 30px rgba(0,0,0,0.08);
            }}
            .footer-pills-container {{
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 10px;
                margin-bottom: 22px;
            }}
            .footer-pill {{
                background: rgba(0, 71, 171, 0.08);
                color: #0047AB;
                border: 1px solid rgba(0, 71, 171, 0.2);
                padding: 8px 16px;
                border-radius: 50px;
                font-size: 0.82rem;
                font-weight: 700;
                display: inline-flex;
                align-items: center;
                gap: 6px;
            }}
            .footer-brand {{
                font-size: 1.4rem;
                font-weight: 800;
                letter-spacing: -0.5px;
                margin-bottom: 6px;
            }}
            .footer-tagline {{
                color: {text_sub};
                font-size: 0.9rem;
                font-weight: 500;
                margin-bottom: 20px;
            }}
            .footer-copyright {{
                color: {text_sub};
                font-size: 0.78rem;
                border-top: 1px solid {border_color};
                padding-top: 18px;
                margin-top: 18px;
            }}
        </style>
        <div class="footer-card">
            <div class="footer-pills-container">
                <span class="footer-pill">🛡️ Sistema 100% Verificado</span>
                <span class="footer-pill">⚡ Direct no WhatsApp</span>
                <span class="footer-pill">💳 Pagamentos Via Stripe & PIX</span>
                <span class="footer-pill">🤖 IA Tolerante a Erros</span>
            </div>
            <div class="footer-brand"><span style="color:#0047AB;">GERAL</span><span style="color:#FF8C00;">JÁ</span></div>
            <div class="footer-tagline">Conectando você aos melhores profissionais e comercios da sua região em segundos.</div>
            <div class="footer-copyright">© 2026 GeralJá | Tecnologia e Soluções Locais. Todos os direitos reservados.</div>
        </div>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 7. HEADER PRINCIPAL DA APLICAÇÃO
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
# 8. SISTEMA DE MENU E ABAS
# ------------------------------------------------------------------------------
lista_abas = ["🔍 BUSCAR & VITRINE", "🚀 CADASTRAR", "👤 MEU PERFIL", "👑 ADMIN", "⭐ FEEDBACK"]
comando = st.sidebar.text_input("Comando Secreto", type="password")
if comando == "abracadabra":
    lista_abas.append("📊 FINANCEIRO")

menu_abas = st.tabs(lista_abas)

# ==============================================================================
# ABA 1: BUSCA + VITRINE SOCIAL (COM IA INTELIGENTE A ERROS + SLIDER CORRIGIDO)
# ==============================================================================
with menu_abas[0]:
    st.markdown("### 🏙️ Quem você procura no seu bairro hoje?")
    
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
    
    # VALOR 15 DEVIDAMENTE INCLUÍDO NAS OPÇÕES DO SLIDER (SEM ValueError)
    raio_km = c2.select_slider("Raio (KM)", options=[1, 3, 5, 10, 15, 20, 50, 100, 500], value=15)

    # ESTILIZAÇÃO DO FEED SOCIAL
    st.markdown("""
    <style>
        .feed-card {
            background: #ffffff;
            border-radius: 22px;
            border: 1px solid #e2e8f0;
            padding: 20px;
            margin-bottom: 25px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
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
        .badge-cat {
            background: #e0f2fe;
            color: #0369a1;
            font-weight: 700;
            font-size: 12px;
            padding: 4px 10px;
            border-radius: 12px;
            display: inline-block;
        }
        .badge-elite {
            background: #fef3c7;
            color: #b45309;
            font-weight: 800;
            font-size: 11px;
            padding: 4px 8px;
            border-radius: 10px;
        }
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
        }
        .pill-faisca {
            background: #fff7ed;
            color: #c2410c;
        }
        .insta-gallery {
            display: flex;
            gap: 12px;
            overflow-x: auto;
            padding: 8px 0 14px 0;
        }
        .gallery-item {
            flex: 0 0 220px;
            height: 270px;
            border-radius: 16px;
            overflow: hidden;
        }
        .gallery-item img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .btn-social-zap {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            background: #25D366;
            color: white !important;
            padding: 14px;
            border-radius: 14px;
            font-weight: 800;
            font-size: 16px;
            text-decoration: none;
            margin-top: 15px;
        }
    </style>
    """, unsafe_allow_html=True)

    if termo_busca:
        cat_ia = processar_ia_avancada(termo_busca)
        
        if cat_ia != "NAO_ENCONTRADO" and cat_ia != "Vazio":
            st.info(f"✨ Inteligência GeralJá: Identificamos que você busca por **{cat_ia}**!")
            profs = db.collection("profissionais").where("area", "==", cat_ia).where("aprovado", "==", True).stream()
        else:
            st.warning("🔎 Buscando por palavra-chave aproximada no perfil...")
            profs = db.collection("profissionais").where("aprovado", "==", True).stream()

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
                <p style="color: #856404; margin: 6px 0 0 0;">Tente aumentar o raio de distância ou seja o primeiro parceiro cadastrado nessa área!</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            for p in lista_ranking:
                is_elite = p.get('verificado') and p.get('saldo', 0) > 0
                zap_limpo = limpar_whatsapp(p['id'])
                msg_zap = quote(f"Olá {p.get('nome')}, vi seu perfil na Vitrine do GeralJá!")
                link_zap = f"https://api.whatsapp.com/send?phone={zap_limpo}&text={msg_zap}"
                
                foto_p = p.get('foto_url')
                if not foto_p or len(str(foto_p)) < 50:
                    foto_p = AVATAR_PADRAO_SVG

                fotos_lista = p.get('portfolio_imgs', [])
                fotos_html = ""
                for img_item in fotos_lista[:6]:
                    src = img_item if str(img_item).startswith("data") else f"data:image/jpeg;base64,{img_item}"
                    fotos_html += f'<div class="gallery-item"><img src="{src}"></div>'

                ring_class = "story-ring-elite" if is_elite else "story-ring"
                
                st.markdown(f"""
                <div class="feed-card">
                    <div class="feed-header">
                        <div class="user-info-group">
                            <div class="{ring_class}">
                                <img src="{foto_p}" class="foto-avatar">
                            </div>
                            <div>
                                <h3 style="margin:0; color:#0f172a;">{p.get('nome','').upper()} {"☑️" if p.get('verificado') else ""}</h3>
                                <span class="badge-cat">{p.get('area')}</span>
                            </div>
                        </div>
                        <div>{"<span class='badge-elite'>⭐ DESTAQUE</span>" if is_elite else ""}</div>
                    </div>

                    <div style="font-size: 13.5px; color: #334155; margin: 10px 0;">{p.get('descricao','')}</div>

                    <div class="orkut-pills">
                        <span class="pill-orkut">📍 {p['dist']:.1f} km</span>
                        <span class="pill-orkut pill-faisca">🔥 Confiável</span>
                        <span class="pill-orkut">⭐ {p.get('rating', 5.0)}/5</span>
                        <span class="pill-orkut">👀 {p.get('cliques', 0)} visitas</span>
                    </div>

                    {"<div class='insta-gallery'>" + fotos_html + "</div>" if fotos_html else ""}

                    <a href="{link_zap}" target="_blank" class="btn-social-zap">
                        💬 CHAMAR NO WHATSAPP AGORA
                    </a>
                </div>
                """, unsafe_allow_html=True)

                db.collection("profissionais").document(p['id']).update({"cliques": p.get('cliques', 0) + 1})

# ==============================================================================
# ABA 2: CADASTRAR
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
        
        endereco_input = st.text_input("Endereço de Atendimento")
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

                lat_salvar, lon_salvar = LAT_REF, LON_REF
                end_oficial = endereco_input
                if endereco_input:
                    g_lat, g_lon, g_end = obter_coords_google(endereco_input)
                    if g_lat and g_lon:
                        lat_salvar, lon_salvar, end_oficial = g_lat, g_lon, g_end

                foto_final = ""
                if foto_upload:
                    b64_img = otimizar_e_converter_b64(foto_upload, max_largura=350, qualidade=70)
                    foto_final = f"data:image/jpeg;base64,{b64_img}"

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
                    "cliques": 0,
                    "rating": 5.0,
                    "lat": lat_salvar,
                    "lon": lon_salvar,
                    "data_cadastro": datetime.now().strftime("%d/%m/%Y")
                }

                doc_ref.set(novo_pro)
                st.balloons()
                st.success(f"🎉 Cadastro realizado com sucesso! Bônus de {saldo_atual} moedas ativo.")
            except Exception as e:
                st.error(f"❌ Erro ao salvar cadastro: {e}")

# ==============================================================================
# ABA 3: MEU PERFIL (SISTEMA DE MOEDAS VIA STRIPE OU PIX)
# ==============================================================================
with menu_abas[2]:
    if 'auth' not in st.session_state: st.session_state.auth = False

    if not st.session_state.get('auth'):
        st.subheader("🚀 Acesso ao Painel do Parceiro")
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
                st.error("Credenciais inválidas.")
    else:
        doc_ref = db.collection("profissionais").document(st.session_state.user_id)
        d = doc_ref.get().to_dict() or {}

        st.write(f"### Olá, {d.get('nome', 'Parceiro')}!")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Saldo de Moedas 🪙", f"{d.get('saldo', 0)}")
        m2.metric("Visitas ao Perfil 🚀", f"{d.get('cliques', 0)}")
        m3.metric("Status no Sistema", "🟢 ATIVO" if d.get('aprovado') else "🟡 PENDENTE")

        st.divider()

        with st.expander("💳 COMPRAR MOEDAS (CARTÃO DE CRÉDITO VIA STRIPE OU PIX)", expanded=True):
            st.markdown("#### Escolha como deseja recarregar suas moedas:")
            
            t_stripe, t_pix = st.tabs(["💳 Cartão de Crédito / Débito (Stripe)", "⚡ PIX Instantâneo"])

            with t_stripe:
                st.write("Processamento 100% seguro via **Stripe**:")
                col_st1, col_st2, col_st3 = st.columns(3)
                
                with col_st1:
                    st.markdown("##### 🪙 10 Moedas")
                    st.write("**R$ 10,00**")
                    if STRIPE_LINK_10 != "#":
                        st.link_button("💳 Pagar com Stripe", STRIPE_LINK_10, use_container_width=True)
                    else:
                        st.info("Link Stripe em configuração")

                with col_st2:
                    st.markdown("##### 🪙 50 Moedas")
                    st.write("**R$ 45,00** *(Com Desconto)*")
                    if STRIPE_LINK_50 != "#":
                        st.link_button("💳 Pagar com Stripe", STRIPE_LINK_50, use_container_width=True)
                    else:
                        st.info("Link Stripe em configuração")

                with col_st3:
                    st.markdown("##### 🪙 100 Moedas")
                    st.write("**R$ 80,00** *(Melhor Valor)*")
                    if STRIPE_LINK_100 != "#":
                        st.link_button("💳 Pagar com Stripe", STRIPE_LINK_100, use_container_width=True)
                    else:
                        st.info("Link Stripe em configuração")

            with t_pix:
                st.warning(f"Chave PIX Oficial: `{PIX_OFICIAL}`")
                c1, c2, c3 = st.columns(3)
                if c1.button("10 Moedas (R$ 10)"): st.code(PIX_OFICIAL)
                if c2.button("50 Moedas (R$ 45)"): st.code(PIX_OFICIAL)
                if c3.button("100 Moedas (R$ 80)"): st.code(PIX_OFICIAL)
                st.link_button("📲 ENVIAR COMPROVANTE WHATSAPP", f"https://api.whatsapp.com/send?phone={ZAP_ADMIN}&text=Comprovante%20do%20usuario%20{st.session_state.user_id}", use_container_width=True)

        with st.expander("📸 EDIÇÃO DE PERFIL E FOTOS"):
            with st.form("form_edit_perfil"):
                n_nome = st.text_input("Nome de Exibição", d.get('nome', ''))
                n_desc = st.text_area("Descrição do Perfil / Serviços", d.get('descricao', ''))
                n_foto = st.file_uploader("Trocar Foto do Perfil", type=['jpg','png','jpeg'])
                n_portfolio = st.file_uploader("Fotos da Vitrine (Até 4)", type=['jpg','png','jpeg'], accept_multiple_files=True)

                if st.form_submit_button("SALVAR ALTERAÇÕES", use_container_width=True):
                    up = {"nome": n_nome, "descricao": n_desc}
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
                    st.success("✅ Perfil atualizado com sucesso!")
                    time.sleep(1)
                    st.rerun()

        if st.button("SAIR DA CONTA", use_container_width=True):
            st.session_state.auth = False
            st.rerun()

# ==============================================================================
# ABA 4: ADMIN / TERMINAL MASTER
# ==============================================================================
with menu_abas[3]:
    st.markdown("## 👑 Terminal Master GeralJá")
    access_adm = st.text_input("Senha Master", type="password", key="auth_master")

    if access_adm == CHAVE_ADMIN:
        st.success("🔓 Painel Master Desbloqueado.")
        todos_profs_docs = list(db.collection("profissionais").stream())
        profs_data = [p.to_dict() | {"id": p.id} for p in todos_profs_docs]

        for p in profs_data:
            pid = p['id']
            with st.expander(f"👤 {p.get('nome','').upper()} ({pid})"):
                val_m = st.number_input("Adicionar Moedas", 1, 500, 10, key=f"m_{pid}")
                if st.button("➕ CREDITAR MOEDAS", key=f"add_{pid}"):
                    db.collection("profissionais").document(pid).update({"saldo": p.get('saldo', 0) + val_m})
                    st.rerun()

# ==============================================================================
# ABA 5: FEEDBACK
# ==============================================================================
with menu_abas[4]:
    st.header("⭐ Avalie a Experiência no GeralJá")
    nota_usr = st.slider("Nota", 1, 5, 5)
    comentario_usr = st.text_area("Comentário")
    if st.button("Enviar Avaliação", type="primary"):
        db.collection("feedbacks").add({"nota": nota_usr, "comentario": comentario_usr, "data": datetime.now()})
        st.success("Obrigado pelo seu feedback!")

# ==============================================================================
# ABA OPCIONAL: FINANCEIRO
# ==============================================================================
if "📊 FINANCEIRO" in lista_abas and len(menu_abas) > 5:
    with menu_abas[5]:
        st.header("📊 Painel Financeiro GeralJá")
        profs_all = list(db.collection("profissionais").stream())
        df_fin = pd.DataFrame([p.to_dict() for p in profs_all])
        if not df_fin.empty:
            st.dataframe(df_fin[['nome', 'whatsapp', 'saldo', 'cliques', 'data_cadastro']])

# Executa e renderiza o novo rodapé responsivo
finalizar_e_alinhar_layout()
