# ==============================================================================
# GERALJÁ SP - ULTIMATE v20.0 | UPLOAD DE FOTOS E CATEGORIAS MANUAIS
# ==============================================================================
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime
from PIL import Image
from io import BytesIO

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GeralJá | Pro", layout="centered")

# --- DATABASE ---
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

# --- LISTA DE PROFISSÕES OFICIAIS ---
CATEGORIAS_OFICIAIS = [
    "Ajudante Geral", "Bombeiro Civil", "Borracheiro", "Cabeleireiro", 
    "Diarista", "Eletricista", "Encanador", "Esteticista", "Fretes", 
    "Gesseiro", "Jardineiro", "Manicure", "Mecânico", "Montador de Móveis", 
    "Pedreiro", "Pintor", "Serralheiro", "Telhadista", "TI / Informática"
]

# --- FUNÇÃO PARA PROCESSAR IMAGEM ---
def converter_imagem_para_b64(arquivo):
    if arquivo:
        img = Image.open(arquivo)
        # Redimensionar para não pesar o banco de dados
        img.thumbnail((400, 400))
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=80)
        return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode()
    return None

# --- DESIGN ---
st.markdown("""
<style>
    .perfil-img { width: 150px; height: 150px; border-radius: 50%; object-fit: cover; border: 5px solid #FF8C00; margin-bottom: 20px; }
    .card-edit { background: white; padding: 30px; border-radius: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

TABS = st.tabs(["🔍 BUSCA", "👤 PERFIL PROFISSIONAL"])

# ------------------------------------------------------------------------------
# ABA PERFIL: ONDE TUDO ACONTECE (CADASTRO E EDIÇÃO)
# ------------------------------------------------------------------------------
with TABS[1]:
    if 'logado' not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:
        # TELA DE ACESSO/REGISTRO
        opcao = st.radio("Escolha:", ["Entrar na minha conta", "Criar novo cadastro"])
        
        if opcao == "Entrar na minha conta":
            zap = st.text_input("WhatsApp")
            senha = st.text_input("Senha", type="password")
            if st.button("ACESSAR"):
                doc = db.collection("profissionais").document(zap).get()
                if doc.exists and doc.to_dict().get('senha') == senha:
                    st.session_state.logado = True
                    st.session_state.user_id = zap
                    st.rerun()
                else: st.error("Erro no login.")

        else:
            # NOVO CADASTRO COMPLETO
            with st.form("novo_cadastro"):
                st.write("### 📝 Ficha de Cadastro")
                n_nome = st.text_input("Nome Profissional")
                n_zap = st.text_input("WhatsApp (Login)")
                n_senha = st.text_input("Senha Master", type="password")
                n_cat = st.selectbox("Sua Profissão Principal", CATEGORIAS_OFICIAIS)
                n_desc = st.text_area("Descreva seus diferenciais")
                n_foto = st.file_uploader("Carregar Foto de Perfil", type=['jpg', 'png', 'jpeg'])
                
                if st.form_submit_button("CADASTRAR E GANHAR 5 MOEDAS"):
                    foto_b64 = converter_imagem_para_b64(n_foto)
                    db.collection("profissionais").document(n_zap).set({
                        "nome": n_nome, "senha": n_senha, "area": n_cat,
                        "whatsapp": n_zap, "descricao": n_desc, "foto_url": foto_b64,
                        "saldo": 5, "aprovado": False, "rating": 5.0
                    })
                    st.success("Cadastro realizado! Aguarde a aprovação do Admin.")

    else:
        # ÁREA DE EDIÇÃO DO PROFISSIONAL LOGADO
        uid = st.session_state.user_id
        dados = db.collection("profissionais").document(uid).get().to_dict()

        st.markdown(f"### Bem-vindo, {dados['nome']}")
        
        # Mostrar foto atual
        if dados.get('foto_url'):
            st.markdown(f'<center><img src="{dados["foto_url"]}" class="perfil-img"></center>', unsafe_allow_html=True)
        else:
            st.info("Você ainda não tem foto de perfil.")

        with st.expander("⚙️ EDITAR MEUS DADOS E FOTO"):
            with st.form("form_edicao"):
                ed_nome = st.text_input("Nome", value=dados['nome'])
                ed_cat = st.selectbox("Mudar Profissão", CATEGORIAS_OFICIAIS, index=CATEGORIAS_OFICIAIS.index(dados['area']))
                ed_desc = st.text_area("Minha Bio", value=dados.get('descricao', ''))
                ed_foto = st.file_uploader("Trocar Foto de Perfil", type=['jpg', 'png'])
                
                if st.form_submit_button("SALVAR ALTERAÇÕES"):
                    update_data = {
                        "nome": ed_nome,
                        "area": ed_cat,
                        "descricao": ed_desc
                    }
                    if ed_foto:
                        update_data["foto_url"] = converter_imagem_para_b64(ed_foto)
                    
                    db.collection("profissionais").document(uid).update(update_data)
                    st.success("Perfil Atualizado com Sucesso!")
                    time.sleep(1)
                    st.rerun()

        if st.button("SAIR (LOGOUT)"):
            st.session_state.logado = False
            st.rerun()

# ABA DE BUSCA (Apenas para visualizar como fica)
with TABS[0]:
    st.write("### Profissionais em SP")
    # ... código de busca aqui ...
