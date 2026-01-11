import streamlit as st
import pandas as pd
import datetime
import math
import re
import unicodedata
from urllib.parse import quote

# 1. CONFIGURAÇÃO DE PÁGINA (ESTILO GOOGLE)
st.set_page_config(page_title="GeralJá | Pesquisa Inteligente", page_icon="🎯", layout="wide", initial_sidebar_state="collapsed")

# 2. BANCO DE DADOS EMBUTIDO (Simulando o que viria do Firebase)
# Aqui estão os dados que você já tinha espalhados nos apps
if 'db_local' not in st.session_state:
    st.session_state.db_local = [
        {"id": 1, "nome": "João Silva", "categoria": "Encanador", "nota": 4.9, "elite": True, "verificado": True, "whatsapp": "5511999999999", "descricao": "Especialista em vazamentos e tubulações de cobre.", "bairro": "Grajaú", "saldo": 150},
        {"id": 2, "nome": "Maria Reparos", "categoria": "Eletricista", "nota": 5.0, "elite": True, "verificado": True, "whatsapp": "5511888888888", "descricao": "Instalações elétricas residenciais e chuveiros.", "bairro": "Interlagos", "saldo": 200},
        {"id": 3, "nome": "Carlos Faxina", "categoria": "Diarista", "nota": 4.7, "elite": False, "verificado": True, "whatsapp": "5511777777777", "descricao": "Limpeza pesada e pós-obra.", "bairro": "Santo Amaro", "saldo": 50},
        {"id": 4, "nome": "Pizzaria da Villa", "categoria": "Alimentação", "nota": 4.8, "elite": False, "verificado": False, "whatsapp": "5511666666666", "descricao": "Melhor pizza artesanal da região.", "bairro": "Grajaú", "saldo": 10},
    ]

# 3. INTELIGÊNCIA DE MAPEAMENTO (IA DE BUSCA)
MAPA_IA = {
    "fome": "Alimentação",
    "pizza": "Alimentação",
    "vazamento": "Encanador",
    "cano": "Encanador",
    "curto": "Eletricista",
    "luz": "Eletricista",
    "sujeira": "Diarista",
    "limpeza": "Diarista"
}

# 4. FUNÇÕES DE UTILIDADE (Soma dos seus arquivos)
def normalizar_texto(texto):
    return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').lower()

def criar_link_whatsapp(numero, nome_cliente):
    msg = quote(f"Olá, vi seu perfil no GeralJá e gostaria de um orçamento!")
    return f"https://wa.me/{numero}?text={msg}"

# 5. ESTILIZAÇÃO CSS (GOOGLE MINIMALIST)
st.markdown("""
    <style>
        .stApp { background-color: white !important; }
        .nav-google { display: flex; justify-content: flex-end; padding: 10px 20px; gap: 15px; }
        .nav-item { color: #5f6368; text-decoration: none; font-size: 13px; font-family: Arial; }
        
        /* Barra de Busca */
        div.stTextInput > div > div > input {
            border-radius: 24px !important;
            border: 1px solid #dfe1e5 !important;
            padding: 12px 25px !important;
            box-shadow: none !important;
        }
        div.stTextInput > div > div > input:hover { box-shadow: 0 1px 6px rgba(32,33,36,0.28) !important; }

        /* Estilo dos Resultados */
        .result-box { max-width: 650px; margin-bottom: 25px; font-family: 'Arial', sans-serif; }
        .result-url { color: #202124; font-size: 14px; margin-bottom: 2px; }
        .result-title { color: #1a0dab; font-size: 20px; text-decoration: none; cursor: pointer; font-weight: 400; }
        .result-title:hover { text-decoration: underline; }
        .result-snippet { color: #4d5156; font-size: 14px; line-height: 1.5; }
        
        .badge-elite { background-color: #FF8C00; color: white; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: bold; }
        .verificado { color: #1a73e8; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 6. INTERFACE: MENU SUPERIOR
st.markdown("""
    <div class="nav-google">
        <a class="nav-item">Sobre o GeralJá</a>
        <a class="nav-item">Parceiros</a>
        <a class="nav-item"><b>Anunciar</b></a>
    </div>
""", unsafe_allow_html=True)

# 7. LOGICA DE ESTADO (HOME vs RESULTADOS)
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'search_term' not in st.session_state:
    st.session_state.search_term = ""

# --- MODO HOME ---
if st.session_state.page == 'home':
    st.write("##")
    st.write("##")
    st.write("##")
    # Logo Google-Style
    st.markdown("<h1 style='text-align: center; font-size: 90px; font-family: sans-serif; letter-spacing: -4px;'><span style='color:#4285F4'>G</span><span style='color:#EA4335'>e</span><span style='color:#FBBC05'>r</span><span style='color:#4285F4'>a</span><span style='color:#34A853'>l</span><span style='color:#EA4335'>Já</span></h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        query = st.text_input("", placeholder="Busque um serviço ou problema (ex: vazamento)", key="main_search")
        st.write("##")
        b1, b2, b3, b4, b5 = st.columns(5)
        with b2:
            if st.button("Pesquisa GeralJá", use_container_width=True) or (query != ""):
                if query:
                    st.session_state.search_term = query
                    st.session_state.page = 'results'
                    st.rerun()
        with b4:
            st.button("Estou com Sorte", use_container_width=True)

# --- MODO RESULTADOS ---
else:
    t1, t2, t3 = st.columns([1, 4, 1])
    with t1:
        if st.button("← Home"):
            st.session_state.page = 'home'
            st.rerun()
    with t2:
        st.session_state.search_term = st.text_input("", value=st.session_state.search_term)

    st.markdown("---")
    
    # IA de Busca (Mapeamento de Sinônimos)
    termo_norm = normalizar_texto(st.session_state.search_term)
    categoria_alvo = MAPA_IA.get(termo_norm, st.session_state.search_term)
    
    resultados = [p for p in st.session_state.db_local if normalizar_texto(categoria_alvo) in normalizar_texto(p['categoria']) or normalizar_texto(categoria_alvo) in normalizar_texto(p['descricao'])]
    
    # Ranking Inteligente: Elite e Saldo no topo
    resultados = sorted(resultados, key=lambda x: (x['elite'], x['saldo']), reverse=True)

    if resultados:
        st.write(f"Cerca de {len(resultados)} profissionais encontrados para '{st.session_state.search_term}'")
        for p in resultados:
            elite = "<span class='badge-elite'>ELITE</span>" if p['elite'] else ""
            verificado = "<span class='verificado'>✔</span>" if p['verificado'] else ""
            link_wa = criar_link_whatsapp(p['whatsapp'], "Cliente")
            
            st.markdown(f"""
                <div class="result-box">
                    <div class="result-url">https://www.geralja.com.br › {normalizar_texto(p['categoria'])}</div>
                    <a href="{link_wa}" target="_blank" class="result-title">{p['nome']} {verificado} {elite}</a>
                    <div class="result-snippet">
                        <b>⭐ {p['nota']}</b> · Profissional em {p['bairro']} · Atende agora.<br>
                        {p['descricao']}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if st.button(f"Falar com {p['nome']}", key=f"btn_{p['id']}"):
                st.write(f"📲 Abrindo WhatsApp de {p['nome']}...")
    else:
        st.warning("Nenhum resultado encontrado. Tente 'fome', 'vazamento' ou 'luz'.")

# 8. RODAPÉ (VARREDOR)
st.markdown("<div style='position: fixed; bottom: 0; width: 100%; background: #f2f2f2; padding: 10px; text-align: center; color: #70757a; font-size: 13px;'>Brasil · São Paulo - Baseado no seu histórico local · GeralJá v20.0</div>", unsafe_allow_html=True)
