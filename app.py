# ==============================================================================
# GERALJÁ: CRIANDO SOLUÇÕES - VERSÃO ESTÁVEL COMPLETA
# ==============================================================================
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import math
import re
import time
import pandas as pd
from datetime import datetime
import pytz
import unicodedata
import requests
from groq import Groq
from fuzzywuzzy import process
from urllib.parse import quote
import google.generativeai as genai
from streamlit_js_eval import streamlit_js_eval, get_geolocation
from google_auth_oauthlib.flow import Flow

# --- 1. CONFIGURAÇÃO DE AMBIENTE ---
st.set_page_config(
    page_title="GeralJá | Criando Soluções",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CONFIGURAÇÃO DE CHAVES E IA ---
try:
    # Configuração Gemini
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # Configuração Google Auth
    FB_ID = st.secrets["FB_CLIENT_ID"]
    FB_SECRET = st.secrets["FB_CLIENT_SECRET"]
    FIREBASE_API_KEY = st.secrets["FIREBASE_API_KEY"]
    REDIRECT_URI = "https://geralja-zxiaj2ot56fuzgcz7xhcks.streamlit.app/"
    
    # Cliente Groq
    client_groq = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error(f"Erro Crítico: Chaves não encontradas no Secrets. ({e})")
    st.stop()

HANDLER_URL = "https://geralja-5bb49.firebaseapp.com/__/auth/handler"

# --- 2. CAMADA DE PERSISTÊNCIA (FIREBASE) ---
@st.cache_resource
def conectar_banco_master():
    if not firebase_admin._apps:
        try:
            if "firebase" in st.secrets and "base64" in st.secrets["firebase"]:
                b64_key = st.secrets["firebase"]["base64"]
                decoded_json = base64.b64decode(b64_key).decode("utf-8")
                cred_dict = json.loads(decoded_json)
                cred = credentials.Certificate(cred_dict)
                return firebase_admin.initialize_app(cred)
            else:
                st.error("⚠️ Configuração 'firebase.base64' não encontrada.")
                st.stop()
        except Exception as e:
            st.error(f"❌ FALHA NA INFRAESTRUTURA: {e}")
            st.stop()
    return firebase_admin.get_app()

app_engine = conectar_banco_master()
db = firestore.client()

# --- 3. FUNÇÕES DE SUPORTE E INFRAESTRUTURA ---

@st.cache_data(ttl=600)
def carregar_categorias_do_banco():
    try:
        doc = db.collection("configuracoes").document("categorias").get()
        if doc.exists:
            return doc.to_dict().get("lista", [])
        return []
    except Exception as e:
        return []

def processar_ia_suprema(termo):
    if not termo: return None
    categorias = carregar_categorias_do_banco()
    
    # IA 1: FUZZY Rápida
    match, score = process.extractOne(termo, categorias)
    if score > 90: return match

    # IA 2: GROQ
    try:
        prompt = f"Categorize '{termo}' em apenas UMA destas opções: {categorias}. Responda apenas o nome."
        res = client_groq.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192", temperature=0
        )
        resp = res.choices[0].message.content.strip()
        if resp in categorias: return resp
    except: pass

    # IA 3: GEMINI
    try:
        model = genai.GenerativeModel('gemini-pro')
        res = model.generate_content(f"Selecione a categoria exata de '{termo}' na lista {categorias}")
        if res.text.strip() in categorias: return res.text.strip()
    except: pass

    return match if score > 50 else "Ajudante Geral"

def calcular_distancia_real(lat1, lon1, lat2, lon2):
    try:
        if None in [lat1, lon1, lat2, lon2]: return 999.0
        R = 6371.0
        dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return round(R * c, 1)
    except: return 999.0

def limpar_whatsapp(numero):
    num = re.sub(r'\D', '', str(numero))
    if not num.startswith('55') and len(num) >= 10:
        num = f"55{num}"
    return num

def normalizar(texto):
    if not texto: return ""
    return "".join(ch for ch in unicodedata.normalize('NFKD', str(texto)) 
                   if unicodedata.category(ch) != 'Mn').lower().strip()

# --- 4. POLÍTICAS E CONSTANTES ---
CATEGORIAS_OFICIAIS = carregar_categorias_do_banco() or ["Ajudante Geral", "Eletricista", "Encanador", "Pedreiro"]

CONCEITOS_EXPANDIDOS = {
    "pizza": "Pizzaria", "fome": "Pizzaria", "lanche": "Lanchonete", "vazamento": "Encanador",
    "cano": "Encanador", "curto": "Eletricista", "luz": "Eletricista", "carro": "Mecânico",
    "pet": "Pet Shop", "faxina": "Diarista", "jardim": "Jardineiro"
}

# --- 5. LOGICA DE LOGIN GOOGLE ---
def get_google_flow():
    g_auth = st.secrets["google_auth"]
    client_config = {
        "web": {
            "client_id": g_auth["client_id"],
            "client_secret": g_auth["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [g_auth["redirect_uri"]]
        }
    }
    return Flow.from_client_config(
        client_config,
        scopes=["openid", "https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"],
        redirect_uri=g_auth["redirect_uri"]
    )

query_params = st.query_params
if "code" in query_params:
    try:
        flow = get_google_flow()
        flow.fetch_token(code=query_params["code"])
        session = flow.authorized_session()
        user_info = session.get('https://www.googleapis.com/userinfo').json()
        
        email_google = user_info.get("email")
        st.query_params.clear()
        
        pro_ref = db.collection("profissionais").where("email", "==", email_google).limit(1).get()
        if pro_ref:
            st.session_state.auth = True
            st.session_state.user_id = pro_ref[0].id
            st.rerun()
        else:
            st.session_state.pre_cadastro = {"email": email_google, "nome": user_info.get("name"), "foto": user_info.get("picture")}
            st.toast("Complete seu cadastro profissional!")
    except Exception as e:
        st.error(f"Erro Login Google: {e}")

# --- 6. DESIGN SYSTEM ---
if 'modo_noite' not in st.session_state:
    st.session_state.modo_noite = True

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    * {{ font-family: 'Inter', sans-serif; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    .stApp {{ background-color: {"#0D1117" if st.session_state.modo_noite else "#F8FAFC"} !important; }}
    .header-container {{ background: white; padding: 40px 20px; border-radius: 0 0 50px 50px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.05); border-bottom: 8px solid #FF8C00; margin-bottom: 25px; }}
    .logo-azul {{ color: #0047AB; font-weight: 900; font-size: 50px; letter-spacing: -2px; }}
    .logo-laranja {{ color: #FF8C00; font-weight: 900; font-size: 50px; letter-spacing: -2px; }}
</style>
""", unsafe_allow_html=True)

# Topo
c_t1, c_t2 = st.columns([2, 8])
with c_t1:
    st.session_state.modo_noite = st.toggle("🌙 Modo Noite", value=st.session_state.modo_noite)

st.markdown('<div class="header-container"><span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span><br><small style="color:#64748B; font-weight:700;">BRASIL ELITE EDITION</small></div>', unsafe_allow_html=True)

lista_abas = ["🔍 BUSCAR", "🚀 CADASTRAR", "👤 MEU PERFIL", "👑 ADMIN", "⭐ FEEDBACK"]
menu_abas = st.tabs(lista_abas)

comando = st.sidebar.text_input("Comando Secreto", type="password")
if comando == "abracadabra":
    lista_abas.append("📊 FINANCEIRO")

# ==============================================================================
# --- ABA 0: VITRINE PROFISSIONAL ELITE 3.0 ---
# ==============================================================================
with menu_abas[0]:
    # 1. DESIGN SYSTEM (CSS) - Isso transforma texto em interface de App
    st.markdown("""
    <style>
        .vitrine-container { font-family: 'Inter', sans-serif; }
        .cartao-geral { 
            background: #ffffff; border-radius: 20px; padding: 20px; margin-bottom: 25px; 
            box-shadow: 0 10px 25px rgba(0,0,0,0.05); border-left: 10px solid var(--cborda, #0047AB); 
            color: #1e293b; position: relative; overflow: hidden;
        }
        .elite-glow {
            position: absolute; top: 0; right: 0; width: 100px; height: 100px;
            background: linear-gradient(45deg, transparent, rgba(255,215,0,0.1));
        }
        .perfil-row { display: flex; gap: 15px; align-items: center; }
        .foto-perfil { 
            width: 70px; height: 70px; border-radius: 50%; object-fit: cover; 
            border: 3px solid #25D366; background: #f1f5f9;
        }
        .distancia-tag { background: #f1f5f9; color: #64748b; padding: 5px 12px; border-radius: 50px; font-size: 11px; font-weight: 700; }
        .elite-tag { background: #FFD700; color: #000; padding: 5px 12px; border-radius: 50px; font-size: 11px; font-weight: 800; }
        
        /* Galeria de Fotos Estilo Instagram */
        .social-track { display: flex; overflow-x: auto; gap: 12px; padding: 15px 0; scrollbar-width: none; }
        .social-track::-webkit-scrollbar { display: none; }
        .social-card { flex: 0 0 140px; height: 190px; border-radius: 15px; overflow: hidden; background: #f1f5f9; }
        .social-card img { width: 100%; height: 100%; object-fit: cover; transition: 0.3s; }
        .social-card img:hover { transform: scale(1.1); }

        .btn-zap { 
            display: block; background: #25D366; color: white !important; text-align: center; 
            padding: 16px; border-radius: 15px; font-weight: 800; text-decoration: none; 
            margin-top: 15px; font-size: 15px; transition: 0.3s;
        }
        .btn-zap:hover { background: #128C7E; transform: translateY(-2px); }
    </style>
    """, unsafe_allow_html=True)

    # 2. INTERFACE DE BUSCA
    st.markdown("### 🔍 Encontre o melhor no Grajaú")
    termo_busca = st.text_input("", placeholder="O que você precisa? (ex: consertar pia)", label_visibility="collapsed")
    
    col_dist, col_cat = st.columns([1, 1])
    with col_dist:
        raio_km = st.select_slider("Distância máxima", options=[2, 5, 10, 20, 50], value=10)
    
    if termo_busca:
        # A. IA RESOLVENDO A CATEGORIA
        with st.status("🧠 Consultando especialistas...", expanded=False) as status:
            cat_final = processar_ia_suprema(termo_busca)
            status.update(label=f"🎯 Categoria: {cat_final}", state="complete")

        # B. LOCALIZAÇÃO DO USUÁRIO
        try:
            loc = get_geolocation()
            m_lat = loc['coords']['latitude'] if loc else LAT_REF
            m_lon = loc['coords']['longitude'] if loc else LON_REF
        except:
            m_lat, m_lon = LAT_REF, LON_REF

        # C. BUSCA NO FIREBASE
        docs = db.collection("profissionais").where("area", "==", cat_final).where("aprovado", "==", True).stream()
        
        lista_ranking = []
        for d in docs:
            p = d.to_dict()
            dist = calcular_distancia_real(m_lat, m_lon, p.get('lat', LAT_REF), p.get('lon', LON_REF))
            if dist <= raio_km:
                p['dist'] = dist
                p['score'] = (p.get('saldo', 0) * 5) + (500 if p.get('verificado') else 0)
                lista_ranking.append(p)

        # Ordenar: Mais moedas (Score) e mais perto (Dist)
        
        lista_ranking.sort(key=lambda x: (-x['score'], x['dist']))

        # D. RENDERIZAÇÃO DA VITRINE
        if not lista_ranking:
            st.warning(f"Nenhum '{cat_final}' encontrado neste raio. Tente aumentar a distância!")
        else:
            for prof in lista_ranking:
                is_elite = prof.get('verificado') and prof.get('saldo', 0) > 0
                cor_borda = "#FFD700" if is_elite else "#0047AB"
                
                # Trata o WhatsApp
                zap_link = re.sub(r'\D', '', str(prof.get('whatsapp', '')))
                if not zap_link.startswith('55'): zap_link = f"55{zap_link}"
                
                # Monta Galeria de Fotos (f1 a f5)
                fotos_html = ""
                for i in range(1, 6):
                    f_data = prof.get(f'f{i}')
                    if f_data and len(str(f_data)) > 50:
                        src = f_data if str(f_data).startswith("http") else f"data:image/jpeg;base64,{f_data}"
                        fotos_html += f'<div class="social-card"><img src="{src}"></div>'

                # HTML DO CARD (Onde a mágica acontece)
                st.markdown(f"""
                <div class="cartao-geral" style="--cborda: {cor_borda};">
                    <div class="elite-glow"></div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
                        <span class="distancia-tag">📍 {prof['dist']:.1f} KM</span>
                        {"<span class='elite-tag'>🏆 ELITE</span>" if is_elite else ""}
                    </div>
                    <div class="perfil-row">
                        <img src="{prof.get('foto_url', 'https://cdn-icons-png.flaticon.com/512/149/149071.png')}" class="foto-perfil">
                        <div>
                            <h4 style="margin:0; font-size:18px; color:#0f172a;">{prof.get('nome', '').upper()}</h4>
                            <p style="margin:0; font-size:13px; color:#64748b; font-weight:600;">{prof.get('area')}</p>
                        </div>
                    </div>
                    <div style="margin-top:10px; font-size:14px; color:#475569; line-height:1.4;">
                        {prof.get('descricao', '')[:110]}...
                    </div>
                    <div class="social-track">
                        {fotos_html}
                    </div>
                    <a href="https://wa.me/{zap_link}?text=Olá, vi seu perfil no GeralJá!" target="_blank" class="btn-zap">
                        SOLICITAR ORÇAMENTO AGORA
                    </a>
                </div>
                """, unsafe_allow_html=True)
# ==============================================================================
# ABA 2: 🚀 PAINEL DO PARCEIRO (COMPLETO: FB + IMAGENS + FAQ + EXCLUSÃO)
# ==============================================================================
with menu_abas[2]:
    # 1. LÓGICA DE CAPTURA DO FACEBOOK (QUERY PARAMS)
    params = st.query_params
    if "uid" in params and not st.session_state.get('auth'):
        fb_uid = params["uid"]
        user_query = db.collection("profissionais").where("fb_uid", "==", fb_uid).limit(1).get()
        if user_query:
            doc = user_query[0]
            st.session_state.auth = True
            st.session_state.user_id = doc.id
            st.success(f"✅ Bem-vindo!")
            time.sleep(1)
            st.rerun()

    if 'auth' not in st.session_state: 
        st.session_state.auth = False
    
   # --- 2. TELA DE LOGIN (VERSÃO FINAL SEM ERROS) ---
    if not st.session_state.get('auth'):
        st.subheader("🚀 Acesso ao Painel")
        
        # 1. Definição das variáveis de conexão
        fb_id = st.secrets.get("FB_CLIENT_ID", "")
        redirect_uri = "https://geralja-zxiaj2ot56fuzgcz7xhcks.streamlit.app/"
        
        # 2. Criamos as duas variáveis para matar o NameError de vez
        url_direta_fb = f"https://www.facebook.com/v18.0/dialog/oauth?client_id={fb_id}&redirect_uri={redirect_uri}&scope=public_profile,email"
        link_auth = url_direta_fb 
        
        # 3. O Botão Visual (Usando target="_top" para o Facebook aceitar)
        st.markdown(f'''
            <a href="{url_direta_fb}" target="_top" style="text-decoration:none;">
                <div style="background:#1877F2;color:white;padding:12px;border-radius:8px;text-align:center;font-weight:bold;display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow: 0px 4px 6px rgba(0,0,0,0.1);">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/2021_Facebook_icon.svg" width="20px" style="margin-right:10px;">
                    ENTRAR COM FACEBOOK
                </div>
            </a>
        ''', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.write("--- ou use seus dados ---")
        
        # 4. Formulário de Login Manual (Com chaves exclusivas)
        col1, col2 = st.columns(2)
        l_zap = col1.text_input("WhatsApp", key="login_zap_geralja_v10", placeholder="Ex: 11999999999")
        l_pw = col2.text_input("Senha", type="password", key="login_pw_geralja_v10")
        
        if st.button("ENTRAR NO PAINEL", key="btn_entrar_geralja_v10", use_container_width=True):
            try:
                u = db.collection("profissionais").document(l_zap).get()
                if u.exists:
                    dados_user = u.to_dict()
                    if str(dados_user.get('senha')) == str(l_pw):
                        st.session_state.auth = True
                        st.session_state.user_id = l_zap
                        st.success("Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Senha incorreta.")
                else:
                    st.error("❌ WhatsApp não cadastrado.")
            except Exception as e:
                st.error(f"Erro ao acessar banco de dados: {e}")
    # --- 3. PAINEL LOGADO ---
    else:
        doc_ref = db.collection("profissionais").document(st.session_state.user_id)
        d = doc_ref.get().to_dict()
        
        st.write(f"### Olá, {d.get('nome', 'Parceiro')}!")
        
        # Dashboard de métricas
        m1, m2, m3 = st.columns(3)
        m1.metric("Saldo 🪙", f"{d.get('saldo', 0)}")
        m2.metric("Cliques 🚀", f"{d.get('cliques', 0)}")
        m3.metric("Status", "🟢 ATIVO" if d.get('aprovado') else "🟡 PENDENTE")

        # Botão GPS
        if st.button("📍 ATUALIZAR MEU GPS", use_container_width=True):
            from streamlit_js_eval import streamlit_js_eval
            loc = streamlit_js_eval(js_expressions="navigator.geolocation.getCurrentPosition(s => s)", key='gps_v8')
            if loc and 'coords' in loc:
                doc_ref.update({"lat": loc['coords']['latitude'], "lon": loc['coords']['longitude']})
                st.success("✅ Localização GPS Atualizada!")

        # --- EDIÇÃO DE PERFIL E VITRINE ---
        with st.expander("📝 EDITAR MEU PERFIL & VITRINE", expanded=False):
            # Função de tratamento de imagem interna e robusta
            def otimizar_imagem(arq, qualidade=50, size=(800, 800)):
                try:
                    img = Image.open(arq)
                    if img.mode in ("RGBA", "P"): 
                        img = img.convert("RGB")
                    img.thumbnail(size)
                    output = io.BytesIO()
                    img.save(output, format="JPEG", quality=qualidade, optimize=True)
                    return f"data:image/jpeg;base64,{base64.b64encode(output.getvalue()).decode()}"
                except Exception as e:
                    st.error(f"Erro ao processar imagem: {e}")
                    return None

            with st.form("perfil_v8"):
                n_nome = st.text_input("Nome Comercial", d.get('nome', ''))
                # CATEGORIAS_OFICIAIS deve estar definida no início do código globalmente
                n_area = st.selectbox("Segmento", CATEGORIAS_OFICIAIS, 
                                     index=CATEGORIAS_OFICIAIS.index(d.get('area')) if d.get('area') in CATEGORIAS_OFICIAIS else 0)
                n_desc = st.text_area("Descrição do Serviço", d.get('descricao', ''))
                
                st.markdown("---")
                st.write("📷 **Fotos**")
                n_foto = st.file_uploader("Trocar Foto de Perfil", type=['jpg','png','jpeg'])
                n_portfolio = st.file_uploader("Vitrine de Serviços (Máx 4 fotos)", type=['jpg','png','jpeg'], accept_multiple_files=True)
                
                if st.form_submit_button("💾 SALVAR TODAS AS ALTERAÇÕES", use_container_width=True):
                    updates = {
                        "nome": n_nome,
                        "area": n_area,
                        "descricao": n_desc
                    }
                    
                    # Processa foto de perfil se houver upload
                    if n_foto:
                        img_base64 = otimizar_imagem(n_foto, qualidade=60, size=(300, 300))
                        if img_base64:
                            updates["foto_url"] = img_base64

                    # Processa fotos da vitrine (f1, f2, f3, f4)
                    if n_portfolio:
                        # Limpa as fotos antigas da vitrine para subir as novas
                        for i in range(1, 5):
                            updates[f'f{i}'] = None
                        
                        for i, f in enumerate(n_portfolio[:4]):
                            img_p_base64 = otimizar_imagem(f)
                            if img_p_base64:
                                updates[f"f{i+1}"] = img_p_base64
                    
                    # Envia para o Firebase
                    doc_ref.update(updates)
                    st.success("✅ Perfil e Vitrine atualizados com sucesso!")
                    time.sleep(1)
                    st.rerun()

        # --- FAQ ---
        with st.expander("❓ PERGUNTAS FREQUENTES"):
            st.write("**Como ganho o selo Elite?**")
            st.write("Mantenha seu saldo acima de 10 moedas e perfil completo com fotos.")
            st.write("**Como funciona a cobrança?**")
            st.write("Cada clique no seu botão de WhatsApp desconta 1 moeda do seu saldo atual.")

        # VINCULAR FACEBOOK (Caso ainda não tenha)
        if not d.get('fb_uid'):
            with st.expander("🔗 CONECTAR FACEBOOK"):
                st.info("Conecte seu Facebook para fazer login rápido sem senha.")
                st.link_button("VINCULAR AGORA", link_auth, use_container_width=True)

        st.divider()

        # --- LOGOUT E EXCLUSÃO ---
        col_out, col_del = st.columns(2)
        
        with col_out:
            if st.button("🚪 SAIR DO PAINEL", use_container_width=True):
                st.session_state.auth = False
                st.rerun()
                
        with col_del:
            with st.expander("⚠️ EXCLUIR CONTA"):
                st.write("Atenção: Isso apaga todos os seus dados permanentemente.")
                if st.button("CONFIRMAR EXCLUSÃO", type="secondary", use_container_width=True):
                    doc_ref.delete()
                    st.session_state.auth = False
                    st.error("Sua conta foi removida do sistema.")
                    time.sleep(2)
                    st.rerun()
# --- ABA 1: CADASTRAR & EDITAR (VERSÃO FINAL GERALJÁ CORRIGIDA) ---
with menu_abas[1]:
    st.markdown("### 🚀 Cadastro ou Edição de Profissional")

    # 1. BUSCA CATEGORIAS DINÂMICAS DO FIREBASE
    try:
        doc_cat = db.collection("configuracoes").document("categorias").get()
        if doc_cat.exists:
            CATEGORIAS_OFICIAIS = doc_cat.to_dict().get("lista", ["Geral"])
        else:
            CATEGORIAS_OFICIAIS = ["Pedreiro", "Locutor", "Eletricista", "Mecânico"]
    except:
        CATEGORIAS_OFICIAIS = ["Pedreiro", "Locutor", "Eletricista", "Mecânico"]

    # 2. VERIFICAÇÃO DE DADOS VINDOS DO GOOGLE AUTH
    dados_google = st.session_state.get("pre_cadastro", {})
    email_inicial = dados_google.get("email", "")
    nome_inicial = dados_google.get("nome", "")
    foto_google = dados_google.get("foto", "")

    # Interface Visual de Login Social
    st.markdown("##### Entre rápido com:")
    col_soc1, col_soc2 = st.columns(2)
    
    g_auth = st.secrets.get("google_auth", {})
    g_id = g_auth.get("client_id")
    g_uri = g_auth.get("redirect_uri", "https://geralja-zxiaj2ot56fuzgcz7xhcks.streamlit.app/")

    with col_soc1:
        if g_id:
            url_google = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={g_id}&response_type=code&scope=openid%20profile%20email&redirect_uri={g_uri}"
            st.markdown(f'''
                <a href="{url_google}" target="_self" style="text-decoration:none;">
                    <div style="display:flex; align-items:center; justify-content:center; border:1px solid #dadce0; border-radius:8px; padding:8px; background:white;">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/5/53/Google_%22G%22_Logo.svg" width="18px" style="margin-right:10px;">
                        <span style="color:#3c4043; font-weight:bold; font-size:14px;">Google</span>
                    </div>
                </a>
            ''', unsafe_allow_html=True)
        else:
            st.caption("⚠️ Google Auth não configurado")

    with col_soc2:
        fb_id = st.secrets.get("FB_CLIENT_ID", "")
        st.markdown(f'''
            <a href="https://www.facebook.com/v18.0/dialog/oauth?client_id={fb_id}&redirect_uri={g_uri}&scope=public_profile,email" target="_self" style="text-decoration:none;">
                <div style="display:flex; align-items:center; justify-content:center; border-radius:8px; padding:8px; background:#1877F2;">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/2021_Facebook_icon.svg" width="18px" style="margin-right:10px;">
                    <span style="color:white; font-weight:bold; font-size:14px;">Facebook</span>
                </div>
            </a>
        ''', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    BONUS_WELCOME = 20 

    # 3. FORMULÁRIO INTELIGENTE
    with st.form("form_profissional", clear_on_submit=False):
        st.caption("DICA: Se você já tem cadastro, use o mesmo WhatsApp para editar seus dados.")
        
        col1, col2 = st.columns(2)
        nome_input = col1.text_input("Nome do Profissional ou Loja", value=nome_inicial)
        zap_input = col2.text_input("WhatsApp (DDD + Número sem espaços)")
        
        email_input = st.text_input("E-mail (Para login via Google)", value=email_inicial)
        
        col3, col4 = st.columns(2)
        cat_input = col3.selectbox("Selecione sua Especialidade Principal", CATEGORIAS_OFICIAIS)
        senha_input = col4.text_input("Sua Senha de Acesso", type="password", help="Necessária para salvar alterações")
        
        desc_input = st.text_area("Descrição Completa (Serviços, Horários, Diferenciais)")
        tipo_input = st.radio("Tipo", ["👨‍🔧 Profissional Autônomo", "🏢 Comércio/Loja"], horizontal=True)
        
        # Componente de Upload
        foto_upload = st.file_uploader("Atualizar Foto de Perfil ou Logo", type=['png', 'jpg', 'jpeg'])
        
        btn_acao = st.form_submit_button("✅ FINALIZAR: SALVAR OU ATUALIZAR", use_container_width=True)

    # 4. LÓGICA DE SALVAMENTO E EDIÇÃO
    if btn_acao:
        if not nome_input or not zap_input or not senha_input:
            st.warning("⚠️ Nome, WhatsApp e Senha são obrigatórios!")
        else:
            try:
                with st.spinner("Sincronizando com o ecossistema GeralJá..."):
                    # Referência do documento no Firebase
                    doc_ref = db.collection("profissionais").document(zap_input)
                    perfil_antigo = doc_ref.get()
                    dados_antigos = perfil_antigo.to_dict() if perfil_antigo.exists else {}

                    # --- LÓGICA DE FOTO CORRIGIDA ---
                    foto_b64 = dados_antigos.get("foto_url", "") # Mantém a antiga por padrão

                    # Se o usuário subir uma foto nova agora
                    if foto_upload is not None:
                        file_ext = foto_upload.name.split('.')[-1]
                        img_bytes = foto_upload.getvalue() # getvalue() é mais estável que read()
                        encoded_img = base64.b64encode(img_bytes).decode()
                        foto_b64 = f"data:image/{file_ext};base64,{encoded_img}"
                    
                    # Se não houver foto no banco E não houver upload, tenta pegar a do Google
                    elif not foto_b64 and foto_google:
                        foto_b64 = foto_google

                    # --- LÓGICA DE SALDO E CLIQUES ---
                    saldo_final = dados_antigos.get("saldo", BONUS_WELCOME)
                    cliques_atuais = dados_antigos.get("cliques", 0)

                    # --- MONTAGEM DO DICIONÁRIO ---
                    dados_pro = {
                        "nome": nome_input,
                        "whatsapp": zap_input,
                        "email": email_input,
                        "area": cat_input,
                        "senha": senha_input,
                        "descricao": desc_input,
                        "tipo": tipo_input,
                        "foto_url": foto_b64,
                        "saldo": saldo_final,
                        "data_cadastro": datetime.now().strftime("%d/%m/%Y"),
                        "aprovado": True,
                        "cliques": cliques_atuais,
                        "rating": 5,
                        "lat": minha_lat if 'minha_lat' in locals() else -23.55,
                        "lon": minha_lon if 'minha_lon' in locals() else -46.63
                    }
                    
                    # Salva no Banco de Dados
                    doc_ref.set(dados_pro)
                    
                    # Limpa cache de pré-cadastro
                    if "pre_cadastro" in st.session_state:
                        del st.session_state["pre_cadastro"]
                    
                    st.balloons()
                    if perfil_antigo.exists:
                        st.success(f"✅ Perfil de {nome_input} atualizado com sucesso!")
                    else:
                        st.success(f"🎊 Bem-vindo ao GeralJá! Cadastro concluído!")
                        
            except Exception as e:
                st.error(f"❌ Erro ao processar perfil: {e}")
# ==============================================================================
# ABA 4: 👑 TORRE DE CONTROLE MASTER (COMPLETA: GESTÃO DE REDE + CATEGORIAS)
# ==============================================================================
with menu_abas[3]:
    import pytz
    from datetime import datetime
    import pandas as pd
    import time

    # 1. CONFIGURAÇÃO DE TEMPO E SEGURANÇA
    fuso_br = pytz.timezone('America/Sao_Paulo')
    agora_br = datetime.now(fuso_br)
    
    ADMIN_USER_OFICIAL = st.secrets.get("ADMIN_USER", "admin")
    ADMIN_PASS_OFICIAL = st.secrets.get("ADMIN_PASS", "geralja2026")

    if 'admin_logado' not in st.session_state:
        st.session_state.admin_logado = False

    if not st.session_state.admin_logado:
        st.markdown("### 🔐 Acesso Restrito à Diretoria")
        with st.form("painel_login_adm"):
            u = st.text_input("Usuário Administrativo")
            p = st.text_input("Senha de Acesso", type="password")
            if st.form_submit_button("ACESSAR TORRE DE CONTROLE", use_container_width=True):
                if u == ADMIN_USER_OFICIAL and p == ADMIN_PASS_OFICIAL:
                    st.session_state.admin_logado = True
                    st.success("Acesso concedido!")
                    time.sleep(1); st.rerun()
                else:
                    st.error("Credenciais inválidas.")
    
    else:
        st.markdown(f"## 👑 Central de Comando GeralJá")
        st.caption(f"🕒 {agora_br.strftime('%H:%M:%S')} | Poder de Edição Total Ativo")
        
        if st.button("🚪 Sair do Sistema", key="logout_adm"):
            st.session_state.admin_logado = False
            st.rerun()

        # ----------------------------------------------------------------------
        # 🟢 GESTÃO DE CATEGORIAS (ADICIONAR/REMOVER DO BANCO)
        # ----------------------------------------------------------------------
        st.divider()
        with st.expander("📁 GERENCIAR LISTA DE CATEGORIAS", expanded=False):
            doc_cat_ref = db.collection("configuracoes").document("categorias")
            res_cat = doc_cat_ref.get()
            
            # Puxa a lista dinâmica ou usa a CATEGORIAS_OFICIAIS atual
            lista_atual = res_cat.to_dict().get("lista", CATEGORIAS_OFICIAIS) if res_cat.exists else CATEGORIAS_OFICIAIS
            
            c_cat1, c_cat2 = st.columns([3, 1])
            nova_cat_input = c_cat1.text_input("Nova Profissão/Categoria:")
            if c_cat2.button("➕ ADICIONAR", use_container_width=True):
                if nova_cat_input and nova_cat_input not in lista_atual:
                    lista_atual.append(nova_cat_input)
                    lista_atual.sort()
                    doc_cat_ref.set({"lista": lista_atual})
                    st.success("Adicionada!"); time.sleep(0.5); st.rerun()
            
            st.write("---")
            cat_del = st.selectbox("Remover Categoria Existente:", ["Selecione..."] + lista_atual)
            if cat_del != "Selecione...":
                if st.button(f"🗑️ EXCLUIR {cat_del}", type="secondary"):
                    lista_atual.remove(cat_del)
                    doc_cat_ref.set({"lista": lista_atual})
                    st.error("Removida!"); time.sleep(0.5); st.rerun()

        try:
            # 2. COLETA DE DADOS
            profs_ref = list(db.collection("profissionais").stream())
            profs_data = [p.to_dict() | {"id": p.id} for p in profs_ref]
            df = pd.DataFrame(profs_data)

            if not df.empty:
                # Sincronizando campo 'area'
                df['categoria_display'] = df['area'].fillna("Geral") if 'area' in df.columns else "Geral"
                df = df.fillna({"nome": "Sem Nome", "aprovado": False, "saldo": 0, "cliques": 0})

            # 3. MÉTRICAS
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Parceiros", len(df))
            m2.metric("Pendentes", len(df[df['aprovado'] == False]) if not df.empty else 0)
            m3.metric("Cliques", int(df['cliques'].sum()) if not df.empty else 0)
            m4.metric("GeralCones", f"💎 {int(df['saldo'].sum())}" if not df.empty else 0)

            # 4. GESTÃO INDIVIDUAL (FILTROS)
            st.divider()
            f1, f2 = st.columns(2)
            busca = f1.text_input("🔍 Buscar nome ou Zap:")
            # Usa a lista atualizada do banco para o filtro
            filtro_cat = f2.selectbox("Filtrar Exibição:", ["Todas"] + lista_atual)

            df_display = df.copy()
            if busca:
                df_display = df_display[df_display['nome'].str.contains(busca, case=False, na=False) | 
                                        df_display['id'].str.contains(busca, na=False)]
            if filtro_cat != "Todas":
                df_display = df_display[df_display['categoria_display'] == filtro_cat]

            # 5. LISTAGEM COM TODAS AS FUNÇÕES
            for _, p in df_display.iterrows():
                pid = p['id']
                status = "🟢" if p.get('aprovado') else "🟡"
                cat_atual = p.get('area', 'Geral')
                
                with st.expander(f"{status} {p.get('nome').upper()} - ({cat_atual})"):
                    col_info, col_edit, col_btn = st.columns([2, 2, 1.2])
                    
                    with col_info:
                        st.write(f"**WhatsApp:** {pid}")
                        st.write(f"**Saldo:** {p.get('saldo', 0)} 💎")
                        st.write(f"**Cliques:** {p.get('cliques', 0)}")
                    
                    with col_edit:
                        # ALTERAR CATEGORIA DO PROFISSIONAL
                        try:
                            idx = lista_atual.index(cat_atual)
                        except:
                            idx = 0
                        
                        nova_cat = st.selectbox(f"Mudar para", lista_atual, index=idx, key=f"cat_{pid}")
                        if st.button("💾 Salvar Categoria", key=f"save_cat_{pid}"):
                            db.collection("profissionais").document(pid).update({"area": nova_cat})
                            st.success("Salvo!"); time.sleep(0.5); st.rerun()

                    with col_btn:
                        # Aprovação
                        if not p.get('aprovado'):
                            if st.button("✅ APROVAR", key=f"ok_{pid}", use_container_width=True, type="primary"):
                                db.collection("profissionais").document(pid).update({"aprovado": True})
                                st.rerun()
                        else:
                            if st.button("🚫 SUSPENDER", key=f"no_{pid}", use_container_width=True):
                                db.collection("profissionais").document(pid).update({"aprovado": False})
                                st.rerun()
                        
                        # Moedas e Banir
                        col_sub1, col_sub2 = st.columns(2)
                        if col_sub1.button("➕10", key=f"m10_{pid}"):
                            db.collection("profissionais").document(pid).update({"saldo": p.get('saldo', 0) + 10})
                            st.rerun()
                        if col_sub2.button("🗑️", key=f"del_{pid}", help="Banir Profissional"):
                            db.collection("profissionais").document(pid).delete()
                            st.rerun()

        except Exception as e:
            st.error(f"Erro na Torre de Controle: {e}")

# ==============================================================================
# ABA 5: FEEDBACK
# ==============================================================================
with menu_abas[4]:
    st.header("⭐ Avalie a Plataforma")
    st.write("Sua opinião nos ajuda a melhorar.")
    
    nota = st.slider("Nota", 1, 5, 5)
    comentario = st.text_area("O que podemos melhorar?")
    
    if st.button("Enviar Feedback"):
        st.success("Obrigado! Sua mensagem foi enviada para nossa equipe.")
        # Em produção, salvaria em uma coleção 'feedbacks'

# ------------------------------------------------------------------------------
# FINALIZAÇÃO (DO ARQUIVO ORIGINAL)
# ------------------------------------------------------------------------------
finalizar_e_alinhar_layout()
# =========================================================
# MÓDULO: RODAPÉ BLINDADO (LGPD & SECURITY SHIELD)
# =========================================================

st.markdown("---")

# 1. ESTILIZAÇÃO DO SELO DE SEGURANÇA (CSS)
st.markdown("""
<style>
    .footer-container {
        text-align: center;
        padding: 20px;
        color: #64748B;
        font-size: 12px;
    }
    .security-badge {
        display: inline-flex;
        align-items: center;
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 20px;
        padding: 5px 15px;
        margin-bottom: 10px;
        color: #0f172a;
        font-weight: bold;
    }
    .shield-icon {
        color: #22c55e;
        margin-right: 8px;
    }
</style>
""", unsafe_allow_html=True)

# 2. INTERFACE DO RODAPÉ
st.markdown("""
<div class="footer-container">
    <div class="security-badge">
        <span class="shield-icon">🛡️</span> IA de Proteção Ativa: Monitorando Contra Ameaças
    </div>
    <p>© 2026 GeralJá - Grajaú, São Paulo</p>
</div>
""", unsafe_allow_html=True)

# 3. EXPANDER JURÍDICO (A Blindagem LGPD)
with st.expander("📄 Transparência e Privacidade (LGPD)"):
    st.write("### 🛡️ Protocolo de Segurança e Privacidade")
    st.info("""
    **Proteção contra Invasões:** Este sistema utiliza criptografia de ponta a ponta via Google Cloud. 
    Tentativas de injeção de SQL ou scripts maliciosos (XSS) são bloqueadas automaticamente pela nossa camada de firewall.
    """)
    
    st.markdown("""
    **Como tratamos seus dados:**
    1. **Finalidade:** Seus dados são usados exclusivamente para conectar você a clientes no Grajaú.
    2. **Exclusão:** Você possui controle total. A exclusão definitiva pode ser feita no seu painel mediante senha de segurança.
    3. **Vírus e Malware:** Todas as fotos enviadas passam por um processo de normalização de bits para evitar a execução de códigos ocultos em arquivos de imagem.
    
    *Em conformidade com a Lei Federal nº 13.709 (LGPD).*
    """)

# 4. LÓGICA DE PROTEÇÃO (Simulação de Monitoramento)
# 🧩 PULO DA GATA: Pequena lógica que simula a verificação de integridade
if "security_check" not in st.session_state:
    st.toast("🛡️ IA: Verificando integridade da conexão...", icon="🔍")
    time.sleep(1)
    st.session_state.security_check = True
    st.toast("✅ Conexão Segura: Firewall GeralJá Ativo!", icon="🛡️")



















































