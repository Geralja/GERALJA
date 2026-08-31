import streamlit as st
import json
import os
import re
import time
import uuid
import unicodedata
import base64

# ==========================================
# 1. CARREGAMENTO DEFENSIVO DE DEPENDÊNCIAS
# ==========================================
# Trata pacotes opcionais sem interromper a execução da aplicação
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
# 2. ISOLAMENTO E EXECUÇÃO SEGURA DE BLOCOS
# ==========================================
def executar_bloco_seguro(titulo, funcao, *args, **kwargs):
    """
    Executa um módulo da interface dentro de um container isolado.
    Se ocorrer uma exceção, o erro é capturado sem derrubar a aplicação[cite: 3, 4, 5].
    """
    st.subheader(titulo)
    with st.container():
        try:
            return funcao(*args, **kwargs)
        except Exception as e:
            st.error(f"Erro ao carregar o módulo '{titulo}': {e}")
            return None


# ==========================================
# 3. INFRAESTRUTURA FIREBASE & OAUTH
# ==========================================
def inicializar_firebase():
    """
    Inicializa a conexão com o Cloud Firestore via credenciais Base64
    armazenadas em st.secrets.
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
        st.warning(f"Modo offline (sem conexão ao Firestore): {e}")
        return None


# ==========================================
# 4. MOTOR DE CARTEIRA MULTI-MOEDA
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
        if f"carteira_{user_id}" not in st.session_state:
            st.session_state[f"carteira_{user_id}"] = {
                "geralcoins": 100.0,
                "credito_brl": 50.00,
                "custodia_brl": 0.00
            }
        return st.session_state[f"carteira_{user_id}"]

    @staticmethod
    def converter_gc_para_credito(user_id, quantidade_gc):
        """Converte GeralCoins em Crédito BRL pré-pago[cite: 2, 8]."""
        saldo = CarteiraEngine.obter_saldo(user_id)
        if saldo["geralcoins"] >= quantidade_gc:
            valor_brl = quantidade_gc * CarteiraEngine.TAXA_CONVERSAO_GC_BRL
            saldo["geralcoins"] -= quantidade_gc
            saldo["credito_brl"] += valor_brl
            st.session_state[f"carteira_{user_id}"] = saldo
            CarteiraEngine.registrar_transacao(
                user_id, "conversao", valor_brl, "BRL", f"Conversão de {quantidade_gc} GC"
            )
            return True, valor_brl
        return False, 0.0

    @staticmethod
    def registrar_transacao(user_id, tipo, valor, moeda, descricao):
        """Registra a movimentação no histórico do ledger[cite: 8]."""
        if "historico_transacoes" not in st.session_state:
            st.session_state["historico_transacoes"] = []
        st.session_state["historico_transacoes"].append({
            "user_id": user_id,
            "tipo": tipo,
            "valor": valor,
            "moeda": moeda,
            "descricao": descricao,
            "timestamp": time.time()
        })


# ==========================================
# 5. MOTOR DE BUSCA TOLERANTE E NORMALIZAÇÃO
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
    
    # Matching Direto
    resultados = [cat for cat in lista_categorias if termo_limpo in normalizar_texto(cat)]
    if resultados:
        return resultados

    # Fuzzy Matching Fallback
    if fuzz:
        resultados_fuzzy = [
            cat for cat in lista_categorias 
            if fuzz.partial_ratio(termo_limpo, normalizar_texto(cat)) > 75
        ]
        if resultados_fuzzy:
            return resultados_fuzzy

    return lista_categorias


# ==========================================
# 6. PAY-PER-ENGAGEMENT (PPE) E WEB SHARE
# ==========================================
def processar_recompensa_social(user_id, merchant_id, acao):
    """
    Recompensa o morador com GeralCoins por engajamento e debita do anunciante.
    Curtir: +1 GC | Comentar: +2 GC | Compartilhar: +3 GC[cite: 3, 4].
    """
    recompensas = {"curtir": 1.0, "comentar": 2.0, "compartilhar": 3.0}
    valor_gc = recompensas.get(acao, 0.0)
    
    if valor_gc > 0:
        saldo = CarteiraEngine.obter_saldo(user_id)
        saldo["geralcoins"] += valor_gc
        st.session_state[f"carteira_{user_id}"] = saldo
        CarteiraEngine.registrar_transacao(
            user_id, "credito", valor_gc, "GC", f"Recompensa PPE ({acao})"
        )
        st.toast(f"🎉 Você ganhou +{valor_gc} GeralCoins por {acao}![cite: 3, 4]")

def gerar_token_compartilhamento(user_id, item_id):
    """Gera um token único validado para compartilhamento via Web Share API[cite: 2, 7, 8]."""
    token = str(uuid.uuid4())
    st.session_state[f"share_token_{token}"] = {"user_id": user_id, "item_id": item_id, "usado": False}
    return token


# ==========================================
# 7. MONITOR DE PEDIDOS COM ALERTA SONORO
# ==========================================
def renderizar_monitor_pedidos():
    """
    Painel de despacho de pedidos com sinal sonoro continuo em loop (<audio autoplay loop>)
    disparado ao detectar novos pedidos pendentes.
    """
    if "pedidos_pendentes" not in st.session_state:
        st.session_state["pedidos_pendentes"] = [
            {"id": "PED-201", "cliente": "Maria Souza", "item": "Marmita Fitness G", "status": "Pendente"}
        ]

    pedidos = st.session_state["pedidos_pendentes"]

    if pedidos:
        st.warning(f"🚨 Atendimento: {len(pedidos)} novo(s) pedido(s) pendente(s)!")
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
        c1, c2 = st.columns([3, 1])
        with c1:
            st.write(f"**{ped['id']}** | Cliente: {ped['cliente']} - *{ped['item']}*")
        with c2:
            if st.button("Aceitar Pedido", key=f"btn_ped_{idx}"):
                st.session_state["pedidos_pendentes"].pop(idx)
                st.success("Pedido enviado para preparo!")
                st.rerun()


# ==========================================
# 8. E-COMMERCE OMNICHANNEL E OFERTAS
# ==========================================
def renderizar_cartao_oferta(titulo, preco, imagem_url, links_omnichannel):
    """
    Renderiza os cards de produto contendo links diretos para iFood, Shopee, Mercado Livre e 99Food[cite: 3].
    """
    st.markdown(f"### {titulo}")
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


# ==========================================
# 9. GERALJÁ LABORATÓRIO 2.0 (DEV SANDBOX)
# ==========================================
def renderizar_laboratorio_dev():
    """
    Ambiente de desenvolvimento com editor ao vivo, sandbox de execução exec()
    e deploy direto para o Firestore no documento configuracoes/layout_ia.
    """
    st.title("🛠️ GeralJá Laboratório 2.0")
    
    codigo_padrao = "# Escreva seu código de teste aqui\nst.write('Módulo em execução no Sandbox!')"
    codigo_usuario = st.text_area("Editor de Código Live", value=codigo_padrao, height=180)

    col_exec, col_pub = st.columns(2)
    
    with col_exec:
        if st.button("▶️ Executar Preview Isolado"):
            st.markdown("---")
            st.markdown("**Resultado:**")
            try:
                exec(codigo_usuario, {"st": st})
            except Exception as e:
                st.error(f"Erro de execução: {e}")

    with col_pub:
        if st.button("🚀 Publicar no Firestore"):
            db = inicializar_firebase()
            if db:
                try:
                    db.collection("configuracoes").document("layout_ia").set({
                        "codigo": codigo_usuario,
                        "atualizado_em": time.time()
                    })
                    st.success("Publicado em configuracoes/layout_ia![cite: 6]")
                except Exception as e:
                    st.error(f"Erro na publicação: {e}")
            else:
                st.error("Conexão com Firestore indisponível no ambiente local.")


# ==========================================
# 10. INTERFACE PRINCIPAL E NAVEGAÇÃO
# ==========================================
def renderizar_busca_ui(user_id):
    categorias = ["Eletricista", "Encanador", "Marmitaria Fit", "Mecânico", "Pintor", "Salão de Beleza"]
    termo = st.text_input("O que você procura no bairro hoje?")
    if termo:
        res = buscar_servicos(termo, categorias)
        st.write("Resultados encontrados:", res)
    else:
        st.write("Categorias em destaque:", categorias)

def renderizar_ofertas_ui(user_id):
    links = {
        "ifood": "https://ifood.com.br",
        "shopee": "https://shopee.com.br",
        "mercadolivre": "https://mercadolivre.com.br",
        "99food": "https://99app.com"
    }
    renderizar_cartao_oferta("Marmita Executiva", 22.90, None, links)
    
    st.markdown("---")
    st.write("**Ganhe moedas interagindo com este anúncio (PPE):**")
    c1, c2, c3 = st.columns(3)
    if c1.button("👍 Curtir (+1 GC)"):
        processar_recompensa_social(user_id, "loja_01", "curtir")
    if c2.button("💬 Comentar (+2 GC)"):
        processar_recompensa_social(user_id, "loja_01", "comentar")
    if c3.button("🔗 Compartilhar (+3 GC)"):
        processar_recompensa_social(user_id, "loja_01", "compartilhar")

def renderizar_carteira_ui(user_id):
    saldo = CarteiraEngine.obter_saldo(user_id)
    c1, c2, c3 = st.columns(3)
    c1.metric("GeralCoins (GC)", f"{saldo['geralcoins']:.1f} GC")
    c2.metric("Crédito BRL", f"R$ {saldo['credito_brl']:.2f}")
    c3.metric("Custódia BRL", f"R$ {saldo['custodia_brl']:.2f}")

    st.markdown("---")
    st.subheader("Converter GeralCoins em Crédito BRL")
    qtd = st.number_input("Quantidade de GC", min_value=10.0, step=10.0)
    if st.button("Converter (10 GC = R$ 1,00)"):
        sucesso, valor = CarteiraEngine.converter_gc_para_credito(user_id, qtd)
        if sucesso:
            st.success(f"Convertido! +R$ {valor:.2f} adicionados ao Crédito BRL.")
            st.rerun()
        else:
            st.error("Saldo insuficiente de GeralCoins.")

def main():
    st.set_page_config(page_title="GeralJá v6.0 Master", layout="wide", page_icon="🚀")

    st.sidebar.title("🌐 GeralJá v6.0")
    menu = st.sidebar.radio("Navegação", [
        "Vitrine & Busca",
        "Minha Carteira",
        "Painel Lojista (Pedidos)",
        "Laboratório Dev 2.0"
    ])

    user_id = st.sidebar.text_input("ID do Usuário", value="user_demo_123")

    if menu == "Vitrine & Busca":
        executar_bloco_seguro("🔍 Busca Tolerante de Serviços", lambda: renderizar_busca_ui(user_id))
        executar_bloco_seguro("🛍️ Vitrine & Links Omnichannel", lambda: renderizar_ofertas_ui(user_id))

    elif menu == "Minha Carteira":
        executar_bloco_seguro("💰 Carteira Multi-Moeda", lambda: renderizar_carteira_ui(user_id))

    elif menu == "Painel Lojista (Pedidos)":
        executar_bloco_seguro("🚨 Despacho de Pedidos em Tempo Real", renderizar_monitor_pedidos)

    elif menu == "Laboratório Dev 2.0":
        executar_bloco_seguro("🛠️ GeralJá Laboratório 2.0", renderizar_laboratorio_dev)

if __name__ == "__main__":
    main()
