import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

st.set_page_config(page_title="Teste GeralJá", page_icon="⚡")

# --- TESTE DE CONEXÃO ---
db = None

if not firebase_admin._apps:
    try:
        # Tenta ler os segredos como um dicionário direto
        firebase_info = dict(st.secrets)
        cred = credentials.Certificate(firebase_info)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        st.success("✅ CONEXÃO ESTABELECIDA COM SUCESSO!")
    except Exception as e:
        st.error(f"❌ Falha na conexão: {e}")
        st.info("Se o erro for 'missing project_id', verifique se o JSON foi colado inteiro nos Secrets.")
else:
    db = firestore.client()
    st.success("✅ Firebase já estava ativo!")

# --- INTERFACE SIMPLES ---
st.title("GeralJá - Teste de Banco de Dados")

if db:
    nome_teste = st.text_input("Digite um nome para testar o banco:")
    if st.button("Gravar no Firebase"):
        try:
            # Tenta gravar um documento simples
            db.collection("testes").add({
                "nome": nome_teste,
                "data": "2025-12-26"
            })
            st.balloons()
            st.success(f"O nome '{nome_teste}' foi salvo no seu console do Firebase!")
        except Exception as e:
            st.error(f"Erro ao gravar: {e}")
