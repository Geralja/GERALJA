import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import math
import re
import time
import pandas as pd
import unicodedata
import pytz
from datetime import datetime

# [1] CONFIGURAÇÃO INICIAL
st.set_page_config(page_title="GeralJá v3.0", layout="wide")

# Constantes globais que faltavam no seu código
CHAVE_ADMIN = "1234" # Altere para sua senha mestre
ZAP_ADMIN = "5511999999999"
LAT_REF = -23.5505
LON_REF = -46.6333
CATEGORIAS_OFICIAIS = ["Pintor", "Encanador", "Eletricista", "Mecânico", "Alimentação", "Pedreiro", "Limpeza", "Ar Condicionado", "Marido de Aluguel"]

# [2] FUNÇÃO DE CONVERSÃO DE IMAGEM (A QUE ESTAVA DANDO ERRO)
def converter_img_b64(arquivo):
    if arquivo is None: return ""
    try:
        return base64.b64encode(arquivo.read()).decode('utf-8')
    except:
        return ""

# [3] CONEXÃO FIREBASE (Descomente e configure no Streamlit Cloud)
if not firebase_admin._apps:
    try:
        if "FIREBASE_BASE64" in st.secrets:
            b64_key = st.secrets["FIREBASE_BASE64"]
            decoded_json = base64.b64decode(b64_key).decode("utf-8")
            cred_dict = json.loads(decoded_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        else:
            st.error("⚠️ Erro: Secret 'FIREBASE_BASE64' não encontrada.")
    except Exception as e:
        st.error(f"Erro Firebase: {e}")

db = firestore.client()

# [4] O MOTOR MESTRE
class MotorGeralJa:
    @staticmethod
    def normalizar(texto):
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn').lower().strip()

IA_MESTRE = MotorGeralJa()

# [5] INTERFACE DE ABAS
lista_abas = ["🔍 BUSCAR", "🚀 CADASTRAR", "👤 MEU PERFIL", "👑 ADMIN", "⭐ FEEDBACK"]
menu_abas = st.tabs(lista_abas)

# ==============================================================================
# --- ABA 1: BUSCA (Omitida para brevidade, mantenha sua lógica atual) ---
# ==============================================================================
with menu_abas[0]:
    st.title("Encontre Profissionais")

# ==============================================================================
# --- ABA 2: CADASTRO (BLINDADO CONTRA DUPLICADOS) ---
# ==============================================================================
with menu_abas[1]:
    st.markdown("### 🚀 Cadastro de Profissional Elite")
    st.info("🎁 BÔNUS: Novos cadastros ganham **10 GeralCones**!")

    with st.form("form_cadastro_v3", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome Completo")
            telefone = st.text_input("WhatsApp (Ex: 11999998888)")
            area = st.selectbox("Especialidade", CATEGORIAS_OFICIAIS)
        with col2:
            cidade = st.text_input("Cidade / UF")
            senha_cad = st.text_input("Crie uma Senha", type="password")
        
        desc = st.text_area("Descrição dos Serviços")
        
        st.write("📷 **Fotos do Portfólio**")
        f1 = st.file_uploader("Foto Principal (Obrigatória)", type=['jpg','png'], key="f1")
        f2 = st.file_uploader("Foto 2", type=['jpg','png'], key="f2")
        
        if st.form_submit_button("🚀 FINALIZAR CADASTRO"):
            tel_id = re.sub(r'\D', '', telefone)
            
            if not nome or len(tel_id) < 10 or not senha_cad or not f1:
                st.error("❌ Preencha todos os campos e envie a foto principal!")
            else:
                # TRAVA DE DUPLICADOS
                doc_existente = db.collection("profissionais").document(tel_id).get()
                if doc_existente.exists:
                    st.error(f"❌ O número {tel_id} já está cadastrado!")
                else:
                    dados = {
                        "nome": nome.upper(), "telefone": tel_id, "area": area,
                        "cidade": cidade, "senha": senha_cad, "descricao": desc,
                        "f1": converter_img_b64(f1), "f2": converter_img_b64(f2),
                        "saldo": 10.0, "aprovado": False, "verificado": False,
                        "cliques": 0, "lat": LAT_REF, "lon": LON_REF,
                        "data_cadastro": datetime.now().strftime("%d/%m/%Y")
                    }
                    db.collection("profissionais").document(tel_id).set(dados)
                    st.balloons()
                    st.success("✅ Cadastro realizado! Agora faça login na aba 'MEU PERFIL'.")

# ==============================================================================
# --- ABA 3: MEU PERFIL (LOGIN + EDIÇÃO COMPLETA) ---
# ==============================================================================
with menu_abas[2]:
    if 'auth' not in st.session_state: st.session_state.auth = False

    if not st.session_state.auth:
        st.subheader("🔐 Acesso ao Perfil")
        l_zap = st.text_input("WhatsApp", key="login_zap")
        l_pw = st.text_input("Senha", type="password", key="login_pw")
        if st.button("ENTRAR"):
            tel_clean = re.sub(r'\D', '', l_zap)
            user_doc = db.collection("profissionais").document(tel_clean).get()
            if user_doc.exists and str(user_doc.to_dict().get('senha')) == l_pw:
                st.session_state.auth = True
                st.session_state.user_id = tel_clean
                st.rerun()
            else:
                st.error("❌ Celular ou Senha incorretos.")
    else:
        uid = st.session_state.user_id
        dados = db.collection("profissionais").document(uid).get().to_dict()
        
        st.success(f"Bem-vindo, {dados.get('nome')}!")
        
        # FORMULÁRIO DE EDIÇÃO (TRAZENDO DE VOLTA)
        with st.expander("📝 EDITAR MEU PERFIL E FOTOS", expanded=True):
            with st.form("form_edicao"):
                ed_nome = st.text_input("Nome", value=dados.get('nome'))
                ed_desc = st.text_area("Descrição", value=dados.get('descricao'))
                ed_tel = st.text_input("Alterar WhatsApp (ID)", value=dados.get('telefone'))
                
                st.write("🖼️ **Trocar Fotos** (Deixe vazio para não alterar)")
                new_f1 = st.file_uploader("Nova Foto Principal", type=['jpg','png'])
                
                if st.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                    novo_tel = re.sub(r'\D', '', ed_tel)
                    up_dados = {"nome": ed_nome.upper(), "descricao": ed_desc, "telefone": novo_tel}
                    
                    if new_f1: up_dados["f1"] = converter_img_b64(new_f1)
                    
                    # Se mudou o telefone, move o documento
                    if novo_tel != uid:
                        db.collection("profissionais").document(novo_tel).set({**dados, **up_dados})
                        db.collection("profissionais").document(uid).delete()
                        st.session_state.user_id = novo_tel
                    else:
                        db.collection("profissionais").document(uid).update(up_dados)
                    
                    st.success("✅ Perfil Atualizado!")
                    time.sleep(1)
                    st.rerun()

        if st.button("SAIR"):
            st.session_state.auth = False
            st.rerun()

# [6] RODAPÉ
st.markdown("---")
st.caption("GeralJá v3.0 - © 2026")
