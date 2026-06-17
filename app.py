# ==============================================================================
# GERALJÁ - MASTER SKELETON (Versão Final Integrada)
# ARQUITETURA: Imports -> Infra -> Motores -> Interface -> Main
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

# --- 2. CONFIGURAÇÃO GLOBAL ---
st.set_page_config(page_title="GeralJá | Criando Soluções", page_icon="🇧🇷", layout="wide")

# CSS Premium (Injetado)
st.markdown("""<style>
    .card { background: white; border-radius: 12px; padding: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-bottom: 4px solid #003399; margin-bottom: 20px; }
    .hero-title { text-align: center; font-size: 3rem; font-weight: 800; color: #003399; }
</style>""", unsafe_allow_html=True)

# --- 3. INFRAESTRUTURA (Firebase/Database) ---
@st.cache_resource
def init_db():
    if not firebase_admin._apps:
        cred = credentials.Certificate("firebase_key.json")
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = init_db()

# --- 4. MOTORES (Busca, Capturador, Economia) ---
def motor_busca_inteligente(query, vitrine):
    norm = lambda t: unicodedata.normalize('NFKD', str(t)).casefold().strip()
    q = norm(query)
    res = [item for item in vitrine if process.extractOne(q, [norm(item.get('nome', ''))])[1] > 50]
    return sorted(res, key=lambda x: x.get('score', 0), reverse=True)

def processar_curtida_coin(comerciante_id):
    doc_ref = db.collection("profissionais").document(comerciante_id)
    @firestore.transactional
    def atualizar(transaction, doc_ref):
        snap = doc_ref.get(transaction=transaction)
        saldo = snap.get("geral_coin") or 0
        if saldo >= 1:
            transaction.update(doc_ref, {"geral_coin": saldo - 1})
            return True, saldo - 1
        return False, saldo
    return atualizar(db.transaction(), doc_ref)

def extrair_info_shopee(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        soup = BeautifulSoup(requests.get(url, headers=headers, timeout=5).content, 'html.parser')
        return {
            "nome": soup.find("meta", property="og:title")["content"] if soup.find("meta", property="og:title") else "Produto",
            "foto": soup.find("meta", property="og:image")["content"] if soup.find("meta", property="og:image") else "",
            "url": url
        }
    except: return {"error": "Falha na captura"}

# --- 5. INTERFACE (Componentes) ---
def renderizar_card(item):
    st.markdown(f'<div class="card"><h4>{item.get("nome")}</h4>', unsafe_allow_html=True)
    if st.button("💬 Falar no WhatsApp", key=f"zap_{item.get('id')}"):
        sucesso, saldo = processar_curtida_coin(item.get('id'))
        if sucesso:
            st.success(f"Contato liberado! (Saldo: {saldo} GC)")
            st.link_button("🚀 Abrir Conversa", f"https://wa.me/55{item.get('whatsapp')}")
        else:
            st.error("Profissional sem saldo de GeralCoin.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 6. EXECUÇÃO (MAIN) ---
def main():
    if 'pesquisou' not in st.session_state: st.session_state.pesquisou = False
    
    if not st.session_state.pesquisou:
        st.markdown('<div class="hero-title">Portal Grajaú Tem</div>', unsafe_allow_html=True)
        query = st.text_input("O que você procura?")
        if query:
            st.session_state.pesquisou = True
            st.session_state.query = query
            st.rerun()
    else:
        # Busca no banco
        vitrine = [d.to_dict() for d in db.collection("loja").stream()]
        resultados = motor_busca_inteligente(st.session_state.query, vitrine)
        
        if st.button("⬅️ Nova Pesquisa"): st.session_state.pesquisou = False; st.rerun()
        
        for item in resultados:
            renderizar_card(item)

if __name__ == "__main__":
    main()
