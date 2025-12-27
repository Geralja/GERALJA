import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="GeralJá | Grajaú", page_icon="⚡", layout="centered")

# --- CONEXÃO FIREBASE (SISTEMA BASE64) ---
if not firebase_admin._apps:
    try:
        b64_data = st.secrets["FIREBASE_BASE64"]
        json_data = base64.b64decode(b64_data).decode("utf-8")
        info_chave = json.loads(json_data)
        
        cred = credentials.Certificate(info_chave)
        firebase_admin.initialize_app(cred)
        st.toast("🔥 GeralJá Conectado!", icon="✅")
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        st.stop()

db = firestore.client()

# --- DESIGN PERSONALIZADO ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    .azul { color: #0047AB; font-size: 45px; font-weight: 900; }
    .laranja { color: #FF8C00; font-size: 45px; font-weight: 900; }
    .card { background: #f9f9f9; padding: 15px; border-radius: 10px; border-left: 5px solid #0047AB; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO ---
st.markdown('<center><span class="azul">GERAL</span><span class="laranja">JÁ</span></center>', unsafe_allow_html=True)
st.markdown("<center><b>Serviços e Comunidade no Grajaú</b></center>", unsafe_allow_html=True)
st.write("---")

# --- NAVEGAÇÃO POR ABAS ---
tab1, tab2, tab3 = st.tabs(["🔍 BUSCAR", "👷 CADASTRAR", "👥 MURAL"])

# --- TAB 1: BUSCA ---
with tab1:
    st.subheader("O que você precisa hoje?")
    filtro = st.selectbox("Escolha uma categoria", ["", "Pintor", "Eletricista", "Encanador", "Diarista", "Mecânico"])
    
    if filtro:
        # Busca no Firebase profissionais daquela área
        profs = db.collection("profissionais").where("area", "==", filtro).stream()
        encontrou = False
        for p in profs:
            encontrou = True
            dados = p.to_dict()
            st.markdown(f"""
            <div class="card">
                <b>👤 {dados['nome']}</b><br>
                🔧 Especialidade: {dados['area']}<br>
                📍 Atende no Grajaú e Região
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Ver WhatsApp de {dados['nome']}", key=p.id):
                st.warning("Página de pagamento em integração...")
        
        if not encontrou:
            st.info(f"Ainda não temos {filtro}s cadastrados. Conhece um? Peça para ele se cadastrar!")

# --- TAB 2: CADASTRO ---
with tab2:
    st.subheader("Divulgue seu trabalho!")
    with st.form("form_cadastro", clear_on_submit=True):
        nome_cad = st.text_input("Seu nome completo")
        area_cad = st.selectbox("Sua especialidade", ["Pintor", "Eletricista", "Encanador", "Diarista", "Mecânico"])
        zap_cad = st.text_input("Seu WhatsApp (ex: 11988887777)")
        
        enviar = st.form_submit_button("CADASTRAR MEU SERVIÇO")
        
        if enviar:
            if nome_cad and zap_cad:
                db.collection("profissionais").add({
                    "nome": nome_cad,
                    "area": area_cad,
                    "whatsapp": zap_cad,
                    "data": datetime.datetime.now()
                })
                st.balloons()
                st.success(f"Parabéns {nome_cad}! Seu cadastro foi enviado com sucesso.")
            else:
                st.error("Por favor, preencha o nome e o WhatsApp.")

# --- TAB 3: MURAL ---
with tab3:
    st.subheader("Mural da Comunidade")
    with st.form("form_mural", clear_on_submit=True):
        mensagem = st.text_area("O que quer compartilhar com o bairro?")
        postar = st.form_submit_button("POSTAR NO MURAL")
        
        if postar and mensagem:
            db.collection("mural").add({
                "msg": mensagem,
                "data": datetime.datetime.now()
            })
            st.rerun()

    st.write("---")
    # Mostra os últimos 5 posts do mural
    posts = db.collection("mural").order_by("data", direction=firestore.Query.DESCENDING).limit(5).stream()
    for p in posts:
        item = p.to_dict()
        st.markdown(f"""
        <div style="background: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 5px;">
            <small>{item['data'].strftime('%d/%m/%Y %H:%M')}</small><br>
            {item['msg']}
        </div>
        """, unsafe_allow_html=True)
