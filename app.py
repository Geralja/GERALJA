# ==============================================================================
# GERALJÁ - MASTER SKELETON (Versão 6.0 - Arquitetura de Execução Inteligente)
# Ordem: 1.Imports -> 2.Config -> 3.Motores -> 4.UI -> 5.Main
# ==============================================================================

# --- 1. IMPORTS (Hierarquia absoluta) ---
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64, json, math, re, time, io, pandas as pd, pytz, unicodedata, requests, feedparser, urllib.parse
from datetime import datetime
from PIL import Image
from groq import Groq
from fuzzywuzzy import process
from urllib.parse import quote
import google.generativeai as genai
from google_auth_oauthlib.flow import Flow

# Fallback seguro para componentes JS
try:
    from streamlit_js_eval import streamlit_js_eval, get_geolocation
except Exception:
    streamlit_js_eval, get_geolocation = None, None

# --- 2. CONFIGURAÇÕES GERAIS ---
# Config de página deve ser o primeiro comando Streamlit
st.set_page_config(page_title="GeralJá | Grajaú Tem", page_icon="📍", layout="wide")

# CSS "Bonito" e "Atrativo" (Injetado logo no início)
st.markdown("""
    <style>
        .main-container { padding: 20px; }
        .hero-title { text-align: center; font-size: 3.5rem; font-weight: 800; color: #003399; }
        .hero-subtitle { text-align: center; color: #FFD700; font-size: 3.5rem; font-weight: 800; }
        .search-container { max-width: 700px; margin: 40px auto; }
        .footer { text-align: center; color: #718096; font-size: 12px; margin-top: 50px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. MOTORES E INFRAESTRUTURA (Firebase/IA) ---
def init_firebase():
    if not firebase_admin._apps:
        # Aqui você coloca o carregamento do seu JSON de credencial
        # cred = credentials.Certificate("seu_arquivo_firebase.json")
        # firebase_admin.initialize_app(cred)
        pass
    return firestore.client() if firebase_admin._apps else None

def motor_busca(query):
    # Lógica de busca entra aqui
    return "Lógica de busca a ser implementada"

# --- 4. FUNÇÕES DE INTERFACE (Os "Quadros") ---
def renderizar_header():
    st.markdown('<div class="hero-title">Portal <span class="hero-subtitle">Grajaú Tem</span></div>', unsafe_allow_html=True)

def renderizar_busca():
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        query = st.text_input("", placeholder="O que você procura no Grajaú?", key="main_search")
        if query:
            st.session_state.pesquisou = True
            st.session_state.query = query
            st.rerun()

def renderizar_vitrine():
    st.write(f"### Resultados para: {st.session_state.get('query', '')}")
    # Aqui vamos chamar a vitrine dinâmica no futuro
    if st.button("Voltar"):
        st.session_state.pesquisou = False
        st.rerun()

# --- 5. EXECUÇÃO (MAIN) ---
def main():
    # Inicializa estado
    if 'pesquisou' not in st.session_state: st.session_state.pesquisou = False
    
    # Inicializa Banco
    db = init_firebase()
    
    # Fluxo principal
    if not st.session_state.pesquisou:
        renderizar_header()
        renderizar_busca()
    else:
        renderizar_vitrine()

if __name__ == "__main__":
    main()
# --- [BLOCO 01: CSS PREMIUM - IDENTIDADE VISUAL] ---
def aplicar_estilo_premium():
    st.markdown("""
        <style>
            /* Reset básico para centralização */
            .main .block-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 80vh;
            }
            
            /* Tipografia Premium */
            .logo-azul { color: #003399; font-size: 4rem; font-weight: 800; }
            .logo-amarelo { color: #FFD700; font-size: 4rem; font-weight: 800; }
            
            /* O "Coração" do Design: O Input de Busca */
            div[data-baseweb="input"] {
                border-radius: 50px !important;
                border: 1px solid #dfe1e5 !important;
                box-shadow: 0 1px 6px rgba(32,33,36,0.28) !important;
                padding: 10px 20px !important;
                transition: box-shadow 0.3s;
            }
            div[data-baseweb="input"]:hover {
                box-shadow: 0 4px 12px rgba(32,33,36,0.28) !important;
            }
            
            /* Ajuste para o texto centralizado */
            .stTextInput label { display: none; }
        </style>
    """, unsafe_allow_html=True)

# Chamada da função no início da sua UI
aplicar_estilo_premium()
# --- [BLOCO 02: MOTOR DE DADOS - FIREBASE E CACHE] ---

@st.cache_resource
def get_db_connection():
    """Conecta ao Firebase apenas uma vez e guarda na memória."""
    try:
        if not firebase_admin._apps:
            # Garanta que o arquivo 'firebase_key.json' esteja na raiz
            cred = credentials.Certificate("firebase_key.json")
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"Erro ao conectar ao banco: {e}")
        return None

@st.cache_data(ttl=600) # O cache dura 10 minutos (600 segundos)
def buscar_vitrine_completa():
    """Busca toda a vitrine do Firebase e retorna uma lista limpa."""
    db = get_db_connection()
    if not db: return []
    
    # Busca a coleção 'loja' (ou a que você usa)
    docs = db.collection("loja").stream()
    
    lista_itens = []
    for doc in docs:
        item = doc.to_dict()
        item['id'] = doc.id  # Importante: mantemos o ID para deletar/editar depois
        lista_itens.append(item)
    return lista_itens

def salvar_item_firebase(dados):
    """Função robusta para salvar um novo item na loja."""
    db = get_db_connection()
    try:
        db.collection("loja").add(dados)
        st.cache_data.clear() # Limpa o cache para mostrar o novo item na hora
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

def deletar_item_firebase(item_id):
    """Função para deletar, verificando se o ID existe."""
    db = get_db_connection()
    try:
        db.collection("loja").document(item_id).delete()
        st.cache_data.clear() # Limpa o cache para atualizar a lista
        return True
    except Exception:
        return False
        # --- [BLOCO 03: MOTOR DE BUSCA INTELIGENTE] ---

def normalizar_texto(texto):
    """Remove acentos, converte para minúsculo e limpa espaços."""
    if not texto: return ""
    texto = unicodedata.normalize('NFKD', str(texto)).encode('ASCII', 'ignore').decode('utf-8')
    return texto.lower().strip()

def motor_busca_inteligente(query_usuario, data_vitrine):
    """
    O Coração do seu Portal:
    1. Normaliza busca e dados.
    2. Usa FuzzyWuzzy para tolerar erros de digitação.
    3. Ordena os resultados por relevância.
    """
    if not query_usuario or not data_vitrine:
        return []

    query_limpa = normalizar_texto(query_usuario)
    resultados = []

    for item in data_vitrine:
        # Pega campos que vamos buscar (Nome, Categoria, Descrição)
        nome = normalizar_texto(item.get('nome', ''))
        cat = normalizar_texto(item.get('categoria', ''))
        desc = normalizar_texto(item.get('descricao', ''))
        
        # Fuzzy Matching: compara a busca com cada campo (retorna score 0-100)
        score_nome = process.extractOne(query_limpa, [nome])[1] if nome else 0
        score_cat = process.extractOne(query_limpa, [cat])[1] if cat else 0
        score_desc = process.extractOne(query_limpa, [desc])[1] if desc else 0
        
        # O score final é o melhor entre os três
        melhor_score = max(score_nome, score_cat, score_desc)
        
        # Filtro de qualidade: só traz resultados com relevância mínima
        if melhor_score > 50:
            item['score'] = melhor_score
            resultados.append(item)

    # Ordena: Quem tem score maior aparece primeiro
    resultados_ordenados = sorted(resultados, key=lambda x: x['score'], reverse=True)
    
    return resultados_ordenados
    # --- [BLOCO 03.5: IA DE REFINAMENTO (O CÉREBRO 5.0)] ---

def refinar_resultados_com_ia(query_usuario, resultados_iniciais):
    """
    Pega os resultados do motor fuzzy e usa a IA (Groq) para escolher
    os melhores baseados na intenção do morador.
    """
    if not resultados_iniciais or len(resultados_iniciais) <= 1:
        return resultados_iniciais

    # Prepara uma lista resumida para a IA analisar
    lista_opcoes = ""
    for i, item in enumerate(resultados_iniciais):
        lista_opcoes += f"{i}: {item.get('nome')} | {item.get('categoria')} | {item.get('descricao')}\n"

    # Prompt de Alta Inteligência
    prompt = f"""
    O usuário no Grajaú buscou por: '{query_usuario}'.
    Aqui estão os estabelecimentos encontrados:
    {lista_opcoes}
    
    Analise os estabelecimentos e retorne apenas a lista de índices (0, 1, 2...) 
    ordenados do mais relevante para o menos relevante. 
    Responda apenas com os números separados por vírgula.
    """

    try:
        # Chamada ao motor Groq (já configurado no seu arquivo)
        client = Groq(api_key=st.secrets["GROQ_API_KEY"]) # Certifique-se de ter essa chave no Streamlit
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-70b-8192",
        )
        
        # Processa a resposta da IA
        indices_ordenados = [int(x.strip()) for x in chat_completion.choices[0].message.content.split(",")]
        
        # Reordena a lista original
        resultados_finais = []
        for idx in indices_ordenados:
            if idx < len(resultados_iniciais):
                resultados_finais.append(resultados_iniciais[idx])
        
        return resultados_finais

    except Exception as e:
        # Se a IA falhar, a gente volta pro 3.5 (Segurança contra erro)
        return resultados_iniciais
        # --- [BLOCO 04: VITRINE DE ALTA CONVERSÃO] ---

def renderizar_card(item):
    """
    Renderiza um card individual com design premium.
    """
    with st.container():
        st.markdown(f"""
        <style>
            .card-premium {{
                border-radius: 15px;
                padding: 20px;
                background-color: white;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                margin-bottom: 20px;
                border-left: 5px solid #003399; /* Azul Grajaú Tem */
                transition: transform 0.2s;
            }}
            .card-premium:hover {{ transform: scale(1.02); }}
            .card-title {{ font-size: 1.4rem; font-weight: bold; color: #1a1a1a; margin-bottom: 5px; }}
            .card-category {{ color: #718096; font-size: 0.9rem; margin-bottom: 10px; }}
            .card-desc {{ color: #4a5568; font-size: 1rem; margin-bottom: 15px; }}
        </style>
        """, unsafe_allow_html=True)
        
        # Estrutura do Card
        col_img, col_info = st.columns([1, 3])
        
        with col_img:
            # Imagem do comerciante ou placeholder
            st.image(item.get('foto_url', 'https://via.placeholder.com/150'), use_container_width=True)
            
        with col_info:
            st.markdown(f'<div class="card-title">{item.get("nome", "Sem nome")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card-category">🏷️ {item.get("categoria", "Geral")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card-desc">{item.get("descricao", "Sem descrição disponível.")}</div>', unsafe_allow_html=True)
            
            # Botão de ação (WhatsApp)
            zap = item.get('whatsapp', '5511999999999')
            st.link_button("💬 Chamar no WhatsApp", f"https://wa.me/{zap}")
