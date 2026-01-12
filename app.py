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
# 1. MOTOR DE SEGURANÇA (UTF-8 & PADDING FIX)
# ==============================================================================
st.set_page_config(page_title="GeralJá | Elite", page_icon="🎯", layout="wide")

@st.cache_resource
def conectar_banco_blindado():
    if not firebase_admin._apps:
        try:
            b64_key = st.secrets["FIREBASE_BASE64"].strip()
            # Resolve erro de padding do base64 automaticamente
            missing_padding = len(b64_key) % 4
            if missing_padding: b64_key += '=' * (4 - missing_padding)
            
            # Decode forçando UTF-8 e ignorando sujeira binária
            decoded_json = base64.b64decode(b64_key).decode("utf-8", errors="ignore")
            cred_dict = json.loads(decoded_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            return firestore.client()
        except Exception as e:
            st.error(f"Erro de Conexão: {e}")
            return None
    return firestore.client()

db = conectar_banco_blindado()

# ==============================================================================
# 2. ESTILIZAÇÃO DE IMPACTO (NADA DE GOOGLE - MODO DARK/PREMIUM)
# ==============================================================================
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important; color: white !important; }
    
    /* Input de busca customizado */
    div.stTextInput > div > div > input {
        background-color: rgba(255,255,255,0.05) !important;
        color: white !important; border: 1px solid #334155 !important;
        border-radius: 12px !important; height: 55px !important; font-size: 18px !important;
    }

    /* Card Estilo Rede Social / Premium */
    .card-elite {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px; padding: 25px; margin-bottom: 20px;
        transition: 0.4s ease; backdrop-filter: blur(10px);
    }
    .card-elite:hover {
        background: rgba(255, 255, 255, 0.07);
        transform: scale(1.01); border-color: #3b82f6;
    }
    
    .img-social { width: 90px; height: 90px; border-radius: 25px; object-fit: cover; border: 3px solid #3b82f6; }
    .badge-status { background: #10b981; color: white; padding: 4px 12px; border-radius: 8px; font-size: 12px; font-weight: bold; }
    .badge-elite { background: linear-gradient(45deg, #f59e0b, #ef4444); color: white; padding: 4px 12px; border-radius: 8px; font-size: 12px; }
    
    /* Rodapé Varredor */
    .footer-box { text-align: center; padding: 60px; margin-top: 50px; background: rgba(0,0,0,0.3); border-radius: 30px 30px 0 0; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. FUNÇÕES DE SUPORTE (SEM REMOVER NADA)
# ==============================================================================
def normalizar(t):
    return "".join(c for c in unicodedata.normalize('NFD', str(t)) if unicodedata.category(c) != 'Mn').lower()

def zap_link(tel, nome):
    num = re.sub(r'\D', '', str(tel))
    msg = quote(f"Olá {nome}, vi seu perfil no GeralJá e preciso de um serviço!")
    return f"https://wa.me/{num}?text={msg}"

# ==============================================================================
# 4. NAVEGAÇÃO E PÁGINAS
# ==============================================================================
if 'aba' not in st.session_state: st.session_state.aba = 'main'
if 'termo' not in st.session_state: st.session_state.termo = ""

# Header Premium
c_h1, c_h2 = st.columns([8, 2])
with c_h2:
    if st.button("🛡️ ACESSO RESTRITO"): 
        st.session_state.aba = 'admin'
        st.rerun()

# --- TELA INICIAL (IMPACTO) ---
if st.session_state.aba == 'main':
    st.write("##")
    st.markdown("<h1 style='text-align: center; font-size: 70px; font-weight: 800; background: -webkit-linear-gradient(#fff, #94a3b8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>GERALJÁ</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 20px;'>Encontre os melhores profissionais da sua região em segundos.</p>", unsafe_allow_html=True)
    
    col_b1, col_b2, col_b3 = st.columns([1, 4, 1])
    with col_b2:
        busca = st.text_input("", placeholder="O que você precisa resolver agora? (ex: encanador, faxina...)")
        st.write("##")
        b_c1, b_c2, b_c3 = st.columns([1,1,1])
        if b_c2.button("EXPLORAR SOLUÇÕES", use_container_width=True) or (busca != ""):
            if busca:
                st.session_state.termo = busca
                st.session_state.aba = 'busca'
                st.rerun()
        if b_c1.button("CADASTRE SEU SERVIÇO"): st.session_state.aba = 'cadastro'; st.rerun()

# --- VITRINE ESTILO REDE SOCIAL ---
elif st.session_state.aba == 'busca':
    if st.button("← VOLTAR PARA O INÍCIO"): st.session_state.aba = 'main'; st.rerun()
    st.markdown(f"### 🚀 Soluções para: {st.session_state.termo}")
    
    if db:
        profs = db.collection("profissionais").where("aprovado", "==", True).stream()
        lista = [p.to_dict() for p in profs]
        key = normalizar(st.session_state.termo)
        
        # Filtro e Ranking
        res = [p for p in lista if key in normalizar(p.get('categoria','')) or key in normalizar(p.get('nome',''))]
        res = sorted(res, key=lambda x: (x.get('elite', False), x.get('nota', 0)), reverse=True)

        for p in res:
            st.markdown(f"""
                <div class="card-elite">
                    <div style="display: flex; align-items: center; gap: 20px;">
                        <img src="data:image/png;base64,{p.get('foto_b64','')}" class="img-social" onerror="this.src='https://ui-avatars.com/api/?name={p.get('nome')}&background=random'">
                        <div style="flex-grow: 1;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <h2 style="margin:0; font-size: 24px;">{p.get('nome')}</h2>
                                <span class="badge-status">DISPONÍVEL</span>
                            </div>
                            <p style="color: #3b82f6; font-weight: bold; margin: 5px 0;">{p.get('categoria').upper()}</p>
                            <p style="color: #94a3b8; font-size: 14px; margin-bottom: 10px;">{p.get('descricao')}</p>
                            <div style="display: flex; gap: 15px; font-size: 13px;">
                                <span>⭐ {p.get('nota')}</span>
                                <span>📍 {p.get('bairro', 'Atendimento Local')}</span>
                                {"<span class='badge-elite'>PREMIUM ELITE</span>" if p.get('elite') else ""}
                            </div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if st.button(f"CONTRATAR {p.get('nome').upper()}", key=p.get('nome')):
                st.link_button("ABRIR WHATSAPP", zap_link(p.get('telefone'), p.get('nome')))

# --- ADMIN (COFRE & PODERES) ---
elif st.session_state.aba == 'admin':
    if st.button("← SAIR"): st.session_state.aba = 'main'; st.rerun()
    st.title("🛡️ Cofre de Controle")
    
    senha = st.text_input("Insira a Senha Mestra", type="password")
    if senha == "riqueza2026": # Confirmação de senha exigida
        st.success("Sessão Administrativa Ativa")
        t1, t2 = st.tabs(["📊 MÉTRICAS", "📋 APROVAÇÕES"])
        
        with t1:
            all_p = list(db.collection("profissionais").stream())
            df = pd.DataFrame([p.to_dict() for p in all_p])
            st.metric("FATURAMENTO BRUTO", f"R$ {df['total_comprado'].sum():,.2f}")
            st.table(df[['nome', 'total_comprado', 'elite']])
            
        with t2:
            pendentes = db.collection("profissionais").where("aprovado", "==", False).stream()
            for doc in pendentes:
                p = doc.to_dict()
                st.write(f"**{p.get('nome')}** | {p.get('categoria')}")
                if st.button(f"VALIDAR {doc.id}"):
                    db.collection("profissionais").document(doc.id).update({"aprovado": True})
                    st.rerun()
    else:
        st.info("Aguardando credenciais mestre...")

# --- CADASTRO ---
elif st.session_state.aba == 'cadastro':
    if st.button("← VOLTAR"): st.session_state.aba = 'main'; st.rerun()
    st.title("🤝 Junte-se à Elite")
    with st.form("registro"):
        nome = st.text_input("Nome Completo")
        cat = st.selectbox("Sua Especialidade", ["Encanador", "Eletricista", "Diarista", "Mecânico", "Outros"])
        tel = st.text_input("WhatsApp (DDDNÚMERO)")
        desc = st.text_area("O que você faz?")
        foto = st.file_uploader("Sua Foto (Rede Social)", type=['jpg','png'])
        if st.form_submit_button("SOLICITAR VAGA"):
            db.collection("profissionais").add({
                "nome": nome, "categoria": cat, "telefone": tel, "descricao": desc,
                "foto_b64": base64.b64encode(foto.getvalue()).decode() if foto else "",
                "aprovado": False, "elite": False, "nota": 5.0, "total_comprado": 0, "bairro": "São Paulo"
            })
            st.success("Sua solicitação foi enviada para o Admin!")

# ==============================================================================
# 5. RODAPÉ PODEROSO (VARREDURA)
# ==============================================================================
st.markdown(f"""
    <div class="footer-box">
        <h2 style="color: white; margin-bottom: 10px;">🎯 GERALJÁ v20.0</h2>
        <p style="color: #94a3b8;">Sistema de Inteligência Local Blindado • Todos os Direitos Reservados © {datetime.datetime.now().year}</p>
        <div style="display: flex; justify-content: center; gap: 30px; margin-top: 20px; opacity: 0.5; font-size: 12px;">
            <span>🇧🇷 BRASIL</span>
            <span>🔒 ENCRIPTADO</span>
            <span>⚡ ALTA PERFORMANCE</span>
        </div>
    </div>
""", unsafe_allow_html=True)
