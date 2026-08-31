# -*- coding: utf-8 -*-
# ==============================================================================
# GERALJÁ: ECOSSISTEMA COMPLETO v6.5 (LIQUIDA & OFERTAS MERCADO LIVRE EDITION)
# Mídia + Marketplace Híbrido + Carteira Multi-Moedas + Clube de Ofertas Flash
# Busca IA + Firebase Firestore + Google OAuth + Proteção LGPD + Custódia
# ==============================================================================

import base64
from datetime import datetime, timedelta
import difflib
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
# 1. CARREGAMENTO BLINDADO DE SEGREDOS
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
  st.error(
      f"🚨 ERRO CRÍTICO DE SEGURANÇA: Credencial '{chave}' ausente no"
      " st.secrets/secret.py."
  )
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
REDIRECT_URI = st.secrets.get("google_auth", {}).get(
    "redirect_uri", "https://geralja-zxiaj2ot56fuzgcz7xhcks.streamlit.app/"
)

if GEMINI_KEY:
  genai.configure(api_key=GEMINI_KEY)
if GROQ_KEY:
  client_groq = Groq(api_key=GROQ_KEY)


# ==============================================================================
# 2. ENGENHARIA DE SANITIZAÇÃO E MOTOR DE CARTEIRA MULTI-MOEDAS
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


class CarteiraEngine:

  def __init__(self, db_client):
    self.db = db_client
    self.fuso = pytz.timezone("America/Sao_Paulo")

  def obter_saldos(self, user_id: str):
    ref = self.db.collection("carteiras").document(user_id)
    doc = ref.get()
    if not doc.exists:
      saldos_padrao = {"geralcoin": 20, "credito_brl": 0.0, "custodia_brl": 0.0}
      ref.set(
          {
              "saldos": saldos_padrao,
              "atualizado_em": datetime.now(self.fuso).isoformat(),
          },
          merge=True,
      )
      return saldos_padrao
    return doc.to_dict().get(
        "saldos", {"geralcoin": 0, "credito_brl": 0.0, "custodia_brl": 0.0}
    )

  def movimentar_saldo(
      self, user_id: str, moeda: str, valor: float, tipo: str, origem: str
  ):
    ref = self.db.collection("carteiras").document(user_id)
    saldos = self.obter_saldos(user_id)
    chave_moeda = moeda.lower()

    saldo_atual = saldos.get(chave_moeda, 0.0)

    if tipo == "DEBITO" and saldo_atual < valor:
      return False, f"⚠️ Saldo insuficiente em {moeda.upper()}."

    novo_saldo = (
        (saldo_atual + valor) if tipo == "CREDITO" else (saldo_atual - valor)
    )
    saldos[chave_moeda] = round(novo_saldo, 2)

    ref.set(
        {"saldos": saldos, "atualizado_em": datetime.now(self.fuso).isoformat()},
        merge=True,
    )

    if chave_moeda == "geralcoin":
      self.db.collection("profissionais").document(user_id).set(
          {"saldo": int(saldos["geralcoin"])}, merge=True
      )

    self.db.collection("transacoes").add({
        "user_id": user_id,
        "moeda": moeda.upper(),
        "tipo": tipo,
        "valor": valor,
        "origem": origem,
        "timestamp": datetime.now(self.fuso).isoformat(),
    })

    return (
        True,
        f"✅ Sucesso! Novo saldo de {moeda.upper()}: {saldos[chave_moeda]}",
    )

  def converter_geralcoin_para_credito(self, user_id: str, qtd_coins: int):
    taxa_conversao = 0.10
    valor_brl = qtd_coins * taxa_conversao

    sucesso, msg = self.movimentar_saldo(
        user_id, "geralcoin", qtd_coins, "DEBITO", "CONVERSAO_PREPAGO"
    )
    if not sucesso:
      return False, msg

    self.movimentar_saldo(
        user_id, "credito_brl", valor_brl, "CREDITO", "RESGATE_GERALCOIN"
    )
    return (
        True,
        f"🎉 {qtd_coins} GeralCoins convertidas em R$ {valor_brl:.2f} de Crédito"
        " Pré-pago!",
    )


# ==============================================================================
# 3. AMBIENTE & FIRESTORE
# ==============================================================================
st.set_page_config(
    page_title="GeralJá | Ecossistema & Ofertas",
    page_icon="🟡",
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
        st.error("⚠️ Configuração 'firebase.base64' ausente no Secrets.")
        st.stop()
    except Exception as e:
      st.error(f"❌ FALHA FIREBASE: {e}")
      st.stop()
  return firebase_admin.get_app()


app_engine = conectar_banco_master()
db = firestore.client()
carteira_engine = CarteiraEngine(db)

# ==============================================================================
# 4. AUTENTICAÇÃO GOOGLE & COMPARTILHAMENTO
# ==============================================================================
query_params = st.query_params


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

    pro_ref = (
        db.collection("profissionais")
        .where("email", "==", email_google)
        .limit(1)
        .get()
    )

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
    st.error(f"Erro no login do Google: {e}")

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
        user_url, "geralcoin", 10, "CREDITO", f"COMPARTILHAMENTO_REAL_{token_url}"
    )
    st.toast("🎉 Compartilhamento confirmado! +10 GeralCoins adicionadas!")
    st.query_params.clear()
    time.sleep(1)

# ==============================================================================
# 5. CONSTANTES, REGRAS & INTELIGÊNCIA DE BUSCA
# ==============================================================================
LAT_REF = -23.5505
LON_REF = -46.6333

CATEGORIAS_PADRAO = [
    "Pizzaria",
    "Lanchonete",
    "Restaurante",
    "Barbearia/Salão",
    "Mecânico",
    "Eletricista",
    "Encanador",
    "Pedreiro",
    "Pintor",
    "Lava Jato",
    "Pet Shop",
    "Farmácia",
    "Mercado/Adega",
    "Assistência Técnica",
    "Diarista",
    "Freteiro",
    "Outro (Personalizado)",
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


CATEGORIAS_OFICIAIS = carregar_categorias_dinamicas()


def limpar_whatsapp(numero):
  num = re.sub(r"\D", "", str(numero))
  if not num.startswith("55") and len(num) >= 10:
    num = f"55{num}"
  return num


def normalizar(texto):
  if not texto:
    return ""
  return (
      "".join(
          ch
          for ch in unicodedata.normalize("NFKD", str(texto))
          if unicodedata.category(ch) != "Mn"
      )
      .lower()
      .strip()
  )


def calcular_distancia_real(lat1, lon1, lat2, lon2):
  try:
    if None in [lat1, lon1, lat2, lon2]:
      return 999.0
    R = 6371
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))), 1)
  except Exception:
    return 999.0


def processar_busca_tolerante(texto_usuario):
  termo_limpo = normalizar(texto_usuario)
  if not termo_limpo:
    return "Outro (Personalizado)"
  cats_atuais = carregar_categorias_dinamicas()
  categorias_norm = {normalizar(c): c for c in cats_atuais}
  matches_cat = difflib.get_close_matches(
      termo_limpo, list(categorias_norm.keys()), n=1, cutoff=0.50
  )
  if matches_cat:
    return categorias_norm[matches_cat[0]]
  return "Outro (Personalizado)"


def otimizar_imagem(arq, qualidade=50, size=(800, 800)):
  try:
    img = Image.open(arq)
    if img.mode in ("RGBA", "P"):
      img = img.convert("RGB")
    img.thumbnail(size)
    output = io.BytesIO()
    img.save(output, format="JPEG", quality=qualidade, optimize=True)
    return (
        f"data:image/jpeg;base64,{base64.b64encode(output.getvalue()).decode()}"
    )
  except Exception as e:
    st.error(f"Erro ao processar imagem: {e}")
    return None


def criar_link_zap(numero, msg):
  return f"https://api.whatsapp.com/send?phone={limpar_whatsapp(numero)}&text={urllib.parse.quote(msg)}"


@st.cache_data(ttl=600)
def buscar_noticias_rss(busca="Grajaú São Paulo"):
  if not feedparser:
    return []
  try:
    url_rss = f"https://news.google.com/rss/search?q={urllib.parse.quote(busca)}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    feed = feedparser.parse(url_rss)
    return feed.entries[:4]
  except Exception:
    return []


# ==============================================================================
# 6. ESTILIZAÇÃO MERCADO LIVRE & COMPONENTES VISUAIS
# ==============================================================================
st.markdown(
    """
<style>
    /* Estilo do Topo Amarelo Mercado Livre */
    .ml-header {
        background: linear-gradient(90deg, #FFF159 0%, #FFE600 100%);
        padding: 15px 25px;
        border-radius: 0 0 15px 15px;
        color: #333333;
        font-weight: bold;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .ml-badge-discount {
        background-color: #00A650;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
    }
    .ml-trust-badge {
        background-color: #E8F5E9;
        color: #2E7D32;
        border: 1px solid #A5D6A7;
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .stButton > button {
        background-color: #3483FA !important;
        color: white !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        border: none !important;
    }
    .stButton > button:hover {
        background-color: #2968C8 !important;
    }
</style>
<div class="ml-header">
    <span style="font-size: 24px; font-weight: 900; color: #2D3277;">🟡 GeralJá <small style="font-size: 12px; color: #333;">| Liquida Grajaú</small></span>
    <span class="ml-trust-badge">🛡️ Compra Garantida & Custódia Ativa</span>
</div>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# 7. SISTEMA DE NAVEGAÇÃO
# ==============================================================================
lista_abas = [
    "🔍 Buscar",
    "⚡ Liquida & Cupons",
    "🚀 Cadastrar",
    "👤 Meu Perfil",
    "👑 Admin",
    "📊 Financeiro",
]
menu_abas = st.tabs(lista_abas)

# ==============================================================================
# ABA 0: BUSCA DE SERVIÇOS & PILLS
# ==============================================================================
with menu_abas[0]:
  st.markdown("### 🏙️ O que você procura no bairro hoje?")

  # Pílulas de busca rápida estilo Mercado Livre
  st.write("**Filtro Rápido:**")
  col_p1, col_p2, col_p3, col_p4, col_p5 = st.columns(5)
  termo_pílula = ""
  if col_p1.button("🍕 Pizzarias"):
    termo_pílula = "Pizzaria"
  if col_p2.button("🔧 Mecânicos"):
    termo_pílula = "Mecânico"
  if col_p3.button("💈 Salão/Barba"):
    termo_pílula = "Barbearia/Salão"
  if col_p4.button("⚡ Eletricistas"):
    termo_pílula = "Eletricista"
  if col_p5.button("🧼 Lava Jato"):
    termo_pílula = "Lava Jato"

  c1, c2 = st.columns([3, 1])
  termo_busca = c1.text_input(
      "Pesquisar serviço ou estabelecimento...",
      value=termo_pílula,
      key="main_search",
  )
  raio_km = c2.select_slider(
      "Raio (KM)", options=[1, 3, 5, 10, 20, 50], value=5
  )

  if termo_busca:
    cat_ia = processar_busca_tolerante(termo_busca)
    profs = (
        db.collection("profissionais")
        .where("area", "==", cat_ia)
        .where("aprovado", "==", True)
        .stream()
    )

    lista_ranking = []
    for p_doc in profs:
      p = p_doc.to_dict()
      p["id"] = p_doc.id
      dist = calcular_distancia_real(
          LAT_REF, LON_REF, p.get("lat", LAT_REF), p.get("lon", LON_REF)
      )
      if dist <= raio_km:
        p["dist"] = dist
        lista_ranking.append(p)

    if not lista_ranking:
      st.warning(f"Nenhum profissional de '{cat_ia}' encontrado no raio.")
    else:
      for p in lista_ranking:
        zap_limpo = limpar_whatsapp(p.get("whatsapp", p["id"]))
        link_zap = criar_link_zap(
            zap_limpo,
            f"Olá {p.get('nome')}, vi seu anúncio no GeralJá e gostaria de um"
            " orçamento!",
        )

        st.markdown(f"""
                <div style="background: white; padding: 15px; border-radius: 8px; border-left: 5px solid #FFE600; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <h4 style="margin: 0; color: #333;">{p.get('nome')} <span style="font-size: 12px; color: #00A650;">📍 {p['dist']:.1f} km</span></h4>
                    <p style="margin: 5px 0; color: #666; font-size: 13px;">{p.get('descricao', '')}</p>
                    <a href="{link_zap}" target="_blank" style="background: #25D366; color: white; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-weight: bold; font-size: 12px; display: inline-block;">💬 WhatsApp Directo</a>
                </div>
                """, unsafe_allow_html=True)

# ==============================================================================
# ABA 1: LIQUIDA GERALJÁ & OFERTAS RELÂMPAGO (MERCADO LIVRE STYLE)
# ==============================================================================
with menu_abas[1]:
  st.markdown("### ⚡ Liquida GeralJá — Ofertas do Dia")
  st.caption(
      "Aproveite cupons de desconto limitados com resgate garantido por"
      " GeralCoins!"
  )

  id_morador = st.text_input(
      "Informe seu WhatsApp para aplicar seus descontos:",
      value=st.session_state.get("user_id", ""),
  )

  if id_morador:
    zap_m = limpar_whatsapp(id_morador)
    saldos_m = carteira_engine.obter_saldos(zap_m)
    st.info(
        f"🪙 Seu Saldo Atual: **{saldos_m['geralcoin']} GeralCoins** (Equivale a"
        f" **R$ {saldos_m['geralcoin']*0.10:.2f}** de desconto)"
    )

  st.markdown("---")

  ofertas_flash = [
      {
          "id": "of1",
          "loja": "Pizzaria Grajaú Express",
          "item": "Combo Pizza Família + Refrigerante 2L",
          "preco_original": 65.00,
          "preco_promo": 45.00,
          "max_gc": 100,
          "estoque_total": 10,
          "estoque_vendido": 7,
      },
      {
          "id": "of2",
          "loja": "Lava Jato Interlagos",
          "item": "Lavagem Técnica + Cera de Carnaúba",
          "preco_original": 80.00,
          "preco_promo": 55.00,
          "max_gc": 150,
          "estoque_total": 15,
          "estoque_vendido": 12,
      },
      {
          "id": "of3",
          "loja": "Barbearia Estilo Nobre",
          "item": "Corte de Cabelo + Barboterapia",
          "preco_original": 50.00,
          "preco_promo": 35.00,
          "max_gc": 80,
          "estoque_total": 8,
          "estoque_vendido": 3,
      },
  ]

  for of in ofertas_flash:
    with st.container():
      col1, col2 = st.columns([2, 1])

      pct_vendido = int((of["estoque_vendido"] / of["estoque_total"]) * 100)
      desc_percent = int(
          ((of["preco_original"] - of["preco_promo"]) / of["preco_original"])
          * 100
      )

      with col1:
        st.markdown(f"""
                <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #E0E0E0; margin-bottom: 15px;">
                    <span class="ml-badge-discount">{desc_percent}% OFF</span>
                    <h4 style="margin: 5px 0; color: #333;">{of['item']}</h4>
                    <p style="margin: 0; color: #666; font-size: 13px;">🏬 Vendido por: <b>{of['loja']}</b></p>
                    <p style="font-size: 18px; margin: 10px 0;">
                        <s>R$ {of['preco_original']:.2f}</s> ➔ <b style="color: #00A650; font-size: 22px;">R$ {of['preco_promo']:.2f}</b>
                    </p>
                    <div style="margin-top: 10px;">
                        <small style="color: #CC0000; font-weight: bold;">🔥 Corra! {pct_vendido}% dos cupons já foram reservados</small>
                        <progress value="{pct_vendido}" max="100" style="width: 100%; height: 8px;"></progress>
                    </div>
                </div>
                """, unsafe_allow_html=True)

      with col2:
        if st.button(f"🛒 Resgatar Oferta", key=f"btn_flash_{of['id']}"):
          if not id_morador:
            st.warning("Insira seu WhatsApp acima para resgatar.")
          else:
            zap_m = limpar_whatsapp(id_morador)
            saldos = carteira_engine.obter_saldos(zap_m)
            gc_usar = min(saldos["geralcoin"], of["max_gc"])
            desconto_brl = gc_usar * 0.10
            valor_final = of["preco_promo"] - desconto_brl

            if gc_usar > 0:
              carteira_engine.movimentar_saldo(
                  zap_m,
                  "geralcoin",
                  gc_usar,
                  "DEBITO",
                  f"CUPOM_LIQUIDA_{of['id']}",
              )

            msg_zap = (
                f"🚨 *Resgate Liquida GeralJá*\n\n"
                f"📦 Item: {of['item']}\n"
                f"💵 Valor com Desconto: R$ {valor_final:.2f}\n"
                f"🛡️ Compra com Garantia & Custódia GeralJá."
            )
            link_final = criar_link_zap(ZAP_ADMIN, msg_zap)

            st.success(
                f"🎉 Cupom Gerado! Desconto de R$ {desconto_brl:.2f} aplicado."
            )
            st.markdown(
                f'<a href="{link_final}" target="_blank" style="background:'
                " #25D366; color: white; padding: 10px; border-radius: 6px;"
                " text-decoration: none; display: block; text-align: center;"
                ' font-weight: bold;">💬 Enviar Pedido no WhatsApp</a>',
                unsafe_allow_html=True,
            )

# ==============================================================================
# ABA 2: CADASTRO
# ==============================================================================
with menu_abas[2]:
  st.markdown("### 🚀 Cadastre seu Negócio na Vitrine")

  with st.form("form_cadastro_parceiro"):
    nome_input = st.text_input("Nome da Loja ou do Profissional")
    zap_input = st.text_input("WhatsApp com DDD")
    cat_input = st.selectbox(
        "Categoria", carregar_categorias_dinamicas()
    )
    desc_input = st.text_area("Descrição dos Serviços")
    senha_input = st.text_input("Senha para Acesso", type="password")

    if st.form_submit_button("✅ Finalizar Cadastro"):
      zap_l = limpar_whatsapp(zap_input)
      if nome_input and zap_l and senha_input:
        db.collection("profissionais").document(zap_l).set({
            "nome": nome_input,
            "whatsapp": zap_l,
            "area": cat_input,
            "descricao": desc_input,
            "senha": senha_input,
            "aprovado": True,
            "saldo": 20,
            "lat": LAT_REF,
            "lon": LON_REF,
        }, merge=True)
        carteira_engine.obter_saldos(zap_l)
        st.success("Cadastro realizado com sucesso!")
      else:
        st.error("Preencha todos os campos obrigatórios.")

# ==============================================================================
# ABA 3: PERFIL DO PARCEIRO
# ==============================================================================
with menu_abas[3]:
  st.markdown("### 👤 Painel do Parceiro")
  if not st.session_state.get("auth"):
    l_zap = st.text_input("WhatsApp")
    l_pass = st.text_input("Senha", type="password")
    if st.button("Entrar"):
      zap_b = limpar_whatsapp(l_zap)
      u = db.collection("profissionais").document(zap_b).get()
      if u.exists and str(u.to_dict().get("senha")) == str(l_pass):
        st.session_state.auth = True
        st.session_state.user_id = zap_b
        st.rerun()
      else:
        st.error("Credenciais inválidas.")
  else:
    uid = st.session_state.user_id
    saldos = carteira_engine.obter_saldos(uid)
    st.write(f"**WhatsApp Ativo:** {uid}")
    st.metric("GeralCoins 🪙", f"{saldos['geralcoin']} GC")
    st.metric("Crédito Pré-pago 💳", f"R$ {saldos['credito_brl']:.2f}")

    if st.button("Sair"):
      st.session_state.auth = False
      st.rerun()

# ==============================================================================
# ABA 4: ADMIN
# ==============================================================================
with menu_abas[4]:
  st.markdown("### 👑 Painel Administrativo")
  u_adm = st.text_input("Usuário Admin")
  p_adm = st.text_input("Senha Admin", type="password")
  if st.button("Acessar Admin"):
    if u_adm == ADMIN_USER and p_adm == ADMIN_PASS:
      st.success("Acesso Admin Concedido.")
      st.write("Visão geral de controle ativa.")
    else:
      st.error("Dados de acesso incorretos.")

# ==============================================================================
# ABA 5: FINANCEIRO & RELATÓRIOS
# ==============================================================================
with menu_abas[5]:
  st.markdown("### 📊 Balanço & Movimentações")
  st.info(f"Chave PIX Oficial de Recebimento: {PIX_OFICIAL}")
  st.caption(
      "Acompanhamento em tempo real de recargas e resgate de cupons em"
      " custódia."
  )
