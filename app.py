# ==============================================================================
# GERALJÁ SP - ULTIMATE EDITION v18.0 (PROFISSIONAL + EDITÁVEL + IA)
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

# 1. CONFIGURAÇÃO DE ALTA PERFORMANCE
st.set_page_config(
    page_title="GeralJá | Profissionais de São Paulo",
    page_icon="🛠️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. CONEXÃO BLINDADA AO FIREBASE
@st.cache_resource
def init_infra():
    if not firebase_admin._apps:
        try:
            b64_key = st.secrets["FIREBASE_BASE64"]
            decoded_json = base64.decodebytes(b64_key.encode()).decode("utf-8")
            cred = credentials.Certificate(json.loads(decoded_json))
            return firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Erro Crítico de Banco de Dados: {e}")
            st.stop()
    return firebase_admin.get_app()

init_infra()
db = firestore.client()

# 3. REGRAS DE NEGÓCIO E CONSTANTES
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ADMIN = "mumias"
TAXA_LEAD = 1
BONUS_NOVO = 5
LAT_SP = -23.5505
LON_SP = -46.6333

# 4. MOTOR DE INTELIGÊNCIA ARTIFICIAL (MAPEAMENTO)
MAPA_IA = {
    "vazamento": "Encanador", "chuveiro": "Eletricista", "pintura": "Pintor",
    "faxina": "Diarista", "mudança": "Fretes", "unha": "Manicure",
    "carro": "Mecânico", "computador": "TI", "reforma": "Pedreiro",
    "gesso": "Gesseiro", "telhado": "Telhadista", "jardim": "Jardineiro",
    "limpeza": "Diarista", "esgoto": "Encanador", "fiação": "Eletricista"
}

def classificar_ia(texto):
    t = texto.lower() if texto else ""
    for k, v in MAPA_IA.items():
        if k in t: return v
    return "Ajudante Geral"

def calcular_km(lat1, lon1, lat2, lon2):
    if None in [lat1, lon1, lat2, lon2]: return 99.9
    R = 6371
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)

# 5. ESTILIZAÇÃO PREMIUM
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap');
    * { font-family: 'Montserrat', sans-serif; }
    .stApp { background-color: #F4F7F9; }
    .main-logo { text-align: center; padding: 30px; background: #FFF; border-radius: 0 0 50px 50px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); }
    .azul { color: #0047AB; font-weight: 900; font-size: 50px; }
    .laranja { color: #FF8C00; font-weight: 900; font-size: 50px; }
    .card-pro { 
        background: white; border-radius: 20px; padding: 20px; margin-bottom: 15px;
        border-left: 10px solid #0047AB; box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        display: flex; align-items: center;
    }
    .img-perfil { width: 80px; height: 80px; border-radius: 50%; object-fit: cover; margin-right: 20px; border: 2px solid #0047AB; }
    .btn-wpp { background: #25D366; color: white !important; padding: 12px; border-radius: 10px; text-decoration: none; font-weight: 700; display: block; text-align: center; }
    .metric-card { background: #0047AB; color: white; padding: 15px; border-radius: 15px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-logo"><span class="azul">GERAL</span><span class="laranja">JÁ</span><br><small>SÃO PAULO PROFISSIONAL</small></div>', unsafe_allow_html=True)

# 6. NAVEGAÇÃO POR ABAS
Abas = st.tabs(["🔍 BUSCAR", "👤 MEU PERFIL", "✍️ CADASTRAR", "🛡️ ADMIN"])

# ------------------------------------------------------------------------------
# ABA 1: CLIENTE (BUSCA GPS)
# ------------------------------------------------------------------------------
with Abas[0]:
    st.write("### 📍 Encontre um profissional perto de você")
    busca = st.text_input("O que você precisa hoje?", placeholder="Ex: Preciso de um pintor para minha sala")
    raio_km = st.slider("Distância máxima (km)", 1, 50, 15)
    
    if busca:
        cat = classificar_ia(busca)
        st.info(f"Buscando por: **{cat}** em um raio de {raio_km}km")
        
        # Query Otimizada
        docs = db.collection("profissionais").where("area", "==", cat).where("aprovado", "==", True).stream()
        
        resultados = []
        for d in docs:
            p = d.to_dict()
            p['id'] = d.id
            dist = calcular_km(LAT_SP, LON_SP, p.get('lat', LAT_SP), p.get('lon', LON_SP))
            if dist <= raio_km:
                p['dist'] = dist
                resultados.append(p)
        
        resultados.sort(key=lambda x: x['dist'])
        
        if not resultados:
            st.warning("Nenhum profissional encontrado tão próximo. Tente aumentar o raio de busca.")
        else:
            for pro in resultados:
                with st.container():
                    st.markdown(f"""
                    <div class="card-pro">
                        <img src="{pro.get('foto_url') or 'https://cdn-icons-png.flaticon.com/512/3135/3135715.png'}" class="img-perfil">
                        <div style="flex-grow:1;">
                            <b style="font-size:18px;">{pro['nome'].upper()}</b><br>
                            <small>📍 {pro['dist']} km de você | ⭐ {pro.get('rating', 5.0)}</small><br>
                            <span style="color:#666; font-size:13px;">{pro.get('localizacao', 'São Paulo')}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if pro.get('saldo', 0) >= TAXA_LEAD:
                        if st.button(f"SOLICITAR ORÇAMENTO DE {pro['nome'].split()[0]}", key=f"btn_{pro['id']}"):
                            db.collection("profissionais").document(pro['id']).update({
                                "saldo": firestore.Increment(-TAXA_LEAD),
                                "cliques": firestore.Increment(1)
                            })
                            st.markdown(f'<a href="https://wa.me/55{pro["whatsapp"]}?text=Olá, vi seu perfil no GeralJá!" class="btn-wpp">ABRIR WHATSAPP</a>', unsafe_allow_html=True)
                    else:
                        st.error("Este profissional não pode receber novos contatos no momento.")

# ------------------------------------------------------------------------------
# ABA 2: PROFISSIONAL (LOGIN + EDIÇÃO)
# ------------------------------------------------------------------------------
with Abas[1]:
    if 'user' not in st.session_state:
        st.subheader("Acesse sua conta")
        lg_zap = st.text_input("WhatsApp (Login)")
        lg_sen = st.text_input("Senha", type="password")
        if st.button("ENTRAR"):
            doc = db.collection("profissionais").document(lg_zap).get()
            if doc.exists and doc.to_dict().get('senha') == lg_sen:
                st.session_state.user = doc.to_dict()
                st.session_state.uid = lg_zap
                st.rerun()
            else: st.error("Dados inválidos.")
    else:
        u = st.session_state.user
        uid = st.session_state.uid
        st.success(f"Bem-vindo, {u['nome']}!")
        
        # DASHBOARD FINANCEIRO
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="metric-card"><small>SALDO</small><br><b>{u.get("saldo", 0)}</b></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card" style="background:#FF8C00;"><small>CLIQUES</small><br><b>{u.get("cliques", 0)}</b></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card" style="background:#28A745;"><small>NOTA</small><br><b>{u.get("rating", 5.0)}</b></div>', unsafe_allow_html=True)

        st.divider()
        st.write("### 📝 Editar Meu Perfil")
        with st.form("edit_perfil"):
            ed_nome = st.text_input("Nome Profissional", value=u.get('nome'))
            ed_desc = st.text_area("Descrição (IA usa isso para te classificar)", value=u.get('descricao', ''))
            ed_foto = st.text_input("Link da Foto (URL)", value=u.get('foto_url', ''))
            ed_bairro = st.text_input("Bairro/Cidade", value=u.get('localizacao', ''))
            
            st.write("📍 Localização GPS (Para ser achado no mapa)")
            col_la, col_lo = st.columns(2)
            ed_lat = col_la.number_input("Latitude", value=float(u.get('lat', LAT_SP)), format="%.5f")
            ed_lon = col_lo.number_input("Longitude", value=float(u.get('lon', LON_SP)), format="%.5f")
            
            if st.form_submit_button("SALVAR ALTERAÇÕES"):
                nova_area = class_ia(ed_desc)
                upd = {
                    "nome": ed_nome, "descricao": ed_desc, "foto_url": ed_foto,
                    "localizacao": ed_bairro, "lat": ed_lat, "lon": ed_lon, "area": nova_area
                }
                db.collection("profissionais").document(uid).update(upd)
                st.success("Perfil Atualizado! Relogando...")
                del st.session_state.user
                time.sleep(1)
                st.rerun()

        if st.button("SAIR DA CONTA"):
            del st.session_state.user
            st.rerun()

# ------------------------------------------------------------------------------
# ABA 3: CADASTRO INICIAL
# ------------------------------------------------------------------------------
with Abas[2]:
    st.subheader("Seja um Parceiro")
    with st.form("cad_novo"):
        n_nome = st.text_input("Nome Completo")
        n_zap = st.text_input("WhatsApp (apenas números)")
        n_sen = st.text_input("Crie uma Senha", type="password")
        n_desc = st.text_area("O que você faz? (Ex: Sou encanador e eletricista)")
        
        if st.form_submit_button("CADASTRAR"):
            if len(n_zap) < 10: st.error("WhatsApp inválido.")
            else:
                cat_gerada = classificar_ia(n_desc)
                db.collection("profissionais").document(n_zap).set({
                    "nome": n_nome, "whatsapp": n_zap, "senha": n_sen,
                    "descricao": n_desc, "area": cat_gerada, "saldo": BONUS_NOVO,
                    "aprovado": False, "cliques": 0, "rating": 5.0,
                    "lat": LAT_SP, "lon": LON_SP, "localizacao": "São Paulo"
                })
                st.success(f"Cadastrado como {cat_gerada}! Aguarde aprovação.")
                st.markdown(f'<a href="https://wa.me/{ZAP_ADMIN}?text=Quero aprovação: {n_nome}" class="btn-wpp">AVISAR ADMIN</a>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# ABA 4: ADMIN MASTER
# ------------------------------------------------------------------------------
with Abas[3]:
    if st.text_input("Chave Mestra", type="password") == CHAVE_ADMIN:
        st.subheader("🛡️ Painel de Controle")
        
        # Auditoria rápida
        if st.button("🔄 CORRIGIR BANCO DE DADOS"):
            all_p = db.collection("profissionais").stream()
            for doc in all_p:
                d = doc.to_dict()
                if "saldo" not in d: db.collection("profissionais").document(doc.id).update({"saldo": 5, "cliques": 0, "aprovado": False})
            st.success("Banco Sincronizado!")

        search_adm = st.text_input("Buscar Profissional (Nome/Zap)")
        docs_adm = db.collection("profissionais").stream()
        
        for d_adm in docs_adm:
            p_adm = d_adm.to_dict()
            pid = d_adm.id
            if not search_adm or search_adm.lower() in p_adm['nome'].lower() or search_adm in pid:
                cor = "green" if p_adm['aprovado'] else "red"
                with st.expander(f"[{p_adm['area']}] {p_adm['nome']} - Saldo: {p_adm['saldo']}"):
                    st.write(f"WhatsApp: {pid}")
                    st.write(f"Descrição: {p_adm.get('descricao')}")
                    
                    c_a, c_b, c_c = st.columns(3)
                    if c_a.button("APROVAR", key=f"ap_{pid}"):
                        db.collection("profissionais").document(pid).update({"aprovado": True})
                        st.rerun()
                    if c_b.button("+10 MOEDAS", key=f"mo_{pid}"):
                        db.collection("profissionais").document(pid).update({"saldo": firestore.Increment(10)})
                        st.rerun()
                    if c_c.button("DELETAR", key=f"del_{pid}"):
                        db.collection("profissionais").document(pid).delete()
                        st.rerun()
                    
                    nova_sen_adm = st.text_input("Resetar Senha", key=f"rs_{pid}")
                    if st.button("SALVAR SENHA", key=f"brs_{pid}"):
                        db.collection("profissionais").document(pid).update({"senha": nova_sen_adm})
                        st.success("Senha Alterada!")

st.markdown("<br><hr><center><small>GeralJá v18.0 | High Performance 2025</small></center>", unsafe_allow_html=True)


