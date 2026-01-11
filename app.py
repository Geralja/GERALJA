import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime
import math
import pandas as pd
from streamlit_js_eval import get_geolocation

# --- CONFIGURAÇÃO ÚNICA DA PÁGINA ---
st.set_page_config(page_title="GeralJá - Inteligência em Serviços", layout="wide", initial_sidebar_state="collapsed")

# --- LÓGICA DE DADOS EXISTENTES (O seu "Cérebro" de Categorias) ---
CONCEITOS_EXPANDIDOS = {
    "Encanador": ["vazamento", "cano", "torneira", "esgoto", "caixa d'água", "pia", "infiltração"],
    "Eletricista": ["luz", "curto", "tomada", "disjuntor", "fiação", "chuveiro", "instalação elétrica"],
    "Diarista": ["limpeza", "faxina", "arrumação", "passar roupa", "sujeira", "casa", "apartamento"],
    "Mecânico": ["carro", "motor", "pneu", "freio", "revisão", "barulho", "oficina"],
    "Pizzaria": ["fome", "pizza", "comida", "entrega", "jantar", "queijo", "massa"]
}

# --- INTERFACE CSS (ESTILO GOOGLE + MENU) ---
st.markdown("""
    <style>
        .stApp { background-color: white; }
        
        /* Menu Superior */
        .nav-bar {
            display: flex;
            justify-content: flex-end;
            padding: 15px;
            gap: 20px;
            font-family: Arial, sans-serif;
            font-size: 13px;
        }
        .nav-item { color: #5f6368; text-decoration: none; cursor: pointer; }
        .nav-item:hover { text-decoration: underline; }

        /* Barra de Busca */
        div.stTextInput > div > div > input {
            border-radius: 24px !important;
            border: 1px solid #dfe1e5 !important;
            padding: 12px 20px !important;
            box-shadow: none !important;
        }
        
        /* Badges de Elite e Verificado que já tínhamos */
        .badge-elite { background-color: #FF8C00; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: bold; }
        .verificado { color: #1a73e8; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- MENU SUPERIOR ---
st.markdown("""
    <div class="nav-bar">
        <span class="nav-item">Sobre</span>
        <span class="nav-item">Parceiros</span>
        <span class="nav-item"><b>Painel Admin</b></span>
    </div>
""", unsafe_allow_html=True)

# --- ESTADO DA BUSCA ---
if 'search_active' not in st.session_state:
    st.session_state.search_active = False
if 'query' not in st.session_state:
    st.session_state.query = ""

# --- HOME: ESTILO GOOGLE ---
if not st.session_state.search_active:
    st.write("##")
    st.write("##")
    st.markdown("<h1 style='text-align: center; font-size: 90px; font-family: Product Sans, Arial;'><span style='color:#4285F4'>G</span><span style='color:#EA4335'>e</span><span style='color:#FBBC05'>r</span><span style='color:#4285F4'>a</span><span style='color:#34A853'>l</span><span style='color:#EA4335'>Já</span></h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        q = st.text_input("", placeholder="O que você precisa agora?", key="home_input")
        st.write("##")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c2:
            if st.button("Buscar Agora", use_container_width=True) or (q != ""):
                if q:
                    st.session_state.query = q
                    st.session_state.search_active = True
                    st.rerun()
        with c4:
            st.button("Sou Profissional", use_container_width=True)

# --- RESULTADOS: ESTILO GOOGLE SEARCH ---
else:
    t1, t2, t3 = st.columns([1, 4, 1])
    with t1:
        if st.button("← GeralJá"):
            st.session_state.search_active = False
            st.rerun()
    with t2:
        st.session_state.query = st.text_input("", value=st.session_state.query)

    st.markdown("---")
    
    # Inteligência de Mapeamento (Somando os seus dados existentes)
    termo = st.session_state.query.lower()
    categoria_encontrada = None
    
    for cat, sinónimos in CONCEITOS_EXPANDIDOS.items():
        if termo in cat.lower() or any(s in termo for s in sinónimos):
            categoria_encontrada = cat
            break

    if categoria_encontrada:
        st.write(f"Exibindo resultados para: **{categoria_encontrada}**")
        
        # Simulando dados que viriam do seu Firebase
        st.markdown(f"""
            <div style="max-width: 600px; margin-bottom: 25px;">
                <div style="color: #202124; font-size: 14px;">https://www.geralja.com.br › {categoria_encontrada.lower()}</div>
                <div style="color: #1a0dab; font-size: 20px; cursor: pointer;">João Silva - {categoria_encontrada} Elite <span class="verificado">✔</span></div>
                <div style="color: #4d5156; font-size: 14px;">
                    ⭐ 5.0 · <b>Profissional Verificado</b> · Atende a 2km de você.<br>
                    Especialista em {categoria_encontrada} com mais de 10 anos de experiência.
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Chamar no WhatsApp"):
            st.success("Conectando ao profissional...")
    else:
        st.warning("Não encontramos exatamente o que você digitou. Tente termos como 'fome', 'vazamento' ou 'luz'.")

# --- RODAPÉ ---
st.markdown(f"<div style='position: fixed; bottom: 0; width: 100%; background: #f2f2f2; padding: 10px; color: #70757a; font-size: 14px;'>Brasil · São Paulo - Baseado no GeralJá v20.0</div>", unsafe_allow_html=True)
