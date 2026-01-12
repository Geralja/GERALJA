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

# ==============================================================================
# 1. CONFIGURAÇÃO DE AMBIENTE E SEGURANÇA (UTF-8 FIX)
# ==============================================================================
st.set_page_config(
    page_title="GeralJá | Criando Soluções",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

@st.cache_resource
def conectar_banco_blindado():
    """Conecta ao Firebase resolvendo erros de padding e encoding utf-8"""
    if not firebase_admin._apps:
        try:
            if "FIREBASE_BASE64" not in st.secrets:
                st.error("🔑 Chave FIREBASE_BASE64 não encontrada.")
                return None
            
            b64_key = st.secrets["FIREBASE_BASE64"].strip()
            # Correção de Padding para evitar erro de binário
            missing_padding = len(b64_key) % 4
            if missing_padding:
                b64_key += '=' * (4 - missing_padding)
            
            # Decodificação segura garantindo UTF-8 e ignorando resíduos
            decoded_json = base64.b64decode(b64_key).decode("utf-8", errors="ignore")
            cred_dict = json.loads(decoded_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            return firestore.client()
        except Exception as e:
            st.error(f"❌ Erro Crítico: {e}")
            return None
    return firestore.client()

db = conectar_banco_blindado()

# ==============================================================================
# 2. FUNÇÕES MOTORAS (BLINDADAS)
# ==============================================================================
def normalizar(t):
    """Remove acentos e padroniza texto para busca."""
    if not t: return ""
    return "".join(c for c in unicodedata.normalize('NFD', str(t)) if unicodedata.category(c) != 'Mn').lower()

def criar_link_zap(tel, nome_p):
    """Gera link direto para o WhatsApp com mensagem pronta."""
    num = re.sub(r'\D', '', str(tel))
    msg = quote(f"Olá {nome_p}, vi o seu perfil no GeralJá e gostaria de um orçamento!")
    return f"https://wa.me/{num}?text={msg}"

def converter_img_b64(file):
    """Converte upload de imagem para string segura para o banco."""
    if file:
        return base64.b64encode(file.getvalue()).decode()
    return ""

# ==============================================================================
# 3. UI STYLE: GOOGLE MINIMALIST + SOCIAL VITRINE
# ==============================================================================
st.markdown("""
    <style>
    .stApp { background-color: white !important; }
    
    /* Barra de Busca Estilo Google */
    div.stTextInput > div > div > input {
        border-radius: 24px !important; border: 1px solid #dfe1e5 !important;
        padding: 12px 25px !important; transition: 0.3s;
    }
    div.stTextInput > div > div > input:focus { box-shadow: 0 1px 6px rgba(32,33,36,0.28) !important; }
    
    /* Vitrine Estilo Rede Social */
    .social-card {
        border: 1px solid #f0f2f6; border-radius: 15px; padding: 20px;
        margin-bottom: 20px; background: #fff; transition: 0.3s;
    }
    .social-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); transform: translateY(-2px); }
    .profile-pic { width: 70px; height: 70px; border-radius: 50%; object-fit: cover; border: 2px solid #4285F4; }
    .badge-elite { background: #FF8C00; color: white; padding: 2px 12px; border-radius: 20px; font-size: 11px; font-weight: bold; }
    
    /* Rodapé Varredor */
    .footer-clean {
        text-align: center; padding: 40px; color: #64748B; 
        background: #F8FAFC; border-radius: 20px; margin-top: 50px;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. SISTEMA DE NAVEGAÇÃO E ESTADOS
# ==============================================================================
if 'page' not in st.session_state: st.session_state.page = 'home'
if 'query' not in st.session_state: st.session_state.query = ""

# Top Nav
col_t1, col_t2 = st.columns([8, 1])
with col_t2:
    if st.button("⚙️ Admin"): 
        st.session_state.page = 'admin'
        st.rerun()

# ------------------------------------------------------------------------------
# VIEW: HOME
# ------------------------------------------------------------------------------
if st.session_state.page == 'home':
    st.write("##")
    st.markdown("<h1 style='text-align: center; font-size: 85px; color:#4285F4; font-family: sans-serif; letter-spacing: -4px;'>GeralJá</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        q = st.text_input("", placeholder="Pesquise por serviço ou profissional", key="main_q")
        st.write("##")
        b1, b2, b3, b4, b5 = st.columns(5)
        with b2:
            if st.button("Buscar", use_container_width=True) or q:
                if q:
                    st.session_state.query = q
                    st.session_state.page = 'resultados'
                    st.rerun()
        with b4:
            if st.button("Anunciar", use_container_width=True):
                st.session_state.page = 'cadastro'
                st.rerun()

# ------------------------------------------------------------------------------
# VIEW: RESULTADOS (VITRINE SOCIAL)
# ------------------------------------------------------------------------------
elif st.session_state.page == 'resultados':
    t1, t2 = st.columns([1, 5])
    with t1: 
        if st.button("← Voltar"): st.session_state.page = 'home'; st.rerun()
    
    st.markdown(f"### Resultados para: **{st.session_state.query}**")
    
    if db:
        docs = db.collection("profissionais").where("aprovado", "==", True).stream()
        lista = [d.to_dict() for d in docs]
        termo_busca = normalizar(st.session_state.query)
        
        filtrados = [p for p in lista if termo_busca in normalizar(p.get('categoria')) or termo_busca in normalizar(p.get('nome'))]
        filtrados = sorted(filtrados, key=lambda x: (x.get('elite', False), x.get('nota', 0)), reverse=True)

        for p in filtrados:
            st.markdown('<div class="social-card">', unsafe_allow_html=True)
            c1, c2, c3 = st.columns([0.8, 3, 1.2])
            with c1:
                foto = p.get('foto_b64', "")
                if foto:
                    st.markdown(f'<img src="data:image/png;base64,{foto}" class="profile-pic">', unsafe_allow_html=True)
                else:
                    st.markdown(f'<img src="https://ui-avatars.com/api/?name={p.get("nome")}" class="profile-pic">', unsafe_allow_html=True)
            with c2:
                elite = "<span class='badge-elite'>ELITE</span>" if p.get('elite') else ""
                st.markdown(f"**{p.get('nome')}** {elite}")
                st.caption(f"{p.get('categoria')} • ⭐ {p.get('nota')} • {p.get('bairro', 'SP')}")
                st.write(p.get('descricao', ''))
            with c3:
                st.write("##")
                link = criar_link_zap(p.get('telefone'), p.get('nome'))
                st.link_button("💬 WHATSAPP", link, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# VIEW: ADMIN (COFRE BLINDADO)
# ------------------------------------------------------------------------------
elif st.session_state.page == 'admin':
    if st.button("← Sair"): st.session_state.page = 'home'; st.rerun()
    st.title("🛡️ Painel Admin")
    
    senha = st.text_input("Chave Mestra para confirmação", type="password")
    if senha == "riqueza2026":
        st.success("Acesso Autorizado.")
        aba1, aba2 = st.tabs(["💰 Financeiro", "📋 Aprovações"])
        
        with aba1:
            all_p = list(db.collection("profissionais").stream())
            dados = [p.to_dict() for p in all_p]
            df = pd.DataFrame(dados)
            st.metric("FATURAMENTO TOTAL", f"R$ {df['total_comprado'].sum():,.2f}")
            st.dataframe(df[['nome', 'categoria', 'total_comprado', 'elite']])
            
        with aba2:
            pendentes = db.collection("profissionais").where("aprovado", "==", False).stream()
            for doc in pendentes:
                p = doc.to_dict()
                c_a, c_b = st.columns([4, 1])
                c_a.write(f"**{p.get('nome')}** ({p.get('categoria')})")
                if c_b.button("✅ Aprovar", key=doc.id):
                    db.collection("profissionais").document(doc.id).update({"aprovado": True})
                    st.rerun()
    else:
        st.info("Insira a senha para ver dados de faturamento e aprovações.")

# ------------------------------------------------------------------------------
# VIEW: CADASTRO
# ------------------------------------------------------------------------------
elif st.session_state.page == 'cadastro':
    if st.button("← Cancelar"): st.session_state.page = 'home'; st.rerun()
    st.subheader("💼 Cadastro de Profissional")
    with st.form("cad"):
        nome = st.text_input("Seu Nome")
        cat = st.selectbox("Categoria", ["Encanador", "Eletricista", "Diarista", "Mecânico", "Outros"])
        tel = st.text_input("WhatsApp (ex: 5511999999999)")
        desc = st.text_area("Descrição do seu serviço")
        foto = st.file_uploader("Foto de Perfil", type=['jpg', 'png'])
        if st.form_submit_button("CADASTRAR"):
            foto_b64 = converter_img_b64(foto)
            db.collection("profissionais").add({
                "nome": nome, "categoria": cat, "telefone": tel, "descricao": desc,
                "foto_b64": foto_b64, "aprovado": False, "elite": False, "nota": 5.0,
                "total_comprado": 0, "bairro": "São Paulo"
            })
            st.balloons()
            st.success("Cadastro enviado para aprovação!")

# ==============================================================================
# 5. RODAPÉ PODEROSO (VARREDURA)
# ==============================================================================
st.markdown(f"""
    <div class="footer-clean">
        <p style="margin:0; font-weight: bold;">🎯 GERALJÁ v20.0</p>
        <p style="margin:5px; font-size: 13px;">Sistema Blindado • Firestore Cloud • © {datetime.datetime.now().year}</p>
        <div style="margin-top: 15px; font-size: 11px; opacity: 0.5;">
            São Paulo, Brasil • Inteligência Local para Soluções Rápidas.
        </div>
    </div>
""", unsafe_allow_html=True)
