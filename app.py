# ==============================================================================
# GERALJÁ BRASIL - ENTERPRISE EDITION v19.0 (ESTÁVEL E UNIFICADA)
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

# ------------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DE AMBIENTE E PERFORMANCE
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="GeralJá | Ecossistema Profissional Brasil",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ------------------------------------------------------------------------------
# 2. CAMADA DE PERSISTÊNCIA (FIREBASE)
# ------------------------------------------------------------------------------
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

# ------------------------------------------------------------------------------
# 3. POLÍTICAS E CONSTANTES (EXPANDIDAS PARA BRASIL)
# ------------------------------------------------------------------------------
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ADMIN = "mumias"
TAXA_CONTATO = 1
BONUS_WELCOME = 5


# Lista de Estados para o Cadastro Nacional
LISTA_ESTADOS = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]

CATEGORIAS_OFICIAIS = [
    "Encanador", "Eletricista", "Pintor", "Pedreiro", "Gesseiro",
    "Telhadista", "Mecânico", "Borracheiro", "Guincho 24h", "Diarista",
    "Jardineiro", "Piscineiro", "TI", "Refrigeração", "Ajudante Geral", "Outro (Personalizado)"
]

CONCEITOS_EXPANDIDOS = {
    "vazamento": "Encanador", "cano": "Encanador", "curto": "Eletricista", "luz": "Eletricista",
    "pintar": "Pintor", "reforma": "Pedreiro", "piso": "Pedreiro", "gesso": "Gesseiro",
    "carro": "Mecânico", "guincho": "Guincho 24h", "pneu": "Borracheiro", "faxina": "Diarista",
    "jardim": "Jardineiro", "piscina": "Piscineiro", "computador": "TI", "ar": "Refrigeração"
}

# ------------------------------------------------------------------------------
# 4. FUNÇÕES DE SUPORTE
# ------------------------------------------------------------------------------
def processar_ia_avancada(texto):
    if not texto: return "Ajudante Geral"
    t_clean = texto.lower().strip()
    for chave, categoria in CONCEITOS_EXPANDIDOS.items():
        if re.search(rf"\b{chave}\b", t_clean): return categoria
    return "Ajudante Geral"

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
    return base64.b64encode(file.read()).decode()

# ------------------------------------------------------------------------------
# 5. DESIGN SYSTEM (CSS)
# ------------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .header-container { background: white; padding: 40px; border-radius: 0 0 50px 50px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.05); border-bottom: 8px solid #FF8C00; margin-bottom: 20px; }
    .logo-azul { color: #0047AB; font-weight: 900; font-size: 55px; letter-spacing: -2px; }
    .logo-laranja { color: #FF8C00; font-weight: 900; font-size: 55px; letter-spacing: -2px; }
    .pro-card { background: white; border-radius: 25px; padding: 25px; margin-bottom: 20px; border-left: 15px solid #0047AB; box-shadow: 0 10px 20px rgba(0,0,0,0.05); display: flex; align-items: center; }
    .pro-img { width: 100px; height: 100px; border-radius: 50%; object-fit: cover; margin-right: 25px; border: 4px solid #F1F5F9; }
    .badge-dist { background: #DBEAFE; color: #1E40AF; padding: 6px 12px; border-radius: 10px; font-weight: 800; font-size: 11px; }
    .badge-area { background: #FFEDD5; color: #9A3412; padding: 6px 12px; border-radius: 10px; font-weight: 800; font-size: 11px; margin-left: 8px; }
    .btn-zap { background: #22C55E; color: white !important; padding: 15px; border-radius: 15px; text-decoration: none; font-weight: 900; display: block; text-align: center; margin-top: 10px; }
    .metric-box { background: #1E293B; color: white; padding: 20px; border-radius: 20px; text-align: center; border-bottom: 4px solid #FF8C00; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 6. LAYOUT PRINCIPAL E NAVEGAÇÃO
# ------------------------------------------------------------------------------
st.markdown('<div class="header-container"><span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span><br><small style="letter-spacing:8px; color:#64748B; font-weight:700;">BRASIL ELITE EDITION</small></div>', unsafe_allow_html=True)

menu_abas = st.tabs(["🔍 BUSCAR", "💼 MEU PAINEL", "📝 CADASTRAR", "🛡️ ADMIN"])

# --- ABA 1: BUSCA (UNIFICADA E ÚNICA COM FILTRO NACIONAL) ---
with menu_abas[0]:
    st.markdown("### 🏙️ Qual problema resolveremos agora?")
    c_city, c_term, c_raio = st.columns([1, 2, 1])
    busca_cidade = c_city.text_input("Sua Cidade", placeholder="Ex: Rio de Janeiro")
    termo_busca = c_term.text_input("Ex: 'Cano estourado', 'Pintar casa'", key="main_search")
    raio_km = c_raio.select_slider("Raio (KM)", options=[1, 5, 10, 20, 50, 100, "Brasil"], value=50, key="main_raio")
    
    if termo_busca:
        cat_ia = processar_ia_avancada(termo_busca)
        st.info(f"✨ IA: Buscando profissionais em **{cat_ia}**.")
        profs = db.collection("profissionais").where("area", "==", cat_ia).where("aprovado", "==", True).stream()
        lista = []
        for p_doc in profs:
            p = p_doc.to_dict()
            p['id'] = p_doc.id
            
            # Lógica de Filtro Nacional vs Raio em SP
            if raio_km == "Brasil":
                lista.append(p)
            elif busca_cidade and busca_cidade.lower() in p.get('cidade', '').lower():
                lista.append(p)
            else:
                dist = calcular_distancia_real(LAT_REF_SP, LON_REF_SP, p.get('lat', LAT_REF_SP), p.get('lon', LON_REF_SP))
                if dist <= (raio_km if isinstance(raio_km, int) else 999):
                    p['dist'] = dist
                    lista.append(p)
        
        # Ordenação: Se tiver distância, ordena por ela. Se não, pelo nome.
        lista.sort(key=lambda x: x.get('dist', 0))
        
        if not lista:
            st.warning("📍 Nenhum profissional encontrado neste raio ou cidade.")
        else:
            for pro in lista:
                with st.container():
                    dist_txt = f"{pro['dist']} KM" if 'dist' in pro else pro.get('cidade', 'Brasil')
                    st.markdown(f"""
                    <div class="pro-card">
                        <img src="{pro.get('foto_url') or 'https://api.dicebear.com/7.x/avataaars/svg?seed='+pro['id']}" class="pro-img">
                        <div style="flex-grow:1;">
                            <span class="badge-dist">📍 {dist_txt}</span><span class="badge-area">💎 {pro['area']}</span>
                            <h2 style="margin:10px 0; color:#1E293B;">{pro.get('nome', 'Profissional').upper()}</h2>
                            <p style="color:#475569; font-size:14px;">{pro.get('descricao')}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if pro.get('saldo', 0) >= TAXA_CONTATO:
                        if st.button(f"CONTATAR {pro['nome'].split()[0].upper()}", key=f"btn_{pro['id']}"):
                            db.collection("profissionais").document(pro['id']).update({"saldo": firestore.Increment(-TAXA_CONTATO), "cliques": firestore.Increment(1)})
                            st.balloons()
                            st.markdown(f'<a href="https://wa.me/55{pro["whatsapp"]}" class="btn-zap">ABRIR WHATSAPP</a>', unsafe_allow_html=True)

# --- ABA 2: PAINEL DO PARCEIRO (LOGIN + DASHBOARD) ---
with menu_abas[1]:
    if 'auth' not in st.session_state: st.session_state.auth = False
    if not st.session_state.auth:
        st.subheader("🔑 Login")
        l_zap = st.text_input("WhatsApp (Login)", key="l_zap")
        l_pw = st.text_input("Senha", type="password", key="l_pw")
        if st.button("ACESSAR PAINEL"):
            doc = db.collection("profissionais").document(l_zap).get()
            if doc.exists and doc.to_dict().get('senha') == l_pw:
                st.session_state.auth, st.session_state.user_id = True, l_zap
                st.rerun()
            else: st.error("Erro de login.")
    else:
        dados = db.collection("profissionais").document(st.session_state.user_id).get().to_dict()
        st.success(f"Olá, {dados.get('nome')}!")
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="metric-box">SALDO<br><b>{dados.get("saldo")} 🪙</b></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-box">LEADS<br><b>{dados.get("cliques")} 🚀</b></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-box">STATUS<br><b>{"ATIVO" if dados.get("aprovado") else "PENDENTE"}</b></div>', unsafe_allow_html=True)
        
        with st.expander("🛠️ EDITAR PERFIL"):
            with st.form("edit_f"):
                e_nome = st.text_input("Nome", value=dados.get('nome'))
                e_cat = st.selectbox("Categoria", CATEGORIAS_OFICIAIS, index=CATEGORIAS_OFICIAIS.index(dados.get('area', 'Ajudante Geral')))
                e_desc = st.text_area("Descrição", value=dados.get('descricao'))
                if st.form_submit_button("SALVAR"):
                    db.collection("profissionais").document(st.session_state.user_id).update({"nome": e_nome, "area": e_cat, "descricao": e_desc})
                    st.rerun()
        if st.button("SAIR"): 
            st.session_state.auth = False
            st.rerun()

# --- ABA 3: CADASTRO (NACIONALIZADO) ---
with menu_abas[2]:
    st.markdown("### 🚀 Cadastro de Profissional")
    with st.form("cad_f"):
        r_nome = st.text_input("Nome Completo")
        r_zap = st.text_input("WhatsApp (DDD + Número)")
        r_pw = st.text_input("Senha", type="password")
        
        # Novos campos para expansão Brasil
        col_cid, col_uf = st.columns(2)
        r_cidade = col_cid.text_input("Cidade")
        r_uf = col_uf.selectbox("Estado (UF)", LISTA_ESTADOS)
        
        r_cat_sel = st.selectbox("Categoria", CATEGORIAS_OFICIAIS)
        r_cat_custom = st.text_input("Se escolheu 'Outro', qual?")
        r_desc = st.text_area("Descreva seus serviços")
        
        if st.form_submit_button("CADASTRAR"):
            cat_final = r_cat_custom if r_cat_sel == "Outro (Personalizado)" else r_cat_sel
            db.collection("profissionais").document(r_zap).set({
                "nome": r_nome, "whatsapp": r_zap, "senha": r_pw, "area": cat_final,
                "cidade": r_cidade.strip().title(), "uf": r_uf,
                "descricao": r_desc, "saldo": BONUS_WELCOME, "cliques": 0, "aprovado": False,
                "lat": LAT_REF_SP, "lon": LON_REF_SP, "data_registro": datetime.datetime.now()
            })
            st.success("Cadastro realizado! Aguarde aprovação.")

# --- ABA 4: ADMIN (TOTALMENTE PRESERVADA) ---
with menu_abas[3]:
    adm_pw = st.text_input("Senha Admin", type="password", key="adm_pw")
    if adm_pw == CHAVE_ADMIN:
        st.write("### Gestão de Profissionais")
        profs_adm = db.collection("profissionais").stream()
        for p in profs_adm:
            d, pid = p.to_dict(), p.id
            with st.expander(f"{d.get('nome')} | {d.get('area')} | {d.get('cidade', 'SP')}"):
                col1, col2 = st.columns(2)
                if col1.button("APROVAR", key=f"ap_{pid}"):
                    db.collection("profissionais").document(pid).update({"aprovado": True})
                    st.rerun()
                moedas = col2.number_input("Moedas", 1, 100, 10, key=f"m_{pid}")
                if col2.button("CREDITAR", key=f"cr_{pid}"):
                    db.collection("profissionais").document(pid).update({"saldo": firestore.Increment(moedas)})
                    st.rerun()

# ------------------------------------------------------------------------------
# RODAPÉ (PRESERVADO)
# ------------------------------------------------------------------------------
st.markdown(f'<div style="text-align:center; padding:30px; color:#94A3B8; font-size:11px;">GERALJÁ BRASIL v19.0 © {datetime.datetime.now().year}</div>', unsafe_allow_html=True)


