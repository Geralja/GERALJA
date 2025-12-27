import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GeralJá | Business", page_icon="💰", layout="centered")

# --- CONEXÃO FIREBASE ---
if not firebase_admin._apps:
    try:
        b64_data = st.secrets["FIREBASE_BASE64"]
        json_data = base64.b64decode(b64_data).decode("utf-8")
        info_chave = json.loads(json_data)
        cred = credentials.Certificate(info_chave)
        firebase_admin.initialize_app(cred)
    except: st.stop()

db = firestore.client()

# --- CONFIGURAÇÕES DO NEGÓCIO ---
VALOR_CLIQUE = 1
PIX_ADMIN = "11991853488"
ZAP_ADMIN = "5511991853488" # Formato internacional para o link

# --- CSS ---
st.markdown("""
    <style>
    .azul { color: #0047AB; font-size: 40px; font-weight: 900; }
    .laranja { color: #FF8C00; font-size: 40px; font-weight: 900; }
    .coin-balance {
        background: #FFF9C4; color: #F57F17; padding: 15px;
        border-radius: 10px; text-align: center; font-weight: bold; font-size: 24px;
        border: 2px dashed #F57F17; margin-bottom: 20px;
    }
    .pacote-card {
        border: 1px solid #ddd; padding: 15px; border-radius: 12px;
        text-align: center; background: white; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .pix-box {
        background: #f0f2f5; padding: 15px; border-radius: 10px;
        text-align: center; border: 1px solid #0047AB; margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<center><span class="azul">GERAL</span><span class="laranja">JÁ</span></center>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🔍 BUSCAR", "🏦 MINHA CARTEIRA", "👥 MURAL"])

# --- TAB 1: BUSCA (MANTIDA) ---
with tab1:
    st.subheader("O que você busca hoje?")
    busca = st.selectbox("Escolha a categoria:", ["", "Pintor", "Eletricista", "Encanador", "Barman", "Diarista", "Mecânico"])
    
    if busca:
        profs = db.collection("profissionais").where("area", "==", busca).where("aprovado", "==", True).stream()
        for p in profs:
            d = p.to_dict()
            pid = p.id
            saldo = d.get("saldo", 0)
            
            st.markdown(f'<div style="background:white; padding:15px; border-radius:10px; border:1px solid #ddd; margin-bottom:10px;"><b>👤 {d["nome"]}</b><br>Saldo: {saldo} GC</div>', unsafe_allow_html=True)
            
            if saldo >= VALOR_CLIQUE:
                if st.button(f"VER CONTATO DE {d['nome'].upper()}", key=pid):
                    db.collection("profissionais").document(pid).update({"saldo": firestore.Increment(-VALOR_CLIQUE)})
                    zap_limpo = "".join(filter(str.isdigit, d['whatsapp']))
                    st.success(f"Contato liberado! -{VALOR_CLIQUE} GC")
                    st.markdown(f'👉 [ABRIR WHATSAPP](https://wa.me/55{zap_limpo})')
            else:
                st.warning("Profissional sem créditos no momento.")

# --- TAB 2: CARTEIRA COM PIX ATUALIZADO ---
with tab2:
    st.subheader("Área do Profissional")
    login = st.text_input("Acesse com seu WhatsApp (Login):", placeholder="Ex: 11988887777")
    
    if login:
        doc = db.collection("profissionais").document(login).get()
        if doc.exists:
            user = doc.to_dict()
            st.markdown(f"### Olá, {user['nome']}! 👋")
            st.markdown(f'<div class="coin-balance">{user.get("saldo", 0)} GeralCoins</div>', unsafe_allow_html=True)
            
            st.write("---")
            st.subheader("🛒 Recarregar GeralCoins")
            st.write("Escolha um pacote e faça o PIX para liberar seus contatos:")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown('<div class="pacote-card">🥉<br><b>Bronze</b><br>10 GC<br>R$ 10</div>', unsafe_allow_html=True)
                if st.button("Comprar 10", key="p10"):
                    st.session_state.pacote = "Bronze (10 GC)"
            with c2:
                st.markdown('<div class="pacote-card">🥈<br><b>Prata</b><br>30 GC<br>R$ 25</div>', unsafe_allow_html=True)
                if st.button("Comprar 30", key="p30"):
                    st.session_state.pacote = "Prata (30 GC)"
            with c3:
                st.markdown('<div class="pacote-card">🥇<br><b>Ouro</b><br>70 GC<br>R$ 50</div>', unsafe_allow_html=True)
                if st.button("Comprar 70", key="p70"):
                    st.session_state.pacote = "Ouro (70 GC)"

            if 'pacote' in st.session_state:
                st.markdown(f"""
                <div class="pix-box">
                    <b>PACOTE SELECIONADO: {st.session_state.pacote}</b><br>
                    Chave PIX Celular: <br>
                    <span style="font-size: 20px; color: #0047AB;"><b>{PIX_ADMIN}</b></span><br>
                    <small>Nome: (Confira se aparece seu nome no banco)</small>
                </div>
                """, unsafe_allow_html=True)
                
                # Link direto para o seu WhatsApp já com a mensagem pronta
                msg_pix = f"Olá! Fiz o PIX para o pacote {st.session_state.pacote}. Segue o comprovante para meu WhatsApp: {login}"
                st.markdown(f"""
                    <a href="https://wa.me/{ZAP_ADMIN}?text={msg_pix}" target="_blank" 
                    style="display: block; background: #25D366; color: white; text-align: center; padding: 12px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 10px;">
                        ENVIAR COMPROVANTE AGORA
                    </a>
                """, unsafe_allow_html=True)
        else:
            st.error("WhatsApp não cadastrado como profissional.")

# --- TAB 3: MURAL ---
with tab3:
    st.info("O Mural Social está em atualização.")
