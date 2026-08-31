import streamlit as st
import json
import base64
import unicodedata
import re
import traceback
import time
from datetime import datetime, timezone

# ==============================================================================
# 1. IMPORTS DEFENSIVOS E CARREGAMENTO DE DEPENDÊNCIAS
# ==============================================================================
# Trata pacotes opcionais para evitar paradas críticas do aplicativo.

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    HAS_FIREBASE = True
except ImportError:
    HAS_FIREBASE = False

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False

try:
    from difflib import SequenceMatcher
    HAS_DIFFLIB = True
except ImportError:
    HAS_DIFFLIB = False


# ==============================================================================
# 2. INICIALIZAÇÃO DO FIREBASE E SERVIÇOS DE NUVEM
# ==============================================================================
# Decodificação de credenciais em Base64 armazenadas no st.secrets.

@st.cache_resource
def inicializar_firebase():
    """Inicializa a conexão Firestore utilizando credenciais em Base64 isoladas[cite: 2, 7, 8]."""
    if not HAS_FIREBASE:
        return None
    try:
        if not firebase_admin._apps:
            if "FIREBASE_CREDENTIALS_BASE64" in st.secrets:
                creds_b64 = st.secrets["FIREBASE_CREDENTIALS_BASE64"]
                creds_json = json.loads(base64.b64decode(creds_b64).decode("utf-8"))
                cred = credentials.Certificate(creds_json)
                firebase_admin.initialize_app(cred)
            else:
                firebase_admin.initialize_app()
        return firestore.client()
    except Exception as e:
        st.error(f"Erro ao conectar ao Firestore: {str(e)}")
        return None

db = inicializar_firebase()


# ==============================================================================
# 3. MOTOR DE ESTILIZAÇÃO E INTERFACE DE USUÁRIO (CSS)
# ==============================================================================
def injetar_css_global(modo_noite=True):
    """Aplica o tema CSS dinâmico (modo escuro ou claro) na aplicação[cite: 2, 5, 9]."""
    bg_color = "#0e1117" if modo_noite else "#ffffff"
    text_color = "#ffffff" if modo_noite else "#000000"
    card_bg = "#1e222a" if modo_noite else "#f0f2f6"
    
    css = f"""
    <style>
        .stApp {{
            background-color: {bg_color};
            color: {text_color};
        }}
        .card-servico {{
            background-color: {card_bg};
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
            border: 1px solid #333;
        }}
        .badge-gc {{
            background-color: #ffd700;
            color: #000;
            font-weight: bold;
            padding: 2px 8px;
            border-radius: 5px;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


# ==============================================================================
# 4. MOTOR DA CARTEIRA MULTIMOEDAS (CarteiraEngine)
# ==============================================================================
# Gerencia GeralCoins, Crédito BRL e Custódia BRL. Taxa de conversão: 10 GC = R$ 1,00[cite: 2, 8].

class CarteiraEngine:
    @staticmethod
    def obter_saldo(usuario_id):
        """Retorna os saldos das três carteiras do usuário[cite: 2, 3]."""
        if not db:
            return {"geralcoins": 0, "credito_brl": 0.0, "custodia_brl": 0.0}
        
        doc_ref = db.collection("carteiras").document(usuario_id)
        doc = doc_ref.get()
        if doc.exists:
            dados = doc.to_dict()
            return {
                "geralcoins": dados.get("geralcoins", 0),
                "credito_brl": dados.get("credito_brl", 0.0),
                "custodia_brl": dados.get("custodia_brl", 0.0)
            }
        return {"geralcoins": 0, "credito_brl": 0.0, "custodia_brl": 0.0}

    @staticmethod
    def registrar_transacao(usuario_id, moeda, valor, tipo, descricao=""):
        """Registra movimentações financeiras com auditoria detalhada[cite: 8]."""
        if not db:
            return False
        try:
            carteira_ref = db.collection("carteiras").document(usuario_id)
            transacao_ref = db.collection("transacoes").document()
            
            # Atualização atômica simplificada
            carteira = carteira_ref.get().to_dict() or {"geralcoins": 0, "credito_brl": 0.0, "custodia_brl": 0.0}
            carteira[moeda] = carteira.get(moeda, 0) + valor
            
            carteira_ref.set(carteira, merge=True)
            transacao_ref.set({
                "usuario_id": usuario_id,
                "moeda": moeda,
                "valor": valor,
                "tipo": tipo,
                "descricao": descricao,
                "data": datetime.now(timezone.utc)
            })
            return True
        except Exception as e:
            st.error(f"Erro na transação: {str(e)}")
            return False

    @staticmethod
    def converter_gc_para_brl(usuario_id, gc_quantidade):
        """Converte GeralCoins em Crédito BRL na proporção 10 GC = R$ 1.00[cite: 2, 8]."""
        if gc_quantidade <= 0 or gc_quantidade % 10 != 0:
            return False, "A quantidade deve ser múltipla de 10 GeralCoins."
            
        saldos = CarteiraEngine.obter_saldo(usuario_id)
        if saldos["geralcoins"] < gc_quantidade:
            return False, "Saldo de GeralCoins insuficiente."
            
        valor_brl = (gc_quantidade / 10) * 1.0
        
        # Debita GC e Credita BRL[cite: 2, 8]
        CarteiraEngine.registrar_transacao(usuario_id, "geralcoins", -gc_quantidade, "conversao", "Conversão para BRL")
        CarteiraEngine.registrar_transacao(usuario_id, "credito_brl", valor_brl, "conversao", "Resgate de GeralCoins")
        return True, f"Sucesso! R$ {valor_brl:.2f} adicionados aos seus créditos."


# ==============================================================================
# 5. MOTOR DE BUSCA TOLERANTE E INTEGRAÇÃO GROQ IA
# ==============================================================================
# Normalização NFKD, fuzzy matching e fallback para Llama 3 via Groq[cite: 2, 7, 8].

def normalizar_texto(texto):
    """Remove acentos, pontuações e converte texto para caixa baixa[cite: 2, 7, 8]."""
    if not texto:
        return ""
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    return re.sub(r'[^a-zA-Z0-9\s]', '', texto).lower().strip()

def busca_tolerante_servicos(termo_busca, categorias_disponiveis):
    """Executa busca por correspondência exata, similaridade e consulta cached na IA[cite: 2, 7, 8]."""
    termo_norm = normalizar_texto(termo_busca)
    
    # 1. Correspondência Exata / Parcial[cite: 2, 7]
    resultados = [cat for cat in categorias_disponiveis if termo_norm in normalizar_texto(cat)]
    if resultados:
        return resultados
        
    # 2. Similaridade Fuzzy (difflib)[cite: 2, 7]
    if HAS_DIFFLIB:
        for cat in categorias_disponiveis:
            ratio = SequenceMatcher(None, termo_norm, normalizar_texto(cat)).ratio()
            if ratio > 0.6:
                resultados.append(cat)
        if resultados:
            return resultados

    # 3. Fallback com IA Groq Llama 3[cite: 2, 7, 8]
    if HAS_GROQ and "GROQ_API_KEY" in st.secrets:
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            prompt = f"O usuário buscou por '{termo_busca}'. Qual destas categorias melhor se encaixa? {categorias_disponiveis}. Responda apenas com o nome exato da categoria."
            chat = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
            )
            resposta = chat.choices[0].message.content.strip()
            if resposta in categorias_disponiveis:
                return [resposta]
        except Exception:
            pass

    return []


# ==============================================================================
# 6. ENGAJAMENTO SOCIAL (PAY-PER-ENGAGEMENT - PPE) E TOKENS DE COMPARTILHAMENTO
# ==============================================================================
# Recompensas monetizadas por ações sociais financiadas pelos comerciantes[cite: 3, 4].

def gerar_token_compartilhamento(usuario_id, anuncio_id):
    """Gera um token único no Firestore para validar compartilhamento via Web Share API[cite: 2, 7, 8]."""
    if not db:
        return None
    token = f"tok_{usuario_id}_{int(time.time())}"
    db.collection("tokens_compartilhamento").document(token).set({
        "usuario_id": usuario_id,
        "anuncio_id": anuncio_id,
        "usado": False,
        "criado_em": datetime.now(timezone.utc)
    })
    return token

def validar_token_compartilhamento(token):
    """Valida o token de compartilhamento e concede a recompensa em GeralCoins ao usuário[cite: 2, 7, 8]."""
    if not db:
        return False
    doc_ref = db.collection("tokens_compartilhamento").document(token)
    doc = doc_ref.get()
    if doc.exists and not doc.to_dict().get("usado"):
        dados = doc.to_dict()
        doc_ref.update({"usado": True})
        # Credita +3 GC por compartilhamento verificado[cite: 3, 4]
        CarteiraEngine.registrar_transacao(dados["usuario_id"], "geralcoins", 3, "ppe_recompensa", "Recompensa por Compartilhamento")
        return True
    return False


# ==============================================================================
# 7. EXECUTOR ISOLADO E SEGURO DE BLOCOS (Fault-Tolerant Execution)
# ==============================================================================
# Garante a continuidade do app mesmo em caso de falha em um módulo.

def executar_bloco_seguro(funcao, *args, **kwargs):
    """Envolve a execução da UI em um contêiner isolado com tratamento de exceção[cite: 3, 4, 5]."""
    with st.container():
        try:
            return funcao(*args, **kwargs)
        except Exception as e:
            st.error(f"⚠️ Erro ao carregar este bloco: {str(e)}")
            with st.expander("Detalhes técnicos do erro"):
                st.code(traceback.format_exc())


# ==============================================================================
# 8. MÓDULOS DE INTERFACE E FUNCIONALIDADES
# ==============================================================================

def exibir_painel_pedidos_comerciante(comerciante_id):
    """Exibe o painel de ordens em tempo real com alerta sonoro em loop para novos pedidos."""
    st.subheader("📦 Painel de Pedidos em Tempo Real")
    
    # Exemplo simulado de consulta de pedidos pendentes
    pedidos_pendentes = True  # Alterne conforme consulta ao Firestore
    
    if pedidos_pendentes:
        # Toca sinal sonoro dinâmico via áudio HTML autoplay[cite: 3]
        st.markdown(
            """
            <audio autoplay loop>
                <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg">
            </audio>
            """, 
            unsafe_allow_html=True
        )
        st.warning("🔔 Você tem novos pedidos aguardando confirmação!")


def exibir_módulo_ppe_anuncios(usuario_id, anuncio):
    """Módulo Pay-Per-Engagement com links para e-commerce e botões sociais[cite: 3, 4]."""
    st.markdown(f"### {anuncio.get('titulo', 'Anúncio em Destaque')}")
    st.write(anuncio.get('descricao', ''))
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("👍 Curtir (+1 GC)"):
            CarteiraEngine.registrar_transacao(usuario_id, "geralcoins", 1, "ppe_curtida", "Recompensa por Curtida")
            st.toast("Você ganhou 1 GeralCoin!")
            
    with col2:
        if st.button("💬 Comentar (+2 GC)"):
            CarteiraEngine.registrar_transacao(usuario_id, "geralcoins", 2, "ppe_comentario", "Recompensa por Comentário")
            st.toast("Você ganhou 2 GeralCoins!")

    with col3:
        if st.button("🔗 Compartilhar (+3 GC)"):
            token = gerar_token_compartilhamento(usuario_id, anuncio.get("id", "123"))
            st.code(f"https://geralja.com.br/?token={token}")
            st.info("Envie o link para um amigo para validar seus pontos!")

    # Links Omnichannel de e-commerce e entregas[cite: 3]
    st.markdown("**Compre diretamente nas plataformas:**")
    cols_ecom = st.columns(4)
    cols_ecom[0].link_button("iFood", anuncio.get("link_ifood", "https://ifood.com.br"))
    cols_ecom[1].link_button("Shopee", anuncio.get("link_shopee", "https://shopee.com.br"))
    cols_ecom[2].link_button("Mercado Livre", anuncio.get("link_meli", "https://mercadolivre.com.br"))
    cols_ecom[3].link_button("99Food", anuncio.get("link_99", "https://99app.com"))


def laboratorio_dev():
    """Ambiente de desenvolvimento GeralJá Laboratório 2.0 com editor dinâmico."""
    st.title("🧪 GeralJá Laboratório 2.0")
    st.write("Editor ao vivo e publicação direta nas configurações do Firestore[cite: 6].")
    
    codigo = st.text_area("Código Python / Streamlit:", value="st.write('Teste ao vivo no Laboratório!')", height=200)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Executar Preview"):
            try:
                exec(codigo)
            except Exception as e:
                st.error(f"Erro na execução: {str(e)}")
                
    with col2:
        if st.button("🚀 Publicar no Firestore"):
            if db:
                db.collection("configuracoes").document("layout_ia").set({
                    "codigo": codigo,
                    "atualizado_em": datetime.now(timezone.utc)
                })
                st.success("Código implantado com sucesso no Firestore!")


# ==============================================================================
# 9. NAVEGAÇÃO E FLUXO PRINCIPAL DA APLICAÇÃO
# ==============================================================================
def main():
    injetar_css_global(modo_noite=True)
    
    # Validação de token via query params URL[cite: 2, 7, 8]
    query_params = st.query_params
    if "token" in query_params:
        if validar_token_compartilhamento(query_params["token"]):
            st.success("Recompensa de compartilhamento resgatada com sucesso!")

    st.sidebar.title("🌐 GeralJá v6.0")
    usuario_id = st.sidebar.text_input("ID do Usuario Logado:", value="user_demo_123")
    
    # Exibição dos Saldos da Carteira[cite: 2, 3]
    saldos = CarteiraEngine.obter_saldo(usuario_id)
    st.sidebar.markdown(f"""
    **Saldos da Conta:**
    - 🪙 GeralCoins: **{saldos['geralcoins']} GC**
    - 💵 Crédito BRL: **R$ {saldos['credito_brl']:.2f}**
    - 🔒 Custódia BRL: **R$ {saldos['custodia_brl']:.2f}**
    """)
    
    # Conversão rápida na Barra Lateral[cite: 2, 8]
    with st.sidebar.expander("💱 Convertor de Moedas"):
        gc_input = st.number_input("Qtd. GeralCoins (múltiplo de 10)", min_value=10, step=10)
        if st.button("Convert em R$"):
            sucesso, msg = CarteiraEngine.converter_gc_para_brl(usuario_id, gc_input)
            if sucesso:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    menu = st.sidebar.radio("Navegação", ["Buscar Serviços", "Ofertas & Engajamento", "Comerciante", "Laboratório Dev"])
    
    if menu == "Buscar Serviços":
        st.header("🔎 Busca Tolerante de Serviços")
        categorias = ["Eletricista", "Encanador", "Pintor", "Mecânico", "Manicure", "Pedreiro"]
        termo = st.text_input("O que você precisa hoje?")
        if termo:
            resultados = busca_tolerante_servicos(termo, categorias)
            if resultados:
                st.success(f"Categorias encontradas: {', '.join(resultados)}")
            else:
                st.warning("Nenhuma categoria encontrada.")

    elif menu == "Ofertas & Engajamento":
        st.header("📢 Vitrine de Ofertas")
        anuncio_demo = {
            "id": "anuncio_001",
            "titulo": "Promoção Especial de Pizzas",
            "descricao": "Peça qualquer pizza grande com 20% de desconto nesta semana!"
        }
        executar_bloco_seguro(exibir_módulo_ppe_anuncios, usuario_id, anuncio_demo)

    elif menu == "Comerciante":
        executar_bloco_seguro(exibir_painel_pedidos_comerciante, usuario_id)

    elif menu == "Laboratório Dev":
        executar_bloco_seguro(laboratorio_dev)

if __name__ == "__main__":
    main()
