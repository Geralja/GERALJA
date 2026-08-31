# -*- coding: utf-8 -*-
# ==============================================================================
# GERALJÁ: SISTEMA OPERACIONAL MODULAR & ECOSSISTEMA DE SERVIÇOS (v10.0 MASTER)
# Arquitetura por Containers Isolados | Proteção Total contra KeyError
# Mídia + Marketplace Híbrido + Carteira Multi-Moedas + Gamificação + Análise IA
# ==============================================================================

import base64
from datetime import datetime
import difflib
import hashlib
import io
import json
import math
import os
import re
import sys
import time
import unicodedata
import urllib.parse
from urllib.parse import quote

import firebase_admin
from firebase_admin import credentials, firestore
from google_auth_oauthlib.flow import Flow
import google.generativeai as genai
from groq import Groq
import pandas as pd
from PIL import Image
import pytz
import requests
import streamlit as st
import streamlit.components.v1 as components

# --- IMPORTAÇÕES DEFENSIVAS DE COMPONENTES EXTERNOS ---
try:
    import feedparser
except ImportError:
    feedparser = None

try:
    from streamlit_js_eval import get_geolocation, streamlit_js_eval
except ImportError:
    get_geolocation = None


# ==============================================================================
# 1. ENGENHARIA DE ISOLAMENTO: EXECUTOR SEGURO DE BLOCOS (INQUEBRÁVEL)
# ==============================================================================
def executar_bloco_seguro(nome_bloco: str, funcao_bloco, *args, container=None, **kwargs):
    """Executa qualquer funcionalidade dentro de um container isolado.
    Garante que se um módulo falhar, o restante da aplicação continue ativo sem derrubar o site.
    """
    alvo = container if container is not None else st
    try:
        with alvo.container():
            funcao_bloco(*args, **kwargs)
    except Exception as e:
        alvo.warning(f"⚠️ Módulo '{nome_bloco}' em manutenção ou desativado temporariamente.")
        with alvo.expander(f"🔍 Detalhes do Erro ({nome_bloco})", expanded=False):
            st.error(f"Falha na execução do módulo: {e}")


# ==============================================================================
# 2. CARREGAMENTO BLINDADO DE SEGREDOS & CREDENCIAIS
# ==============================================================================
def obter_segredo_critico(chave: str):
    if chave in st.secrets:
        return st.secrets[chave]

    try:
        import secret
        if hasattr(secret, chave):
            return getattr(secret, chave)
    except ImportError:
        pass

    st.error(f"🚨 ERRO CRÍTICO DE SEGURANÇA: A credencial '{chave}' é obrigatória no st.secrets ou secret.py.")
    st.stop()


ADMIN_USER = obter_segredo_critico("ADMIN_USER")
ADMIN_PASS = obter_segredo_critico("ADMIN_PASS")
PIX_OFICIAL = obter_segredo_critico("PIX_OFICIAL")
ZAP_ADMIN = obter_segredo_critico("ZAP_ADMIN")
ZAP_VENDAS = obter_segredo_critico("ZAP_VENDAS")

GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", "")
GROQ_KEY = st.secrets.get("GROQ_API_KEY", "")
FB_ID = st.secrets.get("FB_CLIENT_ID", "")
FB_SECRET = st.secrets.get("FB_CLIENT_SECRET", "")
REDIRECT_URI = st.secrets.get("google_auth", {}).get("redirect_uri", "https://geralja-zxiaj2ot56fuzgcz7xhcks.streamlit.app/")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
if GROQ_KEY:
    client_groq = Groq(api_key=GROQ_KEY)


# ==============================================================================
# 3. GERENCIADOR DE IMAGENS RESILIENTE & FALLBACKS BASE64 (CORREÇÃO DE 'IMG')
# ==============================================================================
SVG_PIZZA_FALLBACK = "data:image/svg+xml;base64," + base64.b64encode(b"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400"><rect width="100%" height="100%" fill="#E2E8F0"/><text x="50%" y="50%" font-size="28" font-family="Arial" font-weight="bold" fill="#0F172A" text-anchor="middle" dy=".3em">🍕 Oferta de Gastronomia</text></svg>""").decode()
SVG_SERVICO_FALLBACK = "data:image/svg+xml;base64," + base64.b64encode(b"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400"><rect width="100%" height="100%" fill="#E2E8F0"/><text x="50%" y="50%" font-size="28" font-family="Arial" font-weight="bold" fill="#0F172A" text-anchor="middle" dy=".3em">🚗 Oferta de Serviços</text></svg>""").decode()

def extrair_url_imagem_segura(dicionario_oferta, fallback=SVG_PIZZA_FALLBACK):
    """Busca com segurança qualquer chave de imagem no dicionário sem gerar KeyError."""
    if not isinstance(dicionario_oferta, dict):
        return fallback
    
    for chave in ["img", "foto_url", "imagem", "imagem_url", "foto"]:
        val = dicionario_oferta.get(chave)
        if val and len(str(val).strip()) > 5:
            return str(val).strip()
            
    return fallback


def exibir_imagem_segura(url_ou_b64, legenda="", fallback=SVG_PIZZA_FALLBACK):
    """Exibe imagens protegendo a aplicação contra falhas de rede ou URLs quebradas."""
    if not url_ou_b64 or len(str(url_ou_b64)) < 10:
        st.image(fallback, use_container_width=True, caption=legenda)
        return

    try:
        st.image(url_ou_b64, use_container_width=True, caption=legenda)
    except Exception:
        try:
            st.image(fallback, use_container_width=True, caption=legenda)
        except Exception:
            st.warning("🖼️ Imagem temporariamente indisponível")


def otimizar_imagem(arq, qualidade=60, size=(800, 800)):
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


# ==============================================================================
# 4. UTILITÁRIOS EXTERNOS: CLIMA VIA OPEN-METEO & VIA-CEP
# ==============================================================================
def buscar_clima_local(lat=-23.7028, lon=-46.6872):
    """Obtém a previsão do clima do bairro em tempo real."""
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            temp = res.json()["current_weather"]["temperature"]
            return f"{temp}°C"
    except Exception:
        pass
    return "25°C"


def buscar_cep(cep: str):
    """Preenchimento automático do endereço via BrasilAPI/ViaCEP."""
    cep_limpo = re.sub(r"\D", "", cep)
    if len(cep_limpo) == 8:
        try:
            res = requests.get(f"https://brasilapi.com.br/api/cep/v1/{cep_limpo}", timeout=3)
            if res.status_code == 200:
                return res.json()
        except Exception:
            pass
    return None


# ==============================================================================
# 5. MOTOR DA CARTEIRA, GAMIFICAÇÃO & ANÁLISE DE IA
# ==============================================================================
class GeralJaEngine:
    def __init__(self):
        self.fuso = pytz.timezone("America/Sao_Paulo")

    def sanitizar(self, codigo_bruto):
        if not codigo_bruto:
            return ""
        limpo = codigo_bruto.replace("\u00a0", " ").replace("\xa0", " ")
        return re.sub(r"[^\x20-\x7E\n\t\r]", "", limpo)


engine = GeralJaEngine()
fuso_br = engine.fuso

REGRAS_NIVEL = {
    "Bronze": {"min_xp": 0, "multiplicador": 0.5, "icone": "🥉"},
    "Prata": {"min_xp": 100, "multiplicador": 1.0, "icone": "🥈"},
    "Ouro": {"min_xp": 300, "multiplicador": 1.5, "icone": "🥇"},
    "Diamante": {"min_xp": 700, "multiplicador": 2.0, "icone": "💎"}
}


def calcular_nivel(xp: int):
    """Calcula a categoria de confiança e o multiplicador de ganho do morador."""
    nivel_atual = "Bronze"
    for nivel, dados in REGRAS_NIVEL.items():
        if xp >= dados["min_xp"]:
            nivel_atual = nivel
    return nivel_atual, REGRAS_NIVEL[nivel_atual]


def analisar_sentimento_ia(texto: str) -> str:
    """Classificação de sentimento via Groq/Gemini com fallback em regra."""
    if GROQ_KEY:
        try:
            prompt = f"Analise este comentário de cliente: '{texto}'. Responda unicamente com uma destas palavras: POSITIVO, NEUTRO ou NEGATIVO."
            res = client_groq.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
                temperature=0.1
            )
            resp = res.choices[0].message.content.strip().upper()
            if resp in ["POSITIVO", "NEUTRO", "NEGATIVO"]:
                return resp
        except Exception:
            pass

    texto_lc = texto.lower()
    termos_negativos = ["demorou", "frio", "fria", "pessimo", "ruim", "horrivel", "nunca mais", "odiei", "nojento", "podre", "atraso"]
    if any(t in texto_lc for t in termos_negativos):
        return "NEGATIVO"
    return "POSITIVO"


class CarteiraEngine:
    def __init__(self, db_client):
        self.db = db_client
        self.fuso = pytz.timezone("America/Sao_Paulo")

    def obter_saldos(self, user_id: str):
        ref = self.db.collection("carteiras").document(user_id)
        doc = ref.get()
        if not doc.exists:
            saldos_padrao = {"geralcoin": 20, "credito_brl": 0.0, "custodia_brl": 0.0, "xp": 0, "verificado": True}
            ref.set({"saldos": saldos_padrao, "atualizado_em": datetime.now(self.fuso).isoformat()}, merge=True)
            return saldos_padrao
        
        dados = doc.to_dict().get("saldos", {})
        if "xp" not in dados:
            dados["xp"] = 0
        if "verificado" not in dados:
            dados["verificado"] = True
        return dados

    def movimentar_saldo(self, user_id: str, moeda: str, valor: float, tipo: str, origem: str):
        ref = self.db.collection("carteiras").document(user_id)
        saldos = self.obter_saldos(user_id)
        chave_moeda = moeda.lower()

        saldo_atual = saldos.get(chave_moeda, 0.0)

        if tipo == "DEBITO" and saldo_atual < valor:
            return False, f"⚠️ Saldo insuficiente em {moeda.upper()}."

        novo_saldo = (saldo_atual + valor) if tipo == "CREDITO" else (saldo_atual - valor)
        saldos[chave_moeda] = round(novo_saldo, 2)

        if tipo == "CREDITO" and chave_moeda == "geralcoin":
            saldos["xp"] = saldos.get("xp", 0) + int(valor * 10)

        ref.set({"saldos": saldos, "atualizado_em": datetime.now(self.fuso).isoformat()}, merge=True)

        if chave_moeda == "geralcoin":
            self.db.collection("profissionais").document(user_id).set({"saldo": int(saldos["geralcoin"])}, merge=True)

        self.db.collection("transacoes").add({
            "user_id": user_id,
            "moeda": moeda.upper(),
            "tipo": tipo,
            "valor": valor,
            "origem": origem,
            "timestamp": datetime.now(self.fuso).isoformat()
        })

        return True, f"✅ Saldo de {moeda.upper()} atualizado: {saldos[chave_moeda]}"

    def converter_geralcoin_para_credito(self, user_id: str, qtd_coins: int):
        taxa_conversao = 0.10
        valor_brl = qtd_coins * taxa_conversao

        sucesso, msg = self.movimentar_saldo(user_id, "geralcoin", qtd_coins, "DEBITO", "CONVERSAO_PREPAGO")
        if not sucesso:
            return False, msg

        self.movimentar_saldo(user_id, "credito_brl", valor_brl, "CREDITO", "RESGATE_GERALCOIN")
        return True, f"🎉 {qtd_coins} GeralCoins convertidas em R$ {valor_brl:.2f} de Crédito Pré-pago!"


# ==============================================================================
# 6. CONFIGURAÇÃO DE AMBIENTE & FIRESTORE MASTER
# ==============================================================================
st.set_page_config(
    page_title="GeralJá | Ecossistema Integrado",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="collapsed",
)


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
                st.error("⚠️ Configuração 'firebase.base64' ausente no Secrets / secrets.toml.")
                st.stop()
        except Exception as e:
            st.error(f"❌ FALHA FIREBASE: {e}")
            st.stop()
    return firebase_admin.get_app()


app_engine = conectar_banco_master()
db = firestore.client()
carteira_engine = CarteiraEngine(db)

query_params = st.query_params


# ==============================================================================
# 7. AUTH GOOGLE & TOKEN DE COMPARTILHAMENTO
# ==============================================================================
def get_google_flow():
    g_auth = st.secrets["google_auth"]
    client_config = {
        "web": {
            "client_id": g_auth["client_id"],
            "client_secret": g_auth["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [g_auth["redirect_uri"]],
        }
    }
    return Flow.from_client_config(
        client_config,
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
        ],
        redirect_uri=g_auth["redirect_uri"],
    )


def processar_oauth_e_tokens():
    if "code" in query_params:
        try:
            flow = get_google_flow()
            flow.fetch_token(code=query_params["code"])
            session = flow.authorized_session()
            user_info = session.get("https://www.googleapis.com/userinfo").json()

            email_google = user_info.get("email")
            nome_google = user_info.get("name")
            foto_google = user_info.get("picture")

            st.query_params.clear()

            pro_ref = db.collection("profissionais").where("email", "==", email_google).limit(1).get()

            if pro_ref:
                st.session_state.auth = True
                st.session_state.user_id = pro_ref[0].id
                st.success(f"Logado como {nome_google}!")
                time.sleep(1)
                st.rerun()
            else:
                st.session_state.pre_cadastro = {
                    "email": email_google,
                    "nome": nome_google,
                    "foto": foto_google,
                }
                st.toast(f"Olá {nome_google}! Complete seu cadastro abaixo.")
        except Exception as e:
            st.error(f"Erro ao processar login do Google: {e}")

    if "share_token" in query_params and "user_id" in query_params:
        token_url = query_params["share_token"]
        user_url = query_params["user_id"]

        token_ref = db.collection("tokens_compartilhamento").document(token_url).get()
        if token_ref.exists and not token_ref.to_dict().get("resgatado", False):
            db.collection("tokens_compartilhamento").document(token_url).set(
                {"resgatado": True, "resgatado_em": datetime.now(fuso_br).isoformat()},
                merge=True,
            )
            carteira_engine.movimentar_saldo(
                user_url,
                "geralcoin",
                10,
                "CREDITO",
                f"COMPARTILHAMENTO_REAL_{token_url}",
            )
            st.toast("🎉 Compartilhamento confirmado! +10 GeralCoins adicionadas!")
            st.query_params.clear()
            time.sleep(1)


executar_bloco_seguro("Processador OAuth e Recompensas", processar_oauth_e_tokens)

# ==============================================================================
# 8. CONFIGURAÇÃO VISUAL & ESTILOS DINÂMICOS
# ==============================================================================
LAT_REF = -23.5505
LON_REF = -46.6333

CATEGORIAS_PADRAO = [
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
    "Churrascaria", "Hamburgueria", "Comida Japonesa", "Cafeteria", "Farmácia",
    "Barbearia/Salão", "Manicure/Pedicure", "Estética Facial", "Tatuagem/Piercing",
    "Fitness", "Academia", "Fisioterapia", "Odontologia", "Clínica Médica",
    "Psicologia", "Nutricionista", "TI", "Assistência Técnica", "Celulares",
    "Informática", "Refrigeração", "Técnico de Fogão", "Técnico de Lavadora",
    "Eletrônicos", "Chaveiro", "Montador", "Freteiro", "Carreto", "Motoboy/Entregas",
    "Pet Shop", "Veterinário", "Banho e Tosa", "Adestrador", "Agropecuária",
    "Aulas Particulares", "Escola Infantil", "Reforço Escolar", "Idiomas",
    "Advocacia", "Contabilidade", "Imobiliária", "Seguros", "Ajudante Geral",
    "Diarista", "Cuidador de Idosos", "Babá", "Outro (Personalizado)",
]


def carregar_categorias_dinamicas():
    try:
        doc_cat = db.collection("configuracoes").document("categorias").get()
        if doc_cat.exists:
            lista_banco = doc_cat.to_dict().get("lista", [])
            if lista_banco:
                return lista_banco
    except Exception:
        pass
    return CATEGORIAS_PADRAO


def limpar_whatsapp(numero):
    num = re.sub(r"\D", "", str(numero))
    if not num.startswith("55") and len(num) >= 10:
        num = f"55{num}"
    return num


def criar_link_zap(numero, msg):
    return f"https://api.whatsapp.com/send?phone={limpar_whatsapp(numero)}&text={urllib.parse.quote(msg)}"


if "modo_noite" not in st.session_state:
    st.session_state.modo_noite = False

c_t1, c_t2 = st.columns([2, 8])
with c_t1:
    st.session_state.modo_noite = st.toggle("🌙 Modo Noite", value=st.session_state.modo_noite)

clima_atual = buscar_clima_local()

estilo_dinamico = f"""
<style>
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    header {{ visibility: hidden; }}
    
    .main .block-container {{ 
        padding-top: 0.5rem !important; 
        padding-bottom: 5rem !important; 
    }}

    .stApp {{
        background-color: {"#0D1117" if st.session_state.modo_noite else "#FFFAFA"} !important;
        color: {"#FFFFFF" if st.session_state.modo_noite else "#1A1A1B"} !important;
    }}

    .header-container {{
        background: {"#161B22" if st.session_state.modo_noite else "#FFFFFF"};
        padding: 12px 15px !important;
        border-radius: 0 0 20px 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.06);
        border-bottom: 5px solid #FF8C00;
        margin-bottom: 15px !important;
    }}
    .logo-azul {{ color: #0047AB; font-weight: 900; font-size: 36px; }}
    .logo-laranja {{ color: #FF8C00; font-weight: 900; font-size: 36px; }}
</style>
"""
st.markdown(estilo_dinamico, unsafe_allow_html=True)
st.markdown(
    f'<div class="header-container"><span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span><br><small style="color:#64748B; font-weight:700;">ECOSSISTEMA INTEGRADO DE SERVIÇOS | 🌤️ Clima Agora: {clima_atual}</small></div>',
    unsafe_allow_html=True,
)

# Botão Flutuante
st.markdown(
    f"""
    <a href="https://wa.me/{ZAP_VENDAS}?text=Ol%C3%A1%2C%20quero%20anunciar%20minha%20marca%20na%20Vitrine%20do%20GeralJ%C3%A1" target="_blank" 
       style="position:fixed; bottom:25px; right:20px; background-color:#25d366; color:white; 
              border-radius:50px; padding:12px 22px; font-weight:bold; text-decoration:none; 
              box-shadow: 2px 4px 15px rgba(0,0,0,0.3); z-index:9999; display:flex; align-items:center; gap:8px;">
        📢 <span>Anuncie seu negócio</span>
    </a>
""",
    unsafe_allow_html=True,
)


# ==============================================================================
# 9. MÓDULO: CLUBE DE CUPONS & VITRINE SOCIAL (CORRIGIDO PROTEGIDO CONTRA 'IMG')
# ==============================================================================
def modulo_clube_cupons():
    st.markdown("### 🎟️ Clube de Cupons & Vitrine Social PPE")
    st.caption("Engaje nas ofertas da comunidade, acumule GeralCoins e troque por descontos exclusivos!")

    id_morador = st.text_input(
        "Digite seu WhatsApp para consultar saldo e usar os descontos:",
        value=st.session_state.get("user_id", ""),
        placeholder="Ex: 11999999999",
        key="clube_input_whatsapp"
    )

    if id_morador:
        zap_morador_limpo = limpar_whatsapp(id_morador)
        saldos_morador = carteira_engine.obter_saldos(zap_morador_limpo) if db else {"geralcoin": 20, "xp": 0}
        nivel_nome, nivel_info = calcular_nivel(saldos_morador.get("xp", 0))

        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("Carteira GeralCoins 🪙", f"{saldos_morador.get('geralcoin', 0)} GC")
        c_m2.metric("Nível de Confiança", f"{nivel_info['icone']} {nivel_nome}")
        c_m3.metric("Poder em Descontos", f"R$ {saldos_morador.get('geralcoin', 0) * 0.10:.2f}")

    st.markdown("---")
    st.subheader("🔥 Ofertas Recomendadas da Vitrine")

    if "social_stats" not in st.session_state:
        st.session_state.social_stats = {}

    def obter_stats(p_id):
        if p_id not in st.session_state.social_stats:
            st.session_state.social_stats[p_id] = {
                "likes": 28,
                "comments": [{"user": "Morador Grajaú", "texto": "Excelente produto, recomendo!", "data": "Hoje"}],
                "shares": 12,
            }
        return st.session_state.social_stats[p_id]

    ofertas_fallback = [
        {
            "id": "post_pizzaria_master",
            "loja_id": ZAP_ADMIN,
            "loja": "Pizzaria Grajaú Express",
            "item": "Combo Família: Pizza Grande + Guaraná 2L",
            "preco_brl": 65.00,
            "min_gc": 50,
            "max_gc": 150,
            "img": SVG_PIZZA_FALLBACK,
            "foto_url": SVG_PIZZA_FALLBACK,
            "palavras_bloqueadas": ["ruim", "péssimo", "demora"],
            "link_ifood": "https://www.ifood.com.br"
        },
        {
            "id": "post_lavajato_master",
            "loja_id": ZAP_ADMIN,
            "loja": "Lava Jato & Estética Interlagos",
            "item": "Lavagem Completa + Cera de Carnaúba",
            "preco_brl": 80.00,
            "min_gc": 50,
            "max_gc": 200,
            "img": SVG_SERVICO_FALLBACK,
            "foto_url": SVG_SERVICO_FALLBACK,
            "palavras_bloqueadas": ["ruim", "prejuízo"]
        }
    ]

    ofertas_exemplo = []
    if db:
        try:
            vitrine_db = list(db.collection("vitrine_posts").limit(10).stream())
            for vdoc in vitrine_db:
                d_post = vdoc.to_dict()
                d_post["id"] = vdoc.id
                ofertas_exemplo.append(d_post)
        except Exception:
            pass

    if not ofertas_exemplo:
        ofertas_exemplo = ofertas_fallback

    for of in ofertas_exemplo:
        post_id = of.get("id", "post_temp")
        loja_id = of.get("loja_id", ZAP_ADMIN)
        stats = obter_stats(post_id)

        with st.container(border=True):
            col_o1, col_o2 = st.columns([1, 2])
            
            with col_o1:
                url_imagem = extrair_url_imagem_segura(of, fallback=SVG_PIZZA_FALLBACK)
                exibir_imagem_segura(url_imagem, legenda=of.get("item", "Oferta"), fallback=SVG_PIZZA_FALLBACK)
                
                st.caption("👥 **Engajamento do Público:**")
                st.info(f"👍 **{stats['likes']}** Curtidas | 💬 **{len(stats['comments'])}** Comentários | 📢 **{stats['shares']}** Divulgações")

            with col_o2:
                st.markdown(f"#### {of.get('item', 'Oferta Especial')}")
                st.write(f"🏢 **{of.get('loja', 'Comércio Local')}**")

                desc_min = of.get("min_gc", 50) * 0.10
                desc_max = of.get("max_gc", 150) * 0.10
                preco_min = of.get("preco_brl", 50.0) - desc_max
                preco_max = of.get("preco_brl", 50.0) - desc_min

                st.markdown(
                    f"""
                    * Preço Normal: ~~R$ {of.get('preco_brl', 50.0):.2f}~~
                    * **Preço com Cupom:** <span style="color:#22c55e; font-weight:bold; font-size:18px;">R$ {preco_min:.2f} a R$ {preco_max:.2f}</span>
                    * 🎯 Exige de **{of.get('min_gc', 50)}** a **{of.get('max_gc', 150)}** GeralCoins
                    """,
                    unsafe_allow_html=True,
                )

                links_ext = []
                if of.get("link_ifood"):
                    links_ext.append(f'<a href="{of["link_ifood"]}" target="_blank" style="background:#EA1D2C; color:white; padding:5px 10px; border-radius:6px; text-decoration:none; font-size:11px; font-weight:bold;">🍔 iFood</a>')
                if of.get("link_shopee"):
                    links_ext.append(f'<a href="{of["link_shopee"]}" target="_blank" style="background:#EE4D2D; color:white; padding:5px 10px; border-radius:6px; text-decoration:none; font-size:11px; font-weight:bold;">🛍️ Shopee</a>')
                if of.get("link_mercadolivre"):
                    links_ext.append(f'<a href="{of["link_mercadolivre"]}" target="_blank" style="background:#FFE600; color:#2D3277; padding:5px 10px; border-radius:6px; text-decoration:none; font-size:11px; font-weight:bold;">💛 Mercado Livre</a>')
                
                if links_ext:
                    st.markdown('<div style="display:flex; gap:6px; flex-wrap:wrap; margin-bottom:10px;">' + "".join(links_ext) + '</div>', unsafe_allow_html=True)

                c_act1, c_act2, c_act3 = st.columns(3)
                
                if c_act1.button("👍 Curtir (+1 GC)", key=f"btn_lk_{post_id}"):
                    if not id_morador:
                        st.warning("Informe seu WhatsApp acima para acumular moedas!")
                    else:
                        zap_m = limpar_whatsapp(id_morador)
                        stats["likes"] += 1
                        if db:
                            carteira_engine.movimentar_saldo(zap_m, "geralcoin", 1, "CREDITO", f"CURTIDA_{post_id}")
                        st.toast("🎉 Você curtiu e ganhou +1 GeralCoin!", icon="👍")
                        time.sleep(0.3)
                        st.rerun()

                with c_act2:
                    with st.popover("💬 Comentar (+2 GC)"):
                        txt_comm = st.text_input("Escreva sua opinião:", key=f"in_comm_{post_id}")
                        if st.button("Enviar Comentário", key=f"sub_comm_{post_id}"):
                            if not id_morador:
                                st.warning("Informe seu WhatsApp acima!")
                            elif len(txt_comm.strip()) >= 3:
                                zap_m = limpar_whatsapp(id_morador)
                                palavras_bloqueadas = of.get("palavras_bloqueadas", [])
                                tem_bloqueio = any(pb.lower() in txt_comm.lower() for pb in palavras_bloqueadas if pb.strip())
                                
                                if tem_bloqueio:
                                    st.error("🚨 Seu comentário contém termos retidos pelas regras do anúncio.")
                                else:
                                    sentimento = analisar_sentimento_ia(txt_comm)
                                    stats["comments"].append({"user": zap_m[-4:], "texto": txt_comm, "data": "Agora"})
                                    
                                    if sentimento == "NEGATIVO":
                                        st.warning("💬 Comentário publicado! Porém avaliações negativas não geram moedas.")
                                    else:
                                        if db:
                                            carteira_engine.movimentar_saldo(zap_m, "geralcoin", 2, "CREDITO", f"COMENTARIO_{post_id}")
                                        st.toast("🎉 Comentário aprovado! +2 GeralCoins adicionadas!", icon="💬")
                                    time.sleep(0.5)
                                    st.rerun()

                with c_act3:
                    with st.popover("📢 Divulgar (+3 GC)"):
                        link_direto = f"https://geralja.app/?post={post_id}"
                        msg_share = f"Olha essa oferta imperdível no Grajaú Já: {of.get('item')} por R$ {preco_min:.2f}! {link_direto}"
                        link_zap_share = f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg_share)}"
                        
                        st.markdown(f'<a href="{link_zap_share}" target="_blank" style="display:block; text-align:center; background:#25D366; color:white; padding:8px; border-radius:8px; text-decoration:none; font-weight:bold; margin-bottom:8px;">📲 Enviar no WhatsApp</a>', unsafe_allow_html=True)
                        
                        if st.button("Confirmar Envio", key=f"sub_sh_{post_id}"):
                            if not id_morador:
                                st.warning("Informe seu WhatsApp acima!")
                            else:
                                zap_m = limpar_whatsapp(id_morador)
                                stats["shares"] += 1
                                if db:
                                    carteira_engine.movimentar_saldo(zap_m, "geralcoin", 3, "CREDITO", f"COMPARTILHAMENTO_{post_id}")
                                st.toast("🎉 Compartilhamento registrado! +3 GeralCoins!", icon="📢")
                                time.sleep(0.5)
                                st.rerun()

                if stats["comments"]:
                    with st.expander(f"💬 Ver comentários ({len(stats['comments'])})"):
                        for c in reversed(stats["comments"][-3:]):
                            st.caption(f"**Morador (final {c.get('user', '***')}):** {c.get('texto')}")

                st.write("")

                if st.button(f"🛒 Resgatar Cupom de Desconto", key=f"btn_resg_{post_id}", type="primary", use_container_width=True):
                    if not id_morador:
                        st.warning("Informe seu WhatsApp no topo da página para resgatar.")
                    else:
                        zap_m = limpar_whatsapp(id_morador)
                        saldos = carteira_engine.obter_saldos(zap_m) if db else {"geralcoin": 50}

                        if saldos["geralcoin"] < of.get("min_gc", 50):
                            st.error(f"⚠️ Saldo insuficiente. Esta oferta exige no mínimo {of.get('min_gc', 50)} GeralCoins.")
                        else:
                            gc_usar = min(saldos["geralcoin"], of.get("max_gc", 150))
                            desconto_brl = gc_usar * 0.10
                            valor_pix = of.get("preco_brl", 50.0) - desconto_brl

                            if db:
                                carteira_engine.movimentar_saldo(zap_m, "geralcoin", gc_usar, "DEBITO", f"COMPRA_CUPOM_{post_id}")

                            voucher_code = f"GJ-{zap_m[-4:] if len(zap_m)>=4 else '0000'}-{int(time.time()) % 10000}"

                            if db:
                                try:
                                    db.collection("pedidos").add({
                                        "loja_id": loja_id,
                                        "cliente_zap": zap_m,
                                        "item": of.get("item"),
                                        "voucher": voucher_code,
                                        "valor_pix": valor_pix,
                                        "status": "pendente",
                                        "timestamp": datetime.now(fuso_br).isoformat(),
                                    })
                                except Exception:
                                    pass

                            st.balloons()
                            st.success(f"🎉 Cupom {voucher_code} gerado com sucesso!")
                            
                            with st.container(border=True):
                                st.subheader("🎟️ VOUCHER OFICIAL DE DESCONTO")
                                st.write(f"**Código:** `{voucher_code}`")
                                st.write(f"**Item:** {of.get('item')}")
                                st.write(f"**Abatimento ({gc_usar} GC):** -R$ {desconto_brl:.2f}")
                                st.markdown(f"### **TOTAL A PAGAR NO PIX:** R$ {valor_pix:.2f}")
                                st.info(f"🔑 Chave PIX da Loja: `{of.get('pix', PIX_OFICIAL)}`")

                            msg_pedido = f"""🚨 *Novo Pedido GeralJá - Cupom Aplicado*
🎟️ *Voucher:* {voucher_code}
👤 *Cliente:* {zap_m}
📦 *Item:* {of.get('item')}
🏬 *Estabelecimento:* {of.get('loja')}

💵 *Valor Tabela:* R$ {of.get('preco_brl', 0):.2f}
🪙 *Abatimento ({gc_usar} GC):* -R$ {desconto_brl:.2f}
✅ *Total a Pagar no PIX:* R$ {valor_pix:.2f}"""

                            link_pedido_zap = criar_link_zap(of.get("zap", ZAP_ADMIN), msg_pedido)
                            st.markdown(f'<a href="{link_pedido_zap}" target="_blank" style="display:block; background:#25D366; color:white; text-align:center; padding:12px; border-radius:10px; font-weight:600; text-decoration:none;">💬 Confirmar Pedido no WhatsApp da Loja</a>', unsafe_allow_html=True)


# ==============================================================================
# 10. MÓDULO: TORRE DE CONTROLE ADMIN SUPREMA (CORRIGIDO PROTEGIDO CONTRA 'IMG')
# ==============================================================================
def modulo_admin_torre_controle():
    if not st.session_state.get("admin_logado"):
        st.markdown("### 🔐 Acesso Restrito à Diretoria")
        with st.form("painel_login_adm"):
            u = st.text_input("Usuário Administrativo")
            p = st.text_input("Senha", type="password")
            if st.form_submit_button("Acessar Torre de Controle", use_container_width=True):
                if u == ADMIN_USER and p == ADMIN_PASS:
                    st.session_state.admin_logado = True
                    st.success("Acesso concedido!")
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")
    else:
        st.markdown("## 👑 Central de Comando Supremo GeralJá")
        if st.button("🚪 Sair da Torre de Controle"):
            st.session_state.admin_logado = False
            st.rerun()

        st.divider()
        try:
            profs_ref = list(db.collection("profissionais").stream()) if db else []
            profs_data = [p.to_dict() | {"id": p.id} for p in profs_ref]

            carteiras_ref = list(db.collection("carteiras").stream()) if db else []
            total_moedas_circulando = sum(c.to_dict().get("saldos", {}).get("geralcoin", 0) for c in carteiras_ref)

            c_a1, c_a2, c_a3 = st.columns(3)
            c_a1.metric("Membros Cadastrados", len(profs_data))
            c_a2.metric("GeralCoins Emitidas", f"🪙 {total_moedas_circulando} GC")
            c_a3.metric("Contas Ativas", len(carteiras_ref))

            sub_tabs = st.tabs(["🏛️ Gestão de Moedas", "👥 Membros", "🛒 Vitrine"])

            with sub_tabs[0]:
                st.subheader("🏛️ Gestão do Banco de Moedas")
                target_id = st.text_input("WhatsApp do Usuário:", key="adm_target_coin")
                qtd_coin = st.number_input("Quantidade de GeralCoins:", min_value=1, value=100, key="adm_qtd_coin")

                if st.button("🚀 Injetar Moedas", type="primary"):
                    if target_id.strip():
                        target_clean = limpar_whatsapp(target_id)
                        ok, msg = carteira_engine.movimentar_saldo(target_clean, "geralcoin", qtd_coin, "CREDITO", "RECARGA_ADMIN")
                        if ok:
                            st.success(f"Adicionadas {qtd_coin} GeralCoins para {target_clean}!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(msg)

            with sub_tabs[1]:
                st.subheader("👥 Usuários Registrados")
                for p in profs_data:
                    st.text(f"• {p.get('nome', 'Sem Nome')} ({p['id']}) - Saldo: {p.get('saldo', 0)} GC")

            with sub_tabs[2]:
                st.subheader("🛒 Controle de Anúncios")
                vitrine_ref = list(db.collection("vitrine_posts").stream()) if db else []
                for vdoc in vitrine_ref:
                    vdata = vdoc.to_dict()
                    midia_post = extrair_url_imagem_segura(vdata)
                    st.write(f"• **{vdata.get('item', 'Anúncio sem nome')}** - Loja ID: {vdata.get('loja_id', 'Sem ID')}")

        except Exception as e:
            st.error(f"Erro no painel administrativo: {e}")


# ==============================================================================
# 11. ROTEADOR DE ABAS DA APLICAÇÃO
# ==============================================================================
lista_abas = ["🎟️ Clube de Cupons", "👑 Admin GeralJá"]
menu_abas = st.tabs(lista_abas)

with menu_abas[0]:
    executar_bloco_seguro("Clube de Cupons", modulo_clube_cupons)

with menu_abas[1]:
    executar_bloco_seguro("Torre de Controle Admin", modulo_admin_torre_controle)

st.write("---")
st.caption("GeralJá Ecosystem v10.0 Master Defensive | Sistema de Economia Local Protegido")
