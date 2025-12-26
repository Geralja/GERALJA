import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
import datetime
import random

# --- 1. CONFIGURAÇÃO E CONEXÃO FIREBASE ---
st.set_page_config(page_title="GeralJá | Oficial", page_icon="⚡", layout="centered")

# Inicializa Firebase via Secrets (Cofre Seguro)
if not firebase_admin._apps:
    try:
        # Lê o JSON que você colou nos Secrets do Streamlit
        firebase_info = json.loads(st.secrets["FIREBASE_JSON"])
        cred = credentials.Certificate(firebase_info)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Erro ao conectar no Firebase: {e}")

db = firestore.client()

# --- 2. MOTOR DE ESTADO (SESSION STATE) ---
if 'etapa' not in st.session_state: st.session_state.etapa = 'busca'
if 'profissional_logado' not in st.session_state: st.session_state.profissional_logado = False

CHAVE_PIX = "09be938c-ee95-469f-b221-a3beea63964b"

# --- 3. CSS CUSTOMIZADO (DESIGN ELEGANTE) ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    .logo-box { text-align: center; padding-bottom: 20px; }
    .azul { color: #0047AB; font-size: 42px; font-weight: 900; }
    .laranja { color: #FF8C00; font-size: 42px; font-weight: 900; }
    
    /* Botões de Navegação Superior */
    div.stButton > button {
        background-color: #f0f2f6;
        color: #333;
        border-radius: 10px;
        border: none;
        width: 100%;
        font-weight: bold;
    }
    
    /* Botão de Ação Laranja */
    .btn-acao div.stButton > button {
        background-color: #FF8C00 !important;
        color: white !important;
        height: 50px;
        font-size: 18px;
    }
    
    .card-post {
        background: #f9f9f9; padding: 15px; border-radius: 12px;
        margin-bottom: 10px; border-left: 5px solid #0047AB;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    header, footer { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 4. MENU SUPERIOR FIXO ---
st.markdown('<div class="logo-box"><span class="azul">GERAL</span><span class="laranja">JÁ</span></div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1: 
    if st.button("🔍 Busca"): st.session_state.etapa = 'busca'; st.rerun()
with c2: 
    if st.button("👥 Social"): st.session_state.etapa = 'social'; st.rerun()
with c3: 
    if st.button("👷 Cadastro"): st.session_state.etapa = 'cadastro'; st.rerun()
with c4: 
    if st.button("📊 Admin"): st.session_state.etapa = 'admin'; st.rerun()

st.divider()

# --- 5. LÓGICA DAS TELAS ---

# TELA: CADASTRO DE PROFISSIONAL (SALVANDO NO FIREBASE)
# --- 1. FUNÇÃO DE APOIO (Coloque isso logo após os 'import') ---
def criar_link_zap(numero, mensagem):
    # Remove espaços e caracteres do número
    numero_limpo = "".join(filter(str.isdigit, numero))
    msg_url = mensagem.replace(" ", "%20")
    return f"https://wa.me/55{numero_limpo}?text={msg_url}"

# --- 2. NA TELA DE CADASTRO (Substitua a sua etapa de cadastro por esta) ---
if st.session_state.etapa == 'cadastro':
    st.markdown("### 👷 Cadastro de Profissional")
    
    # Criamos abas para o processo não ficar confuso
    passo = st.radio("Passo:", ["1. Dados Pessoais", "2. Verificação"], horizontal=True)

    if passo == "1. Dados Pessoais":
        nome_prof = st.text_input("Seu Nome Completo")
        especialidade = st.selectbox("Sua Área", ["Pintor", "Eletricista", "Encanador", "Diarista", "Mecânico"])
        zap_prof = st.text_input("Seu WhatsApp (com DDD)", placeholder="11912345678")
        
        if st.button("GERAR MEU CÓDIGO"):
            if nome_prof and zap_prof:
                # Gera o código e salva no Firebase
                cod_gerado = str(random.randint(1000, 9999))
                db.collection("verificacoes").document(zap_prof).set({
                    "nome": nome_prof,
                    "codigo": cod_gerado,
                    "status": "pendente",
                    "data": datetime.datetime.now()
                })
                
                # Prepara o link gratuito de WhatsApp
                texto_zap = f"Olá {nome_prof}, seu código de verificação para o GeralJá é: {cod_gerado}"
                link = criar_link_zap(zap_prof, texto_zap)
                
                st.info(f"Código **{cod_gerado}** gerado com sucesso!")
                st.markdown(f'''
                    <a href="{link}" target="_blank">
                        <button style="background-color: #25D366; color: white; border: none; padding: 10px 20px; border-radius: 10px; cursor: pointer; width: 100%;">
                            ENVIAR CÓDIGO VIA WHATSAPP (GRÁTIS)
                        </button>
                    </a>
                ''', unsafe_allow_html=True)
            else:
                st.warning("Preencha nome e WhatsApp!")

    elif passo == "2. Verificação":
        st.write("Insira o código que você recebeu:")
        zap_conferir = st.text_input("Confirme seu WhatsApp")
        input_cod = st.text_input("Código de 4 dígitos", max_chars=4)
        
        if st.button("VALIDAR MEU PERFIL"):
            # Busca no Firebase se o código bate
            doc_ref = db.collection("verificacoes").document(zap_conferir).get()
            if doc_ref.exists:
                dados = doc_ref.to_dict()
                if dados['codigo'] == input_cod:
                    # SALVA O PROFISSIONAL DEFINITIVO
                    db.collection("profissionais").document(zap_conferir).set({
                        "nome": dados['nome'],
                        "status": "Verificado ✔️",
                        "data_adesao": datetime.datetime.now()
                    })
                    st.success("🔥 PARABÉNS! Você agora é um profissional oficial do GeralJá!")
                    st.balloons()
                else:
                    st.error("Código incorreto!")
            else:
                st.error("WhatsApp não encontrado. Peça o código no Passo 1.")
    st.markdown("### 👷 Cadastro de Prestador")
    
    if not st.session_state.profissional_logado:
        nome = st.text_input("Nome Completo")
        profissao = st.selectbox("Sua Especialidade", ["Pintor", "Eletricista", "Encanador", "Diarista", "Mecânico"])
        zap = st.text_input("Seu WhatsApp (apenas números)")
        
        st.markdown('<div class="btn-acao">', unsafe_allow_html=True)
        if st.button("FINALIZAR CADASTRO NO FIREBASE"):
            if nome and zap:
                # SALVANDO NO BANCO DE DADOS REAL
                doc_ref = db.collection("profissionais").document(zap)
                doc_ref.set({
                    "nome": nome,
                    "profissao": profissao,
                    "contato": zap,
                    "status": "Verificado",
                    "data": str(datetime.datetime.now())
                })
                st.session_state.profissional_logado = True
                st.balloons()
                st.rerun()
            else:
                st.error("Por favor, preencha todos os campos.")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.success("✅ Seu perfil está ATIVO e salvo no banco de dados!")
        if st.button("Sair"): st.session_state.profissional_logado = False; st.rerun()

# TELA: BUSCA
elif st.session_state.etapa == 'busca':
    st.markdown("### 🔍 Qual serviço você precisa?")
    escolha = st.selectbox("Selecione", ["", "Pintor", "Eletricista", "Encanador", "Diarista"])
    if escolha:
        st.session_state.servico_busca = escolha
        st.session_state.etapa = 'resultado'; st.rerun()

# TELA: RESULTADO (BUSCANDO DO FIREBASE)
elif st.session_state.etapa == 'resultado':
    st.markdown(f"### Profissionais de {st.session_state.servico_busca}")
    
    # Exemplo de como listar do Firebase
    profs = db.collection("profissionais").where("profissao", "==", st.session_state.servico_busca).stream()
    
    encontrou = False
    for p in profs:
        encontrou = True
        dados = p.to_dict()
        with st.container():
            st.markdown(f"**{dados['nome']}** - {dados['status']} ⭐")
            if st.button(f"Contratar {dados['nome']}", key=dados['contato']):
                st.session_state.etapa = 'pagamento'; st.rerun()
            st.divider()
    
    if not encontrou:
        st.warning("Nenhum profissional cadastrado para esta categoria ainda.")

# TELA: REDE SOCIAL (SALVANDO POSTS NO FIREBASE)
elif st.session_state.etapa == 'social':
    st.markdown("### 👥 Mural do Grajaú")
    with st.form("mural"):
        msg = st.text_area("O que está acontecendo no bairro?")
        if st.form_submit_button("Postar"):
            if msg:
                db.collection("mural").add({"msg": msg, "data": datetime.datetime.now()})
                st.rerun()
    
    # Listar posts do Firebase
    posts = db.collection("mural").order_by("data", direction=firestore.Query.DESCENDING).limit(10).stream()
    for p in posts:
        st.markdown(f'<div class="card-post">{p.to_dict()["msg"]}</div>', unsafe_allow_html=True)

# TELA: PAGAMENTO (PIX REAL)
elif st.session_state.etapa == 'pagamento':
    st.markdown("### 💳 Pagamento Seguro")
    st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={CHAVE_PIX}")
    st.code(CHAVE_PIX)
    if st.button("CONFIRMAR PAGAMENTO"):
        db.collection("vendas").add({"valor": 25.0, "data": datetime.datetime.now()})
        st.balloons()
        st.session_state.etapa = 'busca'; st.rerun()

# TELA: ADMIN
elif st.session_state.etapa == 'admin':
    st.markdown("### 📊 Painel GeralJá")
    senha = st.text_input("Senha", type="password")
    if senha == "admin777":
        vendas = db.collection("vendas").stream()
        total = sum([v.to_dict()['valor'] for v in vendas])
        st.metric("Faturamento Acumulado", f"R$ {total:.2f}")

