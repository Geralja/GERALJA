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

# ==============================================================================
# 1. CONEXÃO BLINDADA (RESOLVE ERRO UTF-8)
# ==============================================================================
st.set_page_config(page_title="GeralJá | Brasil", page_icon="🎯", layout="wide")

@st.cache_resource
def conectar_banco():
    if not firebase_admin._apps:
        try:
            b64_key = st.secrets["FIREBASE_BASE64"].strip()
            # Ajuste de Padding para evitar erro binário
            missing_padding = len(b64_key) % 4
            if missing_padding: b64_key += '=' * (4 - missing_padding)
            
            # Decode forçando UTF-8 para evitar erro de caracteres
            decoded_json = base64.b64decode(b64_key).decode("utf-8", errors="ignore")
            cred_dict = json.loads(decoded_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            return firestore.client()
        except Exception as e:
            st.error(f"Erro ao conectar: {e}")
            return None
    return firestore.client()

db = conectar_banco()

# ==============================================================================
# 2. ESTILIZAÇÃO VITRINE (ESTILO REDE SOCIAL)
# ==============================================================================
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    /* Estilo Card Rede Social */
    .card-social {
        background: white; border-radius: 15px; padding: 20px;
        margin-bottom: 20px; border: 1px solid #e1e4e8;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .img-perfil { width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 2px solid #25d366; }
    .badge-elite { background: gold; color: black; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. FUNÇÕES (SEM REMOVER NADA)
# ==============================================================================
def normalizar(t):
    return "".join(c for c in unicodedata.normalize('NFD', str(t)) if unicodedata.category(c) != 'Mn').lower()

def link_zap(tel, nome):
    num = re.sub(r'\D', '', str(tel))
    msg = quote(f"Olá {nome}, vi seu perfil no GeralJá!")
    return f"https://wa.me/{num}?text={msg}"

# ==============================================================================
# 4. ESTRUTURA DE ABAS (CONFORME O MODELO ORIGINAL)
# ==============================================================================
menu = st.tabs(["🏠 HOME", "🔎 BUSCAR", "📝 CADASTRO", "🛡️ ADMIN"])

# --- ABA 1: HOME ---
with menu[0]:
    st.title("🎯 GeralJá: Conectando Soluções")
    st.write("A plataforma líder em serviços locais. Escolha uma das abas acima para começar.")
    st.image("https://images.unsplash.com/photo-1581578731548-c64695cc6954?auto=format&fit=crop&w=800&q=80")

# --- ABA 2: BUSCAR (VITRINE REDE SOCIAL) ---
with menu[1]:
    busca = st.text_input("O que você precisa hoje?", placeholder="Ex: Encanador, Eletricista...")
    if db:
        docs = db.collection("profissionais").where("aprovado", "==", True).stream()
        profs = [d.to_dict() for d in docs]
        
        if busca:
            termo = normalizar(busca)
            profs = [p for p in profs if termo in normalizar(p.get('categoria','')) or termo in normalizar(p.get('nome',''))]

        for p in profs:
            st.markdown('<div class="card-social">', unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1, 4, 2])
            with c1:
                foto = p.get('foto_b64', "")
                if foto: st.markdown(f'<img src="data:image/png;base64,{foto}" class="img-perfil">', unsafe_allow_html=True)
                else: st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=80)
            with c2:
                elite = "<span class='badge-elite'>ELITE</span>" if p.get('elite') else ""
                st.markdown(f"### {p.get('nome')} {elite}")
                st.caption(f"⭐ {p.get('nota', 5.0)} | {p.get('categoria')}")
                st.write(p.get('descricao', ''))
            with c3:
                st.write("##")
                st.link_button("💬 WHATSAPP", link_zap(p.get('telefone'), p.get('nome')), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

# --- ABA 3: CADASTRO ---
with menu[2]:
    st.subheader("Cadastre o seu Serviço")
    with st.form("form_cad"):
        nome = st.text_input("Seu Nome")
        cat = st.selectbox("Categoria", ["Encanador", "Eletricista", "Diarista", "Mecânico", "Outros"])
        tel = st.text_input("WhatsApp")
        desc = st.text_area("Descrição do seu trabalho")
        foto = st.file_uploader("Sua Foto", type=['jpg', 'png'])
        if st.form_submit_button("SOLICITAR ENTRADA"):
            db.collection("profissionais").add({
                "nome": nome, "categoria": cat, "telefone": tel, "descricao": desc,
                "foto_b64": base64.b64encode(foto.getvalue()).decode() if foto else "",
                "aprovado": False, "elite": False, "nota": 5.0, "total_comprado": 0
            })
            st.success("Enviado! Aguarde a aprovação do Admin.")

# --- ABA 4: ADMIN (PODERES + CONFIRMAÇÃO SENHA) ---
with menu[3]:
    st.subheader("🛡️ Área Restrita")
    senha = st.text_input("Chave Mestra", type="password")
    if senha == "riqueza2026":
        st.success("Acesso Liberado!")
        t_admin1, t_admin2 = st.tabs(["📊 FINANCEIRO", "✅ APROVAÇÕES"])
        
        with t_admin1:
            all_p = list(db.collection("profissionais").stream())
            df = pd.DataFrame([p.to_dict() for p in all_p])
            st.metric("FATURAMENTO TOTAL", f"R$ {df['total_comprado'].sum():,.2f}")
            st.dataframe(df[['nome', 'total_comprado', 'elite']])
            
        with t_admin2:
            pendentes = db.collection("profissionais").where("aprovado", "==", False).stream()
            for doc in pendentes:
                p = doc.to_dict()
                col_a, col_b = st.columns([3, 1])
                col_a.write(f"**{p.get('nome')}** ({p.get('categoria')})")
                if col_b.button("APROVAR", key=doc.id):
                    db.collection("profissionais").document(doc.id).update({"aprovado": True})
                    st.rerun()
    else:
        st.info("Insira a senha para gerir o sistema.")

# ==============================================================================
# 5. RODAPÉ PODEROSO DE VARREDURA
# ==============================================================================
st.write("---")
st.markdown(f"""
    <div style="text-align: center; padding: 20px; color: #94A3B8; font-family: sans-serif;">
        <p style="margin: 0; font-weight: bold;">🎯 GERALJÁ v20.0 - Inteligência Local</p>
        <p style="margin: 5px; font-size: 12px;">Varredura Cloud Ativa • Blindagem UTF-8 • © {datetime.datetime.now().year}</p>
    </div>
""", unsafe_allow_html=True)
