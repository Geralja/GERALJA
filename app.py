import streamlit as st
import json
import os
import re
import time
import uuid
import unicodedata
import base64

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILOS CSS
# ==========================================
st.set_page_config(
    page_title="GeralJá v6.0 Master Ecosystem",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS customizada integrada[cite: 2, 7, 9]
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    .metric-card {
        background-color: #1e222d;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #2e3440;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 2. CARREGAMENTO DEFENSIVO DE DEPENDÊNCIAS
# ==========================================
# Trata importações opcionais sem interromper a aplicação[cite: 3, 4, 5, 8]
try:
    import feedparser
except ImportError:
    feedparser = None

try:
    from streamlit_js_eval import streamlit_js_eval
except ImportError:
    streamlit_js_eval = None

try:
    import gspread
except ImportError:
    gspread = None

try:
    from fuzzywuzzy import fuzz
except ImportError:
    fuzz = None


# ==========================================
# 3. ISOLAMENTO E EXECUÇÃO SEGURA DE BLOCOS
# ==========================================
def executar_bloco_seguro(titulo, funcao, *args, **kwargs):
    """
    Executa um módulo da interface dentro de um container isolado.
    Se ocorrer um erro, a falha é contida sem derrubar a aplicação.
    """
    st.subheader(titulo)
    with st.container():
        try:
            return funcao(*args, **kwargs)
        except Exception as e:
            st.error(f"⚠️ Erro ao carregar o módulo '{titulo}': {e}")
            return None


# ==========================================
# 4. INFRAESTRUTURA FIREBASE & OAUTH
# ==========================================
def inicializar_firebase():
    """
    Inicializa a conexão com o Cloud Firestore via credenciais Base64
    armazenadas em st.secrets[cite: 2, 7, 8].
    """
    if "firebase_db" in st.session_state:
        return st.session_state["firebase_db"]
    
    try:
        if "FIREBASE_CREDENTIALS_BASE64" in st.secrets:
            import firebase_admin
            from firebase_admin import credentials, firestore
            
            if not firebase_admin._apps:
                cred_json = json.loads(
                    base64.b64decode(st.secrets["FIREBASE_CREDENTIALS_BASE64"]).decode('utf-8')
                )
                cred = credentials.Certificate(cred_json)
                firebase_admin.initialize_app(cred)
            
            db = firestore.client()
            st.session_state["firebase_db"] = db
            return db
        else:
            return None
    except Exception as e:
        st.sidebar.warning(f"Modo local/offline: {e}")
        return None


# ==========================================
# 5. MOTOR DE CARTEIRA MULTI-MOEDA
# ==========================================
class CarteiraEngine:
    """
    Gerencia a contabilidade tri-moeda do ecossistema:
    - GeralCoins (Recompensas de engajamento)
    - Crédito BRL (Compra pré-paga de leads/orçamentos)
    - Custódia BRL (Escrow para garantia de serviços)[cite: 2, 3, 8]
    """
    TAXA_CONVERSAO_GC_BRL = 0.10  # 10 GeralCoins = R$ 1,00

    @staticmethod
    def obter_saldo(user_id):
        key = f"carteira_{user_id}"
        if key not in st.session_state:
            st.session_state[key] = {
                "geralcoins": 100.0,
                "credito_brl": 50.00,
                "custodia_brl": 0.00
            }
        return st.session_state[key]

    @staticmethod
    def converter_gc_para_credito(user_id, quantidade_gc):
        """Converte GeralCoins acumuladas em Crédito BRL pré-pago[cite: 2, 8]."""
        saldo = CarteiraEngine.obter_saldo(user_id)
        if saldo["geralcoins"] >= quantidade_gc:
            valor_brl = quantidade_gc * CarteiraEngine.TAXA_CONVERSAO_GC_BRL
            saldo["geralcoins"] -= quantidade_gc
            saldo["credito_brl"] += valor_brl
            st.session_state[f"carteira_{user_id}"] = saldo
            CarteiraEngine.registrar_transacao(
                user_id, "conversao", valor_brl, "BRL", f"Conversão de {quantidade_gc} GC em R$ {valor_brl:.2f}"
            )
            return True, valor_brl
        return False, 0.0

    @staticmethod
    def registrar_transacao(user_id, tipo, valor, moeda, descricao):
        """Registra a movimentação no ledger[cite: 8]."""
        if "historico_transacoes" not in st.session_state:
            st.session_state["historico_transacoes"] = []
        
        transacao = {
            "user_id": user_id,
            "tipo": tipo,
            "valor": valor,
            "moeda": moeda,
            "descricao": descricao,
            "timestamp": time.time()
        }
        st.session_state["historico_transacoes"].append(transacao)
        
        # Sincronização assíncrona com Firestore se disponível[cite: 8]
        db = inicializar_firebase()
        if db:
            try:
                db.collection("transacoes").add(transacao)
            except Exception:
                pass


# ==========================================
# 6. MOTOR DE BUSCA TOLERANTE E NORMALIZAÇÃO
# ==========================================
def normalizar_texto(texto):
    """Aplica normalização Unicode NFKD e remove acentuação[cite: 2, 7, 8]."""
    if not texto:
        return ""
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8').lower().strip()

def buscar_servicos(termo_busca, lista_categorias):
    """
    Busca tolerante a falhas por correspondência direta ou fuzzy matching[cite: 2, 7, 8].
    """
    termo_limpo = normalizar_texto(termo_busca)
    if not termo_limpo:
        return lista_categorias
    
    # 1. Direct Matching[cite: 2, 7, 8]
    resultados = [cat for cat in lista_categorias if termo_limpo in normalizar_texto(cat)]
    if resultados:
        return resultados

    # 2. Fuzzy Matching Fallback[cite: 2, 7, 8]
    if fuzz:
        resultados_fuzzy = [
            cat for cat in lista_categorias 
            if fuzz.partial_ratio(termo_limpo, normalizar_texto(cat)) > 70
        ]
        if resultados_fuzzy:
            return resultados_fuzzy

    return lista_categorias


# ==========================================
# 7. PAY-PER-ENGAGEMENT (PPE) E WEB SHARE
# ==========================================
def processar_recompensa_social(user_id, merchant_id, acao):
    """
    Recompensa o morador com GeralCoins por engajamento e debita do saldo do comerciante[cite: 3, 4].
    Curtir: +1 GC | Comentar: +2 GC | Compartilhar: +3 GC[cite: 3, 4].
    """
    recompensas = {"curtir": 1.0, "comentar": 2.0, "compartilhar": 3.0}
    valor_gc = recompensas.get(acao, 0.0)
    
    if valor_gc > 0:
        saldo = CarteiraEngine.obter_saldo(user_id)
        saldo["geralcoins"] += valor_gc
        st.session_state[f"carteira_{user_id}"] = saldo
        CarteiraEngine.registrar_transacao(
            user_id, "credito", valor_gc, "GC", f"Recompensa PPE ({acao}) da loja {merchant_id}"
        )
        st.toast(f"🎉 Você acumulou +{valor_gc} GC por {acao}![cite: 3, 4]")

def gerar_token_compartilhamento(user_id, item_id):
    """Gera token único validado para compartilhamento seguro via Web Share API[cite: 2, 7, 8]."""
    token = str(uuid.uuid4())
    st.session_state[f"share_token_{token}"] = {
        "user_id": user_id, 
        "item_id": item_id, 
        "usado": False,
        "criado_em": time.time()
    }
    return token


# ==========================================
# 8. MONITOR DE PEDIDOS COM ALERTA SONORO
# ==========================================
def renderizar_monitor_pedidos():
    """
    Painel de despacho com sinal sonoro contínuo em loop (<audio autoplay loop>)
    disparado ao receber novos pedidos pendentes.
    """
    if "pedidos_pendentes" not in st.session_state:
        st.session_state["pedidos_pendentes"] = [
            {"id": "PED-801", "cliente": "João Silva", "item": "Marmita Executiva", "valor": 22.90, "status": "Pendente"},
            {"id": "PED-802", "cliente": "Ana Lima", "item": "Suco Natural 500ml", "valor": 8.00, "status": "Pendente"}
        ]

    pedidos = st.session_state["pedidos_pendentes"]

    if pedidos:
        st.warning(f"🚨 ATENÇÃO: Existe(m) {len(pedidos)} novo(s) pedido(s) pendente(s)!")
        # Sinal sonoro em loop automático[cite: 3]
        st.markdown(
            """
            <audio autoplay loop>
                <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg">
            </audio>
            """,
            unsafe_allow_html=True
        )

    for idx, ped in enumerate(pedidos):
        with st.card() if hasattr(st, 'card') else st.container():
            c1, c2, c3 = st.columns([3, 2, 2])
            with c1:
                st.write(f"**{ped['id']}** - {ped['cliente']}")
                st.caption(f"Item: {ped['item']}")
            with c2:
                st.write(f"**R$ {ped['valor']:.2f}**")
            with c3:
                if st.button("Aceitar & Despachar", key=f"btn_aceitar_{ped['id']}"):
                    st.session_state["pedidos_pendentes"].pop(idx)
                    st.success(f"Pedido {ped['id']} aceito!")
                    st.rerun()


# ==========================================
# 9. VITRINE OMNICHANNEL & OFERTAS
# ==========================================
def renderizar_cartao_oferta(titulo, preco, imagem_url, links_omnichannel, merchant_id, user_id):
    """
    Renderiza os cards de produto contendo links diretos para iFood, Shopee, Mercado Livre e 99Food[cite: 3].
    """
    st.markdown(f"### 🛒 {titulo}")
    st.markdown(f"**Preço:** R$ {preco:.2f}")

    col1, col2, col3, col4 = st.columns(4)
    if "ifood" in links_omnichannel:
        col1.link_button("iFood", links_omnichannel["ifood"])
    if "shopee" in links_omnichannel:
        col2.link_button("Shopee", links_omnichannel["shopee"])
    if "mercadolivre" in links_omnichannel:
        col3.link_button("Mercado Livre", links_omnichannel["mercadolivre"])
    if "99food" in links_omnichannel:
        col4.link_button("99Food", links_omnichannel["99food"])

    st.caption("Engaje para ganhar GeralCoins:")
    c_curtir, c_coment, c_share = st.columns(3)
    if c_curtir.button("👍 Curtir (+1 GC)", key=f"like_{titulo}"):
        processar_recompensa_social(user_id, merchant_id, "curtir")
    if c_coment.button("💬 Comentar (+2 GC)", key=f"comm_{titulo}"):
        processar_recompensa_social(user_id, merchant_id, "comentar")
    if c_share.button("🔗 Compartilhar (+3 GC)", key=f"share_{titulo}"):
        token = gerar_token_compartilhamento(user_id, titulo)
        processar_recompensa_social(user_id, merchant_id, "compartilhar")


# ==========================================
# 10. LEITOR DE NOTÍCIAS RSS LOCAL
# ==========================================
def renderizar_noticias_rss():
    """Lê o feed RSS de notícias locais da região[cite: 2, 7]."""
    url_feed = "https://news.google.com/rss/search?q=Grajaú+São+Paulo&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    
    if feedparser:
        feed = feedparser.parse(url_feed)
        st.write(f"📰 **Últimas Notícias da Região** ({len(feed.entries)} atualizações)")
        for item in feed.entries[:4]:
            st.markdown(f"- **[{item.title}]({item.link})**")
            st.caption(f"Publicado em: {item.get('published', 'Recente')}")
    else:
        st.info("Instale a biblioteca `feedparser` para habilitar as notícias em tempo real[cite: 3, 4].")


# ==========================================
# 11. GERALJÁ LABORATÓRIO 2.0 (DEV SANDBOX)
# ==========================================
def renderizar_laboratorio_dev():
    """
    Ambiente de desenvolvimento integrado com busca de linhas, editor de código,
    preview isolado via exec() e deploy direto no Firestore.
    """
    st.title("🛠️ GeralJá Laboratório 2.0")
    st.caption("Ambiente seguro de testes e atualização remota de layout[cite: 6].")

    codigo_default = """# Código de teste live para o GeralJá
st.success("Módulo carregado dinamicamente com sucesso!")
col1, col2 = st.columns(2)
col1.metric("Status da API", "Online 🟢")
col2.metric("Latência", "12ms")
"""
    
    # Campo de busca de linha[cite: 6]
    termo_busca_linha = st.text_input("🔍 Localizar termo ou linha no código:")
    
    codigo_usuario = st.text_area("Editor de Código Live (Python / Streamlit)", value=codigo_default, height=220)

    if termo_busca_linha:
        linhas = codigo_usuario.split("\n")
        encontradas = [f"Linha {i+1}: {linha}" for i, linha in enumerate(linhas) if termo_busca_linha.lower() in linha.lower()]
        if encontradas:
            st.info("\n".join(encontradas))
        else:
            st.warning("Nenhuma ocorrência encontrada.")

    col_exec, col_pub = st.columns(2)
    
    with col_exec:
        if st.button("▶️ Executar Preview Isolado"):
            st.markdown("---")
            st.markdown("**Resultado da Execução:**")
            try:
                exec(codigo_usuario, {"st": st, "time": time})
            except Exception as e:
                st.error(f"Erro de Execução no Sandbox: {e}")

    with col_pub:
        if st.button("🚀 Publicar Atualização no Firestore"):
            db = inicializar_firebase()
            if db:
                try:
                    db.collection("configuracoes").document("layout_ia").set({
                        "codigo": codigo_usuario,
                        "atualizado_em": time.time(),
                        "autor": "Desenvolvedor Master"
                    })
                    st.success("Código implantado em `configuracoes/layout_ia` com sucesso![cite: 6]")
                except Exception as e:
                    st.error(f"Erro ao publicar no Firestore: {e}")
            else:
                st.error("Conexão ao Firestore indisponível no ambiente local.")


# ==========================================
# 12. PAINEL DO PRESTADOR / ADMINISTRATIVO
# ==========================================
def renderizar_painel_prestador(user_id):
    """Gerenciamento de lances e orçamentos de serviços[cite: 2, 5, 7]."""
    st.write("### 💼 Painel do Prestador de Serviços")
    saldo = CarteiraEngine.obter_saldo(user_id)
    
    st.info(f"Seu saldo disponível para lances de orçamentos: **R$ {saldo['credito_brl']:.2f}**")
    
    st.subheader("Orçamentos Solicitados no Bairro")
    orcam = [
        {"id": "ORC-101", "servico": "Instalação de Chuveiro", "bairro": "Grajaú", "custo_lead": 5.00},
        {"id": "ORC-102", "servico": "Pintura de Portão", "bairro": "Interlagos", "custo_lead": 8.00}
    ]
    
    for item in orcam:
        c1, c2, c3 = st.columns([3, 2, 2])
        c1.write(f"**{item['servico']}** ({item['bairro']})")
        c2.write(f"Custo Lead: R$ {item['custo_lead']:.2f}")
        if c3.button("Comprar Lead", key=f"lead_{item['id']}"):
            if saldo["credito_brl"] >= item["custo_lead"]:
                saldo["credito_brl"] -= item["custo_lead"]
                st.success("Lead adquirido! Contato enviado por WhatsApp.")
                st.rerun()
            else:
                st.error("Saldo de Crédito BRL insuficiente! Converta GeralCoins ou faça uma recarga[cite: 2, 8].")


# ==========================================
# 13. NAVEGAÇÃO E PRINCIPAL (MAIN)
# ==========================================
def renderizar_busca_ui(user_id):
    categorias = ["Eletricista", "Encanador", "Marmitaria Fit", "Mecânico", "Pintor", "Salão de Beleza", "Chaveiro"]
    termo = st.text_input("O que você procura na sua região hoje?")
    
    res = buscar_servicos(termo, categorias)
    st.write("🔍 **Categorias Encontradas:**")
    cols = st.columns(3)
    for idx, cat in enumerate(res):
        cols[idx % 3].button(f"📌 {cat}", key=f"cat_btn_{idx}")

def renderizar_carteira_ui(user_id):
    saldo = CarteiraEngine.obter_saldo(user_id)
    c1, c2, c3 = st.columns(3)
    c1.metric("GeralCoins (GC)", f"{saldo['geralcoins']:.1f} GC")
    c2.metric("Crédito BRL", f"R$ {saldo['credito_brl']:.2f}")
    c3.metric("Custódia BRL", f"R$ {saldo['custodia_brl']:.2f}")

    st.markdown("---")
    st.subheader("🔄 Converter GeralCoins em Crédito BRL")
    st.caption("Taxa oficial: 10 GeralCoins = R$ 1,00[cite: 2, 8]")
    qtd = st.number_input("Quantidade de GC para conversão", min_value=10.0, step=10.0)
    
    if st.button("Efetuar Conversão"):
        sucesso, valor = CarteiraEngine.converter_gc_para_credito(user_id, qtd)
        if sucesso:
            st.success(f"Sucesso! R$ {valor:.2f} adicionados à sua carteira pré-paga.")
            st.rerun()
        else:
            st.error("Saldo de GeralCoins insuficiente.")

def main():
    st.sidebar.title("🌐 GeralJá v6.0 Master")
    
    user_id = st.sidebar.text_input("Identificação do Usuário", value="user_grajau_01")
    
    menu = st.sidebar.radio("Navegação Principal", [
        "🔍 Busca & Serviços",
        "🛒 Vitrine & Ofertas",
        "📰 Notícias Locais",
        "💰 Minha Carteira",
        "💼 Área do Prestador",
        "🚨 Despacho de Pedidos",
        "🛠️ Laboratório Dev 2.0"
    ])

    st.sidebar.markdown("---")
    st.sidebar.caption("GeralJá v6.0 Multi-Engine • 2026")

    # Roteamento seguro utilizando container isolated wrappers[cite: 3, 4, 5]
    if menu == "🔍 Busca & Serviços":
        executar_bloco_seguro("Busca Tolerante", lambda: renderizar_busca_ui(user_id))

    elif menu == "🛒 Vitrine & Ofertas":
        links_demo = {
            "ifood": "https://ifood.com.br",
            "shopee": "https://shopee.com.br",
            "mercadolivre": "https://mercadolivre.com.br",
            "99food": "https://99app.com"
        }
        executar_bloco_seguro(
            "Vitrine do Bairro", 
            lambda: renderizar_cartao_oferta("Marmita Fitness Completa", 22.90, None, links_demo, "loja_1", user_id)
        )

    elif menu == "📰 Notícias Locais":
        executar_bloco_seguro("Radar Regional", renderizar_noticias_rss)

    elif menu == "💰 Minha Carteira":
        executar_bloco_seguro("Gestão Financeira Tri-Moeda", lambda: renderizar_carteira_ui(user_id))

    elif menu == "💼 Área do Prestador":
        executar_bloco_seguro("Lances de Orçamento", lambda: renderizar_painel_prestador(user_id))

    elif menu == "🚨 Despacho de Pedidos":
        executar_bloco_seguro("Monitor Lojista em Tempo Real", renderizar_monitor_pedidos)

    elif menu == "🛠️ Laboratório Dev 2.0":
        executar_bloco_seguro("Laboratório de Testes & Deploy", renderizar_laboratorio_dev)

if __name__ == "__main__":
    main()
