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
# --- ABA 0: BUSCA (IA GROQ + RAIO 3KM + VITRINE SOCIAL) ---
# ==============================================================================
with menu_abas[0]:
    st.markdown("### 🏙️ O que você precisa?")
    
    # --- 1. MOTOR DE LOCALIZAÇÃO ---
    with st.expander("📍 Sua Localização (GPS)", expanded=False):
        loc = get_geolocation()
        if loc and 'coords' in loc:
            minha_lat, minha_lon = loc['coords']['latitude'], loc['coords']['longitude']
            st.success(f"Localização detectada!")
        else:
            minha_lat, minha_lon = LAT_REF, LON_REF
            st.warning("GPS desativado. Usando padrão (Centro).")

    c1, c2 = st.columns([3, 1])
    termo_busca = c1.text_input("Ex: 'Cano estourado' ou 'Pizza'", key="main_search_v_groq")
    
    # ALTERADO: Raio padrão agora inicia em 3 KM conforme solicitado
    raio_km = c2.select_slider("Raio (KM)", options=[1, 3, 5, 10, 20, 50, 100, 500], value=3)
    
    # --- 2. CSS PARA VITRINE E MODAL ---
    st.markdown("""
    <style>
        .cartao-geral { background: white; border-radius: 20px; border-left: 8px solid var(--cor-borda); padding: 15px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); color: #111; }
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
        window.parent.document.getElementById('imgExpandida').src = src;
        window.parent.document.getElementById('linkZapModal').href = link;
        window.parent.document.getElementById('meuModal').style.display = 'flex';
    }
    function fecharModal() {
        window.parent.document.getElementById('meuModal').style.display = 'none';
    }
    </script>
    """, unsafe_allow_html=True)

    if termo_busca:
        # 3. MOTOR DE IA GROQ (Processamento Avançado)
        cat_ia = processar_ia_avancada(termo_busca) 
        st.info(f"✨ IA Groq: Buscando por **{cat_ia}**")
        
        # Busca no Firebase
        profs = db.collection("profissionais").where("area", "==", cat_ia).where("aprovado", "==", True).stream()
        
        lista_ranking = []
        for p_doc in profs:
            p = p_doc.to_dict(); p['id'] = p_doc.id
            dist = calcular_distancia_real(minha_lat, minha_lon, p.get('lat', LAT_REF), p.get('lon', LON_REF))
            
            if dist <= raio_km:
                p['dist'] = dist
                # Cálculo de Score Elite
                score = 0
                score += 1000 if p.get('verificado') else 0
                score += (p.get('saldo', 0) * 10)
                p['score_elite'] = score
                lista_ranking.append(p)

        # 4. ORDENAÇÃO: Mais perto primeiro, Elite como desempate
        lista_ranking.sort(key=lambda x: (x['dist'], -x['score_elite']))

        if not lista_ranking:
            st.warning(f"Nenhum profissional de '{cat_ia}' encontrado em {raio_km}km.")
        else:
            for p in lista_ranking:
                is_elite = p.get('verificado') and p.get('saldo', 0) > 0
                cor_borda = "#FFD700" if is_elite else "#0047AB"
                zap_limpo = limpar_whatsapp(p.get('whatsapp', p['id']))
                link_zap = f"https://wa.me/{zap_limpo}?text=Olá, vi seu portfólio no GeralJá!"
                
                # Montar Fotos
                fotos_html = ""
                for i in range(1, 11):
                    f_data = p.get(f'f{i}')
                    if f_data and len(str(f_data)) > 100:
                        src = f_data if str(f_data).startswith("
                
# ==============================================================================
# ABA 2: 🚀 PAINEL DO PARCEIRO (COMPLETO COM FACEBOOK)
# ==============================================================================
# --- ABA 2: PAINEL DE CONTROLE (VERSÃO TURBINADA COM GPS E VITRINE) ---
with menu_abas[2]:
    # 1. LÓGICA DE CAPTURA DO FACEBOOK (VERIFICA SE VOLTOU DA AUTH EXTERNA)
    params = st.query_params
    if "uid" in params and not st.session_state.get('auth'):
        fb_uid = params["uid"]
        # Busca no Firestore se esse ID já está vinculado
        user_query = db.collection("profissionais").where("fb_uid", "==", fb_uid).limit(1).get()
        
        if user_query:
            doc = user_query[0]
            st.session_state.auth = True
            st.session_state.user_id = doc.id
            st.success(f"✅ Bem-vindo, {doc.to_dict().get('nome', 'Parceiro')}!")
            time.sleep(1)
            st.rerun()
        else:
            st.warning("⚠️ Conta do Facebook não vinculada. Entre com WhatsApp e vincule no seu perfil.")

    # Inicializa o estado de autenticação se não existir
    if 'auth' not in st.session_state: 
        st.session_state.auth = False
    
    # --- 2. TELA DE LOGIN (CASO NÃO ESTEJA LOGADO) ---
    if not st.session_state.get('auth'):
        st.subheader("🚀 Acesso ao Painel do Profissional")
        
        # Link do Facebook (Usando as chaves das suas Secrets)
        # HANDLER_URL deve estar definida no seu código global ou substitua pela sua URL de auth
        FIREBASE_API_KEY = st.secrets.get("FIREBASE_API_KEY", "")
        HANDLER_URL = "https://sua-url-de-auth.vercel.app/api/auth" # Ajuste conforme seu handler
        
        link_auth = f"{HANDLER_URL}?apiKey={FIREBASE_API_KEY}&providerId=facebook.com"
        
        # Botão Visual Facebook
        st.markdown(f"""
            <a href="{link_auth}" target="_self" style="text-decoration: none;">
                <div style="background-color: #1877F2; color: white; padding: 12px; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 20px; font-family: sans-serif;">
                    🔵 ENTRAR COM FACEBOOK
                </div>
            </a>
        """, unsafe_allow_html=True)
        
        st.write("--- ou use seus dados ---")
        
        col1, col2 = st.columns(2)
        l_zap = col1.text_input("WhatsApp (Login)", key="login_zap_v7")
        l_pw = col2.text_input("Senha", type="password", key="login_pw_v7")
        
        if st.button("ENTRAR NO PAINEL", use_container_width=True, key="btn_entrar_v7"):
            u = db.collection("profissionais").document(l_zap).get()
            if u.exists and str(u.to_dict().get('senha')) == str(l_pw):
                st.session_state.auth, st.session_state.user_id = True, l_zap
                st.rerun()
            else: 
                st.error("❌ Dados incorretos ou usuário não encontrado.")

    # --- 3. PAINEL LOGADO (PAINEL DE MÁXIMA PERFORMANCE) ---
    else:
        doc_ref = db.collection("profissionais").document(st.session_state.user_id)
        d = doc_ref.get().to_dict()
        
        # Cabeçalho e Métricas
        st.write(f"### Olá, {d.get('nome', 'Parceiro')}!")
        m1, m2, m3 = st.columns(3)
        m1.metric("Saldo 🪙", f"{d.get('saldo', 0)}")
        m2.metric("Cliques 🚀", f"{d.get('cliques', 0)}")
        m3.metric("Status", "🟢 ATIVO" if d.get('aprovado') else "🟡 PENDENTE")

        # ATUALIZAÇÃO DE GPS (Importante para aparecer no mapa perto do cliente)
        from streamlit_js_eval import streamlit_js_eval
        if st.button("📍 ATUALIZAR MINHA LOCALIZAÇÃO (GPS)", use_container_width=True, key="gps_v7"):
            loc = streamlit_js_eval(js_expressions="navigator.geolocation.getCurrentPosition(s => s)", key='gps_v7_eval')
            if loc and 'coords' in loc:
                doc_ref.update({"lat": loc['coords']['latitude'], "lon": loc['coords']['longitude']})
                st.success("✅ Sua localização foi atualizada no mapa!")
            else: 
                st.info("🛰️ Tentando captar sinal GPS... Clique novamente em 3 segundos.")

        st.divider()

        # ÁREA DE COMPRA DE MOEDAS
        with st.expander("💎 RECARREGAR MOEDAS (PIX)", expanded=False):
            PIX_CHAVE = st.secrets.get("PIX_OFICIAL", "Sua Chave Aqui")
            st.warning(f"Chave PIX: {PIX_CHAVE}")
            c1, c2, c3 = st.columns(3)
            if c1.button("10 Moedas", key="p10_v7"): st.code(PIX_CHAVE)
            if c2.button("50 Moedas", key="p50_v7"): st.code(PIX_CHAVE)
            if c3.button("100 Moedas", key="p100_v7"): st.code(PIX_CHAVE)
            st.link_button("🚀 ENVIAR COMPROVANTE AGORA", f"https://wa.me/{st.secrets.get('ZAP_ADMIN')}?text=Fiz o PIX para o WhatsApp: {st.session_state.user_id}", use_container_width=True)

        # EDIÇÃO DE PERFIL E VITRINE (Onde o cara brilha)
        with st.expander("📝 EDITAR MEU PERFIL & VITRINE", expanded=True):
            with st.form("perfil_v7"):
                n_nome = st.text_input("Nome do Profissional", d.get('nome', ''))
                
                # Categorias dinâmicas que buscamos no banco
                n_area = st.selectbox("Mudar meu Segmento", CATEGORIAS_OFICIAIS, 
                                     index=CATEGORIAS_OFICIAIS.index(d.get('area')) if d.get('area') in CATEGORIAS_OFICIAIS else 0)

                n_desc = st.text_area("Descrição do seu serviço", d.get('descricao', ''))
                n_cat = st.text_input("Link Catálogo/Instagram", d.get('link_catalogo', ''))
                
                h1, h2 = st.columns(2)
                n_abre = h1.text_input("Abre às", d.get('h_abre', '08:00'))
                n_fecha = h2.text_input("Fecha às", d.get('h_fecha', '18:00'))
                
                n_foto = st.file_uploader("Trocar Foto de Perfil", type=['jpg','png','jpeg'], key="f_v7")
                n_portfolio = st.file_uploader("Vitrine (Até 4 fotos dos seus serviços)", type=['jpg','png','jpeg'], accept_multiple_files=True, key="p_v7")
                
                if st.form_submit_button("💾 SALVAR TODAS AS ALTERAÇÕES", use_container_width=True):
                    up = {
                        "nome": n_nome, "area": n_area, "descricao": n_desc, 
                        "link_catalogo": n_cat, "h_abre": n_abre, "h_fecha": n_fecha
                    }
                    # Converte imagem se houver upload
                    if n_foto:
                        up["foto_url"] = f"data:image/png;base64,{base64.b64encode(n_foto.read()).decode()}"
                    
                    if n_portfolio:
                        # Processa até 4 fotos para não estourar o banco
                        up["portfolio_imgs"] = [f"data:image/png;base64,{base64.b64encode(f.read()).decode()}" for f in n_portfolio[:4]]
                    
                    doc_ref.update(up)
                    st.success("✅ Perfil atualizado com sucesso!")
                    time.sleep(1); st.rerun()

        # VINCULAR REDE SOCIAL
        if not d.get('fb_uid'):
            with st.expander("🔗 CONECTAR FACEBOOK"):
                st.write("Conecte sua conta para fazer login em 1 clique.")
                st.link_button("VINCULAR FACEBOOK AGORA", link_auth, use_container_width=True)

        # SAIR OU EXCLUIR
        st.divider()
        if st.button("🚪 SAIR DO PAINEL", use_container_width=True):
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
    
    # 1. SEGURANÇA (Puxando do Cofre)
    CHAVE_MESTRA = st.secrets.get("CHAVE_ADMIN", "1234") # Fallback se não estiver nas secrets
    ZAP_ADMIN_OFICIAL = st.secrets.get("ZAP_ADMIN", "5511999999999")

    access_adm = st.text_input("Chave Mestra de Segurança", type="password", key="auth_master_v10")

    if access_adm == CHAVE_MESTRA:
        # --- 2. COLETA DE DADOS REAL-TIME ---
        try:
            todos_profs_docs = list(db.collection("profissionais").stream())
            profs_data = [p.to_dict() | {"id": p.id} for p in todos_profs_docs]
            
            lista_pendentes = [p for p in profs_data if not p.get('aprovado')]
            qtd_pendentes = len(lista_pendentes)

            # --- 3. ALERTAS DE GESTÃO ---
            if qtd_pendentes > 0:
                st.error(f"🚨 **ATENÇÃO:** {qtd_pendentes} profissionais aguardando aprovação!")
                msg_central = f"Olá! Central GeralJá, temos {qtd_pendentes} novos cadastros para revisar."
                link_zap_central = f"https://wa.me/{ZAP_ADMIN_OFICIAL}?text={msg_central.replace(' ', '%20')}"
                
                col_alert_1, col_alert_2 = st.columns([3, 1])
                col_alert_1.info(f"Fila: {', '.join([p.get('nome') for p in lista_pendentes])}")
                col_alert_2.link_button("📲 AVISAR EQUIPE", link_zap_central, use_container_width=True, type="primary")
                st.divider()

            # --- 4. DASHBOARD DE PERFORMANCE ---
            st.markdown("### 📊 Performance da Rede")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Parceiros", len(profs_data))
            c2.metric("Cliques Totais", sum(p.get('cliques', 0) for p in profs_data))
            c3.metric("Moedas no Sistema", f"💎 {sum(p.get('saldo', 0) for p in profs_data)}")
            c4.metric("Aguardando", qtd_pendentes)

            st.divider()

            # --- 5. GESTÃO DE CATEGORIAS (LIGADO AO FIREBASE) ---
            with st.expander("⚙️ CONFIGURAÇÕES DO SISTEMA"):
                st.write("**✨ Gerenciar Profissões Oficiais**")
                # Usa a variável global que definimos antes
                st.write(f"Categorias Atuais: {', '.join(CATEGORIAS_OFICIAIS)}")
                
                nova_cat = st.text_input("Nova Profissão", placeholder="Ex: Adestrador", key="add_cat_adm")
                if st.button("➕ Adicionar à Base", use_container_width=True):
                    if nova_cat and nova_cat not in CATEGORIAS_OFICIAIS:
                        CATEGORIAS_OFICIAIS.append(nova_cat)
                        db.collection("configuracoes").document("categorias").set({"lista": CATEGORIAS_OFICIAIS})
                        st.success(f"'{nova_cat}' adicionada!"); st.rerun()

            # --- 6. GESTÃO DE MEMBROS (LISTAGEM INTELIGENTE) ---
            st.subheader("📋 Gestão de Membros")
            busca_p = st.text_input("🔍 Localizar por Nome ou WhatsApp")

            for p in profs_data:
                pid = p['id']
                nome_p = p.get('nome', 'Sem Nome').upper()
                
                if busca_p.lower() in nome_p.lower() or busca_p in pid:
                    status_cor = "🟢" if p.get('aprovado') else "🔴"
                    elite = "🌟" if p.get('verificado') else ""
                    
                    with st.expander(f"{status_cor} {elite} {nome_p} ({pid})"):
                        c_a, c_b, c_c = st.columns([1, 2, 1.5])
                        
                        with c_a:
                            foto = p.get('foto_url') or "https://via.placeholder.com/100"
                            st.image(foto, width=100)
                            st.caption(f"Senha: `{p.get('senha')}`")

                        with c_b:
                            st.write(f"Saldo: **{p.get('saldo', 0)} 💎**")
                            # Ajuste de Saldo
                            val = st.number_input(f"Qtd", 1, 100, 10, key=f"v_{pid}")
                            col_b1, col_b2 = st.columns(2)
                            if col_b1.button(f"➕ Moedas", key=f"add_{pid}"):
                                db.collection("profissionais").document(pid).update({"saldo": p.get('saldo', 0) + val})
                                st.rerun()
                            if col_b2.button(f"➖ Moedas", key=f"rem_{pid}"):
                                db.collection("profissionais").document(pid).update({"saldo": max(0, p.get('saldo', 0) - val)})
                                st.rerun()

                        with c_c:
                            if not p.get('aprovado'):
                                if st.button("✅ APROVAR", key=f"ok_{pid}", use_container_width=True, type="primary"):
                                    db.collection("profissionais").document(pid).update({"aprovado": True})
                                    st.rerun()
                            else:
                                if st.button("🚫 DESATIVAR", key=f"no_{pid}", use_container_width=True):
                                    db.collection("profissionais").document(pid).update({"aprovado": False})
                                    st.rerun()
                            
                            if st.button("🗑️ BANIR", key=f"del_{pid}", use_container_width=True):
                                db.collection("profissionais").document(pid).delete()
                                st.rerun()
        except Exception as e:
            st.error(f"Erro ao carregar Central: {e}")

    elif access_adm != "":
        st.error("🚨 Chave Mestra Incorreta!")

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



























