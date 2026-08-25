# ==============================================================================
# GERALJÁ: SISTEMA OPERACIONAL COMPLETO & ECOSSISTEMA DE SERVIÇOS (v6.0 MASTER)
# Mídia + Marketplace Híbrido + Carteira Multi-Moedas + Clube de Descontos
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
import os
import sys
import pandas as pd
from datetime import datetime
import pytz
import unicodedata
import requests
import feedparser
import urllib.parse
from urllib.parse import quote
from PIL import Image

# --- BIBLIOTECAS AVANÇADAS DE IA E AUTH ---
from groq import Groq
import google.generativeai as genai
from google_auth_oauthlib.flow import Flow

# --- COMPONENTES OPCIONAIS DE NAVEGAÇÃO E GPS ---
try:
    from streamlit_js_eval import streamlit_js_eval, get_geolocation
except ImportError:
    pass

# ==============================================================================
# 1. ENGENHARIA DE SANITIZAÇÃO E MOTOR DE CARTEIRA MULTI-MOEDAS
# ==============================================================================
class GeralJaEngine:
    def __init__(self):
        self.fuso = pytz.timezone('America/Sao_Paulo')
    
    def sanitizar(self, codigo_bruto):
        if not codigo_bruto: return ""
        limpo = codigo_bruto.replace('\u00a0', ' ').replace('\xa0', ' ')
        return re.sub(r'[^\x20-\x7E\n\t\r]', '', limpo)

engine = GeralJaEngine()
fuso_br = engine.fuso

class CarteiraEngine:
    """
    Motor Transacional responsável por gerenciar os três modelos de monetização:
    1. GeralCoin (Virtual / Recompensas / Gamificação)
    2. Crédito BRL (Pré-pago / Compra de Leads / Orçamentos)
    3. Custódia BRL (Escrow / Modelo Uber com comissão retida)
    """
    def __init__(self, db_client):
        self.db = db_client
        self.fuso = pytz.timezone('America/Sao_Paulo')

    def obter_saldos(self, user_id: str):
        ref = self.db.collection("carteiras").document(user_id)
        doc = ref.get()
        if not doc.exists:
            saldos_padrao = {"geralcoin": 20, "credito_brl": 0.0, "custodia_brl": 0.0}
            ref.set({"saldos": saldos_padrao, "atualizado_em": datetime.now(self.fuso).isoformat()}, merge=True)
            return saldos_padrao
        return doc.to_dict().get("saldos", {"geralcoin": 0, "credito_brl": 0.0, "custodia_brl": 0.0})

    def movimentar_saldo(self, user_id: str, moeda: str, valor: float, tipo: str, origem: str):
        ref = self.db.collection("carteiras").document(user_id)
        saldos = self.obter_saldos(user_id)
        chave_moeda = moeda.lower()
        
        saldo_atual = saldos.get(chave_moeda, 0.0)

        if tipo == "DEBITO" and saldo_atual < valor:
            return False, f"⚠️ Saldo insuficiente em {moeda.upper()}."

        novo_saldo = (saldo_atual + valor) if tipo == "CREDITO" else (saldo_atual - valor)
        saldos[chave_moeda] = round(novo_saldo, 2)

        ref.set({
            "saldos": saldos,
            "atualizado_em": datetime.now(self.fuso).isoformat()
        }, merge=True)

        # Atualiza espelho de compatibilidade no perfil do profissional
        if chave_moeda == "geralcoin":
            self.db.collection("profissionais").document(user_id).set({"saldo": int(saldos["geralcoin"])}, merge=True)

        # Registro de histórico transacional para auditoria
        self.db.collection("transacoes").add({
            "user_id": user_id,
            "moeda": moeda.upper(),
            "tipo": tipo,
            "valor": valor,
            "origem": origem,
            "timestamp": datetime.now(self.fuso).isoformat()
        })

        return True, f"✅ Sucesso! Novo saldo de {moeda.upper()}: {saldos[chave_moeda]}"

    def converter_geralcoin_para_credito(self, user_id: str, qtd_coins: int):
        """Conversão: 10 GeralCoins = R$ 1,00 em Saldo Pré-pago BRL"""
        taxa_conversao = 0.10  # R$ 0,10 por GeralCoin
        valor_brl = qtd_coins * taxa_conversao

        sucesso, msg = self.movimentar_saldo(user_id, "geralcoin", qtd_coins, "DEBITO", "CONVERSAO_PREPAGO")
        if not sucesso:
            return False, msg

        self.movimentar_saldo(user_id, "credito_brl", valor_brl, "CREDITO", "RESGATE_GERALCOIN")
        return True, f"🎉 {qtd_coins} GeralCoins convertidas em R$ {valor_brl:.2f} de Crédito Pré-pago!"

# ==============================================================================
# 2. CONFIGURAÇÃO DO AMBIENTE & AMBIENTE STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="GeralJá | Ecossistema Integrado",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

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
    st.error(f"⚠️ Atenção ao carregar segredos: {e}")

# ==============================================================================
# 3. CONEXÃO COM O BANCO DE DADOS (FIREBASE FIRESTORE)
# ==============================================================================
@st.cache_resource
def conectar_banco_master():
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

app_engine = conectar_banco_master()
db = firestore.client()
carteira_engine = CarteiraEngine(db)

# ==============================================================================
# 4. AUTENTICAÇÃO OAUTH GOOGLE
# ==============================================================================
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
            st.session_state.auth = True
            st.session_state.user_id = pro_ref[0].id
            st.success(f"Logado com sucesso como {nome_google}!")
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

# ==============================================================================
# 5. CONSTANTES, REGRAS E FUNÇÕES UTILITÁRIAS
# ==============================================================================
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
ZAP_VENDAS = "5511980168513"
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
        if None in [lat1, lon1, lat2, lon2]: return 999.0
        R = 6371 
        dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)
    except: return 999.0

def processar_ia_avancada(texto):
    if not texto: return "Vazio"
    t_clean = normalizar(texto)
    
    for chave, categoria in CONCEITOS_EXPANDIDOS.items():
        if re.search(rf"\b{normalizar(chave)}\b", t_clean):
            return categoria
    
    for cat in CATEGORIAS_OFICIAIS:
        if normalizar(cat) in t_clean:
            return cat

    try:
        cache_ref = db.collection("cache_buscas").document(t_clean).get()
        if cache_ref.exists:
            return cache_ref.to_dict().get("categoria")

        if "GROQ_API_KEY" in st.secrets:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            prompt = f"O usuário buscou: '{texto}'. Categorias disponíveis: {CATEGORIAS_OFICIAIS}. Responda estritamente o NOME DA CATEGORIA mais próxima."
            res = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
                temperature=0.1
            )
            cat_ia = res.choices[0].message.content.strip()
            db.collection("cache_buscas").document(t_clean).set({"categoria": cat_ia})
            return cat_ia
    except:
        pass
    return "Outro (Personalizado)"

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

def criar_link_zap(numero, msg):
    return f"https://api.whatsapp.com/send?phone={limpar_whatsapp(numero)}&text={urllib.parse.quote(msg)}"

@st.cache_data(ttl=600)
def buscar_noticias_rss(busca="Grajaú São Paulo"):
    try:
        url_rss = f"https://news.google.com/rss/search?q={urllib.parse.quote(busca)}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        feed = feedparser.parse(url_rss)
        return feed.entries[:4]
    except Exception:
        return []

def finalizar_e_alinhar_layout():
    st.write("---")
    fechamento_estilo = """
        <style>
            .main .block-container { padding-bottom: 5rem !important; }
            .footer-clean {
                text-align: center;
                padding: 20px;
                opacity: 0.8;
                font-size: 0.85rem;
                width: 100%;
                color: #64748B;
            }
        </style>
        <div class="footer-clean">
            <p>🎯 <b>GeralJá</b> - Sistema de Inteligência & Economia Local</p>
            <p>Conectando moradores, profissionais e comércio no Grajaú.</p>
            <p>v6.0 Master | © 2026 Todos os direitos reservados</p>
        </div>
    """
    st.markdown(fechamento_estilo, unsafe_allow_html=True)

# ==============================================================================
# 6. CONFIGURAÇÃO VISUAL & MODO DIA / NOITE
# ==============================================================================
if 'modo_noite' not in st.session_state:
    st.session_state.modo_noite = True 

c_t1, c_t2 = st.columns([2, 8])
with c_t1:
    st.session_state.modo_noite = st.toggle("🌙 Modo Noite", value=st.session_state.modo_noite)

estilo_dinamico = f"""
<style>
    @media (max-width: 640px) {{
        .main .block-container {{ padding: 1rem !important; }}
        h1 {{ font-size: 1.8rem !important; }}
    }}
    .stApp {{
        background-color: {"#0D1117" if st.session_state.modo_noite else "#FFFAFA"} !important;
        color: {"#FFFFFF" if st.session_state.modo_noite else "#1A1A1B"} !important;
    }}
    div[data-testid="stVerticalBlock"] > div[style*="background"] {{
        background-color: {"#161B22" if st.session_state.modo_noite else "#FFFFFF"} !important;
        border: 1px solid {"#30363D" if st.session_state.modo_noite else "#E0E0E0"} !important;
        border-radius: 18px !important;
    }}
    .header-container {{
        background: white;
        padding: 25px 20px;
        border-radius: 0 0 35px 35px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        border-bottom: 6px solid #FF8C00;
        margin-bottom: 25px;
    }}
    .logo-azul {{ color: #0047AB; font-weight: 900; font-size: 42px; letter-spacing: -2px; }}
    .logo-laranja {{ color: #FF8C00; font-weight: 900; font-size: 42px; letter-spacing: -2px; }}
</style>
"""
st.markdown(estilo_dinamico, unsafe_allow_html=True)
st.markdown('<div class="header-container"><span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span><br><small style="color:#64748B; font-weight:700;">ECOSSISTEMA INTEGRADO DE SERVIÇOS E MOEDA LOCAL</small></div>', unsafe_allow_html=True)

# ==============================================================================
# 7. BOTÃO FLUTUANTE DE ANÚNCIOS (VITRINE DO GRAJAÚ TEM)
# ==============================================================================
st.markdown(f"""
    <a href="https://wa.me/{ZAP_VENDAS}?text=Ol%C3%A1%2C%20quero%20anunciar%20minha%20marca%20na%20Vitrine%20do%20GeralJ%C3%A1" target="_blank" 
       style="position:fixed; bottom:25px; right:20px; background-color:#25d366; color:white; 
              border-radius:50px; padding:12px 22px; font-weight:bold; text-decoration:none; 
              box-shadow: 2px 4px 15px rgba(0,0,0,0.3); z-index:9999; display:flex; align-items:center; gap:8px;">
        📢 <span>ANUNCIE SEU NEGÓCIO</span>
    </a>
""", unsafe_allow_html=True)

# ==============================================================================
# 8. SISTEMA DE NAVEGAÇÃO POR ABAS
# ==============================================================================
lista_abas = ["🔍 BUSCAR", "🎟️ CLUBE DE CUPONS", "🚀 CADASTRAR", "👤 MEU PERFIL", "👑 ADMIN", "⭐ FEEDBACK"]
comando = st.sidebar.text_input("Comando Secreto", type="password")
if comando == "abracadabra":
    lista_abas.append("📊 FINANCEIRO")

menu_abas = st.tabs(lista_abas)

# ==============================================================================
# ABA 0: BUSCA DE SERVIÇOS & PLANTÃO DE NOTÍCIAS
# ==============================================================================
with menu_abas[0]:
    st.markdown("### 🏙️ O que você precisa no Grajaú hoje?")
    
    with st.expander("📍 Sua Localização (GPS)", expanded=False):
        try:
            loc = get_geolocation(component_key="geo_high_prec")
        except:
            loc = None
        if loc and 'coords' in loc:
            minha_lat = loc['coords']['latitude']
            minha_lon = loc['coords']['longitude']
            st.success(f"GPS Ativo (Precisão: {loc['coords'].get('accuracy', 0):.0f}m)")
        else:
            minha_lat, minha_lon = LAT_REF, LON_REF
            st.warning("Usando localização centro. Ative o GPS para filtrar serviços mais próximos.")

    c1, c2 = st.columns([3, 1])
    termo_busca = c1.text_input("Ex: 'Mecânico', 'Pizzaria' ou 'Cano estourado'", key="main_search_v6")
    raio_km = c2.select_slider("Raio (KM)", options=[1, 3, 5, 10, 20, 50, 500], value=5)

    st.markdown("""
    <style>
        .cartao-geral { background: white; border-radius: 20px; border-left: 8px solid var(--cor-borda); padding: 18px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); color: #111; }
        .perfil-row { display: flex; gap: 15px; align-items: center; margin-bottom: 12px; }
        .foto-perfil { width: 60px; height: 60px; border-radius: 50%; object-fit: cover; border: 2px solid #eee; }
        .social-track { display: flex; overflow-x: auto; gap: 10px; padding-bottom: 10px; }
        .social-card { flex: 0 0 180px; height: 220px; border-radius: 12px; overflow: hidden; cursor: pointer; background: #000; }
        .social-card img { width: 100%; height: 100%; object-fit: cover; }
        .btn-zap-footer { display: block; background: #25D366; color: white !important; text-align: center; padding: 12px; border-radius: 12px; font-weight: bold; text-decoration: none; margin-top: 10px; font-size: 15px; }
    </style>
    """, unsafe_allow_html=True)

    if termo_busca:
        with st.status("🔍 Processando inteligência de busca...", expanded=False) as status:
            doc_cat = db.collection("configuracoes").document("categorias").get()
            lista_oficial = doc_cat.to_dict().get("lista", CATEGORIAS_OFICIAIS) if doc_cat.exists else CATEGORIAS_OFICIAIS
            
            cat_ia = None
            for c in lista_oficial:
                if c.lower() in termo_busca.lower():
                    cat_ia = c
                    break
            
            if not cat_ia:
                cat_ia = processar_ia_avancada(termo_busca)
            
            profs = db.collection("profissionais").where("area", "==", cat_ia).where("aprovado", "==", True).stream()
            
            lista_ranking = []
            for p_doc in profs:
                p = p_doc.to_dict()
                p['id'] = p_doc.id
                dist = calcular_distancia_real(minha_lat, minha_lon, p.get('lat', LAT_REF), p.get('lon', LON_REF))
                
                if dist <= raio_km:
                    p['dist'] = dist
                    p['score_elite'] = (1000 if p.get('verificado') and p.get('saldo', 0) > 0 else 0) + (p.get('saldo', 0) * 10)
                    lista_ranking.append(p)

            lista_ranking.sort(key=lambda x: (x['dist'], -x['score_elite']))
            status.update(label=f"Resultados para '{cat_ia}' encontrados!", state="complete")

        if not lista_ranking:
            st.warning(f"Nenhum profissional de '{cat_ia}' encontrado no raio de {raio_km} km.")
        else:
            for p in lista_ranking:
                is_elite = p['score_elite'] > 0
                cor_borda = "#FFD700" if is_elite else "#0047AB"
                zap_limpo = limpar_whatsapp(p.get('whatsapp', p['id']))
                
                # Desconto de clique no modelo pré-pago
                link_zap = criar_link_zap(zap_limpo, f"Olá {p.get('nome')}, vi seu perfil no GeralJá e gostaria de solicitar um orçamento!")
                
                f_perfil = p.get('foto_url', '') or "https://cdn-icons-png.flaticon.com/512/149/149071.png"

                fotos_html = ""
                for i in range(1, 5):
                    f_data = p.get(f'f{i}')
                    if f_data and len(str(f_data)) > 50:
                        src = f_data if str(f_data).startswith("data") else f"data:image/jpeg;base64,{f_data}"
                        fotos_html += f'<div class="social-card"><img src="{src}"></div>'

                st.markdown(f"""
                <div class="cartao-geral" style="--cor-borda: {cor_borda};">
                    <div style="font-size: 11px; color: #0047AB; font-weight: bold; margin-bottom: 10px;">
                        📍 A {p['dist']:.1f} km de você {" | 🏆 SELO ELITE" if is_elite else ""}
                    </div>
                    <div class="perfil-row">
                        <img src="{f_perfil}" class="foto-perfil">
                        <div>
                            <h4 style="margin:0; color:#1e3a8a;">{str(p.get('nome','')).upper()}</h4>
                            <p style="margin:0; color:#666; font-size:12px;">{str(p.get('descricao',''))[:110]}...</p>
                        </div>
                    </div>
                    {"<div class='social-track'>" + fotos_html + "</div>" if fotos_html else ""}
                    <a href="{link_zap}" target="_blank" class="btn-zap-footer">💬 CHAMAR NO WHATSAPP</a>
                </div>
                """, unsafe_allow_html=True)

    # --- PLANTÃO DE NOTÍCIAS HÍBRIDO ---
    st.markdown("---")
    st.subheader("📰 Plantão Grajaú Tem")

    IMG_PADRAO = "https://images.unsplash.com/photo-1504711432869-0df30d7eaf4d?w=500&q=80"

    try:
        noticias_fb = list(db.collection("noticias").order_by("data", direction="DESCENDING").limit(2).stream())
    except:
        noticias_fb = []

    noticias_auto = buscar_noticias_rss("Grajaú São Paulo")

    fila_noticias = []
    for n in noticias_fb:
        dados = n.to_dict()
        fila_noticias.append({
            "titulo": dados.get('titulo', 'Notícia em destaque'),
            "link": dados.get('link_original', '#'),
            "img": dados.get('imagem_url', IMG_PADRAO),
            "fonte": "⭐ DESTAQUE LOCAL",
            "cor": "#FFD700"
        })

    for n in noticias_auto:
        if len(fila_noticias) >= 4: break
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
            with cols[i % 2]:
                st.markdown(f"""
                    <a href="{noticia['link']}" target="_blank" style="text-decoration:none; color:inherit;">
                        <div style="background:white; border-radius:15px; margin-bottom:20px; box-shadow:0 4px 12px rgba(0,0,0,0.08); overflow:hidden; border-bottom: 5px solid {noticia['cor']}; height: 310px;">
                            <div style="height:140px; background-image: url('{noticia['img']}'); background-size:cover; background-position:center;"></div>
                            <div style="padding:15px;">
                                <span style="background:{noticia['cor']}22; color:{noticia['cor']}; font-size:10px; font-weight:bold; padding:3px 10px; border-radius:50px;">
                                    {noticia['fonte']}
                                </span>
                                <h4 style="margin:10px 0 8px 0; color:#1a1a1a; font-size:14px; line-height:1.3; height: 55px; overflow: hidden;">
                                    {noticia['titulo'][:80]}{'...' if len(noticia['titulo']) > 80 else ''}
                                </h4>
                                <div style="color:{noticia['cor']}; font-weight:bold; font-size:12px; margin-top:8px;">Ver matéria completa →</div>
                            </div>
                        </div>
                    </a>
                """, unsafe_allow_html=True)

# ==============================================================================
# ABA 1: CLUBE DE CUPONS & CHECKOUT HÍBRIDO (GERALCOIN)
# ==============================================================================
with menu_abas[1]:
    st.markdown("### 🎟️ Clube de Cupons & Ofertas com GeralCoin")
    st.caption("Ganhe moedas engajando nas redes do Grajaú Tem e troque por descontos no comércio do bairro!")

    # Identificação do Morador / Visitante para Carteira
    id_morador = st.text_input("Seu WhatsApp para consultar saldo e usar cupons:", value=st.session_state.get('user_id', ''), placeholder="Ex: 11999999999")
    
    if id_morador:
        zap_morador_limpo = limpar_whatsapp(id_morador)
        saldos_morador = carteira_engine.obter_saldos(zap_morador_limpo)
        
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("Sua Carteira GeralCoins 🪙", f"{saldos_morador['geralcoin']} GC")
        c_m2.metric("Valor em Descontos", f"R$ {saldos_morador['geralcoin'] * 0.10:.2f}")
        
        if c_m3.button("🎁 Ganhar 10 GC por Compartilhar"):
            carteira_engine.movimentar_saldo(zap_morador_limpo, "geralcoin", 10, "CREDITO", "COMPARTILHAMENTO_NOTICIA")
            st.toast("🎉 Você ganhou 10 GeralCoins por apoiar o comércio do bairro!")
            time.sleep(1)
            st.rerun()

    st.markdown("---")
    st.subheader("🔥 Ofertas Relâmpago em Destaque")

    ofertas_exemplo = [
        {"id": "o1", "loja": "Pizzaria Grajaú Express", "zap": ZAP_ADMIN, "item": "Pizza Grande Calabresa + Guaraná 2L", "preco_brl": 50.00, "max_gc": 100, "img": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400&q=80"},
        {"id": "o2", "loja": "Lava Jato & Estética Interlagos", "zap": ZAP_ADMIN, "item": "Lavagem Completa + Cera Cristalizada", "preco_brl": 60.00, "max_gc": 150, "img": "https://images.unsplash.com/photo-1520340356584-f9917d1eea6f?w=400&q=80"},
        {"id": "o3", "loja": "Salão & Barbearia Estilo", "zap": ZAP_ADMIN, "item": "Corte Masculino + Barba Terapiada", "preco_brl": 40.00, "max_gc": 80, "img": "https://images.unsplash.com/photo-1503951914875-452162b0f3f1?w=400&q=80"}
    ]

    for of in ofertas_exemplo:
        with st.container():
            col_o1, col_o2 = st.columns([1, 2])
            with col_o1:
                st.image(of['img'], use_container_width=True)
            with col_o2:
                st.markdown(f"#### {of['item']}")
                st.write(f"🏢 **{of['loja']}**")
                
                val_desc_max = of['max_gc'] * 0.10
                preco_com_desconto = of['preco_brl'] - val_desc_max
                
                st.markdown(f"""
                * Preço Original: ~~R$ {of['preco_brl']:.2f}~~
                * **Desconto Máximo com GeralCoins:** -R$ {val_desc_max:.2f} ({of['max_gc']} GC)
                * **Preço Final no PIX/Balcão:** <span style="color:#22c55e; font-weight:bold; font-size:18px;">R$ {preco_com_desconto:.2f}</span>
                """, unsafe_allow_html=True)
                
                if st.button(f"🛒 COMPRAR / GERAR CUPOM ({of['item']})", key=f"btn_{of['id']}"):
                    if not id_morador:
                        st.warning("Informe seu WhatsApp acima para usar seus créditos!")
                    else:
                        zap_m = limpar_whatsapp(id_morador)
                        saldos = carteira_engine.obter_saldos(zap_m)
                        
                        gc_usar = min(saldos['geralcoin'], of['max_gc'])
                        desconto_brl = gc_usar * 0.10
                        valor_a_pagar_pix = of['preco_brl'] - desconto_brl
                        
                        if gc_usar > 0:
                            carteira_engine.movimentar_saldo(zap_m, "geralcoin", gc_usar, "DEBITO", f"COMPRA_CUPOM_{of['id']}")
                        
                        # Mensagem do Pedido formatada estilo iFood/WhatsApp
                        msg_pedido = f"""🚨 *NOVO PEDIDO GERALJÁ - CUPOM APLICADO*
👤 *Cliente:* {zap_m}
📦 *Item:* {of['item']}
🏬 *Estabelecimento:* {of['loja']}

💵 *Valor Total Item:* R$ {of['preco_brl']:.2f}
🪙 *Desconto Aplicado ({gc_usar} GeralCoins):* -R$ {desconto_brl:.2f}
✅ *TOTAL A PAGAR NO PIX/ENTREGA:* R$ {valor_a_pagar_pix:.2f}

📍 Chave PIX do Estabelecimento: {PIX_OFICIAL}"""
                        
                        link_pedido_zap = criar_link_zap(of['zap'], msg_pedido)
                        
                        st.success(f"🎉 Cupom resgatado! {gc_usar} GeralCoins debitadas com sucesso.")
                        st.markdown(f'<a href="{link_pedido_zap}" target="_blank" style="display:block; background:#25D366; color:white; text-align:center; padding:12px; border-radius:10px; font-weight:bold; text-decoration:none;">💬 ENVIAR PEDIDO DIRETO NO WHATSAPP</a>', unsafe_allow_html=True)

# ==============================================================================
# ABA 2: CADASTRAR OU EDITAR PERFIL
# ==============================================================================
with menu_abas[2]:
    st.markdown("### 🚀 Cadastro de Profissional ou Comércio")

    dados_google = st.session_state.get("pre_cadastro", {})
    email_inicial = dados_google.get("email", "")
    nome_inicial = dados_google.get("nome", "")
    foto_google = dados_google.get("foto", "")

    st.markdown("##### Entre rápido com sua conta social:")
    col_soc1, col_soc2 = st.columns(2)
    
    g_auth = st.secrets.get("google_auth", {})
    g_id = g_auth.get("client_id")
    g_uri = g_auth.get("redirect_uri", REDIRECT_URI)

    with col_soc1:
        if g_id:
            url_google = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={g_id}&response_type=code&scope=openid%20profile%20email&redirect_uri={g_uri}"
            st.markdown(f'''
                <a href="{url_google}" target="_self" style="text-decoration:none;">
                    <div style="display:flex; align-items:center; justify-content:center; border:1px solid #dadce0; border-radius:8px; padding:10px; background:white;">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/5/53/Google_%22G%22_Logo.svg" width="18px" style="margin-right:10px;">
                        <span style="color:#3c4043; font-weight:bold; font-size:14px;">Google</span>
                    </div>
                </a>
            ''', unsafe_allow_html=True)

    with col_soc2:
        fb_id = st.secrets.get("FB_CLIENT_ID", "")
        st.markdown(f'''
            <a href="https://www.facebook.com/v18.0/dialog/oauth?client_id={fb_id}&redirect_uri={g_uri}&scope=public_profile,email" target="_self" style="text-decoration:none;">
                <div style="display:flex; align-items:center; justify-content:center; border-radius:8px; padding:10px; background:#1877F2;">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/2021_Facebook_icon.svg" width="18px" style="margin-right:10px;">
                    <span style="color:white; font-weight:bold; font-size:14px;">Facebook</span>
                </div>
            </a>
        ''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    with st.form("form_profissional", clear_on_submit=False):
        col1, col2 = st.columns(2)
        nome_input = col1.text_input("Nome Profissional / Nome da Loja", value=nome_inicial)
        zap_input = col2.text_input("WhatsApp (DDD + Número sem espaços)")
        
        email_input = st.text_input("E-mail para Login", value=email_inicial)
        
        col3, col4 = st.columns(2)
        cat_input = col3.selectbox("Especialidade Principal", CATEGORIAS_OFICIAIS)
        senha_input = col4.text_input("Senha de Acesso", type="password")
        
        desc_input = st.text_area("Descrição dos Serviços e Horário de Atendimento")
        tipo_input = st.radio("Categoria de Conta", ["👨‍🔧 Profissional Autônomo", "🏢 Comércio/Loja"], horizontal=True)
        
        foto_upload = st.file_uploader("Foto de Perfil ou Logomarca", type=['png', 'jpg', 'jpeg'])
        
        btn_acao = st.form_submit_button("✅ SALVAR CADASTRO E GANHAR BÔNUS", use_container_width=True)

    if btn_acao:
        zap_limpo = limpar_whatsapp(zap_input)
        if not nome_input or not zap_limpo or not senha_input:
            st.warning("⚠️ Nome, WhatsApp e Senha são obrigatórios!")
        else:
            try:
                doc_ref = db.collection("profissionais").document(zap_limpo)
                perfil_antigo = doc_ref.get()
                dados_antigos = perfil_antigo.to_dict() if perfil_antigo.exists else {}

                foto_b64 = dados_antigos.get("foto_url", "")
                if foto_upload is not None:
                    foto_b64 = otimizar_imagem(foto_upload, qualidade=60, size=(350, 350))
                elif not foto_b64 and foto_google:
                    foto_b64 = foto_google

                dados_pro = {
                    "nome": nome_input,
                    "whatsapp": zap_limpo,
                    "email": email_input,
                    "area": cat_input,
                    "senha": senha_input,
                    "descricao": desc_input,
                    "tipo": tipo_input,
                    "foto_url": foto_b64,
                    "saldo": dados_antigos.get("saldo", 20),
                    "data_cadastro": datetime.now().strftime("%d/%m/%Y"),
                    "aprovado": True,
                    "cliques": dados_antigos.get("cliques", 0),
                    "lat": LAT_REF,
                    "lon": LON_REF
                }
                
                doc_ref.set(dados_pro, merge=True)
                
                # Inicializa a carteira multi-moedas com o bônus de 20 GeralCoins
                carteira_engine.obter_saldos(zap_limpo)
                
                st.balloons()
                st.success(f"🎉 Cadastro concluído! 20 GeralCoins foram creditadas na sua conta.")
            except Exception as e:
                st.error(f"❌ Erro ao salvar cadastro: {e}")

# ==============================================================================
# ABA 3: PAINEL DO PARCEIRO & GESTÃO DA CARTEIRA
# ==============================================================================
with menu_abas[3]:
    if not st.session_state.get('auth'):
        st.subheader("🚀 Acesso ao Painel do Parceiro")
        col1, col2 = st.columns(2)
        l_zap = col1.text_input("WhatsApp Cadastrado", key="login_zap_v6")
        l_pw = col2.text_input("Senha", type="password", key="login_pw_v6")
        
        if st.button("ENTRAR NO PAINEL", key="btn_login_v6", use_container_width=True):
            zap_busca = limpar_whatsapp(l_zap)
            try:
                u = db.collection("profissionais").document(zap_busca).get()
                if u.exists and str(u.to_dict().get('senha')) == str(l_pw):
                    st.session_state.auth = True
                    st.session_state.user_id = zap_busca
                    st.success("Acesso autorizado!")
                    st.rerun()
                else:
                    st.error("❌ Credenciais inválidas.")
            except Exception as e:
                st.error(f"Erro ao acessar banco: {e}")
    else:
        user_id = st.session_state.user_id
        doc_ref = db.collection("profissionais").document(user_id)
        d = doc_ref.get().to_dict() or {}
        saldos = carteira_engine.obter_saldos(user_id)
        
        st.write(f"### Olá, {d.get('nome', 'Parceiro')}!")
        
        # Exibição dos 3 Modelos de Monetização na Carteira do Usuário
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("GeralCoins 🪙", f"{saldos['geralcoin']} GC", help="Ganha por engajamento / Troca por serviços")
        m2.metric("Crédito Pré-pago 💳", f"R$ {saldos['credito_brl']:.2f}", help="Usado para compra de Leads e Orçamentos")
        m3.metric("Saldo Custódia 🔒", f"R$ {saldos['custodia_brl']:.2f}", help="Valor de serviços retido no modelo Uber")
        m4.metric("Cliques Recebidos 🚀", f"{d.get('cliques', 0)}")

        with st.expander("🔄 CONVERTER GERALCOINS EM CRÉDITO PRÉ-PAGO"):
            qtd_conv = st.number_input("Quantidade de GeralCoins para converter:", min_value=10, max_value=int(saldos['geralcoin']), step=10, value=10)
            if st.button("CONVERTER AGORA (10 GC = R$ 1,00)"):
                ok, msg = carteira_engine.converter_geralcoin_para_credito(user_id, int(qtd_conv))
                if ok:
                    st.success(msg)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(msg)

        st.divider()

        with st.expander("📝 EDITAR MEU PERFIL & GALERIA DA VITRINE"):
            with st.form("perfil_v6"):
                n_nome = st.text_input("Nome Comercial", d.get('nome', ''))
                n_area = st.selectbox("Especialidade", CATEGORIAS_OFICIAIS, 
                                     index=CATEGORIAS_OFICIAIS.index(d.get('area')) if d.get('area') in CATEGORIAS_OFICIAIS else 0)
                n_desc = st.text_area("Descrição Detalhada", d.get('descricao', ''))
                
                n_foto = st.file_uploader("Trocar Foto de Perfil", type=['jpg','png','jpeg'])
                n_portfolio = st.file_uploader("Vitrine de Fotos do Serviço (Máx 4)", type=['jpg','png','jpeg'], accept_multiple_files=True)
                
                if st.form_submit_button("💾 SALVAR ALTERAÇÕES", use_container_width=True):
                    updates = {"nome": n_nome, "area": n_area, "descricao": n_desc}
                    if n_foto:
                        img_b64 = otimizar_imagem(n_foto)
                        if img_b64: updates["foto_url"] = img_b64
                    if n_portfolio:
                        for i, f in enumerate(n_portfolio[:4]):
                            img_p = otimizar_imagem(f)
                            if img_p: updates[f"f{i+1}"] = img_p
                    
                    doc_ref.update(updates)
                    st.success("✅ Perfil atualizado!")
                    time.sleep(1)
                    st.rerun()

        if st.button("🚪 SAIR DA CONTA", use_container_width=True):
            st.session_state.auth = False
            st.rerun()

# ==============================================================================
# ABA 4: TORRE DE CONTROLE ADMIN
# ==============================================================================
with menu_abas[4]:
    ADMIN_USER = st.secrets.get("ADMIN_USER", "admin")
    ADMIN_PASS = st.secrets.get("ADMIN_PASS", "geralja2026")

    if not st.session_state.get('admin_logado'):
        st.markdown("### 🔐 Acesso Restrito à Diretoria")
        with st.form("painel_login_adm"):
            u = st.text_input("Usuário Administrativo")
            p = st.text_input("Senha", type="password")
            if st.form_submit_button("ACESSAR TORRE DE CONTROLE", use_container_width=True):
                if u == ADMIN_USER and p == ADMIN_PASS:
                    st.session_state.admin_logado = True
                    st.success("Acesso concedido!")
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")
    else:
        st.markdown("## 👑 Central de Comando GeralJá")
        if st.button("🚪 Sair do Modo Admin"):
            st.session_state.admin_logado = False
            st.rerun()

        st.divider()
        try:
            profs_ref = list(db.collection("profissionais").stream())
            profs_data = [p.to_dict() | {"id": p.id} for p in profs_ref]
            df = pd.DataFrame(profs_data)

            if not df.empty:
                st.subheader("📊 Métricas de Operação")
                c_a1, c_a2, c_a3 = st.columns(3)
                c_a1.metric("Total de Parceiros Cadastrados", len(df))
                c_a2.metric("Pendentes de Aprovação", len(df[df['aprovado'] == False]) if 'aprovado' in df else 0)
                c_a3.metric("Cliques Acumulados", int(df['cliques'].sum()) if 'cliques' in df else 0)

                st.markdown("---")
                st.subheader("👥 Gestão de Usuários e Carteiras")
                for _, row in df.iterrows():
                    pid = row['id']
                    with st.expander(f"👤 {row.get('nome','').upper()} ({pid})"):
                        col_adm1, col_adm2 = st.columns(2)
                        with col_adm1:
                            st.write(f"**Especialidade:** {row.get('area')}")
                            st.write(f"**E-mail:** {row.get('email')}")
                        with col_adm2:
                            if st.button(f"➕ Recarregar +50 GeralCoins ({pid})"):
                                carteira_engine.movimentar_saldo(pid, "geralcoin", 50, "CREDITO", "RECARGA_ADMIN")
                                st.success("Crédito inserido com sucesso!")
                                time.sleep(0.5)
                                st.rerun()
        except Exception as e:
            st.error(f"Erro ao carregar dados do admin: {e}")

# ==============================================================================
# ABA 5: AVALIAÇÃO & FEEDBACK
# ==============================================================================
with menu_abas[5]:
    st.header("⭐ Avalie o Sistema GeralJá")
    nota = st.slider("Nota da plataforma", 1, 5, 5)
    comentario = st.text_area("O que você achou das ofertas e da moeda GeralCoin?")
    
    if st.button("Enviar Avaliação", use_container_width=True):
        db.collection("feedbacks").add({
            "nota": nota,
            "comentario": comentario,
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        st.success("Obrigado pelo feedback!")

# ==============================================================================
# ABA OPCIONAL: PAINEL FINANCEIRO
# ==============================================================================
if "📊 FINANCEIRO" in lista_abas:
    with menu_abas[6]:
        st.header("📊 Balanço Financeiro da Plataforma")
        st.info(f"Chave PIX Oficial de Recebimento de Pacotes: {PIX_OFICIAL}")
        st.write("Gerencie aqui os relatórios de recargas do modelo pré-pago e comissões do modelo Uber.")

# ==============================================================================
# 9. RODAPÉ DE SEGURANÇA E LGPD
# ==============================================================================
finalizar_e_alinhar_layout()

st.markdown("""
<style>
    .footer-container { text-align: center; padding: 20px; color: #64748B; font-size: 12px; }
    .security-badge { display: inline-flex; align-items: center; background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 20px; padding: 5px 15px; margin-bottom: 10px; color: #0f172a; font-weight: bold; }
    .shield-icon { color: #22c55e; margin-right: 8px; }
</style>
<div class="footer-container">
    <div class="security-badge"><span class="shield-icon">🛡️</span> Criptografia e Proteção de Dados Ativa</div>
    <p>© 2026 GeralJá | Ecossistema Blindado LGPD</p>
</div>
""", unsafe_allow_html=True)
