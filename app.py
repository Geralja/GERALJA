# ==============================================================================
# GERALJÁ: CRIANDO SOLUÇÕES - MÓDULO 1: INFRAESTRUTURA
# ==============================================================================

# --- 1. IMPORTS UNIFICADOS ---
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
import sys
import feedparser
import urllib.parse
from PIL import Image
import io
from groq import Groq
from fuzzywuzzy import process
from urllib.parse import quote
import google.generativeai as genai
from google_auth_oauthlib.flow import Flow
import importlib
import os
# Tenta importar JS
try:
    from streamlit_js_eval import streamlit_js_eval, get_geolocation
except ImportError:
    streamlit_js_eval = None
    get_geolocation = None

# --- 2. CLASSE ENGINE E CONFIGURAÇÃO ---
class GeralJaEngine:
    def __init__(self):
        self.fuso = pytz.timezone('America/Sao_Paulo')
    
    def sanitizar(self, codigo_bruto):
        if not codigo_bruto: return ""
        limpo = codigo_bruto.replace('\u00a0', ' ').replace('\xa0', ' ')
        return re.sub(r'[^\x20-\x7E\n\t\r]', '', limpo)

    def injetar_modulo(self, nome_arquivo, conteudo):
        conteudo_limpo = self.sanitizar(conteudo)
        try:
            with open(f"{nome_arquivo}.py", "w", encoding="utf-8") as f:
                f.write(conteudo_limpo)
            return True, f"✅ Módulo {nome_arquivo} instalado e saneado!"
        except Exception as e:
            return False, f"❌ Falha na instalação: {str(e)}"
            # --- DEFINIÇÃO DE VARIÁVEIS GLOBAIS ---
REDIRECT_URI = "https://geralja-zxiaj2ot56fuzgcz7xhcks.streamlit.app/"
FB_ID = st.secrets.get("FB_CLIENT_ID", "")

# Inicializa o Motor Global
engine = GeralJaEngine()
fuso_br = engine.fuso

# --- 3. CONSTANTES E CATEGORIAS ---
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ADMIN = "mumias"
LAT_REF = -23.5505
LON_REF = -46.6333
ZAP_VENDAS = "5511980168513"
IMG_PADRAO = "https://images.unsplash.com/photo-1504711432869-0df30d7eaf4d?w=500&q=80"
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
# --- 4. FUNÇÕES DE SUPORTE E FIREBASE ---

# Conexão com o Banco de Dados
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

db = firestore.client()
conectar_banco_master()

# Função auxiliar para buscas
def buscar_opcoes_dinamicas(documento, padrao):
    try:
        doc = db.collection("configuracoes").document(documento).get()
        if doc.exists:
            dados = doc.to_dict()
            return dados.get("lista", padrao)
        return padrao
    except:
        return padrao

# --- 5. LÓGICA DE LOGIN GOOGLE ---
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

def handle_google_login():
    query_params = st.query_params
    if "code" in query_params:
        try:
            flow = get_google_flow()
            flow.fetch_token(code=query_params["code"])
            session = flow.authorized_session()
            user_info = session.get('https://www.googleapis.com/userinfo').json()
            email_google = user_info.get("email")
            st.query_params.clear()
            
            pro_ref = db.collection("profissionais").where("email", "==", email_google).limit(1).get()
            if pro_ref:
                st.session_state.auth = True
                st.session_state.user_id = pro_ref[0].id
                st.success(f"Logado com sucesso!")
                time.sleep(1)
                st.rerun()
            else:
                st.session_state.pre_cadastro = {
                    "email": email_google,
                    "nome": user_info.get("name"),
                    "foto": user_info.get("picture")
                }
        except Exception as e:
            st.error(f"Erro ao processar login do Google: {e}")

handle_google_login()

# --- 6. ESTILOS E THEME ---
if 'modo_noite' not in st.session_state: st.session_state.modo_noite = True 

c_t1, c_t2 = st.columns([2, 8])
with c_t1:
    st.session_state.modo_noite = st.toggle("🌙 Modo Noite", value=st.session_state.modo_noite)

estilo_dinamico = f"""
<style>
    .stApp {{ 
        background-color: {"#0D1117" if st.session_state.modo_noite else "#FFFAFA"} !important; 
        color: {"#FFFFFF" if st.session_state.modo_noite else "#1A1A1B"} !important; 
    }}
    div[data-testid="stVerticalBlock"] > div[style*="background"] {{ 
        background-color: {"#161B22" if st.session_state.modo_noite else "#FFFFFF"} !important; 
        border: 1px solid {"#30363D" if st.session_state.modo_noite else "#E0E0E0"} !important; 
        border-radius: 18px !important; 
    }}
</style>
"""
st.markdown(estilo_dinamico, unsafe_allow_html=True)
# --- 7. MOTORES DE IA E UTILS ---
def processar_ia_avancada(texto):
    if not texto: return "Vazio"
    t_clean = normalizar_para_ia(texto)
    # 1. Busca rápida em conceitos definidos
    for chave, categoria in CONCEITOS_EXPANDIDOS.items():
        if re.search(rf"\b{normalizar_para_ia(chave)}\b", t_clean):
            return categoria
    for cat in CATEGORIAS_OFICIAIS:
        if normalizar_para_ia(cat) in t_clean:
            return cat

    # 2. IA Groq (Nota 5.0)
    try:
        cache_ref = db.collection("cache_buscas").document(t_clean).get()
        if cache_ref.exists:
            return cache_ref.to_dict().get("categoria")

        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        prompt = f"O usuário buscou: '{texto}'. Categorias: {CATEGORIAS_OFICIAIS}. Responda apenas o NOME DA CATEGORIA."
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
            temperature=0.1
        )
        cat_ia = res.choices[0].message.content.strip()
        db.collection("cache_buscas").document(t_clean).set({"categoria": cat_ia})
        return cat_ia
    except:
        return "NAO_ENCONTRADO"

def finalizar_e_alinhar_layout():
    st.write("---")
    fechamento_estilo = """
        <style>
            .main .block-container { padding-bottom: 5rem !important; }
            .footer-clean { text-align: center; padding: 20px; opacity: 0.7; font-size: 0.8rem; width: 100%; color: gray; }
        </style>
        <div class="footer-clean">
            <p>🎯 <b>GeralJá</b> - Sistema de Inteligência Local</p>
            <p>Conectando quem precisa com quem sabe fazer.</p>
            <p>v3.0 | © 2026 Todos os direitos reservados</p>
        </div>
    """
    st.markdown(fechamento_estilo, unsafe_allow_html=True)

# --- 8. DESIGN SYSTEM ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .header-container { background: white; padding: 40px 20px; border-radius: 0 0 50px 50px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.05); border-bottom: 8px solid #FF8C00; margin-bottom: 25px; }
    .logo-azul { color: #0047AB; font-weight: 900; font-size: 50px; letter-spacing: -2px; }
    .logo-laranja { color: #FF8C00; font-weight: 900; font-size: 50px; letter-spacing: -2px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-container"><span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span><br><small style="color:#64748B; font-weight:700;">BRASIL ELITE EDITION</small></div>', unsafe_allow_html=True)

# --- 9. DEFINIÇÃO DAS ABAS ---
lista_abas = ["🔍 BUSCAR", "🚀 CADASTRAR", "👤 MEU PERFIL", "👑 ADMIN", "⭐ FEEDBACK"]
comando = st.sidebar.text_input("Comando Secreto", type="password")
if comando == "abracadabra":
    lista_abas.append("📊 FINANCEIRO")

menu_abas = st.tabs(lista_abas)

# --- ABA 0: PORTAL GRAJAÚ TEM ---
with menu_abas[0]:
    st.markdown("### 🏙️ O que você precisa no Grajaú?")
    
    with st.expander("📍 Sua Localização (GPS)", expanded=False):
        loc = get_geolocation(component_key="geo_high_prec") if get_geolocation else None
        if loc and 'coords' in loc:
            minha_lat, minha_lon = loc['coords']['latitude'], loc['coords']['longitude']
            st.success(f"GPS Ativo (Precisão: {loc['coords'].get('accuracy', 0):.0f}m)")
        else:
            minha_lat, minha_lon = LAT_REF, LON_REF
            st.warning("Usando localização padrão (Centro).")

    c1, c2 = st.columns([3, 1])
    termo_busca = c1.text_input("Ex: 'Cano estourado' ou 'Pizzaria'", key="main_search_v4")
    raio_km = c2.select_slider("Raio (KM)", options=[1, 3, 5, 10, 20, 50, 500], value=5)

    if termo_busca:
        with st.status("🔍 Buscando...", expanded=False) as status:
            doc_cat = db.collection("configuracoes").document("categorias").get()
            lista_oficial = doc_cat.to_dict().get("lista", []) if doc_cat.exists else []
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
                dist = # --- FUNÇÃO DE CÁLCULO DE DISTÂNCIA (GEOLOCALIZAÇÃO) ---
def calcular_distancia_real(lat1, lon1, lat2, lon2):
    """
    Calcula a distância em KM entre dois pontos usando a fórmula de Haversine.
    """
    # Raio da Terra em km
    R = 6371
    try:
        dlat = math.radians(float(lat2) - float(lat1))
        dlon = math.radians(float(lon2) - float(lon1))
        a = math.sin(dlat/2)**2 + math.cos(math.radians(float(lat1))) * math.cos(math.radians(float(lat2))) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    except:
        return 9999 # Se falhar, retorna uma distância muito grande

            lista_ranking.sort(key=lambda x: (x['dist'], -x['score_elite']))
            status.update(label=f"Resultados para {cat_ia} encontrados!", state="complete")
            # 3. RENDERIZAÇÃO DOS CARDS (Continuação)
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
                
                is_elite = p.get('score_elite', 0) > 0
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

# --- SEÇÃO DE NOTÍCIAS HÍBRIDA ---
st.markdown("---")
st.subheader("📰 Plantão Grajaú Tem")

# 1. BUSCAR NOTÍCIAS MANUAIS
try:
    noticias_fb = list(db.collection("noticias").order_by("data", direction="DESCENDING").limit(2).stream())
except:
    noticias_fb = []

# 2. BUSCAR NOTÍCIAS AUTOMÁTICAS
def buscar_noticias_rss(busca="Grajaú São Paulo"):
    try:
        url_rss = f"https://news.google.com/rss/search?q={urllib.parse.quote(busca)}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        feed = feedparser.parse(url_rss)
        return feed.entries[:4]
    except:
        return []

noticias_auto = buscar_noticias_rss()

# 3. ORGANIZAÇÃO DA FILA DE EXIBIÇÃO
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
                            <span style="background:{noticia['cor']}22; color:{noticia['cor']}; font-size:10px; font-weight:bold; padding:3px 10px; border-radius:50px;">{noticia['fonte']}</span>
                            <h4 style="margin:12px 0 8px 0; color:#1a1a1a; font-size:15px; line-height:1.3; height: 60px; overflow: hidden;">{noticia['titulo'][:85]}{'...' if len(noticia['titulo']) > 85 else ''}</h4>
                            <div style="color:{noticia['cor']}; font-weight:bold; font-size:12px; margin-top:10px;">Ler matéria completa →</div>
                        </div>
                    </div>
                </a>
            """, unsafe_allow_html=True)

# --- ABA 2: 🚀 PAINEL DO PARCEIRO (COMPLETO) ---
with menu_abas[2]:
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

    if 'auth' not in st.session_state: st.session_state.auth = False
    
    if not st.session_state.get('auth'):
        st.subheader("🚀 Acesso ao Painel")
        fb_id = st.secrets.get("FB_CLIENT_ID", "")
        url_direta_fb = f"https://www.facebook.com/v18.0/dialog/oauth?client_id={fb_id}&redirect_uri={REDIRECT_URI}&scope=public_profile,email"
        
        st.markdown(f'''
            <a href="{url_direta_fb}" target="_top" style="text-decoration:none;">
                <div style="background:#1877F2;color:white;padding:12px;border-radius:8px;text-align:center;font-weight:bold;display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow: 0px 4px 6px rgba(0,0,0,0.1);">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/2021_Facebook_icon.svg" width="20px" style="margin-right:10px;">
                    ENTRAR COM FACEBOOK
                </div>
            </a>
        ''', unsafe_allow_html=True)
                # --- 2. PAINEL LOGADO (Continuação da Aba 2) ---
        st.write("--- ou use seus dados ---")
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
                    else: st.error("❌ Senha incorreta.")
                else: st.error("❌ WhatsApp não cadastrado.")
            except Exception as e: st.error(f"Erro ao acessar banco de dados: {e}")
            
    else: # Usuário Logado
        doc_ref = db.collection("profissionais").document(st.session_state.user_id)
        d = doc_ref.get().to_dict()
        
        st.write(f"### Olá, {d.get('nome', 'Parceiro')}!")
        m1, m2, m3 = st.columns(3)
        m1.metric("Saldo 🪙", f"{d.get('saldo', 0)}")
        m2.metric("Cliques 🚀", f"{d.get('cliques', 0)}")
        m3.metric("Status", "🟢 ATIVO" if d.get('aprovado') else "🟡 PENDENTE")

        if st.button("📍 ATUALIZAR MEU GPS", use_container_width=True):
            loc = streamlit_js_eval(js_expressions="navigator.geolocation.getCurrentPosition(s => s)", key='gps_v8') if streamlit_js_eval else None
            if loc and 'coords' in loc:
                doc_ref.update({"lat": loc['coords']['latitude'], "lon": loc['coords']['longitude']})
                st.success("✅ Localização GPS Atualizada!")

        with st.expander("📝 EDITAR MEU PERFIL & VITRINE", expanded=False):
            def otimizar_imagem_perfil(arq, qualidade=50, size=(800, 800)):
                try:
                    img = Image.open(arq)
                    if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                    img.thumbnail(size)
                    output = io.BytesIO()
                    img.save(output, format="JPEG", quality=qualidade, optimize=True)
                    return f"data:image/jpeg;base64,{base64.b64encode(output.getvalue()).decode()}"
                except: return None

            with st.form("perfil_v8"):
                n_nome = st.text_input("Nome Comercial", d.get('nome', ''))
                n_area = st.selectbox("Segmento", CATEGORIAS_OFICIAIS, index=CATEGORIAS_OFICIAIS.index(d.get('area')) if d.get('area') in CATEGORIAS_OFICIAIS else 0)
                n_desc = st.text_area("Descrição do Serviço", d.get('descricao', ''))
                st.write("📷 **Fotos**")
                n_foto = st.file_uploader("Trocar Foto de Perfil", type=['jpg','png','jpeg'])
                n_portfolio = st.file_uploader("Vitrine de Serviços (Máx 4 fotos)", type=['jpg','png','jpeg'], accept_multiple_files=True)
                
                if st.form_submit_button("💾 SALVAR ALTERAÇÕES", use_container_width=True):
                    updates = {"nome": n_nome, "area": n_area, "descricao": n_desc}
                    if n_foto: updates["foto_url"] = otimizar_imagem_perfil(n_foto)
                    if n_portfolio:
                        for i in range(1, 5): updates[f'f{i}'] = None
                        for i, f in enumerate(n_portfolio[:4]): updates[f"f{i+1}"] = otimizar_imagem_perfil(f)
                    doc_ref.update(updates)
                    st.success("✅ Atualizado!")
                    st.rerun()

        if not d.get('fb_uid'):
            with st.expander("🔗 CONECTAR FACEBOOK"):
                st.link_button("VINCULAR AGORA", url_direta_fb, use_container_width=True)

        col_out, col_del = st.columns(2)
        if col_out.button("🚪 SAIR"): st.session_state.auth = False; st.rerun()
        with col_del.expander("⚠️ EXCLUIR"):
            if st.button("CONFIRMAR EXCLUSÃO"): doc_ref.delete(); st.session_state.auth = False; st.rerun()

# --- ABA 1: CADASTRAR & EDITAR ---
with menu_abas[1]:
    st.markdown("### 🚀 Cadastro ou Edição de Profissional")
    doc_cat = db.collection("configuracoes").document("categorias").get()
    CATS = doc_cat.to_dict().get("lista", ["Pedreiro", "Eletricista"]) if doc_cat.exists else CATEGORIAS_OFICIAIS
    
    dados_google = st.session_state.get("pre_cadastro", {})
    with st.form("form_profissional", clear_on_submit=False):
        c1, c2 = st.columns(2)
        nome_input = c1.text_input("Nome", value=dados_google.get("nome", ""))
        zap_input = c2.text_input("WhatsApp (DDD + Número)")
        email_input = st.text_input("E-mail", value=dados_google.get("email", ""))
        c3, c4 = st.columns(2)
        cat_input = c3.selectbox("Especialidade", CATS)
        senha_input = c4.text_input("Senha", type="password")
        desc_input = st.text_area("Descrição")
        tipo_input = st.radio("Tipo", ["👨‍🔧 Profissional Autônomo", "🏢 Comércio/Loja"], horizontal=True)
        foto_upload = st.file_uploader("Foto de Perfil", type=['png', 'jpg', 'jpeg'])
        # --- LÓGICA DE SALVAMENTO (Continuação Aba 1) ---
        if st.form_submit_button("✅ FINALIZAR: SALVAR OU ATUALIZAR", use_container_width=True):
            if not nome_input or not zap_input or not senha_input:
                st.warning("⚠️ Nome, WhatsApp e Senha são obrigatórios!")
            else:
                try:
                    with st.spinner("Sincronizando com o ecossistema GeralJá..."):
                        doc_ref = db.collection("profissionais").document(zap_input)
                        perfil_antigo = doc_ref.get()
                        dados_antigos = perfil_antigo.to_dict() if perfil_antigo.exists else {}
                        foto_b64 = dados_antigos.get("foto_url", "")
                        if foto_upload:
                            foto_b64 = otimizar_imagem_perfil(foto_upload, size=(350, 350))
                        elif not foto_b64 and dados_google.get("foto"):
                            foto_b64 = dados_google.get("foto")
                        
                        dados_pro = {
                            "nome": nome_input, "whatsapp": zap_input, "email": email_input,
                            "area": cat_input, "senha": senha_input, "descricao": desc_input,
                            "tipo": tipo_input, "foto_url": foto_b64, "saldo": dados_antigos.get("saldo", 0),
                            "data_cadastro": datetime.now().strftime("%d/%m/%Y"), "aprovado": True,
                            "cliques": dados_antigos.get("cliques", 0), "rating": 5,
                            "lat": -23.55, "lon": -46.63
                        }
                        doc_ref.set(dados_pro)
                        if "pre_cadastro" in st.session_state: del st.session_state["pre_cadastro"]
                        st.balloons()
                        st.success("✅ Sucesso!")
                except Exception as e: st.error(f"❌ Erro: {e}")

# --- ABA 3: TORRE DE CONTROLE (ADMIN) ---
with menu_abas[3]:
    if 'admin_logado' not in st.session_state: st.session_state.admin_logado = False
    if not st.session_state.admin_logado:
        with st.form("login_adm"):
            u = st.text_input("Usuário")
            p = st.text_input("Senha", type="password")
            if st.form_submit_button("ACESSAR"):
                if u == st.secrets.get("ADMIN_USER", "geralja") and p == st.secrets.get("ADMIN_PASS", "Bps36ocara"):
                    st.session_state.admin_logado = True; st.rerun()
    else:
        st.subheader("👑 Painel Administrativo")
        if st.button("🚪 Logout Admin"): st.session_state.admin_logado = False; st.rerun()

# --- ABA 4: FEEDBACK ---
with menu_abas[4]:
    st.header("⭐ Avalie")
    nota = st.slider("Nota", 1, 5, 5)
    if st.button("Enviar"): st.success("Obrigado!")

# --- NOVO: SISTEMA DE MÓDULOS (PLUGINS) ---
def carregar_novos_modulos():
    pasta = "modulos"
    if not os.path.exists(pasta): os.makedirs(pasta)
    for arquivo in os.listdir(pasta):
        if arquivo.endswith(".py"):
            nome_mod = arquivo[:-3]
            try:
                spec = importlib.util.spec_from_file_location(nome_mod, f"{pasta}/{arquivo}")
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, "run"): mod.run()
            except Exception as e: st.error(f"Erro no plugin {arquivo}: {e}")

carregar_novos_modulos()

# --- MOTOR DE AUTOCORREÇÃO (WATCHDOG) ---
def verificar_integridade():
    try:
        if not db: raise Exception("Conexão perdida.")
    except Exception:
        st.error("⚠️ Erro crítico detectado. Resetando para modo de segurança.")
        st.session_state.clear()
        st.rerun()

verificar_integridade()

# --- FINALIZAÇÃO (RODAPÉ) ---
finalizar_e_alinhar_layout()

st.markdown("""
<div class="footer-container">
    <div class="security-badge">
        <span class="shield-icon">🛡️</span> IA de Proteção Ativa: Modo Seguro Ativo
    </div>
    <p>© 2026 GeralJá - Grajaú, São Paulo</p>
</div>
""", unsafe_allow_html=True)

with st.expander("📄 Privacidade (LGPD)"):
    st.info("Sistema operando em modo resiliente.")
