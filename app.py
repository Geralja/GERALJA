import streamlit as st
import sys
import os

# Adiciona o diretório atual ao caminho para garantir que o Python ache as pastas
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Importações corrigidas (use sempre o nome exato da classe definida no seu engine.py)
from core.engine import GeralJaEngine
from modules.vitrine import buscar_profissionais, exibir_cards_profissionais
from modules.clima_transito import mostrar_clima_transito
from admin.controller import renderizar_admin

# 1. Configuração da página
st.set_page_config(page_title="GeralJá | Oficial", layout="wide")

# 2. Inicialização do motor (Conexão única)
@st.cache_resource
def iniciar_sistema():
    return GeralJaEngine()

engine = iniciar_sistema()
# Se o seu método for get_db(), mantenha. Se o atributo for apenas db, use engine.db
db = engine.get_db() 

# 3. Sidebar (Menu de navegação)
menu = st.sidebar.selectbox("Menu GeralJá", ["Vitrine de Serviços", "Clima e Trânsito", "Administração"])

# 4. Roteamento de containers
if menu == "Vitrine de Serviços":
    st.header("📍 Busca de Profissionais")
    termo = st.text_input("O que você procura?")
    if termo:
        resultados = buscar_profissionais(db, termo)
        exibir_cards_profissionais(resultados)

elif menu == "Clima e Trânsito":
    mostrar_clima_transito()

elif menu == "Administração":
    if st.session_state.get("auth"):
        renderizar_admin(db)
    else:
        st.warning("Área restrita. Faça login.")

# 5. Rodapé fixo
st.sidebar.markdown("---")
st.sidebar.info("GeralJá v2.0 - O Grajaú conectado.")
