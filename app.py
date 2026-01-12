import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime
import math
import re
import unicodedata
import pandas as pd
from urllib.parse import quote
from streamlit_js_eval import get_geolocation

# ==============================================================================
# 1. NÚCLEO DE SEGURANÇA E CONEXÃO (FIX UTF-8)
# ==============================================================================
st.set_page_config(page_title="GeralJá | Brasil", page_icon="🎯", layout="wide", initial_sidebar_state="collapsed")

@st.cache_resource
def conectar_banco_blindado():
    """Conecta ao Firebase blindando contra erros de encoding e padding."""
    if not firebase_admin._apps:
        try:
            if "FIREBASE_BASE64" not in st.secrets:
                st.error("🔑 Erro: Chave FIREBASE_BASE64 não configurada nos Secrets.")
                return None
            
            b64_key = st.secrets["FIREBASE_BASE64"].strip()
            # Resolve o erro de padding do base64
            missing_padding = len(b64_key) % 4
            if missing_padding:
                b64_key += '=' * (4 - missing_padding)
            
            # Decode forçando utf-8 e ignorando sujeira binária
            decoded_json = base64.b64decode(b64_key).decode("utf-8", errors="ignore")
            cred_dict = json.loads(decoded_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            return firestore.client()
        except Exception as e:
            st.error(f"❌ Erro na Conexão Firebase: {e}")
            return None
    return firestore.client()

db = conectar_banco_blindado()

# ==============================================================================
# 2. FUNÇÕES MOTORAS (NÃO REMOVER NADA)
# ==============================================================================
def normalizar(t):
    return "".join(c for c in unicodedata.normalize('NFD', str(t)) if unicodedata.category(c) != 'Mn').lower()

def criar_link_zap(tel, nome_p):
    num = re.sub(r'\D', '', str(tel))
    msg = quote(f"Olá {nome_p}, vi seu perfil no GeralJá e gostaria de um orçamento!")
    return f"https://wa.me/{num}?text={msg}"

def converter_img_b64(file):
    if file:
        return base64.b64encode(file.getvalue()).decode()
    return ""

# ==============================================================================
# 3. ESTILIZAÇÃO MESTRE (GOOGLE + SOCIAL MEDIA)
# ==============================================================================
st.markdown("""
    <style>
    .stApp { background-color: white !important; }
    /* Busca Estilo Google */
    div.stTextInput > div > div > input {
        border-radius: 24px !important; border: 1px solid #dfe1e5 !important;
        padding: 12px 25px !important; font-size: 16px;
    }
    /* Vitrine Social */
    .card-social {
        border-radius: 15px; border: 1px solid #E2E8F0; padding: 15px;
        margin-bottom: 15px; background: white; transition: 0.3s;
    }
    .card-social:hover { box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    .img-perfil { width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 2px solid #4285F4; }
    .badge-elite { background: #FF8C00; color: white; padding: 2px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. SISTEMA DE NAVEGAÇÃO BOLDADO
# ==============================================================================
if 'view' not in st.session_state: st.session_state.view = 'home'
if 'query' not in st.session_state: st.session_state.query = ""

# Barra de topo discreta
c_top1, c_top2 = st.columns([9, 1])
with c_top2:
    if st.button("⚙️ Admin"): st.session_state.view = 'admin'; st.rerun()

# ------------------------------------------------------------------------------
# VIEW: HOME (ESTILO GOOGLE)
# ------------------------------------------------------------------------------
if st.session_state.view == 'home':
    st.write("##")
    st.markdown("<h1 style='text-align: center; font-size: 90px; color:#4285F4; font-family: sans-serif; letter-spacing: -5px;'>GeralJá</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        busca = st.text_input("", placeholder="O que você precisa resolver hoje?", key="main_search")
        st.write("##")
        b1, b2, b3, b4, b5 = st.columns(5)
        with b2:
            if st.button("Buscar Agora", use_container_width=True) or busca:
                if busca:
                    st.session_state.query = busca
                    st.session_state.view = 'resultados'; st.rerun()
        with b4:
            if st.button("Trabalhe Conosco", use_container_width=True):
                st.session_state.view = 'cadastro'; st.rerun()

# ------------------------------------------------------------------------------
# VIEW: RESULTADOS (VITRINE REDE SOCIAL)
# ------------------------------------------------------------------------------
elif st.session_state.view == 'resultados':
    t1, t2 = st.columns([1, 5])
    with t1:
        if st.button("← Voltar"): st.session_state.view = 'home'; st.rerun()
    
    st.markdown(f"### Mostrando resultados para: **{st.session_state.query}**")
    
    if db:
        # Puxa apenas aprovados (Blindagem de dados)
        docs = db.collection("profissionais").where("aprovado", "==", True).stream()
        lista = [d.to_dict() for d in docs]
        termo = normalizar(st.session_state.query)
        
        # Filtro de Inteligência Local
        filtrados = [p for p in lista if termo in normalizar(p.get('categoria','')) or termo in normalizar(p.get('nome',''))]
        filtrados = sorted(filtrados, key=lambda x: (x.get('elite', False), x.get('nota', 0)), reverse=True)

        if not filtrados:
            st.info("Nenhum resultado exato. Tente buscar por 'vazamento', 'eletricista' ou 'limpeza'.")
        
        for p in filtrados:
            with st.container():
                st.markdown('<div class="card-social">', unsafe_allow_html=True)
                c1, c2, c3 = st.columns([0.8, 3, 1.2])
                with c1:
                    foto = p.get('foto_b64', "")
                    if len(foto) > 100:
                        st.markdown(f'<img src="data:image/png;base64,{foto}" class="img-perfil">', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<img src="https://ui-avatars.com/api/?name={p.get("nome")}&background=random" class="img-perfil">', unsafe_allow_html=True)
                with c2:
                    elite = "<span class='badge-elite'>ELITE</span>" if p.get('elite') else ""
                    st.markdown(f"#### {p.get('nome')} {elite}")
                    st.caption(f"📍 {p.get('bairro', 'Atendimento Local')} • ⭐ {p.get('nota', '5.0')}")
                    st.write(f"{p.get('descricao')}")
                with c3:
                    st.write("##")
                    url_zap = criar_link_zap(p.get('telefone'), p.get('nome'))
                    st.link_button("🔥 CHAMAR NO ZAP", url_zap, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# VIEW: ADMIN (PODERES TOTAIS + COFRE)
# ------------------------------------------------------------------------------
elif st.session_state.view == 'admin':
    if st.button("← Sair do Painel"): st.session_state.view = 'home'; st.rerun()
    st.title("🛡️ Centro de Comando GeralJá")
    
    acesso = st.text_input("Confirmação de Senha Mestra", type="password")
    if acesso == "riqueza2026":
        st.success("Acesso Liberado, Comandante.")
        aba1, aba2, aba3 = st.tabs(["📊 BI & Faturamento", "📋 Aprovar Parceiros", "💬 Feedbacks"])
        
        with aba1:
            profs_all = list(db.collection("profissionais").stream())
            df = pd.DataFrame([p.to_dict() for p in profs_all])
            col_m1, col_m2 = st.columns(2)
            col_m1.metric("Faturamento Real", f"R$ {df['total_comprado'].sum():,.2f}")
            col_m2.metric("Base de Usuários", len(profs_all))
            st.dataframe(df[["nome", "categoria", "total_comprado", "aprovado"]])

        with aba2:
            pendentes = db.collection("profissionais").where("aprovado", "==", False).stream()
            for doc in pendentes:
                p_data = doc.to_dict()
                c_a, c_b = st.columns([4, 1])
                c_a.write(f"**{p_data.get('nome')}** | {p_data.get('categoria')}")
                if c_b.button("✅ APROVAR", key=doc.id):
                    db.collection("profissionais").document(doc.id).update({"aprovado": True})
                    st.rerun()
    else:
        st.warning("Aguardando senha para descriptografar dados...")

# ------------------------------------------------------------------------------
# VIEW: CADASTRO
# ------------------------------------------------------------------------------
elif st.session_state.view == 'cadastro':
    if st.button("← Voltar"): st.session_state.view = 'home'; st.rerun()
    st.title("🚀 Seja um Parceiro Elite")
    with st.form("form_registro"):
        nome = st.text_input("Nome Profissional")
        cat = st.selectbox("Sua Especialidade", ["Encanador", "Eletricista", "Diarista", "Mecânico", "Pizzaria", "Outros"])
        tel = st.text_input("WhatsApp com DDD (Só números)")
        desc = st.text_area("Sua vitrine (O que você faz de melhor?)")
        foto = st.file_uploader("Sua Foto de Perfil", type=['jpg', 'png'])
        if st.form_submit_button("SOLICITAR ENTRADA NO GERALJÁ"):
            foto_b64 = converter_img_b64(foto)
            db.collection("profissionais").add({
                "nome": nome, "categoria": cat, "telefone": tel, "descricao": desc,
                "foto_b64": foto_b64, "aprovado": False, "elite": False, "nota": 5.0,
                "total_comprado": 0, "bairro": "São Paulo"
            })
            st.balloons()
            st.success("Pronto! Seu perfil foi para a mesa do Admin para aprovação.")

# ==============================================================================
# 5. RODAPÉ PODEROSO DE VARREDURA
# ==============================================================================
st.write("---")
st.markdown(f"""
    <div style="text-align: center; padding: 40px; color: #64748B; background: #F8FAFC; border-radius: 20px;">
        <p style="margin:0; font-weight: bold; font-size: 16px;">🎯 GERALJÁ v20.0</p>
        <p style="margin:5px; font-size: 12px;">Sistema de Varredura de Inteligência Local • Blindagem UTF-8 • Firestore Cloud</p>
        <div style="margin-top: 15px; font-size: 11px; opacity: 0.6;">
            © {datetime.datetime.now().year} Criando Soluções Inteligentes para o Brasil.
        </div>
    </div>
""", unsafe_allow_html=True)
