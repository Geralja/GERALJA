import base64
from datetime import datetime
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
import pandas as pd
from PIL import Image
import pytz
import requests
import streamlit as st
import streamlit.components.v1 as components

# --- IMPORTAÇÕES DEFENSIVAS DE COMPONENTES EXTERNOS ---
try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    import feedparser
except ImportError:
    feedparser = None

try:
    from streamlit_js_eval import get_geolocation, streamlit_js_eval
except ImportError:
    get_geolocation, streamlit_js_eval = None, None

try:
    import gspread
except ImportError:
    gspread = None

try:
    import nltk
except ImportError:
    nltk = None

try:
    from fuzzywuzzy import fuzz, process
except ImportError:
    fuzz, process = None, None

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO (MERCADO LIVRE)
# ==========================================
st.set_page_config(
    page_title="GeralJá - Portal, Serviços & Relatórios",
    page_icon="🟡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS inspirada no Mercado Livre
st.markdown("""
<style>
    /* Fundo da aplicação */
    .stApp {
        background-color: #EBEBEB;
    }
    
    /* Topo Amarelo Mercado Livre */
    header[data-testid="stHeader"] {
        background: linear-gradient(90deg, #FFF159 0%, #FFE600 100%);
    }
    
    /* Menu Lateral */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #DCDCDC;
    }
    
    /* Cabeçalho Principal */
    .main-header {
        background: linear-gradient(90deg, #FFF159 0%, #FFE600 100%);
        padding: 18px 25px;
        border-radius: 8px;
        color: #333333;
        font-weight: 800;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
    }
    
    /* Card Container */
    .ml-card {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        margin-bottom: 15px;
        border: 1px solid #E6E6E6;
    }
    
    /* Badge Verde Mercado Livre */
    .ml-badge {
        background-color: #00A650;
        color: #FFFFFF;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: 700;
    }
    
    /* Botão Principal Azul */
    div.stButton > button {
        background-color: #3483FA;
        color: #FFFFFF;
        font-weight: 600;
        border-radius: 6px;
        border: none;
        padding: 0.5rem 1.2rem;
        width: 100%;
        transition: background-color 0.2s ease;
    }
    div.stButton > button:hover {
        background-color: #2968C8;
        color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. INICIALIZAÇÃO SEGURA DO FIREBASE
# ==========================================
@st.cache_resource
def init_firestore():
    cred_file = "serviceAccountKey.json"
    if os.path.exists(cred_file):
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(cred_file)
                firebase_admin.initialize_app(cred)
            return firestore.client()
        except Exception as e:
            st.sidebar.warning(f"Erro ao inicializar Firestore: {e}")
            return None
    return None

db = init_firestore()

# ==========================================
# 3. ESTADO DA SESSÃO (MEMÓRIA LOCAL)
# ==========================================
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {
        "nome": "Morador do Grajaú",
        "email": "cliente@grajautem.com.br",
        "telefone": "(11) 98016-8513",
        "cidade": "São Paulo - SP"
    }

if "wallet_balance" not in st.session_state:
    st.session_state.wallet_balance = 250.00

if "transactions" not in st.session_state:
    st.session_state.transactions = [
        {"data": "2026-08-20", "tipo": "Credito", "descricao": "Recarga Inicial via PIX", "valor": 150.00},
        {"data": "2026-08-22", "tipo": "Debito", "descricao": "Resgate Cupom Hamburgueria", "valor": 28.50},
        {"data": "2026-08-25", "tipo": "Credito", "descricao": "Recarga via PIX", "valor": 100.00},
        {"data": "2026-08-28", "tipo": "Debito", "descricao": "Resgate Lavagem Automotiva", "valor": 42.00},
        {"data": "2026-08-31", "tipo": "Credito", "descricao": "Bônus Clube de Ofertas", "valor": 70.50}
    ]

# ==========================================
# 4. MÓDULOS DO SISTEMA
# ==========================================

# --- MÓDULO 1: PERFIL / CADASTRO ---
def render_perfil():
    st.markdown("### 👤 Perfil e Cadastro do Usuário")
    st.caption("Mantenha seus dados atualizados para serviços locais e cobranças.")
    
    with st.form("form_perfil"):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome Completo", value=st.session_state.user_profile["nome"])
            email = st.text_input("E-mail", value=st.session_state.user_profile["email"])
        with col2:
            telefone = st.text_input("Telefone / WhatsApp", value=st.session_state.user_profile["telefone"])
            cidade = st.text_input("Cidade / Bairro", value=st.session_state.user_profile["cidade"])
            
        salvar = st.form_submit_button("Salvar Alterações")
        
        if salvar:
            st.session_state.user_profile.update({
                "nome": nome,
                "email": email,
                "telefone": telefone,
                "cidade": cidade
            })
            
            if db:
                try:
                    db.collection("perfil_usuarios").document(email).set({
                        "nome": nome,
                        "email": email,
                        "telefone": telefone,
                        "cidade": cidade,
                        "atualizado_em": datetime.now().isoformat()
                    }, merge=True)
                    st.success("Perfil sincronizado com o Cloud Firestore!")
                except Exception as e:
                    st.error(f"Erro ao sincronizar com Firestore: {e}")
            else:
                st.success("Perfil atualizado localmente!")

# --- MÓDULO 2: CARTEIRA DIGITAL ---
def render_carteira():
    st.markdown("### 💳 Carteira Digital do Cliente")
    
    col_bal, col_actions = st.columns([1, 2])
    
    with col_bal:
        st.markdown("<div class='ml-card'>", unsafe_allow_html=True)
        st.metric(label="Saldo Atual", value=f"R$ {st.session_state.wallet_balance:.2f}")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_actions:
        st.markdown("<div class='ml-card'>", unsafe_allow_html=True)
        st.subheader("Adicionar Saldo")
        val_recarga = st.number_input("Valor da Recarga (R$)", min_value=10.0, max_value=5000.0, value=50.0, step=10.0)
        
        if st.button("Realizar Recarga via PIX"):
            st.session_state.wallet_balance += val_recarga
            st.session_state.transactions.insert(0, {
                "data": datetime.now().strftime("%Y-%m-%d"),
                "tipo": "Credito",
                "descricao": "Recarga via PIX",
                "valor": val_recarga
            })
            
            if db:
                try:
                    db.collection("carteiras").document(st.session_state.user_profile["email"]).set({
                        "saldo": st.session_state.wallet_balance,
                        "ultima_atualizacao": datetime.now().isoformat()
                    }, merge=True)
                except Exception:
                    pass
                    
            st.success(f"Recarga de R$ {val_recarga:.2f} confirmada!")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("#### Movimentações Recentes")
    df_trans = pd.DataFrame(st.session_state.transactions)
    st.dataframe(df_trans, use_container_width=True)

# --- MÓDULO 3: CONVERSOR DE MOEDAS ---
def render_conversor():
    st.markdown("### 💱 Conversor de Moedas")
    st.caption("Cotações para cálculos de conversão e pagamentos.")
    
    taxas = {
        "BRL (Real)": 1.0,
        "USD (Dólar Americano)": 5.60,
        "EUR (Euro)": 6.10,
        "GBP (Libra Esterlina)": 7.30
    }
    
    st.markdown("<div class='ml-card'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        valor = st.number_input("Valor", min_value=1.0, value=100.0, step=10.0)
    with col2:
        moeda_origem = st.selectbox("De:", list(taxas.keys()), index=0)
    with col3:
        moeda_destino = st.selectbox("Para:", list(taxas.keys()), index=1)
        
    valor_em_brl = valor * taxas[moeda_origem]
    resultado = valor_em_brl / taxas[moeda_destino]
    
    st.markdown("---")
    st.subheader(f"Resultado: **{resultado:.2f}** {moeda_destino.split()[0]}")
    st.caption(f"Taxa base: 1 {moeda_origem.split()[0]} = {(taxas[moeda_origem]/taxas[moeda_destino]):.4f} {moeda_destino.split()[0]}")
    st.markdown("</div>", unsafe_allow_html=True)

# --- MÓDULO 4: CLUBE DE OFERTAS ---
def render_clube_ofertas():
    st.markdown("### 🏷️ Clube de Ofertas Grajaú Tem")
    st.caption("Descontos exclusivos no comércio da região.")
    
    ofertas = [
        {"titulo": "Almoço Executivo - Restaurante Sabor do Bairro", "desc": "Prato feito completo + Suco natural", "preco_original": 30.00, "preco_promo": 21.00, "desconto": "30% OFF"},
        {"titulo": "Lavagem Completa Automotiva", "desc": "Ducha + Cera líquida + Pretinho", "preco_original": 60.00, "preco_promo": 42.00, "desconto": "30% OFF"},
        {"titulo": "Corte de Cabelo Masculino / Barba", "desc": "Atendimento com hora marcada", "preco_original": 45.00, "preco_promo": 30.00, "desconto": "33% OFF"},
        {"titulo": "Combo Hamburguer Artesanal + Batata", "desc": "Pão brioche, 180g de carne e cheddar", "preco_original": 38.00, "preco_promo": 28.50, "desconto": "25% OFF"}
    ]
    
    cols = st.columns(2)
    for idx, oferta in enumerate(ofertas):
        with cols[idx % 2]:
            st.markdown(f"""
            <div class='ml-card'>
                <span class='ml-badge'>{oferta['desconto']}</span>
                <h4 style='margin-top: 10px; color: #333;'>{oferta['titulo']}</h4>
                <p style='color: #666; font-size: 0.9rem;'>{oferta['desc']}</p>
                <p style='font-size: 1.1rem; color: #333;'>
                    <s>R$ {oferta['preco_original']:.2f}</s> ➔ <b style='color: #00A650; font-size: 1.3rem;'>R$ {oferta['preco_promo']:.2f}</b>
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Resgatar Oferta #{idx+1}", key=f"btn_oferta_{idx}"):
                if st.session_state.wallet_balance >= oferta['preco_promo']:
                    st.session_state.wallet_balance -= oferta['preco_promo']
                    st.session_state.transactions.insert(0, {
                        "data": datetime.now().strftime("%Y-%m-%d"),
                        "tipo": "Debito",
                        "descricao": f"Oferta: {oferta['titulo'][:25]}...",
                        "valor": oferta['preco_promo']
                    })
                    st.success(f"Oferta resgatada! Código enviado para {st.session_state.user_profile['telefone']}.")
                    st.rerun()
                else:
                    st.error("Saldo insuficiente na carteira para esta oferta.")

# --- MÓDULO 5: RELATÓRIOS & ANALYTICS (NOVO) ---
def render_relatorios():
    st.markdown("### 📊 Relatórios e Métricas Financeiras")
    st.caption("Análise consolidada de transações, movimentações e utilização do sistema.")
    
    df = pd.DataFrame(st.session_state.transactions)
    
    # KPIs Rápidos
    total_creditos = df[df['tipo'] == 'Credito']['valor'].sum()
    total_debitos = df[df['tipo'] == 'Debito']['valor'].sum()
    saldo_liquido = total_creditos - total_debitos
    qtd_transacoes = len(df)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Recarregado", f"R$ {total_creditos:.2f}")
    with col2:
        st.metric("Total Empregado/Gasto", f"R$ {total_debitos:.2f}")
    with col3:
        st.metric("Balanço do Período", f"R$ {saldo_liquido:.2f}")
    with col4:
        st.metric("Total de Operações", f"{qtd_transacoes}")
        
    st.markdown("<div class='ml-card'>", unsafe_allow_html=True)
    st.subheader("Evolução Financeira por Tipo de Operação")
    
    # Gráfico de barras simples
    df_chart = df.groupby(['data', 'tipo'])['valor'].sum().unstack().fillna(0)
    st.bar_chart(df_chart)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Exportação de Dados
    st.markdown("#### Exportar Relatório")
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="📥 Baixar Relatório em CSV",
        data=csv_buffer.getvalue(),
        file_name=f"relatorio_financeiro_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

# ==========================================
# 5. NAVEGAÇÃO E EXECUÇÃO PRINCIPAL
# ==========================================
def main():
    st.markdown("<div class='main-header'><h1>🟡 GeralJá — Vitrine, Serviços & Relatórios</h1></div>", unsafe_allow_html=True)
    
    menu_opcoes = [
        "👤 Perfil e Cadastro",
        "💳 Carteira Digital",
        "💱 Conversor de Moedas",
        "🏷️ Clube de Ofertas",
        "📊 Relatórios & Analytics"
    ]
    
    escolha = st.sidebar.radio("Navegação do Sistema", menu_opcoes)
    
    st.sidebar.markdown("---")
    st.sidebar.info(
        f"**Usuário:** {st.session_state.user_profile['nome']}\n\n"
        f"**Saldo Disponível:** R$ {st.session_state.wallet_balance:.2f}"
    )
    
    # Roteamento dos Módulos
    if escolha == "👤 Perfil e Cadastro":
        render_perfil()
    elif escolha == "💳 Carteira Digital":
        render_carteira()
    elif escolha == "💱 Conversor de Moedas":
        render_conversor()
    elif escolha == "🏷️ Clube de Ofertas":
        render_clube_ofertas()
    elif escolha == "📊 Relatórios & Analytics":
        render_relatorios()

if __name__ == "__main__":
    main()
