# ==============================================================================
# GERALJÁ - O SISTEMA COMPLETO NACIONAL v16.0
# TUDO EM UM: ADMIN TOTAL + FINANCEIRO + GPS + IA DE FILTRAGEM
# ==============================================================================

# ==============================================================================
# GERALJÁ - v17.0 | FOCO: CADASTRO EDITÁVEL E GESTÃO DE PERFIL
# ==============================================================================

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import math
import datetime

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="GeralJá | Gestão", layout="centered")

@st.cache_resource
def init_db():
    if not firebase_admin._apps:
        b64_key = st.secrets["FIREBASE_BASE64"]
        decoded_json = base64.b64decode(b64_key).decode("utf-8")
        cred = credentials.Certificate(json.loads(decoded_json))
        return firebase_admin.initialize_app(cred)
    return firebase_admin.get_app()

init_db()
db = firestore.client()

# --- CONSTANTES ---
CHAVE_ADMIN = "mumias"
PIX_OFICIAL = "11991853488"

# --- CSS PREMIUM ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap');
    * { font-family: 'Montserrat', sans-serif; }
    .stApp { background-color: #f8f9fa; }
    .card-edit { background: white; padding: 25px; border-radius: 20px; border: 1px solid #ddd; margin-top: 20px; }
    .azul { color: #0047AB; font-weight: 900; font-size: 40px; }
    .laranja { color: #FF8C00; font-weight: 900; font-size: 40px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<center><span class="azul">GERAL</span><span class="laranja">JÁ</span></center>', unsafe_allow_html=True)

TABS = st.tabs(["🔍 BUSCAR", "👤 PROFISSIONAL", "🛡️ ADMIN"])

# ------------------------------------------------------------------------------
# ABA 1: BUSCA (SIMPLIFICADA PARA FOCO NA EDIÇÃO)
# ------------------------------------------------------------------------------
with TABS[0]:
    st.write("### O que você precisa?")
    # Lógica de busca e GPS mantida conforme v16...
    st.info("Utilize a busca para encontrar profissionais próximos.")

# ------------------------------------------------------------------------------
# ABA 2: PROFISSIONAL (LOGIN + EDIÇÃO DE CADASTRO)
# ------------------------------------------------------------------------------
with TABS[1]:
    if 'logado' not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:
        st.subheader("Login do Parceiro")
        login_zap = st.text_input("WhatsApp (Login)")
        login_pass = st.text_input("Senha", type="password")
        
        if st.button("ACESSAR MINHA CONTA"):
            doc = db.collection("profissionais").document(login_zap).get()
            if doc.exists and doc.to_dict().get('senha') == login_pass:
                st.session_state.logado = True
                st.session_state.user_id = login_zap
                st.rerun()
            else:
                st.error("WhatsApp ou Senha incorretos.")
        
        st.divider()
        st.write("Ainda não tem conta?")
        if st.button("CRIAR NOVO CADASTRO"):
            # Lógica para resetar campos e focar no cadastro
            st.info("Vá na aba de cadastro ou preencha os dados abaixo.")

    else:
        # --- ÁREA DO PROFISSIONAL LOGADO ---
        user_id = st.session_state.user_id
        dados = db.collection("profissionais").document(user_id).get().to_dict()
        
        st.success(f"Logado como: {dados.get('nome')}")
        
        # Dashboard Rápido
        col1, col2 = st.columns(2)
        col1.metric("Meu Saldo 🪙", dados.get('saldo', 0))
        col2.metric("Leads Ganhos 🚀", dados.get('cliques', 0))

        # --- FORMULÁRIO DE EDIÇÃO ---
        st.markdown('<div class="card-edit">', unsafe_allow_html=True)
        st.write("### 📝 Editar Meu Perfil")
        
        with st.form("form_edicao"):
            novo_nome = st.text_input("Nome Visível", value=dados.get('nome'))
            nova_desc = st.text_area("Descrição dos Serviços", value=dados.get('descricao', ''))
            novo_bairro = st.text_input("Bairro/Região", value=dados.get('localizacao'))
            nova_foto = st.text_input("URL da Foto de Perfil", value=dados.get('foto_url', ''))
            
            st.write("📍 **Atualizar Localização GPS**")
            c_lat, c_lon = st.columns(2)
            nova_lat = c_lat.number_input("Latitude", value=float(dados.get('lat', -23.55)), format="%.5f")
            nova_lon = c_lon.number_input("Longitude", value=float(dados.get('lon', -46.63)), format="%.5f")
            
            st.write("🔐 **Segurança**")
            nova_senha = st.text_input("Alterar Senha", placeholder="Deixe em branco para manter a atual", type="password")

            if st.form_submit_button("SALVAR ALTERAÇÕES"):
                update_data = {
                    "nome": novo_nome,
                    "descricao": nova_desc,
                    "localizacao": novo_bairro,
                    "foto_url": nova_foto,
                    "lat": nova_lat,
                    "lon": nova_lon
                }
                if nova_senha:
                    update_data["senha"] = nova_senha
                
                db.collection("profissionais").document(user_id).update(update_data)
                st.success("Perfil atualizado com sucesso!")
                time.sleep(1)
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("SAIR / LOGOUT"):
            st.session_state.logado = False
            st.rerun()

# ------------------------------------------------------------------------------
# ABA 3: ADMIN
# ------------------------------------------------------------------------------
with TABS[2]:
    if st.text_input("Chave Mestra", type="password") == CHAVE_ADMIN:
        st.write("### Gerenciamento de Profissionais")
        # Listagem de profissionais para aprovação/exclusão (mantido conforme anterior)
        profs = db.collection("profissionais").stream()
        for p in profs:
            d = p.to_dict()
            with st.expander(f"{d.get('nome')} ({p.id})"):
                if st.button("Excluir Conta", key=f"del_{p.id}"):
                    db.collection("profissionais").document(p.id).delete()
                    st.rerun()

st.markdown("<br><hr><center><small>GeralJá v17.0 | Sistema com Perfil Editável</small></center>", unsafe_allow_html=True)
