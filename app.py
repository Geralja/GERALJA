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
st.set_page_config(page_title="GeralJá | Brasil", page_icon="🎯", layout="wide", initial_sidebar_state="collapsed")

@st.cache_resource
def conectar_banco_blindado():
    """Conecta ao Firebase resolvendo erros de padding e encoding utf-8"""
    if not firebase_admin._apps:
        try:
            if "FIREBASE_BASE64" not in st.secrets:
                st.error("🔑 Chave FIREBASE_BASE64 não encontrada nos Secrets.")
                return None
            
            b64_key = st.secrets["FIREBASE_BASE64"].strip()
            # Correção de Padding para evitar erro de binário
            missing_padding = len(b64_key) % 4
            if missing_padding:
                b64_key += '=' * (4 - missing_padding)
            
            # Decodificação segura garantindo UTF-8
            decoded_json = base64.b64decode(b64_key).decode("utf-8", errors="ignore")
            cred_dict = json.loads(decoded_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            return firestore.client()
        except Exception as e:
            st.error(f"❌ Erro Crítico de Conexão: {e}")
            return None
    return firestore.client()

db = conectar_banco_blindado()

# ==============================================================================
# 2. FUNÇÕES MOTORAS (NÃO REMOVER NADA)
# ==============================================================================
def normalizar(t):
    return "".join(c for c in unicodedata.normalize('NFD', str(t)) if unicodedata.category(c) != 'Mn').lower()

def criar_link_zap(tel, nome_p):
    msg = quote(f"Olá {nome_p}, vi seu perfil no GeralJá e gostaria de um orçamento!")
    return f"https://wa.me/{str(tel).replace('+', '').replace(' ', '')}?text={msg}"

# ==============================================================================
# 3. UI STYLE: GOOGLE + REDE SOCIAL
# ==============================================================================
st.markdown("""
    <style>
    .stApp { background-color: white !important; }
    /* Estilo Barra de Busca Google */
    div.stTextInput > div > div > input {
        border-radius: 24px !important; border: 1px solid #dfe1e5 !important;
        padding: 12px 25px !important; transition: 0.3s;
    }
    div.stTextInput > div > div > input:focus { box-shadow: 0 1px 6px rgba(32,33,36,0.28) !important; }
    
    /* Vitrine Estilo Rede Social */
    .social-card {
        border: 1px solid #f0f2f6; border-radius: 15px; padding: 20px;
        margin-bottom: 20px; transition: 0.3s; background: #fff;
    }
    .social-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); transform: translateY(-2px); }
    .profile-pic { width: 60px; height: 60px; border-radius: 50%; object-fit: cover; border: 2px solid #4285F4; }
    .badge-elite { background: #FF8C00; color: white; padding: 2px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. NAVEGAÇÃO E ESTADOS
# ==============================================================================
if 'view' not in st.session_state: st.session_state.view = 'home'
if 'query' not in st.session_state: st.session_state.query = ""

# Menu Superior
c_nav1, c_nav2 = st.columns([8, 1])
with c_nav2:
    if st.button("⚙️ Admin"): st.session_state.view = 'admin'; st.rerun()

# --- MODO HOME ---
if st.session_state.view == 'home':
    st.write("##")
    st.markdown("<h1 style='text-align: center; font-size: 80px; color:#4285F4; font-family: sans-serif;'>GeralJá</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        q = st.text_input("", placeholder="O que você precisa agora?", key="search_in")
        st.write("##")
        b1, b2, b3, b4, b5 = st.columns(5)
        with b2:
            if st.button("Pesquisar", use_container_width=True) or q:
                if q:
                    st.session_state.query = q
                    st.session_state.view = 'resultados'; st.rerun()
        with b4:
            if st.button("Sou Profissional", use_container_width=True):
                st.session_state.view = 'cadastro'; st.rerun()

# --- MODO RESULTADOS (VITRINE REDE SOCIAL) ---
elif st.session_state.view == 'resultados':
    t1, t2 = st.columns([1, 5])
    with t1: 
        if st.button("← Voltar"): st.session_state.view = 'home'; st.rerun()
    
    st.markdown(f"### Resultados para: **{st.session_state.query}**")
    
    if db:
        docs = db.collection("profissionais").where("aprovado", "==", True).stream()
        lista = [d.to_dict() for d in docs]
        termo = normalizar(st.session_state.query)
        
        # Filtro Inteligente
        filtrados = [p for p in lista if termo in normalizar(p.get('categoria','')) or termo in normalizar(p.get('nome',''))]
        # Ranking Elite
        filtrados = sorted(filtrados, key=lambda x: (x.get('elite', False), x.get('nota', 0)), reverse=True)

        if not filtrados:
            st.warning("Nenhum profissional encontrado. Tente 'encanador' ou 'limpeza'.")
        
        for p in filtrados:
            with st.container():
                col_p1, col_p2, col_p3 = st.columns([0.6, 3, 1])
                with col_p1:
                    foto = p.get('foto_b64', "https://www.w3schools.com/howto/img_avatar.png")
                    st.markdown(f'<img src="data:image/png;base64,{foto}" class="profile-pic">' if len(foto) > 100 else f'<img src="{foto}" class="profile-pic">', unsafe_allow_html=True)
                with col_p2:
                    elite_tag = "<span class='badge-elite'>ELITE</span>" if p.get('elite') else ""
                    st.markdown(f"**{p.get('nome')}** {elite_tag}")
                    st.caption(f"{p.get('categoria')} • ⭐ {p.get('nota', 5.0)} • {p.get('bairro', 'São Paulo')}")
                    st.write(f"_{p.get('descricao', 'Sem descrição disponível.')}_")
                with col_p3:
                    st.write("##")
                    link = criar_link_zap(p.get('telefone'), p.get('nome'))
                    st.link_button("💬 WHATSAPP", link, use_container_width=True)
                st.markdown("<hr style='margin:10px 0; opacity:0.1'>", unsafe_allow_html=True)

# --- MODO ADMIN (PODERES TOTAIS + CONFIRMAÇÃO) ---
elif st.session_state.view == 'admin':
    if st.button("← Sair"): st.session_state.view = 'home'; st.rerun()
    st.title("🛡️ Painel de Controle GeralJá")
    
    senha = st.text_input("Insira a Chave Mestra para liberar os poderes", type="password")
    
    if senha == "riqueza2026": # Confirmação de Senha
        tab_aprov, tab_finc = st.tabs(["📋 Aprovações", "💰 Financeiro"])
        
        with tab_aprov:
            pendentes = db.collection("profissionais").where("aprovado", "==", False).stream()
            for doc in pendentes:
                p = doc.to_dict()
                col_a, col_b = st.columns([3,1])
                col_a.write(f"**{p.get('nome')}** ({p.get('categoria')})")
                if col_b.button("✅ APROVAR", key=doc.id):
                    db.collection("profissionais").document(doc.id).update({"aprovado": True})
                    st.success(f"{p.get('nome')} aprovado!")
                    st.rerun()
        
        with tab_finc:
            all_profs = db.collection("profissionais").stream()
            dados_f = []
            for doc in all_profs:
                d = doc.to_dict()
                dados_f.append({"Nome": d.get('nome'), "Faturamento": d.get('total_comprado', 0), "Status": "Elite" if d.get('elite') else "Padrão"})
            
            df = pd.DataFrame(dados_f)
            st.metric("FATURAMENTO TOTAL", f"R$ {df['Faturamento'].sum():,.2f}")
            st.table(df)

# --- MODO CADASTRO ---
elif st.session_state.view == 'cadastro':
    if st.button("← Voltar"): st.session_state.view = 'home'; st.rerun()
    st.subheader("💼 Cadastro de Profissional")
    with st.form("cad_form"):
        nome = st.text_input("Nome")
        cat = st.selectbox("Categoria", ["Encanador", "Eletricista", "Diarista", "Mecânico", "Pizzaria", "Outros"])
        tel = st.text_input("WhatsApp (Ex: 5511999999999)")
        desc = st.text_area("Descrição dos seus serviços")
        foto = st.file_uploader("Foto de Perfil", type=['png', 'jpg'])
        if st.form_submit_button("SOLICITAR ENTRADA"):
            # Lógica de salvamento idêntica aos seus arquivos anteriores
            foto_b64 = base64.b64encode(foto.getvalue()).decode() if foto else ""
            db.collection("profissionais").add({
                "nome": nome, "categoria": cat, "telefone": tel, "descricao": desc,
                "foto_b64": foto_b64, "aprovado": False, "elite": False, "nota": 5.0,
                "total_comprado": 0, "data_adesao": str(datetime.date.today())
            })
            st.success("✅ Pedido enviado! Aguarde aprovação do Admin.")

# ==============================================================================
# 5. RODAPÉ PODEROSO (VARREDURA)
# ==============================================================================
st.write("---")
footer_html = f"""
<div style='text-align: center; padding: 30px; color: #94A3B8; font-family: sans-serif;'>
    <p style='margin: 0; font-weight: bold;'>🎯 GERALJÁ v20.0 - Inteligência Local</p>
    <p style='margin: 5px; font-size: 13px;'>Blindagem UTF-8 Ativa • Banco de Dados Cloud Firestore • © {datetime.datetime.now().year}</p>
    <div style='margin-top: 10px;'>
        <span style='margin: 0 10px;'>🇧🇷 Brasil</span>
        <span style='margin: 0 10px;'>🛡️ Segurança Ponta a Ponta</span>
    </div>
</div>
"""
st.markdown(footer_html, unsafe_allow_html=True)
