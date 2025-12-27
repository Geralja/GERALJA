import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GeralJá Social", page_icon="👥", layout="centered")

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

# --- CSS ESTILO REDE SOCIAL ---
st.markdown("""
    <style>
    .azul { color: #0047AB; font-size: 40px; font-weight: 800; }
    .laranja { color: #FF8C00; font-size: 40px; font-weight: 800; }
    .feed-card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 15px; border: 1px solid #eee; }
    .avatar { width: 45px; height: 45px; background: #0047AB; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 12px; }
    .like-btn { color: #65676b; font-size: 14px; cursor: pointer; display: flex; align-items: center; gap: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- TÍTULO ---
st.markdown('<center><span class="azul">GERAL</span><span class="laranja">JÁ</span></center>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🔍 BUSCA", "👷 CADASTRO", "👥 MURAL RESTRITO"])

# --- TAB 1: BUSCA ---
with tab1:
    servico = st.selectbox("O que busca no Grajaú?", ["", "Pintor", "Eletricista", "Encanador", "Diarista", "Mecânico"])
    if servico:
        profs = db.collection("profissionais").where("area", "==", servico).where("aprovado", "==", True).stream()
        for p in profs:
            d = p.to_dict()
            st.markdown(f'<div class="feed-card"><b>{d["nome"]}</b> ✅<br>WhatsApp: {d["whatsapp"]}</div>', unsafe_allow_html=True)

# --- TAB 2: CADASTRO DE ACESSO ---
with tab2:
    st.subheader("Solicitar Acesso ao GeralJá")
    st.info("Após o cadastro, um administrador precisará aprovar seu perfil para você postar no mural.")
    with st.form("cad_user"):
        nome_c = st.text_input("Nome Completo")
        zap_c = st.text_input("WhatsApp (Seu Login)")
        area_c = st.selectbox("Você é profissional de que área?", ["Apenas Morador", "Pintor", "Eletricista", "Encanador", "Diarista", "Mecânico"])
        if st.form_submit_button("Solicitar Aprovação"):
            db.collection("profissionais").document(zap_c).set({
                "nome": nome_c, "whatsapp": zap_c, "area": area_c, 
                "aprovado": False, "data": datetime.datetime.now()
            })
            st.success("Solicitação enviada! Aguarde a aprovação do administrador.")

# --- TAB 3: MURAL (SÓ PARA APROVADOS) ---
with tab3:
    st.subheader("👥 Mural da Comunidade")
    
    # --- LOGIN SIMPLES ---
    login_zap = st.text_input("Digite seu WhatsApp cadastrado para postar:", type="password")
    user_data = None
    if login_zap:
        user_doc = db.collection("profissionais").document(login_zap).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            if not user_data.get("aprovado"):
                st.warning("⚠️ Seu perfil ainda não foi aprovado pelo administrador.")
                user_data = None
        else:
            st.error("❌ Usuário não encontrado. Cadastre-se na aba ao lado.")

    # --- CAMPO DE POSTAR (SÓ APARECE SE APROVADO) ---
    if user_data and user_data.get("aprovado"):
        st.markdown(f"Olá, **{user_data['nome']}**! Compartilhe algo:")
        with st.form("post_social", clear_on_submit=True):
            texto = st.text_area("O que está acontecendo no Grajaú?")
            if st.form_submit_button("Publicar"):
                db.collection("mural").add({
                    "nome": user_data['nome'],
                    "texto": texto,
                    "likes": 0,
                    "data": datetime.datetime.now()
                })
                st.rerun()
    
    st.divider()

    # --- FEED DE POSTAGENS ---
    posts = db.collection("mural").order_by("data", direction=firestore.Query.DESCENDING).limit(20).stream()
    
    for p in posts:
        post = p.to_dict()
        pid = p.id
        inicial = post['nome'][0].upper()
        
        st.markdown(f"""
        <div class="feed-card">
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <div class="avatar">{inicial}</div>
                <div><b>{post['nome']}</b><br><small>{post['data'].strftime('%d/%m %H:%M')}</small></div>
            </div>
            <div style="margin-bottom: 15px;">{post['texto']}</div>
            <div class="like-btn">❤️ {post.get('likes', 0)} curtidas</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Botão de Like funcional (SÓ PARA APROVADOS)
        if user_data and user_data.get("aprovado"):
            if st.button(f"Curtir post de {post['nome']}", key=f"btn_{pid}"):
                db.collection("mural").document(pid).update({"likes": firestore.Increment(1)})
                st.rerun()
