import streamlit as st
import math
import datetime
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA (ESTILO GOOGLE) ---
st.set_page_config(page_title="GeralJá Brasil", layout="centered", initial_sidebar_state="collapsed")

# --- UI IMPLEMENTATION (MINIMALIST WHITE) ---
st.markdown("""
    <style>
        /* Fundo Branco e Fontes Limpas */
        .stApp { background-color: white; }
        
        /* Estilo da Barra de Busca Google */
        .search-container {
            display: flex;
            justify-content: center;
            padding-top: 50px;
        }
        
        div.stTextInput > div > div > input {
            border-radius: 24px !important;
            border: 1px solid #dfe1e5 !important;
            padding: 12px 20px !important;
            font-size: 16px !important;
            box-shadow: none !important;
        }
        
        div.stTextInput > div > div > input:hover, div.stTextInput > div > div > input:focus {
            box-shadow: 0 1px 6px rgba(32,33,36,0.28) !important;
            border-color: rgba(223,225,229,0) !important;
        }

        /* Badge Elite e Verificado */
        .badge-elite {
            background-color: #FACC15;
            color: black;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 10px;
            font-weight: bold;
            margin-left: 5px;
        }
        
        .badge-verificado {
            color: #1a73e8;
            font-size: 14px;
            margin-left: 5px;
        }

        /* Card de Resultados (Estilo Google Search) */
        .result-card {
            padding: 15px 0px;
            border-bottom: 1px solid #f1f3f4;
            max-width: 600px;
        }
        
        .result-title {
            color: #1a0dab;
            font-size: 20px;
            text-decoration: none;
            cursor: pointer;
        }
        
        .result-title:hover { text-decoration: underline; }
        
        .result-url { color: #202124; font-size: 14px; margin-bottom: 2px; }
        
        .result-desc { color: #4d5156; font-size: 14px; line-height: 1.5; }
    </style>
""", unsafe_allow_html=True)

# --- MAPPING SEARCH IMPLEMENTATION (IA SIMULADA) ---
MAPA_IA = {
    "fome": "Alimentação/Pizzaria",
    "vazamento": "Encanador",
    "cano": "Encanador",
    "curto": "Eletricista",
    "luz": "Eletricista",
    "escuro": "Eletricista",
    "limpeza": "Diarista/Faxina",
    "sujeira": "Diarista/Faxina"
}

# Dados de Exemplo (Building the System)
DATA_PROFISSIONAIS = [
    {"nome": "João Silva", "cat": "Encanador", "nota": 4.9, "elite": True, "verificado": True, "dist": 1.2, "whats": "5511999999999", "desc": "Especialista em caça-vazamentos e reparos hidráulicos residenciais."},
    {"nome": "Maria Limpeza", "cat": "Diarista/Faxina", "nota": 4.8, "elite": False, "verificado": True, "dist": 0.8, "whats": "5511888888888", "desc": "Limpeza pós-obra e organização de closets com certificação profissional."},
    {"nome": "Carlos Volts", "cat": "Eletricista", "nota": 5.0, "elite": True, "verificado": True, "dist": 2.5, "whats": "5511777777777", "desc": "Instalações elétricas, quadros de força e manutenção de ar-condicionado."},
]

# --- LÓGICA DE BUSCA ---
def realizar_busca(query):
    query = query.lower()
    # IA Mapping: traduz termos genéricos para categorias reais
    categoria_alvo = MAPA_IA.get(query, query)
    
    resultados = [p for p in DATA_PROFISSIONAIS if categoria_alvo in p['cat'].lower() or categoria_alvo in p['desc'].lower()]
    # Ranking System (Elite > Nota > Distância)
    return sorted(resultados, key=lambda x: (x['elite'], x['nota'], -x['dist']), reverse=True)

# --- UI: HOME STATE (ESTILO GOOGLE.COM) ---
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""

if not st.session_state.search_query:
    st.write("##")
    st.write("##")
    st.markdown("<h1 style='text-align: center; font-size: 80px;'><span style='color:#4285F4'>G</span><span style='color:#EA4335'>e</span><span style='color:#FBBC05'>r</span><span style='color:#4285F4'>a</span><span style='color:#34A853'>l</span><span style='color:#EA4335'>Já</span></h1>", unsafe_allow_html=True)
    
    query = st.text_input("", key="main_search", placeholder="O que você precisa agora?")
    
    col1, col2, col3, col4 = st.columns([1,1,1,1])
    with col2:
        if st.button("Pesquisa GeralJá", use_container_width=True):
            st.session_state.search_query = query
            st.rerun()
    with col3:
        st.button("Estou com Sorte", use_container_width=True)

# --- UI: RESULTS STATE (GOOGLE SEARCH RESULTS) ---
else:
    # Top Bar Minimalista
    t1, t2, t3 = st.columns([1, 4, 1])
    with t1:
        if st.button("← Voltar"):
            st.session_state.search_query = ""
            st.rerun()
    with t2:
        new_query = st.text_input("", value=st.session_state.search_query)
    
    st.markdown("---")
    
    results = realizar_busca(st.session_state.search_query)
    
    if results:
        st.write(f"Aproximadamente {len(results)} resultados encontrados.")
        for p in results:
            elite_tag = "<span class='badge-elite'>ELITE</span>" if p['elite'] else ""
            veri_tag = "<span class='badge-verificado'>●</span>" if p['verificado'] else ""
            
            st.markdown(f"""
                <div class="result-card">
                    <div class="result-url">https://www.geralja.com.br/profissional/{p['nome'].replace(' ','_').lower()}</div>
                    <div class="result-title">{p['nome']} {veri_tag} {elite_tag}</div>
                    <div class="result-desc">
                        <b>{p['cat']}</b> · ⭐ {p['nota']} · 📍 {p['dist']}km de distância<br>
                        {p['desc']}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if st.button(f"Entrar em contato com {p['nome']}", key=p['nome']):
                st.success(f"Redirecionando para o WhatsApp de {p['nome']}...")
    else:
        st.warning("Nenhum profissional encontrado para essa busca. Tente 'fome', 'vazamento' ou 'luz'.")

# --- FOOTER ---
st.markdown("<br><br><div style='text-align:center; color:#70757a; font-size:14px;'>Brasil · São Paulo - Baseado no seu histórico · GeralJá Landing Page 2025</div>", unsafe_allow_html=True)
