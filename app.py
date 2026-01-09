# ==============================================================================
# GERALJÁ: CRIANDO SOLUÇÕES - VERSÃO COMPLETA E INTEGRADA (SEM REMOÇÕES)
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

# 1. CONFIGURAÇÃO ÚNICA DA PÁGINA
st.set_page_config(page_title="GeralJá | Brasil Elite", page_icon="🇧🇷", layout="wide", initial_sidebar_state="collapsed")

# --- FUNÇÕES CORE ---
def converter_img_b64(file):
    if file is not None:
        try:
            return base64.b64encode(file.getvalue()).decode()
        except: return None
    return None

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
            st.error(f"❌ Erro Infra: {e}")
            st.stop()
    return firebase_admin.get_app()

app_engine = conectar_banco_master()
db = firestore.client()

# --- CONSTANTES E POLÍTICAS ---
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ADMIN = "mumias"
TAXA_CONTATO = 1
BONUS_WELCOME = 5
LAT_REF, LON_REF = -23.5505, -46.6333

CATEGORIAS_OFICIAIS = sorted([
    "Academia", "Ajudante Geral", "Assistência Técnica", "Barbearia/Salão", "Chaveiro", 
    "Diarista / Faxineira", "Eletricista", "Encanador", "Estética Automotiva", "Freteiro", 
    "Mecânico de Autos", "Montador de Móveis", "Padaria", "Pet Shop", "Pintor", "Pizzaria", 
    "TI (Tecnologia)", "Web Designer"
])

CONCEITOS_EXPANDIDOS = {
    "pizza": "Pizzaria", "fome": "Pizzaria", "vazamento": "Encanador", "curto": "Eletricista",
    "carro": "Mecânico de Autos", "pneu": "Borracheiro", "frete": "Freteiro", "mudanca": "Freteiro",
    "faxina": "Diarista / Faxineira", "iphone": "Assistência Técnica", "geladeira": "Refrigeração"
}

# --- MOTORES DE IA E SEGURANÇA ---
def normalizar_para_ia(texto):
    if not texto: return ""
    return "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn').lower().strip()

def processar_ia_avancada(texto):
    t_clean = normalizar_para_ia(texto)
    for chave, categoria in CONCEITOS_EXPANDIDOS.items():
        if re.search(rf"\b{normalizar_para_ia(chave)}\b", t_clean): return categoria
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

def guardia_escanear_e_corrigir():
    profs = db.collection("profissionais").stream()
    logs = []
    for p_doc in profs:
        d = p_doc.to_dict()
        if not d.get('area') or d.get('area') not in CATEGORIAS_OFICIAIS:
            db.collection("profissionais").document(p_doc.id).update({"area": "Ajudante Geral"})
            logs.append(f"✅ Fixo: {p_doc.id}")
    return logs if logs else ["SISTEMA OK"]

# --- DESIGN ---
st.markdown("""
<style>
    .header-container { background: white; padding: 25px; border-bottom: 8px solid #FF8C00; text-align: center; }
    .logo-azul { color: #0047AB; font-weight: 900; font-size: 45px; }
    .logo-laranja { color: #FF8C00; font-weight: 900; font-size: 45px; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-container"><span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span><br><small>BRASIL ELITE</small></div>', unsafe_allow_html=True)

# --- SISTEMA DE ABAS DINÂMICO ---
abas_nomes = ["🔍 BUSCAR", "🚀 CADASTRAR", "👤 MEU PERFIL", "👑 ADMIN", "⭐ FEEDBACK"]
cmd_secreto = st.sidebar.text_input("Comando Executivo", type="password")
if cmd_secreto == "abracadabra": abas_nomes.append("📊 FINANCEIRO")

menu_abas = st.tabs(abas_nomes)

# ABA 0: BUSCA (COM MONETIZAÇÃO E INCENTIVO)
with menu_abas[0]:
    loc = get_geolocation()
    u_lat = loc['coords']['latitude'] if loc else LAT_REF
    u_lon = loc['coords']['longitude'] if loc else LON_REF
    
    c1, c2 = st.columns([3, 1])
    busca = c1.text_input("O que você procura?", placeholder="Ex: Encanador...")
    raio = c2.select_slider("Raio (KM)", options=[5, 10, 50, 100], value=10)
    
    if busca:
        cat_alvo = processar_ia_avancada(busca)
        profs = list(db.collection("profissionais").where("area", "==", cat_alvo).where("aprovado", "==", True).stream())
        
        if not profs:
            st.warning(f"Ops! Ainda não temos '{cat_alvo}' cadastrado aqui.")
            st.info("📢 **GANHE DINHEIRO:** Conhece um profissional desta área? Indique o GeralJá e ganhe bônus em moedas quando ele se cadastrar!")
        else:
            ranking = []
            for d in profs:
                p = d.to_dict(); p['id'] = d.id
                p['dist'] = calcular_distancia_real(u_lat, u_lon, p.get('lat', LAT_REF), p.get('lon', LON_REF))
                if p['dist'] <= raio:
                    p['score'] = (p.get('saldo', 0) * 10) + (500 if p.get('verificado') else 0)
                    ranking.append(p)
            
            ranking.sort(key=lambda x: (-x['score'], x['dist']))
            for p in ranking:
                with st.expander(f"📍 {p['dist']}km | {p['nome'].upper()} {'✅' if p.get('verificado') else ''}"):
                    st.write(f"**Especialidade:** {p['area']}")
                    if st.button(f"📞 LIBERAR CONTATO (Custo: {TAXA_CONTATO} Moeda)", key=f"btn_{p['id']}"):
                        if p.get('saldo', 0) >= TAXA_CONTATO:
                            db.collection("profissionais").document(p['id']).update({"saldo": p['saldo'] - TAXA_CONTATO, "cliques": p.get('cliques', 0) + 1})
                            st.success(f"Contato: {p['id']}")
                            st.link_button("ABRIR WHATSAPP", f"https://wa.me/{p['id']}")
                        else:
                            st.error("Profissional temporariamente offline (sem saldo).")

# ABA 1: CADASTRAR
with menu_abas[1]:
    st.subheader("🚀 Cadastro de Parceiro")
    with st.form("form_cadastro"):
        nome_c = st.text_input("Nome ou Empresa")
        zap_c = st.text_input("WhatsApp (ID)")
        area_c = st.selectbox("Sua Especialidade", CATEGORIAS_OFICIAIS)
        pass_c = st.text_input("Crie uma Senha", type="password")
        if st.form_submit_button("FINALIZAR CADASTRO"):
            db.collection("profissionais").document(zap_c).set({
                "nome": nome_c, "area": area_c, "senha": pass_c, "saldo": BONUS_WELCOME,
                "aprovado": False, "verificado": False, "lat": u_lat, "lon": u_lon, "cliques": 0
            })
            st.success("Cadastro enviado! Aguarde a aprovação do Admin.")

# ABA 2: MEU PERFIL (EDIÇÃO E GESTÃO)
with menu_abas[2]:
    if 'auth' not in st.session_state: st.session_state.auth = False
    
    if not st.session_state.auth:
        az, ap = st.text_input("Seu WhatsApp"), st.text_input("Sua Senha", type="password")
        if st.button("LOGAR NO PAINEL"):
            u = db.collection("profissionais").document(az).get()
            if u.exists and u.to_dict().get('senha') == ap:
                st.session_state.auth, st.session_state.user_id = True, az
                st.rerun()
            else: st.error("🚫 Acesso negado. Verifique os dados.")
    else:
        p_ref = db.collection("profissionais").document(st.session_state.user_id)
        p = p_ref.get().to_dict()
        st.header(f"Bem-vindo, {p['nome']}!")
        st.metric("Saldo Disponível", f"{p.get('saldo', 0)} 🪙")
        
        with st.expander("🛠️ EDITAR MEU PERFIL"):
            n_nome = st.text_input("Nome Comercial", p['nome'])
            n_bio = st.text_area("Descrição do Serviço", p.get('bio', ''))
            if st.button("SALVAR DADOS"):
                p_ref.update({"nome": n_nome, "bio": n_bio})
                st.success("Atualizado!")
        
        if st.button("LOGOUT"):
            st.session_state.auth = False
            st.rerun()

# ABA 3: ADMIN (TOTAL POWER)
with menu_abas[3]:
    st.subheader("🔒 Terminal Supremo")
    if st.text_input("Chave Master", type="password", key="master") == CHAVE_ADMIN:
        all_profs = list(db.collection("profissionais").stream())
        pendentes = [p for p in all_profs if not p.to_dict().get('aprovado')]
        
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Total de Parceiros", len(all_profs))
        col_m2.metric("Aprovações Pendentes", len(pendentes))
        
        t_g, t_a = st.tabs(["GESTÃO DE USUÁRIOS", "FILA DE APROVAÇÃO"])
        with t_g:
            for doc in all_profs:
                d, pid = doc.to_dict(), doc.id
                with st.expander(f"{d['nome']} ({pid})"):
                    ns = st.number_input("Ajustar Saldo", value=d.get('saldo', 0), key=f"adj_{pid}")
                    if st.button("SALVAR", key=f"s_{pid}"):
                        db.collection("profissionais").document(pid).update({"saldo": ns})
                        st.rerun()
                    if st.button("BANIR", key=f"del_{pid}"):
                        db.collection("profissionais").document(pid).delete()
                        st.rerun()
        with t_a:
            for p in pendentes:
                if st.button(f"APROVAR {p.id}", key=f"ok_{p.id}"):
                    db.collection("profissionais").document(p.id).update({"aprovado": True})
                    st.rerun()

# ABA 4: FEEDBACK
with menu_abas[4]:
    with st.form("f_feed"):
        n_f = st.select_slider("Satisfação", ["Muito Insatisfeito", "Regular", "Satisfeito", "Excelente"], value="Excelente")
        m_f = st.text_area("Sua mensagem")
        if st.form_submit_button("ENVIAR AVALIAÇÃO"):
            db.collection("feedbacks").add({"data": str(datetime.datetime.now()), "nota": n_f, "mensagem": m_f})
            st.success("Recebemos! Obrigado.")

# ABA 5: FINANCEIRO (COFRE)
if len(menu_abas) > 5:
    with menu_abas[5]:
        if st.text_input("Senha do Cofre", type="password") == "riqueza2026":
            vendas = sum([p.to_dict().get('total_comprado', 0) for p in list(db.collection("profissionais").stream())])
            st.metric("💰 FATURAMENTO REAL", f"R$ {vendas:,.2f}")

# RODAPÉ
st.markdown(f'<div style="text-align:center; padding:30px; color:#94A3B8; font-size:12px;">GERALJÁ v20.0 © {datetime.datetime.now().year}</div>', unsafe_allow_html=True)

