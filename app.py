# ==============================================================================
# GERALJÁ: CRIANDO SOLUÇÕES - VERSÃO INTEGRADA E CORRIGIDA
# ==============================================================================
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime
import math
import re
import time
import pandas as pd
import unicodedata
import pytz
from streamlit_js_eval import streamlit_js_eval, get_geolocation
from urllib.parse import quote

# 1. CONFIGURAÇÃO ÚNICA DA PÁGINA (Deve ser a primeira linha de comando Streamlit)
st.set_page_config(
    page_title="GeralJá | Criando Soluções",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- FUNÇÕES DE UTILITÁRIOS ---
def converter_img_b64(file):
    if file is None: return ""
    try:
        # Se for um BytesIO (upload)
        if hasattr(file, 'getvalue'):
            return base64.b64encode(file.getvalue()).decode()
        # Se já for lido
        return base64.b64encode(file.read()).decode()
    except: return ""

# 2. CAMADA DE PERSISTÊNCIA (FIREBASE)
@st.cache_resource
def conectar_banco_master():
    if not firebase_admin._apps:
        try:
            if "FIREBASE_BASE64" not in st.secrets:
                st.error("🔑 Chave de segurança FIREBASE_BASE64 não encontrada.")
                st.stop()
            b64_key = st.secrets["FIREBASE_BASE64"]
            decoded_json = base64.b64decode(b64_key).decode("utf-8")
            cred_dict = json.loads(decoded_json)
            cred = credentials.Certificate(cred_dict)
            return firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"❌ FALHA NA INFRAESTRUTURA: {e}")
            st.stop()
    return firebase_admin.get_app()

app_engine = conectar_banco_master()
db = firestore.client()

# 3. POLÍTICAS E CONSTANTES
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ADMIN = "mumias"
TAXA_CONTATO = 1
BONUS_WELCOME = 5
LAT_REF, LON_REF = -23.5505, -46.6333

CATEGORIAS_OFICIAIS = sorted([
    "Academia", "Acompanhante de Idosos", "Açougue", "Adega", "Adestrador de Cães", "Advocacia", "Agropecuária", 
    "Ajudante Geral", "Animador de Festas", "Arquiteto(a)", "Armarinho/Aviamentos", "Assistência Técnica", 
    "Aulas Particulares", "Auto Elétrica", "Auto Peças", "Babá (Nanny)", "Banho e Tosa", "Barbearia/Salão", 
    "Barman / Bartender", "Bazar", "Borracheiro", "Cabeleireiro(a)", "Cafeteria", "Calçados", "Carreto", 
    "Celulares", "Chaveiro", "Churrascaria", "Clínica Médica", "Comida Japonesa", "Confeiteiro(a)", 
    "Contabilidade", "Costureira / Alfaiate", "Cozinheiro(a) Particular", "Cuidador de Idosos", 
    "Dançarino(a) / Entretenimento", "Decorador(a) de Festas", "Destaque de Eventos", 
    "Diarista / Faxineira", "Doceria", "Eletrodomésticos", "Eletricista", "Eletrônicos", "Encanador", 
    "Escola Infantil", "Estética Automotiva", "Estética Facial", "Esteticista", "Farmácia", "Fisioterapia", 
    "Fitness", "Floricultura", "Fotógrafo(a)", "Freteiro", "Fretista / Mudanças", "Funilaria e Pintura", 
    "Garçom e garçonete", "Gesseiro", "Guincho 24h", "Hamburgueria", "Hortifruti", "Idiomas", "Imobiliária", 
    "Informática", "Instalador de Ar-condicionado", "Internet de fibra óptica", "Jardineiro", "Joalheria", 
    "Lanchonete", "Lava Jato", "Lavagem de Sofás / Estofados", "Loja de Roupas", "Loja de Variedades", 
    "Madeireira", "Manicure e Pedicure", "Maquiador(a)", "Marceneiro", "Marido de Aluguel", "Material de Construção", 
    "Mecânico de Autos", "Montador de Móveis", "Motoboy/Entregas", "Motorista Particular", "Móveis", 
    "Moto Peças", "Nutricionista", "Odontologia", "Ótica", "Padaria", "Papelaria", 
    "Passeador de Cães (Dog Walker)", "Pastelaria", "Pedreiro", "Pet Shop", "Pintor", "Piscineiro", "Pizzaria", 
    "Professor(a) Particular", "Psicologia", "Recepcionista de Eventos", "Reforço Escolar", "Refrigeração", 
    "Relojoaria", "Salgadeiro(a)", "Segurança / Vigilante", "Seguros", "Som e Alarme", "Sorveteria", 
    "Tatuagem/Piercing", "Técnico de Celular", "Técnico de Fogão", "Técnico de Geladeira", "Técnico de Lavadora", 
    "Técnico de Notebook/PC", "Telhadista", "TI (Tecnologia)", "Tintas", "Veterinário(a)", "Web Designer"
])

CONCEITOS_EXPANDIDOS = {
    "pizza": "Pizzaria", "fome": "Pizzaria", "vazamento": "Encanador", "curto": "Eletricista",
    "carro": "Mecânico", "pneu": "Borracheiro", "frete": "Freteiro", "mudanca": "Freteiro",
    "faxina": "Diarista / Faxineira", "iphone": "Assistência Técnica", "geladeira": "Refrigeração",
    "pao": "Padaria", "lanche": "Lanchonete", "barba": "Barbearia/Salão", "unha": "Manicure e Pedicure"
    # ... adicione mais conforme necessário
}

# --- MOTORES DE IA E SEGURANÇA ---
def normalizar_para_ia(texto):
    if not texto: return ""
    return "".join(c for c in unicodedata.normalize('NFD', str(texto)) 
                  if unicodedata.category(c) != 'Mn').lower().strip()

def processar_ia_avancada(texto):
    if not texto: return "Vazio"
    t_clean = normalizar_para_ia(texto)
    for chave, categoria in CONCEITOS_EXPANDIDOS.items():
        if re.search(rf"\b{normalizar_para_ia(chave)}\b", t_clean): return categoria
    for cat in CATEGORIAS_OFICIAIS:
        if normalizar_para_ia(cat) in t_clean: return cat
    return "NAO_ENCONTRADO"

def calcular_distancia_real(lat1, lon1, lat2, lon2):
    try:
        if None in [lat1, lon1, lat2, lon2]: return 999.0
        R = 6371 
        dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)
    except: return 999.0

def guardia_escanear_e_corrigir():
    status_log = []
    profs = db.collection("profissionais").stream()
    for p_doc in profs:
        d = p_doc.to_dict()
        correcoes = {}
        if not d.get('area') or d.get('area') not in CATEGORIAS_OFICIAIS: correcoes['area'] = "Ajudante Geral"
        if d.get('saldo') is None: correcoes['saldo'] = 0
        if correcoes:
            db.collection("profissionais").document(p_doc.id).update(correcoes)
            status_log.append(f"✅ Corrigido: {p_doc.id}")
    return status_log if status_log else ["SISTEMA ÍNTEGRO"]

def scan_virus_e_scripts():
    profs = db.collection("profissionais").stream()
    perigo = [r"<script>", r"javascript:", r"DROP TABLE"]
    alertas = []
    for p_doc in profs:
        conteudo = str(p_doc.to_dict())
        for p in perigo:
            if re.search(p, conteudo, re.IGNORECASE): alertas.append(f"⚠️ Alerta no ID {p_doc.id}")
    return alertas if alertas else ["LIMPO"]

# --- DESIGN SYSTEM ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: white; }
    .header-container { background: white; padding: 30px; border-bottom: 8px solid #FF8C00; text-align: center; margin-bottom: 20px;}
    .logo-azul { color: #0047AB; font-weight: 900; font-size: 45px; }
    .logo-laranja { color: #FF8C00; font-weight: 900; font-size: 45px; }
    #MainMenu, footer, header { visibility: hidden; display: none!important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-container"><span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span><br><small>BRASIL ELITE</small></div>', unsafe_allow_html=True)

# --- ABAS ---
lista_abas = ["🔍 BUSCAR", "🚀 CADASTRAR", "👤 MEU PERFIL", "👑 ADMIN", "⭐ FEEDBACK"]
comando = st.sidebar.text_input("Comando Secreto", type="password")
if comando == "abracadabra": lista_abas.append("📊 FINANCEIRO")

menu_abas = st.tabs(lista_abas)

# ABA 0: BUSCA
with menu_abas[0]:
    loc = get_geolocation()
    u_lat = loc['coords']['latitude'] if loc else LAT_REF
    u_lon = loc['coords']['longitude'] if loc else LON_REF
    
    c1, c2 = st.columns([3, 1])
    termo = c1.text_input("O que você precisa hoje?", key="search_main")
    raio = c2.select_slider("Raio (KM)", options=[1, 5, 10, 50, 100, 1000], value=10)
    
    if termo:
        cat_alvo = processar_ia_avancada(termo)
        profs = db.collection("profissionais").where("area", "==", cat_alvo).where("aprovado", "==", True).stream()
        ranking = []
        for d in profs:
            p = d.to_dict(); p['id'] = d.id
            p['dist'] = calcular_distancia_real(u_lat, u_lon, p.get('lat', LAT_REF), p.get('lon', LON_REF))
            if p['dist'] <= raio:
                score = (p.get('saldo', 0) * 10) + (500 if p.get('verificado') else 0)
                p['score'] = score
                ranking.append(p)
        
        ranking.sort(key=lambda x: (-x['score'], x['dist']))
        for p in ranking:
            with st.container():
                st.markdown(f"### {p['nome'].upper()} (📍 {p['dist']}km)")
                st.link_button(f"💬 FALAR COM {p['nome'].split()[0].upper()}", f"https://wa.me/{p['id']}")

# ABA 1: CADASTRAR
with menu_abas[1]:
    st.subheader("🚀 Novo Cadastro")
    with st.form("cad_form"):
        n = st.text_input("Nome")
        w = st.text_input("WhatsApp (com DDD)")
        a = st.selectbox("Área", CATEGORIAS_OFICIAIS)
        s = st.text_input("Senha", type="password")
        if st.form_submit_button("CADASTRAR"):
            db.collection("profissionais").document(w).set({
                "nome": n, "area": a, "senha": s, "saldo": BONUS_WELCOME,
                "aprovado": True, "verificado": False, "lat": u_lat, "lon": u_lon, "cliques": 0
            })
            st.success("Cadastrado! Faça login no 'Meu Perfil'.")

# ABA 2: MEU PERFIL
with menu_abas[2]:
    if 'auth' not in st.session_state: st.session_state.auth = False
    if not st.session_state.auth:
        l_zap = st.text_input("WhatsApp", key="log_z")
        l_pw = st.text_input("Senha", type="password", key="log_p")
        if st.button("ENTRAR"):
            u = db.collection("profissionais").document(l_zap).get()
            if u.exists and u.to_dict().get('senha') == l_pw:
                st.session_state.auth, st.session_state.user_id = True, l_zap
                st.rerun()
    else:
        d = db.collection("profissionais").document(st.session_state.user_id).get().to_dict()
        st.write(f"### Olá, {d.get('nome')}!")
        st.metric("Saldo 🪙", d.get('saldo', 0))
        if st.button("SAIR"): 
            st.session_state.auth = False
            st.rerun()

# ABA 3: ADMIN
with menu_abas[3]:
    st.subheader("🔒 Administração")
    if st.text_input("Senha Master", type="password") == CHAVE_ADMIN:
        all_p = list(db.collection("profissionais").stream())
        st.metric("Total Parceiros", len(all_p))
        if st.button("Escaneamento de Segurança"):
            st.write(scan_virus_e_scripts())

# ABA 4: FEEDBACK
with menu_abas[4]:
    with st.form("feed_f"):
        nota = st.select_slider("Nota", options=["Péssimo", "Bom", "Excelente"])
        msg = st.text_area("Mensagem")
        if st.form_submit_button("ENVIAR"):
            db.collection("feedbacks").add({"data": str(datetime.datetime.now()), "nota": nota, "mensagem": msg})
            st.success("Obrigado!")

# ABA 5 (DINÂMICA): FINANCEIRO
if len(menu_abas) > 5:
    with menu_abas[5]:
        if st.text_input("Cofre", type="password") == "riqueza2025":
            st.write("### Painel Financeiro")
            # Lógica financeira aqui

# RODAPÉ
st.markdown(f'<div style="text-align:center; padding:20px; color:gray; font-size:10px;">GERALJÁ © {datetime.datetime.now().year}</div>', unsafe_allow_html=True)

