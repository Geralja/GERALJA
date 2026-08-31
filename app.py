import streamlit as st
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÃO E ESTILO (VIBE RETRÔ ORKUT)
# ==========================================
st.set_page_config(
    page_title="GeralJá - A Rede Social e Vitrine do Seu Bairro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização com a paleta clássica e elementos inspirados no Orkut
st.markdown("""
<style>
    /* Fundo Azul Claro Tradicional */
    .stApp {
        background-color: #e2e8f0;
    }
    
    /* Topo do Card de Perfil */
    .orkut-header {
        background-color: #6d84b4;
        color: white;
        padding: 12px 20px;
        border-radius: 10px 10px 0 0;
        font-weight: bold;
    }
    
    /* Card Geral de Conteúdo */
    .orkut-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 16px;
        border: 1px solid #cbd5e1;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    /* Badges de Avaliação */
    .orkut-badge {
        background-color: #edf2f7;
        border: 1px solid #cbd5e1;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        margin-right: 5px;
    }

    .badge-gold {
        background-color: #fef08a;
        color: #854d0e;
        font-weight: bold;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
    }
    
    .badge-privacy {
        background-color: #3b82f6;
        color: white;
        font-size: 0.72rem;
        padding: 3px 8px;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. BANCO DE DADOS EM MEMÓRIA (SESSION STATE)
# ==========================================

# Usuário Ativo Logado
if "current_user_id" not in st.session_state:
    st.session_state.current_user_id = "usr_1"

# Base Global de Usuários
if "users_db" not in st.session_state:
    st.session_state.users_db = {
        "usr_1": {
            "name": "Morador Grajaú",
            "email": "morador@geralja.com.br",
            "location": "Grajaú",
            "privacy": "Média (Selecionados)",  # Opções: Aberto, Fechado, Média (Selecionados)
            "geral_coins": 220,
            "friends": ["usr_2"],
            "selected_friends": ["usr_2"],  # Amigos que enxergam perfil "Média"
            "friend_requests": ["usr_3"],    # Solicitantes pendentes
            "disliked_offers": [],
            "interests": ["moda", "gastronomia"],
            "bio": "Apaixonado pelo bairro! Sempre de olho nas ofertas locais 🛒"
        },
        "usr_2": {
            "name": "Ana Souza",
            "email": "ana@geralja.com.br",
            "location": "Grajaú",
            "privacy": "Aberto",
            "geral_coins": 310,
            "friends": ["usr_1"],
            "selected_friends": [],
            "friend_requests": [],
            "disliked_offers": [],
            "interests": ["gastronomia"],
            "bio": "Amo encontrar achadinhos na Belmira Marin!"
        },
        "usr_3": {
            "name": "Carlos Lima",
            "email": "carlos@geralja.com.br",
            "location": "Interlagos",
            "privacy": "Fechado",
            "geral_coins": 90,
            "friends": [],
            "selected_friends": [],
            "friend_requests": [],
            "disliked_offers": [],
            "interests": ["servicos"],
            "bio": "Morador recente querendo fazer conexões."
        }
    }

# Banco de Ofertas dos Comerciantes
if "offers_db" not in st.session_state:
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
        }
    ]

# Depoimentos / Recados do Perfil (Estilo Scraps do Orkut)
if "scraps_db" not in st.session_state:
    st.session_state.scraps_db = [
        {
            "to": "usr_1",
            "from": "usr_2",
            "text": "Passando para deixar um recado! Vamos pegar aquela coxinha na promoção?",
            "time": "Hoje às 14:20"
        }
    ]

# ==========================================
# 3. LÓGICA DE PRIVACIDADE E PERMISSÃO
# ==========================================
def can_view_profile(target_user_id, viewer_user_id):
    """
    Verifica se o espectador pode visualizar o perfil/feed privado do usuário alvo.
    - Aberto: Qualquer um vê.
    - Fechado: Apenas se forem amigos aprovados.
    - Média (Selecionados): Apenas se estiver na lista 'selected_friends'.
    """
    if target_user_id == viewer_user_id:
        return True
    
    target = st.session_state.users_db[target_user_id]
    privacy = target["privacy"]
    
    if privacy == "Aberto":
        return True
    elif privacy == "Fechado":
        return viewer_user_id in target["friends"]
    elif privacy == "Média (Selecionados)":
        return viewer_user_id in target["selected_friends"]
    return False

# ==========================================
# 4. BARRA LATERAL (GESTOR DE AMIZADES E PERFIL)
# ==========================================
curr_id = st.session_state.current_user_id
curr_user = st.session_state.users_db[curr_id]

with st.sidebar:
    st.title("🚀 GeralJá Social")
    st.caption("Conectando moradores e comércios do bairro")
    
    # Seletor de Conta (Para Simulação de Diferentes Usuários)
    st.markdown("---")
    selected_account = st.selectbox(
        "🔄 Alternar Conta (Simulador):",
        options=list(st.session_state.users_db.keys()),
        format_func=lambda x: f"{st.session_state.users_db[x]['name']} ({x})"
    )
    if selected_account != st.session_state.current_user_id:
        st.session_state.current_user_id = selected_account
        st.rerun()

    st.markdown("---")
    st.subheader(f"👤 {curr_user['name']}")
    st.write(f"**Privacidade:** `{curr_user['privacy']}`")
    st.write(f"**Bairro:** 📍 {curr_user['location']}")
    
    st.metric(
        label="Sua Carteira",
        value=f"{curr_user['geral_coins']} GeralCoins",
        delta="Atividade Social"
    )

    # Gestão de Solicitações de Amizade Pendentes
    st.markdown("---")
    st.subheader("📩 Pedidos de Amizade")
    
    requests = curr_user["friend_requests"]
    if not requests:
        st.caption("Nenhuma solicitação pendente.")
    else:
        for req_id in requests:
            req_user = st.session_state.users_db[req_id]
            st.write(f"**{req_user['name']}** quer ser seu amigo.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Aceitar", key=f"acc_{req_id}"):
                    # Adiciona aos amigos em ambas as contas
                    curr_user["friends"].append(req_id)
                    req_user["friends"].append(curr_id)
                    curr_user["friend_requests"].remove(req_id)
                    curr_user["geral_coins"] += 10  # Recompensa por expandir a rede
                    st.toast("Amizade confirmada! +10 GeralCoins")
                    st.rerun()
            with c2:
                if st.button("❌ Recusar", key=f"dec_{req_id}"):
                    curr_user["friend_requests"].remove(req_id)
                    st.rerun()

# ==========================================
# 5. PAINEL PRINCIPAL (ABAS DE NAVEGAÇÃO)
# ==========================================
tab_feed, tab_friends, tab_profile = st.tabs(["📱 Feed Social & Vitrine", "👥 Meus Amigos & Conexões", "⚙️ Configuração do Perfil"])

# ------------------------------------------
# ABA 1: FEED SOCIAL & VITRINE DE OFERTAS
# ------------------------------------------
with tab_feed:
    st.subheader("📰 Feed Unificado do Bairro")
    
    # Campo para publicação de Recado / Status Público
    with st.expander("✍️ Criar nova publicação no Feed", expanded=False):
        new_post_text = st.text_area("O que está acontecendo no bairro?")
        if st.button("Publicar no Feed"):
            if new_post_text:
                st.session_state.community_posts = st.session_state.get("community_posts", [])
                st.session_state.community_posts.insert(0, {
                    "author_id": curr_id,
                    "author": curr_user["name"],
                    "content": new_post_text,
                    "time": "Agora mesmo",
                    "likes": 0
                })
                curr_user["geral_coins"] += 2  # Ganha moedas por contribuir com o feed
                st.success("Publicado! Você ganhou +2 GeralCoins.")
                st.rerun()

    st.markdown("---")
    
    # Exibição Intercalada do Feed
    # 1. Ofertas Comerciais
    for offer in st.session_state.offers_db:
        if offer["id"] in curr_user["disliked_offers"]:
            continue  # Oculta ofertas que o usuário deu dislike
            
        st.markdown(f"""
        <div class="orkut-card" style="border-left: 5px solid #ff6b00;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="badge-gold">🔴 Vitrine de Oferta</span>
                <span class="badge-privacy">📍 {offer['location']}</span>
            </div>
            <h3 style="margin: 8px 0;">{offer['image']} {offer['title']}</h3>
            <p style="color: #666; margin: 0;">Anunciante: <strong>{offer['merchant']}</strong></p>
            <h2 style="color: #ff6b00; margin: 10px 0;">{offer['price']}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        c_like, c_dis, c_claim = st.columns([2, 2, 3])
        with c_like:
            if st.button(f"👍 Gostei ({offer['likes']})", key=f"l_off_{offer['id']}"):
                offer['likes'] += 1
                curr_user['geral_coins'] += 1
                st.toast("Interesse gravado! +1 GeralCoin")
                st.rerun()
        with c_dis:
            if st.button("🚫 Não tenho interesse", key=f"d_off_{offer['id']}"):
                curr_user["disliked_offers"].append(offer["id"])
                st.toast("Oferta removida da sua timeline.")
                st.rerun()
        with c_claim:
            if st.button("🛒 Resgatar Cupom", key=f"c_off_{offer['id']}"):
                curr_user["geral_coins"] += offer["coins_reward"]
                st.success(f"Cupom gerado com sucesso! +{offer['coins_reward']} GeralCoins resgatadas.")

    # 2. Publicações da Comunidade
    if "community_posts" in st.session_state:
        for post in st.session_state.community_posts:
            # Checa privacidade do autor do post
            if can_view_profile(post["author_id"], curr_id):
                st.markdown(f"""
                <div class="orkut-card">
                    <div style="display: flex; justify-content: space-between;">
                        <strong>👤 {post['author']}</strong>
                        <span style="color: #888; font-size: 0.8rem;">{post['time']}</span>
                    </div>
                    <p style="margin-top: 10px;">{post['content']}</p>
                </div>
                """, unsafe_allow_html=True)

# ------------------------------------------
# ABA 2: MEUS AMIGOS E BUSCA DE REDE
# ------------------------------------------
with tab_friends:
    st.subheader("👥 Lista de Amigos e Conexões")
    
    col_my_friends, col_find = st.columns(2)
    
    with col_my_friends:
        st.markdown("### Seus Amigos")
        if not curr_user["friends"]:
            st.info("Você ainda não possui amigos adicionados.")
        else:
            for f_id in curr_user["friends"]:
                friend = st.session_state.users_db[f_id]
                is_selected = f_id in curr_user["selected_friends"]
                
                st.markdown(f"""
                <div class="orkut-card">
                    <strong>👤 {friend['name']}</strong><br>
                    <small>📍 {friend['location']} | Privacidade: {friend['privacy']}</small>
                </div>
                """, unsafe_allow_html=True)
                
                # Controle da Privacidade "Média (Selecionados)"
                if curr_user["privacy"] == "Média (Selecionados)":
                    check_val = st.checkbox("Incluir na Lista de Amigos Selecionados", value=is_selected, key=f"sel_{f_id}")
                    if check_val != is_selected:
                        if check_val:
                            curr_user["selected_friends"].append(f_id)
                        else:
                            curr_user["selected_friends"].remove(f_id)
                        st.rerun()

    with col_find:
        st.markdown("### Adicionar Novos Amigos")
        for u_id, u_data in st.session_state.users_db.items():
            if u_id != curr_id and u_id not in curr_user["friends"]:
                st.write(f"**{u_data['name']}** ({u_data['location']})")
                
                if curr_id in u_data["friend_requests"]:
                    st.caption("⏳ Solicitação enviada")
                else:
                    if st.button(f"➕ Enviar Pedido de Amizade", key=f"add_{u_id}"):
                        u_data["friend_requests"].append(curr_id)
                        st.toast(f"Solicitação enviada para {u_data['name']}!")
                        st.rerun()

# ------------------------------------------
# ABA 3: CONFIGURAÇÃO DE PRIVACIDADE E PERFIL
# ------------------------------------------
with tab_profile:
    st.subheader("⚙️ Configurações do Perfil e Privacidade")
    
    with st.form("profile_form"):
        new_bio = st.text_area("Sua Bio / Descrição do Perfil:", value=curr_user["bio"])
        
        # Opções de Privacidade do Perfil
        new_privacy = st.radio(
            "🔒 Quem pode ver suas curtidas, conquistas e recados?",
            options=["Aberto", "Fechado", "Média (Selecionados)"],
            index=["Aberto", "Fechado", "Média (Selecionados)"].index(curr_user["privacy"]),
            help="• Aberto: Qualquer visitante do bairro.\n• Fechado: Apenas amigos confirmados.\n• Média: Apenas os amigos selecionados por você."
        )
        
        save_btn = st.form_submit_button("Salvar Alterações")
        if save_btn:
            curr_user["bio"] = new_bio
            curr_user["privacy"] = new_privacy
            st.success("Configurações atualizadas com sucesso!")
            st.rerun()

    # Visualização em Estilo Orkut (Recados)
    st.markdown("---")
    st.subheader("📬 Seus Recados (Scraps)")
    
    user_scraps = [s for s in st.session_state.scraps_db if s["to"] == curr_id]
    if not user_scraps:
        st.caption("Nenhum recado recebido ainda.")
    else:
        for scrap in user_scraps:
            sender = st.session_state.users_db[scrap["from"]]
            st.markdown(f"""
            <div class="orkut-card">
                <strong>{sender['name']}</strong> escreveu:
                <p style="margin-top: 5px; color: #333;">{scrap['text']}</p>
                <small style="color: #999;">{scrap['time']}</small>
            </div>
            """, unsafe_allow_html=True)
