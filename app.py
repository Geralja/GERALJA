# ==============================================================================
# GERALJÁ: SISTEMA DE INTELIGÊNCIA LOCAL - VERSÃO AGENTE 2026.06
# ==============================================================================
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from groq import Groq
import feedparser
from datetime import datetime
def _sintetizar_resposta(self, query, locais, noticias):
        # 1. Validação: Garante que os dados não são None
        locais_str = str(locais) if locais else "Nenhuma informação local encontrada."
        noticias_str = str(noticias) if noticias else "Nenhuma notícia recente disponível."
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system", 
                        "content": "Você é a IA do Grajaú Tem. Responda como um morador local, direto e útil. Use 1-2 emojis no máximo."
                    },
                    {
                        "role": "user", 
                        "content": f"O usuário busca: '{query}'. \n\nDados de apoio: \nLocais: {locais_str} \nNotícias: {noticias_str} \n\nResponda agora:"
                    }
                ],
                model="llama3-70b-8192", 
                temperature=0.5, # Adicionado para estabilidade
                max_tokens=500   # Adicionado para evitar estouro
            )
            return chat_completion.choices[0].message.content
            
        except Exception as e:
            # 2. Isso vai mostrar o erro exato na tela em vez de esconder
            return f"🚨 Erro na síntese (IA): {str(e)}"

# --- [BLOCO A] CONFIGURAÇÃO E ENGINE ---
st.set_page_config(page_title="GeralJá | Busca Inteligente", page_icon="📍", layout="centered")

class GeralJaEngine:
    def __init__(self):
        self.client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        
    def busca_tripla_inteligencia(self, query):
        """Orquestrador das 3 IAs"""
        # 1. IA Local (Dados Estruturados)
        dados_locais = self._buscar_firestore(query)
        
        # 2. IA de Monitoramento (Notícias Atuais)
        noticias_atuais = self._buscar_feeds()
        
        # 3. IA de Síntese (Groq processando tudo)
        resposta = self._sintetizar_resposta(query, dados_locais, noticias_atuais)
        return resposta

    def _buscar_firestore(self, query):
        # Lógica de busca vetorial/fuzzy no Firestore
        return "Dados encontrados no catálogo local..."

    def _buscar_feeds(self):
        # Lógica de monitoramento de notícias em tempo real
        return "Notícias do Grajaú Tem processadas..."

    def _sintetizar_resposta(self, query, locais, noticias):
        chat_completion = self.client.chat.completions.create(
            messages=[{"role": "system", "content": "Você é a IA do Grajaú Tem. Responda como um morador local, direto e útil."},
                      {"role": "user", "content": f"O usuário busca: {query}. Baseado em {locais} e {noticias}, responda:"}],
            model="llama3-70b-8192",
        )
        return chat_completion.choices[0].message.content

# --- [BLOCO B] INTERFACE MODERNA (ESTILO GOOGLE) ---
def renderizar_ui_moderna():
    st.markdown("""
        <style>
            .stApp { background: #0f172a; color: white; }
            .search-box { width: 100%; padding: 20px; border-radius: 50px; border: 1px solid #334155; }
        </style>
    """, unsafe_allow_html=True)

    st.title("📍 GeralJá")
    query = st.text_input("", placeholder="O que você procura no Grajaú hoje?", label_visibility="collapsed")
    
    if query:
        with st.spinner("Consultando inteligências..."):
            engine = GeralJaEngine()
            resultado = engine.busca_tripla_inteligencia(query)
            st.markdown(f"<div class='card-pro'>{resultado}</div>", unsafe_allow_html=True)

# --- [BLOCO C] FLUXO DE SEGURANÇA ---
if 'logado' not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    renderizar_ui_moderna()
    if st.button("Acesso Profissional"): st.session_state.logado = True
else:
    st.sidebar.title("Painel de Controle")
    # Aqui entram as funções de admin citadas na Revisão-e-melhoria-de-código.py
