import streamlit as st
import random
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E CSS CUSTOMIZADO
# ==========================================
st.set_page_config(
    page_title="GeralJá - O Feed do Seu Bairro",
    page_icon="🚀",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Estilização no padrão de Feed de Rede Social
st.markdown("""
<style>
    /* Estilo Geral */
    .stApp {
        background-color: #f4f6f8;
    }
    
    /* Card de Postagem no Feed */
    .feed-card {
        background-color: #ffffff;
        border-radius: 16px;
        padding: 18px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.04);
        border: 1px solid #eaeaea;
    }
    
    /* Destaque para Ofertas Comerciais */
    .offer-card {
        border-left: 6px solid #ff6b00;
        background: linear-gradient(135deg, #ffffff 80%, #fff9f2 100%);
    }
    
    /* Badges / Etiquetas */
    .badge-offer {
        background-color: #ff6b00;
        color: white;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 20px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge-coin {
        background-color: #10b981;
        color: white;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 20px;
    }
    
    .badge-location {
        background-color: #3b82f6;
        color: white;
        font-size: 0.72rem;
        padding: 3px 8px;
        border-radius: 12px;
    }

    /* Botões Redondos de Rede Social */
    div.stButton > button {
        border-radius: 20px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease-in-out;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. INICIALIZAÇÃO DE ESTADO (SESSION STATE)
# ==========================================
if "user" not in st.session_state:
    st.session_state.user = {
        "email": "morador@geralja.com.br",
        "logged_in": True,
        "location": "Grajaú",
        "geral_coins": 150,
        "interests": ["moda", "gastronomia"],
        "disliked_offers": []  # Lista de IDs de ofertas ocultadas pelo usuário
    }

if "offers_db" not in st.session_state:
    # Banco de Ofertas dos Comerciantes
    st.session_state.offers_db = [
        {
            "id": "off_101",
            "merchant": "Padaria Panela Velha",
            "title": "Combo Café + Coxinha Gourmet",
            "category": "gastronomia",
            "location": "Grajaú",
            "price": "R$ 12,00",
            "coins_reward": 5,
            "image": "☕",
            "likes": 42
        },
        {
            "id": "off_102",
            "merchant": "Boutique Moda Urbana",
            "title": "Short Jeans Feminino - 30% OFF",
            "category": "moda",
            "location": "Grajaú",
            "price": "R$ 59,90",
            "coins_reward": 10,
            "image": "👖",
            "likes": 88
        },
        {
            "id": "off_103",
            "merchant": "Auto Peças & Serviços",
            "title": "Troca de Óleo e Filtro Completa",
            "category": "servicos",
            "location": "Interlagos",
            "price": "R$ 140,00",
            "coins_reward": 15,
            "image": "🚗",
            "likes": 12
        }
    ]

if "community_posts" not in st.session_state:
    # Postagens comunitárias no feed
    st.session_state.community_posts = [
        {
            "id": "post_201",
            "author": "Maria Silva",
            "content": "Alguém indica uma costureira boa aqui perto da estação?",
            "time": "Há 15 min",
            "likes": 5
        },
        {
            "id": "post_202",
            "author": "João Santos",
            "content": "Trânsito fluindo super bem na Av. Dona Belmira Marin agora!",
            "time": "Há 40 min",
            "likes": 19
        }
    ]

# ==========================================
# 3. MOTOR DE INTELIGÊNCIA E RECOMENDAÇÃO
# ==========================================
def rank_and_filter_offers():
    """
    Algoritmo Inteligente:
    1. Filtra ofertas que o usuário deu 'Dislike' / Ocultou.
    2. Calcula pontuação baseada na localização e interesses do usuário.
    """
    user_loc = st.session_state.user["location"]
    user_interests = st.session_state.user["interests"]
    disliked = st.session_state.user["disliked_offers"]
    
    valid_offers = [o for o in st.session_state.offers_db if o["id"] not in disliked]
    
    def calculate_score(offer):
        score = 0
        # Bônus por localização próxima
        if offer["location"].lower() == user_loc.lower():
            score += 50
        # Bônus por interesse/histórico do usuário
        if offer["category"].lower() in [i.lower() for i in user_interests]:
            score += 40
        # Bônus por engajamento (popularidade)
        score += offer["likes"] * 0.5
        return score
    
    return sorted(valid_offers, key=calculate_score, reverse=True)

# ==========================================
# 4. BARRA LATERAL (PERFIL E AUTENTICAÇÃO)
# ==========================================
with st.sidebar:
    st.title("🚀 GeralJá")
    st.caption("A rede social comercial do seu bairro")
    
    if st.session_state.user["logged_in"]:
        st.subheader("👤 Seu Perfil")
        st.write(f"**E-mail:** {st.session_state.user['email']}")
        st.write(f"**Bairro:** 📍 {st.session_state.user['location']}")
        
        st.markdown("---")
        st.metric(
            label="Sua Carteira",
            value=f"{st.session_state.user['geral_coins']} GeralCoins",
            delta="Ganhe interagindo"
        )
        st.markdown("---")
        
        st.subheader("🔑 Segurança")
        if st.button("Redefinir Senha via E-mail"):
            # Lógica simulada do Firebase Auth SendPasswordResetEmail
            st.success(f"E-mail de redefinição enviado para {st.session_state.user['email']}!")
            
        if st.button("Sair da Conta"):
            st.session_state.user["logged_in"] = False
            st.rerun()

    else:
        st.subheader("🔐 Entrar ou Cadastrar")
        email_input = st.text_input("Seu E-mail (@geralja.com.br ou outro):")
        pass_input = st.text_input("Sua Senha:", type="password")
        
        col_login, col_rec = st.columns(2)
        with col_login:
            if st.button("Entrar"):
                st.session_state.user["email"] = email_input or "morador@geralja.com.br"
                st.session_state.user["logged_in"] = True
                st.rerun()
        with col_rec:
            if st.button("Esqueci a Senha"):
                if email_input:
                    st.info(f"Link de verificação enviado para {email_input}.")
                else:
                    st.warning("Preencha o e-mail para recuperar.")

# ==========================================
# 5. FEED PRINCIPAL (ESTILO REDE SOCIAL)
# ==========================================
st.title("📱 Feed do Bairro")

# Campo de busca com inteligência semântica
search_query = st.text_input("🔍 O que você procura hoje no bairro? (Ex: short jeans, coxinha, óleo)...")

if search_query:
    st.caption(f"Exibindo resultados personalizados para: *{search_query}*")
    # Adiciona a busca aos interesses dinâmicos do usuário
    if search_query.lower() not in st.session_state.user["interests"]:
        st.session_state.user["interests"].append(search_query.lower())

# Montagem intercalada do Feed (Posts + Ofertas)
ranked_offers = rank_and_filter_offers()
feed_items = []

# Adiciona posts comunitários
for p in st.session_state.community_posts:
    feed_items.append({"type": "community", "data": p, "sort_time": 1})

# Adiciona ofertas ranqueadas pela IA
for idx, o in enumerate(ranked_offers):
    feed_items.append({"type": "offer", "data": o, "sort_time": idx})

# Exibição Fluida no Feed
for item in feed_items:
    
    # CASE 1: POST COMUNITÁRIO
    if item["type"] == "community":
        data = item["data"]
        st.markdown(f"""
        <div class="feed-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <strong>👤 {data['author']}</strong>
                <span style="color: #888; font-size: 0.8rem;">{data['time']}</span>
            </div>
            <p style="margin-top: 10px; font-size: 1rem;">{data['content']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2, _ = st.columns([1, 1, 3])
        with c1:
            if st.button(f"❤️ {data['likes']}", key=f"like_{data['id']}"):
                data['likes'] += 1
                st.session_state.user["geral_coins"] += 1  # Recompensa por engajamento
                st.rerun()
                
    # CASE 2: OFERTA DO COMERCIANTE (VITRINE INTELIGENTE)
    elif item["type"] == "offer":
        data = item["data"]
        
        # Filtro da barra de busca simples
        if search_query and (search_query.lower() not in data["title"].lower() and search_query.lower() not in data["category"].lower()):
            continue

        st.markdown(f"""
        <div class="feed-card offer-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span class="badge-offer">🔴 Vitrine de Oferta</span>
                <span class="badge-location">📍 {data['location']}</span>
            </div>
            <h3 style="margin: 0; color: #111;">{data['image']} {data['title']}</h3>
            <p style="margin: 4px 0; color: #555;">Anunciado por: <strong>{data['merchant']}</strong></p>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 12px;">
                <h2 style="margin: 0; color: #ff6b00;">{data['price']}</h2>
                <span class="badge-coin">+{data['coins_reward']} GeralCoins</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col_interact, col_dislike, col_buy = st.columns([2, 2, 3])
        
        with col_interact:
            if st.button(f"👍 Gostei ({data['likes']})", key=f"like_{data['id']}"):
                data['likes'] += 1
                # Adiciona categoria aos interesses do usuário
                if data["category"] not in st.session_state.user["interests"]:
                    st.session_state.user["interests"].append(data["category"])
                st.toast("Interesse registrado! Ofertas similares aparecerão mais para você.")
                st.rerun()
                
        with col_dislike:
            # Botão de Ocultar / Dislike (Regra solicitada)
            if st.button("🚫 Não tenho interesse", key=f"dis_{data['id']}"):
                st.session_state.user["disliked_offers"].append(data["id"])
                st.toast("Oferta removida do seu feed!")
                st.rerun()
                
        with col_buy:
            if st.button("🛒 Resgatar Oferta", key=f"buy_{data['id']}"):
                st.session_state.user["geral_coins"] += data["coins_reward"]
                st.success(f"Cupom gerado! Você recebeu +{data['coins_reward']} GeralCoins.")

    st.markdown("---")
