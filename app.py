import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime
import random

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
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        st.stop()

db = firestore.client()

# --- DESIGN SOCIAL (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; background-color: #f0f2f5; }
    
    .azul { color: #0047AB; font-size: 40px; font-weight: 800; }
    .laranja { color: #FF8C00; font-size: 40px; font-weight: 800; }
    
    /* Card de Post de Rede Social */
    .social-card {
        background: white;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        margin-bottom: 15px;
        border: 1px solid #ddd;
    }
    
    .social-header { display: flex; align-items: center; margin-bottom: 10px; }
    
    .avatar {
        width: 40px; height: 40px;
        background-color: #0047AB;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        color: white; font-weight: bold; margin-right: 12px;
    }
    
    .user-info { display: flex; flex-direction: column; }
    .user-name { font-weight: 600; color: #1c1e21; font-size: 15px; }
    .post-time { color: #65676b; font-size: 13px; }
    .post-content { color: #050505; font-size: 15px; line-height: 1.4; }
    
    /* Estilo do Campo de Postagem */
    .post-box {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        margin-bottom: 25px;
    }
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO ---
st.markdown('<center><span class="azul">GERAL</span><span class="laranja">JÁ</span></center>', unsafe_allow_html=True)
st.write("")

tab1, tab2, tab3 = st.tabs(["🔍 BUSCA", "👷 CADASTRO", "👥 MURAL SOCIAL"])

# --- TAB 1 & 2 (Mantidas as lógicas anteriores) ---
with tab1:
    filtro = st.selectbox("Procurar no Grajaú", ["", "Pintor", "Eletricista", "Encanador", "Diarista", "Mecânico"])
    if filtro:
        profs = db.collection("profissionais").where("area", "==", filtro).stream()
        for p in profs:
            d = p.to_dict()
            zap = "".join(filter(str.isdigit, d.get('whatsapp', '')))
            st.markdown(f'<div style="background:white; padding:15px; border-radius:10px; border:1px solid #ddd; margin-bottom:10px;"><b>👤 {d["nome"]}</b><br>Verificado ✔️<br><a href="https://wa.me/55{zap}" style="color:#25D366; font-weight:bold; text-decoration:none;">📱 Chamar no WhatsApp</a></div>', unsafe_allow_html=True)

with tab2:
    with st.form("cad"):
        n = st.text_input("Nome")
        a = st.selectbox("Área", ["Pintor", "Eletricista", "Encanador", "Diarista", "Mecânico"])
        w = st.text_input("WhatsApp")
        if st.form_submit_button("Cadastrar"):
            db.collection("profissionais").add({"nome": n, "area": a, "whatsapp": w})
            st.success("Cadastrado!")

# --- TAB 3: MURAL SOCIAL (REFEITO TIPO REDE SOCIAL) ---
with tab3:
    st.markdown('<div class="post-box">', unsafe_allow_html=True)
    with st.form("novo_post", clear_on_submit=True):
        u_nome = st.text_input("Seu nome ou apelido", placeholder="Ex: João do Grajaú")
        u_msg = st.text_area("O que você quer contar para o bairro hoje?", placeholder="Vagas de emprego, eventos, notícias...")
        submit = st.form_submit_button("Publicar no Feed")
        
        if submit and u_msg:
            # Salvando no banco com nome de usuário
            db.collection("mural").add({
                "usuario": u_nome if u_nome else "Vizinho Anônimo",
                "msg": u_msg,
                "data": datetime.datetime.now()
            })
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # FEED DE POSTAGENS
    st.markdown("### Feed da Comunidade")
    posts = db.collection("mural").order_by("data", direction=firestore.Query.DESCENDING).limit(15).stream()
    
    for p in posts:
        item = p.to_dict()
        nome = item.get("usuario", "Anonimo")
        inicial = nome[0].upper() if nome else "?"
        data_formatada = item['data'].strftime('%d de %b às %H:%M')
        
        st.markdown(f"""
        <div class="social-card">
            <div class="social-header">
                <div class="avatar">{inicial}</div>
                <div class="user-info">
                    <span class="user-name">{nome}</span>
                    <span class="post-time">{data_formatada}</span>
                </div>
            </div>
            <div class="post-content">
                {item['msg']}
            </div>
        </div>
        """, unsafe_allow_html=True)
