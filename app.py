import streamlit as st
from core.engine import GeralJaEngine
# Importando os seus containers (módulos)
from modules.vitrine import buscar_profissionais, exibir_cards_profissionais
from modules.clima_transito import mostrar_clima_transito
from admin.controller import renderizar_admin
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# ... agora vêm os seus imports ...
from core.engine import Engine

# 1. Configuração da página (Deve ser a primeira linha após os imports)
st.set_page_config(page_title="GeralJá | Oficial", layout="wide")

# 2. Inicialização do motor (Conexão única)
@st.cache_resource
def iniciar_sistema():
    engine = GeralJaEngine()
    return engine

engine = iniciar_sistema()
db = engine.get_db()

# 3. Sidebar (Menu de navegação entre os containers)
menu = st.sidebar.selectbox("Menu GeralJá", ["Vitrine de Serviços", "Clima e Trânsito", "Administração"])

# 4. Roteamento de containers (O "mestre" chamando cada parte)
if menu == "Vitrine de Serviços":
    st.header("📍 Busca de Profissionais")
    termo = st.text_input("O que você procura?")
    if termo:
        resultados = buscar_profissionais(db, termo)
        exibir_cards_profissionais(resultados)

elif menu == "Clima e Trânsito":
    # Aqui o seu container de clima e trânsito entra em ação
    mostrar_clima_transito()

elif menu == "Administração":
    # Apenas para você, com autenticação
    if st.session_state.get("auth"):
        renderizar_admin(db)
    else:
        st.warning("Área restrita. Faça login.")

# 5. Rodapé fixo
st.sidebar.markdown("---")
st.sidebar.info("GeralJá v2.0 - O Grajaú conectado.")
