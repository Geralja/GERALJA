# ==============================================================================
# GERALJÁ SP - ENTERPRISE EDITION v19.0 (STABLE & EXPANDED)
# O SISTEMA MAIS COMPLETO JÁ DESENVOLVIDO PARA GESTÃO DE SERVIÇOS EM SÃO PAULO
# ==============================================================================

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime
import math
import random
import re
import time
import pandas as pd
from io import BytesIO

# ------------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DE AMBIENTE E PERFORMANCE
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="GeralJá | Ecossistema Profissional SP",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ------------------------------------------------------------------------------
# 2. CAMADA DE PERSISTÊNCIA (FIREBASE)
# ------------------------------------------------------------------------------
@st.cache_resource
def conectar_banco_master():
    """Inicializa a conexão com segurança e tratamento de falhas."""
    if not firebase_admin._apps:
        try:
            if "FIREBASE_BASE64" not in st.secrets:
                st.error("🔑 Chave de segurança FIREBASE_BASE64 não encontrada nos Secrets.")
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
# 3. POLÍTICAS DE GOVERNANÇA E CONSTANTES
# ------------------------------------------------------------------------------
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ADMIN = "mumias"
TAXA_CONTATO = 1
BONUS_WELCOME = 5

# Localização Referência: São Paulo - SP
LAT_REF_SP = -23.5505
LON_REF_SP = -46.6333

CATEGORIAS_OFICIAIS = [
    "Encanador", "Eletricista", "Pintor", "Pedreiro", "Gesseiro",
    "Telhadista", "Mecânico", "Borracheiro", "Guincho 24h", "Diarista",
    "Jardineiro", "Piscineiro", "TI", "Refrigeração", "Ajudante Geral"
]

# ------------------------------------------------------------------------------
# 4. MOTOR DE IA E GEOLOCALIZAÇÃO
# ------------------------------------------------------------------------------
CONCEITOS_EXPANDIDOS = {
    "vazamento": "Encanador", "cano": "Encanador", "torneira": "Encanador", "esgoto": "Encanador",
    "curto": "Eletricista", "fiação": "Eletricista", "disjuntor": "Eletricista", "luz": "Eletricista",
    "pintar": "Pintor", "reforma": "Pedreiro", "piso": "Pedreiro", "gesso": "Gesseiro",
    "carro": "Mecânico", "motor": "Mecânico", "guincho": "Guincho 24h", "pneu": "Borracheiro",
    "faxina": "Diarista", "jardim": "Jardineiro", "piscina": "Piscineiro",
    "computador": "TI", "celular": "TI", "wifi": "TI", "ar": "Refrigeração"
}

def processar_ia_avancada(texto):
    """Analisa a intenção do cliente e mapeia para a categoria correta."""
    if not texto: return "Ajudante Geral"
    t_clean = texto.lower().strip()
    for chave, categoria in CONCEITOS_EXPANDIDOS.items():
        if re.search(rf"\b{chave}\b", t_clean):
            return categoria
    return "Ajudante Geral"

def calcular_distancia_real(lat1, lon1, lat2, lon2):
    """Cálculo Matemático de Haversine para Precisão Geográfica."""
    try:
        if None in [lat1, lon1, lat2, lon2]: return 999.0
        R = 6371 # Raio da Terra em KM
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return round(R * c, 1)
    except:
        return 999.0

def converter_img_b64(file):
    """Converte arquivos de imagem para armazenamento Base64 no Firebase."""
    if file is None: return ""
    return base64.b64encode(file.read()).decode()

# ------------------------------------------------------------------------------
# 5. DESIGN SYSTEM - CSS CUSTOMIZADO (EXPANDIDO)
# ------------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    
    * { font-family: 'Inter', sans-serif; transition: all 0.2s ease-in-out; }
    .stApp { background-color: #F8FAFC; }
    
    /* Header Container */
    .header-container { 
        background: white; padding: 50px 20px; border-radius: 0 0 60px 60px; 
        text-align: center; box-shadow: 0 10px 40px rgba(0,0,0,0.08); 
        border-bottom: 10px solid #FF8C00; margin-bottom: 30px;
    }
    
    .logo-azul { color: #0047AB; font-weight: 900; font-size: 70px; letter-spacing: -3px; }
    .logo-laranja { color: #FF8C00; font-weight: 900; font-size: 70px; letter-spacing: -3px; }
    
    /* Cards Profissionais */
    .pro-card { 
        background: white; border-radius: 35px; padding: 30px; margin-bottom: 25px; 
        border-left: 20px solid #0047AB; box-shadow: 0 15px 30px rgba(0,0,0,0.05); 
        display: flex; align-items: center; border-right: 1px solid #E2E8F0;
    }
    
    .pro-card:hover { transform: scale(1.01); box-shadow: 0 20px 40px rgba(0,0,0,0.1); }
    
    .pro-img { 
        width: 120px; height: 120px; border-radius: 50%; object-fit: cover; 
        border: 5px solid #F1F5F9; margin-right: 30px; box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    /* Badges */
    .badge-dist { background: #DBEAFE; color: #1E40AF; padding: 8px 16px; border-radius: 15px; font-weight: 800; font-size: 12px; text-transform: uppercase; }
    .badge-area { background: #FFEDD5; color: #9A3412; padding: 8px 16px; border-radius: 15px; font-weight: 800; font-size: 12px; text-transform: uppercase; margin-left: 10px; }
    
    /* Botoes */
    .btn-zap { 
        background: #22C55E; color: white !important; padding: 18px; border-radius: 20px; 
        text-decoration: none; font-weight: 900; display: block; text-align: center; 
        font-size: 18px; margin-top: 15px; box-shadow: 0 4px 14px 0 rgba(34, 197, 94, 0.39);
    }
    .btn-zap:hover { background: #16a34a; transform: translateY(-2px); }

    /* Painel Admin e Metricas */
    .metric-box { 
        background: #1E293B; color: white; padding: 30px; border-radius: 30px; 
        text-align: center; border-bottom: 6px solid #FF8C00; box-shadow: 0 10px 20px rgba(0,0,0,0.15);
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 6. ESTRUTURA DE ABAS (ORGANIZADA PARA NÃO REPETIR)
# ------------------------------------------------------------------------------
st.markdown('<div class="header-container"><span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span><br><small style="letter-spacing:10px; color:#64748B; font-weight:700;">SÃO PAULO ELITE EDITION</small></div>', unsafe_allow_html=True)

menu_abas = st.tabs([
    "🔍 ENCONTRAR ESPECIALISTA", 
    "💼 CENTRAL DO PARCEIRO", 
    "📝 NOVO CADASTRO", 
    "🛡️ TERMINAL ADMIN"
])

# --- ABA 1: MOTOR DE BUSCA (UNIFICADO) ---
with menu_abas[0]:
    st.markdown("### 🏙️ Qual problema resolveremos agora?")
    c1, c2 = st.columns([3, 1])
    
    # Busca e Raio (Uma única vez com chaves seguras)
    termo_busca = c1.text_input("Ex: 'Cano estourado', 'Instalar ventilador'", key="main_search_final")
    raio_km = c2.select_slider("Raio de Busca (KM)", options=[1, 5, 10, 20, 50, 100], value=5, key="main_slider_final")
    
    if termo_busca:
        cat_ia = processar_ia_avancada(termo_busca)
        st.info(f"✨ **Análise da IA:** Filtrando os melhores profissionais em **{cat_ia}** próximo a você.")
        
        profs = db.collection("profissionais").where("area", "==", cat_ia).where("aprovado", "==", True).stream()
        lista_ranking = []
        
        for p_doc in profs:
            p = p_doc.to_dict()
            p['id'] = p_doc.id
            dist = calcular_distancia_real(LAT_REF_SP, LON_REF_SP, p.get('lat', LAT_REF_SP), p.get('lon', LON_REF_SP))
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
                            <p style="color:#475569; font-size:15px; line-height:1.6;">{pro.get('descricao', 'Especialista pronto para te atender.')}</p>
                            <p style="color:#64748B; font-size:13px;">⭐ {pro.get('rating', 5.0)} | 🏙️ {pro.get('localizacao', 'São Paulo - SP')}</p>
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
                            st.markdown(f'<a href="https://wa.me/55{pro["whatsapp"]}?text=Olá {pro["nome"]}, vi seu anúncio no GeralJá!" class="btn-zap">ABRIR WHATSAPP</a>', unsafe_allow_html=True)
                    else:
                        st.error("⏳ Este profissional está com a agenda lotada.")

# --- ABA 2: CENTRAL DO PARCEIRO (COM LOGIN E DASHBOARD) ---
with menu_abas[1]:
    if 'auth' not in st.session_state: st.session_state.auth = False
    
    if not st.session_state.auth:
        st.subheader("🔑 Login do Parceiro")
        col_l1, col_l2 = st.columns(2)
        login_zap = col_l1.text_input("WhatsApp (Login)", key="login_z")
        login_pw = col_l2.text_input("Senha", type="password", key="login_p")
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
        # (Aqui ficam as métricas e edição que você já tem)
        if st.button("SAIR DA CONTA"):
            st.session_state.auth = False
            st.rerun()

# --- ABA 3: NOVO CADASTRO (COM CATEGORIA MANUAL) ---
with menu_abas[2]:
    st.markdown("### 🚀 Junte-se à elite dos profissionais")
    with st.form("form_reg_final"):
        reg_nome = st.text_input("Nome/Empresa")
        reg_zap = st.text_input("WhatsApp")
        reg_cat_sel = st.selectbox("Categoria Principal", CATEGORIAS_OFICIAIS + ["Outra (Manual)"])
        reg_cat_custom = ""
        if reg_cat_sel == "Outra (Manual)":
            reg_cat_custom = st.text_input("Qual sua especialidade?")
        if st.form_submit_button("CRIAR MEU PERFIL"):
            st.success("Cadastro
