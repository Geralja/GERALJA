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

# --- GERENCIADOR DE TEMA (MODO NOITE LUXO) ---
if 'modo_noite' not in st.session_state:
    st.session_state.modo_noite = False

# Botão discreto no topo
col_theme, _ = st.columns([1, 10])
with col_theme:
    st.session_state.modo_noite = st.toggle("🌙 Modo Noite", value=st.session_state.modo_noite)

if st.session_state.modo_noite:
    st.markdown("""
        <style>
            /* Fundo Total Escuro */
            .stApp, .stAppViewContainer, .stMain {
                background-color: #0E1117 !important;
            }
            
            /* Textos em Branco */
            h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, .stCaption {
                color: #FFFFFF !important;
            }

            /* Cartões e Inputs Escuros com Borda Fina */
            .stTextInput input, .stSelectbox div, .stTextArea textarea, .stNumberInput input {
                background-color: #1A1C23 !important;
                color: #FFFFFF !important;
                border: 1px solid #30363D !important;
            }

            /* Abas (Tabs) */
            button[data-baseweb="tab"] p {
                color: #FFFFFF !important;
            }
            
            /* Ajuste para os cards brancos da vitrine não "gritarem" no fundo preto */
            div[style*="background: white"], div[style*="background: #FFFFFF"] {
                background-color: #161B22 !important;
                border: 1px solid #30363D !important;
            }
        </style>
    """, unsafe_allow_html=True)

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
# --- ABA 1: BUSCA (SISTEMA GPS + RANKING ELITE + VITRINE) ---
# ==============================================================================
with menu_abas[0]:
    st.markdown("### 🏙️ O que você precisa?")
    
    # --- MOTOR DE LOCALIZAÇÃO EM TEMPO REAL ---
    with st.expander("📍 Sua Localização (GPS)", expanded=False):
        loc = get_geolocation()
        if loc:
            minha_lat = loc['coords']['latitude']
            minha_lon = loc['coords']['longitude']
            st.success(f"Localização detectada!")
        else:
            minha_lat = LAT_REF
            minha_lon = LON_REF
            st.warning("GPS desativado. Usando localização padrão (SP).")

    c1, c2 = st.columns([3, 1])
    termo_busca = c1.text_input("Ex: 'Cano estourado' ou 'Pizza'", key="main_search")
    raio_km = c2.select_slider("Raio (KM)", options=[1, 3, 5, 10, 20, 50, 100, 500, 2000], value=10)
    
    if termo_busca:
        # Processamento via IA para identificar a categoria
        cat_ia = processar_ia_avancada(termo_busca)
        st.info(f"✨ IA: Buscando por **{cat_ia}** próximo a você")
        
        # Lógica de Horário em tempo real
        from datetime import datetime
        import pytz
        import re
        from urllib.parse import quote
        
        fuso = pytz.timezone('America/Sao_Paulo')
        hora_atual = datetime.now(fuso).strftime('%H:%M')

        # Busca no Firebase (Filtra apenas aprovados e da categoria certa)
        profs = db.collection("profissionais").where("area", "==", cat_ia).where("aprovado", "==", True).stream()
        
        lista_ranking = []
        for p_doc in profs:
            p = p_doc.to_dict()
            p['id'] = p_doc.id
            
            # CALCULA DISTÂNCIA REAL (GPS vs Profissional)
            dist = calcular_distancia_real(minha_lat, minha_lon, p.get('lat', LAT_REF), p.get('lon', LON_REF))
            
            if dist <= raio_km:
                p['dist'] = dist
                # MOTOR DE SCORE ELITE (Ranking)
                score = 0
                score += 500 if p.get('verificado', False) else 0
                score += (p.get('saldo', 0) * 10)
                score += (p.get('rating', 5) * 20)
                p['score_elite'] = score
                lista_ranking.append(p)

        # Ordenação: Elite primeiro (maior score), depois os mais próximos (menor distância)
        lista_ranking.sort(key=lambda x: (-x['score_elite'], x['dist']))

        if not lista_ranking:
            st.markdown(f"""
            <div style="background-color: #FFF4E5; padding: 20px; border-radius: 15px; border-left: 5px solid #FF8C00;">
                <h3 style="color: #856404;">🔍 Essa profissão ainda não foi preenchida nesta região.</h3>
                <p style="color: #856404;">Compartilhe o <b>GeralJá</b> e ajude a crescer sua rede local!</p>
            </div>
            """, unsafe_allow_html=True)
            
            link_share = "https://wa.me/?text=Ei!%20Procurei%20um%20serviço%20no%20GeralJá%20e%20vi%20que%20ainda%20temos%20vagas!%20Cadastre-se:%20https://geralja.streamlit.app"
            st.markdown(f'<a href="{link_share}" target="_blank" style="text-decoration:none;"><div style="background:#22C55E; color:white; padding:15px; border-radius:10px; text-align:center; font-weight:bold; margin-top:10px;">📲 COMPARTILHAR NO WHATSAPP</div></a>', unsafe_allow_html=True)
        
        else:
            # --- RENDERIZAÇÃO DOS CARDS (LOOP) ---
            for p in lista_ranking:
                pid = p['id']
                is_elite = p.get('verificado') and p.get('saldo', 0) > 0
                
                with st.container():
                    # Cores dinâmicas baseadas no tipo de conta
                    cor_borda = "#FFD700" if is_elite else ("#FF8C00" if p.get('tipo') == "🏢 Comércio/Loja" else "#0047AB")
                    bg_card = "#FFFDF5" if is_elite else "#FFFFFF"
                    
                    st.markdown(f"""
                    <div style="border-left: 8px solid {cor_borda}; padding: 15px; background: {bg_card}; border-radius: 15px; margin-bottom: 5px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                        <span style="font-size: 12px; color: gray; font-weight: bold;">📍 a {p['dist']:.1f} km de você {" | 🏆 DESTAQUE" if is_elite else ""}</span>
                    </div>
                    """, unsafe_allow_html=True)

                    col_img, col_txt = st.columns([1, 4])
                    with col_img:
                        foto = p.get('foto_url', 'https://via.placeholder.com/150')
                        st.markdown(f'<img src="{foto}" style="width:75px; height:75px; border-radius:50%; object-fit:cover; border:3px solid {cor_borda}">', unsafe_allow_html=True)
                    
                    with col_txt:
                        nome_exibicao = p.get('nome', '').upper()
                        if p.get('verificado', False): nome_exibicao += " <span style='color:#1DA1F2;'>☑️</span>"
                        
                        status_loja = ""
                        if p.get('tipo') == "🏢 Comércio/Loja":
                            h_ab, h_fe = p.get('h_abre', '08:00'), p.get('h_fecha', '18:00')
                            status_loja = " 🟢 <b style='color:green;'>ABERTO</b>" if h_ab <= hora_atual <= h_fe else " 🔴 <b style='color:red;'>FECHADO</b>"
                        
                        st.markdown(f"**{nome_exibicao}** {status_loja}", unsafe_allow_html=True)
                        st.caption(f"{p.get('descricao', '')[:120]}...")

                    # Vitrine de Fotos do Portfólio
                    if p.get('portfolio_imgs'):
                        cols_v = st.columns(3)
                        for i, img_b64 in enumerate(p.get('portfolio_imgs')[:3]):
                            cols_v[i].image(img_b64, use_container_width=True)

                    # --- LÓGICA DO BOTÃO DE WHATSAPP (AQUI DENTRO DO LOOP) ---
                    nome_curto = p.get('nome', 'Profissional').split()[0].upper()
                    
                    # Limpeza do número de telefone (ID do documento)
                    numero_limpo = re.sub(r'\D', '', str(pid))
                    if not numero_limpo.startswith('55'):
                        numero_limpo = f"55{numero_limpo}"
                    
                    texto_zap = quote(f"Olá {p.get('nome')}, vi seu perfil no GeralJá!")
                    link_final = f"https://wa.me/{numero_limpo}?text={texto_zap}"

                    # --- BOTÃO ÚNICO (VISUAL TOP + ABRE SEMPRE) ---
                    import re
                    from urllib.parse import quote
                    
                    # 1. Preparação dos dados
                    num_limpo = re.sub(r'\D', '', str(pid))
                    if not num_limpo.startswith('55'): num_limpo = f"55{num_limpo}"
                    texto_zap = quote(f"Olá {p.get('nome')}, vi seu perfil no GeralJá!")
                    link_final = f"https://wa.me/{num_limpo}?text={texto_zap}"
                    nome_btn = p.get('nome', 'Profissional').split()[0].upper()
                    
                    # 2. BOTÃO HTML (Ocupa o lugar do st.button)
                    # Este botão abre o WhatsApp instantaneamente e não é bloqueado
                    st.markdown(f"""
                        <a href="{link_final}" target="_blank" style="text-decoration: none;">
                            <div style="
                                background-color: #25D366;
                                color: white;
                                padding: 15px;
                                border-radius: 12px;
                                text-align: center;
                                font-weight: bold;
                                font-size: 18px;
                                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                                transition: 0.3s;
                                cursor: pointer;
                                margin-top: 10px;
                            ">
                                💬 FALAR COM {nome_btn}
                            </div>
                        </a>
                    """, unsafe_allow_html=True)
                    
                    # 3. LÓGICA DE DÉBITO E SEGURANÇA
                # Verifica se tem saldo antes de processar
                if p.get('saldo', 0) <= 0:
                    continue  # <--- AGORA ESTÁ DENTRO DO IF (4 espaços)

                # Se passou pelo if acima, registra o clique/visualização
                db.collection("profissionais").document(pid).update({
                    "cliques": p.get('cliques', 0) + 1
                })
                
# ==============================================================================
# ABA 2: 📝 CADASTRO TURBINADO E BLINDADO
# ==============================================================================
with menu_abas[1]:
    st.header("🚀 Seja um Parceiro GeralJá")
    st.write("Cadastre seu serviço e seja encontrado por clientes próximos!")
    
    # Função interna para usar a chave que você salvou nos Secrets
    def obter_coords_google(endereco):
        api_key = st.secrets["GOOGLE_MAPS_API_KEY"]
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={endereco}&key={api_key}"
        try:
            response = requests.get(url).json()
            if response['status'] == 'OK':
                loc = response['results'][0]['geometry']['location']
                end_formatado = response['results'][0]['formatted_address']
                return loc['lat'], loc['lng'], end_formatado
        except:
            pass
        return None, None, None

    with st.form("reg_preciso"):
        col_c1, col_c2 = st.columns(2)
        r_n = col_c1.text_input("Nome Completo")
        r_z = col_c2.text_input("WhatsApp (Apenas números)", help="Ex: 11999999999")
        
        # CAMPO CRUCIAL: O endereço que o Google vai ler
        r_endereco = st.text_input("Endereço de Atendimento", placeholder="Rua, Número, Bairro, Cidade - Estado")
        
        col_c3, col_c4 = st.columns(2)
        r_s = col_c3.text_input("Crie uma Senha", type="password")
        r_a = col_c4.selectbox("Sua Especialidade Principal", CATEGORIAS_OFICIAIS)
        
        r_d = st.text_area("Descreva seus serviços")
        
        st.info("📌 Sua localização será usada para mostrar seus serviços aos clientes mais próximos.")
        
        if st.form_submit_button("FINALIZAR MEU CADASTRO", use_container_width=True):
            if len(r_z) < 10 or not r_endereco:
                st.error("⚠️ Nome, WhatsApp e Endereço são obrigatórios!")
            else:
                # MÁGICA DO GOOGLE ACONTECENDO AQUI
                lat, lon, endereco_real = obter_coords_google(r_endereco)
                
                if lat and lon:
                    try:
                        db.collection("profissionais").document(r_z).set({
                            "nome": r_n,
                            "whatsapp": r_z,
                            "senha": r_s,
                            "area": r_a,
                            "descricao": r_d,
                            "endereco_digitado": r_endereco,
                            "endereco_oficial": endereco_real, # Endereço corrigido pelo Google
                            "lat": lat,
                            "lon": lon,
                            "saldo": BONUS_WELCOME,
                            "cliques": 0,
                            "rating": 5.0,
                            "aprovado": False,
                            "data_registro": datetime.datetime.now()
                        })
                        st.success(f"✅ Cadastro enviado! Localizamos você em: {endereco_real}")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Erro ao salvar no banco: {e}")
                else:
                    st.error("❌ Não conseguimos validar este endereço no mapa. Tente incluir o número da casa e a cidade.")

# ==============================================================================
# ABA 3: MEU PERFIL (VITRINE LUXUOSA ESTILO INSTA)
# ==============================================================================
with menu_abas[2]:
    if 'auth' not in st.session_state: st.session_state.auth = False
    
    if not st.session_state.auth:
        st.markdown("<h2 style='text-align:center;'>🔐 Portal do Parceiro</h2>", unsafe_allow_html=True)
        with st.container():
            l_zap = st.text_input("WhatsApp (ID)", key="login_zap")
            l_pw = st.text_input("Senha", type="password", key="login_pw")
            if st.button("ENTRAR NA MINHA VITRINE", use_container_width=True):
                if l_zap:
                    doc_ref = db.collection("profissionais").document(l_zap)
                    doc = doc_ref.get()
                    if doc.exists and doc.to_dict().get('senha') == l_pw:
                        st.session_state.auth = True
                        st.session_state.user_id = l_zap
                        st.rerun()
                    else:
                        st.error("❌ Credenciais inválidas.")
    else:
        uid = st.session_state.user_id
        doc_ref = db.collection("profissionais").document(uid)
        d = doc_ref.get().to_dict()
        
        # --- HEADER ESTILO INSTAGRAM ---
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 20px; padding: 20px; background: white; border-radius: 20px; border: 1px solid #E2E8F0; margin-bottom: 20px;">
                <div style="position: relative;">
                    <img src="data:image/png;base64,{d.get('foto_b64', '')}" 
                         style="width: 100px; height: 100px; border-radius: 50%; object-fit: cover; border: 3px solid #E1306C;"
                         onerror="this.src='https://ui-avatars.com/api/?name={d.get('nome')}&background=random'">
                    <div style="position: absolute; bottom: 5px; right: 5px; background: #22C55E; width: 15px; height: 15px; border-radius: 50%; border: 2px solid white;"></div>
                </div>
                <div style="flex-grow: 1;">
                    <h2 style="margin: 0; font-size: 22px;">{d.get('nome')}</h2>
                    <p style="margin: 0; color: #64748B; font-size: 14px;">@{d.get('area').lower().replace(' ', '')}</p>
                    <div style="display: flex; gap: 15px; margin-top: 10px;">
                        <div style="text-align: center;"><b style="display: block;">{d.get('cliques', 0)}</b><small style="color: #64748B;">Cliques</small></div>
                        <div style="text-align: center;"><b style="display: block;">⭐ {d.get('rating', 5.0)}</b><small style="color: #64748B;">Nota</small></div>
                        <div style="text-align: center;"><b style="display: block;">{d.get('saldo', 0)}</b><small style="color: #64748B;">Moedas</small></div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # --- DASHBOARD DE PERFORMANCE (LUXUOSA) ---
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Visibilidade", f"{d.get('cliques', 0)} rkt", "Aumento de 12%")
        col_m2.metric("Saldo Atual", f"{d.get('saldo', 0)} 🪙")
        col_m3.metric("Status Perfil", "Elite" if d.get('elite') else "Padrão")

        # --- LOJA DE DESTAQUES (GRID VISUAL) ---
        st.markdown("### 💎 Impulsione sua Vitrine")
        with st.container():
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("<div style='background: linear-gradient(135deg, #FFD700, #FFA500); padding: 15px; border-radius: 15px; color: white; text-align: center;'><b>BRONZE</b><br>10 🪙<br>R$ 25</div>", unsafe_allow_html=True)
                if st.button("Comprar 10", key="buy_10", use_container_width=True):
                     st.markdown(f'<meta http-equiv="refresh" content="0;URL=https://wa.me/{ZAP_ADMIN}?text=Quero 10 moedas para ID: {uid}">', unsafe_allow_html=True)
            with c2:
                st.markdown("<div style='background: linear-gradient(135deg, #C0C0C0, #808080); padding: 15px; border-radius: 15px; color: white; text-align: center;'><b>PRATA</b><br>30 🪙<br>R$ 60</div>", unsafe_allow_html=True)
                if st.button("Comprar 30", key="buy_30", use_container_width=True):
                     st.markdown(f'<meta http-equiv="refresh" content="0;URL=https://wa.me/{ZAP_ADMIN}?text=Quero 30 moedas para ID: {uid}">', unsafe_allow_html=True)
            with c3:
                st.markdown("<div style='background: linear-gradient(135deg, #FFD700, #D4AF37); padding: 15px; border-radius: 15px; color: white; text-align: center;'><b>OURO</b><br>100 🪙<br>R$ 150</div>", unsafe_allow_html=True)
                if st.button("Comprar 100", key="buy_100", use_container_width=True):
                     st.markdown(f'<meta http-equiv="refresh" content="0;URL=https://wa.me/{ZAP_ADMIN}?text=Quero 100 moedas para ID: {uid}">', unsafe_allow_html=True)

        st.divider()

        # --- EDIÇÃO DE DADOS (TURBINADA) ---
        with st.expander("⚙️ CONFIGURAÇÕES DA VITRINE", expanded=False):
            with st.form("edit_v2"):
                st.markdown("#### ✨ Informações Públicas")
                new_foto = st.file_uploader("Trocar Foto de Perfil", type=["jpg", "png", "jpeg"])
                n_nome = st.text_input("Nome da Vitrine", value=d.get('nome'))
                n_desc = st.text_area("Bio (O que você faz de melhor?)", value=d.get('descricao'))
                
                col_e1, col_e2 = st.columns(2)
                n_area = col_e1.selectbox("Categoria", CATEGORIAS_OFICIAIS, index=CATEGORIAS_OFICIAIS.index(d.get('area', 'Ajudante Geral')))
                n_tipo = col_e2.radio("Tipo", ["👤 Profissional", "🏢 Comércio/Loja"], index=0 if d.get('tipo') == "👤 Profissional" else 1, horizontal=True)

                if st.form_submit_button("💾 ATUALIZAR MINHA VITRINE", use_container_width=True):
                    up = {
                        "nome": n_nome, "area": n_area, "descricao": n_desc, "tipo": n_tipo
                    }
                    if new_foto:
                        up["foto_b64"] = converter_img_b64(new_foto)
                    
                    doc_ref.update(up)
                    st.success("Vitrine atualizada! 🚀")
                    time.sleep(1)
                    st.rerun()

        if st.button("LOGOUT", type="secondary"):
            st.session_state.auth = False
            st.rerun()
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















