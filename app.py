# ==============================================================================
# GERALJÁ: CÓDIGO MESTRE INTEGRADO (Estrutura Definitiva)
# Ordem de Execução: Imports -> Config -> Motores -> UI -> Main
# ==============================================================================

# --- 1. IMPORTS ---
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64, json, math, re, time, io, pandas as pd, pytz, unicodedata, requests, feedparser, urllib.parse
from datetime import datetime
from PIL import Image
from groq import Groq
from fuzzywuzzy import process
from bs4 import BeautifulSoup
from urllib.parse import quote

# --- 2. CONFIGURAÇÃO E CSS ---
st.set_page_config(page_title="GeralJá | Grajaú Tem", page_icon="📍", layout="wide")

st.markdown("""
<style>
    .hero-title { text-align: center; font-size: 3.5rem; font-weight: 800; color: #003399; margin-top: 50px; }
    .hero-subtitle { color: #FFD700; }
    .card { background: white; border-radius: 12px; padding: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-bottom: 4px solid #003399; margin-bottom: 20px; }
    .stButton>button { width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- 3. MOTORES (DADOS, IA, ECONOMIA) ---
@st.cache_resource
def get_db():
    if not firebase_admin._apps:
        cred = credentials.Certificate("firebase_key.json")
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = get_db()

def processar_curtida_coin(comerciante_id):
    """Motor de transação GeralCoin (CPC)"""
    doc_ref = db.collection("profissionais").document(comerciante_id)
    @firestore.transactional
    def atualizar_saldo(transaction, doc_ref):
        snapshot = doc_ref.get(transaction=transaction)
        saldo_atual = snapshot.get("geral_coin") or 0
        if saldo_atual >= 1:
            transaction.update(doc_ref, {"geral_coin": saldo_atual - 1})
            return True
        return False
    return atualizar_saldo(db.transaction(), doc_ref)

def motor_busca_inteligente(query, vitrine):
    """Motor de busca Fuzzy"""
    query_norm = unicodedata.normalize('NFKD', query).casefold()
    resultados = []
    for item in vitrine:
        nome = unicodedata.normalize('NFKD', item.get('nome', '')).casefold()
        if process.extractOne(query_norm, [nome])[1] > 50:
            resultados.append(item)
    return resultados

def extrair_info_shopee(url):
    """Capturador Automático"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        return {
            "nome": soup.find("meta", property="og:title")["content"] if soup.find("meta", property="og:title") else "Produto",
            "foto": soup.find("meta", property="og:image")["content"] if soup.find("meta", property="og:image") else "",
            "url": url
        }
    except:
        return {"error": "Falha ao capturar."}

# --- 4. FUNÇÕES DE INTERFACE (VITRINE) ---
def renderizar_card(item):
    with st.container():
        st.markdown(f'<div class="card"><h4>{item.get("nome")}</h4>', unsafe_allow_html=True)
        st.image(item.get('foto_url', 'https://via.placeholder.com/300'), use_container_width=True)
        
        if st.button("💬 Falar no WhatsApp", key=f"zap_{item['id']}"):
            sucesso = processar_curtida_coin(item['id'])
            if sucesso:
                st.link_button("🚀 Abrir Conversa", f"https://wa.me/55{item.get('whatsapp')}")
            else:
                st.error("Profissional sem saldo de GeralCoin.")
        st.markdown('</div>', unsafe_allow_html=True)

def renderizar_admin():
    st.header("⚙️ Painel de Controle")
    # Lógica de gestão aqui...

# --- 5. MAIN (CONTROLADOR) ---
def main():
    if 'pesquisou' not in st.session_state: st.session_state.pesquisou = False
    
    if not st.session_state.pesquisou:
        st.markdown('<div class="hero-title">Portal <span class="hero-subtitle">Grajaú Tem</span></div>', unsafe_allow_html=True)
        query = st.text_input("O que você procura?")
        if query:
            st.session_state.pesquisou = True
            st.session_state.query = query
            st.rerun()
    else:
        vitrine = [doc.to_dict() for doc in db.collection("loja").stream()] # Exemplo simples
        resultados = motor_busca_inteligente(st.session_state.query, vitrine)
        
        if st.button("Voltar"): st.session_state.pesquisou = False; st.rerun()
        
        for item in resultados:
            renderizar_card(item)

if __name__ == "__main__":
    main()
