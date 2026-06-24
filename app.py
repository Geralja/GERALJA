import streamlit as st
import sys
import os
import os
import sys
# Isso garante que a pasta atual seja sempre reconhecida como o 'coração' do projeto
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# AGORA sim, pode fazer os imports:
from core.engine import GeralJaEngine
# ... resto do código

# --- BLINDAGEM DE CAMINHO ---
# Garante que o Python sempre encontre as pastas 'core', 'modules', etc.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- IMPORTS MODULARES ---
from core.engine import GeralJaEngine
from modules.vitrine import buscar_profissionais, exibir_cards_profissionais
from modules.clima_transito import mostrar_clima_transito
from admin.controller import renderizar_admin

# --- CONFIGURAÇÃO DE ELITE ---
st.set_page_config(page_title="GeralJá | Oficial", layout="wide", page_icon="📍")

# --- INICIALIZAÇÃO SEGURA ---
@st.cache_resource
def iniciar_sistema():
    try:
        engine = GeralJaEngine()
        return engine
    except Exception as e:
        st.error(f"Erro ao inicializar o motor: {e}")
        return None

engine = iniciar_sistema()
if engine:
    db = engine.get_db()

    # --- NAVEGAÇÃO ESTRUTURADA ---
    menu = st.sidebar.selectbox("Menu GeralJá", ["Vitrine de Serviços", "Clima e Trânsito", "Administração"])

    if menu == "Vitrine de Serviços":
        st.header("📍 Busca de Profissionais")
        termo = st.text_input("O que você procura hoje no Grajaú?")
        if termo:
            # A lógica de busca fica dentro do módulo 'vitrine'
            resultados = buscar_profissionais(db, termo)
            exibir_cards_profissionais(resultados)

    elif menu == "Clima e Trânsito":
        mostrar_clima_transito()

    elif menu == "Administração":
        if st.session_state.get("auth"):
            renderizar_admin(db)
        else:
            st.warning("Área restrita. Por favor, faça login.")

    st.sidebar.markdown("---")
    st.sidebar.info("GeralJá v2.0 - O Grajaú conectado.")
else:
    st.error("Não foi possível conectar ao sistema. Verifique o banco de dados.")
