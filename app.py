# ==============================================================================
# GERALJÁ - ECOSSISTEMA PROFISSIONAL NACIONAL v15.0
# FOCO: GEOLOCALIZAÇÃO PRECISA + CONTROLE TOTAL DE ADMIN
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

# ------------------------------------------------------------------------------
# 1. SETUP E INFRAESTRUTURA
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="GeralJá | Profissionais Próximos",
    page_icon="🛠️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

@st.cache_resource
def conectar_banco():
    if not firebase_admin._apps:
        try:
            b64_key = st.secrets["FIREBASE_BASE64"]
            decoded_json = base64.b64decode(b64_key).decode("utf-8")
            cred = credentials.Certificate(json.loads(decoded_json))
            return firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Erro Fatal: {e}")
            st.stop()
    return firebase_admin.get_app()

conectar_banco()
db = firestore.client()

# ------------------------------------------------------------------------------
# 2. REGRAS E CONSTANTES (SEM MENÇÃO A CIDADE ESPECÍFICA)
# ------------------------------------------------------------------------------
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ADMIN = "mumias"
TAXA_CONTATO = 1
BONUS_NOVO = 5

# Dicionário IA (Mapeamento de Necessidades)
CONCEITOS = {
    "vazamento": "Encanador", "chuveiro": "Eletricista", "pintura": "Pintor",
    "faxina": "Diarista", "mudança": "Fretes", "unha": "Manicure",
    "carro": "Mecânico", "computador": "TI", "reforma": "Pedreiro"
}

# ------------------------------------------------------------------------------
# 3. MOTORES DE LÓGICA (IA + GPS)
# ------------------------------------------------------------------------------
def processar_ia(texto):
    if not texto: return "Ajudante Geral"
    t = texto.lower()
    for k, v in CONCEITOS.items():
        if k in t: return v
    return "Ajudante Geral"

def calcular_distancia(lat1, lon1, lat2, lon2):
    """Calcula distância real entre cliente e profissional"""
    if None in [lat1, lon1, lat2, lon2]: return 99.0
    R = 6371
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)

# ------------------------------------------------------------------------------
# 4. DESIGN SYSTEM (PREMIUM)
# ------------------------------------------------------------------------------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap');
    * { font-family: 'Montserrat', sans-serif; }
    .stApp { background-color: #FAFAFA; }
    .header { text-align: center; padding: 30px; }
    .txt-azul { color: #0047AB; font-size: 50px; font-weight: 900; }
    .txt-laranja { color: #FF8C00; font-size: 50px; font-weight: 900; }
    .card-vazado { 
        background: white; border-radius: 20px; padding: 20px; margin-bottom: 15px;
        border-left: 10px solid #0047AB; box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        display: flex; align-items: center;
    }
    .avatar-pro { width: 80px; height: 80px; border-radius: 50%; object-fit: cover; margin-right: 20px; }
    .badge-km { background: #E3F2FD; color: #0047AB; padding: 3px 10px; border-radius: 8px; font-weight: 900; font-size: 11px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="header"><span class="txt-azul">GERAL</span><span class="txt-laranja">JÁ</span></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 5. NAVEGAÇÃO POR ABAS
# ------------------------------------------------------------------------------
UI_TABS = st.tabs(["🔍 BUSCAR", "👤 MEU PERFIL", "✍️ CADASTRAR", "🛡️ ADMIN"])

# ABA 1: BUSCA (O QUE VOCÊ PEDIU: FILTRO POR PROXIMIDADE)
with UI_TABS[0]:
    st.write("### 📍 Onde você está agora?")
    # O cliente pode digitar a latitude ou usar o GPS do navegador
    c_gps1, c_gps2 = st.columns(2)
    lat_c = c_gps1.number_input("Sua Latitude", value=-23.55, format="%.5f")
    lon_c = c_gps2.number_input("Sua Longitude", value=-46.63, format="%.5f")
    
    st.divider()
    busca = st.text_input("O que você precisa hoje?", placeholder="Ex: Chuveiro queimado")
    raio_max = st.slider("Ver profissionais em um raio de (KM):", 1, 100, 20)
    
    if busca:
        cat_ia = processar_ia(busca)
        st.info(f"IA: Buscando **{cat_ia}** num raio de {raio_max}km...")
        
        query = db.collection("profissionais").where("area", "==", cat_ia).where("aprovado", "==", True).stream()
        
        lista_resultados = []
        for doc in query:
            p = doc.to_dict()
            dist = calcular_distancia(lat_c, lon_c, p.get('lat'), p.get('lon'))
            if dist <= raio_max:
                p['id'] = doc.id
                p['dist'] = dist
                lista_resultados.append(p)
        
        # Ordenar por proximidade real
        lista_resultados.sort(key=lambda x: x['dist'])
        
        if not lista_resultados:
            st.warning("Nenhum profissional desta categoria tão próximo de você.")
        else:
            for pro in lista_resultados:
                st.markdown(f"""
                <div class="card-vazado">
                    <img src="{pro.get('foto_url') or 'https://via.placeholder.com/80'}" class="avatar-pro">
                    <div style="flex-grow:1;">
                        <span class="badge-km">📍 A {pro['dist']} KM DE VOCÊ</span>
                        <h4 style="margin:5px 0;">{pro['nome']}</h4>
                        <p style="margin:0; font-size:12px; color:#666;">⭐ {pro['rating']} | {pro['localizacao']}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if pro.get('saldo', 0) >= TAXA_CONTATO:
                    if st.button(f"LIBERAR WHATSAPP", key=f"btn_{pro['id']}"):
                        db.collection("profissionais").document(pro['id']).update({
                            "saldo": firestore.Increment(-TAXA_CONTATO),
                            "cliques": firestore.Increment(1)
                        })
                        st.markdown(f'<a href="https://wa.me/55{pro["whatsapp"]}" style="background:#25D366; color:white; padding:12px; display:block; text-align:center; border-radius:10px; text-decoration:none; font-weight:bold;">ABRIR CONVERSA</a>', unsafe_allow_html=True)
                else:
                    st.error("Profissional indisponível no momento.")

# ABA 2: PERFIL (PAINEL DO PROFISSIONAL)
with UI_TABS[1]:
    # ... (Lógica de login e dashboard do profissional igual à v10 que você enviou)
    st.subheader("Acesso do Parceiro")
    # Login e métricas aqui...

# ABA 3: CADASTRO (COM CAPTURA DE LOCALIZAÇÃO)
with UI_TABS[2]:
    with st.form("reg"):
        st.write("### ✍️ Cadastre-se")
        f_n = st.text_input("Nome")
        f_w = st.text_input("WhatsApp")
        f_s = st.text_input("Senha", type="password")
        st.info("⚠️ Para ser encontrado, informe as coordenadas da sua base:")
        f_lat = st.number_input("Sua Latitude", value=-23.55, format="%.5f")
        f_lon = st.number_input("Sua Longitude", value=-46.63, format="%.5f")
        f_d = st.text_area("O que você faz?")
        
        if st.form_submit_button("CADASTRAR"):
            cat = processar_ia(f_d)
            db.collection("profissionais").document(f_w).set({
                "nome": f_n, "whatsapp": f_w, "senha": f_s, "area": cat,
                "lat": f_lat, "lon": f_lon, "saldo": BONUS_NOVO, 
                "aprovado": False, "cliques": 0, "rating": 5.0
            })
            st.success("Cadastrado! Fale com o admin para aprovação.")

# ABA 4: ADMIN (O CONTROLE TOTAL QUE VOCÊ EXIGIU)
with UI_TABS[3]:
    if st.text_input("Senha Admin", type="password") == CHAVE_ADMIN:
        st.write("### 🛡️ Gestão Master")
        
        profs = db.collection("profissionais").stream()
        for p_doc in profs:
            d = p_doc.to_dict()
            pid = p_doc.id
            status = "✅" if d.get('aprovado') else "⏳"
            
            with st.expander(f"{status} {d.get('nome')} | Saldo: {d.get('saldo')}"):
                c1, c2, c3 = st.columns(3)
                if c1.button("APROVAR", key=f"ap_{pid}"):
                    db.collection("profissionais").document(pid).update({"aprovado": True})
                    st.rerun()
                if c2.button("+10 MOEDAS", key=f"m_{pid}"):
                    db.collection("profissionais").document(pid).update({"saldo": firestore.Increment(10)})
                    st.rerun()
                if c3.button("BANIR", key=f"del_{pid}"):
                    db.collection("profissionais").document(pid).delete()
                    st.rerun()
                
                # Troca de Senha e Ajustes Manuais
                nova_s = st.text_input("Nova Senha", key=f"pw_{pid}")
                if st.button("Trocar Senha", key=f"btns_{pid}"):
                    db.collection("profissionais").document(pid).update({"senha": nova_s})
                    st.success("Senha alterada!")

st.markdown("<center><small>GeralJá v15.0 | Inteligência por Proximidade</small></center>", unsafe_allow_html=True)
