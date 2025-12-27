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

# --- VALORES DA PLATAFORMA ---
VALOR_CLIQUE = 1  # Custa 1 GeralCoin abrir o contato
BONUS_CADASTRO = 5 # Novos usuários ganham 5 GC

# --- CSS ESTILIZADO ---
st.markdown("""
    <style>
    .azul { color: #0047AB; font-size: 40px; font-weight: 900; }
    .laranja { color: #FF8C00; font-size: 40px; font-weight: 900; }
    .card-pro {
        background: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px;
        border-top: 6px solid #FF8C00;
    }
    .coin-balance {
        background: #FFF9C4; color: #F57F17; padding: 10px;
        border-radius: 10px; text-align: center; font-weight: bold; font-size: 20px;
    }
    .pacote-card {
        border: 1px solid #ddd; padding: 10px; border-radius: 8px;
        text-align: center; background: #f9f9f9;
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown('<center><span class="azul">GERAL</span><span class="laranja">JÁ</span></center>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🔍 BUSCAR", "🏦 MINHA CARTEIRA", "👥 MURAL"])

# --- TAB 1: BUSCA COM CONSUMO ---
with tab1:
    st.subheader("O que você busca hoje?")
    # Simulando a lista de profissões (em produção usaríamos a lista completa de 1000)
    busca = st.selectbox("Escolha a categoria:", ["", "Pintor", "Eletricista", "Encanador", "Barman", "Diarista"])
    
    if busca:
        profs = db.collection("profissionais").where("area", "==", busca).where("aprovado", "==", True).stream()
        
        for p in profs:
            d = p.to_dict()
            pid = p.id
            saldo = d.get("saldo", 0)
            
            st.markdown(f"""
            <div class="card-pro">
                <div style="display: flex; justify-content: space-between;">
                    <span style="font-size: 18px; font-weight: bold;">👤 {d['nome']}</span>
                    <span style="color: #25D366; font-weight: bold;">Verificado ✔️</span>
                </div>
                <p>🔧 Especialista em {d['area']}</p>
            """, unsafe_allow_html=True)
            
            if saldo >= VALOR_CLIQUE:
                if st.button(f"VER WHATSAPP DE {d['nome'].upper()}", key=pid):
                    # Deduz saldo e mostra o link
                    db.collection("profissionais").document(pid).update({"saldo": firestore.Increment(-VALOR_CLIQUE)})
                    zap_limpo = "".join(filter(str.isdigit, d['whatsapp']))
                    st.success(f"Contato liberado! -{VALOR_CLIQUE} GC")
                    st.markdown(f'👉 [ABRIR WHATSAPP](https://wa.me/55{zap_limpo})', unsafe_allow_html=True)
            else:
                st.warning("Este profissional atingiu o limite de contatos gratuitos.")
            st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 2: CARTEIRA E LOJA ---
with tab2:
    st.subheader("Área do Profissional")
    login = st.text_input("Seu WhatsApp cadastrado:")
    
    if login:
        doc = db.collection("profissionais").document(login).get()
        if doc.exists:
            user = doc.to_dict()
            st.markdown(f"### Olá, {user['nome']}!")
            st.markdown(f'<div class="coin-balance">Saldo: {user.get("saldo", 0)} GeralCoins 💰</div>', unsafe_allow_html=True)
            
            st.write("---")
            st.subheader("🛒 Recarregar Créditos")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown('<div class="pacote-card"><b>Bronze</b><br>10 GC<br>R$ 10</div>', unsafe_allow_html=True)
                if st.button("Comprar 10"): st.info("Chame o Admin no Pix")
            with c2:
                st.markdown('<div class="pacote-card"><b>Prata</b><br>30 GC<br>R$ 25</div>', unsafe_allow_html=True)
                if st.button("Comprar 30"): st.info("Chame o Admin no Pix")
            with c3:
                st.markdown('<div class="pacote-card"><b>Ouro</b><br>70 GC<br>R$ 50</div>', unsafe_allow_html=True)
                if st.button("Comprar 70"): st.info("Chame o Admin no Pix")
                
            st.caption("Ao clicar em comprar, envie o comprovante PIX para o administrador para a liberação.")
        else:
            st.error("WhatsApp não cadastrado.")
            if st.button("Criar meu cadastro agora"):
                # Lógica para levar ao formulário
                pass

# --- TAB 3: MURAL ---
with tab3:
    st.info("Mural em transição para o sistema de recompensas!")
