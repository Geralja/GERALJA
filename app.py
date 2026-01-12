# ==============================================================================
# GERALJÁ: CRIANDO SOLUÇÕES - VERSÃO COMPLETA E BLINDADA
# ==============================================================================
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime
import math
import re
import pandas as pd
import unicodedata
from urllib.parse import quote

# ------------------------------------------------------------------------------
# 1. SEGURANÇA E CONEXÃO (RESOLUÇÃO DO ERRO 'utf-8')
# ------------------------------------------------------------------------------
st.set_page_config(page_title="GeralJá | Online", page_icon="🎯", layout="wide", initial_sidebar_state="collapsed")

@st.cache_resource
def conectar_banco_blindado():
    if not firebase_admin._apps:
        try:
            if "FIREBASE_BASE64" not in st.secrets:
                st.error("🔑 Erro: FIREBASE_BASE64 não configurado.")
                return None
            
            b64_key = st.secrets["FIREBASE_BASE64"].strip()
            # Correção de Padding para evitar erro de binário
            missing_padding = len(b64_key) % 4
            if missing_padding: b64_key += '=' * (4 - missing_padding)
            
            # Decode forçando utf-8 e ignorando erros de caracteres especiais
            decoded_json = base64.b64decode(b64_key).decode("utf-8", errors="ignore")
            cred_dict = json.loads(decoded_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            return firestore.client()
        except Exception as e:
            st.error(f"❌ Erro de Conexão: {e}")
            return None
    return firestore.client()

db = conectar_banco_blindado()

# ------------------------------------------------------------------------------
# 2. MOTOR DE FUNÇÕES (MANTENDO TUDO DO "GERALJA ONLINE.PY")
# ------------------------------------------------------------------------------
def normalizar(t):
    if not t: return ""
    return "".join(c for c in unicodedata.normalize('NFD', str(t)) if unicodedata.category(c) != 'Mn').lower()

def criar_link_zap(tel, nome_p):
    num = re.sub(r'\D', '', str(tel))
    msg = quote(f"Olá {nome_p}, vi seu perfil no GeralJá e gostaria de um orçamento!")
    return f"https://wa.me/{num}?text={msg}"

def converter_img_b64(file):
    if file: return base64.b64encode(file.getvalue()).decode()
    return ""

# ------------------------------------------------------------------------------
# 3. ESTILIZAÇÃO VITRINE SOCIAL & GOOGLE
# ------------------------------------------------------------------------------
st.markdown("""
    <style>
    .stApp { background-color: white !important; }
    /* Barra de Busca Google */
    div.stTextInput > div > div > input {
        border-radius: 24px !important; border: 1px solid #dfe1e5 !important;
        padding: 12px 25px !important;
    }
    /* Card Vitrine Social */
    .social-card {
        border-radius: 15px; border: 1px solid #E2E8F0; padding: 20px;
        margin-bottom: 20px; background: white; transition: 0.3s;
    }
    .social-card:hover { box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    .img-perfil { width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 2px solid #4285F4; }
    .badge-elite { background: #FF8C00; color: white; padding: 3px 12px; border-radius: 20px; font-size: 11px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 4. SISTEMA DE NAVEGAÇÃO POR ESTADO
# ------------------------------------------------------------------------------
if 'view' not in st.session_state: st.session_state.view = 'home'
if 'query' not in st.session_state: st.session_state.query = ""

# Botão Admin Invisível (Top Right)
c1, c2 = st.columns([9, 1])
with c2:
    if st.button("⚙️ Admin"): st.session_state.view = 'admin'; st.rerun()

# --- PÁGINA INICIAL (HOME) ---
if st.session_state.view == 'home':
    st.write("##")
    st.markdown("<h1 style='text-align: center; font-size: 90px; color:#4285F4; font-family: sans-serif; letter-spacing: -5px;'>GeralJá</h1>", unsafe_allow_html=True)
    
    col_h1, col_h2, col_h3 = st.columns([1, 2, 1])
    with col_h2:
        q = st.text_input("", placeholder="O que você procura hoje?", key="search_main")
        st.write("##")
        b1, b2, b3, b4, b5 = st.columns(5)
        with b2:
            if st.button("Buscar", use_container_width=True) or q:
                if q:
                    st.session_state.query = q
                    st.session_state.view = 'resultados'; st.rerun()
        with b4:
            if st.button("Sou Profissional", use_container_width=True):
                st.session_state.view = 'cadastro'; st.rerun()

# --- PÁGINA DE RESULTADOS (VITRINE) ---
elif st.session_state.view == 'resultados':
    if st.button("← Voltar"): st.session_state.view = 'home'; st.rerun()
    st.markdown(f"### 🔎 Resultados para: **{st.session_state.query}**")
    
    if db:
        profs = db.collection("profissionais").where("aprovado", "==", True).stream()
        lista = [p.to_dict() for p in profs]
        termo = normalizar(st.session_state.query)
        
        filtrados = [p for p in lista if termo in normalizar(p.get('categoria')) or termo in normalizar(p.get('nome'))]
        filtrados = sorted(filtrados, key=lambda x: (x.get('elite', False), x.get('nota', 0)), reverse=True)

        for p in filtrados:
            st.markdown('<div class="social-card">', unsafe_allow_html=True)
            col_v1, col_v2, col_v3 = st.columns([0.8, 3, 1.2])
            with col_v1:
                foto = p.get('foto_b64', "")
                if foto: st.markdown(f'<img src="data:image/png;base64,{foto}" class="img-perfil">', unsafe_allow_html=True)
                else: st.markdown(f'<img src="https://ui-avatars.com/api/?name={p.get("nome")}" class="img-perfil">', unsafe_allow_html=True)
            with col_v2:
                elite = "<span class='badge-elite'>ELITE</span>" if p.get('elite') else ""
                st.markdown(f"#### {p.get('nome')} {elite}")
                st.caption(f"{p.get('categoria')} • ⭐ {p.get('nota')} • {p.get('bairro', 'SP')}")
                st.write(p.get('descricao', ''))
            with col_v3:
                st.write("##")
                st.link_button("🚀 CONTACTAR AGORA", criar_link_zap(p.get('telefone'), p.get('nome')), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

# --- PAINEL ADMIN (COFRE & PODERES) ---
elif st.session_state.view == 'admin':
    if st.button("← Sair"): st.session_state.view = 'home'; st.rerun()
    st.title("🛡️ Painel de Gestão")
    
    senha = st.text_input("Confirme a Chave Mestra", type="password")
    if senha == "riqueza2026": # Sua senha do "Geralja online.py"
        tab1, tab2 = st.tabs(["💰 Financeiro", "📋 Pendentes"])
        
        with tab1:
            all_p = list(db.collection("profissionais").stream())
            df = pd.DataFrame([p.to_dict() for p in all_p])
            st.metric("FATURAMENTO TOTAL", f"R$ {df['total_comprado'].sum():,.2f}")
            st.dataframe(df[['nome', 'total_comprado', 'elite']])
            
        with tab2:
            pendentes = db.collection("profissionais").where("aprovado", "==", False).stream()
            for doc in pendentes:
                p = doc.to_dict()
                c_a, c_b = st.columns([4, 1])
                c_a.write(f"**{p.get('nome')}** solicita entrada.")
                if c_b.button("APROVAR", key=doc.id):
                    db.collection("profissionais").document(doc.id).update({"aprovado": True})
                    st.rerun()

# --- CADASTRO ---
elif st.session_state.view == 'cadastro':
    if st.button("← Cancelar"): st.session_state.view = 'home'; st.rerun()
    st.title("💼 Novo Parceiro")
    with st.form("cad_pro"):
        nome = st.text_input("Nome")
        cat = st.selectbox("Categoria", ["Encanador", "Eletricista", "Diarista", "Outros"])
        tel = st.text_input("WhatsApp (Só números)")
        desc = st.text_area("Descrição")
        foto = st.file_uploader("Sua Foto", type=['jpg', 'png'])
        if st.form_submit_button("CADASTRAR"):
            db.collection("profissionais").add({
                "nome": nome, "categoria": cat, "telefone": tel, "descricao": desc,
                "foto_b64": converter_img_b64(foto), "aprovado": False, "elite": False,
                "nota": 5.0, "total_comprado": 0, "bairro": "São Paulo"
            })
            st.success("Enviado! O Admin irá analisar.")

# ------------------------------------------------------------------------------
# 5. RODAPÉ VARREDOR (O "FINALIZADOR")
# ------------------------------------------------------------------------------
st.write("---")
st.markdown(f"""
    <div style="text-align: center; padding: 40px; color: #94A3B8; background: #F8FAFC; border-radius: 20px;">
        <p style="margin:0; font-weight: bold;">🎯 GERALJÁ v20.0</p>
        <p style="margin:5px; font-size: 12px;">Sistema de Inteligência Local Blindado • © {datetime.datetime.now().year}</p>
        <div style="margin-top: 15px; font-size: 11px; opacity: 0.5;">
            Varredura ativa: {len(list(db.collection("profissionais").stream())) if db else 0} profissionais monitorizados.
        </div>
    </div>
""", unsafe_allow_html=True)
