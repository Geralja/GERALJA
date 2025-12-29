# ==============================================================================
# GERALJÁ - O SISTEMA COMPLETO NACIONAL v16.0
# TUDO EM UM: ADMIN TOTAL + FINANCEIRO + GPS + IA DE FILTRAGEM
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
import io

# ------------------------------------------------------------------------------
# 1. NÚCLEO DE CONFIGURAÇÃO (SPA)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="GeralJá | Gestão Profissional",
    page_icon="🛠️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

@st.cache_resource
def startup_db():
    if not firebase_admin._apps:
        try:
            b64_key = st.secrets["FIREBASE_BASE64"]
            decoded_json = base64.b64decode(b64_key).decode("utf-8")
            cred = credentials.Certificate(json.loads(decoded_json))
            return firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Erro de Infraestrutura: {e}")
            st.stop()
    return firebase_admin.get_app()

startup_db()
db = firestore.client()

# ------------------------------------------------------------------------------
# 2. CONSTANTES E REGRAS FINANCEIRAS
# ------------------------------------------------------------------------------
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ADMIN = "mumias"
TAXA_LEAD = 1
BONUS_CADASTRO = 5

# Dicionário de IA para Classificação de Serviços
MAPA_SERVICOS = {
    "vazamento": "Encanador", "chuveiro": "Eletricista", "pintura": "Pintor",
    "faxina": "Diarista", "mudança": "Fretes", "unha": "Manicure",
    "carro": "Mecânico", "computador": "TI", "reforma": "Pedreiro",
    "gesso": "Gesseiro", "telhado": "Telhadista", "jardim": "Jardineiro"
}

# ------------------------------------------------------------------------------
# 3. MOTORES DE CÁLCULO (GPS E IA)
# ------------------------------------------------------------------------------
def calcular_distancia(lat1, lon1, lat2, lon2):
    """Fórmula de Haversine para cálculo de proximidade real"""
    if None in [lat1, lon1, lat2, lon2]: return 999.0
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)

def classificar_servico(texto):
    if not texto: return "Ajudante Geral"
    t = texto.lower()
    for k, v in MAPA_SERVICOS.items():
        if k in t: return v
    return "Ajudante Geral"

# ------------------------------------------------------------------------------
# 4. DESIGN SYSTEM (LAYOUT PREMIUM VAZADO)
# ------------------------------------------------------------------------------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap');
    * { font-family: 'Montserrat', sans-serif; }
    .stApp { background-color: #F8F9FA; }
    
    .logo-container { text-align: center; padding: 20px; background: white; border-bottom: 5px solid #FF8C00; border-radius: 0 0 40px 40px; }
    .azul { color: #0047AB; font-weight: 900; font-size: 45px; }
    .laranja { color: #FF8C00; font-weight: 900; font-size: 45px; }
    
    .card-pro { 
        background: white; border-radius: 25px; padding: 20px; margin-bottom: 15px;
        border-left: 12px solid #0047AB; box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        display: flex; align-items: center; 
    }
    .avatar { width: 90px; height: 90px; border-radius: 50%; object-fit: cover; margin-right: 20px; border: 3px solid #EEE; }
    .badge-dist { background: #E3F2FD; color: #0047AB; padding: 5px 12px; border-radius: 12px; font-weight: 900; font-size: 11px; }
    
    .metric-box { background: #0047AB; color: white; padding: 15px; border-radius: 20px; text-align: center; }
    .btn-wpp { background: #25D366; color: white !important; padding: 15px; border-radius: 15px; text-decoration: none; display: block; text-align: center; font-weight: 900; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="logo-container"><span class="azul">GERAL</span><span class="laranja">JÁ</span><br><small style="color:#666; letter-spacing:5px;">SERVIÇOS PROFISSIONAIS</small></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 5. SISTEMA DE NAVEGAÇÃO (TUDO EM UM)
# ------------------------------------------------------------------------------
ABAS = st.tabs(["🔍 BUSCAR", "👤 PROFISSIONAL", "✍️ CADASTRAR", "🛡️ ADMIN"])

# --- ABA 1: O CLIENTE (BUSCA COM GPS) ---
with ABAS[0]:
    st.write("### 📍 Onde você precisa do serviço?")
    col_g1, col_g2 = st.columns(2)
    lat_cliente = col_g1.number_input("Sua Latitude", value=-23.550, format="%.4f")
    lon_cliente = col_g2.number_input("Sua Longitude", value=-46.633, format="%.4f")
    
    termo = st.text_input("O que você procura?", placeholder="Ex: Consertar pia")
    raio = st.slider("Distância máxima (KM)", 1, 100, 15)
    
    if termo:
        categoria = classificar_servico(termo)
        st.info(f"IA identificou: **{categoria}**")
        
        # Filtro Firestore: Categoria + Aprovados
        docs = db.collection("profissionais").where("area", "==", categoria).where("aprovado", "==", True).stream()
        
        lista_final = []
        for d in docs:
            p = d.to_dict()
            p['id'] = d.id
            dist = calcular_distancia(lat_cliente, lon_cliente, p.get('lat'), p.get('lon'))
            
            # FILTRO DE PROXIMIDADE REAL
            if dist <= raio:
                p['dist'] = dist
                lista_final.append(p)
        
        # Ordenar: Mais perto primeiro
        lista_final.sort(key=lambda x: x['dist'])
        
        if not lista_final:
            st.warning("Nenhum profissional desta área encontrado tão próximo de você.")
        else:
            for pro in lista_final:
                st.markdown(f"""
                <div class="card-pro">
                    <img src="{pro.get('foto_url') or 'https://via.placeholder.com/100'}" class="avatar">
                    <div style="flex-grow:1;">
                        <span class="badge-dist">📍 A {pro['dist']} KM DE VOCÊ</span>
                        <h4 style="margin:5px 0; color:#333;">{pro.get('nome').upper()}</h4>
                        <p style="margin:0; font-size:13px; color:#666;">⭐ {pro.get('rating', 5.0)} | {pro.get('localizacao')}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if pro.get('saldo', 0) >= TAXA_LEAD:
                    if st.button(f"CONTATAR {pro.get('nome').split()[0].upper()}", key=f"c_{pro['id']}"):
                        db.collection("profissionais").document(pro['id']).update({
                            "saldo": firestore.Increment(-TAXA_LEAD),
                            "cliques": firestore.Increment(1)
                        })
                        st.markdown(f'<a href="https://wa.me/55{pro.get("whatsapp")}" class="btn-wpp">CONVERSAR NO WHATSAPP</a>', unsafe_allow_html=True)
                else:
                    st.error("Este profissional excedeu o limite de hoje.")

# --- ABA 2: O PROFISSIONAL (FINANCEIRO E DASHBOARD) ---
with ABAS[1]:
    st.subheader("Login do Parceiro")
    l_zap = st.text_input("WhatsApp (Login)")
    l_sen = st.text_input("Senha", type="password")
    
    if l_zap and l_sen:
        doc_ref = db.collection("profissionais").document(l_zap).get()
        if doc_ref.exists and doc_ref.to_dict().get('senha') == l_sen:
            p_data = doc_ref.to_dict()
            st.success(f"Bem-vindo, {p_data.get('nome')}!")
            
            c1, c2, c3 = st.columns(3)
            c1.markdown(f'<div class="metric-box"><small>SALDO</small><br><b style="font-size:25px;">{p_data.get("saldo")}</b></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="metric-box" style="background:#FF8C00;"><small>CLIQUES</small><br><b style="font-size:25px;">{p_data.get("cliques")}</b></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="metric-box" style="background:#28A745;"><small>NOTA</small><br><b style="font-size:25px;">{p_data.get("rating")}</b></div>', unsafe_allow_html=True)
            
            st.divider()
            st.write("### 💰 Recarregar Moedas")
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={PIX_OFICIAL}")
            st.code(f"PIX: {PIX_OFICIAL}")
            st.markdown(f'<a href="https://wa.me/{ZAP_ADMIN}?text=Fiz o PIX de recarga para: {l_zap}" class="btn-wpp">ENVIAR COMPROVANTE</a>', unsafe_allow_html=True)
        else: st.error("Dados de acesso incorretos.")

# --- ABA 3: CADASTRO (COM GPS OBRIGATÓRIO) ---
with ABAS[2]:
    with st.form("reg_form"):
        st.write("### ✍️ Faça seu Cadastro")
        r_nome = st.text_input("Nome Completo")
        r_zap = st.text_input("WhatsApp com DDD (Somente números)")
        r_senha = st.text_input("Crie uma Senha", type="password")
        r_bairro = st.text_input("Bairro/Cidade Principal")
        st.info("📍 Informe sua localização GPS para ser encontrado:")
        col_r1, col_r2 = st.columns(2)
        r_lat = col_r1.number_input("Latitude", value=-23.5, format="%.5f")
        r_lon = col_r2.number_input("Longitude", value=-46.6, format="%.5f")
        r_desc = st.text_area("Descreva seus serviços (IA vai te classificar)")
        
        if st.form_submit_button("CADASTRAR MEU PERFIL"):
            if len(r_zap) < 10: st.error("WhatsApp inválido.")
            else:
                cat_gerada = classificar_servico(r_desc)
                db.collection("profissionais").document(r_zap).set({
                    "nome": r_nome, "whatsapp": r_zap, "senha": r_senha,
                    "area": cat_gerada, "localizacao": r_bairro,
                    "lat": r_lat, "lon": r_lon, "saldo": BONUS_CADASTRO,
                    "aprovado": False, "cliques": 0, "rating": 5.0, "descricao": r_desc
                })
                st.success(f"Cadastro realizado como {cat_gerada}! Fale com o admin para liberar.")
                st.markdown(f'<a href="https://wa.me/{ZAP_ADMIN}?text=Quero aprovação: {r_nome}" class="btn-wpp">AVISAR ADMIN</a>', unsafe_allow_html=True)

# --- ABA 4: O ADMIN (CONTROLE TOTAL RECUPERADO) ---
with ABAS[3]:
    if st.text_input("Master Key", type="password") == CHAVE_ADMIN:
        st.subheader("🛡️ Gestão Estratégica")
        
        # 1. Auditoria de Dados
        if st.button("🔄 EXECUTAR AUDITORIA DE SEGURANÇA", use_container_width=True):
            all_p = db.collection("profissionais").stream()
            for doc in all_p:
                d = doc.to_dict()
                u = {}
                if "saldo" not in d: u["saldo"] = BONUS_CADASTRO
                if "cliques" not in d: u["cliques"] = 0
                if "aprovado" not in d: u["aprovado"] = False
                if u: db.collection("profissionais").document(doc.id).update(u)
            st.success("Banco de dados sincronizado!")

        st.divider()
        # 2. Lista de Profissionais
        busca_adm = st.text_input("Buscar Profissional (Nome ou Zap)")
        docs_adm = db.collection("profissionais").stream()
        
        for d_adm in docs_adm:
            p_adm = d_adm.to_dict()
            pid = d_adm.id
            if busca_adm.lower() in p_adm.get('nome').lower() or busca_adm in pid:
                status = "✅" if p_adm.get('aprovado') else "⏳"
                with st.expander(f"{status} {p_adm.get('nome')} | Moedas: {p_adm.get('saldo')}"):
                    # Controles de Saldo e Aprovação
                    c_a1, c_a2, c_a3 = st.columns(3)
                    if c_a1.button("APROVAR", key=f"ok_{pid}"):
                        db.collection("profissionais").document(pid).update({"aprovado": True})
                        st.rerun()
                    if c_a2.button("+10 MOEDAS", key=f"m_{pid}"):
                        db.collection("profissionais").document(pid).update({"saldo": firestore.Increment(10)})
                        st.rerun()
                    if c_a3.button("EXCLUIR", key=f"del_{pid}"):
                        db.collection("profissionais").document(pid).delete()
                        st.rerun()
                    
                    # Troca de Senha (RECUPERADA)
                    st.write("---")
                    nova_senha = st.text_input("Redefinir Senha", key=f"pw_{pid}")
                    if st.button("SALVAR SENHA", key=f"bp_{pid}"):
                        db.collection("profissionais").document(pid).update({"senha": nova_senha})
                        st.success("Senha alterada com sucesso!")

st.markdown("<br><hr><center><small>GeralJá v16.0 | Engine de Alta Performance 2025</small></center>", unsafe_allow_html=True)

