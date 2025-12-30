# ==============================================================================
# GERALJÁ BRASIL - ENTERPRISE EDITION v19.0 (FULL & UNIFIED)
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
# 3. POLÍTICAS, CONSTANTES E GEOPOSICIONAMENTO
# ------------------------------------------------------------------------------
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ADMIN = "mumias"
TAXA_CONTATO = 1
BONUS_WELCOME = 5

# Referência Central (Para cálculos de distância inicial)
LAT_REF = -23.5505
LON_REF = -46.6333

CATEGORIAS_OFICIAIS = [
    "Encanador", "Eletricista", "Pintor", "Pedreiro", "Gesseiro",
    "Telhadista", "Mecânico", "Borracheiro", "Guincho 24h", "Diarista",
    "Jardineiro", "Piscineiro", "TI", "Refrigeração", "Ajudante Geral", "Outro (Personalizado)"
]

CONCEITOS_EXPANDIDOS = {
    "vazamento": "Encanador", "cano": "Encanador", "torneira": "Encanador", "curto": "Eletricista", 
    "fiação": "Eletricista", "luz": "Eletricista", "pintar": "Pintor", "reforma": "Pedreiro", 
    "piso": "Pedreiro", "gesso": "Gesseiro", "carro": "Mecânico", "motor": "Mecânico", 
    "guincho": "Guincho 24h", "pneu": "Borracheiro", "faxina": "Diarista", "jardim": "Jardineiro", 
    "piscina": "Piscineiro", "computador": "TI", "wifi": "TI", "ar": "Refrigeração"
}

import re
import unicodedata
import math
import base64

# --- 1. MOTOR DE INTELIGÊNCIA AVANÇADA ---
def normalizar_para_ia(texto):
    """Padroniza o texto removendo acentos para a busca não falhar."""
    if not texto: return ""
    return "".join(c for c in unicodedata.normalize('NFD', texto) 
                  if unicodedata.category(c) != 'Mn').lower().strip()

def processar_ia_avancada(texto):
    """Analisa a necessidade do cliente e define a categoria."""
    if not texto: return "Ajudante Geral"
    
    # Normalizamos a entrada do cliente e as chaves do dicionário
    t_clean = normalizar_para_ia(texto)
    
    # CONCEITOS_EXPANDIDOS deve estar definido no seu código
    for chave, categoria in CONCEITOS_EXPANDIDOS.items():
        chave_norm = normalizar_para_ia(chave)
        # O \b garante que procuremos a palavra exata (evita confundir 'ar' com 'armário')
        if re.search(rf"\b{chave_norm}\b", t_clean):
            return categoria
            
    return "Ajudante Geral"

# --- 2. MOTOR DE GEOLOCALIZAÇÃO (Fórmula de Haversine) ---

def calcular_distancia_real(lat1, lon1, lat2, lon2):
    """Calcula a distância em KM entre dois pontos no globo."""
    try:
        # Se as coordenadas forem nulas, joga o profissional para o fim da lista (999km)
        if None in [lat1, lon1, lat2, lon2]: return 999.0
        
        R = 6371 # Raio da Terra em KM
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
            math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return round(R * c, 1)
    except: 
        return 999.0

# --- 3. MOTOR DE MÍDIA (PORTFÓLIO) ---
def converter_img_b64(file):
    """Converte arquivo de imagem para string base64 para salvar no banco."""
    if file is None: return ""
    try:
        return base64.b64encode(file.read()).decode()
    except:
        return ""
# ------------------------------------------------------------------------------
# 5. DESIGN SYSTEM - CSS CUSTOMIZADO
# ------------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    * { font-family: 'Inter', sans-serif; transition: all 0.2s ease-in-out; }
    .stApp { background-color: #F8FAFC; }
    .header-container { background: white; padding: 50px 20px; border-radius: 0 0 60px 60px; text-align: center; box-shadow: 0 10px 40px rgba(0,0,0,0.08); border-bottom: 10px solid #FF8C00; margin-bottom: 30px; }
    .logo-azul { color: #0047AB; font-weight: 900; font-size: 60px; letter-spacing: -3px; }
    .logo-laranja { color: #FF8C00; font-weight: 900; font-size: 60px; letter-spacing: -3px; }
    .pro-card { background: white; border-radius: 35px; padding: 30px; margin-bottom: 25px; border-left: 20px solid #0047AB; box-shadow: 0 15px 30px rgba(0,0,0,0.05); display: flex; align-items: center; }
    .pro-card:hover { transform: scale(1.01); }
    .pro-img { width: 120px; height: 120px; border-radius: 50%; object-fit: cover; border: 5px solid #F1F5F9; margin-right: 30px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
    .badge-dist { background: #DBEAFE; color: #1E40AF; padding: 8px 16px; border-radius: 15px; font-weight: 800; font-size: 12px; }
    .badge-area { background: #FFEDD5; color: #9A3412; padding: 8px 16px; border-radius: 15px; font-weight: 800; font-size: 12px; margin-left: 10px; }
    .btn-zap { background: #22C55E; color: white !important; padding: 18px; border-radius: 20px; text-decoration: none; font-weight: 900; display: block; text-align: center; font-size: 18px; margin-top: 15px; }
    .metric-box { background: #1E293B; color: white; padding: 30px; border-radius: 30px; text-align: center; border-bottom: 6px solid #FF8C00; box-shadow: 0 10px 20px rgba(0,0,0,0.15); }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 6. LAYOUT PRINCIPAL E NAVEGAÇÃO
# ------------------------------------------------------------------------------
st.markdown('<div class="header-container"><span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span><br><small style="letter-spacing:10px; color:#64748B; font-weight:700;">BRASIL ELITE EDITION</small></div>', unsafe_allow_html=True)

menu_abas = st.tabs(["🔍 ENCONTRAR ESPECIALISTA", "💼 CENTRAL DO PARCEIRO", "📝 NOVO CADASTRO", "🛡️ TERMINAL ADMIN"])

# --- ABA 1: MOTOR DE BUSCA (LÓGICA DE GEOLOCALIZAÇÃO INTEGRADA) ---
with menu_abas[0]:
    st.markdown("### 🏙️ Qual problema resolveremos agora?")
    c1, c2 = st.columns([3, 1])
    termo_busca = c1.text_input("Ex: 'Cano estourado', 'Instalar ventilador'", key="main_search")
    raio_km = c2.select_slider("Raio de Busca (KM)", options=[1, 5, 10, 20, 50, 100, 500], value=5)
    
    if termo_busca:
        cat_ia = processar_ia_avancada(termo_busca)
        st.info(f"✨ **Análise da IA:** Buscando os melhores profissionais em **{cat_ia}**.")
        
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
        
        if not lista_ranking:
            st.warning(f"📍 Nenhum profissional de {cat_ia} atende neste raio de {raio_km}km.")
        else:
            for pro in lista_ranking:
                with st.container():
                    st.markdown(f"""
                    <div class="pro-card">
                        <img src="{pro.get('foto_url') or 'https://api.dicebear.com/7.x/avataaars/svg?seed='+pro['id']}" class="pro-img">
                        <div style="flex-grow:1;">
                            <span class="badge-dist">📍 {pro['dist']} KM DE VOCÊ</span>
                            <span class="badge-area">💎 {pro['area']}</span>
                            <h2 style="margin:15px 0; color:#1E293B;">{pro.get('nome', 'Profissional').upper()}</h2>
                            <p style="color:#475569; font-size:15px;">{pro.get('descricao')}</p>
                            <p style="color:#64748B; font-size:13px;">⭐ {pro.get('rating', 5.0)} | 🏙️ {pro.get('localizacao', 'Brasil')}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if pro.get('saldo', 0) >= TAXA_CONTATO:
                        if st.button(f"FALAR COM {pro['nome'].split()[0].upper()}", key=f"btn_contact_{pro['id']}"):
                            db.collection("profissionais").document(pro['id']).update({
                                "saldo": firestore.Increment(-TAXA_CONTATO),
                                "cliques": firestore.Increment(1)
                            })
                            st.balloons()
                            st.markdown(f'<a href="https://wa.me/55{pro["whatsapp"]}?text=Olá, vi seu perfil no GeralJá!" class="btn-zap">ABRIR WHATSAPP</a>', unsafe_allow_html=True)
                    else:
                        st.error("⏳ Este profissional está com a agenda lotada.")

# --- ABA 2: CENTRAL DO PARCEIRO (LOGIN, DASHBOARD E EDIÇÃO) ---
with menu_abas[1]:
    if 'auth' not in st.session_state: st.session_state.auth = False
    
    if not st.session_state.auth:
        st.subheader("🔑 Login do Parceiro")
        col_l1, col_l2 = st.columns(2)
        login_zap = col_l1.text_input("WhatsApp (Login)")
        login_pw = col_l2.text_input("Senha", type="password")
        if st.button("ENTRAR NO PAINEL", use_container_width=True):
            user_doc = db.collection("profissionais").document(login_zap).get()
            if user_doc.exists and user_doc.to_dict().get('senha') == login_pw:
                st.session_state.auth = True
                st.session_state.user_id = login_zap
                st.rerun()
            else: st.error("Credenciais inválidas.")
    else:
        uid = st.session_state.user_id
        dados = db.collection("profissionais").document(uid).get().to_dict()
        st.success(f"### Bem-vindo, {dados.get('nome')}!")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(f'<div class="metric-box"><small>SALDO</small><br><b style="font-size:35px;">{dados.get("saldo", 0)} 🪙</b></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric-box"><small>LEADS</small><br><b style="font-size:35px;">{dados.get("cliques", 0)} 🚀</b></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric-box"><small>NOTA</small><br><b style="font-size:35px;">{dados.get("rating", 5.0)} ⭐</b></div>', unsafe_allow_html=True)
        m4.markdown(f'<div class="metric-box" style="background:{"#059669" if dados.get("aprovado") else "#B91C1C"}"><small>STATUS</small><br><b style="font-size:25px;">{"ATIVO" if dados.get("aprovado") else "PENDENTE"}</b></div>', unsafe_allow_html=True)
        
        st.divider()
        with st.expander("🛠️ EDITAR PERFIL E FOTO"):
            with st.form("edit_profile"):
                new_nome = st.text_input("Nome de Exibição", value=dados.get('nome'))
                new_desc = st.text_area("Descrição do Serviço", value=dados.get('descricao'))
                new_foto = st.file_uploader("Trocar Foto de Perfil", type=['jpg', 'png'])
                if st.form_submit_button("SALVAR ALTERAÇÕES"):
                    upd = {"nome": new_nome, "descricao": new_desc}
                    if new_foto: upd["foto_url"] = f"data:image/png;base64,{converter_img_b64(new_foto)}"
                    db.collection("profissionais").document(uid).update(upd)
                    st.success("Perfil atualizado!")
                    time.sleep(1)
                    st.rerun()
        
        if st.button("SAIR DA CONTA"):
            st.session_state.auth = False
            st.rerun()

# --- ABA 3: NOVO CADASTRO (LÓGICA DE CATEGORIA MANUAL + IA) ---
with menu_abas[2]:
    st.markdown("### 🚀 Junte-se à elite dos profissionais")
    with st.form("form_registro"):
        reg_nome = st.text_input("Nome Completo ou Empresa")
        reg_zap = st.text_input("WhatsApp (DDD + Número)")
        reg_pw = st.text_input("Crie uma Senha", type="password")
        reg_cat_sel = st.selectbox("Escolha sua Categoria", CATEGORIAS_OFICIAIS)
        reg_cat_custom = st.text_input("Se escolheu 'Outro', qual sua especialidade?")
        reg_desc = st.text_area("Descreva o que você faz (Dica: Use palavras-chave)")
        
        if st.form_submit_button("SOLICITAR CADASTRO"):
            if not reg_nome or not reg_zap:
                st.error("Preencha os dados obrigatórios.")
            else:
                cat_final = reg_cat_custom if reg_cat_sel == "Outro (Personalizado)" else reg_cat_sel
                db.collection("profissionais").document(reg_zap).set({
                    "nome": reg_nome, "whatsapp": reg_zap, "senha": reg_pw, "area": cat_final,
                    "descricao": reg_desc, "saldo": BONUS_WELCOME, "cliques": 0, "rating": 5.0,
                    "aprovado": False, "foto_url": "", "lat": LAT_REF, "lon": LON_REF,
                    "data_registro": datetime.datetime.now()
                })
                st.success("Cadastro enviado! Aguarde aprovação do administrador.")
                st.balloons()

# --- ABA 4: TERMINAL ADMIN (GESTÃO DE CRÉDITOS E FEEDBACKS) ---
with menu_abas[3]:
    access_adm = st.text_input("Senha Master", type="password", key="adm_auth")
    if access_adm == CHAVE_ADMIN:
        tab_p, tab_f = st.tabs(["👥 PROFISSIONAIS", "📩 FEEDBACKS"])
        
        with tab_p:
            profs_all = db.collection("profissionais").stream()
            for p_doc in profs_all:
                p, pid = p_doc.to_dict(), p_doc.id
                with st.expander(f"{'🟢' if p.get('aprovado') else '🟡'} {p.get('nome')} | ID: {pid}"):
                    c1, c2, c3 = st.columns(3)
                    if c1.button("APROVAR", key=f"ap_{pid}"):
                        db.collection("profissionais").document(pid).update({"aprovado": True})
                        st.rerun()
                    
                    v_moedas = c2.number_input("Qtd Moedas", 1, 500, 50, key=f"v_{pid}")
                    if c2.button("CREDITAR", key=f"cr_{pid}"):
                        db.collection("profissionais").document(pid).update({"saldo": firestore.Increment(v_moedas)})
                        st.success(f"Creditado {v_moedas} moedas!")
                    
                    if c3.button("REMOVER", key=f"del_{pid}"):
                        db.collection("profissionais").document(pid).delete()
                        st.rerun()
        
        with tab_f:
            st.info("Sistema de monitoramento de feedbacks em tempo real.")
            # (Aqui você pode adicionar o loop de leitura da coleção 'feedbacks')

# ------------------------------------------------------------------------------
# RODAPÉ ÚNICO
# ------------------------------------------------------------------------------
st.markdown(f'<div style="text-align:center; padding:40px; color:#94A3B8; font-size:12px;">GERALJÁ BRASIL v19.0 © {datetime.datetime.now().year}</div>', unsafe_allow_html=True)

