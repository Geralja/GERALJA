import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime
import math
import random
import re

# ==============================================================================
# 1. CONFIGURAÇÃO E INFRAESTRUTURA
# ==============================================================================
st.set_page_config(
    page_title="GeralJá | Profissionais de São Paulo",
    page_icon="🏙️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

@st.cache_resource
def inicializar_infraestrutura_dados():
    if not firebase_admin._apps:
        try:
            b64_key = st.secrets["FIREBASE_BASE64"]
            decoded_json = base64.b64decode(b64_key).decode("utf-8")
            cred_dict = json.loads(decoded_json)
            credenciais = credentials.Certificate(cred_dict)
            return firebase_admin.initialize_app(credenciais)
        except Exception as e:
            st.error(f"❌ Erro de Conexão: {e}")
            st.stop()
    return firebase_admin.get_app()

app_engine = inicializar_infraestrutura_dados()
db = firestore.client()

# Constantes
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ACESSO_ADMIN = "mumias"
TAXA_CONTATO = 1
BONUS_WELCOME = 5
LAT_SP_REF, LON_SP_REF = -23.5505, -46.6333

# ==============================================================================
# 2. MOTOR DE INTELIGÊNCIA (IA & GEOLOC)
# ==============================================================================
from concepts import CONCEITOS_SERVICOS # Ou mantenha o dicionário aqui se preferir

def processar_servico_ia(texto_cliente):
    if not texto_cliente: return "Ajudante Geral"
    t_clean = texto_cliente.lower().strip()
    # Lógica de busca por palavras-chave (Regex)
    # (Dicionário simplificado para exemplo, use o seu completo aqui)
    mapping = {"vazamento": "Encanador", "luz": "Eletricista", "pintar": "Pintor", "reforma": "Pedreiro"}
    for key, prof in mapping.items():
        if re.search(rf"\b{key}\b", t_clean): return prof
    return "Ajudante Geral"

def calcular_km_sp(lat1, lon1, lat2, lon2):
    R = 6371 
    d_lat, d_lon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2)**2)
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 1)

# ==============================================================================
# 3. INTERFACE E ESTILO (CSS)
# ==============================================================================
st.markdown("""
    <style>
    .txt-azul { color: #0047AB; font-size: 50px; font-weight: 900; }
    .txt-laranja { color: #FF8C00; font-size: 50px; font-weight: 900; }
    .card-vazado { background: white; border-radius: 20px; padding: 20px; margin-bottom: 15px; 
                   box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-left: 10px solid #0047AB; }
    .avatar-pro { width: 80px; height: 80px; border-radius: 50%; object-fit: cover; }
    .btn-wpp-link { background-color: #25D366; color: white !important; padding: 12px; 
                    border-radius: 10px; text-decoration: none; display: block; text-align: center; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<center><span class="txt-azul">GERAL</span><span class="txt-laranja">JÁ</span></center>', unsafe_allow_html=True)
st.markdown('<center><p style="letter-spacing: 5px; color: gray;">SÃO PAULO PROFISSIONAL</p></center>', unsafe_allow_html=True)

UI_ABAS = st.tabs(["🔍 BUSCAR", "👤 MINHA CONTA", "📝 CADASTRAR", "🛡️ ADMIN"])

# --- ABA 1: BUSCA ---
with UI_ABAS[0]:
    busca = st.text_input("O que você precisa hoje?", placeholder="Ex: Preciso consertar um vazamento")
    if busca:
        cat = processar_servico_ia(busca)
        st.info(f"✨ IA: Localizamos profissionais de **{cat}**")
        profs = db.collection("profissionais").where("area", "==", cat).where("aprovado", "==", True).stream()
        
        for p in profs:
            d = p.to_dict()
            dist = calcular_km_sp(LAT_SP_REF, LON_SP_REF, d.get('lat', LAT_SP_REF), d.get('lon', LON_SP_REF))
            with st.container():
                st.markdown(f'''<div class="card-vazado">
                    <h4>{d["nome"]}</h4>
                    <p>📍 {d.get("localizacao", "SP")} ({dist} km)</p>
                </div>''', unsafe_allow_html=True)
                if d.get('saldo', 0) >= TAXA_CONTATO:
                    if st.button(f"CONTATAR {d['nome'].upper()}", key=p.id):
                        db.collection("profissionais").document(p.id).update({
                            "saldo": firestore.Increment(-TAXA_CONTATO),
                            "cliques": firestore.Increment(1)
                        })
                        st.markdown(f'<a href="https://wa.me/55{d["whatsapp"]}" class="btn-wpp-link">WHATSAPP</a>', unsafe_allow_html=True)
                else:
                    st.warning("Profissional temporariamente indisponível.")

# --- ABA 2: CONTA (CORRIGIDA) ---
with UI_ABAS[1]:
    st.subheader("🔑 Área do Parceiro")
    c1, c2 = st.columns(2)
    z_log = c1.text_input("WhatsApp (Login)", key="l_z")
    s_log = c2.text_input("Senha", type="password", key="l_s")

    if z_log and s_log:
        ref = db.collection("profissionais").document(z_log).get()
        if ref.exists and ref.to_dict()['senha'] == s_log:
            dados = ref.to_dict()
            st.success(f"Bem-vindo, {dados['nome']}!")
            
            # Dashboard
            col1, col2 = st.columns(2)
            col1.metric("Meu Saldo", f"{dados.get('saldo', 0)} Moedas")
            col2.metric("Contatos Recebidos", dados.get('cliques', 0))
            
            st.divider()
            st.write("💰 **Recarga de Moedas**")
            st.code(f"Chave PIX: {PIX_OFICIAL}")
            st.markdown(f'<a href="https://wa.me/{ZAP_ADMIN}?text=Fiz o PIX para {z_log}" class="btn-wpp-link">ENVIAR COMPROVANTE</a>', unsafe_allow_html=True)
        else:
            st.error("Dados de acesso incorretos.")

# --- ABA 3: CADASTRO ---
with UI_ABAS[2]:
    with st.form("cad"):
        f_n = st.text_input("Nome")
        f_z = st.text_input("WhatsApp (DDD+Número)")
        f_s = st.text_input("Senha", type="password")
        f_d = st.text_area("Descrição do seu serviço")
        if st.form_submit_button("CADASTRAR"):
            if f_n and f_z:
                db.collection("profissionais").document(f_z).set({
                    "nome": f_n, "whatsapp": f_z, "senha": f_s, 
                    "area": processar_servico_ia(f_d), "saldo": BONUS_WELCOME,
                    "aprovado": False, "cliques": 0, "rating": 5.0,
                    "lat": LAT_SP_REF, "lon": LON_SP_REF
                })
                st.success("Cadastro realizado! Aguarde aprovação do admin.")

# --- ABA 4: ADMIN ---
with UI_ABAS[3]:
    if st.text_input("Acesso Admin", type="password") == CHAVE_ACESSO_ADMIN:
        pends = db.collection("profissionais").where("aprovado", "==", False).stream()
        for p in pends:
            d = p.to_dict()
            st.write(f"👤 {d['nome']} - {d['area']}")
            if st.button(f"APROVAR {p.id}"):
                db.collection("profissionais").document(p.id).update({"aprovado": True})
                st.rerun()
