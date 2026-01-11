import streamlit as st
import datetime
import pandas as pd
from urllib.parse import quote

# 1. CONFIGURAÇÃO DE PÁGINA
st.set_page_config(page_title="GeralJá | Brasil", layout="wide", initial_sidebar_state="collapsed")

# 2. ESTADO GLOBAL (O "Cérebro" da Navegação)
if 'pagina_atual' not in st.session_state:
    st.session_state.pagina_atual = 'home'
if 'busca' not in st.session_state:
    st.session_state.busca = ""

# 3. BANCO DE DADOS LOCAL (Funcionalidade de Teste)
DB_EXEMPLO = [
    {"nome": "Ricardo Silva", "cat": "Encanador", "nota": 4.9, "elite": True, "tel": "5511999999999", "desc": "Especialista em reparos rápidos e detecção de vazamentos."},
    {"nome": "Ana Tomadas", "cat": "Eletricista", "nota": 5.0, "elite": True, "tel": "5511888888888", "desc": "Instalações elétricas residenciais e manutenção de quadros."},
]

# 4. ESTILIZAÇÃO CSS (Organização dos Botões)
st.markdown("""
    <style>
        .stApp { background-color: white !important; }
        
        /* Botão Estilo Google Search */
        .stButton>button {
            background-color: #f8f9fa;
            color: #3c4043;
            border: 1px solid #f8f9fa;
            border-radius: 4px;
            padding: 8px 16px;
            font-family: arial,sans-serif;
            font-size: 14px;
            margin: 11px 4px;
        }
        .stButton>button:hover {
            border: 1px solid #dadce0;
            color: #202124;
            box-shadow: 0 1px 1px rgba(0,0,0,.1);
        }
        
        /* Botão de WhatsApp (Chamada para Ação) */
        .btn-whats {
            background-color: #25D366 !important;
            color: white !important;
            border-radius: 20px !important;
        }
    </style>
""", unsafe_allow_html=True)

# 5. FUNÇÕES DE FUNCIONALIDADE
def ir_para(pagina):
    st.session_state.pagina_atual = pagina
    st.rerun()

def abrir_whats(numero, nome_p):
    texto = quote(f"Olá {nome_p}, vi seu perfil no GeralJá e gostaria de um orçamento.")
    link = f"https://wa.me/{numero}?text={texto}"
    st.markdown(f'<meta http-equiv="refresh" content="0;URL={link}">', unsafe_allow_html=True)

# 6. MENU SUPERIOR FUNCIONAL
col_nav1, col_nav2 = st.columns([6, 1])
with col_nav2:
    if st.button("⚙️ Admin", key="btn_admin_nav"):
        ir_para('admin')

# ------------------------------------------------------------------------------
# INTERFACE DINÂMICA
# ------------------------------------------------------------------------------

# --- PÁGINA: HOME ---
if st.session_state.pagina_atual == 'home':
    st.write("##")
    st.write("##")
    st.markdown("<h1 style='text-align: center; font-size: 90px; color:#4285F4; font-family: sans-serif;'>GeralJá</h1>", unsafe_allow_html=True)
    
    col_s1, col_s2, col_s3 = st.columns([1, 2, 1])
    with col_s2:
        query = st.text_input("", placeholder="O que você precisa agora?", key="input_busca")
        
        c1, c2, c3, c4, c5 = st.columns(5)
        with c2:
            if st.button("Buscar Agora", use_container_width=True) or (query != ""):
                if query:
                    st.session_state.busca = query
                    ir_para('resultados')
        with c4:
            if st.button("Sou Profissional", use_container_width=True):
                ir_para('cadastro')

# --- PÁGINA: RESULTADOS ---
elif st.session_state.pagina_atual == 'resultados':
    t1, t2 = st.columns([1, 5])
    with t1:
        if st.button("← Voltar"): ir_para('home')
    with t2:
        st.subheader(f"Resultados para: {st.session_state.busca}")
    
    st.divider()
    
    # Exibição Funcional dos Cards
    for p in DB_EXEMPLO:
        with st.container():
            col_res1, col_res2 = st.columns([4, 1])
            with col_res1:
                elite = "🟠 ELITE" if p['elite'] else ""
                st.markdown(f"### {p['nome']} {elite}")
                st.caption(f"{p['cat']} • ⭐ {p['nota']}")
                st.write(p['desc'])
            with col_res2:
                st.write("##")
                if st.button(f"Contratar", key=f"whats_{p['nome']}"):
                    abrir_whats(p['tel'], p['nome'])
            st.divider()

# --- PÁGINA: ADMIN (O COFRE) ---
elif st.session_state.pagina_atual == 'admin':
    if st.button("← Sair do Painel"): ir_para('home')
    st.title("🛡️ Painel de Controle GeralJá")
    
    senha = st.text_input("Chave Mestra", type="password")
    if senha == "riqueza2026":
        st.success("Acesso Autorizado")
        st.metric("Total de Parceiros", len(DB_EXEMPLO))
        # Aqui você colocaria a tabela do Firebase que vimos nos seus arquivos
    else:
        st.warning("Insira a senha para ver os dados faturamento.")

# --- PÁGINA: CADASTRO ---
elif st.session_state.pagina_atual == 'cadastro':
    if st.button("← Cancelar"): ir_para('home')
    st.title("💼 Cadastro de Novo Parceiro")
    with st.form("form_cadastro"):
        nome = st.text_input("Nome Completo")
        cat = st.selectbox("Categoria", ["Encanador", "Eletricista", "Diarista", "Mecânico"])
        whats = st.text_input("WhatsApp (com DDD)")
        if st.form_submit_button("FINALIZAR CADASTRO"):
            st.balloons()
            st.success("Cadastro enviado para aprovação!")

# ------------------------------------------------------------------------------
# RODAPÉ
# ------------------------------------------------------------------------------
st.markdown(f"<div style='position: fixed; bottom: 0; width: 100%; text-align: center; padding: 10px; color: gray; font-size: 12px;'>GeralJá Brasil © {datetime.datetime.now().year}</div>", unsafe_allow_html=True)
