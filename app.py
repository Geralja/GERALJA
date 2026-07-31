# ==============================================================================
# GERALJÁ: CRIANDO SOLUÇÕES - SISTEMA UNIFICADO MASTER
# VERSÃO 5.0 SOCIAL & COMMERCIAL ELITE EDITION (2026)
# ==============================================================================
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import math
import re
import time
import io
import pandas as pd
from datetime import datetime
import pytz
import unicodedata
import requests
import feedparser
import urllib.parse
from PIL import Image

# --- BIBLIOTECAS DE IA ---
from groq import Groq
import google.generativeai as genai

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILOS CSS
# ==============================================================================
st.set_page_config(
    page_title="GeralJá | Criando Soluções",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inicialização do Tema e Sessão
if 'modo_noite' not in st.session_state:
    st.session_state.modo_noite = False

for key, default in {
    'auth': False,
    'user_id': None,
    'admin_logado': False,
    'minha_lat': -23.5505,
    'minha_lon': -46.6333
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    * {{ font-family: 'Inter', sans-serif; }}
    .main .block-container {{ padding-top: 1rem !important; padding-bottom: 1rem !important; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    
    .stApp {{ 
        background-color: {"#0D1117" if st.session_state.modo_noite else "#FFFAFA"} !important; 
        color: {"#FFFFFF" if st.session_state.modo_noite else "#1A1A1B"} !important; 
    }}
    
    .header-container {{ 
        background: linear-gradient(135deg, #0047AB 0%, #FF8C00 100%); 
        padding: 20px 15px; 
        border-radius: 0 0 25px 25px; 
        text-align: center; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); 
        margin-bottom: 15px;
        margin-top: -1rem;
    }}
    .logo-azul {{ color: #FFFFFF; font-weight: 900; font-size: 38px; letter-spacing: -1px; text-shadow: 1px 1px 3px rgba(0,0,0,0.2); }}
    .logo-laranja {{ color: #FFD700; font-weight: 900; font-size: 38px; letter-spacing: -1px; text-shadow: 1px 1px 3px rgba(0,0,0,0.2); }}
    .sub-logo {{ color: #FFFFFF; font-weight: 600; font-size: 12px; opacity: 0.9; }}
    
    .card-prestador {{
        background-color: {"#161B22" if st.session_state.modo_noite else "#FFFFFF"};
        border: 1px solid {"#30363D" if st.session_state.modo_noite else "#E2E8F0"};
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 15px;
        border-left: 6px solid #0047AB;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }}

    @media (max-width: 640px) {{
        .header-container {{ padding: 15px 10px; margin-bottom: 10px; }}
        .logo-azul, .logo-laranja {{ font-size: 32px; }}
        .stButton button {{ width: 100%; }}
    }}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. BANCO DE DADOS E CONEXÕES APIs
# ==============================================================================
@st.cache_resource
def conectar_banco_master():
    if not firebase_admin._apps:
        try:
            if "firebase" in st.secrets and "base64" in st.secrets["firebase"]:
                b64_key = st.secrets["firebase"]["base64"]
                decoded_json = base64.b64decode(b64_key).decode("utf-8")
                cred = credentials.Certificate(json.loads(decoded_json))
                firebase_admin.initialize_app(cred)
            else:
                st.error("⚠️ Credencial 'firebase.base64' não encontrada nos Secrets.")
                st.stop()
        except Exception as e:
            st.error(f"❌ Erro ao inicializar o Firebase: {e}")
            st.stop()
    return firebase_admin.get_app()

app_engine = conectar_banco_master()
db = firestore.client()

client_groq = None
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    if "GROQ_API_KEY" in st.secrets:
        client_groq = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    pass

CATEGORIAS_PADRAO = [
    "Encanador", "Eletricista", "Pintor", "Pedreiro", "Mecânico", 
    "Pizzaria", "Lanchonete", "Restaurante", "Barbearia/Salão", "Pet Shop", "Outros"
]

CONCEITOS_EXPANDIDOS = {
    "pizza": "Pizzaria", "pizzaria": "Pizzaria", "fome": "Pizzaria",
    "lanche": "Lanchonete", "hamburguer": "Lanchonete", "marmita": "Restaurante",
    "cano": "Encanador", "vazamento": "Encanador", "pia": "Encanador",
    "luz": "Eletricista", "curto": "Eletricista", "fio": "Eletricista",
    "carro": "Mecânico", "motor": "Mecânico", "pneu": "Mecânico",
    "cabelo": "Barbearia/Salão", "corte": "Barbearia/Salão", "barba": "Barbearia/Salão",
    "cachorro": "Pet Shop", "gato": "Pet Shop", "racao": "Pet Shop"
}

# ==============================================================================
# 3. FUNÇÕES UTILITÁRIAS
# ==============================================================================
def limpar_whatsapp(numero):
    num = re.sub(r'\D', '', str(numero))
    if not num.startswith('55') and len(num) >= 10:
        num = f"55{num}"
    return num

def normalizar_texto(texto):
    if not texto: return ""
    return "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn').lower().strip()

def otimizar_imagem(file, size=(400, 400)):
    try:
        img = Image.open(file)
        if img.mode in ("RGBA", "P"): 
            img = img.convert("RGB")
        img.thumbnail(size)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=75)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return ""

def processar_categoria_ia(texto):
    t_clean = normalizar_texto(texto)
    for chave, cat in CONCEITOS_EXPANDIDOS.items():
        if chave in t_clean:
            return cat
            
    if client_groq:
        try:
            prompt = f"Classifique a busca '{texto}' em exatamente uma destas categorias: {', '.join(CATEGORIAS_PADRAO)}. Responda apenas o nome da categoria."
            res = client_groq.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192", 
                temperature=0.1
            )
            cat_retornada = res.choices[0].message.content.strip()
            if cat_retornada in CATEGORIAS_PADRAO:
                return cat_retornada
        except Exception:
            pass
    return "Geral"

# ==============================================================================
# 4. INTERFACE PRINCIPAL & CABEÇALHO
# ==============================================================================
c_t1, c_t2 = st.columns([2, 8])
with c_t1:
    st.session_state.modo_noite = st.toggle("🌙 Modo Noite", value=st.session_state.modo_noite)

st.markdown("""
<div class="header-container">
    <span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span><br>
    <span class="sub-logo">MÓDULO UNIFICADO MASTER - GRAJAÚ TEM</span>
</div>
""", unsafe_allow_html=True)

# Navegação Lateral & Abas
lista_abas = ["🔍 BUSCAR", "🚀 CADASTRAR", "👤 MEU PERFIL", "⭐ FEEDBACK"]

with st.sidebar:
    st.markdown("### 🔐 Acesso Restrito")
    comando = st.text_input("Código de Acesso", type="password", key="admin_key")
    if comando in ["abracadabra", "geralja_master"]:
        lista_abas.append("👑 ADMIN")
    if comando in ["financeiro2026", "geralja_master"]:
        lista_abas.append("📊 FINANCEIRO")

menu_abas = st.tabs(lista_abas)

# ==============================================================================
# 5. ABA 1: BUSCA INTELIGENTE & NOTÍCIAS
# ==============================================================================
with menu_abas[0]:
    st.markdown("### 🏙️ O que você precisa no Grajaú hoje?")
    
    col_b1, col_b2 = st.columns([3, 1])
    termo_busca = col_b1.text_input("Ex: 'Cano vazando', 'Marmita', 'Pizzaria'", key="main_search")
    raio_km = col_b2.select_slider("Raio (KM)", options=[1, 3, 5, 10, 20, 50], value=5)

    if termo_busca:
        cat_identificada = processar_categoria_ia(termo_busca)
        st.info(f"🔍 Categoria identificada por IA: **{cat_identificada}**")
        
        docs_profs = db.collection("profissionais").where("aprovado", "==", True).stream()
        encontrou = False
        
        for doc in docs_profs:
            p = doc.to_dict()
            p_id = doc.id
            nome = p.get('nome', 'Profissional')
            area = p.get('area', '')
            desc = p.get('descricao', '')
            zap = p.get('whatsapp', '')
            foto = p.get('foto_url', 'https://cdn-icons-png.flaticon.com/512/149/149071.png')
            
            # Match por Categoria ou Nome
            if (cat_identificada.lower() in area.lower()) or (normalizar_texto(termo_busca) in normalizar_texto(nome)) or (cat_identificada == "Geral"):
                encontrou = True
                zap_limpo = limpar_whatsapp(zap)
                msg_zap = urllib.parse.quote(f"Olá {nome}, vi seu anúncio no GeralJá e gostaria de um orçamento!")
                link_zap = f"https://api.whatsapp.com/send?phone={zap_limpo}&text={msg_zap}"
                
                # Atualiza cliques
                def registrar_clique(doc_id):
                    db.collection("profissionais").document(doc_id).update({"cliques": firestore.Increment(1)})

                st.markdown(f"""
                <div class="card-prestador">
                    <div style="display:flex; align-items:center; gap:15px;">
                        <img src="{foto}" style="width:70px; height:70px; border-radius:50%; object-fit:cover;">
                        <div>
                            <h3 style="margin:0; color:#0047AB;">{nome}</h3>
                            <p style="margin:2px 0; font-weight:bold;">📍 {area}</p>
                            <p style="margin:2px 0; font-size:14px;">{desc}</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                c_btn1, c_btn2 = st.columns([2, 2])
                with c_btn1:
                    st.markdown(f'<a href="{link_zap}" target="_blank" style="display:block; text-align:center; background:#25D366; color:white; padding:10px; border-radius:8px; text-decoration:none; font-weight:bold;">💬 Chamar no WhatsApp</a>', unsafe_allow_html=True)
                with c_btn2:
                    if st.button(f"⭐ Avaliar / Ver Detalhes", key=f"det_{p_id}"):
                        registrar_clique(p_id)
                        st.success(f"Contato contabilizado para {nome}!")

        if not encontrou:
            st.warning("Nenhum profissional ou comércio encontrado para esse termo na região.")

    st.markdown("---")
    st.subheader("📰 Plantão de Notícias Locais — Grajaú Tem")
    
    try:
        feed = feedparser.parse("https://news.google.com/rss/search?q=Grajaú+São+Paulo&hl=pt-BR&gl=BR&ceid=BR:pt-419")
        if feed.entries:
            cols_noticias = st.columns(3)
            for idx, item in enumerate(feed.entries[:3]):
                with cols_noticias[idx]:
                    st.markdown(f"""
                    <div style="border:1px solid #CCC; border-radius:10px; padding:12px; height:180px; background:white; color:#222;">
                        <small style="color:#FF8C00; font-weight:bold;">GOOGLE NEWS</small>
                        <h4 style="font-size:13px; margin:5px 0;">{item.title[:65]}...</h4>
                        <a href="{item.link}" target="_blank" style="color:#0047AB; font-weight:bold; font-size:12px; text-decoration:none;">Ler notícia completa ➔</a>
                    </div>
                    """, unsafe_allow_html=True)
    except Exception:
        st.caption("Feed de notícias temporariamente offline.")

# ==============================================================================
# 6. ABA 2: CADASTRO DE PARCEIRO
# ==============================================================================
with menu_abas[1]:
    st.header("🚀 Cadastre seu Negócio ou Serviço no GeralJá")
    st.write("Junte-se à maior vitrine comercial do Grajaú e receba clientes direto no seu WhatsApp.")
    
    with st.form("form_cadastro_novo"):
        cad_nome = st.text_input("Nome Comercial ou Seu Nome *")
        cad_zap = st.text_input("WhatsApp com DDD (Somente números) *")
        cad_email = st.text_input("Seu E-mail *")
        cad_senha = st.text_input("Crie uma Senha de Acesso *", type="password")
        cad_area = st.selectbox("Selecione sua Categoria Principal *", CATEGORIAS_PADRAO)
        cad_desc = st.text_area("Descrição Breve do Serviço ou Produtos", max_chars=250)
        cad_foto = st.file_uploader("Foto de Perfil ou Logomarca", type=['jpg', 'jpeg', 'png'])
        
        btn_cadastrar = st.form_submit_button("CONCLUIR CADASTRO GRATUITO", use_container_width=True)
        
        if btn_cadastrar:
            zap_limpo = re.sub(r'\D', '', cad_zap)
            if cad_nome and zap_limpo and cad_senha and cad_email:
                foto_b64 = otimizar_imagem(cad_foto) if cad_foto else ""
                url_foto = f"data:image/jpeg;base64,{foto_b64}" if foto_b64 else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
                
                dados_parceiro = {
                    "nome": cad_nome,
                    "whatsapp": zap_limpo,
                    "email": cad_email,
                    "senha": cad_senha,
                    "area": cad_area,
                    "descricao": cad_desc,
                    "foto_url": url_foto,
                    "saldo": 20, # Bônus de boas-vindas
                    "cliques": 0,
                    "aprovado": True,
                    "tipo_conta": "prestador",
                    "produtos": [],
                    "data_cadastro": datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%Y-%m-%d %H:%M:%S")
                }
                
                db.collection("profissionais").document(zap_limpo).set(dados_parceiro)
                st.success("🎉 Cadastro aprovado e publicado com sucesso! Vá para a aba 'MEU PERFIL' para fazer login.")
            else:
                st.error("Preencha todos os campos obrigatórios (*).")

# ==============================================================================
# 7. ABA 3: PERFIL DO USUÁRIO & GESTÃO DE PRODUTOS
# ==============================================================================
with menu_abas[2]:
    if not st.session_state.auth:
        st.subheader("🔐 Área Exclusiva do Parceiro")
        col_l1, col_l2 = st.columns(2)
        login_zap = col_l1.text_input("WhatsApp Cadastrado", key="log_zap")
        login_pw = col_l2.text_input("Sua Senha", type="password", key="log_pw")
        
        if st.button("ENTRAR NO PAINEL", use_container_width=True):
            z_limpo = re.sub(r'\D', '', login_zap)
            doc_user = db.collection("profissionais").document(z_limpo).get()
            
            if doc_user.exists and str(doc_user.to_dict().get('senha')) == str(login_pw):
                st.session_state.auth = True
                st.session_state.user_id = z_limpo
                st.success("Login efetuado com sucesso!")
                st.rerun()
            else:
                st.error("WhatsApp ou senha incorretos.")
    else:
        ref_user = db.collection("profissionais").document(st.session_state.user_id)
        dados_user = ref_user.get().to_dict()
        
        st.markdown(f"## Bem-vindo(a), {dados_user.get('nome')}! 👋")
        
        # Painel de Métricas
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Saldo de Moedas", f"🪙 {dados_user.get('saldo', 0)}")
        col_m2.metric("Cliques no WhatsApp", f"🚀 {dados_user.get('cliques', 0)}")
        col_m3.metric("Status da Conta", "Ativa ✅" if dados_user.get('aprovado') else "Pendente ⚠️")
        
        tab_p1, tab_p2 = st.tabs(["🛒 Minha Vitrine / Produtos", "⚙️ Opções da Conta"])
        
        with tab_p1:
            st.subheader("Gerenciador de Catálogo de Produtos")
            produtos = dados_user.get('produtos', [])
            
            with st.form("form_add_produto"):
                p_nome = st.text_input("Nome do Produto / Item")
                p_preco = st.number_input("Preço (R$)", min_value=0.0, format="%.2f")
                p_img = st.file_uploader("Foto do Produto", type=['jpg', 'png'])
                
                if st.form_submit_button("Adicionar à Vitrine"):
                    if p_nome and p_preco > 0:
                        img_prod = otimizar_imagem(p_img) if p_img else ""
                        produtos.append({
                            "nome": p_nome,
                            "preco": p_preco,
                            "foto": f"data:image/jpeg;base64,{img_prod}" if img_prod else ""
                        })
                        ref_user.update({"produtos": produtos, "tipo_conta": "comerciante"})
                        st.success("Produto adicionado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Informe o nome e um preço válido.")
            
            st.markdown("---")
            st.subheader("Seus Produtos Cadastrados")
            if produtos:
                cols_p = st.columns(3)
                for idx, prod in enumerate(produtos):
                    with cols_p[idx % 3]:
                        st.markdown(f"""
                        <div style="border:1px solid #DDD; padding:10px; border-radius:8px; text-align:center;">
                            <p style="font-weight:bold; margin:0;">{prod.get('nome')}</p>
                            <p style="color:#25D366; font-weight:bold;">R$ {prod.get('preco'):.2f}</p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.caption("Você ainda não tem produtos cadastrados.")

        with tab_p2:
            st.subheader("Configurações do Perfil")
            if st.button("🚪 Sair do Painel", use_container_width=True):
                st.session_state.auth = False
                st.session_state.user_id = None
                st.rerun()

# ==============================================================================
# 8. ABA 4: FEEDBACK
# ==============================================================================
with menu_abas[3]:
    st.header("⭐ Sua Opinião é Muito Importante")
    st.write("Ajude-nos a melhorar a plataforma GeralJá para todo o bairro do Grajaú.")
    
    nota = st.slider("Qual sua nota para o aplicativo?", 1, 5, 5)
    comentario = st.text_area("Deixe seu comentário ou sugestão")
    
    if st.button("ENVIAR AVALIAÇÃO"):
        if comentario:
            db.collection("feedbacks").add({
                "nota": nota,
                "comentario": comentario,
                "data": datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%Y-%m-%d %H:%M:%S")
            })
            st.success("Agradecemos pelo seu feedback!")
        else:
            st.error("Escreva um comentário antes de enviar.")

# ==============================================================================
# 9. ABAS RESTRITAS: ADMIN E FINANCEIRO (OPCIONAIS VIA SENHA)
# ==============================================================================
if "👑 ADMIN" in lista_abas:
    idx_admin = lista_abas.index("👑 ADMIN")
    with menu_abas[idx_admin]:
        st.header("👑 Painel Administrativo Master")
        
        if not st.session_state.admin_logado:
            ad_user = st.text_input("Usuário Admin", key="ad_u")
            ad_pass = st.text_input("Senha Admin", type="password", key="ad_p")
            if st.button("Autenticar GeralJá"):
                if ad_user == st.secrets.get("ADMIN_USER", "geralja") and ad_pass == st.secrets.get("ADMIN_PASS", "Bps36ocara"):
                    st.session_state.admin_logado = True
                    st.rerun()
                else:
                    st.error("Credenciais administrativas inválidas.")
        else:
            st.success("Autenticado como Diretor Master.")
            if st.button("Encerrar Sessão Admin"):
                st.session_state.admin_logado = False
                st.rerun()
            
            # Tabela Geral de Parceiros
            st.subheader("📋 Lista Geral de Profissionais")
            profs_stream = db.collection("profissionais").stream()
            lista_p = [doc.to_dict() | {"ID": doc.id} for doc in profs_stream]
            
            if lista_p:
                df_profs = pd.DataFrame(lista_p)
                st.dataframe(df_profs[['ID', 'nome', 'area', 'whatsapp', 'saldo', 'cliques']])

if "📊 FINANCEIRO" in lista_abas:
    idx_fin = lista_abas.index("📊 FINANCEIRO")
    with menu_abas[idx_fin]:
        st.header("📊 Métricas de Receita e Engajamento")
        profs_stream = db.collection("profissionais").stream()
        lista_p = [doc.to_dict() for doc in profs_stream]
        
        if lista_p:
            df_fin = pd.DataFrame(lista_p)
            col_f1, col_f2 = st.columns(2)
            col_f1.metric("Moedas Distribuídas", f"🪙 {df_fin['saldo'].sum() if 'saldo' in df_fin else 0}")
            col_f2.metric("Total de Interações/WhatsApp", f"💬 {df_fin['cliques'].sum() if 'cliques' in df_fin else 0}")

# ==============================================================================
# 10. RODAPÉ FIXO
# ==============================================================================
st.markdown("""
<hr>
<div style="text-align: center; padding: 10px; color: #64748B; font-size: 12px;">
    🛡️ GeralJá & Grajaú Tem © 2026 — Plataforma Protegida e Unificada
</div>
""", unsafe_allow_html=True)
