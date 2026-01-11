import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime
import math
import pandas as pd
from streamlit_js_eval import get_geolocation

# 1. CONFIGURAÇÃO DE PÁGINA (ESTILO MINIMALISTA)
st.set_page_config(page_title="GeralJá | Brasil", page_icon="🇧🇷", layout="wide", initial_sidebar_state="collapsed")

# 2. CONEXÃO FIREBASE (Soma dos seus arquivos anteriores)
@st.cache_resource
def conectar_banco():
    if not firebase_admin._apps:
        try:
            # Aqui ele pega a sua chave FIREBASE_BASE64 que já está no seu Secrets
            b64_key = st.secrets["FIREBASE_BASE64"]
            decoded_json = base64.b64decode(b64_key).decode("utf-8")
            cred_dict = json.loads(decoded_json)
            cred = credentials.Certificate(cred_dict)
            return firebase_admin.initialize_app(cred).firestore()
        except Exception as e:
            st.error(f"Erro de conexão: {e}")
            return None
    return firestore.client()

db = conectar_banco()

# 3. INTELIGÊNCIA DE MAPEAMENTO (CONCEITOS EXPANDIDOS)
MAPA_IA = {
    "Encanador": ["vazamento", "cano", "torneira", "esgoto", "pia", "infiltração", "hidráulica"],
    "Eletricista": ["luz", "curto", "tomada", "disjuntor", "chuveiro", "fiação", "energia"],
    "Diarista": ["limpeza", "faxina", "arrumação", "casa", "apartamento", "sujeira"],
    "Mecânico": ["carro", "motor", "pneu", "freio", "revisão", "barulho", "oficina"],
    "Pizzaria": ["fome", "pizza", "comida", "entrega", "jantar", "fome"]
}

# 4. ESTILIZAÇÃO CSS (GOOGLE INTERFACE)
st.markdown("""
    <style>
        .stApp { background-color: white !important; }
        
        /* Menu Superior Discreto */
        .nav-google { display: flex; justify-content: flex-end; padding: 10px 20px; gap: 15px; font-size: 13px; font-family: Arial; }
        .nav-item { color: #5f6368; text-decoration: none; cursor: pointer; font-family: sans-serif; }

        /* Barra de Busca Arredondada */
        div.stTextInput > div > div > input {
            border-radius: 24px !important;
            border: 1px solid #dfe1e5 !important;
            padding: 12px 25px !important;
            box-shadow: none !important;
            max-width: 600px;
            margin: 0 auto;
        }
        
        /* Card de Resultado (Estilo Google) */
        .result-box { max-width: 650px; margin-bottom: 25px; font-family: 'Arial', sans-serif; }
        .result-link { color: #202124; font-size: 14px; margin-bottom: 2px; }
        .result-title { color: #1a0dab; font-size: 20px; text-decoration: none; cursor: pointer; }
        .result-title:hover { text-decoration: underline; }
        .result-snippet { color: #4d5156; font-size: 14px; line-height: 1.5; }
        
        /* Badges de Elite do GeralJá */
        .badge-elite { background-color: #FF8C00; color: white; padding: 1px 7px; border-radius: 8px; font-size: 10px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 5. MENU SUPERIOR
st.markdown("""
    <div class="nav-google">
        <span class="nav-item">Sobre</span>
        <span class="nav-item">Parceiros</span>
        <span class="nav-item">⚙️ <b>Admin</b></span>
    </div>
""", unsafe_allow_html=True)

# 6. ESTADO DO APLICATIVO
if 'busca_ativa' not in st.session_state:
    st.session_state.busca_ativa = False
if 'termo_pesquisa' not in st.session_state:
    st.session_state.termo_pesquisa = ""

# 7. LOGICA DE BUSCA (A melhor dos seus arquivos)
def calcular_ranking(query):
    query = query.lower()
    cat_alvo = None
    for cat, sinonimos in MAPA_IA.items():
        if query in cat.lower() or any(s in query for s in sinonimos):
            cat_alvo = cat
            break
    
    # Busca no Firebase (Simulação dos seus dados reais)
    if db:
        profs = db.collection("profissionais").where("categoria", "==", cat_alvo).stream()
        lista = [p.to_dict() for p in profs]
        # Ordena por Elite e Saldo (Como você tinha no app original)
        return sorted(lista, key=lambda x: (x.get('elite', False), x.get('saldo', 0)), reverse=True)
    return []

# 8. UI: MODO HOME (GOOGLE SEARCH)
if not st.session_state.busca_ativa:
    st.write("##")
    st.write("##")
    st.write("##")
    # Logo Colorida GeralJá
    st.markdown("<h1 style='text-align: center; font-size: 90px; font-family: sans-serif; letter-spacing: -4px;'><span style='color:#4285F4'>G</span><span style='color:#EA4335'>e</span><span style='color:#FBBC05'>r</span><span style='color:#4285F4'>a</span><span style='color:#34A853'>l</span><span style='color:#EA4335'>Já</span></h1>", unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        entrada = st.text_input("", placeholder="Busque um profissional ou problema (ex: vazamento)", key="search_home")
        st.write("##")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c2:
            if st.button("Pesquisa GeralJá", use_container_width=True) or (entrada != ""):
                if entrada:
                    st.session_state.termo_pesquisa = entrada
                    st.session_state.busca_ativa = True
                    st.rerun()
        with c4:
            st.button("Sou Profissional", use_container_width=True)

# 9. UI: MODO RESULTADOS (PÁGINA DE BUSCA)
else:
    t1, t2, t3 = st.columns([1, 4, 1])
    with t1:
        if st.button("← Voltar"):
            st.session_state.busca_ativa = False
            st.rerun()
    with t2:
        st.session_state.termo_pesquisa = st.text_input("", value=st.session_state.termo_pesquisa)
    
    st.markdown("---")
    
    resultados = calcular_ranking(st.session_state.termo_pesquisa)
    
    if resultados:
        st.write(f"Cerca de {len(resultados)} profissionais encontrados para '{st.session_state.termo_pesquisa}'")
        for p in resultados:
            elite = "<span class='badge-elite'>ELITE</span>" if p.get('elite') else ""
            st.markdown(f"""
                <div class="result-box">
                    <div class="result-link">https://www.geralja.com.br › {p.get('categoria','servicos').lower()}</div>
                    <div class="result-title">{p.get('nome')} {elite}</div>
                    <div class="result-snippet">
                        <b>⭐ {p.get('rating', 5.0)}</b> · Profissional verificado · Disponível agora.<br>
                        {p.get('descricao', 'Especialista em serviços gerais pronto para te atender.')}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if st.button(f"Entrar em contato com {p.get('nome')}", key=p.get('nome')):
                st.success("Abrindo WhatsApp...")
    else:
        st.info("Dica: Tente termos simples como 'luz', 'cano' ou 'limpeza'.")

# 10. RODAPÉ (VARREDOR)
st.markdown("<div style='position: fixed; bottom: 0; width: 100%; background: #f2f2f2; padding: 10px; text-align: center; color: #70757a; font-size: 13px;'>Brasil · São Paulo - Baseado no seu histórico · GeralJá v20.0</div>", unsafe_allow_html=True)
