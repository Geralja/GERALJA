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

# --- DESIGN PREMIUM (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700;900&display=swap');
    
    html, body, [class*="st-"] { font-family: 'Roboto', sans-serif; }
    
    .azul { color: #0047AB; font-size: 45px; font-weight: 900; letter-spacing: -1px; }
    .laranja { color: #FF8C00; font-size: 45px; font-weight: 900; letter-spacing: -1px; }
    
    /* Card do Profissional */
    .card-pro {
        background: white;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 20px;
        transition: transform 0.2s;
    }
    .card-pro:hover { transform: translateY(-3px); }
    
    .nome-pro { color: #333; font-size: 20px; font-weight: 700; margin-bottom: 5px; }
    .area-pro { color: #666; font-size: 16px; margin-bottom: 10px; font-weight: 500; }
    .selo-verificado { color: #28a745; font-size: 14px; font-weight: 700; }
    
    /* Botão de WhatsApp */
    .btn-zap {
        background-color: #25D366;
        color: white !important;
        padding: 12px 20px;
        border-radius: 10px;
        text-decoration: none;
        font-weight: bold;
        display: block;
        text-align: center;
        width: 100%;
        margin-top: 15px;
        box-sizing: border-box;
    }
    .btn-zap:hover { background-color: #128C7E; text-decoration: none; }
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO ---
st.markdown('<center><span class="azul">GERAL</span><span class="laranja">JÁ</span></center>', unsafe_allow_html=True)
st.markdown("<center style='margin-top:-15px;'><b>O guia oficial de serviços do Grajaú</b></center>", unsafe_allow_html=True)
st.write("")

# --- NAVEGAÇÃO ---
tab1, tab2, tab3 = st.tabs(["🔍 ENCONTRAR PROFISSIONAL", "👷 DIVULGAR MEU SERVIÇO", "👥 MURAL"])

# --- TAB 1: BUSCA ---
with tab1:
    st.write("")
    filtro = st.selectbox("O que você precisa hoje?", ["", "Pintor", "Eletricista", "Encanador", "Diarista", "Mecânico"])
    
    if filtro:
        profs = db.collection("profissionais").where("area", "==", filtro).stream()
        encontrou = False
        for p in profs:
            encontrou = True
            dados = p.to_dict()
            # Limpa o número para o link do zap
            zap_limpo = "".join(filter(str.isdigit, dados.get('whatsapp', '')))
            
            st.markdown(f"""
            <div class="card-pro">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="nome-pro">👤 {dados['nome']}</span>
                    <span class="selo-verificado">Verificado ✔️</span>
                </div>
                <div class="area-pro">🔧 {dados['area']}</div>
                <div style="font-size: 14px; color: #888;">📍 Atende em: Grajaú e Região</div>
                <a href="https://wa.me/55{zap_limpo}?text=Olá%20{dados['nome']},%20vi%20seu%20contato%20no%20GeralJá!" target="_blank" class="btn-zap">
                    CHAMAR NO WHATSAPP
                </a>
            </div>
            """, unsafe_allow_html=True)
        
        if not encontrou:
            st.info(f"Ainda não temos {filtro}s cadastrados no sistema.")

# --- TAB 2: CADASTRO ---
with tab2:
    st.subheader("Faça parte do GeralJá")
    with st.form("form_cadastro", clear_on_submit=True):
        nome_cad = st.text_input("Nome Completo")
        area_cad = st.selectbox("Sua Especialidade", ["Pintor", "Eletricista", "Encanador", "Diarista", "Mecânico"])
        zap_cad = st.text_input("WhatsApp com DDD (ex: 11999998888)")
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
                st.success("Cadastro realizado com sucesso! Procure seu nome na busca.")

# --- TAB 3: MURAL ---
with tab3:
    st.subheader("Mural da Comunidade")
    with st.form("form_mural", clear_on_submit=True):
        mensagem = st.text_area("Compartilhe algo com o bairro...")
        postar = st.form_submit_button("PUBLICAR")
        if postar and mensagem:
            db.collection("mural").add({"msg": mensagem, "data": datetime.datetime.now()})
            st.rerun()

    posts = db.collection("mural").order_by("data", direction=firestore.Query.DESCENDING).limit(10).stream()
    for p in posts:
        item = p.to_dict()
        st.markdown(f"""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 12px; margin-bottom: 10px; border: 1px solid #eee;">
            <small style="color: #999;">{item['data'].strftime('%d/%m - %H:%M')}</small><br>
            <span style="color: #444;">{item['msg']}</span>
        </div>
        """, unsafe_allow_html=True)
