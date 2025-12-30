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

st.markdown("<br><hr><center>GeralJá v4.1 | 2025</center>", unsafe_allow_html=True)
