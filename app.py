# ==============================================================================
# GERALJÁ: SISTEMA INTEGRAL - MASTER APP (ORQUESTRADOR)
# ==============================================================================
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import os

# ==========================================
# BLOCO 1: CONFIGURAÇÃO E CONEXÃO (BACKEND)
# ==========================================
def init_firebase():
    if not firebase_admin._apps:
        # Ajuste aqui o caminho do seu arquivo de credenciais
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = init_firebase()

# ==========================================
# BLOCO 2: LÓGICA DE NEGÓCIO (GERAL COIN & INDEXADOR)
# ==========================================
def check_geral_coin(user_id):
    """Verifica se o prestador tem saldo para aparecer na vitrine"""
    doc = db.collection("usuarios").document(user_id).get()
    if doc.exists:
        return doc.to_dict().get("geral_coin", 0) > 0
    return False

def adicionar_servico(titulo, categoria, video_url, user_id):
    """
    Indexador Automático: Simula o trigger.
    Salva nos dois lugares (coleção bruta e índice de busca) de uma vez.
    """
    data = {
        "titulo": titulo,
        "categoria": categoria,
        "video_url": video_url,
        "ativo": True
    }
    # 1. Salva na coleção base
    ref = db.collection("prestadores").add(data)
    
    # 2. Indexa na vitrine (Opção A - Indexador Automático)
    db.collection("SearchIndex").document(ref[1].id).set(data)
    return True

# ==========================================
# BLOCO 3: INTERFACE (FRONTEND TIKTOK-LIKE)
# ==========================================
st.set_page_config(page_title="GeralJá - Grajaú", layout="wide")

st.title("🔥 GeralJá - A Vitrine do Grajaú")
st.markdown("---")

# Aba de busca e Cadastro
tab1, tab2 = st.tabs(["🔍 Busca", "➕ Cadastrar Serviço"])

with tab1:
    st.subheader("O que você procura?")
    query = st.text_input("Digite o serviço ou produto...")
    
    if query:
        # Busca otimizada lendo apenas o SearchIndex
        results = db.collection("SearchIndex").where("titulo", "==", query).stream()
        
        cols = st.columns(3) 
        i = 0
        for doc in results:
            data = doc.to_dict()
            with cols[i % 3]:
                # Container fixo para manter a uniformidade visual
                with st.container(border=True, height=450):
                    st.video(data.get('video_url', ''))
                    st.subheader(data.get('titulo'))
                    st.write(f"Categoria: {data.get('categoria')}")
                    st.button(f"Contratar {data.get('titulo')}", key=doc.id)
            i += 1
    else:
        st.info("Digite algo para ver as ofertas em destaque.")

with tab2:
    st.subheader("Cadastro de Prestador")
    with st.form("cadastro"):
        titulo = st.text_input("Título do serviço")
        cat = st.selectbox("Categoria", ["Pedreiro", "Pizza", "Eletricista", "Barbeiro"])
        url = st.text_input("URL do Vídeo (ex: link do YouTube/CDN)")
        uid = st.text_input("Seu ID de Usuário (Para checar Geral Coin)")
        submit = st.form_submit_button("Cadastrar")
        
        if submit:
            if check_geral_coin(uid):
                adicionar_servico(titulo, cat, url, uid)
                st.success("Serviço indexado com sucesso na vitrine!")
            else:
                st.error("Saldo insuficiente em Geral Coin. Recarregue para anunciar!")
