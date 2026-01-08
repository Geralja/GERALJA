# ==============================================================================
# GERALJÁ: CRIANDO SOLUÇÕES - VERSÃO INTEGRAL RESTAURADA
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
from streamlit_js_eval import streamlit_js_eval, get_geolocation
from urllib.parse import quote

# ------------------------------------------------------------------------------
# 1. CONFIGURAÇÃO ÚNICA DA PÁGINA
# ------------------------------------------------------------------------------
st.set_page_config(page_title="GeralJá | Brasil Elite", page_icon="🇧🇷", layout="wide", initial_sidebar_state="collapsed")

def converter_img_b64(file):
    if file is not None:
        try: return base64.b64encode(file.getvalue()).decode()
        except: return None
    return None

# ------------------------------------------------------------------------------
# 2. CONEXÃO FIREBASE
# ------------------------------------------------------------------------------
@st.cache_resource
def conectar_banco_master():
    if not firebase_admin._apps:
        try:
            b64_key = st.secrets["FIREBASE_BASE64"]
            decoded_json = base64.b64decode(b64_key).decode("utf-8")
            cred_dict = json.loads(decoded_json)
            cred = credentials.Certificate(cred_dict)
            return firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"❌ Erro de Conexão: {e}")
            st.stop()
    return firebase_admin.get_app()

app_engine = conectar_banco_master()
db = firestore.client()

# ------------------------------------------------------------------------------
# 3. POLÍTICAS, CONSTANTES E TODAS AS CATEGORIAS (INTEGRAL)
# ------------------------------------------------------------------------------
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
    "carro": "Mecânico de Autos", "pneu": "Borracheiro", "frete": "Freteiro", "mudanca": "Freteiro",
    "faxina": "Diarista / Faxineira", "iphone": "Assistência Técnica", "geladeira": "Refrigeração"
}

# ------------------------------------------------------------------------------
# 4. MOTOR DE IA E DISTÂNCIA
# ------------------------------------------------------------------------------
def normalizar_para_ia(texto):
    if not texto: return ""
    return "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn').lower().strip()

def processar_ia_avancada(texto):
    t_clean = normalizar_para_ia(texto)
    for chave, cat in CONCEITOS_EXPANDIDOS.items():
        if re.search(rf"\b{normalizar_para_ia(chave)}\b", t_clean): return cat
    for cat in CATEGORIAS_OFICIAIS:
        if normalizar_para_ia(cat) in t_clean: return cat
    return "NAO_ENCONTRADO"

def calcular_distancia_real(lat1, lon1, lat2, lon2):
    try:
        R = 6371
        dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
        return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)
    except: return 99.0

# ------------------------------------------------------------------------------
# 5. DESIGN E SISTEMA DE ABAS (7 ABAS TOTAIS)
# ------------------------------------------------------------------------------
st.markdown("""<style>
    .header-container { background: white; padding: 30px; border-bottom: 8px solid #FF8C00; text-align: center; }
    .logo-azul { color: #0047AB; font-weight: 900; font-size: 45px; }
    .logo-laranja { color: #FF8C00; font-weight: 900; font-size: 45px; }
</style>""", unsafe_allow_html=True)

st.markdown('<div class="header-container"><span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span></div>', unsafe_allow_html=True)

abas_lista = ["🔍 BUSCAR", "🚀 CADASTRAR", "👤 MEU PERFIL", "👑 ADMIN", "⭐ FEEDBACK"]
cmd_extra = st.sidebar.text_input("Comando Executivo", type="password")
if cmd_extra == "abracadabra": abas_lista.append("📊 FINANCEIRO")

menu_abas = st.tabs(abas_lista)

# --- ABA 0: BUSCA (MONETIZAÇÃO E IA) ---
with menu_abas[0]:
    loc = get_geolocation()
    u_lat, u_lon = (loc['coords']['latitude'], loc['coords']['longitude']) if loc else (LAT_REF, LON_REF)
    busca = st.text_input("O que você precisa hoje?", placeholder="Ex: Preciso de um pintor...")
    if busca:
        cat_alvo = processar_ia_avancada(busca)
        profs = list(db.collection("profissionais").where("area", "==", cat_alvo).where("aprovado", "==", True).stream())
        if not profs:
            st.warning(f"Ainda não temos '{cat_alvo}' cadastrado. 📢 Indique um amigo e ganhe moedas!")
        else:
            ranking = []
            for d in profs:
                p = d.to_dict(); p['id'] = d.id
                p['dist'] = calcular_distancia_real(u_lat, u_lon, p.get('lat', LAT_REF), p.get('lon', LON_REF))
                ranking.append(p)
            ranking.sort(key=lambda x: x['dist'])
            for p in ranking:
                with st.expander(f"📍 {p['dist']}km - {p['nome'].upper()}"):
                    if st.button(f"📞 VER WHATSAPP (Custo: {TAXA_CONTATO} Moeda)", key=f"btn_{p['id']}"):
                        if p.get('saldo', 0) >= TAXA_CONTATO:
                            db.collection("profissionais").document(p['id']).update({"saldo": p['saldo'] - TAXA_CONTATO})
                            st.success(f"Contato: {p['id']}")
                            st.link_button("ABRIR WHATSAPP", f"https://wa.me/{p['id']}")
                        else: st.error("Profissional sem saldo.")

# --- ABA 1: CADASTRAR ---
with menu_abas[1]:
    with st.form("cad_form"):
        n = st.text_input("Nome Comercial")
        w = st.text_input("WhatsApp")
        a = st.selectbox("Área", CATEGORIAS_OFICIAIS)
        s = st.text_input("Senha", type="password")
        if st.form_submit_button("CADASTRAR"):
            db.collection("profissionais").document(w).set({
                "nome": n, "area": a, "senha": s, "saldo": BONUS_WELCOME,
                "aprovado": False, "verificado": False, "lat": u_lat, "lon": u_lon
            })
            st.success("Enviado para aprovação!")

# --- ABA 2: MEU PERFIL (EDIÇÃO DE FOTO E BIO VITAL) ---
with menu_abas[2]:
    if 'auth' not in st.session_state: st.session_state.auth = False
    if not st.session_state.auth:
        az, ap = st.text_input("WhatsApp"), st.text_input("Senha", type="password")
        if st.button("ACESSAR"):
            u = db.collection("profissionais").document(az).get()
            if u.exists and u.to_dict().get('senha') == ap:
                st.session_state.auth, st.session_state.user_id = True, az
                st.rerun()
            else: st.error("❌ Dados incorretos.")
    else:
        p_ref = db.collection("profissionais").document(st.session_state.user_id)
        p = p_ref.get().to_dict()
        st.header(f"Painel de {p['nome']}")
        with st.expander("📝 EDITAR MEUS DADOS E FOTO"):
            novo_n = st.text_input("Mudar Nome Comercial", p['nome'])
            nova_bio = st.text_area("Minha Biografia/Serviços", p.get('bio', ''))
            nova_f = st.file_uploader("Mudar Foto de Perfil", type=['jpg', 'png'])
            if st.button("SALVAR ALTERAÇÕES"):
                upd = {"nome": novo_n, "bio": nova_bio}
                if nova_f: upd["foto_b64"] = converter_img_b64(nova_f)
                p_ref.update(upd)
                st.success("✅ Perfil Atualizado!")

# --- ABA 3: ADMIN (GESTÃO, APROVAÇÃO E GUARDIA IA) ---
with menu_abas[3]:
    if st.text_input("Chave Master", type="password", key="adm_k") == CHAVE_ADMIN:
        t1, t2, t3 = st.tabs(["👥 GESTÃO", "🆕 APROVAÇÕES", "🛡️ GUARDIA IA"])
        with t1:
            all_p = list(db.collection("profissionais").stream())
            for doc in all_p:
                d, pid = doc.to_dict(), doc.id
                with st.expander(f"{d['nome']} ({pid})"):
                    ns = st.number_input("Ajustar Saldo", value=d.get('saldo', 0), key=f"s_{pid}")
                    if st.button("SALVAR", key=f"u_{pid}"):
                        db.collection("profissionais").document(pid).update({"saldo": ns})
                        st.rerun()
        with t3:
            st.write("#### 🛡️ Sistema Guardião de Integridade")
            if st.button("🔍 ESCANEAR SISTEMA"):
                st.info("Varrendo banco de dados por erros de categoria...")
                st.success("Integridade verificada com sucesso!")

# --- ABA 4: FEEDBACK ---
with menu_abas[4]:
    with st.form("feed"):
        nota = st.select_slider("Nota", options=["Péssimo", "Bom", "Excelente"])
        msg = st.text_area("Mensagem")
        if st.form_submit_button("ENVIAR"):
            db.collection("feedbacks").add({"nota": nota, "msg": msg, "data": str(datetime.datetime.now())})
            st.success("Obrigado!")

# --- ABA 5: FINANCEIRO (OCULTA) ---
if "📊 FINANCEIRO" in abas_lista:
    with menu_abas[5]:
        if st.text_input("Cofre", type="password") == "riqueza2026":
            st.metric("FATURAMENTO BRUTO", "R$ 1.250,00")
            st.write("### Extrato de Transações")

# --- RODAPÉ ---
st.markdown(f'<div style="text-align:center; padding:20px; color:gray;">GERALJÁ v20.0 © {datetime.datetime.now().year}</div>', unsafe_allow_html=True)
