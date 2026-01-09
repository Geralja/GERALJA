# ==============================================================================
# GERALJÁ | O ESQUELETO MESTRE (VERSÃO COMPLETA E BLINDADA)
# ==============================================================================
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime
import math
import re
import unicodedata
import pandas as pd
from streamlit_js_eval import get_geolocation

# ------------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DE PÁGINA E ESTILO
# ------------------------------------------------------------------------------
st.set_page_config(page_title="GeralJá | Soluções Rápidas", page_icon="🎯", layout="wide")

if 'tema_claro' not in st.session_state:
    st.session_state.tema_claro = False

def aplicar_estilo():
    hide_style = """
        <style>
            header[data-testid="stHeader"] { visibility: hidden !important; height: 0; }
            footer { visibility: hidden !important; }
            .block-container { padding-top: 2rem !important; }
            .stButton>button { border-radius: 10px; font-weight: bold; width: 100%; }
            .stTabs [data-baseweb="tab-list"] { gap: 10px; }
            .stTabs [data-baseweb="tab"] { 
                background-color: #f0f2f6; border-radius: 5px 5px 0 0; padding: 10px;
            }
        </style>
    """
    st.markdown(hide_style, unsafe_allow_html=True)
    if st.session_state.tema_claro:
        st.markdown("<style>.stApp { background-color: white !important; } * { color: #1E293B !important; }</style>", unsafe_allow_html=True)

aplicar_estilo()

# ------------------------------------------------------------------------------
# 2. FUNÇÕES DE INTELIGÊNCIA E GEOLOCALIZAÇÃO
# ------------------------------------------------------------------------------
def remover_acentos(texto):
    if not texto: return ""
    nfkd_form = unicodedata.normalize('NFKD', str(texto))
    return "".join([c for c in nfkd_form if not unicodedata.category(c) == 'Mn']).lower().strip()

def calcular_distancia(lat1, lon1, lat2, lon2):
    try:
        if None in [lat1, lon1, lat2, lon2]: return 0.0
        R = 6371.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi, dlambda = math.radians(lat2-lat1), math.radians(lon2-lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)
    except: return 0.0

def converter_img_b64(file):
    if file: return base64.b64encode(file.getvalue()).decode()
    return None

# ------------------------------------------------------------------------------
# 3. CONEXÃO FIREBASE E BANCO DE DADOS
# ------------------------------------------------------------------------------
@st.cache_resource
def conectar_banco():
    if not firebase_admin._apps:
        try:
            b64_key = st.secrets["FIREBASE_BASE64"]
            cred = credentials.Certificate(json.loads(base64.b64decode(b64_key).decode("utf-8")))
            return firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Erro Firebase: {e}"); st.stop()
    return firebase_admin.get_app()

db = firestore.client() if conectar_banco() else None

# ------------------------------------------------------------------------------
# 4. FUNÇÕES DE SUPORTE (IA, CARGA E RADAR)
# ------------------------------------------------------------------------------
def ia_busca_consciente_v2(termo_usuario):
    termo_limpo = remover_acentos(termo_usuario)
    try:
        doc = db.collection("configuracoes").document("dicionario_ia").get()
        if doc.exists:
            for k, v in doc.to_dict().items():
                if remover_acentos(k) in termo_limpo: return v
    except: pass
    return termo_usuario.title()

def carregar_ia_em_massa():
    conhecimento = {
        "vazamento": "Encanador", "fio": "Eletricista", "tijolo": "Pedreiro", "pintar": "Pintor",
        "iphone": "Técnico de Celular", "computador": "Informática", "limpeza": "Diarista",
        "jardim": "Jardineiro", "pizza": "Pizzaria", "fome": "Lanchonete", "remedio": "Drogaria / Farmácia"
    }
    db.collection("configuracoes").document("dicionario_ia").set(conhecimento)
    return True

# ------------------------------------------------------------------------------
# 5. INTERFACE PRINCIPAL (ABAS)
# ------------------------------------------------------------------------------
st.markdown("<h1 style='text-align: center; color: #0047AB;'>🎯 GERAL<span style='color: #FF8C00;'>JÁ</span></h1>", unsafe_allow_html=True)

tabs = st.tabs(["🔍 BUSCAR", "🚀 CADASTRAR", "👤 PERFIL", "👑 ADMIN", "⭐ FEEDBACK"])

# --- ABA BUSCAR ---
with tabs[0]:
    st.markdown("### ⚡ RADAR GERALJÁ (Ofertas)")
    try:
        agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ofertas = db.collection("ofertas_live").where("expira_em", ">", agora).stream()
        cols_o = st.columns(3)
        for i, o in enumerate(ofertas):
            d = o.to_dict()
            cols_o[i % 3].info(f"**{d['nome']}**:\n{d['mensagem']}")
    except: st.write("Nenhuma oferta agora.")
    
    loc = get_geolocation()
    lat_c, lon_c = (loc['coords']['latitude'], loc['coords']['longitude']) if loc else (None, None)
    
    busca = st.text_input("O que você precisa?", placeholder="Ex: cano quebrado")
    if busca:
        cat_alvo = ia_busca_consciente_v2(busca)
        profs = db.collection("profissionais").where("status", "==", "ativo").stream()
        res = []
        for p in profs:
            d = p.to_dict()
            if remover_acentos(cat_alvo) in remover_acentos(d.get('categoria','')) or remover_acentos(busca) in remover_acentos(d.get('nome','')):
                d['dist'] = calcular_distancia(lat_c, lon_c, d.get('latitude'), d.get('longitude'))
                d['id'] = p.id
                res.append(d)
        
        if res:
            df = pd.DataFrame(res).sort_values(by=['ranking_elite', 'dist'], ascending=[False, True])
            for _, prof in df.iterrows():
                c1, c2, c3 = st.columns([1, 2, 1])
                with c1: 
                    if prof.get('foto'): st.image(f"data:image/png;base64,{prof['foto']}", width=100)
                    else: st.title("👤")
                with c2:
                    st.markdown(f"**{prof['nome']}** ({prof.get('dist', 0)} km)")
                    st.caption(f"{prof.get('categoria')} | {prof.get('descricao')[:50]}...")
                with c3:
                    tel = re.sub(r'\D', '', str(prof.get('whatsapp', '')))
                    st.link_button("🟢 WHATSAPP", f"https://wa.me/55{tel}")
        else: st.warning("Nada encontrado.")

# --- ABA CADASTRAR ---
with tabs[1]:
    tipo = st.radio("Tipo:", ["Profissional Liberal", "Comércio / Loja"], horizontal=True)
    cats_p = sorted(["Eletricista", "Encanador", "Pedreiro", "Pintor", "Técnico de Celular", "Diarista"])
    cats_c = sorted(["Lanchonete", "Pizzaria", "Drogaria / Farmácia", "Mercado", "Padaria"])
    
    with st.form("cad"):
        nome = st.text_input("Nome*")
        zap = st.text_input("WhatsApp*")
        cat = st.selectbox("Categoria*", cats_p if "Profissional" in tipo else cats_c)
        desc = st.text_area("Descrição")
        foto = st.file_uploader("Foto")
        if st.form_submit_button("CADASTRAR"):
            if nome and zap and lat_c:
                db.collection("profissionais").add({
                    "nome": nome, "whatsapp": zap, "categoria": cat, "descricao": desc,
                    "foto": converter_img_b64(foto), "latitude": lat_c, "longitude": lon_c,
                    "status": "ativo", "saldo": 5.0, "ranking_elite": 0, "visualizacoes": 0
                })
                st.success("Cadastrado!")
            else: st.error("Falta nome, zap ou GPS!")

# --- ABA ADMIN ---
with tabs[3]:
    if st.text_input("Senha Master", type="password") == "mumias":
        if st.button("🚀 INICIALIZAR IA"):
            if carregar_ia_em_massa(): st.success("IA Pronta!")

# --- ABA FEEDBACK ---
with tabs[4]:
    msg_f = st.text_area("Sugestões")
    if st.button("ENVIAR") and msg_f:
        db.collection("feedbacks").add({"mensagem": msg_f, "data": datetime.datetime.now().isoformat()})
        st.success("Valeu!")
