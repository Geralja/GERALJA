import os
import json
import base64
import math
import re
from datetime import datetime
import io

import streamlit as st
import streamlit.components.v1 as components

# ==============================================================================
# 1. TRATAMENTO SEGURO DE IMPORTAÇÕES (FALLBACK SYSTEM)
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
# 2. CONFIGURAÇÃO DA PÁGINA STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="GeralJá | Grajaú Tem — O Portal da Nossa Região",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS Personalizada
st.markdown("""
<style>
    /* Estilização Geral e Cards Social 5.0 */
    .stApp { background-color: #f8f9fa; }
    .main-header { font-size: 26px; font-weight: 800; color: #0047AB; text-align: center; margin-bottom: 5px; }
    .sub-header { font-size: 14px; color: #555; text-align: center; margin-bottom: 15px; }
    
    .card-social {
        background-color: #ffffff;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        overflow: hidden;
        margin-bottom: 20px;
        border: 1px solid #e0e0e0;
    }
    .card-banner {
        width: 100%;
        height: 110px;
        object-fit: cover;
        background-color: #0047AB;
    }
    .card-body {
        padding: 15px;
        position: relative;
    }
    .avatar-container {
        margin-top: -45px;
        margin-bottom: 10px;
    }
    .card-avatar {
        width: 70px;
        height: 70px;
        border-radius: 50%;
        border: 3px solid #ffffff;
        object-fit: cover;
        background-color: #fff;
    }
    .badge-ouro { background-color: #FFD700; color: #000; font-weight: bold; padding: 2px 8px; border-radius: 10px; font-size: 11px; }
    .badge-prata { background-color: #C0C0C0; color: #000; font-weight: bold; padding: 2px 8px; border-radius: 10px; font-size: 11px; }
    .badge-bronze { background-color: #CD7F32; color: #fff; font-weight: bold; padding: 2px 8px; border-radius: 10px; font-size: 11px; }
    .badge-vitrine { background-color: #FF0000; color: #fff; font-weight: bold; padding: 2px 8px; border-radius: 10px; font-size: 11px; }
    
    .price-tag { color: #28a745; font-weight: bold; font-size: 16px; }
    .footer-box { text-align: center; padding: 20px; font-size: 12px; color: #777; border-top: 1px solid #ddd; margin-top: 40px; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. CONEXÃO FIREBASE & FUNÇÕES AUXILIARES
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

def otimizar_imagem(upload_file, max_size=(800, 800), quality=80):
    """Comprime imagens para evitar estourar o limite de 1MB do Firestore"""
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

# Registrar lead / clique
def registrar_lead_clique(parceiro_id):
    if db:
        try:
            doc_ref = db.collection("parceiros").document(parceiro_id)
            doc_ref.update({"cliques": firestore.Increment(1)})
        except Exception:
            pass

# Registrar intenção de compra de mídia
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

# ==============================================================================
# 4. RÁDIO GRAJAÚ TEM (PLAYER INTEGRADO CLOUDFRONT)
# ==============================================================================
def renderizar_player_radio():
    st.markdown("""
    <div style="margin-bottom: 2px;">
        <strong style="font-size: 14px; color: #0047AB;">📻 Rádio Grajaú Tem — Ao Vivo</strong>
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

# ==============================================================================
# 5. NAVEGAÇÃO PRINCIPAL (ABAS)
# ==============================================================================
renderizar_player_radio()

st.markdown("<h1 class='main-header'>GeralJá + Grajaú Tem</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>A maior vitrine de serviços e comércio do Grajaú e região</p>", unsafe_allow_html=True)

aba_publica, aba_parceiro, aba_admin = st.tabs([
    "📍 Encontrar Serviços", 
    "👤 Área do Parceiro / Anunciante", 
    "👑 Painel Master (Admin)"
])

# ==============================================================================
# ABA 1: ENCONTRAR SERVIÇOS (PÚBLICO)
# ==============================================================================
with aba_publica:
    st.markdown("### 🔎 O que você precisa hoje?")
    
    # Botões Rápidos de Busca
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

    # Carregar parceiros do Firestore
    lista_parceiros = []
    if db:
        try:
            docs = db.collection("parceiros").stream()
            for d in docs:
                p = d.to_dict()
                p["id"] = d.id
                lista_parceiros.append(p)
        except Exception as e:
            st.error(f"Erro ao buscar parceiros: {e}")

    # Dados Mock se o banco estiver vazio
    if not lista_parceiros:
        lista_parceiros = [
            {
                "id": "mock1",
                "nome": "Padaria & Confeitaria Solar",
                "categoria": "Pizzaria / Padaria",
                "bio": "Pães quentinhos toda hora, pizzas no forno a lenha e os melhores doces da região.",
                "whatsapp": "11980168513",
                "avatar": "https://via.placeholder.com/150",
                "capa": "https://via.placeholder.com/800x200",
                "lat": -23.7520, "lon": -46.6920,
                "destaque": "OURO",
                "produtos": [{"titulo": "Pizza Calabresa", "preco": "R$ 45,00", "desc": "Molho caseiro e queijo no capricho"}]
            },
            {
                "id": "mock2",
                "nome": "Eletricista Silva 24h",
                "categoria": "Eletricista",
                "bio": "Instalações elétricas residenciais e comerciais. Atendimento de urgência no Grajaú.",
                "whatsapp": "11991853488",
                "avatar": "https://via.placeholder.com/150",
                "capa": "https://via.placeholder.com/800x200",
                "lat": -23.7550, "lon": -46.6950,
                "destaque": "VITRINE",
                "produtos": []
            }
        ]

    # Filtragem dos parceiros
    parceiros_filtrados = []
    for p in lista_parceiros:
        match = True
        if input_busca:
            termo = input_busca.lower()
            nome_match = termo in p.get("nome", "").lower()
            cat_match = termo in p.get("categoria", "").lower()
            bio_match = termo in p.get("bio", "").lower()
            match = nome_match or cat_match or bio_match
        if match:
            parceiros_filtrados.append(p)

    st.subheader(f"Encontrados ({len(parceiros_filtrados)})")

    # Renderização dos Cards Social 5.0
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

            # Botão WhatsApp
            if wa_num:
                link_wa = f"https://wa.me/{wa_num}?text=Olá!%20Vi%20seu%20perfil%20no%20GeralJá%20e%20gostaria%20de%20mais%20informações."
                if st.button(f"💬 Chamar no WhatsApp ({p.get('nome')})", key=f"btn_wa_{p['id']}"):
                    registrar_lead_clique(p['id'])
                    st.markdown(f"<script>window.open('{link_wa}', '_blank');</script>", unsafe_allow_html=True)

            # Vitrine de Produtos (Expander)
            produtos = p.get("produtos", [])
            if produtos:
                with st.expander(f"🛍️ Ver Ofertas/Produtos ({len(produtos)})"):
                    for prod in produtos:
                        st.markdown(f"**{prod.get('titulo')}** — <span class='price-tag'>{prod.get('preco')}</span>", unsafe_allow_html=True)
                        st.caption(prod.get('desc', ''))
                        if prod.get('foto'):
                            st.image(safe_image_src(prod.get('foto')), width=150)
                        st.markdown("---")

# ==============================================================================
# ABA 2: ÁREA DO PARCEIRO (GERENCIAMENTO + IMPULSIONAMENTO PRIVADO)
# ==============================================================================
with aba_parceiro:
    st.subheader("👤 Painel de Controle do Parceiro")
    
    sub_tab_login, sub_tab_perfil, sub_tab_impulsionar = st.tabs([
        "🔑 Entrar / Cadastrar", 
        "✏️ Meu Perfil & Produtos", 
        "🚀 Impulsionar no Grajaú Tem"
    ])

    with sub_tab_login:
        st.markdown("##### Acesse sua conta de parceiro")
        login_wa = st.text_input("Seu WhatsApp cadastrado (apenas números):", key="log_wa")
        if st.button("Acessar Painel"):
            st.session_state["parceiro_logado"] = login_wa
            st.success("Acesso liberado! Navegue pelas abas 'Meu Perfil' e 'Impulsionar'.")

    with sub_tab_perfil:
        st.markdown("##### Atualize seus Dados de Exibição")
        nome_p = st.text_input("Nome Comercial / Marca:")
        cat_p = st.text_input("Categoria (ex: Barberia, Encanador, Salão):")
        bio_p = st.text_area("Biografia / Descrição do Negócio:")
        wa_p = st.text_input("WhatsApp de Atendimento:")
        
        col_img1, col_img2 = st.columns(2)
        up_avatar = col_img1.file_uploader("Foto de Perfil (Avatar):", type=["jpg", "png", "jpeg"])
        up_capa = col_img2.file_uploader("Foto de Capa (Banner):", type=["jpg", "png", "jpeg"])

        if st.button("💾 Salvar Perfil"):
            if db and wa_p:
                data_update = {
                    "nome": nome_p,
                    "categoria": cat_p,
                    "bio": bio_p,
                    "whatsapp": wa_p,
                    "atualizado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                if up_avatar:
                    data_update["avatar"] = otimizar_imagem(up_avatar)
                if up_capa:
                    data_update["capa"] = otimizar_imagem(up_capa)

                db.collection("parceiros").document(limpar_whatsapp(wa_p)).set(data_update, merge=True)
                st.success("Perfil atualizado com sucesso!")
            else:
                st.warning("Preencha o WhatsApp e garanta a conexão com o banco.")

        st.markdown("---")
        st.markdown("##### 🛍️ Cadastrar Oferta / Produto na Vitrine")
        prod_titulo = st.text_input("Nome do Produto/Oferta:")
        prod_preco = st.text_input("Preço (ex: R$ 49,90):")
        prod_desc = st.text_input("Descrição Curta:")
        prod_foto = st.file_uploader("Foto do Produto:", type=["jpg", "png"], key="prod_img")

        if st.button("➕ Adicionar Produto"):
            if db and wa_p:
                novo_prod = {
                    "titulo": prod_titulo,
                    "preco": prod_preco,
                    "desc": prod_desc,
                    "foto": otimizar_imagem(prod_foto) if prod_foto else None
                }
                doc_ref = db.collection("parceiros").document(limpar_whatsapp(wa_p))
                doc_ref.update({"produtos": firestore.ArrayUnion([novo_prod])})
                st.success("Produto adicionado à sua vitrine!")

    # --------------------------------------------------------------------------
    # CENTRAL RESTRITA DE IMPULSIONAMENTO (PACOTES COMERCIAIS GRAJAÚ TEM)
    # --------------------------------------------------------------------------
    with sub_tab_impulsionar:
        st.markdown("### 🚀 Central de Mídia & Impulsionamento Grajaú Tem")
        st.info("Coloque sua marca em evidência para mais de 539 mil seguidores e 20 milhões de visualizações/mês!")

        parceiro_atual = st.session_state.get("parceiro_logado", "Parceiro")

        # Tabela de Pacotes Comerciais Privados
        col_pac1, col_pac2, col_pac3 = st.columns(3)

        with col_pac1:
            st.markdown("""
            <div style='background:#fff; padding:15px; border-radius:10px; border:2px solid #FF0000;'>
                <h4 style='color:#FF0000; margin:0;'>🔴 Vitrine de Ofertas</h4>
                <p style='font-size:12px; color:#555;'>Giro diário de notícias (Trânsito/Clima)</p>
                <ul>
                    <li><strong>R$ 100</strong> (Inserção Avulsa)</li>
                    <li><strong>R$ 600/mês</strong> (8 Inserções Mensais)</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Quero Vitrine Avulsa (R$ 100)", key="btn_vit_100"):
                registrar_intencao_compra(parceiro_atual, "Vitrine Avulsa R$100")
                msg_wa = f"Olá! Sou o parceiro {parceiro_atual} e quero fechar o pacote *Vitrine de Ofertas Avulsa (R$ 100)*."
                st.markdown(f"<script>window.open('https://wa.me/5511980168513?text={msg_wa}', '_blank');</script>", unsafe_allow_html=True)
            if st.button("Quero Vitrine Mensal (R$ 600)", key="btn_vit_600"):
                registrar_intencao_compra(parceiro_atual, "Vitrine Mensal R$600")
                msg_wa = f"Olá! Sou o parceiro {parceiro_atual} e quero fechar o pacote *Vitrine de Ofertas Mensal (R$ 600)*."
                st.markdown(f"<script>window.open('https://wa.me/5511980168513?text={msg_wa}', '_blank');</script>", unsafe_allow_html=True)

        with col_pac2:
            st.markdown("""
            <div style='background:#fff; padding:15px; border-radius:10px; border:2px solid #0047AB;'>
                <h4 style='color:#0047AB; margin:0;'>📦 Postagens Avulsas</h4>
                <p style='font-size:12px; color:#555;'>Publicações no Feed Oficial</p>
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
                <p style='font-size:12px; color:#555;'>Anúncio em áudio na programação ao vivo</p>
                <ul>
                    <li><strong>R$ 300 / mês</strong></li>
                    <li>Chamadas comerciais de 30s</li>
                    <li>Link direto no player topo</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Anunciar na Rádio (R$ 300)", key="btn_radio"):
                registrar_intencao_compra(parceiro_atual, "Rádio Grajaú Tem R$300")
                st.markdown(f"<script>window.open('https://wa.me/5511991853488?text=Olá!%20Quero%20anunciar%20na%20Rádio%20Grajaú%20Tem', '_blank');</script>", unsafe_allow_html=True)

# ==============================================================================
# ABA 3: PAINEL MASTER (ADMINISTRATIVO & COMERCIAL)
# ==============================================================================
with aba_admin:
    st.subheader("👑 Painel Administrativo de Diretoria")
    
    senha_admin = st.text_input("Senha de Acesso Master:", type="password")
    if senha_admin in ["geralja_master", "abracadabra"]:
        st.success("Autenticado como Administrador Master.")
        
        tab_adm_intencoes, tab_adm_parceiros = st.tabs(["📊 Intenções de Compra (Leads)", "⚙️ Gerenciar Destaques"])

        with tab_adm_intencoes:
            st.markdown("##### 📩 Solicitações de Impulsionamento Registradas")
            if db:
                try:
                    intencoes = db.collection("intencoes_compra").stream()
                    dados_int = [doc.to_dict() for doc in intencoes]
                    if dados_int:
                        st.dataframe(dados_int)
                    else:
                        st.info("Nenhuma intenção de compra registrada até o momento.")
                except Exception as e:
                    st.error(f"Erro ao carregar intenções: {e}")

        with tab_adm_parceiros:
            st.markdown("##### 🏅 Atribuir Selo de Destaque ao Parceiro")
            id_parceiro_selo = st.text_input("WhatsApp/ID do Parceiro:")
            selo_opcao = st.selectbox("Selo de Impulsionamento:", ["NENHUM", "VITRINE", "BRONZE", "PRATA", "OURO"])
            
            if st.button("Atualizar Selo do Parceiro"):
                if db and id_parceiro_selo:
                    db.collection("parceiros").document(limpar_whatsapp(id_parceiro_selo)).update({
                        "destaque": selo_opcao
                    })
                    st.success(f"Selo {selo_opcao} atribuído com sucesso!")
    else:
        if senha_admin:
            st.error("Senha master incorreta.")

# ==============================================================================
# 6. RODAPÉ INSTITUCIONAL & LGPD (RODAPÉ BLINDADO)
# ==============================================================================
st.markdown("""
<div class='footer-box'>
    <strong>GeralJá & Grajaú Tem — Comunicação e Soluções Locais</strong><br>
    Conformidade com a LGPD (Lei Geral de Proteção de Dados) | Ambiente Monitorado e Protegido<br>
    <small>© 2005 - 2026 Grajaú Tem. Todos os direitos reservados.</small>
</div>
""", unsafe_allow_html=True)
