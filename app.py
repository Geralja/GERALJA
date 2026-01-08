import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import base64
import json
import math
import re
import unicodedata
from datetime import datetime
import pytz
from streamlit_js_eval import streamlit_js_eval, get_geolocation

# ==============================================================================
# 1. CONFIGURAÇÃO VISUAL E CSS (DESIGN PROFISSIONAL)
# ==============================================================================
st.set_page_config(page_title="GeralJá - Conectando Você", page_icon="🎯", layout="centered")

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stApp { background-color: #f0f2f5; }
        .main-title { color: #1E3A8A; font-weight: 800; text-align: center; margin-top: -30px; }
        .prof-card {
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            border-left: 6px solid #1E3A8A;
            margin-bottom: 20px;
        }
        .btn-wpp {
            background-color: #25D366;
            color: white !important;
            padding: 10px 20px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: bold;
            display: inline-block;
        }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. FUNÇÕES DE APOIO (MATEMÁTICA, SEGURANÇA E TEXTO)
# ==============================================================================
def remover_acentos(texto):
    if not texto: return ""
    return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').lower()

def scan_virus_e_scripts(texto):
    return re.sub(r'<[^>]*?>|javascript:|alert\(', '', str(texto))

def calcular_distancia(lat1, lon1, lat2, lon2):
    R = 6371 
    dLat, dLon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dLat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2) ** 2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

# ==============================================================================
# 3. CONEXÃO FIREBASE
# ==============================================================================
@st.cache_resource
def conectar_banco_master():
    if not firebase_admin._apps:
        try:
            if "FIREBASE_BASE64" not in st.secrets:
                st.error("🔑 Configure a chave nos Secrets.")
                st.stop()
            b64_key = st.secrets["FIREBASE_BASE64"]
            decoded_json = base64.b64decode(b64_key).decode("utf-8")
            cred = credentials.Certificate(json.loads(decoded_json))
            return firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"❌ Erro: {e}")
            st.stop()
    return firebase_admin.get_app()

app_engine = conectar_banco_master()
db = firestore.client()

# ==============================================================================
# 4. CATEGORIAS E DICIONÁRIO
# ==============================================================================
CATEGORIAS_OFICIAIS = [
    "Academia", "Acompanhante de Idosos", "Açougue", "Adega", "Adestrador de Cães", "Advocacia", "Agropecuária", 
    "Ajudante Geral", "Animador de Festas", "Arquiteto(a)", "Armarinho/Aviamentos", "Assistência Técnica", 
    "Aulas Particulares", "Auto Elétrica", "Auto Peças", "Babá (Nanny)", "Banho e Tosa", "Barbearia/Salão", 
    "Barman / Bartender", "Bazar", "Borracheiro", "Cabeleireiro(a)", "Cafeteria", "Calçados", "Carreto", 
    "Celulares", "Chaveiro", "Churrascaria", "Clínica Médica", "Comida Japonesa", "Confeiteiro(a)", 
    "Contabilidade", "Costureira / Alfaiate", "Cozinheiro(a) Particular", "Cuidador de Idosos", 
    "Dançarino(a)", "Decorador(a) de Festas", "Destaque de Eventos", "Diarista / Faxineira", "Doceria", 
    "Eletrodomésticos", "Eletricista", "Eletrônicos", "Encanador", "Escola Infantil", "Estética Automotiva", 
    "Estética Facial", "Esteticista", "Farmácia", "Fisioterapia", "Fitness", "Floricultura", "Fotógrafo(a)", 
    "Freteiro", "Fretista / Mudanças", "Funilaria e Pintura", "Garçom e garçonete", "Gesseiro", "Guincho 24h", 
    "Hamburgueria", "Hortifruti", "Idiomas", "Imobiliária", "Informática", "Instalador de Ar-condicionado", 
    "Internet de fibra óptica", "Jardineiro", "Joalheria", "Lanchonete", "Lava Jato", "Lavagem de Sofás", 
    "Loja de Roupas", "Loja de Variedades", "Madeireira", "Manicure e Pedicure", "Maquiador(a)", "Marceneiro", 
    "Marido de Aluguel", "Material de Construção", "Mecânico de Autos", "Montador de Móveis", "Motoboy/Entregas", 
    "Motorista Particular", "Móveis", "Moto Peças", "Nutricionista", "Odontologia", "Ótica", "Padaria", 
    "Papelaria", "Passeador de Cães", "Pastelaria", "Pedreiro", "Pet Shop", "Pintor", "Piscineiro", "Pizzaria", 
    "Professor(a) Particular", "Psicologia", "Recepcionista de Eventos", "Reforço Escolar", "Refrigeração", 
    "Relojoaria", "Salgadeiro(a)", "Segurança / Vigilante", "Seguros", "Som e Alarme", "Sorveteria", 
    "Tatuagem/Piercing", "Técnico de Celular", "Técnico de Fogão", "Técnico de Geladeira", "Técnico de Lavadora", 
    "Técnico de Notebook/PC", "Telhadista", "TI (Tecnologia)", "Tintas", "Veterinário(a)", "Web Designer"
]

CONCEITOS_EXPANDIDOS = {
    "celular": "Técnico de Celular", "iphone": "Técnico de Celular", "fogao": "Técnico de Fogão",
    "geladeira": "Técnico de Geladeira", "lavadora": "Técnico de Lavadora", "notebook": "Técnico de Notebook/PC",
    "telhado": "Telhadista", "vazamento": "Encanador", "curto": "Eletricista", "fome": "Lanchonete"
}

# ==============================================================================
# 5. LOCALIZAÇÃO E ABAS (CORREÇÃO NAMEERROR)
# ==============================================================================
st.markdown("<h1 class='main-title'>🎯 GeralJá</h1>", unsafe_allow_html=True)

loc = get_geolocation()
lat_usuario = loc['coords']['latitude'] if loc else -23.5505
lon_usuario = loc['coords']['longitude'] if loc else -46.6333

titulos_abas = ["🔍 BUSCAR", "🚀 CADASTRAR", "👤 PERFIL", "👑 ADMIN"]
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1063/1063376.png", width=80)
    cmd = st.text_input("Comando Secreto", type="password")
    aba_fin_ativa = False
    if cmd == "abracadabra":
        titulos_abas.append("📊 FINANCEIRO")
        aba_fin_ativa = True

objetos_abas = st.tabs(titulos_abas)
tab_busca, tab_cad, tab_perfil, tab_admin = objetos_abas[0], objetos_abas[1], objetos_abas[2], objetos_abas[3]

# ==============================================================================
# 6. CONTEÚDO DAS ABAS
# ==============================================================================

with tab_busca:
    st.write("### O que você precisa hoje?")
    c1, c2, c3, c4 = st.columns(4)
    atalho = ""
    if c1.button("📱 Celular"): atalho = "Técnico de Celular"
    if c2.button("🔧 Reparos"): atalho = "Marido de Aluguel"
    if c3.button("🏠 Obra"): atalho = "Pedreiro"
    if c4.button("🍔 Fome"): atalho = "Lanchonete"
    
    busca_in = st.text_input("Busque serviço ou categoria", value=atalho)
    if busca_in:
        termo = remover_acentos(busca_in)
        alvo = CONCEITOS_EXPANDIDOS.get(termo, busca_in)
        st.subheader(f"📍 Resultados para '{alvo}'")
        st.markdown(f'<div class="prof-card"><h4>João Exemplo</h4><p>📍 A 2km de você</p><a href="#" class="btn-wpp">WHATSAPP</a></div>', unsafe_allow_html=True)

with tab_cad:
    st.write("### 🚀 Cadastro")
    with st.form("f_reg"):
        n, c = st.text_input("Nome"), st.selectbox("Categoria", CATEGORIAS_OFICIAIS)
        w, b = st.text_input("WhatsApp"), st.text_area("Bio")
        if st.form_submit_button("CADASTRAR"):
            db.collection("profissionais").add({"nome": n, "categoria": c, "whatsapp": w, "bio": b, "lat": lat_usuario, "lon": lon_usuario, "status": "pendente", "data": datetime.now()})
            st.success("Enviado para aprovação!")

with tab_perfil:
    st.write("### 👤 Meu Perfil (Em breve)")

with tab_admin:
    st.write("### 👑 Admin")
    if st.text_input("Senha Admin", type="password") == "mumias":
        pends = db.collection("profissionais").where("status", "==", "pendente").stream()
        for p in pends:
            d = p.to_dict()
            with st.expander(f"Aprovar {d['nome']}"):
                if st.button("APROVAR", key=p.id):
                    db.collection("profissionais").document(p.id).update({"status": "ativo"})
                    st.rerun()

if aba_fin_ativa:
    with objetos_abas[4]:
        st.write("### 📊 Financeiro")
        st.metric("Saldo do Sistema", "R$ 1.250,00")

st.markdown("---")
st.caption("© 2026 GeralJá")
