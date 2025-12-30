import streamlit as st
import pandas as pd
from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from fuzzywuzzy import fuzz
from gtts import gTTS
import io
import json
import base64
import datetime

# ----------------------------------------------------------
# BLOCO PROTEGIDO: ENGENHARIA DE DADOS E IA
# ----------------------------------------------------------
class GeralJaEngine:
    def __init__(self):
        self.db = self._init_db()
        self._setup_nlp()
        self.CONFIG = {
            "PIX": "11991853488",
            "CUSTO_CLIQUE": 1,
            "BONUS": 5,
            "PROFISSOES": sorted([
                "Eletricista", "Encanador", "Pintor", "Pedreiro", "Diarista", 
                "Mecânico", "Manicure", "Cabeleireiro", "Montador de Móveis",
                "Jardineiro", "Técnico de TI", "Freteiro", "Ajudante Geral"
            ])
        }

    @st.cache_resource
    def _init_db(_self):
        if not firebase_admin._apps:
            try:
                b64_data = st.secrets["FIREBASE_BASE64"]
                info_chave = json.loads(base64.b64decode(b64_data).decode("utf-8"))
                cred = credentials.Certificate(info_chave)
                firebase_admin.initialize_app(cred)
            except Exception as e:
                st.error("Erro Crítico de Infraestrutura."); st.stop()
        return firestore.Client()

    @st.cache_resource
    def _setup_nlp(_self):
        try:
            for res in ['punkt', 'stopwords', 'wordnet', 'omw-1.4', 'punkt_tab']:
                nltk.download(res, quiet=True)
        except: pass

    def processar_ia(self, texto):
        if not texto: return None
        tokens = word_tokenize(texto.lower())
        stops = set(stopwords.words('portuguese'))
        limpos = [w for w in tokens if w not in stops and len(w) > 2]
        
        melhor_match, maior_score = "Ajudante Geral", 0
        busca_str = " ".join(limpos) if limpos else texto.lower()
        
        for prof in self.CONFIG["PROFISSOES"]:
            score = fuzz.token_set_ratio(busca_str, prof.lower())
            if score > 70 and score > maior_score:
                maior_score = score
                melhor_match = prof
        return melhor_match

    def gerar_voz(self, texto):
        try:
            tts = gTTS(text=texto, lang='pt')
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            return fp
        except: return None

# Inicialização
engine = GeralJaEngine()

# ----------------------------------------------------------
# DESIGN SYSTEM (UI)
# ----------------------------------------------------------
st.set_page_config(page_title="GeralJá | Oficial", page_icon="📍", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .card { background: white; padding: 20px; border-radius: 15px; border-left: 10px solid #0047AB; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 15px; }
    .premium-header { text-align: center; padding: 2rem; background: linear-gradient(90deg, #0047AB 0%, #FF8C00 100%); color: white; border-radius: 15px; margin-bottom: 20px; }
    .btn-wpp { background-color: #25D366; color: white !important; padding: 12px; border-radius: 10px; text-align: center; font-weight: bold; text-decoration: none; display: block; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="premium-header"><h1>GERALJÁ 📍</h1><p>Encontre Profissionais Qualificados Próximo a Você</p></div>', unsafe_allow_html=True)

tabs = st.tabs(["🔍 Busca Inteligente", "💼 Área do Profissional", "📝 Cadastro", "🛡️ Admin"])

# --- ABA BUSCA ---
with tabs[0]:
    pergunta = st.text_input("O que você precisa agora?", placeholder="Ex: chuveiro queimou...")
    if pergunta:
        categoria = engine.processar_ia(pergunta)
        st.success(f"🤖 Entendi! Você procura por: **{categoria}**")
        
        # Feedback por Voz
        audio_fp = engine.gerar_voz(f"Mostrando especialistas para {categoria}")
        if audio_fp: st.audio(audio_fp, format="audio/mp3")

        profs = engine.db.collection("profissionais").where("area", "==", categoria).where("aprovado", "==", True).stream()
        
        encontrou = False
        for doc in profs:
            encontrou = True
            d = doc.to_dict()
            with st.container():
                st.markdown(f"""
                <div class="card">
                    <h3>{d['nome']}</h3>
                    <p>📍 <b>Cidade:</b> {d.get('cidade', 'Não informada')} | ⭐ <b>Rating:</b> {d.get('rating', 5.0)}</p>
                    <p><i>"{d.get('descricao', 'Sem descrição disponível.')}"</i></p>
                </div>
                """, unsafe_allow_html=True)
                
                if d.get("saldo", 0) >= engine.CONFIG["CUSTO_CLIQUE"]:
                    if st.button(f"Falar com {d['nome'].split()[0]}", key=doc.id):
                        engine.db.collection("profissionais").document(doc.id).update({"saldo": firestore.Increment(-engine.CONFIG["CUSTO_CLIQUE"])})
                        st.markdown(f'<a href="https://wa.me/55{d["whatsapp"]}?text=Olá, vi seu perfil no GeralJá!" class="btn-wpp">ABRIR WHATSAPP</a>', unsafe_allow_html=True)
                else:
                    st.warning("Profissional temporariamente sem saldo para novos contatos.")
        
        if not encontrou:
            st.info(f"Ainda não temos {categoria} aprovados nesta região.")

# --- ABA CARTEIRA ---
with tabs[1]:
    st.subheader("💼 Painel do Profissional")
    c1, c2 = st.columns(2)
    z_log = c1.text_input("Seu WhatsApp (apenas números)")
    s_log = c2.text_input("Sua Senha", type="password")
    
    if z_log and s_log:
        user_doc = engine.db.collection("profissionais").document(z_log).get()
        if user_doc.exists and user_doc.to_dict().get('senha') == s_log:
            dados = user_doc.to_dict()
            st.success(f"Bem-vindo, {dados['nome']}!")
            col_m1, col_m2 = st.columns(2)
            col_m1.metric("Saldo GeralCoins", f"{dados.get('saldo', 0)} cr")
            col_m2.metric("Status", "Ativo" if dados.get('aprovado') else "Pendente")
            
            st.info(f"Para recarregar, faça um PIX para: **{engine.CONFIG['PIX']}**")
        else:
            st.error("Credenciais incorretas.")

# --- ABA CADASTRO ---
with tabs[2]:
    st.subheader("📝 Cadastre-se na Plataforma")
    with st.form("form_cadastro", clear_on_submit=True):
        f_nome = st.text_input("Nome Completo")
        f_zap = st.text_input("WhatsApp (ex: 11999998888)")
        f_pass = st.text_input("Crie uma Senha", type="password")
        f_area = st.selectbox("Sua Especialidade", engine.CONFIG["PROFISSOES"])
        f_cid = st.text_input("Sua Cidade")
        f_desc = st.text_area("Descrição dos seus serviços (O que você faz?)")
        
        if st.form_submit_button("FINALIZAR CADASTRO"):
            if f_nome and f_zap and f_pass:
                engine.db.collection("profissionais").document(f_zap).set({
                    "nome": f_nome, "whatsapp": f_zap, "senha": f_pass, 
                    "area": f_area, "cidade": f_cid, "descricao": f_desc,
                    "saldo": engine.CONFIG["BONUS"], "aprovado": False,
                    "rating": 5.0, "data": datetime.datetime.now()
                })
                st.balloons()
                st.success("Cadastro realizado com sucesso! Aguarde a aprovação do administrador.")
            else:
                st.warning("Preencha todos os campos obrigatórios.")

# --- ABA ADMIN ---
with tabs[3]:
    adm_pass = st.text_input("Senha de Administrador", type="password")
    if adm_pass == st.secrets.get("ADM_PASS", "mumias"):
        st.write("### 🛡️ Gestão de Aprovações")
        pendentes = engine.db.collection("profissionais").where("aprovado", "==", False).stream()
        
        for p in pendentes:
            data = p.to_dict()
            with st.expander(f"Solicitação: {data['nome']}"):
                st.write(f"**Área:** {data['area']} | **Cidade:** {data['cidade']}")
                st.write(f"**Descrição:** {data['descricao']}")
                if st.button(f"APROVAR AGORA", key=f"adm_{p.id}"):
                    engine.db.collection("profissionais").document(p.id).update({"aprovado": True})
                    st.rerun()

st.markdown("<br><hr><center>GeralJá v4.1 | 2025</center>", unsafe_allow_html=True)        return melhor_match

    def gerar_voz(self, texto):
        tts = gTTS(text=texto, lang='pt')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp

# Instância Protegida
engine = GeralJaEngine()

# ----------------------------------------------------------
# DESIGN SYSTEM
# ----------------------------------------------------------
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; }
    .card { background: white; padding: 20px; border-radius: 15px; border-left: 8px solid #0047AB; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 15px; }
    .btn-wpp { background-color: #25D366; color: white !important; padding: 10px; border-radius: 10px; text-align: center; font-weight: bold; text-decoration: none; display: block; }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# INTERFACE (UI)
# ----------------------------------------------------------
st.title("GERALJÁ | Inteligência Profissional 📍")

tabs = st.tabs(["🔍 BUSCAR", "💼 CARTEIRA", "📝 CADASTRAR", "🛡️ ADMIN"])

# --- ABA BUSCA ---
with tabs[0]:
    busca = st.text_input("O que você precisa hoje?", placeholder="Ex: Meu cano estourou")
    if busca:
        cat = engine.processar_ia(busca)
        st.subheader(f"🤖 IA: Especialista em {cat}")
        
        # Audio de Resposta (Opcional)
        audio = engine.gerar_voz(f"Buscando especialistas em {cat}")
        st.audio(audio, format="audio/mp3")

        profs = engine.db.collection("profissionais").where("area", "==", cat).where("aprovado", "==", True).stream()
        
        for doc in profs:
            d = doc.to_dict()
            with st.container():
                st.markdown(f'<div class="card"><h4>{d["nome"]}</h4><p>📍 {d.get("cidade", "São Paulo")}</p></div>', unsafe_allow_html=True)
                
                if d.get("saldo", 0) >= engine.CONFIG["CUSTO_CLIQUE"]:
                    if st.button(f"VER CONTATO DE {d['nome'].upper()}", key=doc.id):
                        # Transação Segura de Saldo
                        engine.db.collection("profissionais").document(doc.id).update({"saldo": firestore.Increment(-engine.CONFIG["CUSTO_CLIQUE"])})
                        st.markdown(f'<a href="https://wa.me/55{d["whatsapp"]}" class="btn-wpp">ABRIR WHATSAPP</a>', unsafe_allow_html=True)
                else:
                    st.warning("Profissional Offline (Sem Créditos)")

# --- ABA CARTEIRA ---
with tabs[1]:
    st.subheader("Minha Conta")
    zap_log = st.text_input("WhatsApp")
    pass_log = st.text_input("Senha", type="password")
    if zap_log and pass_log:
        u = engine.db.collection("profissionais").document(zap_log).get()
        if u.exists and u.to_dict()['senha'] == pass_log:
            dados = u.to_dict()
            st.metric("Saldo GeralCoins", f"{dados.get('saldo', 0)} Moedas")
            st.code(f"PIX RECARGA: {engine.CONFIG['PIX']}")
        else: st.error("Dados Inválidos")

# --- ABA CADASTRO ---
with tabs[2]:
    with st.form("cad"):
        f_n = st.text_input("Nome")
        f_z = st.text_input("WhatsApp")
        f_s = st.text_input("Senha", type="password")
        f_a = st.selectbox("Área", engine.CONFIG["PROFISSOES"])
        if st.form_submit_button("CADASTRAR"):
            engine.db.collection("profissionais").document(f_z).set({
                "nome": f_n, "whatsapp": f_z, "senha": f_s, "area": f_a,
                "saldo": engine.CONFIG["BONUS"], "aprovado": False, "data": datetime.datetime.now()
            })
            st.success("Cadastrado! Aguarde ativação.")

# --- ABA ADMIN ---
with tabs[3]:
    if st.text_input("Senha Master", type="password") == st.secrets.get("ADM_PASS", "mumias"):
        pendentes = engine.db.collection("profissionais").where("aprovado", "==", False).stream()
        for p in pendentes:
            if st.button(f"APROVAR {p.to_dict()['nome']}", key=f"adm_{p.id}"):
                engine.db.collection("profissionais").document(p.id).update({"aprovado": True})
                st.rerun()

st.markdown("<center>GeralJá v4.0 Protected Engine</center>", unsafe_allow_html=True)

# ----------------------------------------------------------
# 1. SETUP E IA CORE (NLP)
# ----------------------------------------------------------
st.set_page_config(page_title="GeralJá | Próximo de Você", page_icon="📍", layout="wide")

@st.cache_resource
def setup_ia():
    try:
        nltk.download('punkt')
        nltk.download('stopwords')
        nltk.download('wordnet')
        nltk.download('omw-1.4')
        nltk.download('punkt_tab')
    except Exception as e:
        st.error(f"Erro ao baixar recursos NLTK: {e}")

setup_ia()

# ----------------------------------------------------------
# 2. CONEXÃO FIREBASE (Sua lógica de Secret preservada)
# ----------------------------------------------------------
@st.cache_resource
def init_db():
    if not firebase_admin._apps:
        try:
            b64_data = st.secrets["FIREBASE_BASE64"]
            json_data = base64.b64decode(b64_data).decode("utf-8")
            info_chave = json.loads(json_data)
            cred = credentials.Certificate(info_chave)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Erro de Conexão Firebase: {e}")
            st.stop()
    return firestore.Client()

db = init_db()

# ----------------------------------------------------------
# 3. LÓGICA DE PROCESSAMENTO DE TEXTO (IA)
# ----------------------------------------------------------
def inteligência_busca(texto_usuario, lista_profissoes):
    """
    Usa Tokenização, Stopwords e Fuzzy Matching para encontrar o serviço.
    """
    if not texto_usuario: return None
    
    # Normalização
    stop_words = set(stopwords.words('portuguese'))
    tokens = word_tokenize(texto_usuario.lower())
    filtrados = [w for w in tokens if w not in stop_words and len(w) > 2]
    
    # 1. Busca Exata nos Tokens
    for token in filtrados:
        for prof in lista_profissoes:
            if token in prof.lower():
                return prof
                
    # 2. Busca Fuzzy (Aproximada) se não achar exato
    melhor_match = None
    maior_score = 0
    for prof in lista_profissoes:
        score = fuzz.partial_ratio(texto_usuario.lower(), prof.lower())
        if score > 80 and score > maior_score:
            maior_score = score
            melhor_match = prof
            
    return melhor_match if melhor_match else "Ajudante Geral"

# ----------------------------------------------------------
# 4. CONFIGURAÇÕES E DESIGN
# ----------------------------------------------------------
PIX_CHAVE = "11991853488"
ZAP_ADMIN = "5511991853488"
VALOR_CLIQUE = 1
BONUS_INICIAL = 5

PROFISSÕES = sorted([
    "Eletricista", "Encanador", "Pintor", "Pedreiro", "Diarista", 
    "Mecânico", "Manicure", "Cabeleireiro", "Montador de Móveis",
    "Jardineiro", "Técnico de TI", "Freteiro", "Ajudante Geral"
])

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; }
    .card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 15px; border-left: 8px solid #0047AB; }
    .premium-header { text-align: center; padding: 20px; background: linear-gradient(90deg, #0047AB 0%, #FF8C00 100%); color: white; border-radius: 15px; margin-bottom: 25px; }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# 5. INTERFACE (UI)
# ----------------------------------------------------------
st.markdown('<div class="premium-header"><h1>GERALJÁ 📍</h1><p>Inteligência Artificial em Serviços</p></div>', unsafe_allow_html=True)

aba_busca, aba_perfil, aba_cadastro, aba_adm = st.tabs(["🔍 Busca Inteligente", "💼 Área do Profissional", "📝 Cadastro", "🛡️ Painel Admin"])

# --- ABA BUSCA ---
with aba_busca:
    pergunta = st.text_input("O que você precisa agora?", placeholder="Ex: meu chuveiro queimou ou preciso de limpeza")
    
    if pergunta:
        categoria = inteligência_busca(pergunta, PROFISSÕES)
        st.success(f"🤖 Entendi! Você está procurando por: **{categoria}**")
        
        # Busca no Firestore
        profs = db.collection("profissionais").where("area", "==", categoria).where("aprovado", "==", True).stream()
        
        count = 0
        for doc in profs:
            count += 1
            d = doc.to_dict()
            with st.container():
                st.markdown(f"""
                <div class="card">
                    <h4>{d['nome']}</h4>
                    <p>📍 {d.get('cidade', 'São Paulo')} | ⭐ {d.get('rating', 5.0)}</p>
                    <small>{d.get('descricao', '')}</small>
                </div>
                """, unsafe_allow_html=True)
                
                if d.get("saldo", 0) >= VALOR_CLIQUE:
                    if st.button(f"Falar com {d['nome'].split()[0]}", key=doc.id):
                        db.collection("profissionais").document(doc.id).update({"saldo": firestore.Increment(-VALOR_CLIQUE)})
                        st.markdown(f'<a href="https://wa.me/55{d["whatsapp"]}?text=Olá, vi seu perfil no GeralJá!" target="_blank" style="text-decoration:none;"><div style="background:#25D366; color:white; padding:10px; text-align:center; border-radius:10px; font-weight:bold;">ABRIR WHATSAPP</div></a>', unsafe_allow_html=True)
                else:
                    st.warning("Este profissional está sem saldo no momento.")

# --- ABA CADASTRO ---
with aba_cadastro:
    st.subheader("Faça parte da nossa rede")
    with st.form("cad_novo"):
        n = st.text_input("Nome")
        z = st.text_input("WhatsApp (DDD + Número)")
        s = st.text_input("Senha", type="password")
        a = st.selectbox("Sua Especialidade", PROFISSÕES)
        c = st.text_input("Sua Cidade")
        desc = st.text_area("Breve descrição do seu serviço")
        
        enviado = st.form_submit_button("CADASTRAR")
        if enviado and n and z:
            db.collection("profissionais").document(z).set({
                "nome": n, "whatsapp": z, "senha": s, "area": a, "cidade": c,
                "descricao": desc, "saldo": BONUS_INICIAL, "aprovado": False,
                "rating": 5.0, "data": datetime.datetime.now()
            })
            st.balloons()
            st.success("Cadastro enviado! Aguarde aprovação do administrador.")

# --- ABA ADMIN ---
with aba_adm:
    senha_adm = st.text_input("Acesso Master", type="password")
    if senha_adm == "mumias":
        st.write("### Profissionais Aguardando Aprovação")
        pendentes = db.collection("profissionais").where("aprovado", "==", False).stream()
        for p in pendentes:
            data = p.to_dict()
            col1, col2 = st.columns([3, 1])
            col1.write(f"**{data['nome']}** ({data['area']})")
            if col2.button("APROVAR", key=f"ap_{p.id}"):
                db.collection("profissionais").document(p.id).update({"aprovado": True})
                st.rerun()

# --- RODAPÉ ---
st.markdown("<br><hr><center>GeralJá v3.5 | 2025</center>", unsafe_allow_html=True)

