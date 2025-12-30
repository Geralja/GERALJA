# ==============================================================================
# GERALJÁ BRASIL - ENTERPRISE EDITION v20.0 (FULL & UNIFIED)
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

# ------------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DE AMBIENTE E PERFORMANCE
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="GeralJá | Ecossistema Profissional Brasil",
    page_icon="🇧🇷",
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
# 3. POLÍTICAS E CONSTANTES
# ------------------------------------------------------------------------------
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ADMIN = "mumias"
TAXA_CONTATO = 1
BONUS_WELCOME = 5
LAT_REF = -23.5505
LON_REF = -46.6333

CATEGORIAS_OFICIAIS = [
    "Encanador", "Eletricista", "Pintor", "Pedreiro", "Gesseiro",
    "Telhadista", "Mecânico", "Borracheiro", "Guincho 24h", "Diarista",
    "Jardineiro", "Piscineiro", "TI", "Refrigeração", "Serralheiro",
    "Montador", "Freteiro", "Chaveiro", "Técnico de Fogão", "Técnico de Lavadora",
    "Ajudante Geral", "Outro (Personalizado)"
]

# DICIONÁRIO EXPANDIDO (Soma de inteligência)
CONCEITOS_EXPANDIDOS = {
    # Hidráulica
    "vazamento": "Encanador", "cano": "Encanador", "torneira": "Encanador", "descarga": "Encanador", 
    "caixa dagua": "Encanador", "esgoto": "Encanador", "pia": "Encanador", "entupiu": "Encanador",
    # Elétrica
    "curto": "Eletricista", "fiacao": "Eletricista", "luz": "Eletricista", "chuveiro": "Eletricista", 
    "tomada": "Eletricista", "disjuntor": "Eletricista", "energia": "Eletricista", "lampada": "Eletricista",
    # Reforma
    "pintar": "Pintor", "pintura": "Pintor", "reforma": "Pedreiro", "piso": "Pedreiro", "azulejo": "Pedreiro", 
    "tijolo": "Pedreiro", "cimento": "Pedreiro", "telhado": "Telhadista", "goteira": "Telhadista",
    "gesso": "Gesseiro", "drywall": "Gesseiro", "solda": "Serralheiro", "portao": "Serralheiro",
    # Automotivo
    "carro": "Mecânico", "motor": "Mecânico", "oleo": "Mecânico", "guincho": "Guincho 24h", 
    "reboque": "Guincho 24h", "pneu": "Borracheiro", "estepe": "Borracheiro", "furou": "Borracheiro",
    # Domésticos
    "faxina": "Diarista", "limpeza": "Diarista", "passar": "Diarista", "jardim": "Jardineiro", 
    "grama": "Jardineiro", "piscina": "Piscineiro", "cloro": "Piscineiro",
    # Tecnologia/Eletros
    "computador": "TI", "notebook": "TI", "formatar": "TI", "wifi": "TI", "internet": "TI",
    "ar": "Refrigeração", "geladeira": "Refrigeração", "freezer": "Refrigeração",
    "fogao": "Técnico de Fogão", "maquina de lavar": "Técnico de Lavadora",
    # Logística/Montagem
    "montar": "Montador", "armario": "Montador", "moveis": "Montador",
    "frete": "Freteiro", "mudanca": "Freteiro", "carreto": "Freteiro",
    "chave": "Chaveiro", "fechadura": "Chaveiro"
}

# ------------------------------------------------------------------------------
# 4. MOTORES DE IA E GEOLOCALIZAÇÃO
# ------------------------------------------------------------------------------
def normalizar_para_ia(texto):
    if not texto: return ""
    return "".join(c for c in unicodedata.normalize('NFD', str(texto)) 
                  if unicodedata.category(c) != 'Mn').lower().strip()

def processar_ia_avancada(texto):
    if not texto: return "Ajudante Geral"
    t_clean = normalizar_para_ia(texto)
    for chave, categoria in CONCEITOS_EXPANDIDOS.items():
        chave_norm = normalizar_para_ia(chave)
        if re.search(rf"\b{chave_norm}\b", t_clean):
            return categoria
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
    try: return base64.b64encode(file.read()).decode()
    except: return ""
# ==============================================================================
# SISTEMA GUARDIAO - IA DE AUTORRECUPERAÇÃO E SEGURANÇA
# ==============================================================================

def guardia_escanear_e_corrigir():
    """Varre o banco de dados em busca de erros de estrutura e corrige na hora."""
    status_log = []
    try:
        profs = db.collection("profissionais").stream()
        for p_doc in profs:
            dados = p_doc.to_dict()
            id_pro = p_doc.id
            correcoes = {}

            # 1. Verifica campos nulos que causam travamentos
            if not dados.get('area') or dados.get('area') not in CATEGORIAS_OFICIAIS:
                correcoes['area'] = "Ajudante Geral"
            
            if not dados.get('descricao'):
                correcoes['descricao'] = "Profissional parceiro do ecossistema GeralJá Brasil."
            
            if dados.get('saldo') is None:
                correcoes['saldo'] = 0
            
            if dados.get('lat') is None or dados.get('lon') is None:
                correcoes['lat'] = LAT_REF
                correcoes['lon'] = LON_REF

            # 2. Se houver algo errado, aplica a cura automática
            if correcoes:
                db.collection("profissionais").document(id_pro).update(correcoes)
                status_log.append(f"✅ Corrigido: {id_pro}")
        
        return status_log if status_log else ["SISTEMA ÍNTEGRO: Nenhum erro encontrado."]
    except Exception as e:
        return [f"❌ Erro no Scanner: {e}"]

def scan_virus_e_scripts():
    """Detecta se há tentativas de injeção de scripts maliciosos nos campos de texto."""
    alertas = []
    profs = db.collection("profissionais").stream()
    # Padrões comuns de ataque XSS e Injeção
    padroes_perigosos = [r"<script>", r"javascript:", r"DROP TABLE", r"OR 1=1"]
    
    for p_doc in profs:
        dados = p_doc.to_dict()
        conteudo = str(dados.get('nome', '')) + str(dados.get('descricao', ''))
        
        for padrao in padroes_perigosos:
            if re.search(padrao, conteudo, re.IGNORECASE):
                alertas.append(f"⚠️ PERIGO: Conteúdo suspeito no ID {p_doc.id}")
                # Bloqueia o profissional preventivamente
                db.collection("profissionais").document(p_doc.id).update({"aprovado": False})
    
    return alertas if alertas else ["LIMPO: Nenhum script malicioso detectado."]
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
    .pro-card { background: white; border-radius: 25px; padding: 25px; margin-bottom: 20px; border-left: 15px solid #0047AB; box-shadow: 0 10px 20px rgba(0,0,0,0.04); display: flex; align-items: center; }
    .pro-img { width: 100px; height: 100px; border-radius: 50%; object-fit: cover; margin-right: 25px; border: 4px solid #F1F5F9; }
    .btn-zap { background: #22C55E; color: white !important; padding: 15px; border-radius: 15px; text-decoration: none; font-weight: 800; display: block; text-align: center; margin-top: 10px; }
    .metric-box { background: #1E293B; color: white; padding: 20px; border-radius: 20px; text-align: center; border-bottom: 4px solid #FF8C00; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-container"><span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span><br><small style="color:#64748B; font-weight:700;">BRASIL ELITE EDITION</small></div>', unsafe_allow_html=True)

menu_abas = st.tabs(["🔍 BUSCAR", "💼 MEU PERFIL", "📝 CADASTRAR", "🛡️ ADMIN"])

# --- ABA 1: BUSCA ---
with menu_abas[0]:
    st.markdown("### 🏙️ O que você precisa?")
    c1, c2 = st.columns([3, 1])
    termo_busca = c1.text_input("Ex: 'Cano estourado'", key="main_search")
    raio_km = c2.select_slider("Raio (KM)", options=[1, 5, 10, 20, 50, 100, 500], value=10)
    
    if termo_busca:
        cat_ia = processar_ia_avancada(termo_busca)
        st.info(f"✨ IA: Buscando por **{cat_ia}**")
        profs = db.collection("profissionais").where("area", "==", cat_ia).where("aprovado", "==", True).stream()
        
        lista_ranking = []
        for p_doc in profs:
            p = p_doc.to_dict()
            p['id'] = p_doc.id
            dist = calcular_distancia_real(LAT_REF, LON_REF, p.get('lat', LAT_REF), p.get('lon', LON_REF))
            if dist <= raio_km:
                p['dist'] = dist
                lista_ranking.append(p)
        
        lista_ranking.sort(key=lambda x: x['dist'])
        
        for pro in lista_ranking:
            with st.container():
                st.markdown(f"""
                <div class="pro-card">
                    <img src="{pro.get('foto_url') or 'https://api.dicebear.com/7.x/avataaars/svg?seed='+pro['id']}" class="pro-img">
                    <div style="flex-grow:1;">
                        <small>📍 {pro['dist']} KM | 💎 {pro['area']}</small>
                        <h3 style="margin:5px 0;">{pro.get('nome').upper()}</h3>
          desc_segura = (pro.get('descricao') or "Profissional qualificado GeralJá")[:150]
st.markdown(f'<p style="font-size:14px; color:#475569;">{desc_segura}...</p>', unsafe_allow_html=True)
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if pro.get('saldo', 0) >= TAXA_CONTATO:
                    if st.button(f"WHATSAPP - {pro['nome']}", key=f"z_{pro['id']}"):
                        db.collection("profissionais").document(pro['id']).update({"saldo": firestore.Increment(-TAXA_CONTATO), "cliques": firestore.Increment(1)})
                        st.markdown(f'<a href="https://wa.me/55{pro["whatsapp"]}" class="btn-zap">ABRIR CONVERSA</a>', unsafe_allow_html=True)
                else: st.warning("Agenda temporariamente cheia.")

# --- ABA 2: CENTRAL PARCEIRO ---
with menu_abas[1]:
    if 'auth' not in st.session_state: st.session_state.auth = False
    if not st.session_state.auth:
        col1, col2 = st.columns(2)
        l_zap = col1.text_input("WhatsApp")
        l_pw = col2.text_input("Senha", type="password")
        if st.button("ENTRAR"):
            u = db.collection("profissionais").document(l_zap).get()
            if u.exists and u.to_dict().get('senha') == l_pw:
                st.session_state.auth, st.session_state.user_id = True, l_zap
                st.rerun()
    else:
        d = db.collection("profissionais").document(st.session_state.user_id).get().to_dict()
        m1, m2, m3 = st.columns(3)
        m1.markdown(f'<div class="metric-box">SALDO: {d.get("saldo")} 🪙</div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric-box">CLIQUES: {d.get("cliques")} 🚀</div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric-box">STATUS: {"ATIVO" if d.get("aprovado") else "PENDENTE"}</div>', unsafe_allow_html=True)
        
        with st.expander("📝 EDITAR PERFIL"):
            with st.form("ed"):
                n_nome = st.text_input("Nome", d.get('nome'))
                # PROTEÇÃO CONTRA VALUE ERROR NO SELECTBOX
                try:
                    idx_at = CATEGORIAS_OFICIAIS.index(d.get('area', 'Ajudante Geral'))
                except:
                    idx_at = CATEGORIAS_OFICIAIS.index("Ajudante Geral")
                
                n_area = st.selectbox("Área", CATEGORIAS_OFICIAIS, index=idx_at)
                n_desc = st.text_area("Descrição", d.get('descricao'))
                n_foto = st.file_uploader("Nova Foto")
                if st.form_submit_button("SALVAR"):
                    up = {"nome": n_nome, "area": n_area, "descricao": n_desc}
                    if n_foto: up["foto_url"] = f"data:image/png;base64,{converter_img_b64(n_foto)}"
                    db.collection("profissionais").document(st.session_state.user_id).update(up)
                    st.success("Atualizado!")
                    st.rerun()
        if st.button("SAIR"): st.session_state.auth = False; st.rerun()

# --- ABA 3: CADASTRO ---
with menu_abas[2]:
    st.header("Seja um Parceiro")
    with st.form("reg"):
        r_n = st.text_input("Nome")
        r_z = st.text_input("WhatsApp")
        r_s = st.text_input("Senha", type="password")
        r_a = st.selectbox("Sua Especialidade", CATEGORIAS_OFICIAIS)
        r_d = st.text_area("O que você faz?")
        if st.form_submit_button("CADASTRAR"):
            db.collection("profissionais").document(r_z).set({
                "nome": r_n, "whatsapp": r_z, "senha": r_s, "area": r_a, "descricao": r_d,
                "saldo": BONUS_WELCOME, "cliques": 0, "aprovado": False, "lat": LAT_REF, "lon": LON_REF,
                "foto_url": "", "data_registro": datetime.datetime.now()
            })
            st.success("Enviado para aprovação!")

# --- ABA 4: ADMIN ---
with menu_abas[3]:
    if st.text_input("Acesso Admin", type="password") == CHAVE_ADMIN:
        ps = db.collection("profissionais").stream()
        for p_doc in ps:
            p, pid = p_doc.to_dict(), p_doc.id
            with st.expander(f"{p.get('nome')} ({pid})"):
                c1, c2 = st.columns(2)
                if c1.button("APROVAR", key=f"ap_{pid}"): db.collection("profissionais").document(pid).update({"aprovado": True}); st.rerun()
                if c2.button("CREDITAR +50", key=f"cr_{pid}"): db.collection("profissionais").document(pid).update({"saldo": firestore.Increment(50)}); st.success("+50!"); time.sleep(1); st.rerun()
                if st.button("EXCLUIR", key=f"ex_{pid}"): db.collection("profissionais").document(pid).delete(); st.rerun()

# ------------------------------------------------------------------------------
# RODAPÉ ÚNICO (Final do Arquivo)
# ------------------------------------------------------------------------------
st.markdown(f'<div style="text-align:center; padding:20px; color:#94A3B8; font-size:10px;">GERALJÁ v20.0 © {datetime.datetime.now().year}</div>', unsafe_allow_html=True)



