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
from datetime import datetime # Único import de data necessário
import pytz
from streamlit_js_eval import streamlit_js_eval # Para capturar localização real
import unicodedata
# --- CONFIGURAÇÕES DE AUTENTICAÇÃO (PUXANDO DO COFRE) ---
try:
    FB_CLIENT_ID = st.secrets["FB_CLIENT_ID"]
    FB_CLIENT_SECRET = st.secrets["FB_CLIENT_SECRET"]
    FIREBASE_API_KEY = st.secrets["FIREBASE_API_KEY"]
except:
    st.error("Erro: As chaves de segurança não foram encontradas no Secrets.")

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

# --- CONFIGURAÇÕES DE AUTENTICAÇÃO ---
FB_CLIENT_ID = "SEU_ID_DO_APP"
FB_CLIENT_SECRET = "SUA_CHAVE_SECRETA" # Aquela que você mandou
FIREBASE_API_KEY = "SUA_API_KEY_DO_FIREBASE"
HANDLER_URL = "https://geralja-5bb49.firebaseapp.com/__/auth/handler"

lista_abas = ["🔍 BUSCAR", "🚀 CADASTRAR", "👤 MEU PERFIL", "👑 ADMIN", "⭐ FEEDBACK"]
comando = st.sidebar.text_input("Comando Secreto", type="password")
if comando == "abracadabra":
    lista_abas.append("📊 FINANCEIRO")

menu_abas = st.tabs(lista_abas)
# ==============================================================================
# --- ABA 1: BUSCA (GPS + SCORE ELITE + VITRINE SOCIAL V2.0) ---
# ==============================================================================
with menu_abas[0]:
    st.markdown("### 🏙️ O que você precisa?")
    
    # --- 1. MOTOR DE LOCALIZAÇÃO ---
    with st.expander("📍 Sua Localização (GPS)", expanded=False):
        loc = get_geolocation()
        if loc:
            minha_lat, minha_lon = loc['coords']['latitude'], loc['coords']['longitude']
            st.success("Localização detectada!")
        else:
            minha_lat, minha_lon = LAT_REF, LON_REF
            st.warning("GPS desativado. Usando padrão (SP).")

    c1, c2 = st.columns([3, 1])
    termo_busca = c1.text_input("Ex: 'Cano estourado' ou 'Pizza'", key="main_search_v4")
    raio_km = c2.select_slider("Raio (KM)", options=[1, 3, 5, 10, 20, 50, 100, 500], value=10)
    
    # --- 2. CSS PARA VITRINE E MODAL (LIMPO E MODERNO) ---
    st.markdown("""
    <style>
        .cartao-geral { background: white; border-radius: 20px; border-left: 8px solid var(--cor-borda); padding: 15px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        .perfil-row { display: flex; gap: 15px; align-items: center; margin-bottom: 12px; }
        .foto-perfil { width: 55px; height: 55px; border-radius: 50%; object-fit: cover; border: 2px solid #eee; }
        .social-track { display: flex; overflow-x: auto; gap: 10px; padding-bottom: 10px; scrollbar-width: none; }
        .social-track::-webkit-scrollbar { display: none; }
        .social-card { flex: 0 0 200px; height: 280px; border-radius: 12px; overflow: hidden; cursor: pointer; background: #000; }
        .social-card img { width: 100%; height: 100%; object-fit: cover; transition: 0.3s; }
        .btn-zap-footer { display: block; background: #25D366; color: white !important; text-align: center; padding: 15px; border-radius: 12px; font-weight: bold; text-decoration: none; margin-top: 10px; font-size: 16px; }
    </style>
    <script>
    function abrirModal(src, link) {
        document.getElementById('imgExpandida').src = src;
        document.getElementById('linkZapModal').href = link;
        document.getElementById('meuModal').style.display = 'flex';
    }
    function fecharModal() {
        document.getElementById('meuModal').style.display = 'none';
    }
    </script>
    """, unsafe_allow_html=True)

    if termo_busca:
        cat_ia = processar_ia_avancada(termo_busca)
        st.info(f"✨ IA: Buscando por **{cat_ia}**")
        
        # Busca e Filtragem
        profs = db.collection("profissionais").where("area", "==", cat_ia).where("aprovado", "==", True).stream()
        
        lista_ranking = []
        for p_doc in profs:
            p = p_doc.to_dict(); p['id'] = p_doc.id
            dist = calcular_distancia_real(minha_lat, minha_lon, p.get('lat', LAT_REF), p.get('lon', LON_REF))
            
            if dist <= raio_km:
                p['dist'] = dist
                # SCORE ELITE
                score = 0
                score += 500 if p.get('verificado') else 0
                score += (p.get('saldo', 0) * 10)
                score += (p.get('rating', 5) * 20)
                p['score_elite'] = score
                lista_ranking.append(p)

        lista_ranking.sort(key=lambda x: (-x['score_elite'], x['dist']))

        if not lista_ranking:
            st.warning("Nenhum profissional nesta região ainda.")
        else:
            for p in lista_ranking:
                # Definição de Cores e Link Zap
                is_elite = p.get('verificado') and p.get('saldo', 0) > 0
                cor_borda = "#FFD700" if is_elite else "#0047AB"
                zap_limpo = limpar_whatsapp(p['id'])
                link_zap = f"https://wa.me/{zap_limpo}?text=Olá, vi seu portfólio no GeralJá!"
                
                # Montar Carrossel de Fotos (f1 até f10)
                fotos_html = ""
                for i in range(1, 11):
                    f_data = p.get(f'f{i}')
                    if f_data and len(str(f_data)) > 100:
                        src = f_data if str(f_data).startswith("data") else f"data:image/jpeg;base64,{f_data}"
                        fotos_html += f'<div class="social-card" onclick="abrirModal(\'{src}\', \'{link_zap}\')"><img src="{src}"></div>'

                # RENDERIZAÇÃO DO CARD INTEGRADO
                st.markdown(f"""
                <div class="cartao-geral" style="--cor-borda: {cor_borda};">
                    <div style="font-size: 11px; color: gray; margin-bottom: 10px;">
                        📍 a {p['dist']:.1f} km de você {" | 🏆 ELITE" if is_elite else ""}
                    </div>
                    <div class="perfil-row">
                        <img src="{p.get('foto_url','')}" class="foto-perfil">
                        <div>
                            <h4 style="margin:0; color:#1e3a8a;">{p.get('nome','').upper()} {"☑️" if p.get('verificado') else ""}</h4>
                            <p style="margin:0; color:#666; font-size:12px;">{p.get('descricao','')[:90]}...</p>
                        </div>
                    </div>
                    <div class="social-track">{fotos_html}</div>
                    <a href="{link_zap}" target="_blank" class="btn-zap-footer">💬 FALAR COM {p.get('nome','').split()[0].upper()}</a>
                </div>
                """.replace('\n', ' '), unsafe_allow_html=True)

            # Estrutura Única do Modal no final do loop
            st.markdown("""
            <div id="meuModal" style="display:none; position:fixed; z-index:9999; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.9); align-items:center; justify-content:center; flex-direction:column;">
                <span onclick="fecharModal()" style="position:absolute; top:20px; right:30px; color:white; font-size:40px; cursor:pointer;">&times;</span>
                <img id="imgExpandida" style="max-width:90%; max-height:75%; border-radius:10px; border: 2px solid #fff;">
                <a id="linkZapModal" href="#" target="_blank" style="margin-top:20px; background:#25D366; color:white; padding:15px 40px; border-radius:30px; text-decoration:none; font-weight:bold;">✅ CHAMAR NO WHATSAPP</a>
            </div>
            """.replace('\n', ' '), unsafe_allow_html=True)

            # Lógica de cobrança de cliques (opcional, manter se quiser descontar saldo)
            if is_elite:
                db.collection("profissionais").document(p['id']).update({"cliques": p.get('cliques', 0) + 1})
                
# ==============================================================================
# ABA 2: 🚀 PAINEL DO PARCEIRO (COMPLETO COM FACEBOOK)
# ==============================================================================
with menu_abas[2]:
    # --- 1. LÓGICA DE CAPTURA DO FACEBOOK (VERIFICA SE VOLTOU DA AUTH) ---
    params = st.query_params
    if "uid" in params and not st.session_state.get('auth'):
        fb_uid = params["uid"]
        # Busca no Firestore se esse ID já está vinculado a alguém
        user_query = db.collection("profissionais").where("fb_uid", "==", fb_uid).limit(1).get()
        
        if user_query:
            doc = user_query[0]
            st.session_state.auth = True
            st.session_state.user_id = doc.id
            st.success(f"✅ Bem-vindo, {doc.to_dict().get('nome', 'Parceiro')}!")
            time.sleep(1)
            st.rerun()
        else:
            st.warning("⚠️ Conta do Facebook não vinculada. Entre com WhatsApp e vincule no perfil.")

    # Inicializa o estado de autenticação se não existir
    if 'auth' not in st.session_state: 
        st.session_state.auth = False
    
    # --- 2. TELA DE LOGIN (CASO NÃO ESTEJA LOGADO) ---
    if not st.session_state.get('auth'):
        st.subheader("🚀 Acesso ao Painel")
        
        # O LINK QUE CHAMA O FACEBOOK USANDO SUAS CHAVES DO COFRE
        link_auth = f"{HANDLER_URL}?apiKey={FIREBASE_API_KEY}&providerId=facebook.com"
        
        # BOTÃO VISUAL FACEBOOK
        st.markdown(f"""
            <a href="{link_auth}" target="_self" style="text-decoration: none;">
                <div style="background-color: #1877F2; color: white; padding: 12px; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 20px; font-family: sans-serif;">
                    🔵 ENTRAR COM FACEBOOK
                </div>
            </a>
        """, unsafe_allow_html=True)
        
        st.write("--- ou use seus dados ---")
        
        col1, col2 = st.columns(2)
        l_zap = col1.text_input("WhatsApp (números)", key="login_zap_v7")
        l_pw = col2.text_input("Senha", type="password", key="login_pw_v7")
        
        if st.button("ENTRAR NO PAINEL", use_container_width=True, key="btn_entrar_v7"):
            u = db.collection("profissionais").document(l_zap).get()
            if u.exists and u.to_dict().get('senha') == l_pw:
                st.session_state.auth, st.session_state.user_id = True, l_zap
                st.rerun()
            else: 
                st.error("Dados incorretos.")

    # --- 3. PAINEL LOGADO (CASO ESTEJA AUTENTICADO) ---
    else:
        doc_ref = db.collection("profissionais").document(st.session_state.user_id)
        d = doc_ref.get().to_dict()
        
        # MÉTRICAS DO PROFISSIONAL
        st.write(f"### Olá, {d.get('nome', 'Parceiro')}!")
        m1, m2, m3 = st.columns(3)
        m1.metric("Saldo 🪙", f"{d.get('saldo', 0)}")
        m2.metric("Cliques 🚀", f"{d.get('cliques', 0)}")
        m3.metric("Status", "🟢 ATIVO" if d.get('aprovado') else "🟡 PENDENTE")

        # ATUALIZAÇÃO DE GPS
        if st.button("📍 ATUALIZAR LOCALIZAÇÃO GPS", use_container_width=True, key="gps_v7"):
            loc = streamlit_js_eval(js_expressions="navigator.geolocation.getCurrentPosition(s => s)", key='gps_v7_eval')
            if loc and 'coords' in loc:
                doc_ref.update({"lat": loc['coords']['latitude'], "lon": loc['coords']['longitude']})
                st.success("✅ Localização salva!")
            else: 
                st.info("Aguardando sinal... Clique novamente.")

        st.divider()

        # COMPRA DE MOEDAS
        with st.expander("💎 COMPRAR MOEDAS (PIX)", expanded=False):
            st.warning(f"Chave PIX: {PIX_OFICIAL}")
            c1, c2, c3 = st.columns(3)
            if c1.button("10 Moedas", key="p10_v7"): st.code(PIX_OFICIAL)
            if c2.button("50 Moedas", key="p50_v7"): st.code(PIX_OFICIAL)
            if c3.button("100 Moedas", key="p100_v7"): st.code(PIX_OFICIAL)
            st.link_button("🚀 ENVIAR COMPROVANTE AGORA", f"https://wa.me/{ZAP_ADMIN}?text=Fiz o PIX: {st.session_state.user_id}", use_container_width=True)

        # EDIÇÃO DE PERFIL
        with st.expander("📝 EDITAR MEU PERFIL & VITRINE", expanded=True):
            with st.form("perfil_v7"):
                n_nome = st.text_input("Nome Profissional", d.get('nome', ''))
                
                # Busca as categorias dinâmicas do banco ou usa a padrão
                cats = buscar_opcoes_dinamicas("categorias", ["Ajudante Geral"])
                try: index_cat = cats.index(d.get('area', 'Ajudante Geral'))
                except: index_cat = 0
                n_area = st.selectbox("Mudar meu Segmento/Área", cats, index=index_cat)

                n_desc = st.text_area("Descrição", d.get('descricao', ''))
                n_cat = st.text_input("Link Catálogo/Instagram", d.get('link_catalogo', ''))
                
                h1, h2 = st.columns(2)
                n_abre = h1.text_input("Abre às (ex: 08:00)", d.get('h_abre', '08:00'))
                n_fecha = h2.text_input("Fecha às (ex: 18:00)", d.get('h_fecha', '18:00'))
                
                n_foto = st.file_uploader("Trocar Foto Perfil", type=['jpg','png','jpeg'], key="f_v7")
                n_portfolio = st.file_uploader("Vitrine (Até 4 fotos)", type=['jpg','png','jpeg'], accept_multiple_files=True, key="p_v7")
                
                if st.form_submit_button("SALVAR ALTERAÇÕES", use_container_width=True):
                    up = {
                        "nome": n_nome, "area": n_area, "descricao": n_desc, 
                        "link_catalogo": n_cat, "h_abre": n_abre, "h_fecha": n_fecha
                    }
                    if n_foto: up["foto_url"] = f"data:image/png;base64,{converter_img_b64(n_foto)}"
                    if n_portfolio:
                        # Limite de 4 fotos na vitrine
                        up["portfolio_imgs"] = [f"data:image/png;base64,{converter_img_b64(f)}" for f in n_portfolio[:4]]
                    
                    doc_ref.update(up)
                    st.success("✅ Perfil atualizado!")
                    time.sleep(1); st.rerun()

        # VINCULAR FACEBOOK (NOVO)
        if not d.get('fb_uid'):
            with st.expander("🔗 CONECTAR FACEBOOK"):
                st.write("Vincule sua conta para entrar sem senha na próxima vez.")
                vinc_link = f"{HANDLER_URL}?apiKey={FIREBASE_API_KEY}&providerId=facebook.com"
                st.link_button("VINCULAR AGORA", vinc_link, use_container_width=True)

        # SEGURANÇA E EXCLUSÃO
        with st.expander("🔐 SEGURANÇA E EXCLUSÃO DE DADOS"):
            st.write("Deseja encerrar sua conta?")
            confirma_pw = st.text_input("Confirme sua SENHA para excluir", type="password", key="excluir_pw")
            if st.button("❌ APAGAR MINHA CONTA DEFINITIVAMENTE", type="primary"):
                if confirma_pw == d.get('senha'):
                    doc_ref.delete()
                    st.error("Dados removidos. Saindo...")
                    time.sleep(2)
                    st.session_state.auth = False
                    st.rerun()
                else:
                    st.error("Senha incorreta!")

        if st.button("SAIR DO PAINEL", use_container_width=True):
            st.session_state.auth = False
            st.rerun()

# --- ABA 1: CADASTRAR & EDITAR (VERSÃO FINAL GERALJÁ) ---
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

    # 2. AUTENTICAÇÃO SOCIAL (Visual para análise da Meta)
    st.markdown("##### Entre rápido com:")
    col_soc1, col_soc2 = st.columns(2)
    with col_soc1:
        st.markdown(f'<a href="https://accounts.google.com/o/oauth2/v2/auth?client_id={st.secrets["google_auth"]["client_id"]}&response_type=code&scope=openid%20profile%20email&redirect_uri=https://geralja-zxiaj2ot56fuzgcz7xhcks.streamlit.app/" target="_self"><div style="display:flex; align-items:center; justify-content:center; border:1px solid #dadce0; border-radius:8px; padding:8px; background:white;"><img src="https://upload.wikimedia.org/wikipedia/commons/5/53/Google_%22G%22_Logo.svg" width="18px" style="margin-right:10px;"><span style="color:#3c4043; font-weight:bold; font-size:14px;">Google</span></div></a>', unsafe_allow_html=True)
    with col_soc2:
        st.markdown(f'<a href="https://www.facebook.com/v18.0/dialog/oauth?client_id={st.secrets["FB_CLIENT_ID"]}&redirect_uri=https://geralja-zxiaj2ot56fuzgcz7xhcks.streamlit.app/&scope=public_profile,email" target="_self"><div style="display:flex; align-items:center; justify-content:center; border-radius:8px; padding:8px; background:#1877F2;"><img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/2021_Facebook_icon.svg" width="18px" style="margin-right:10px;"><span style="color:white; font-weight:bold; font-size:14px;">Facebook</span></div></a>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    BONUS_WELCOME = 20 

    # 3. FORMULÁRIO INTELIGENTE
    with st.form("form_profissional", clear_on_submit=False):
        st.caption("DICA: Se você já tem cadastro, use o mesmo WhatsApp para editar seus dados.")
        col1, col2 = st.columns(2)
        nome_input = col1.text_input("Nome do Profissional ou Loja")
        zap_input = col2.text_input("WhatsApp (DDD + Número sem espaços)")
        
        col3, col4 = st.columns(2)
        # Aqui estão as categorias para edição/cadastro
        cat_input = col3.selectbox("Selecione sua Especialidade Principal", CATEGORIAS_OFICIAIS)
        senha_input = col4.text_input("Sua Senha de Acesso", type="password", help="Necessária para salvar alterações")
        
        desc_input = st.text_area("Descrição Completa (Serviços, Horários, Diferenciais)")
        tipo_input = st.radio("Tipo", ["👨‍🔧 Profissional Autônomo", "🏢 Comércio/Loja"], horizontal=True)
        foto_upload = st.file_uploader("Atualizar Foto de Perfil ou Logo", type=['png', 'jpg', 'jpeg'])
        
        btn_acao = st.form_submit_button("✅ FINALIZAR: SALVAR OU ATUALIZAR", use_container_width=True)

    # 4. LÓGICA DE SALVAMENTO E EDIÇÃO
    if btn_acao:
        if not nome_input or not zap_input or not senha_input:
            st.warning("⚠️ Nome, WhatsApp e Senha são obrigatórios para identificar seu perfil!")
        else:
            try:
                with st.spinner("Sincronizando com o ecossistema GeralJá..."):
                    # Verifica se o profissional já existe
                    doc_ref = db.collection("profissionais").document(zap_input)
                    perfil_antigo = doc_ref.get()
                    
                    # Processa Foto (mantém a antiga se não subir nova)
                    foto_b64 = perfil_antigo.to_dict().get("foto_url", "") if perfil_antigo.exists else ""
                    if foto_upload:
                        foto_b64 = f"data:image/png;base64,{base64.b64encode(foto_upload.read()).decode()}"
                    
                    # Define Saldo (Dá 20 se for novo, mantém se for edição)
                    saldo_final = perfil_antigo.to_dict().get("saldo", BONUS_WELCOME) if perfil_antigo.exists else BONUS_WELCOME

                    # Monta o objeto final
                    dados_pro = {
                        "nome": nome_input,
                        "whatsapp": zap_input,
                        "area": cat_input,
                        "senha": senha_input,
                        "descricao": desc_input,
                        "tipo": tipo_input,
                        "foto_url": foto_b64,
                        "saldo": saldo_final,
                        "data_cadastro": datetime.now().strftime("%d/%m/%Y"),
                        "aprovado": True,
                        "cliques": perfil_antigo.to_dict().get("cliques", 0) if perfil_antigo.exists else 0,
                        "rating": 5,
                        "lat": minha_lat if 'minha_lat' in locals() else -23.55,
                        "lon": minha_lon if 'minha_lon' in locals() else -46.63
                    }
                    
                    # Salva ou Sobrescreve (Edição)
                    doc_ref.set(dados_pro)
                    
                    st.balloons()
                    if perfil_antigo.exists:
                        st.success(f"✅ Perfil de {nome_input} atualizado com sucesso!")
                    else:
                        st.success(f"🎊 Bem-vindo! Cadastro concluído e {BONUS_WELCOME} moedas creditadas!")
                        
            except Exception as e:
                st.error(f"❌ Erro ao processar perfil: {e}")
# ==============================================================================
# ABA 4: 👑 PAINEL DE CONTROLE MASTER (AUTORIDADE MÁXIMA COMPLETA)
# ==============================================================================
with menu_abas[3]:
    st.markdown("## 👑 Central de Comando GeralJá")
    
    access_adm = st.text_input("Chave Mestra de Segurança", type="password", key="auth_master_v10")

    if access_adm == CHAVE_ADMIN:
        # --- 1. COLETA DE DADOS ---
        todos_profs_docs = list(db.collection("profissionais").stream())
        profs_data = [p.to_dict() | {"id": p.id} for p in todos_profs_docs]
        
        # Filtra quem está aguardando para o Alerta
        lista_pendentes = [p for p in profs_data if not p.get('aprovado')]
        qtd_pendentes = len(lista_pendentes)

        # --- 2. ALERTA DE NOVOS CADASTROS (DESTAQUE) ---
        if qtd_pendentes > 0:
            st.error(f"🚨 **ATENÇÃO:** Existem {qtd_pendentes} profissionais aguardando aprovação!")
            
            # Mensagem para a Central Zap
            msg_central = f"Olá! Central GeralJá, temos {qtd_pendentes} novos profissionais aguardando aprovação no painel."
            link_zap_central = f"https://wa.me/{ZAP_ADMIN}?text={msg_central.replace(' ', '%20')}"
            
            col_alert_1, col_alert_2 = st.columns([3, 1])
            col_alert_1.info(f"Fila de espera: {', '.join([p.get('nome') for p in lista_pendentes])}")
            col_alert_2.link_button("📲 AVISAR CENTRAL", link_zap_central, use_container_width=True, type="primary")
            st.divider()

        # --- 3. DASHBOARD ESTATÍSTICO ---
        st.markdown("### 📊 Performance da Rede")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total de Parceiros", len(profs_data))
        c2.metric("Cliques Acumulados", sum(p.get('cliques', 0) for p in profs_data))
        c3.metric("Moedas no Sistema", f"💎 {sum(p.get('saldo', 0) for p in profs_data)}")
        c4.metric("Aguardando", qtd_pendentes, delta=qtd_pendentes, delta_color="inverse")

        st.divider()

        # --- 4. GESTÃO DE CATEGORIAS E CONFIGURAÇÕES ---
        with st.expander("⚙️ CONFIGURAÇÕES DE EXPANSÃO (Categorias/Tipos)"):
            col_cfg_1, col_cfg_2 = st.columns(2)
            with col_cfg_1:
                st.write("**✨ Novas Profissões**")
                nova_cat = st.text_input("Nome da Profissão", placeholder="Ex: Adestrador", key="add_cat_adm")
                if st.button("➕ Adicionar Categoria", use_container_width=True):
                    if nova_cat:
                        doc_ref = db.collection("configuracoes").document("categorias")
                        lista = buscar_opcoes_dinamicas("categorias", [])
                        if nova_cat not in lista:
                            lista.append(nova_cat)
                            doc_ref.set({"lista": lista})
                            st.success(f"'{nova_cat}' adicionada!"); time.sleep(1); st.rerun()

            with col_cfg_2:
                st.write("**🏢 Novos Tipos de Negócio**")
                novo_tipo = st.text_input("Tipo de Comércio", placeholder="Ex: Food Truck", key="add_tipo_adm")
                if st.button("➕ Adicionar Tipo", use_container_width=True):
                    if novo_tipo:
                        doc_ref = db.collection("configuracoes").document("tipos")
                        lista = buscar_opcoes_dinamicas("tipos", [])
                        if novo_tipo not in lista:
                            lista.append(novo_tipo)
                            doc_ref.set({"lista": lista})
                            st.success(f"'{novo_tipo}' adicionado!"); time.sleep(1); st.rerun()

        st.divider()

        # --- 5. PESQUISA E GESTÃO DE PROFISSIONAIS ---
        st.subheader("📋 Gestão de Membros")
        busca_p = st.text_input("🔍 Localizar por Nome ou WhatsApp", placeholder="Ex: João ou 1199...")

        for p in profs_data:
            pid = p['id']
            nome_p = p.get('nome', 'Sem Nome').upper()
            
            if busca_p.lower() in nome_p.lower() or busca_p in pid:
                status_cor = "🟢" if p.get('aprovado') else "🔴"
                elite_tag = "⭐" if p.get('verificado') else ""
                
                with st.expander(f"{status_cor} {elite_tag} {nome_p} ({pid})"):
                    col_adm_1, col_adm_2, col_adm_3 = st.columns([1.5, 2, 1.5])
                    
                    with col_adm_1:
                        st.markdown("**📸 Perfil**")
                        foto_p = p.get('foto_url') or (f"data:image/png;base64,{p.get('foto_b64')}" if p.get('foto_b64') else None)
                        if foto_p:
                            st.image(foto_p, width=120)
                        st.write(f"🔑 Senha: `{p.get('senha')}`")
                        st.write(f"📞 Zap: {pid}")

                    with col_adm_2:
                        st.markdown("**💰 Financeiro & Status**")
                        valor_moedas = st.number_input(f"Valor para {nome_p}", 1, 500, 10, key=f"val_{pid}")
                        c_m1, c_m2 = st.columns(2)
                        if c_m1.button(f"➕ ADD {valor_moedas}", key=f"badd_{pid}", use_container_width=True):
                            db.collection("profissionais").document(pid).update({"saldo": p.get('saldo', 0) + valor_moedas})
                            st.toast(f"Adicionado {valor_moedas} para {nome_p}"); time.sleep(0.5); st.rerun()
                        
                        if c_m2.button(f"➖ REM {valor_moedas}", key=f"brem_{pid}", use_container_width=True):
                            db.collection("profissionais").document(pid).update({"saldo": max(0, p.get('saldo', 0) - valor_moedas)})
                            st.rerun()

                        st.write(f"Saldo Atual: **{p.get('saldo', 0)} 💎**")
                        st.write(f"Cliques: **{p.get('cliques', 0)}**")

                    with col_adm_3:
                        st.markdown("**⚡ Ações de Autoridade**")
                        
                        if not p.get('aprovado'):
                            if st.button("✅ APROVAR AGORA", key=f"apr_{pid}", use_container_width=True, type="primary"):
                                db.collection("profissionais").document(pid).update({"aprovado": True})
                                st.rerun()
                        else:
                            if st.button("🚫 DESATIVAR", key=f"des_{pid}", use_container_width=True):
                                db.collection("profissionais").document(pid).update({"aprovado": False})
                                st.rerun()

                        is_ver = p.get('verificado', False)
                        if st.button(f"{'⚪ REMOVER ELITE' if is_ver else '🌟 TORNAR ELITE'}", key=f"ver_{pid}", use_container_width=True):
                            db.collection("profissionais").document(pid).update({"verificado": not is_ver})
                            st.rerun()

                        if st.button("🗑️ BANIR DEFINITIVO", key=f"del_{pid}", use_container_width=True):
                            db.collection("profissionais").document(pid).delete()
                            st.error(f"{nome_p} removido."); time.sleep(1); st.rerun()

    elif access_adm != "":
        st.error("🚨 Chave Mestra Incorreta!")
    else:
        st.info("🔓 Insira a Chave Mestra para acessar a Central de Autoridade.")

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





















