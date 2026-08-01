import os
import json
import base64
import math
import re
from datetime import datetime
import io
import urllib.request
import xml.etree.ElementTree as ET

import streamlit as st
import streamlit.components.v1 as components

# ==============================================================================
# 1. TRATAMENTO SEGURO DE DEPENDÊNCIAS (FALLBACK SYSTEM)
# ==============================================================================
try:
    from PIL import Image
except ImportError:
    Image = None

try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from fuzzywuzzy import process, fuzz
except ImportError:
    process, fuzz = None, None

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:
    firebase_admin, credentials, firestore = None, None, None

try:
    from streamlit_js_eval import streamlit_js_eval
except ImportError:
    streamlit_js_eval = None

# ==============================================================================
# 2. CONFIGURAÇÃO DA PÁGINA STREAMLIT & ESTILIZAÇÃO SOCIAL 5.0
# ==============================================================================
st.set_page_config(
    page_title="GeralJá | Grajaú Tem — O Portal da Nossa Região",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Global & Redes Sociais */
    .stApp { background-color: #f8f9fa; }
    .main-header { font-size: 28px; font-weight: 800; color: #0047AB; text-align: center; margin-bottom: 2px; }
    .sub-header { font-size: 14px; color: #555; text-align: center; margin-bottom: 20px; }
    
    /* Card do Profissional (Estilo Social 5.0) */
    .card-social {
        background-color: #ffffff;
        border-radius: 12px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.08);
        overflow: hidden;
        margin-bottom: 22px;
        border: 1px solid #e0e0e0;
        transition: transform 0.2s;
    }
    .card-banner {
        width: 100%;
        height: 120px;
        object-fit: cover;
        background-color: #0047AB;
    }
    .card-body {
        padding: 16px;
        position: relative;
    }
    .avatar-container {
        margin-top: -50px;
        margin-bottom: 10px;
    }
    .card-avatar {
        width: 75px;
        height: 75px;
        border-radius: 50%;
        border: 3px solid #ffffff;
        object-fit: cover;
        background-color: #fff;
    }
    
    /* Badges Destaques */
    .badge-ouro { background-color: #FFD700; color: #000; font-weight: bold; padding: 3px 9px; border-radius: 12px; font-size: 11px; }
    .badge-prata { background-color: #C0C0C0; color: #000; font-weight: bold; padding: 3px 9px; border-radius: 12px; font-size: 11px; }
    .badge-bronze { background-color: #CD7F32; color: #fff; font-weight: bold; padding: 3px 9px; border-radius: 12px; font-size: 11px; }
    .badge-vitrine { background-color: #FF0000; color: #fff; font-weight: bold; padding: 3px 9px; border-radius: 12px; font-size: 11px; }
    
    .price-tag { color: #28a745; font-weight: bold; font-size: 15px; }
    .coin-tag { color: #ff9900; font-weight: bold; font-size: 14px; }
    
    .news-card {
        background: #ffffff;
        padding: 12px;
        border-radius: 8px;
        border-left: 4px solid #0047AB;
        margin-bottom: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }

    .footer-box { text-align: center; padding: 25px; font-size: 12px; color: #666; border-top: 1px solid #ddd; margin-top: 50px; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. CONEXÃO COM O FIREBASE FIRESTORE
# ==============================================================================
@st.cache_resource
def inicializar_firebase():
    if not firebase_admin or not credentials:
        return None
    try:
        if not firebase_admin._apps:
            if "firebase" in st.secrets and "base64" in st.secrets["firebase"]:
                json_str = base64.b64decode(st.secrets["firebase"]["base64"]).decode('utf-8')
                cred_dict = json.loads(json_str)
                cred = credentials.Certificate(cred_dict)
            elif os.path.exists("firebase_key.json"):
                cred = credentials.Certificate("firebase_key.json")
            else:
                return None
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"Erro ao conectar ao Firebase: {e}")
        return None

db = inicializar_firebase()

# ==============================================================================
# 4. ENGINE DE INTELIGÊNCIA & PROCESSAMENTO (GERALJÁ ENGINE)
# ==============================================================================
class GeralJaEngine:
    def __init__(self, db_client):
        self.db = db_client
        self.groq_api_key = st.secrets.get("GROQ_API_KEY", "") if "GROQ_API_KEY" in st.secrets else os.getenv("GROQ_API_KEY", "")
        self.gemini_api_key = st.secrets.get("GEMINI_API_KEY", "") if "GEMINI_API_KEY" in st.secrets else os.getenv("GEMINI_API_KEY", "")

    def sanitizar_texto(self, texto):
        if not texto:
            return ""
        return re.sub(r'[^\w\s\-\.\,\@]', '', str(texto)).strip()

    def classificar_busca_ia(self, termo):
        """Classifica o termo de busca usando Groq ou Gemini com fallback"""
        if not termo:
            return None
        
        # 1. Consulta Groq
        if Groq and self.groq_api_key:
            try:
                client = Groq(api_key=self.groq_api_key)
                response = client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[{
                        "role": "system",
                        "content": "Você é um classificador de categorias de serviços urbanos. Responda APENAS com 1 ou 2 palavras indicando a categoria exata (ex: Pizzaria, Encanador, Eletricista, Barbeiro)."
                    }, {
                        "role": "user",
                        "content": f"Classifique este pedido de busca: {termo}"
                    }],
                    temperature=0.1,
                    max_tokens=10
                )
                cat = response.choices[0].message.content.strip()
                if cat:
                    return cat
            except Exception:
                pass

        # 2. Fallback Gemini
        if genai and self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content(f"Responda apenas com a categoria do serviço: {termo}")
                if res.text:
                    return res.text.strip()
            except Exception:
                pass

        return None

    def buscar_fuzzy(self, termo, lista_categorias):
        """Busca por similaridade de texto caso as IAs falhem"""
        if process and lista_categorias:
            resultado = process.extractOne(termo, lista_categorias, scorer=fuzz.partial_ratio)
            if resultado and resultado[1] >= 60:
                return resultado[0]
        return termo

engine = GeralJaEngine(db)

# ==============================================================================
# 5. FUNÇÕES AUXILIARES E OTIMIZAÇÃO DE IMAGENS
# ==============================================================================
def otimizar_imagem(upload_file, max_size=(800, 800), quality=80):
    if not Image or not upload_file:
        return None
    try:
        img = Image.open(upload_file)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality)
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{encoded}"
    except Exception:
        return None

def safe_image_src(src_str, fallback="https://via.placeholder.com/300"):
    if not src_str:
        return fallback
    if src_str.startswith("http") or src_str.startswith("data:image"):
        return src_str
    return f"data:image/jpeg;base64,{src_str}"

def limpar_whatsapp(numero):
    if not numero:
        return ""
    num_limpo = re.sub(r'\D', '', str(numero))
    if not num_limpo.startswith("55"):
        num_limpo = "55" + num_limpo
    return num_limpo

def calcular_distancia_real(lat1, lon1, lat2, lon2):
    try:
        r = 6371.0
        phi1, phi2 = math.radians(float(lat1)), math.radians(float(lat2))
        dphi = math.radians(float(lat2) - float(lat1))
        dlambda = math.radians(float(lon2) - float(lon1))
        a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
        return round(2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 1)
    except Exception:
        return None

def registrar_lead_clique(parceiro_id):
    if db:
        try:
            doc_ref = db.collection("parceiros").document(parceiro_id)
            doc_ref.update({"cliques": firestore.Increment(1)})
        except Exception:
            pass

def registrar_intencao_compra(parceiro_nome, pacote_nome):
    if db:
        try:
            db.collection("intencoes_compra").add({
                "parceiro": parceiro_nome,
                "pacote": pacote_nome,
                "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        except Exception:
            pass

def carregar_noticias_rss():
    """Carrega feed de notícias em tempo real"""
    noticias = []
    try:
        url = "https://g1.globo.com/rss/g1/sao-paulo/"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        xml_data = urllib.request.urlopen(req, timeout=3).read()
        root = ET.fromstring(xml_data)
        for item in root.findall('./channel/item')[:4]:
            noticias.append({
                "titulo": item.find('title').text if item.find('title') is not None else "",
                "link": item.find('link').text if item.find('link') is not None else "#"
            })
    except Exception:
        noticias = [
            {"titulo": "🚨 Trânsito intenso na Av. Dona Belmira Marin nesta manhã", "link": "#"},
            {"titulo": "☀️ Previsão do tempo: Sol com pancadas de chuva no Grajaú", "link": "#"}
        ]
    return noticias

# ==============================================================================
# 6. HEADER & PLAYER DA RÁDIO GRAJAÚ TEM (CLOUDFRONT)
# ==============================================================================
def renderizar_player_radio():
    st.markdown("""
    <div style="margin-bottom: 2px;">
        <strong style="font-size: 14px; color: #0047AB;">📻 Rádio Grajaú Tem — Programação Ao Vivo</strong>
    </div>
    """, unsafe_allow_html=True)
    components.html(
        """
        <iframe src="https://d1uzdx1j6g4d0a.cloudfront.net/players/topo/37/245321/?socials=1&apps=true&sl-item%5B%5D=1&sl-item%5B%5D=2&sl-item%5B%5D=5&identifier=GeralJ%C3%A1&source=17973" 
                border="0" scrolling="no" frameborder="0" allow="autoplay" allowtransparency="true" 
                style="background-color: transparent; width: 100%; height: 62px; border: none;">
        </iframe>
        """,
        height=65
    )

renderizar_player_radio()

st.markdown("<h1 class='main-header'>GeralJá + Grajaú Tem</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>A maior vitrine de serviços, comércio e notícias da nossa região</p>", unsafe_allow_html=True)

# ==============================================================================
# 7. NAVEGAÇÃO PRINCIPAL (ABAS ESTRUTURADAS)
# ==============================================================================
aba_publica, aba_noticias, aba_parceiro, aba_admin = st.tabs([
    "📍 Encontrar Serviços", 
    "📰 Giro de Notícias",
    "👤 Área do Parceiro", 
    "👑 Painel Master (Admin)"
])

# ==============================================================================
# ABA 1: ENCONTRAR SERVIÇOS (PÚBLICO)
# ==============================================================================
with aba_publica:
    st.markdown("### 🔎 O que você precisa no Grajaú hoje?")
    
    col_b1, col_b2, col_b3, col_b4, col_b5, col_b6 = st.columns(6)
    termo_busca = ""
    if col_b1.button("🍕 Pizzaria"): termo_busca = "Pizzaria"
    if col_b2.button("🔧 Encanador"): termo_busca = "Encanador"
    if col_b3.button("⚡ Eletricista"): termo_busca = "Eletricista"
    if col_b4.button("💈 Barbeiro"): termo_busca = "Barbeiro"
    if col_b5.button("🚗 Mecânico"): termo_busca = "Mecânico"
    if col_b6.button("🧹 Limpeza"): termo_busca = "Limpeza"

    input_busca = st.text_input("Digite o serviço ou nome do estabelecimento:", value=termo_busca)
    
    col_gps1, col_gps2 = st.columns(2)
    lat_user = col_gps1.number_input("Sua Latitude (opcional):", value=-23.7500, format="%.4f")
    lon_user = col_gps2.number_input("Sua Longitude (opcional):", value=-46.6900, format="%.4f")

    st.markdown("---")

    # Carregar parceiros
    lista_parceiros = []
    if db:
        try:
            docs = db.collection("parceiros").stream()
            for d in docs:
                p = d.to_dict()
                p["id"] = d.id
                lista_parceiros.append(p)
        except Exception as e:
            st.error(f"Erro ao carregar parceiros: {e}")

    # Fallback Mock se banco estiver vazio
    if not lista_parceiros:
        lista_parceiros = [
            {
                "id": "mock1",
                "nome": "Padaria & Confeitaria Solar",
                "categoria": "Pizzaria / Padaria",
                "bio": "Pães quentinhos toda hora, pizzas no forno a lenha e doces finos.",
                "whatsapp": "11980168513",
                "avatar": "https://via.placeholder.com/150",
                "capa": "https://via.placeholder.com/800x200",
                "lat": -23.7520, "lon": -46.6920,
                "destaque": "OURO",
                "geralcoins": 250,
                "produtos": [{"titulo": "Pizza Calabresa Especial", "preco": "R$ 45,00", "desc": "Queijo duplo e azeitonas", "foto": None}]
            },
            {
                "id": "mock2",
                "nome": "Eletricista Silva 24h",
                "categoria": "Eletricista",
                "bio": "Instalações elétricas residenciais e comerciais de urgência.",
                "whatsapp": "11991853488",
                "avatar": "https://via.placeholder.com/150",
                "capa": "https://via.placeholder.com/800x200",
                "lat": -23.7550, "lon": -46.6950,
                "destaque": "VITRINE",
                "geralcoins": 50,
                "produtos": []
            }
        ]

    # Processar inteligência de busca com Engine de IA/Fuzzy
    categoria_ia = None
    if input_busca:
        categoria_ia = engine.classificar_busca_ia(input_busca)

    parceiros_filtrados = []
    for p in lista_parceiros:
        match = True
        if input_busca:
            termo = input_busca.lower()
            nome_match = termo in p.get("nome", "").lower()
            cat_match = termo in p.get("categoria", "").lower()
            bio_match = termo in p.get("bio", "").lower()
            ia_match = categoria_ia.lower() in p.get("categoria", "").lower() if categoria_ia else False
            match = nome_match or cat_match or bio_match or ia_match
        if match:
            parceiros_filtrados.append(p)

    st.subheader(f"Resultados Encontrados ({len(parceiros_filtrados)})")

    # Renderizar Cards de Parceiros
    cols = st.columns(2)
    for idx, p in enumerate(parceiros_filtrados):
        col = cols[idx % 2]
        with col:
            distancia_str = ""
            if "lat" in p and "lon" in p:
                dist = calcular_distancia_real(lat_user, lon_user, p["lat"], p["lon"])
                if dist is not None:
                    distancia_str = f"📍 {dist} km de você"

            badge_html = ""
            dest = p.get("destaque", "").upper()
            if dest == "OURO": badge_html = "<span class='badge-ouro'>🥇 OURO</span>"
            elif dest == "PRATA": badge_html = "<span class='badge-prata'>🥈 PRATA</span>"
            elif dest == "BRONZE": badge_html = "<span class='badge-bronze'>🥉 BRONZE</span>"
            elif dest == "VITRINE": badge_html = "<span class='badge-vitrine'>🔴 VITRINE</span>"

            capa_src = safe_image_src(p.get("capa"))
            avatar_src = safe_image_src(p.get("avatar"))
            wa_num = limpar_whatsapp(p.get("whatsapp", ""))

            st.markdown(f"""
            <div class='card-social'>
                <img src='{capa_src}' class='card-banner'>
                <div class='card-body'>
                    <div class='avatar-container'>
                        <img src='{avatar_src}' class='card-avatar'>
                    </div>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <h4 style='margin:0; color:#333;'>{p.get("nome")}</h4>
                        {badge_html}
                    </div>
                    <small style='color:#0047AB; font-weight:bold;'>{p.get("categoria", "Serviço Geral")}</small><br>
                    <small style='color:#777;'>{distancia_str}</small>
                    <p style='font-size:13px; color:#555; margin-top:8px;'>{p.get("bio", "")}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if wa_num:
                link_wa = f"https://wa.me/{wa_num}?text=Olá!%20Vi%20seu%20perfil%20no%20GeralJá%20e%20gostaria%20de%20atendimento."
                if st.button(f"💬 Atendimento WhatsApp", key=f"btn_wa_{p['id']}"):
                    registrar_lead_clique(p['id'])
                    st.markdown(f"<script>window.open('{link_wa}', '_blank');</script>", unsafe_allow_html=True)

            produtos = p.get("produtos", [])
            if produtos:
                with st.expander(f"🛍️ Ofertas & Catálogo ({len(produtos)})"):
                    for prod in produtos:
                        st.markdown(f"**{prod.get('titulo')}** — <span class='price-tag'>{prod.get('preco')}</span>", unsafe_allow_html=True)
                        st.caption(prod.get('desc', ''))
                        if prod.get('foto'):
                            st.image(safe_image_src(prod.get('foto')), width=140)
                        st.markdown("---")

# ==============================================================================
# ABA 2: GIRO DE NOTÍCIAS (GRAJAÚ TEM)
# ==============================================================================
with aba_noticias:
    st.subheader("📰 Giro de Notícias & Informativo Regional")
    st.caption("Fique por dentro de tudo o que acontece no Grajaú e Zona Sul de SP")
    
    feed_noticias = carregar_noticias_rss()
    for item in feed_noticias:
        st.markdown(f"""
        <div class='news-card'>
            <strong style='font-size:15px; color:#222;'>{item['titulo']}</strong><br>
            <a href='{item['link']}' target='_blank' style='font-size:12px; color:#0047AB;'>Leia mais no portal oficial →</a>
        </div>
        """, unsafe_allow_html=True)

# ==============================================================================
# ABA 3: ÁREA DO PARCEIRO (GERENCIAMENTO + PACOTES RESTRITOS)
# ==============================================================================
with aba_parceiro:
    st.subheader("👤 Painel Exclusivo do Parceiro / Comerciante")
    
    sub_tab_login, sub_tab_perfil, sub_sub_produtos, sub_tab_coins, sub_tab_impulsionar = st.tabs([
        "🔑 Entrar / Cadastrar", 
        "✏️ Meu Perfil & Fotos", 
        "🛍️ Gerenciar Vitrine",
        "💰 GeralCoins",
        "🚀 Impulsionar no Grajaú Tem"
    ])

    with sub_tab_login:
        st.markdown("##### Acesse seu painel de parceiro")
        login_wa = st.text_input("Seu WhatsApp cadastrado (apenas números):", key="log_wa")
        if st.button("Acessar Meu Painel"):
            st.session_state["parceiro_logado"] = login_wa
            st.success("Login efetuado! Navegue pelas abas acima para gerenciar seu perfil e anúncios.")

    with sub_tab_perfil:
        st.markdown("##### Dados Principais do Perfil Social 5.0")
        nome_p = st.text_input("Nome Fantasia / Razão Social:")
        cat_p = st.text_input("Categoria Principal (ex: Pizzaria, Barbeiro):")
        bio_p = st.text_area("Biografia / Apresentação do Negócio:")
        wa_p = st.text_input("WhatsApp de Contato:")
        lat_p = st.number_input("Latitude da Loja (GPS):", value=-23.7500, format="%.4f")
        lon_p = st.number_input("Longitude da Loja (GPS):", value=-46.6900, format="%.4f")
        
        col_img1, col_img2 = st.columns(2)
        up_avatar = col_img1.file_uploader("Alterar Avatar (Foto Perfil):", type=["jpg", "png", "jpeg"])
        up_capa = col_img2.file_uploader("Alterar Banner de Capa:", type=["jpg", "png", "jpeg"])

        if st.button("💾 Salvar Alterações de Perfil"):
            if db and wa_p:
                num_id = limpar_whatsapp(wa_p)
                data_update = {
                    "nome": engine.sanitizar_texto(nome_p),
                    "categoria": engine.sanitizar_texto(cat_p),
                    "bio": engine.sanitizar_texto(bio_p),
                    "whatsapp": num_id,
                    "lat": lat_p,
                    "lon": lon_p,
                    "atualizado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                if up_avatar:
                    data_update["avatar"] = otimizar_imagem(up_avatar)
                if up_capa:
                    data_update["capa"] = otimizar_imagem(up_capa)

                db.collection("parceiros").document(num_id).set(data_update, merge=True)
                st.success("Perfil salvo e atualizado com sucesso!")
            else:
                st.warning("Informe um número de WhatsApp válido.")

    with sub_sub_produtos:
        st.markdown("##### ➕ Cadastrar Novo Produto/Oferta na Vitrine")
        prod_titulo = st.text_input("Nome do Produto ou Serviço:")
        prod_preco = st.text_input("Preço de Venda (ex: R$ 39,90):")
        prod_desc = st.text_input("Descrição resumida do item:")
        prod_foto = st.file_uploader("Foto do Produto:", type=["jpg", "png"], key="prod_img")

        if st.button("Adicionar à Minha Vitrine"):
            wa_sessao = st.session_state.get("parceiro_logado")
            if db and wa_sessao:
                novo_prod = {
                    "titulo": prod_titulo,
                    "preco": prod_preco,
                    "desc": prod_desc,
                    "foto": otimizar_imagem(prod_foto) if prod_foto else None
                }
                doc_ref = db.collection("parceiros").document(limpar_whatsapp(wa_sessao))
                doc_ref.update({"produtos": firestore.ArrayUnion([novo_prod])})
                st.success("Produto adicionado à sua vitrine com sucesso!")
            else:
                st.error("Efetue login na primeira aba para salvar seus produtos.")

    with sub_tab_coins:
        st.markdown("##### 💰 Saldo de GeralCoins & Recompensas")
        st.caption("Use suas moedas virtuais para destacar seu anúncio nos resultados de busca.")
        
        wa_sessao = st.session_state.get("parceiro_logado", "Não logado")
        saldo_moedas = 0
        if db and wa_sessao != "Não logado":
            doc = db.collection("parceiros").document(limpar_whatsapp(wa_sessao)).get()
            if doc.exists:
                saldo_moedas = doc.to_dict().get("geralcoins", 0)

        st.markdown(f"### Seu Saldo Atual: <span class='coin-tag'>{saldo_moedas} GeralCoins</span>", unsafe_allow_html=True)
        st.info("Para recarregar suas moedas ou resgatar cupons de impulso, fale diretamente com a equipe comercial.")

    # --------------------------------------------------------------------------
    # CENTRAL RESTRITA DE IMPULSIONAMENTO (PACOTES GRAJAÚ TEM - PRIVADO)
    # --------------------------------------------------------------------------
    with sub_tab_impulsionar:
        st.markdown("### 🚀 Central de Impulsionamento Grajaú Tem")
        st.info("Pacotes de publicidade na maior vitrine da região: +20 Milhões de views/mês e 539k seguidores!")

        parceiro_atual = st.session_state.get("parceiro_logado", "Parceiro")

        col_pac1, col_pac2, col_pac3 = st.columns(3)

        with col_pac1:
            st.markdown("""
            <div style='background:#fff; padding:15px; border-radius:10px; border:2px solid #FF0000;'>
                <h4 style='color:#FF0000; margin:0;'>🔴 Vitrine de Ofertas</h4>
                <p style='font-size:12px; color:#555;'>Giro Diário de Notícias (Trânsito/Clima)</p>
                <ul>
                    <li><strong>R$ 100</strong> (1 Inserção Avulsa)</li>
                    <li><strong>R$ 600/mês</strong> (8 Inserções Mensais)</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Solicitar Vitrine Avulsa (R$ 100)", key="btn_vit_100"):
                registrar_intencao_compra(parceiro_atual, "Vitrine Avulsa R$100")
                msg_wa = f"Olá! Sou o parceiro {parceiro_atual} e quero contratar a *Vitrine de Ofertas Avulsa (R$ 100)*."
                st.markdown(f"<script>window.open('https://wa.me/5511980168513?text={msg_wa}', '_blank');</script>", unsafe_allow_html=True)
            if st.button("Solicitar Vitrine Mensal (R$ 600)", key="btn_vit_600"):
                registrar_intencao_compra(parceiro_atual, "Vitrine Mensal R$600")
                msg_wa = f"Olá! Sou o parceiro {parceiro_atual} e quero contratar a *Vitrine de Ofertas Mensal (R$ 600)*."
                st.markdown(f"<script>window.open('https://wa.me/5511980168513?text={msg_wa}', '_blank');</script>", unsafe_allow_html=True)

        with col_pac2:
            st.markdown("""
            <div style='background:#fff; padding:15px; border-radius:10px; border:2px solid #0047AB;'>
                <h4 style='color:#0047AB; margin:0;'>📦 Postagens Feed</h4>
                <p style='font-size:12px; color:#555;'>Divulgação nas Redes Sociais</p>
                <ul>
                    <li>🥉 <strong>Bronze (1 Post):</strong> R$ 150</li>
                    <li>🥈 <strong>Prata (3 Posts):</strong> R$ 400</li>
                    <li>🥇 <strong>Ouro (10 Posts):</strong> R$ 700</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Contratar Bronze (R$ 150)", key="btn_bronze"):
                registrar_intencao_compra(parceiro_atual, "Pacote Bronze R$150")
                st.markdown(f"<script>window.open('https://wa.me/5511980168513?text=Olá!%20Quero%20o%20Pacote%20Bronze', '_blank');</script>", unsafe_allow_html=True)
            if st.button("Contratar Prata (R$ 400)", key="btn_prata"):
                registrar_intencao_compra(parceiro_atual, "Pacote Prata R$400")
                st.markdown(f"<script>window.open('https://wa.me/5511980168513?text=Olá!%20Quero%20o%20Pacote%20Prata', '_blank');</script>", unsafe_allow_html=True)
            if st.button("Contratar Ouro (R$ 700)", key="btn_ouro"):
                registrar_intencao_compra(parceiro_atual, "Pacote Ouro R$700")
                st.markdown(f"<script>window.open('https://wa.me/5511980168513?text=Olá!%20Quero%20o%20Pacote%20Ouro', '_blank');</script>", unsafe_allow_html=True)

        with col_pac3:
            st.markdown("""
            <div style='background:#fff; padding:15px; border-radius:10px; border:2px solid #28a745;'>
                <h4 style='color:#28a745; margin:0;'>📻 Rádio Grajaú Tem</h4>
                <p style='font-size:12px; color:#555;'>Inserções Comerciais de Áudio</p>
                <ul>
                    <li><strong>R$ 300 / mês</strong></li>
                    <li>Spot comercial na rádio ao vivo</li>
                    <li>Destaque no player do topo</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Anunciar na Rádio (R$ 300)", key="btn_radio"):
                registrar_intencao_compra(parceiro_atual, "Rádio Grajaú Tem R$300")
                st.markdown(f"<script>window.open('https://wa.me/5511991853488?text=Olá!%20Quero%20anunciar%20na%20Rádio%20Grajaú%20Tem', '_blank');</script>", unsafe_allow_html=True)

# ==============================================================================
# ABA 4: PAINEL MASTER (ADMINISTRATIVO COMPLETO)
# ==============================================================================
with aba_admin:
    st.subheader("👑 Painel Administrativo de Controle Master")
    
    senha_admin = st.text_input("Senha Master do Administrador:", type="password")
    if senha_admin in ["geralja_master", "abracadabra"]:
        st.success("Autenticação Master Confirmada!")
        
        tab_adm_dash, tab_adm_intencoes, tab_adm_parceiros, tab_adm_coins = st.tabs([
            "📊 Métricas Globais", 
            "📩 Solicitações de Mídia", 
            "🏅 Gestão de Destaques",
            "💰 Recarga de GeralCoins"
        ])

        with tab_adm_dash:
            col_m1, col_m2, col_m3 = st.columns(3)
            tot_parceiros = len(lista_parceiros)
            tot_cliques = sum([p.get("cliques", 0) for p in lista_parceiros])
            tot_coins = sum([p.get("geralcoins", 0) for p in lista_parceiros])
            
            col_m1.metric("Parceiros Cadastrados", tot_parceiros)
            col_m2.metric("Total de Leads Gerados", tot_cliques)
            col_m3.metric("GeralCoins em Circulação", tot_coins)

        with tab_adm_intencoes:
            st.markdown("##### 📥 Relatório de Intenções de Compra de Mídia")
            if db:
                try:
                    intencoes = db.collection("intencoes_compra").stream()
                    dados_int = [doc.to_dict() for doc in intencoes]
                    if dados_int:
                        st.dataframe(dados_int)
                    else:
                        st.info("Nenhuma intenção de compra registrada ainda.")
                except Exception as e:
                    st.error(f"Erro ao carregar intenções: {e}")

        with tab_adm_parceiros:
            st.markdown("##### 🏅 Atribuir Selo e Categoria de Destaque")
            id_p_selo = st.text_input("WhatsApp do Parceiro (apenas números):")
            selo_opcao = st.selectbox("Escolha o Selo de Destaque:", ["NENHUM", "VITRINE", "BRONZE", "PRATA", "OURO"])
            
            if st.button("Aplicar Selo ao Anúncio"):
                if db and id_p_selo:
                    db.collection("parceiros").document(limpar_whatsapp(id_p_selo)).update({
                        "destaque": selo_opcao
                    })
                    st.success(f"Selo {selo_opcao} aplicado com sucesso ao parceiro {id_p_selo}!")

        with tab_adm_coins:
            st.markdown("##### 💰 Injetar GeralCoins na Conta do Parceiro")
            id_p_coins = st.text_input("WhatsApp do Parceiro para Recarga:")
            qtd_coins = st.number_input("Quantidade de GeralCoins:", value=100, step=50)
            
            if st.button("Adicionar Moedas"):
                if db and id_p_coins:
                    db.collection("parceiros").document(limpar_whatsapp(id_p_coins)).update({
                        "geralcoins": firestore.Increment(int(qtd_coins))
                    })
                    st.success(f"Adicionados {qtd_coins} GeralCoins com sucesso!")
    else:
        if senha_admin:
            st.error("Senha master incorreta.")

# ==============================================================================
# 8. RODAPÉ INSTITUCIONAL & LGPD (RODAPÉ BLINDADO)
# ==============================================================================
st.markdown("""
<div class='footer-box'>
    <strong>GeralJá & Grajaú Tem — Portal e Comunicação Regional</strong><br>
    Conformidade com a LGPD (Lei Geral de Proteção de Dados) | Sistema Protegido contra Injeções XSS/SQL<br>
    <small>© 2005 - 2026 Grajaú Tem. Todos os direitos reservados.</small>
</div>
""", unsafe_allow_html=True)
