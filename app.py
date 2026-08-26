# -*- coding: utf-8 -*-
# ==============================================================================
# GERALJÁ: CARRETA & CONTAINERS MASTER (v7.0 INTEGRATED)
# Chassi de Engate Rápido + Vitrine Social Pay-Per-Engagement (PPE)
# ==============================================================================

import base64
from datetime import datetime
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

# ==============================================================================
# 1. ENGENHARIA DE ENGATE: EXECUTOR SEGURO DE CONTAINERS
# ==============================================================================
def executar_bloco_seguro(
    nome_bloco: str, funcao_bloco, *args, container=None, **kwargs
):
  """Pino de Engate: Executa o container isolado sem derrubar a carreta caso ocorra falha."""
  alvo = container if container is not None else st
  try:
    with alvo.container():
      funcao_bloco(*args, **kwargs)
  except Exception as e:
    alvo.warning(
        f"⚠️ Container '{nome_bloco}' em manutenção ou desativado temporariamente."
    )
    with alvo.expander(f"🔍 Detalhes ({nome_bloco})", expanded=False):
      st.error(f"Falha na execução: {e}")


# ==============================================================================
# 2. CARREGAMENTO DE COFRE & SEGREDOS
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
  st.error(f"🚨 Credencial obrigatória '{chave}' ausente nos secrets.")
  st.stop()


ADMIN_USER = obter_segredo_critico("ADMIN_USER")
ADMIN_PASS = obter_segredo_critico("ADMIN_PASS")
PIX_OFICIAL = obter_segredo_critico("PIX_OFICIAL")
ZAP_ADMIN = obter_segredo_critico("ZAP_ADMIN")
ZAP_VENDAS = obter_segredo_critico("ZAP_VENDAS")


# ==============================================================================
# 3. MOTOR DE CARTEIRA MULTI-MOEDAS E BANCO FIRESTORE
# ==============================================================================
class CarteiraEngine:

  def __init__(self, db_client):
    self.db = db_client
    self.fuso = pytz.timezone("America/Sao_Paulo")

  def obter_saldos(self, user_id: str):
    if not self.db:
      return {"geralcoin": 20, "credito_brl": 0.0, "custodia_brl": 0.0}
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
    if not self.db:
      return True, "Modo offline"
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
    return True, f"✅ Sucesso! Novo saldo: {saldos[chave_moeda]}"


st.set_page_config(
    page_title="GeralJá | Sistema Operacional",
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
    except Exception as e:
      st.error(f"❌ FALHA FIREBASE: {e}")
      return None
  return firebase_admin.get_app()


app_engine = conectar_banco_master()
db = firestore.client() if app_engine else None
carteira_engine = CarteiraEngine(db)

# ==============================================================================
# 4. TEMA E TOPO DA CARRETA
# ==============================================================================
if "modo_noite" not in st.session_state:
  st.session_state.modo_noite = False

st.markdown(
    f"""
<style>
    #MainMenu, footer, header {{ visibility: hidden; }}
    .main .block-container {{ padding-top: 0.5rem !important; padding-bottom: 5rem !important; }}
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
    .logo-azul {{ color: #0047AB; font-weight: 900; font-size: 32px; }}
    .logo-laranja {{ color: #FF8C00; font-weight: 900; font-size: 32px; }}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="header-container"><span class="logo-azul">GERAL</span><span'
    ' class="logo-laranja">JÁ</span><br><small'
    ' style="color:#64748B;font-weight:700;">ECOSSISTEMA INTEGRADO DE SERVIÇOS E'
    " MOEDA LOCAL</small></div>",
    unsafe_allow_html=True,
)


# ==============================================================================
# 5. CONTAINER 1: VITRINE SOCIAL PAY-PER-ENGAGEMENT (MÓDULO ENGATADO)
# ==============================================================================
def container_vitrine_social_ppe():
  fuso_br = pytz.timezone("America/Sao_Paulo")

  st.markdown(
      '<h2 style="text-align:center; color:#FF8C00; font-weight:900;">📢'
      " COMPARTILHE, GANHE MOEDAS E UTILIZE NO COMÉRCIO LOCAL!</h2>",
      unsafe_allow_html=True,
  )

  if "social_stats" not in st.session_state:
    st.session_state.social_stats = {}
  if "saldo_lojistas" not in st.session_state:
    st.session_state.saldo_lojistas = {
        "loja_pizzaria_express": 100,
        "loja_interlagos_wash": 0,
    }

  def obter_stats(post_id):
    if post_id not in st.session_state.social_stats:
      st.session_state.social_stats[post_id] = {
          "likes": 18,
          "comments": [{
              "user": "11987654321",
              "texto": "Excelente serviço!",
              "data": "Ontem",
          }],
          "shares": 6,
      }
    return st.session_state.social_stats[post_id]

  def verificar_trava(user_id, post_id, acao):
    chave = f"{user_id}_{post_id}_{acao}"
    if db:
      try:
        return db.collection("trilha_engajamento").document(chave).get().exists
      except Exception:
        return False
    else:
      if "mock_trilha" not in st.session_state:
        st.session_state.mock_trilha = set()
      return chave in st.session_state.mock_trilha

  def processar_ppe(
      user_id,
      loja_id,
      post_id,
      acao,
      valor_gc,
      msg_ok,
      texto_comentario=None,
  ):
    chave = f"{user_id}_{post_id}_{acao}"
    stats = obter_stats(post_id)

    if verificar_trava(user_id, post_id, acao):
      return False, "⚠️ Ação já realizada nesta publicação!"

    if db:
      saldos_loja = carteira_engine.obter_saldos(loja_id)
      saldo_loja = saldos_loja.get("geralcoin", 0)
    else:
      saldo_loja = st.session_state.saldo_lojistas.get(loja_id, 0)

    if saldo_loja < valor_gc:
      return (
          False,
          "🛑 O comerciante atingiu o limite de orçamento de engajamento para"
          " este anúncio!",
      )

    if db:
      carteira_engine.movimentar_saldo(
          loja_id, "geralcoin", valor_gc, "DEBITO", f"PPE_PAY_{post_id}"
      )
      carteira_engine.movimentar_saldo(
          user_id, "geralcoin", valor_gc, "CREDITO", f"PPE_EARN_{post_id}"
      )
      db.collection("trilha_engajamento").document(chave).set({
          "user_id": user_id,
          "loja_id": loja_id,
          "post_id": post_id,
          "acao": acao,
          "valor_gc": valor_gc,
          "timestamp": datetime.now(fuso_br).isoformat(),
      })
    else:
      st.session_state.saldo_lojistas[loja_id] -= valor_gc
      if "mock_saldos" not in st.session_state:
        st.session_state.mock_saldos = {"geralcoin": 10, "credito_brl": 0.0}
      st.session_state.mock_saldos["geralcoin"] += valor_gc
      st.session_state.mock_trilha.add(chave)

    if acao == "LIKE":
      stats["likes"] += 1
    elif acao == "COMMENT" and texto_comentario:
      stats["comments"].append({
          "user": user_id,
          "texto": texto_comentario,
          "data": datetime.now(fuso_br).strftime("%H:%M"),
      })
    elif acao == "SHARE":
      stats["shares"] += 1

    return True, msg_ok

  # Autenticação
  is_logado = st.session_state.get("auth", False)
  user_id = st.session_state.get("user_id", "")

  if not is_logado:
    st.info(
        "🔑 **Acesso Restrito:** Identifique-se para liberar suas GeralCoins e"
        " usar os cupons do bairro."
    )
    t1, t2 = st.tabs(["🔑 Entrar", "📝 Cadastrar"])
    with t1:
      with st.form("f_login"):
        u_zap = st.text_input("WhatsApp:", placeholder="11999999999")
        u_pw = st.text_input("Senha:", type="password")
        if st.form_submit_button("Entrar", use_container_width=True):
          num_c = re.sub(r"\D", "", str(u_zap))
          if len(num_c) >= 10 and u_pw:
            st.session_state.auth = True
            st.session_state.user_id = num_c
            st.toast("✅ Acesso liberado!")
            time.sleep(0.3)
            st.rerun()
    with t2:
      with st.form("f_cad"):
        c_nome = st.text_input("Nome Completo:")
        c_zap = st.text_input("WhatsApp:", placeholder="11999999999")
        c_senha = st.text_input("Senha:", type="password")
        if st.form_submit_button("Cadastrar", use_container_width=True):
          num_c = re.sub(r"\D", "", str(c_zap))
          if len(num_c) >= 10 and c_nome and c_senha:
            st.session_state.auth = True
            st.session_state.user_id = num_c
            st.success("🎉 Perfil criado com sucesso!")
            time.sleep(0.3)
            st.rerun()
    return

  # Dashboard de Saldo
  if db:
    saldos = carteira_engine.obter_saldos(user_id)
    saldo_gc = saldos.get("geralcoin", 0)
  else:
    saldo_gc = st.session_state.get("mock_saldos", {}).get("geralcoin", 10)

  st.markdown(
      f"""
    <div style="background: linear-gradient(135deg, #0047AB, #1e3a8a); border-radius: 16px; padding: 15px; color: white; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
        <div><b>CONTA ATIVA:</b> {user_id}</div>
        <div><b>SALDO:</b> 🪙 {saldo_gc} GC <span style="color:#22c55e;">(R$ {saldo_gc * 0.10:.2f})</span></div>
    </div>
    """,
      unsafe_allow_html=True,
  )

  # Encartes PPE
  posts = [
      {
          "post_id": "post_pizzaria_master",
          "loja_id": "loja_pizzaria_express",
          "loja_nome": "Pizzaria Grajaú Express",
          "loja_avatar": "🍕",
          "item": "Combo Família: Pizza Grande + Refri 2L",
          "descricao": "Forno a lenha com borda recheada grátis.",
          "preco_brl": 65.00,
          "min_gc": 50,
          "max_gc": 150,
          "estoque": 6,
          "pix_loja": "11980168513",
          "zap_loja": "11980168513",
          "img": (
              "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600&q=80"
          ),
      },
      {
          "post_id": "post_lavajato_master",
          "loja_id": "loja_interlagos_wash",
          "loja_nome": "Lava Jato & Estética Interlagos",
          "loja_avatar": "🚘",
          "item": "Lavagem Completa + Cera de Carnaúba",
          "descricao": "Proteção para a pintura do seu veículo.",
          "preco_brl": 80.00,
          "min_gc": 50,
          "max_gc": 200,
          "estoque": 4,
          "pix_loja": "11991853488",
          "zap_loja": "11991853488",
          "img": (
              "https://images.unsplash.com/photo-1520340356584-f9917d1eea6f?w=600&q=80"
          ),
      },
  ]

  for post in posts:
    p_id = post["post_id"]
    l_id = post["loja_id"]

    saldo_loja = (
        carteira_engine.obter_saldos(l_id).get("geralcoin", 0)
        if db
        else st.session_state.saldo_lojistas.get(l_id, 0)
    )

    if saldo_loja <= 0:
      st.warning(
          f"⏸️ **Anúncio em Pausa ({post['loja_nome']}):** O comerciante está"
          " aguardando recarga de GeralCoins para liberar novas recompensas."
      )
      continue

    stats = obter_stats(p_id)
    link_direto = f"https://geralja.app/?post={p_id}"

    with st.container(border=True):
      st.markdown(
          f"### {post['loja_avatar']} {post['loja_nome']} <small"
          f" style='font-size:12px;'>(Orçamento: {saldo_loja} GC)</small>",
          unsafe_allow_html=True,
      )
      st.image(post["img"], use_container_width=True)
      st.subheader(post["item"])
      st.write(post["descricao"])

      desc_max_brl = post["max_gc"] * 0.10
      st.success(
          f"💵 **De R$ {post['preco_brl']:.2f} por até R$"
          f" {post['preco_brl'] - desc_max_brl:.2f}** (Usando {post['max_gc']}"
          " GC)"
      )

      st.info(
          f"👍 **{stats['likes']}** Curtidas | 💬 **{len(stats['comments'])}**"
          f" Comentários | 📢 **{stats['shares']}** Compartilhamentos"
      )

      c1, c2, c3 = st.columns(3)
      if c1.button("👍 Curtir\n1 GeralCoin", key=f"lk_{p_id}"):
        ok, msg = processar_ppe(
            user_id,
            l_id,
            p_id,
            "LIKE",
            1,
            "Parabéns! +1 GeralCoin (paga pelo lojista) creditada!",
        )
        if ok:
          st.toast(msg, icon="🎉")
        else:
          st.warning(msg)
        time.sleep(0.4)
        st.rerun()

      with c2:
        with st.popover("💬 Comentar\n2 GeralCoins"):
          txt = st.text_input("Comentário:", key=f"in_comm_{p_id}")
          if st.button("Enviar", key=f"sub_comm_{p_id}"):
            if len(txt.strip()) >= 3:
              ok, msg = processar_ppe(
                  user_id,
                  l_id,
                  p_id,
                  "COMMENT",
                  2,
                  "Uau! +2 GeralCoins (pagas pelo lojista) creditadas!",
                  texto_comentario=txt,
              )
              if ok:
                st.toast(msg, icon="💬")
              else:
                st.warning(msg)
              time.sleep(0.4)
              st.rerun()

      with c3:
        with st.popover("📢 Divulgar\n3 GeralCoins"):
          st.write("Escolha onde compartilhar:")
          link_zap = f"https://api.whatsapp.com/send?text={urllib.parse.quote('Confira esta oferta no GeralJá: ' + link_direto)}"
          st.markdown(
              f'<a href="{link_zap}" target="_blank">📲 Compartilhar no'
              " WhatsApp</a>",
              unsafe_allow_html=True,
          )
          if st.button("✅ Confirmar Crédito", key=f"sub_sh_{p_id}"):
            ok, msg = processar_ppe(
                user_id,
                l_id,
                p_id,
                "SHARE",
                3,
                "Parabéns! +3 GeralCoins (pagas pelo lojista) creditadas!",
            )
            if ok:
              st.toast(msg, icon="📢")
            else:
              st.warning(msg)
            time.sleep(0.4)
            st.rerun()

      with st.expander(f"🔽 Ver Comentários ({len(stats['comments'])})"):
        for comm in stats["comments"]:
          st.write(f"💬 **{comm['user']}** ({comm['data']}): {comm['texto']}")

      if st.button(
          f"🎟️ RESGATAR CUPOM DA {post['loja_nome'].upper()}",
          key=f"resg_{p_id}",
          type="primary",
          use_container_width=True,
      ):
        if saldo_gc < post["min_gc"]:
          st.error(
              f"⚠️ Saldo insuficiente! Esta oferta exige no mínimo"
              f" **{post['min_gc']} GeralCoins**."
          )
        else:
          gc_usar = min(saldo_gc, post["max_gc"])
          desconto = gc_usar * 0.10
          valor_pagar = post["preco_brl"] - desconto

          if db:
            carteira_engine.movimentar_saldo(
                user_id, "geralcoin", gc_usar, "DEBITO", f"RESGATE_{p_id}"
            )
          else:
            st.session_state.mock_saldos["geralcoin"] -= gc_usar

          v_code = f"GJ-{user_id[-4:]}-{int(time.time()) % 10000}"
          st.balloons()

          with st.container(border=True):
            st.subheader("🎟️ VOUCHER OFICIAL DE DESCONTO")
            st.write(f"**Código:** `{v_code}`")
            st.write(f"**Produto:** {post['item']}")
            st.write(f"**Desconto ({gc_usar} GC):** -R$ {desconto:.2f}")
            st.markdown(
                f"### **TOTAL A PAGAR NO PIX:** R$ {valor_pagar:.2f}"
            )
            st.info(f"🔑 Chave PIX do Estabelecimento: `{post['pix_loja']}`")

          msg_zap = (
              f"🚨 *PEDIDO COM CUPOM - GERALJÁ*\n\n🎟️ *Voucher:* {v_code}\n👤"
              f" *Cliente:* {user_id}\n📦 *Item:* {post['item']}\n✅ *TOTAL NO"
              f" PIX:* R$ {valor_pagar:.2f}"
          )
          link_w = f"https://api.whatsapp.com/send?phone={post['zap_loja']}&text={urllib.parse.quote(msg_zap)}"
          st.markdown(
              f'<a href="{link_w}" target="_blank" style="display:block;'
              " background:#25D366; color:white; text-align:center;"
              " padding:15px; border-radius:12px; font-weight:bold;"
              ' text-decoration:none;">💬 ENVIAR COMPROVANTE E PEDIDO NO'
              " WHATSAPP DA LOJA</a>",
              unsafe_allow_html=True,
          )


# ==============================================================================
# 6. CONTAINERS SECUNDÁRIOS DO ECOSSISTEMA
# ==============================================================================
def container_busca_e_servicos():
  st.subheader("🔍 Encontre Serviços no Grajaú")
  st.text_input("O que você procura hoje?", placeholder="Ex: Mecânico, Pizza...")


def container_painel_parceiro():
  st.subheader("👨‍💼 Painel do Comerciante")
  st.write("Compre pacotes de GeralCoins e mantenha seus anúncios ativos!")


# ==============================================================================
# 7. ROTEADOR AUTOMÁTICO DE ABAS (PINO DE ENGATE DA CARRETA)
# ==============================================================================
# LISTA CENTRAL DE ENGATE: Para alterar módulos, basta mudar esta lista simples!
CONTAINERS_ENGATADOS = [
    ("🛍️ Vitrine Social & Cupons (PPE)", container_vitrine_social_ppe),
    ("🔍 Buscar Serviços", container_busca_e_servicos),
    ("👨‍💼 Painel do Lojista", container_painel_parceiro),
]

# Montagem automática das abas
titulos_abas = [c[0] for c in CONTAINERS_ENGATADOS]
abas_renderizadas = st.tabs(titulos_abas)

for i, (nome, funcao_container) in enumerate(CONTAINERS_ENGATADOS):
  with abas_renderizadas[i]:
    executar_bloco_seguro(nome, funcao_container)
