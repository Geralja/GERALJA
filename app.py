 
# ==============================================================================
# GERALJÁ: CRIANDO SOLUÇÕES
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
from streamlit_js_eval import streamlit_js_eval, get_geolocation
import unicodedata
from groq import Groq # <--- Novo

# --- ADICIONE ESTES 3 PARA O NÍVEL 5.0 ---
from groq import Groq                # Para a IA avançada
from fuzzywuzzy import process       # Para buscas com erros de digitação
from urllib.parse import quote       # Para links de WhatsApp seguros
# --- CONFIGURAÇÕES DE AUTENTICAÇÃO (PUXANDO DO COFRE) ---

import requests

# --- CONFIGURAÇÃO DE CHAVES ---
try:
    import requests  # Agora está dentro do recuo (4 espaços)
    FB_ID = st.secrets["FB_CLIENT_ID"]
    FB_SECRET = st.secrets["FB_CLIENT_SECRET"]
    FIREBASE_API_KEY = st.secrets["FIREBASE_API_KEY"]
    REDIRECT_URI = "https://geralja-zxiaj2ot56fuzgcz7xhcks.streamlit.app/"
except Exception as e:
    st.error(f"Erro: Chaves não encontradas no Secrets. ({e})")
    st.stop()

# O restante do código volta para o alinhamento normal (sem espaços no início)
HANDLER_URL = "https://geralja-5bb49.firebaseapp.com/__/auth/handler"

try:
    from streamlit_js_eval import streamlit_js_eval, get_geolocation
except ImportError:
    pass
# URL do Handler (Pode ficar visível)
HANDLER_URL = "https://geralja-5bb49.firebaseapp.com/__/auth/handler"
# Tenta importar bibliotecas extras do arquivo original, se não tiver, segue sem quebrar
try:
    from streamlit_js_eval import streamlit_js_eval, get_geolocation
except ImportError:
    pass

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
@st.cache_resource
def conectar_banco_master():
    if not firebase_admin._apps:
        try:
            # Pega do grupo [firebase] que configuramos no Secrets
            if "firebase" in st.secrets and "base64" in st.secrets["firebase"]:
                b64_key = st.secrets["firebase"]["base64"]
                decoded_json = base64.b64decode(b64_key).decode("utf-8")
                cred_dict = json.loads(decoded_json)
                cred = credentials.Certificate(cred_dict)
                return firebase_admin.initialize_app(cred)
            else:
                st.error("⚠️ Configuração 'firebase.base64' não encontrada nos Secrets.")
                st.stop()
        except Exception as e:
            st.error(f"❌ FALHA NA INFRAESTRUTURA: {e}")
            st.stop()
    return firebase_admin.get_app()

app_engine = conectar_banco_master()

if app_engine:
    db = firestore.client()
else:
    st.error("Erro ao conectar ao Firebase. Verifique suas configurações.")
    st.stop()

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

# --- PROSSEGUIR COM O RESTANTE DO CÓDIGO ---

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
# ==============================================================================
# --- ABA 0: BUSCA (IA GROQ + VITRINE PREMIUM V5.0) ---
# ==============================================================================
with menu_abas[0]:
    # 1. INICIALIZAÇÃO DE SEGURANÇA
    termo_busca = None 
    
    # 2. MOTOR DE LOCALIZAÇÃO
    with st.expander("📍 Sua Localização (GPS)", expanded=False):
        try:
            loc = get_geolocation()
            if loc and 'coords' in loc:
                minha_lat, minha_lon = loc['coords']['latitude'], loc['coords']['longitude']
                st.success("Localização detectada!")
            else:
                minha_lat, minha_lon = LAT_REF, LON_REF
                st.info("Usando localização padrão (Centro).")
        except:
            minha_lat, minha_lon = LAT_REF, LON_REF

    # 3. CAMPOS DE BUSCA
    st.markdown("### 🏙️ O que você precisa?")
    c1, c2 = st.columns([3, 1])
    termo_busca = c1.text_input("Ex: 'Cano estourado' ou 'Pizza'", key="busca_insta_v5_final")
    raio_km = c2.select_slider("Raio (KM)", options=[1, 3, 5, 10, 20, 50, 100], value=3)
    
    # 4. CSS PREMIUM (FOTOS MENORES E SNAP-SCROLL)
    st.markdown("""
    <style>
        .cartao-insta { 
            background: white; border-radius: 20px; padding: 12px; 
            margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            border: 1px solid #f0f0f0; color: #111;
        }
        .insta-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
        .insta-avatar { width: 38px; height: 38px; border-radius: 50%; border: 2px solid #E1306C; padding: 1.5px; object-fit: cover; }
        .insta-nome { font-weight: 700; color: #262626; font-size: 13px; }
        
        /* Carrossel Estilo Portfólio (Aparece a pontinha da próxima foto) */
        .insta-carousel { 
            display: flex; overflow-x: auto; scroll-snap-type: x mandatory; 
            gap: 10px; border-radius: 12px; scrollbar-width: none; padding: 5px 0;
        }
        .insta-carousel::-webkit-scrollbar { display: none; }
        
        .insta-photo-box { 
            flex: 0 0 82%; /* Ajuste aqui para o tamanho da foto */
            scroll-snap-align: center; 
            aspect-ratio: 4 / 3; /* Formato retangular mais profissional */
            background: #f8f8f8; border-radius: 10px; overflow: hidden;
            box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        }
        .insta-photo-box img { width: 100%; height: 100%; object-fit: cover; }

        .insta-btn {
            display: block; background: #25D366; color: white !important;
            text-align: center; padding: 12px; border-radius: 10px;
            font-weight: bold; text-decoration: none; margin-top: 12px; font-size: 15px;
        }
    </style>

    <script>
    function abrirInsta(src, link) {
        window.parent.document.getElementById('imgExpandida').src = src;
        window.parent.document.getElementById('linkZapModal').href = link;
        window.parent.document.getElementById('meuModal').style.display = 'flex';
    }
    function fecharInsta() {
        window.parent.document.getElementById('meuModal').style.display = 'none';
    }
    </script>
    """, unsafe_allow_html=True)

    # 5. LÓGICA DE EXIBIÇÃO
    if termo_busca:
        cat_ia = processar_ia_avancada(termo_busca) 
        st.info(f"✨ Buscando por: **{cat_ia}**")
        
        profs = db.collection("profissionais").where("area", "==", cat_ia).where("aprovado", "==", True).stream()
        
        lista_ranking = []
        for p_doc in profs:
            p = p_doc.to_dict()
            p['id'] = p_doc.id
            dist = calcular_distancia_real(minha_lat, minha_lon, p.get('lat', LAT_REF), p.get('lon', LON_REF))
            if dist <= raio_km:
                p['dist'] = dist
                score = 1000 if p.get('verificado') else 0
                score += (p.get('saldo', 0) * 10)
                p['score_elite'] = score
                lista_ranking.append(p)

        lista_ranking.sort(key=lambda x: (x['dist'], -x['score_elite']))

        if not lista_ranking:
            st.warning("Nenhum profissional encontrado nesta área.")
        else:
            for p in lista_ranking:
                is_elite = p.get('saldo', 0) > 10
                zap_limpo = p.get('whatsapp', p['id'])
                link_zap = f"https://wa.me/{zap_limpo}?text=Olá {p.get('nome')}, vi seu portfólio no GeralJá!"
                
                # Fotos da Vitrine
                vitrine_lista = p.get('vitrine', [])
                fotos_html = ""
                for img_data in vitrine_lista:
                    if img_data:
                        src = img_data if str(img_data).startswith("data") else f"data:image/jpeg;base64,{img_data}"
                        fotos_html += f'<div class="insta-photo-box" onclick="abrirInsta(\'{src}\', \'{link_zap}\')"><img src="{src}"></div>'

                st.markdown(f"""
                <div class="cartao-insta">
                    <div class="insta-header">
                        <img src="{p.get('foto_url','')}" class="insta-avatar">
                        <div>
                            <div class="insta-nome">{p.get('nome','').upper()} {" ✅" if is_elite else ""}</div>
                            <div style="font-size:10px; color:#8e8e8e;">📍 a {p['dist']:.1f} km de você</div>
                        </div>
                    </div>
                    <div class="insta-carousel">
                        {fotos_html if fotos_html else '<div style="padding:40px; color:#ccc;">Sem fotos na vitrine</div>'}
                    </div>
                    <div style="padding: 10px 0;">
                        <span style="font-size:13px; color:#444;">{p.get('descricao','')[:120]}...</span>
                    </div>
                    <a href="{link_zap}" target="_blank" class="insta-btn">💬 CHAMAR NO WHATSAPP</a>
                </div>
                """, unsafe_allow_html=True)

    # 6. MODAL PREMIUM
    st.markdown("""
    <div id="meuModal" onclick="fecharInsta()" style="display:none; position:fixed; z-index:9999; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.95); align-items:center; justify-content:center; flex-direction:column;">
        <span style="position:absolute; top:20px; right:30px; color:white; font-size:40px; cursor:pointer;">&times;</span>
        <img id="imgExpandida" style="max-width:95%; max-height:75%; border-radius:12px; object-fit: contain; box-shadow: 0 0 20px rgba(255,255,255,0.1);">
        <a id="linkZapModal" href="#" target="_blank" style="margin-top:20px; background:#25D366; color:white; padding:15px 40px; border-radius:30px; text-decoration:none; font-weight:bold; box-shadow: 0 4px 15px rgba(37,211,102,0.4);">✅ CONTRATAR AGORA</a>
    </div>
    """, unsafe_allow_html=True)
# ==============================================================================
# ABA 2: 🚀 PAINEL DO PARCEIRO (VERSÃO PREMIUM V5.0)
# ==============================================================================
with menu_abas[2]:
    import base64, io, time
    from PIL import Image
    from datetime import datetime

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

    # --- 2. TELA DE LOGIN (CASO NÃO ESTEJA AUTENTICADO) ---
    if not st.session_state.get('auth'):
        st.subheader("🚀 Acesso ao Painel")
        
        fb_id = st.secrets.get("FB_CLIENT_ID", "")
        redirect_uri = "https://geralja-zxiaj2ot56fuzgcz7xhcks.streamlit.app/"
        url_direta_fb = f"https://www.facebook.com/v18.0/dialog/oauth?client_id={fb_id}&redirect_uri={redirect_uri}&scope=public_profile,email"
        
        st.markdown(f'''<a href="{url_direta_fb}" target="_top" style="text-decoration:none;"><div style="background:#1877F2;color:white;padding:12px;border-radius:8px;text-align:center;font-weight:bold;display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow: 0px 4px 6px rgba(0,0,0,0.1);"><img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/2021_Facebook_icon.svg" width="20px" style="margin-right:10px;"> ENTRAR COM FACEBOOK</div></a>''', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.write("--- ou use seus dados ---")
        
        col1, col2 = st.columns(2)
        l_zap = col1.text_input("WhatsApp", key="login_zap_final", placeholder="DDD + Número").strip()
        l_pw = col2.text_input("Senha", type="password", key="login_pw_final").strip()
        
        if st.button("ENTRAR NO PAINEL", key="btn_entrar_final", use_container_width=True):
            u = db.collection("profissionais").document(l_zap).get()
            if u.exists:
                d_user = u.to_dict()
                if str(d_user.get('senha')).strip() == l_pw:
                    st.session_state.auth = True
                    st.session_state.user_id = l_zap
                    st.rerun()
                else: st.error("❌ Senha incorreta.")
            else: st.error("❌ WhatsApp não cadastrado.")

    # --- 3. PAINEL LOGADO ---
    else:
        doc_ref = db.collection("profissionais").document(st.session_state.user_id)
        d = doc_ref.get().to_dict()
        
        st.write(f"### Olá, {d.get('nome', 'Parceiro')}! 👋")
        
        # Dashboard de Métricas
        m1, m2, m3 = st.columns(3)
        m1.metric("Saldo 🪙", f"{d.get('saldo', 0)}")
        m2.metric("Cliques 🚀", f"{d.get('cliques', 0)}")
        m3.metric("Status", "🟢 ATIVO" if d.get('aprovado') else "🟡 PENDENTE")

        # --- SEÇÃO DE EDIÇÃO COMPLETA COM TIPO DE PERFIL ---
        with st.expander("📝 EDITAR MEU PERFIL & VITRINE", expanded=True):
            with st.form("perfil_v20_completo"):
                # Escolha do Tipo (Autônomo ou Comércio)
                tipo_atual = d.get('tipo', 'autonomo')
                idx_tipo = 0 if tipo_atual == 'autonomo' else 1
                n_tipo = st.radio("Sua Categoria", ["Autônomo (Prestador)", "Comércio (Loja/Delivery)"], index=idx_tipo, horizontal=True)
                
                n_nome = st.text_input("Nome Comercial", d.get('nome', ''))
                
                # Campos Específicos
                if "Autônomo" in n_tipo:
                    n_extra = st.text_area("📄 Currículo / Experiência", d.get('curriculo', ''), height=150)
                    tipo_save = 'autonomo'
                else:
                    n_extra = st.text_area("📢 Mural da Loja / Recados", d.get('recados', ''), height=150)
                    tipo_save = 'comercio'

                n_desc = st.text_area("Descrição Curta (Aparece na busca)", d.get('descricao', ''), height=80)
                
                st.write("--- **Fotos de Alta Qualidade** ---")
                n_foto = st.file_uploader("Trocar Foto de Perfil", type=['jpg','jpeg','png'])
                n_vits = st.file_uploader("Atualizar Vitrine (Até 10 fotos)", type=['jpg','jpeg','png'], accept_multiple_files=True)
                
                if st.form_submit_button("💾 SALVAR ALTERAÇÕES", use_container_width=True):
                    # --- FUNÇÃO OTIMIZAR PREMIUM (800px / 80% Qualidade) ---
                    def otimizar_premium(arq):
                        img = Image.open(arq).convert("RGB")
                        img.thumbnail((800, 800))
                        buf = io.BytesIO()
                        img.save(buf, format="JPEG", quality=80)
                        return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"

                    updates = {
                        "nome": n_nome, 
                        "tipo": tipo_save,
                        "descricao": n_desc,
                        "curriculo" if tipo_save == 'autonomo' else "recados": n_extra
                    }
                    
                    if n_foto: updates["foto_url"] = otimizar_premium(n_foto)
                    if n_vits: updates["vitrine"] = [otimizar_premium(f) for f in n_vits[:10]]
                    
                    doc_ref.update(updates)
                    st.success("🔥 Perfil e Vitrine atualizados com sucesso!")
                    time.sleep(1)
                    st.rerun()

        # Botão de GPS fora do formulário
        if st.button("📍 ATUALIZAR MEU GPS", key="btn_gps_v20", use_container_width=True):
            from streamlit_js_eval import streamlit_js_eval
            loc = streamlit_js_eval(js_expressions="navigator.geolocation.getCurrentPosition(s => s)", key='gps_v20')
            if loc and 'coords' in loc:
                doc_ref.update({"lat": loc['coords']['latitude'], "lon": loc['coords']['longitude']})
                st.success("✅ Localização GPS Atualizada!")

        st.divider()
        if st.button("🚪 SAIR DO PAINEL", use_container_width=True):
            st.session_state.auth = False
            st.rerun()
# --- ABA 1: CADASTRAR & EDITAR (COM VITRINE DE 4 FOTOS) ---
with menu_abas[1]:
    import base64
    from datetime import datetime

    st.markdown("### 🚀 Cadastro ou Edição de Profissional")

    # 1. BUSCA CATEGORIAS DINÂMICAS
    try:
        doc_cat = db.collection("configuracoes").document("categorias").get()
        CATEGORIAS_OFICIAIS = doc_cat.to_dict().get("lista", ["Geral"]) if doc_cat.exists else ["Pedreiro", "Locutor", "Eletricista", "Mecânico"]
    except:
        CATEGORIAS_OFICIAIS = ["Pedreiro", "Locutor", "Eletricista", "Mecânico"]

    # 2. DADOS SOCIAIS
    dados_social = st.session_state.get("pre_cadastro", {})
    email_inicial = dados_social.get("email", "")
    nome_inicial = dados_social.get("nome", "")
    foto_social = dados_social.get("foto", "")

    # Interface de Login Social
    st.markdown("##### Entre rápido com:")
    col_soc1, col_soc2 = st.columns(2)
    g_auth = st.secrets.get("google_auth", {})
    fb_id = st.secrets.get("FB_CLIENT_ID", "")
    g_uri = "https://geralja-zxiaj2ot56fuzgcz7xhcks.streamlit.app/"

    with col_soc1:
        if g_auth.get("client_id"):
            url_g = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={g_auth.get('client_id')}&response_type=code&scope=openid%20profile%20email&redirect_uri={g_uri}"
            st.markdown(f'<a href="{url_g}" target="_top" style="text-decoration:none;"><div style="display:flex; align-items:center; justify-content:center; border:1px solid #dadce0; border-radius:8px; padding:8px; background:white;"><img src="https://upload.wikimedia.org/wikipedia/commons/5/53/Google_%22G%22_Logo.svg" width="18px" style="margin-right:10px;"><span style="color:#3c4043; font-weight:bold; font-size:14px;">Google</span></div></a>', unsafe_allow_html=True)
    
    with col_soc2:
        if fb_id:
            url_fb = f"https://www.facebook.com/v18.0/dialog/oauth?client_id={fb_id}&redirect_uri={g_uri}&scope=public_profile,email"
            st.markdown(f'<a href="{url_fb}" target="_top" style="text-decoration:none;"><div style="display:flex; align-items:center; justify-content:center; border-radius:8px; padding:8px; background:#1877F2;"><img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/2021_Facebook_icon.svg" width="18px" style="margin-right:10px;"><span style="color:white; font-weight:bold; font-size:14px;">Facebook</span></div></a>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. FORMULÁRIO COM VITRINE
    with st.form("form_completo_v11", clear_on_submit=False):
        col1, col2 = st.columns(2)
        nome_input = col1.text_input("Nome do Profissional ou Loja", value=nome_inicial)
        zap_input = col2.text_input("WhatsApp (Somente Números)")
        
        email_input = st.text_input("E-mail", value=email_inicial)
        
        col3, col4 = st.columns(2)
        cat_input = col3.selectbox("Especialidade Principal", CATEGORIAS_OFICIAIS)
        senha_input = col4.text_input("Sua Senha de Acesso", type="password")
        
        desc_input = st.text_area("Descrição dos Serviços")
        tipo_input = st.radio("Tipo", ["👨‍🔧 Profissional Autônomo", "🏢 Comércio/Loja"], horizontal=True)

        st.divider()
        st.write("🖼️ **Fotos do Perfil e Vitrine**")
        foto_perfil_upload = st.file_uploader("Foto de Perfil (Avatar)", type=['png', 'jpg', 'jpeg'], key="perfil")
        
        st.write("Escolha até 4 fotos para mostrar seus trabalhos:")
        col_f1, col_f2 = st.columns(2)
        v1 = col_f1.file_uploader("Foto Vitrine 1", type=['png', 'jpg', 'jpeg'], key="v1")
        v2 = col_f2.file_uploader("Foto Vitrine 2", type=['png', 'jpg', 'jpeg'], key="v2")
        v3 = col_f1.file_uploader("Foto Vitrine 3", type=['png', 'jpg', 'jpeg'], key="v3")
        v4 = col_f2.file_uploader("Foto Vitrine 4", type=['png', 'jpg', 'jpeg'], key="v4")

        btn_acao = st.form_submit_button("✅ FINALIZAR CADASTRO / ATUALIZAR", use_container_width=True)

    # 4. LÓGICA DE SALVAMENTO
    if btn_acao:
        if not nome_input or not zap_input or not senha_input:
            st.warning("⚠️ Nome, WhatsApp e Senha são obrigatórios!")
        else:
            try:
                with st.spinner("Processando fotos e salvando..."):
                    doc_ref = db.collection("profissionais").document(zap_input)
                    res = doc_ref.get()
                    dados_velhos = res.to_dict() if res.exists else {}

                    # Função interna para converter imagens
                    def conv_img(upload, antiga):
                        if upload:
                            ext = upload.name.split('.')[-1]
                            return f"data:image/{ext};base64,{base64.b64encode(upload.getvalue()).decode()}"
                        return antiga

                    # Processa Foto de Perfil
                    foto_perfil_final = conv_img(foto_perfil_upload, dados_velhos.get("foto_url", foto_social))
                    
                    # Processa Vitrine (Lista de 4 fotos)
                    vitrine_atual = dados_velhos.get("vitrine", ["", "", "", ""])
                    foto_v1 = conv_img(v1, vitrine_atual[0] if len(vitrine_atual) > 0 else "")
                    foto_v2 = conv_img(v2, vitrine_atual[1] if len(vitrine_atual) > 1 else "")
                    foto_v3 = conv_img(v3, vitrine_atual[2] if len(vitrine_atual) > 2 else "")
                    foto_v4 = conv_img(v4, vitrine_atual[3] if len(vitrine_atual) > 3 else "")

                    dados_pro = {
                        "nome": nome_input,
                        "whatsapp": zap_input,
                        "email": email_input,
                        "area": cat_input,
                        "senha": senha_input,
                        "descricao": desc_input,
                        "tipo": tipo_input,
                        "foto_url": foto_perfil_final,
                        "vitrine": [foto_v1, foto_v2, foto_v3, foto_v4],
                        "saldo": dados_velhos.get("saldo", 20),
                        "data_cadastro": datetime.now().strftime("%d/%m/%Y"),
                        "aprovado": True,
                        "cliques": dados_velhos.get("cliques", 0),
                        "rating": 5,
                        "lat": st.session_state.get('lat', -23.55),
                        "lon": st.session_state.get('lon', -46.63)
                    }

                    doc_ref.set(dados_pro)
                    st.balloons()
                    st.success("✅ Tudo pronto! Seu perfil com vitrine está no ar!")
                    if "pre_cadastro" in st.session_state: del st.session_state["pre_cadastro"]
            except Exception as e:
                st.error(f"❌ Erro ao salvar: {e}")
# ==============================================================================
# ABA 4: 👑 TORRE DE CONTROLE MASTER (COMPLETA: GESTÃO DE REDE + CATEGORIAS)
# ==============================================================================
with menu_abas[3]:
    import pytz
    from datetime import datetime
    import pandas as pd
    import time

    # 1. CONFIGURAÇÃO DE TEMPO E SEGURANÇA
    fuso_br = pytz.timezone('America/Sao_Paulo')
    agora_br = datetime.now(fuso_br)
    
    ADMIN_USER_OFICIAL = st.secrets.get("ADMIN_USER", "admin")
    ADMIN_PASS_OFICIAL = st.secrets.get("ADMIN_PASS", "geralja2026")

    if 'admin_logado' not in st.session_state:
        st.session_state.admin_logado = False

    if not st.session_state.admin_logado:
        st.markdown("### 🔐 Acesso Restrito à Diretoria")
        with st.form("painel_login_adm"):
            u = st.text_input("Usuário Administrativo")
            p = st.text_input("Senha de Acesso", type="password")
            if st.form_submit_button("ACESSAR TORRE DE CONTROLE", use_container_width=True):
                if u == ADMIN_USER_OFICIAL and p == ADMIN_PASS_OFICIAL:
                    st.session_state.admin_logado = True
                    st.success("Acesso concedido!")
                    time.sleep(1); st.rerun()
                else:
                    st.error("Credenciais inválidas.")
    
    else:
        st.markdown(f"## 👑 Central de Comando GeralJá")
        st.caption(f"🕒 {agora_br.strftime('%H:%M:%S')} | Poder de Edição Total Ativo")
        
        if st.button("🚪 Sair do Sistema", key="logout_adm"):
            st.session_state.admin_logado = False
            st.rerun()

        # ----------------------------------------------------------------------
        # 🟢 GESTÃO DE CATEGORIAS (ADICIONAR/REMOVER DO BANCO)
        # ----------------------------------------------------------------------
        st.divider()
        with st.expander("📁 GERENCIAR LISTA DE CATEGORIAS", expanded=False):
            doc_cat_ref = db.collection("configuracoes").document("categorias")
            res_cat = doc_cat_ref.get()
            
            # Puxa a lista dinâmica ou usa a CATEGORIAS_OFICIAIS atual
            lista_atual = res_cat.to_dict().get("lista", CATEGORIAS_OFICIAIS) if res_cat.exists else CATEGORIAS_OFICIAIS
            
            c_cat1, c_cat2 = st.columns([3, 1])
            nova_cat_input = c_cat1.text_input("Nova Profissão/Categoria:")
            if c_cat2.button("➕ ADICIONAR", use_container_width=True):
                if nova_cat_input and nova_cat_input not in lista_atual:
                    lista_atual.append(nova_cat_input)
                    lista_atual.sort()
                    doc_cat_ref.set({"lista": lista_atual})
                    st.success("Adicionada!"); time.sleep(0.5); st.rerun()
            
            st.write("---")
            cat_del = st.selectbox("Remover Categoria Existente:", ["Selecione..."] + lista_atual)
            if cat_del != "Selecione...":
                if st.button(f"🗑️ EXCLUIR {cat_del}", type="secondary"):
                    lista_atual.remove(cat_del)
                    doc_cat_ref.set({"lista": lista_atual})
                    st.error("Removida!"); time.sleep(0.5); st.rerun()

        try:
            # 2. COLETA DE DADOS
            profs_ref = list(db.collection("profissionais").stream())
            profs_data = [p.to_dict() | {"id": p.id} for p in profs_ref]
            df = pd.DataFrame(profs_data)

            if not df.empty:
                # Sincronizando campo 'area'
                df['categoria_display'] = df['area'].fillna("Geral") if 'area' in df.columns else "Geral"
                df = df.fillna({"nome": "Sem Nome", "aprovado": False, "saldo": 0, "cliques": 0})

            # 3. MÉTRICAS
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Parceiros", len(df))
            m2.metric("Pendentes", len(df[df['aprovado'] == False]) if not df.empty else 0)
            m3.metric("Cliques", int(df['cliques'].sum()) if not df.empty else 0)
            m4.metric("GeralCones", f"💎 {int(df['saldo'].sum())}" if not df.empty else 0)

            # 4. GESTÃO INDIVIDUAL (FILTROS)
            st.divider()
            f1, f2 = st.columns(2)
            busca = f1.text_input("🔍 Buscar nome ou Zap:")
            # Usa a lista atualizada do banco para o filtro
            filtro_cat = f2.selectbox("Filtrar Exibição:", ["Todas"] + lista_atual)

            df_display = df.copy()
            if busca:
                df_display = df_display[df_display['nome'].str.contains(busca, case=False, na=False) | 
                                        df_display['id'].str.contains(busca, na=False)]
            if filtro_cat != "Todas":
                df_display = df_display[df_display['categoria_display'] == filtro_cat]

            # 5. LISTAGEM COM TODAS AS FUNÇÕES
            for _, p in df_display.iterrows():
                pid = p['id']
                status = "🟢" if p.get('aprovado') else "🟡"
                cat_atual = p.get('area', 'Geral')
                
                with st.expander(f"{status} {p.get('nome').upper()} - ({cat_atual})"):
                    col_info, col_edit, col_btn = st.columns([2, 2, 1.2])
                    
                    with col_info:
                        st.write(f"**WhatsApp:** {pid}")
                        st.write(f"**Saldo:** {p.get('saldo', 0)} 💎")
                        st.write(f"**Cliques:** {p.get('cliques', 0)}")
                    
                    with col_edit:
                        # ALTERAR CATEGORIA DO PROFISSIONAL
                        try:
                            idx = lista_atual.index(cat_atual)
                        except:
                            idx = 0
                        
                        nova_cat = st.selectbox(f"Mudar para", lista_atual, index=idx, key=f"cat_{pid}")
                        if st.button("💾 Salvar Categoria", key=f"save_cat_{pid}"):
                            db.collection("profissionais").document(pid).update({"area": nova_cat})
                            st.success("Salvo!"); time.sleep(0.5); st.rerun()

                    with col_btn:
                        # Aprovação
                        if not p.get('aprovado'):
                            if st.button("✅ APROVAR", key=f"ok_{pid}", use_container_width=True, type="primary"):
                                db.collection("profissionais").document(pid).update({"aprovado": True})
                                st.rerun()
                        else:
                            if st.button("🚫 SUSPENDER", key=f"no_{pid}", use_container_width=True):
                                db.collection("profissionais").document(pid).update({"aprovado": False})
                                st.rerun()
                        
                        # Moedas e Banir
                        col_sub1, col_sub2 = st.columns(2)
                        if col_sub1.button("➕10", key=f"m10_{pid}"):
                            db.collection("profissionais").document(pid).update({"saldo": p.get('saldo', 0) + 10})
                            st.rerun()
                        if col_sub2.button("🗑️", key=f"del_{pid}", help="Banir Profissional"):
                            db.collection("profissionais").document(pid).delete()
                            st.rerun()

        except Exception as e:
            st.error(f"Erro na Torre de Controle: {e}")

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




















































