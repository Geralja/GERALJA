# ==============================================================================
# GERALJÁ: SISTEMA INTEGRAL - MASTER APP (ORQUESTRADOR)
# ==============================================================================
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64, json, sys, os, importlib

# --- 1. CONFIGURAÇÃO E FIREBASE (BLINDADO) ---
@st.cache_resource
def iniciar_banco():
    if not firebase_admin._apps:
        # Pega a chave do secrets com segurança
        b64_key = st.secrets["firebase"]["base64"]
        cred = credentials.Certificate(json.loads(base64.b64decode(b64_key).decode("utf-8")))
        firebase_admin.initialize_app(cred)
    return firestore.client()

# Inicializa o banco uma única vez
db = iniciar_banco()

# --- 2. ENGINE E CONFIGURAÇÕES GLOBAIS ---
st.set_page_config(page_title="GeralJá", layout="wide")

# CSS Global para manter a identidade visual
st.markdown("""
<style>
    .header-container { background: white; padding: 20px; border-radius: 0 0 50px 50px; text-align: center; border-bottom: 8px solid #FF8C00; margin-bottom: 25px; }
    .logo-azul { color: #0047AB; font-weight: 900; font-size: 40px; }
    .logo-laranja { color: #FF8C00; font-weight: 900; font-size: 40px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-container"><span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span></div>', unsafe_allow_html=True)

# --- 3. ORQUESTRAÇÃO POR ABAS ---
menu_abas = st.tabs(["🔍 BUSCAR", "🚀 CADASTRAR", "👤 MEU PERFIL", "👑 ADMIN", "⭐ FEEDBACK"])

# O app.py agora chama os módulos para cada aba
# Isso mantém o app.py leve e fácil de ler
with menu_abas[0]:
    # Exemplo: Chamando um plugin de busca
    if os.path.exists("modulos/busca.py"):
        import modulos.busca as busca
        busca.run()
    else: st.warning("Módulo de busca não encontrado.")

with menu_abas[1]:
    if os.path.exists("modulos/cadastro.py"):
        import modulos.cadastro as cadastro
        cadastro.run()

with menu_abas[2]:
    if os.path.exists("modulos/perfil.py"):
        import modulos.perfil as perfil
        perfil.run()

with menu_abas[3]:
    if os.path.exists("modulos/admin.py"):
        import modulos.admin as admin
        admin.run()

# --- 4. MOTOR DE PLUGINS (PARA FUNÇÕES EXTRAS/FUNDO) ---
def carregar_plugins_extras():
    pasta_plugins = os.path.join(os.getcwd(), "modulos/plugins")
    if not os.path.exists(pasta_plugins): return
    
    for arquivo in os.listdir(pasta_plugins):
        if arquivo.endswith(".py") and arquivo != "__init__.py":
            try:
                spec = importlib.util.spec_from_file_location(arquivo[:-3], os.path.join(pasta_plugins, arquivo))
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, "run"): mod.run()
            except Exception as e:
                st.error(f"Erro no plugin {arquivo}: {e}")

carregar_plugins_extras()
