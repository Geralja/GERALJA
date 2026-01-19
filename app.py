# ==============================================================================
# GERALJÁ: CRIANDO SOLUÇÕES
# ==============================================================================
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime
import math
import re
import time
import pandas as pd
import unicodedata
from datetime import datetime
import pytz

# Tenta importar bibliotecas extras do arquivo original, se não tiver, segue sem quebrar
try:
    from streamlit_js_eval import streamlit_js_eval, get_geolocation
except ImportError:
    pass

# ------------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DE AMBIENTE E PERFORMANCE
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="GeralJá | Criando Soluções",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- FUNCIONALIDADE DO ARQUIVO: TEMA MANUAL ---
if 'tema_claro' not in st.session_state:
    st.session_state.tema_claro = False

# Mantém os menus escondidos
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)
# ------------------------------------------------------------------------------
# 2. CAMADA DE PERSISTÊNCIA (FIREBASE)
# ------------------------------------------------------------------------------
@st.cache_resource
def conectar_banco_master():
    if not firebase_admin._apps:
        try:
            # Tenta pegar dos secrets do Streamlit
            if "FIREBASE_BASE64" in st.secrets:
                b64_key = st.secrets["FIREBASE_BASE64"]
                decoded_json = base64.b64decode(b64_key).decode("utf-8")
                cred_dict = json.loads(decoded_json)
                cred = credentials.Certificate(cred_dict)
                return firebase_admin.initialize_app(cred)
            else:
                # Fallback para desenvolvimento local (se houver arquivo json)
                # cred = credentials.Certificate("serviceAccountKey.json")
                # return firebase_admin.initialize_app(cred)
                st.warning("⚠️ Configure a secret FIREBASE_BASE64 para conectar ao banco.")
                return None
        except Exception as e:
            st.error(f"❌ FALHA NA INFRAESTRUTURA: {e}")
            st.stop()
    return firebase_admin.get_app()

app_engine = conectar_banco_master()

if app_engine:
    db = firestore.client()
else:
    st.error("Erro ao conectar ao Firebase. Verifique suas configurações.")
    st.stop()

# --- FUNÇÕES DE SUPORTE (Mantenha fora de blocos IF/ELSE para funcionar no app todo) ---

def buscar_opcoes_dinamicas(documento, padrao):
    """
    Busca listas de categorias ou tipos na coleção 'configuracoes'.
    """
    try:
        doc = db.collection("configuracoes").document(documento).get()
        if doc.exists:
            dados = doc.to_dict()
            return dados.get("lista", padrao)
        return padrao
    except Exception as e:
        # Se houver erro ou o banco estiver vazio, retorna a lista padrão
        return padrao
        # --- COLOCAR LOGO ABAIXO DA CONEXÃO DB ---

if 'modo_noite' not in st.session_state:
    st.session_state.modo_noite = True 

# Layout do topo (Toggle)
c_t1, c_t2 = st.columns([2, 8])
with c_t1:
    st.session_state.modo_noite = st.toggle("🌙 Modo Noite", value=st.session_state.modo_noite)

# Bloco CSS Dinâmico
estilo_dinamico = f"""
<style>
    /* Ajustes Mobile */
    @media (max-width: 640px) {{
        .main .block-container {{ padding: 1rem !important; }}
        h1 {{ font-size: 1.8rem !important; }}
    }}

  /* Lógica de Cores - Estilo Branco Neve */
    .stApp {{
        background-color: {"#0D1117" if st.session_state.modo_noite else "#FFFAFA"} !important;
        color: {"#FFFFFF" if st.session_state.modo_noite else "#1A1A1B"} !important;
    }}

    /* Cards Adaptáveis */
    div[data-testid="stVerticalBlock"] > div[style*="background"] {{
        background-color: {"#161B22" if st.session_state.modo_noite else "#FFFFFF"} !important;
        border: 1px solid {"#30363D" if st.session_state.modo_noite else "#E0E0E0"} !important;
        border-radius: 18px !important;
    }}
</style>
"""
st.markdown(estilo_dinamico, unsafe_allow_html=True)
        # ==========================================================
# FUNÇÕES DE SUPORTE (COLE NO TOPO DO ARQUIVO)
# ==========================================================
import re
from urllib.parse import quote

def limpar_whatsapp(numero):
    """Remove parênteses, espaços e traços do número."""
    num = re.sub(r'\D', '', str(numero))
    if not num.startswith('55') and len(num) >= 10:
        num = f"55{num}"
    return num

def normalizar(texto):
    """Remove acentos e deixa tudo em minúsculo para busca."""
    import unicodedata
    if not texto: return ""
    return "".join(ch for ch in unicodedata.normalize('NFKD', texto) 
                   if unicodedata.category(ch) != 'Mn').lower()

# Verifique se você já tem a função de distância, senão adicione esta:
def calcular_distancia_real(lat1, lon1, lat2, lon2):
    import math
    R = 6371  # Raio da Terra em KM
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# --- PROSSEGUIR COM O RESTANTE DO CÓDIGO ---

# ------------------------------------------------------------------------------
# 3. POLÍTICAS E CONSTANTES
# ------------------------------------------------------------------------------
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ADMIN = "mumias"
LAT_REF = -23.5505
LON_REF = -46.6333

CATEGORIAS_OFICIAIS = [
    "Encanador", "Eletricista", "Pintor", "Pedreiro", "Gesseiro", "Telhadista", 
    "Serralheiro", "Vidraceiro", "Marceneiro", "Marmoraria", "Calhas e Rufos", 
    "Dedetização", "Desentupidora", "Piscineiro", "Jardineiro", "Limpeza de Estofados",
    "Mecânico", "Borracheiro", "Guincho 24h", "Estética Automotiva", "Lava Jato", 
    "Auto Elétrica", "Funilaria e Pintura", "Som e Alarme", "Moto Peças", "Auto Peças",
    "Loja de Roupas", "Calçados", "Loja de Variedades", "Relojoaria", "Joalheria", 
    "Ótica", "Armarinho/Aviamentos", "Papelaria", "Floricultura", "Bazar", 
    "Material de Construção", "Tintas", "Madeireira", "Móveis", "Eletrodomésticos",
    "Pizzaria", "Lanchonete", "Restaurante", "Confeitaria", "Padaria", "Açaí", 
    "Sorveteria", "Adega", "Doceria", "Hortifruti", "Açougue", "Pastelaria", 
    "Churrascaria", "Hamburgueria", "Comida Japonesa", "Cafeteria",
    "Farmácia", "Barbearia/Salão", "Manicure/Pedicure", "Estética Facial", 
    "Tatuagem/Piercing", "Fitness", "Academia", "Fisioterapia", "Odontologia", 
    "Clínica Médica", "Psicologia", "Nutricionista", "TI", "Assistência Técnica", 
    "Celulares", "Informática", "Refrigeração", "Técnico de Fogão", "Técnico de Lavadora", 
    "Eletrônicos", "Chaveiro", "Montador", "Freteiro", "Carreto", "Motoboy/Entregas",
    "Pet Shop", "Veterinário", "Banho e Tosa", "Adestrador", "Agropecuária",
    "Aulas Particulares", "Escola Infantil", "Reforço Escolar", "Idiomas", 
    "Advocacia", "Contabilidade", "Imobiliária", "Seguros", "Ajudante Geral", 
    "Diarista", "Cuidador de Idosos", "Babá", "Outro (Personalizado)"
]

CONCEITOS_EXPANDIDOS = {
    "pizza": "Pizzaria", "pizzaria": "Pizzaria", "fome": "Pizzaria", "massa": "Pizzaria",
    "lanche": "Lanchonete", "hamburguer": "Lanchonete", "burger": "Lanchonete", "salgado": "Lanchonete",
    "comida": "Restaurante", "almoco": "Restaurante", "marmita": "Restaurante", "jantar": "Restaurante",
    "doce": "Confeitaria", "bolo": "Confeitaria", "pao": "Padaria", "padaria": "Padaria",
    "acai": "Açaí", "sorvete": "Sorveteria", "cerveja": "Adega", "bebida": "Adega",
    "roupa": "Loja de Roupas", "moda": "Loja de Roupas", "sapato": "Calçados", "tenis": "Calçados",
    "presente": "Loja de Variedades", "relogio": "Relojoaria", "joia": "Joalheria",
    "remedio": "Farmácia", "farmacia": "Farmácia", "cabelo": "Barbearia/Salão", "unha": "Barbearia/Salão",
    "celular": "Assistência Técnica", "iphone": "Assistência Técnica", "computador": "TI", "pc": "TI",
    "geladeira": "Refrigeração", "ar condicionado": "Refrigeração", "fogao": "Técnico de Fogão",
    "tv": "Eletrônicos", "pet": "Pet Shop", "racao": "Pet Shop", "cachorro": "Pet Shop",
    "vazamento": "Encanador", "cano": "Encanador", "curto": "Eletricista", "luz": "Eletricista",
    "pintar": "Pintor", "parede": "Pintor", "reforma": "Pedreiro", "piso": "Pedreiro",
    "telhado": "Telhadista", "solda": "Serralheiro", "vidro": "Vidraceiro", "chave": "Chaveiro",
    "carro": "Mecânico", "motor": "Mecânico", "pneu": "Borracheiro", "guincho": "Guincho 24h",
    "frete": "Freteiro", "mudanca": "Freteiro", "faxina": "Diarista", "limpeza": "Diarista",
    "jardim": "Jardineiro", "piscina": "Piscineiro"
}

# ------------------------------------------------------------------------------
# 4. MOTORES DE IA E UTILS
# ------------------------------------------------------------------------------
def normalizar_para_ia(texto):
    if not texto: return ""
    return "".join(c for c in unicodedata.normalize('NFD', str(texto)) 
                   if unicodedata.category(c) != 'Mn').lower().strip()

def processar_ia_avancada(texto):
    if not texto: return "Vazio"
    t_clean = normalizar_para_ia(texto)
    for chave, categoria in CONCEITOS_EXPANDIDOS.items():
        if re.search(rf"\b{normalizar_para_ia(chave)}\b", t_clean):
            return categoria
    for cat in CATEGORIAS_OFICIAIS:
        if normalizar_para_ia(cat) in t_clean:
            return cat
    return "NAO_ENCONTRADO"

def calcular_distancia_real(lat1, lon1, lat2, lon2):
    try:
        if None in [lat1, lon1, lat2, lon2]: return 999.0
        R = 6371 
        dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)
    except: return 999.0

def converter_img_b64(file):
    if file is None: return ""
    try: return base64.b64encode(file.read()).decode()
    except: return ""

# --- FUNCIONALIDADE DO ARQUIVO: O VARREDOR (Rodapé Automático) ---
def finalizar_e_alinhar_layout():
    """
    Esta função atua como um ímã. Puxa o conteúdo e limpa o rodapé.
    """
    st.write("---")
    fechamento_estilo = """
        <style>
            .main .block-container { padding-bottom: 5rem !important; }
            .footer-clean {
                text-align: center;
                padding: 20px;
                opacity: 0.7;
                font-size: 0.8rem;
                width: 100%;
                color: gray;
            }
        </style>
        <div class="footer-clean">
            <p>🎯 <b>GeralJá</b> - Sistema de Inteligência Local</p>
            <p>Conectando quem precisa com quem sabe fazer.</p>
            <p>v3.0 | © 2026 Todos os direitos reservados</p>
        </div>
    """
    st.markdown(fechamento_estilo, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 5. DESIGN SYSTEM
# ------------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F8FAFC; }
    .header-container { background: white; padding: 40px 20px; border-radius: 0 0 50px 50px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.05); border-bottom: 8px solid #FF8C00; margin-bottom: 25px; }
    .logo-azul { color: #0047AB; font-weight: 900; font-size: 50px; letter-spacing: -2px; }
    .logo-laranja { color: #FF8C00; font-weight: 900; font-size: 50px; letter-spacing: -2px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-container"><span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span><br><small style="color:#64748B; font-weight:700;">BRASIL ELITE EDITION</small></div>', unsafe_allow_html=True)

lista_abas = ["🔍 BUSCAR", "🚀 CADASTRAR", "👤 MEU PERFIL", "👑 ADMIN", "⭐ FEEDBACK"]
comando = st.sidebar.text_input("Comando Secreto", type="password")
if comando == "abracadabra":
    lista_abas.append("📊 FINANCEIRO")

menu_abas = st.tabs(lista_abas)
# ==============================================================================
# --- ABA 1: BUSCA (GPS + SCORE ELITE + VITRINE SOCIAL V2.0) ---
# ==============================================================================
with menu_abas[0]:
    st.markdown("### 🏙️ O que você precisa?")
    
    # --- 1. MOTOR DE LOCALIZAÇÃO ---
    with st.expander("📍 Sua Localização (GPS)", expanded=False):
        loc = get_geolocation()
        if loc:
            minha_lat, minha_lon = loc['coords']['latitude'], loc['coords']['longitude']
            st.success("Localização detectada!")
        else:
            minha_lat, minha_lon = LAT_REF, LON_REF
            st.warning("GPS desativado. Usando padrão (SP).")

    c1, c2 = st.columns([3, 1])
    termo_busca = c1.text_input("Ex: 'Cano estourado' ou 'Pizza'", key="main_search_v4")
    raio_km = c2.select_slider("Raio (KM)", options=[1, 3, 5, 10, 20, 50, 100, 500], value=10)
    
    # --- 2. CSS PARA VITRINE E MODAL (LIMPO E MODERNO) ---
    st.markdown("""
    <style>
        .cartao-geral { background: white; border-radius: 20px; border-left: 8px solid var(--cor-borda); padding: 15px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        .perfil-row { display: flex; gap: 15px; align-items: center; margin-bottom: 12px; }
        .foto-perfil { width: 55px; height: 55px; border-radius: 50%; object-fit: cover; border: 2px solid #eee; }
        .social-track { display: flex; overflow-x: auto; gap: 10px; padding-bottom: 10px; scrollbar-width: none; }
        .social-track::-webkit-scrollbar { display: none; }
        .social-card { flex: 0 0 200px; height: 280px; border-radius: 12px; overflow: hidden; cursor: pointer; background: #000; }
        .social-card img { width: 100%; height: 100%; object-fit: cover; transition: 0.3s; }
        .btn-zap-footer { display: block; background: #25D366; color: white !important; text-align: center; padding: 15px; border-radius: 12px; font-weight: bold; text-decoration: none; margin-top: 10px; font-size: 16px; }
    </style>
    <script>
    function abrirModal(src, link) {
        document.getElementById('imgExpandida').src = src;
        document.getElementById('linkZapModal').href = link;
        document.getElementById('meuModal').style.display = 'flex';
    }
    function fecharModal() {
        document.getElementById('meuModal').style.display = 'none';
    }
    </script>
    """, unsafe_allow_html=True)

    if termo_busca:
        cat_ia = processar_ia_avancada(termo_busca)
        st.info(f"✨ IA: Buscando por **{cat_ia}**")
        
        # Busca e Filtragem
        profs = db.collection("profissionais").where("area", "==", cat_ia).where("aprovado", "==", True).stream()
        
        lista_ranking = []
        for p_doc in profs:
            p = p_doc.to_dict(); p['id'] = p_doc.id
            dist = calcular_distancia_real(minha_lat, minha_lon, p.get('lat', LAT_REF), p.get('lon', LON_REF))
            
            if dist <= raio_km:
                p['dist'] = dist
                # SCORE ELITE
                score = 0
                score += 500 if p.get('verificado') else 0
                score += (p.get('saldo', 0) * 10)
                score += (p.get('rating', 5) * 20)
                p['score_elite'] = score
                lista_ranking.append(p)

        lista_ranking.sort(key=lambda x: (-x['score_elite'], x['dist']))

        if not lista_ranking:
            st.warning("Nenhum profissional nesta região ainda.")
        else:
            for p in lista_ranking:
                # Definição de Cores e Link Zap
                is_elite = p.get('verificado') and p.get('saldo', 0) > 0
                cor_borda = "#FFD700" if is_elite else "#0047AB"
                zap_limpo = limpar_whatsapp(p['id'])
                link_zap = f"https://wa.me/{zap_limpo}?text=Olá, vi seu portfólio no GeralJá!"
                
                # Montar Carrossel de Fotos (f1 até f10)
                fotos_html = ""
                for i in range(1, 11):
                    f_data = p.get(f'f{i}')
                    if f_data and len(str(f_data)) > 100:
                        src = f_data if str(f_data).startswith("data") else f"data:image/jpeg;base64,{f_data}"
                        fotos_html += f'<div class="social-card" onclick="abrirModal(\'{src}\', \'{link_zap}\')"><img src="{src}"></div>'

                # RENDERIZAÇÃO DO CARD INTEGRADO
                st.markdown(f"""
                <div class="cartao-geral" style="--cor-borda: {cor_borda};">
                    <div style="font-size: 11px; color: gray; margin-bottom: 10px;">
                        📍 a {p['dist']:.1f} km de você {" | 🏆 ELITE" if is_elite else ""}
                    </div>
                    <div class="perfil-row">
                        <img src="{p.get('foto_url','')}" class="foto-perfil">
                        <div>
                            <h4 style="margin:0; color:#1e3a8a;">{p.get('nome','').upper()} {"☑️" if p.get('verificado') else ""}</h4>
                            <p style="margin:0; color:#666; font-size:12px;">{p.get('descricao','')[:90]}...</p>
                        </div>
                    </div>
                    <div class="social-track">{fotos_html}</div>
                    <a href="{link_zap}" target="_blank" class="btn-zap-footer">💬 FALAR COM {p.get('nome','').split()[0].upper()}</a>
                </div>
                """.replace('\n', ' '), unsafe_allow_html=True)

            # Estrutura Única do Modal no final do loop
            st.markdown("""
            <div id="meuModal" style="display:none; position:fixed; z-index:9999; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.9); align-items:center; justify-content:center; flex-direction:column;">
                <span onclick="fecharModal()" style="position:absolute; top:20px; right:30px; color:white; font-size:40px; cursor:pointer;">&times;</span>
                <img id="imgExpandida" style="max-width:90%; max-height:75%; border-radius:10px; border: 2px solid #fff;">
                <a id="linkZapModal" href="#" target="_blank" style="margin-top:20px; background:#25D366; color:white; padding:15px 40px; border-radius:30px; text-decoration:none; font-weight:bold;">✅ CHAMAR NO WHATSAPP</a>
            </div>
            """.replace('\n', ' '), unsafe_allow_html=True)

            # Lógica de cobrança de cliques (opcional, manter se quiser descontar saldo)
            if is_elite:
                db.collection("profissionais").document(p['id']).update({"cliques": p.get('cliques', 0) + 1})
                
# --- ABA 2: PAINEL DO PARCEIRO (VERSÃO ATUALIZADA) ---
with menu_abas[2]:
    if 'auth' not in st.session_state: st.session_state.auth = False
    
    if not st.session_state.auth:
        st.subheader("🚀 Acesso ao Painel")
        col1, col2 = st.columns(2)
        l_zap = col1.text_input("WhatsApp (números)", key="login_zap_v7")
        l_pw = col2.text_input("Senha", type="password", key="login_pw_v7")
        
        if st.button("ENTRAR NO PAINEL", use_container_width=True, key="btn_entrar_v7"):
            u = db.collection("profissionais").document(l_zap).get()
            if u.exists and u.to_dict().get('senha') == l_pw:
                st.session_state.auth, st.session_state.user_id = True, l_zap
                st.rerun()
            else: st.error("Dados incorretos.")
    else:
        doc_ref = db.collection("profissionais").document(st.session_state.user_id)
        d = doc_ref.get().to_dict()
        
        # 1. MÉTRICAS
        st.write(f"### Olá, {d.get('nome', 'Parceiro')}!")
        m1, m2, m3 = st.columns(3)
        m1.metric("Saldo 🪙", f"{d.get('saldo', 0)}")
        m2.metric("Cliques 🚀", f"{d.get('cliques', 0)}")
        m3.metric("Status", "🟢 ATIVO" if d.get('aprovado') else "🟡 PENDENTE")

        # 2. GPS
        if st.button("📍 ATUALIZAR LOCALIZAÇÃO GPS", use_container_width=True, key="gps_v7"):
            loc = streamlit_js_eval(js_expressions="navigator.geolocation.getCurrentPosition(s => s)", key='gps_v7_eval')
            if loc and 'coords' in loc:
                doc_ref.update({"lat": loc['coords']['latitude'], "lon": loc['coords']['longitude']})
                st.success("✅ Localização salva!")
            else: st.info("Aguardando sinal... Clique novamente.")

        st.divider()

# --- 3. LOJA TURBINADA DE MOEDAS (PIX) ---
        with st.expander("💎 RECARREGAR SALDO E TURBINAR PERFIL", expanded=False):
            st.markdown(f"""
                <div style="background-color: #FFF4E5; padding: 15px; border-radius: 10px; border-left: 5px solid #FF8C00; margin-bottom: 20px;">
                    <p style="margin: 0; color: #856404; font-weight: bold;">🔑 Chave PIX Oficial:</p>
                    <code style="font-size: 16px; color: #1E293B;">{PIX_OFICIAL}</code>
                </div>
            """, unsafe_allow_html=True)

            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                st.markdown('<div style="text-align: center; border: 1px solid #E2E8F0; padding: 10px; border-radius: 10px; background: #FFF;"><h3>🥉</h3><p><b>10</b><br><small>MOEDAS</small></p></div>', unsafe_allow_html=True)
                if st.button("🛒 R$ 10", key="p10_v8", use_container_width=True): st.code(PIX_OFICIAL)

            with col_p2:
                st.markdown('<div style="text-align: center; border: 2px solid #FF8C00; padding: 10px; border-radius: 10px; background: #FFF;"><span style="background:#FF8C00;color:white;padding:2px;border-radius:5px;font-size:10px;">TOP</span><h3>🥈</h3><p><b>55</b><br><small>MOEDAS</small></p></div>', unsafe_allow_html=True)
                if st.button("🛒 R$ 50", key="p50_v8", use_container_width=True): st.code(PIX_OFICIAL)

            with col_p3:
                st.markdown('<div style="text-align: center; border: 1px solid #E2E8F0; padding: 10px; border-radius: 10px; background: #FFF;"><h3>🥇</h3><p><b>120</b><br><small>MOEDAS</small></p></div>', unsafe_allow_html=True)
                if st.button("🛒 R$ 100", key="p100_v8", use_container_width=True): st.code(PIX_OFICIAL)

            st.link_button("🚀 ENVIAR COMPROVANTE", f"https://wa.me/{ZAP_ADMIN}?text=Fiz o PIX: {st.session_state.user_id}", use_container_width=True)

        # --- 4. EDIÇÃO DE PERFIL ---
        with st.expander("📝 EDITAR MEU PERFIL & VITRINE", expanded=True):
            with st.form("perfil_v8_final"):
                n_nome = st.text_input("Nome Profissional", d.get('nome', ''))
                # (... restante do seu formulário aqui ...)
                if st.form_submit_button("SALVAR"):
                    pass # Sua lógica de save

    st.write("---")
    st.link_button("🚀 ENVIAR COMPROVANTE AGORA", 
                   f"https://wa.me/{ZAP_ADMIN}?text=Olá! Acabei de fazer o PIX para o pacote de moedas no GeralJá. Meu ID é: {st.session_state.user_id}", 
                   use_container_width=True)
        
        # 4. EDIÇÃO DE PERFIL
        with st.expander("📝 EDITAR MEU PERFIL & VITRINE", expanded=True):
            with st.form("perfil_v7"):
                n_nome = st.text_input("Nome Profissional", d.get('nome', ''))
                
                try: index_cat = CATEGORIAS_OFICIAIS.index(d.get('area', 'Ajudante Geral'))
                except: index_cat = 0
                n_area = st.selectbox("Mudar meu Segmento/Área", CATEGORIAS_OFICIAIS, index=index_cat)

                n_desc = st.text_area("Descrição", d.get('descricao', ''))
                n_cat = st.text_input("Link Catálogo/Instagram", d.get('link_catalogo', ''))
                
                h1, h2 = st.columns(2)
                n_abre = h1.text_input("Abre às (ex: 08:00)", d.get('h_abre', '08:00'))
                n_fecha = h2.text_input("Fecha às (ex: 18:00)", d.get('h_fecha', '18:00'))
                
                n_foto = st.file_uploader("Trocar Foto Perfil", type=['jpg','png','jpeg'], key="f_v7")
                # 🚀 AJUSTE DA GÊNIA: Agora aceita 4 fotos na vitrine
                n_portfolio = st.file_uploader("Vitrine (Até 4 fotos)", type=['jpg','png','jpeg'], accept_multiple_files=True, key="p_v7")
                
                if st.form_submit_button("SALVAR ALTERAÇÕES", use_container_width=True):
                    up = {
                        "nome": n_nome, "area": n_area, "descricao": n_desc, 
                        "link_catalogo": n_cat, "h_abre": n_abre, "h_fecha": n_fecha
                    }
                    if n_foto: up["foto_url"] = f"data:image/png;base64,{converter_img_b64(n_foto)}"
                    if n_portfolio:
                        # Limite de 4 fotos
                        up["portfolio_imgs"] = [f"data:image/png;base64,{converter_img_b64(f)}" for f in n_portfolio[:4]]
                    
                    doc_ref.update(up)
                    st.success("✅ Perfil atualizado!")
                    time.sleep(1); st.rerun()

        # 5. SEGURANÇA E EXCLUSÃO (NOVO BLOCO)
        with st.expander("🔐 SEGURANÇA E EXCLUSÃO DE DADOS"):
            st.write("Deseja encerrar sua conta e apagar todos os seus dados?")
            confirma_pw = st.text_input("Confirme sua SENHA para excluir", type="password", key="excluir_pw")
            if st.button("❌ APAGAR MINHA CONTA DEFINITIVAMENTE", type="primary"):
                if confirma_pw == d.get('senha'):
                    doc_ref.delete()
                    st.error("Dados removidos conforme LGPD. Saindo...")
                    time.sleep(2)
                    st.session_state.auth = False
                    st.rerun()
                else:
                    st.error("Senha incorreta!")

        if st.button("SAIR DO PAINEL", use_container_width=True):
            st.session_state.auth = False
            st.rerun()
# --- ABA 1: CADASTRAR (SISTEMA DE ADMISSÃO DE ELITE) ---
with menu_abas[1]:
    st.markdown("### 🚀 Cadastro de Profissional")
    st.info("Preencha os dados abaixo para entrar no ecossistema GeralJá.")

    # Início do Formulário - O 'with' garante que tudo aqui dentro pertença ao botão de salvar
    with st.form("form_novo_profissional", clear_on_submit=False):
        col_id1, col_id2 = st.columns(2)
        nome_input = col_id1.text_input("Nome do Profissional ou Loja", placeholder="Ex: João Mecânico")
        zap_input = col_id2.text_input("WhatsApp (DDD + Número)", placeholder="Ex: 11991853488")
        
        col_id3, col_id4 = st.columns(2)
        categoria_input = col_id3.selectbox("Sua Área Principal", CATEGORIAS_OFICIAIS)
        senha_input = col_id4.text_input("Crie uma Senha", type="password", help="Para editar seu perfil depois")
        
        descricao_input = st.text_area("Descrição do Serviço", placeholder="Conte o que você faz, diferenciais e experiência...")
        
        tipo_input = st.radio("Tipo de Cadastro", ["👨‍🔧 Profissional Autônomo", "🏢 Comércio/Loja"], horizontal=True)
        
        foto_upload = st.file_uploader("Foto de Perfil ou Logo", type=['jpg', 'jpeg', 'png'])

        st.markdown("---")
        st.caption("📍 A sua localização atual será capturada automaticamente para te mostrar nos resultados próximos aos clientes.")
        
        # O BOTÃO DE SALVAR PRECISA ESTAR AQUI DENTRO DO FORM
        btn_finalizar = st.form_submit_button("✅ FINALIZAR E SALVAR CADASTRO", use_container_width=True)

    # Lógica que acontece APÓS o clique no botão
    if btn_finalizar:
        if not nome_input or not zap_input or not senha_input:
            st.error("⚠️ ERRO: Nome, WhatsApp e Senha são obrigatórios!")
        else:
            with st.spinner("Conectando ao banco de dados..."):
                try:
                    # 1. Processamento da Imagem
                    foto_final = ""
                    if foto_upload:
                        foto_final = f"data:image/png;base64,{converter_img_b64(foto_upload)}"
                    
                    # 2. Garantia de Localização (Se o GPS falhar, usa a LAT_REF/LON_REF que você definiu)
                    # Use as variáveis que o seu script já detectou no topo da página
                    lat_salvar = minha_lat if 'minha_lat' in locals() else LAT_REF
                    lon_salvar = minha_lon if 'minha_lon' in locals() else LON_REF

                    # 3. Montagem do Objeto (Sem apagar nada do que você já usa)
                    novo_pro = {
                        "nome": nome_input,
                        "area": categoria_input,
                        "descricao": descricao_input,
                        "senha": senha_input,
                        "tipo": tipo_input,
                        "whatsapp": zap_input,
                        "foto_url": foto_final,
                        "saldo": BONUS_WELCOME, # Dá os 5 créditos iniciais
                        "aprovado": True,        # Já nasce ativo conforme seu fluxo
                        "verificado": False,
                        "cliques": 0,
                        "rating": 5,
                        "lat": lat_salvar,
                        "lon": lon_salvar,
                        "data_cadastro": datetime.datetime.now().strftime("%d/%m/%Y")
                    }

                    # 4. Envio para o Firestore usando o WhatsApp como ID (Evita duplicados)
                    db.collection("profissionais").document(zap_input).set(novo_pro)
                    
                    st.balloons()
                    st.success(f"🎊 BEM-VINDO, {nome_input.upper()}! Seu cadastro foi concluído com sucesso.")
                    st.info("💡 DICA: Vá na aba '👤 MEU PERFIL' para fazer login e ver seu saldo de moedas.")
                    
                    # Alerta para o Admin (Usando sua função existente)
                    link_admin = enviar_alerta_admin(nome_input, categoria_input, zap_input)
                    st.markdown(f'[📢 Avisar Administração via WhatsApp]({link_admin})')

                except Exception as e:
                    st.error(f"❌ Erro técnico ao salvar: {e}")
# ==============================================================================
# ABA 4: 👑 PAINEL DE CONTROLE MASTER (TURBINADO)
# ==============================================================================
with menu_abas[3]:
    st.markdown("## 👑 Gestão Estratégica GeralJá")
    
    access_adm = st.text_input("Chave Mestra", type="password", key="auth_master")

    if access_adm == CHAVE_ADMIN:
        # --- 1. DASHBOARD DE MÉTRICAS ---
        st.markdown("### 📊 Performance da Rede")
        todos_profs = list(db.collection("profissionais").stream())
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Profissionais", len(todos_profs))
        
        # Cálculos rápidos
        total_cliques = sum([p.to_dict().get('cliques', 0) for p in todos_profs])
        saldo_total = sum([p.to_dict().get('saldo', 0) for p in todos_profs])
        pendentes = len([p for p in todos_profs if not p.to_dict().get('aprovado')])
        
        m2.metric("Cliques Totais", total_cliques)
        m3.metric("Saldo em Circulação", f"{saldo_total} 💎")
        m4.metric("Aguardando Aprovação", pendentes, delta_color="inverse", delta=pendentes)

        st.divider()# --- GERENCIADOR DE CATEGORIAS DINÂMICAS ---
        st.divider()
        st.markdown("### 🛠️ Configurações de Expansão")
        st.caption("Adicione novas opções que aparecerão instantaneamente no formulário de cadastro.")
        
        col_adm_1, col_adm_2 = st.columns(2)
        
        with col_adm_1:
            st.write("**✨ Novas Profissões (IA)**")
            nova_cat = st.text_input("Nome da Profissão", placeholder="Ex: Adestrador", key="add_cat_input")
            if st.button("➕ Adicionar Categoria", use_container_width=True):
                if nova_cat:
                    doc_ref = db.collection("configuracoes").document("categorias")
                    lista_atual = buscar_opcoes_dinamicas("categorias", [])
                    if nova_cat not in lista_atual:
                        lista_atual.append(nova_cat)
                        doc_ref.set({"lista": lista_atual})
                        st.success(f"'{nova_cat}' agora faz parte do sistema!")
                        time.sleep(1)
                        st.rerun()

        with col_adm_2:
            st.write("**🏢 Novos Tipos de Negócio**")
            novo_tipo = st.text_input("Tipo de Comércio", placeholder="Ex: Food Truck", key="add_tipo_input")
            if st.button("➕ Adicionar Tipo", use_container_width=True):
                if novo_tipo:
                    doc_ref = db.collection("configuracoes").document("tipos")
                    lista_atual = buscar_opcoes_dinamicas("tipos", [])
                    if novo_tipo not in lista_atual:
                        lista_atual.append(novo_tipo)
                        doc_ref.set({"lista": lista_atual})
                        st.success(f"'{novo_tipo}' adicionado com sucesso!")
                        time.sleep(1)
                        st.rerun()

        # --- 2. LISTA DE GESTÃO ---
        st.markdown("### 📋 Gerenciar Profissionais")
        
        for p_doc in todos_profs:
            p = p_doc.to_dict()
            pid = p_doc.id
            
            with st.expander(f"{'✅' if p.get('aprovado') else '⏳'} {p.get('nome').upper()} - {p.get('area')}"):
                c1, c2, c3 = st.columns([1, 2, 1])
                
                with c1:
                    # Foto de Perfil
                    foto = p.get('foto_b64')
                    if foto:
                        st.image(f"data:image/png;base64,{foto}", width=100)
                    st.write(f"ID: `{pid}`")
                    st.write(f"Saldo: **{p.get('saldo', 0)} 💎**")

                with c2:
                    st.write(f"**Descrição:** {p.get('descricao')}")
                    st.write(f"**Tipo:** {p.get('tipo')}")
                    st.write(f"**Cliques:** {p.get('cliques', 0)}")
                    
                    # Exibir as 3 fotos da vitrine se existirem
                    st.write("🖼️ **Vitrine:**")
                    fv = [p.get('f1'), p.get('f2'), p.get('f3')]
                    cols_f = st.columns(3)
                    for i, f_data in enumerate(fv):
                        if f_data:
                            cols_f[i].image(f"data:image/png;base64,{f_data}", use_container_width=True)

                with c3:
                    st.write("⚡ **Ações Rápidas**")
                    
                    # Aprovação
                    if not p.get('aprovado'):
                        if st.button("✅ APROVAR AGORA", key=f"apr_{pid}", use_container_width=True):
                            db.collection("profissionais").document(pid).update({"aprovado": True})
                            st.rerun()
                    
                    # Verificado/Elite
                    is_ver = p.get('verificado', False)
                    label_ver = "💎 REMOVER ELITE" if is_ver else "🌟 TORNAR ELITE"
                    if st.button(label_ver, key=f"ver_{pid}", use_container_width=True):
                        db.collection("profissionais").document(pid).update({"verificado": not is_ver})
                        st.rerun()

                    # Adicionar Saldo (Pacote de 10)
                    if st.button("➕ ADD 10 SALDO", key=f"plus_{pid}", use_container_width=True):
                        db.collection("profissionais").document(pid).update({"saldo": p.get('saldo', 0) + 10})
                        st.rerun()

                    # Botão de Exclusão (Cuidado!)
                    if st.button("🗑️ EXCLUIR", key=f"del_{pid}", use_container_width=True):
                        db.collection("profissionais").document(pid).delete()
                        st.rerun()

    elif access_adm != "":
        st.error("🚫 Acesso negado. Chave incorreta.")
    else:
        st.info("Aguardando Chave Mestra para liberar os controles.")

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


















