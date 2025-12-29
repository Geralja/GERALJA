# ==============================================================================
# GERALJÁ BRASIL - OMNIVERSAL EDITION v2.000 (SISTEMA INTEGRAL PRONTO)
# ==============================================================================
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime
import math
import re

# ------------------------------------------------------------------------------
# 1. CONFIGURAÇÃO E INFRAESTRUTURA
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="GeralJá | Ecossistema Nacional de Serviços",
    page_icon="🏙️",
    layout="wide",
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
            st.error(f"Erro Crítico: {e}")
            st.stop()
    return firebase_admin.get_app()

app_engine = inicializar_infraestrutura_dados()
db = firestore.client()

# ------------------------------------------------------------------------------
# 2. PARÂMETROS E INTELIGÊNCIA DE CATEGORIAS
# ------------------------------------------------------------------------------
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ACESSO_ADMIN = "mumias"
TAXA_CONTATO = 1
BONUS_WELCOME = 5
LAT_SP_REF, LON_SP_REF = -23.5505, -46.6333

LISTA_ESTADOS = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]

MAPA_PROFISSOES = {
    "Encanador": ["vazamento", "cano", "torneira", "esgoto", "hidraulico", "caixa d'água", "pia", "privada"],
    "Eletricista": ["fio", "luz", "chuveiro", "tomada", "disjuntor", "curto", "energia", "fiação"],
    "Pintor": ["pintar", "parede", "verniz", "massa corrida", "textura", "grafiato"],
    "Pedreiro": ["reforma", "construção", "tijolo", "cimento", "piso", "azulejo", "alvenaria"],
    "Marceneiro": ["madeira", "móvel", "armário", "porta", "guarda-roupa", "restauração"],
    "Mecânico": ["carro", "motor", "freio", "suspensão", "oficina", "veículo"],
    "Diarista": ["limpeza", "faxina", "passar roupa", "organização", "casa"],
    "Manicure": ["unha", "esmalte", "mão", "pé", "cutícula"],
    "Cabeleireiro": ["cabelo", "corte", "tintura", "escova", "progressiva"],
    "Barbeiro": ["barba", "degrade", "navalha"],
    "Técnico TI": ["computador", "notebook", "celular", "wi-fi", "formatar", "software"],
    "Refrigeração": ["ar condicionado", "geladeira", "freezer", "carregar gás"],
    "Montador": ["montar", "desmontar", "móveis", "ikea", "magazine"],
    "Freteiro": ["frete", "mudança", "transporte", "carreto", "entrega"],
    "Jardineiro": ["grama", "jardim", "planta", "poda", "adubo"],
    "Gesseiro": ["gesso", "drywall", "sanca", "forro"]
}
LISTA_AREAS_DROP = sorted(list(MAPA_PROFISSOES.keys()) + ["Ajudante Geral"])

# ------------------------------------------------------------------------------
# 3. MOTORES DE LÓGICA
# ------------------------------------------------------------------------------
def processar_servico_ia(texto):
    if not texto: return "Ajudante Geral"
    t_clean = texto.lower()
    for prof, palavras in MAPA_PROFISSOES.items():
        if any(p in t_clean for p in palavras): return prof
    return "Ajudante Geral"

def calcular_km_real(lat1, lon1, lat2, lon2):
    try:
        R = 6371
        d_lat, d_lon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(d_lat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon/2)**2
        return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)
    except: return 0.0

# ------------------------------------------------------------------------------
# 4. DESIGN SYSTEM PREMIUM
# ------------------------------------------------------------------------------
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap');
    * {{ font-family: 'Montserrat', sans-serif; }}
    .stApp {{ background-color: #F8FAFC; }}
    .header-box {{ 
        text-align: center; padding: 40px; background: white; 
        border-bottom: 8px solid #FF8C00; border-radius: 0 0 50px 50px; 
        box-shadow: 0 15px 35px rgba(0,0,0,0.08); margin-bottom: 30px;
    }}
    .txt-azul {{ color: #0047AB; font-size: 55px; font-weight: 900; letter-spacing: -3px; }}
    .txt-laranja {{ color: #FF8C00; font-size: 55px; font-weight: 900; letter-spacing: -3px; }}
    .card-vazado {{ 
        background: white; border-radius: 25px; padding: 25px; margin-bottom: 20px; 
        border-left: 15px solid #0047AB; box-shadow: 0 10px 25px rgba(0,0,0,0.05); 
        display: flex; align-items: center;
    }}
    .avatar-pro {{ width: 90px; height: 90px; border-radius: 50%; object-fit: cover; margin-right: 25px; border: 4px solid #F1F5F9; background: #E2E8F0; }}
    .btn-wpp {{ background: #22C55E; color: white !important; padding: 15px; border-radius: 12px; text-decoration: none; display: block; text-align: center; font-weight: 900; }}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-box"><span class="txt-azul">GERAL</span><span class="txt-laranja">JÁ</span><br><small style="color:#64748B; letter-spacing:8px; font-size:14px; font-weight:700;">BRASIL PROFISSIONAL</small></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 5. SISTEMA DE ABAS
# ------------------------------------------------------------------------------
UI_ABAS = st.tabs(["🔍 BUSCAR", "💼 MINHA CONTA", "📝 CADASTRAR", "🛡️ ADMIN"])

# --- ABA 1: CLIENTE ---
with UI_ABAS[0]:
    col_c, col_t = st.columns([1, 2])
    cidade_alvo = col_c.text_input("📍 Cidade", placeholder="Ex: São Paulo")
    termo_busca = col_t.text_input("🛠️ O que você precisa?", placeholder="Ex: Pintar casa, arrumar pia...")
    
    if termo_busca:
        cat_ia = processar_servico_ia(termo_busca)
        st.info(f"✨ IA: Buscando por profissionais em **{cat_ia}**")
        
        query = db.collection("profissionais").where("area", "==", cat_ia).where("aprovado", "==", True).stream()
        for d in query:
            p = d.to_dict()
            if not cidade_alvo or cidade_alvo.lower() in p.get('cidade', '').lower():
                dist = calcular_km_real(LAT_SP_REF, LON_SP_REF, p.get('lat', LAT_SP_REF), p.get('lon', LON_SP_REF))
                st.markdown(f'''
                    <div class="card-vazado">
                        <div class="avatar-pro" style="display:flex; align-items:center; justify-content:center; font-size:40px;">👤</div>
                        <div style="flex-grow:1;">
                            <h3 style="margin:0;">{p['nome'].upper()}</h3>
                            <p style="color:#64748B; margin:5px 0;">📍 {p.get('cidade')} | ⭐ {p.get('rating', 5.0)}</p>
                            <p><b>Serviço:</b> {p.get('descricao')[:100]}...</p>
                        </div>
                    </div>
                ''', unsafe_allow_html=True)
                if p.get('saldo', 0) >= TAXA_CONTATO:
                    if st.button(f"CONTATO: {p['nome'].split()[0]}", key=f"call_{d.id}"):
                        db.collection("profissionais").document(d.id).update({"saldo": firestore.Increment(-TAXA_CONTATO), "cliques": firestore.Increment(1)})
                        st.markdown(f'<a href="https://wa.me/55{p["whatsapp"]}?text=Olá, vi seu perfil no GeralJá!" class="btn-wpp">ABRIR WHATSAPP</a>', unsafe_allow_html=True)

# --- ABA 2: PROFISSIONAL ---
with UI_ABAS[1]:
    if 'auth' not in st.session_state: st.session_state.auth = False
    if not st.session_state.auth:
        st.subheader("🔑 Login do Parceiro")
        l_z = st.text_input("WhatsApp (Login)")
        l_p = st.text_input("Senha", type="password")
        if st.button("ENTRAR"):
            doc = db.collection("profissionais").document(l_z).get()
            if doc.exists and doc.to_dict().get('senha') == l_p:
                st.session_state.auth, st.session_state.user = True, l_z
                st.rerun()
            else: st.error("Dados inválidos.")
    else:
        u = db.collection("profissionais").document(st.session_state.user).get().to_dict()
        st.success(f"Logado como: {u['nome']}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Moedas", u.get('saldo'))
        c2.metric("Vistos", u.get('cliques'))
        c3.metric("Nota", u.get('rating'))
        st.divider()
        st.write("### 💳 Recarga PIX")
        st.code(f"Chave PIX: {PIX_OFICIAL}")
        st.markdown(f'<a href="https://wa.me/{ZAP_ADMIN}?text=Fiz o PIX para o usuário: {st.session_state.user}" class="btn-wpp">ENVIAR COMPROVANTE</a>', unsafe_allow_html=True)
        if st.button("SAIR"): st.session_state.auth = False; st.rerun()

# --- ABA 3: CADASTRO ---
with UI_ABAS[2]:
    st.subheader("📝 Cadastro Nacional de Profissionais")
    with st.form("reg_form"):
        f_n = st.text_input("Nome/Empresa")
        f_z = st.text_input("WhatsApp (Somente números)")
        f_s = st.text_input("Senha", type="password")
        f_a = st.selectbox("Sua Especialidade", LISTA_AREAS_DROP)
        f_c = st.text_input("Cidade")
        f_u = st.selectbox("Estado", LISTA_ESTADOS, index=24)
        f_d = st.text_area("O que você faz?")
        if st.form_submit_button("CADASTRAR E RECEBER 5 MOEDAS"):
            if f_n and f_z and f_s:
                db.collection("profissionais").document(f_z).set({
                    "nome": f_n, "whatsapp": f_z, "senha": f_s, "cidade": f_c, "uf": f_u,
                    "area": f_a, "descricao": f_d, "saldo": BONUS_WELCOME, "cliques": 0,
                    "rating": 5.0, "aprovado": False, "timestamp": datetime.datetime.now(),
                    "lat": LAT_SP_REF, "lon": LON_SP_REF
                })
                st.success("Cadastro realizado! Aguarde aprovação.")
                st.markdown(f'<a href="https://wa.me/{ZAP_ADMIN}?text=Aprovar meu cadastro: {f_n}" class="btn-wpp">AVISAR ADMIN</a>', unsafe_allow_html=True)

# --- ABA 4: ADMIN MASTER ---
with UI_ABAS[3]:
    adm_p = st.text_input("Acesso Admin", type="password")
    if adm_p == CHAVE_ACESSO_ADMIN:
        st.subheader("🛡️ Gestão de Ecossistema")
        if st.button("🚀 VARREDURA E LIMPEZA IA"):
            docs = db.collection("profissionais").stream()
            for doc in docs:
                d = doc.to_dict()
                if "saldo" not in d: db.collection("profissionais").document(doc.id).update({"saldo": 5})
            st.success("Banco de dados sanitizado!")
        
        profs = db.collection("profissionais").stream()
        for p_doc in profs:
            p, pid = p_doc.to_dict(), p_doc.id
            with st.expander(f"{'✅' if p.get('aprovado') else '⏳'} {p['nome'].upper()} | {p.get('area')}"):
                c1, c2, c3 = st.columns(3)
                if c1.button("APROVAR", key=f"ap_{pid}"): db.collection("profissionais").document(pid).update({"aprovado": True}); st.rerun()
                if c2.button("DAR +10 MOEDAS", key=f"moe_{pid}"): db.collection("profissionais").document(pid).update({"saldo": firestore.Increment(10)}); st.rerun()
                if c3.button("EXCLUIR", key=f"del_{pid}"): db.collection("profissionais").document(pid).delete(); st.rerun()
                st.write(f"ZAP: {p.get('whatsapp')} | Senha: {p.get('senha')}")

st.markdown("<br><hr><center><p style='color:#64748B; font-size:12px;'>GeralJá Brasil v2.000 © 2025 | Sistema de Alta Performance</p></center>", unsafe_allow_html=True)



