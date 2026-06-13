# ==============================================================================
# GERALJÁ MASTER ENGINE: SEU ECOSSISTEMA COMPLETO DE MARKETPLACE E MODERAÇÃO
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

# --- BIBLIOTECAS DE INTELIGÊNCIA E AGILIDADE ---
try:
    from fuzzywuzzy import process
except ImportError:
    process = None

try:
    from streamlit_js_eval import streamlit_js_eval, get_geolocation
except ImportError:
    pass

# ==============================================================================
# 🛡️ 1. CONFIGURAÇÕES DE DIRETRIZ E INFRAESTRUTURA DE NÍVEL SÊNIOR
# ==============================================================================
st.set_page_config(
    page_title="GeralJá | Plataforma Suprema",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constantes Estratégicas e Parâmetros Operacionais
CHAVE_ADMIN_ARQUITETO = "123" 
BONUS_WELCOME = 50
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
LAT_REF = -23.5505
LON_REF = -46.6333

CATEGORIAS_OFICIAIS = [
    "Pizzaria", "Lanchonete", "Restaurante", "Confeitaria", "Padaria", "Açaí", 
    "Sorveteria", "Adega", "Doceria", "Hortifruti", "Açougue", "Pastelaria", 
    "Encanador", "Eletricista", "Pintor", "Pedreiro", "Gesseiro", "Telhadista", 
    "Serralheiro", "Vidraceiro", "Marceneiro", "Marmoraria", "Calhas e Rufos", 
    "Dedetização", "Desentupidora", "Jardineiro", "Limpeza de Estofados",
    "Mecânico", "Borracheiro", "Guincho 24h", "Estética Automotiva", "Lava Jato", 
    "Loja de Roupas", "Calçados", "Loja de Variedades", "Relojoaria", "Joalheria", 
    "Ótica", "Material de Construção", "Tintas", "Móveis", "Eletrodomésticos",
    "Farmácia", "Barbearia/Salão", "Manicure/Pedicure", "Estética Facial", 
    "TI", "Assistência Técnica", "Celulares", "Informática", "Refrigeração", 
    "Chaveiro", "Montador", "Freteiro", "Carreto", "Motoboy/Entregas",
    "Pet Shop", "Veterinário", "Banho e Tosa", "Diarista", "Outros"
]

CONCEITOS_MAPPING = {
    "pizza": "Pizzaria", "fome": "Pizzaria", "massa": "Pizzaria",
    "lanche": "Lanchonete", "hamburguer": "Lanchonete", "burger": "Lanchonete",
    "comida": "Restaurante", "almoco": "Restaurante", "marmita": "Restaurante",
    "doce": "Confeitaria", "bolo": "Confeitaria", "pao": "Padaria",
    "acai": "Açaí", "sorvete": "Sorveteria", "cerveja": "Adega", "bebida": "Adega",
    "roupa": "Loja de Roupas", "moda": "Loja de Roupas", "sapato": "Calçados",
    "remedio": "Farmácia", "farmacia": "Farmácia", "cabelo": "Barbearia/Salão",
    "celular": "Assistência Técnica", "iphone": "Assistência Técnica", "computador": "TI",
    "vazamento": "Encanador", "cano": "Encanador", "curto": "Eletricista", "luz": "Eletricista",
    "pintar": "Pintor", "reforma": "Pedreiro", "piso": "Pedreiro", "chave": "Chaveiro",
    "carro": "Mecânico", "pneu": "Borracheiro", "frete": "Freteiro", "faxina": "Diarista"
}

# Inicialização de Estados Universais Seguros
if 'modo_noite' not in st.session_state:
    st.session_state.modo_noite = False  # PADRÃO INDISCUTÍVEL: MODO DIA (LIGHT MODE)
if 'auth' not in st.session_state:
    st.session_state.auth = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = {}

# Inicialização Blindada do Firestore
if not firebase_admin._apps:
    try:
        if "FIREBASE_BASE64" in st.secrets:
            fb_dict = json.loads(base64.b64decode(st.secrets["FIREBASE_BASE64"]).decode("utf-8"))
            firebase_admin.initialize_app(credentials.Certificate(fb_dict))
        elif "firebase" in st.secrets and "base64" in st.secrets["firebase"]:
            fb_dict = json.loads(base64.b64decode(st.secrets["firebase"]["base64"]).decode("utf-8"))
            firebase_admin.initialize_app(credentials.Certificate(fb_dict))
    except Exception as e:
        st.error(f"Aviso de Inicialização Firebase: {e}")

db = firestore.client()

# ==============================================================================
# ⚙️ 2. CLASSE DE INFRAESTRUTURA DESIGNADA (GERALJÁ ENGINE)
# ==============================================================================
class GeralJaEngine:
    def __init__(self):
        self.fuso = pytz.timezone('America/Sao_Paulo')
    
    def sanitizar(self, codigo_bruto):
        if not codigo_bruto: return ""
        limpo = codigo_bruto.replace('\u00a0', ' ').replace('\xa0', ' ')
        return re.sub(r'[^\x20-\x7E\n\t\r]', '', limpo)

    def injetar_modulo(self, nome_arquivo, conteudo):
        conteudo_limpo = self.sanitizar(conteudo)
        try:
            with open(nome_arquivo, "w", encoding="utf-8") as f:
                f.write(conteudo_limpo)
            return True
        except:
            return False

engine = GeralJaEngine()

# ==============================================================================
# 🧰 3. UTENSÍLIOS DE SUPORTE OPERACIONAL E GEOLOCALIZAÇÃO
# ==============================================================================
def limpar_whatsapp(numero):
    num = re.sub(r'\D', '', str(numero))
    if not num.startswith('55') and len(num) >= 10:
        num = f"55{num}"
    return num

def normalizar_texto(texto):
    if not texto: return ""
    return "".join(ch for ch in unicodedata.normalize('NFKD', str(texto)) 
                   if unicodedata.category(ch) != 'Mn').lower().strip()

def calcular_distancia_real(lat1, lon1, lat2, lon2):
    try:
        if None in [lat1, lon1, lat2, lon2]: return 999.0
        R = 6371  
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return round(R * c, 1)
    except: 
        return 999.0

def otimizar_imagem_local(arq, qualidade=50, size=(400, 400)):
    try:
        img = Image.open(arq)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail(size)
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=qualidade, optimize=True)
        return f"data:image/jpeg;base64,{base64.b64encode(output.getvalue()).decode()}"
    except:
        return ""

def carregar_bloco_dinamico():
    try:
        doc = db.collection("configuracoes").document("layout_ia").get()
        return doc.to_dict().get("codigo_injetado", "") if doc.exists else ""
    except: 
        return ""

def painel_adm_arquiteto():
    st.markdown('<br><hr style="border:1px dashed #cbd5e1;"><br>', unsafe_allow_html=True)
    with st.expander("🔐 MODO ARQUITETO (SISTEMA STRUCT)"):
        senha = st.text_input("Senha Master Arquiteto", type="password", key="master_pass_struct")
        if list(senha) and senha == CHAVE_ADMIN_ARQUITETO:
            novo_cod = st.text_area("Injetor de Código Dinâmico (Core)", height=200, key="inj_area_struct")
            if st.button("🚀 SOLDAR E INJETAR DINAMICAMENTE"):
                db.collection("configuracoes").document("layout_ia").set({
                    "codigo_injetado": novo_cod, 
                    "data": datetime.now(engine.fuso)
                })
                st.success("Código injetado com sucesso via Firestore!"); time.sleep(0.4); st.rerun()

# ==============================================================================
# 🎨 4. CORE DESIGN SYSTEM E ARQUITETURA DE RENDERIZAÇÃO
# ==============================================================================
def main():
    # Configuração Temática - Prioridade Absoluta Modo Dia (Light)
    if not st.session_state.modo_noite:
        cor_bg = "#F8FAFC"
        cor_texto = "#0F172A"
        cor_bloco = "#FFFFFF"
        cor_borda = "#E2E8F0"
        cor_subtexto = "#475569"
    else:
        cor_bg = "#0B0F19"
        cor_texto = "#F8FAFC"
        cor_bloco = "#111827"
        cor_borda = "#1F2937"
        cor_subtexto = "#94A3B8"

    # CSS de Alta Precisão - Otimização de Espaçamentos e Redução Total de Margem do Botão
    st.markdown(f"""
    <style>
        #MainMenu, footer, header {{ visibility: hidden; }}
        .stApp {{ background-color: {cor_bg} !important; color: {cor_texto} !important; }}
        .block-container {{ padding-top: 1rem !important; padding-bottom: 2rem !important; }}
        
        .bloco {{ 
            background: {cor_bloco} !important; 
            border-radius: 12px; 
            padding: 18px; 
            margin-bottom: 15px; 
            border: 1px solid {cor_borda} !important; 
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.01), 0 2px 4px -1px rgba(0,0,0,0.01); 
            color: {cor_texto} !important;
        }}
        
        /* Container Interno do Banner para Acolher o Seletor */
        .banner-wrapper {{
            position: relative;
            background: linear-gradient(135deg, #1d4ed8 0%, #1e3a8a 100%); 
            border-radius: 12px; 
            padding: 20px; 
            color: white;
            margin-bottom: 12px;
        }}
        
        /* Ajuste do Botão de Alternância de Tema Estilo Micro - Sem Distância ou Quebra de Layout */
        .micro-toggle-box {{
            position: absolute;
            top: 12px;
            right: 15px;
            z-index: 99999;
            background: rgba(255, 255, 255, 0.12);
            padding: 2px 8px;
            border-radius: 20px;
            backdrop-filter: blur(4px);
        }}
        .micro-toggle-box .stToggle {{
            scale: 0.68 !important;
            transform-origin: right center;
            margin: 0 !important;
            padding: 0 !important;
        }}
        .micro-toggle-box div[data-testid="stWidgetLabel"] p {{
            font-size: 10px !important;
            font-weight: 800 !important;
            color: #FFFFFF !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
    </style>
    """, unsafe_allow_html=True)

    # Criação do Layout Lateral vs Central do Aplicativo
    col_lateral, col_central = st.columns([1, 2.7])

    # 🧭 NAVEGADOR LATERAL FIXO (MENU INTERATIVO)
    with col_lateral:
        st.markdown('<div class="bloco">', unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top:0; font-weight:800;'>🧭 Navegador GeralJá</h4>", unsafe_allow_html=True)
        
        opcoes_navegacao = ["🔍 BUSCAR", "🚀 CADASTRAR PERFIL", "👤 PAINEL PERFIL", "⭐ FEEDBACK"]
        
        pass_cmd = st.text_input("Console Secreto", type="password", help="Comandos Estruturais de Infraestrutura")
        if pass_cmd == "abracadabra":
            opcoes_navegacao.append("📊 FINANCEIRO")
        elif pass_cmd == "admin99":
            opcoes_navegacao.append("👑 ADMIN PRO")
            
        aba_atual = st.radio("Selecione a Área de Acesso:", opcoes_navegacao, label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Injetor Master Arquiteto acoplado ao rodapé lateral
        painel_adm_arquiteto()

    # 🏢 PAINEL CENTRAL SUPREMO
    with col_central:
        # Renderização do Banner Principal
        st.markdown(f"""
        <div class="banner-wrapper">
            <h2 style="color: white; margin: 0; font-size: 1.8rem; font-weight: 900; letter-spacing: -1px;">GeralJá Ecossistema 🎯</h2>
            <div style="color: #93C5FD; font-size: 11px; font-weight: 700; letter-spacing: 0.8px; margin-top: 2px;">CONEXÃO INTELIGENTE DE FORNECEDORES E CLIENTES</div>
        </div>
        """, unsafe_allow_html=True)

        # Injeção do Botão Compactado Exatamente Dentro da Capa do Site (Posicionamento Absoluto)
        st.markdown('<div class="micro-toggle-box">', unsafe_allow_html=True)
        st.session_state.modo_noite = st.toggle("🌙 Modo Escuro", value=st.session_state.modo_noite)
        st.markdown('</div>', unsafe_allow_html=True)

        # Execução Direta do Canteiro de Obras Dinâmico Injetado por IA (Sem Interferências)
        codigo_da_ia = carregar_bloco_dinamico()
        if codigo_da_ia:
            try:
                exec(engine.sanitizar(codigo_da_ia))
            except Exception as e:
                st.caption(f"Aviso Volátil: {e}")

        # ======================================================================
        # INTERFACE: 🔍 BUSCAR PARCEIROS E PRODUTOS
        # ======================================================================
        if aba_atual == "🔍 BUSCAR":
            st.markdown('<div class="bloco">', unsafe_allow_html=True)
            st.markdown("<h4 style='margin-top:0; font-weight: 700;'>🏙️ O que você necessita encontrar no bairro?</h4>", unsafe_allow_html=True)
            
            c_b1, c_b2 = st.columns([7, 3])
            termo_busca = c_b1.text_input("Digite o serviço ou estabelecimento desejado:", key="busca_root_v6")
            raio_km = c_b2.select_slider("Filtro de Raio (KM)", options=[1, 2, 5, 10, 15, 50, 200], value=10)
            st.markdown('</div>', unsafe_allow_html=True)

            if termo_busca:
                categoria_resolvida = "Outros"
                t_normalizado = normalizar_texto(termo_busca)
                
                for chave, cat in CONCEITOS_MAPPING.items():
                    if chave in t_normalizado:
                        categoria_resolvida = cat
                        break
                if categoria_resolvida == "Outros":
                    for cat in CATEGORIAS_OFICIAIS:
                        if normalizar_texto(cat) in t_normalizado:
                            categoria_resolvida = cat
                            break

                # Query Filtrada: Retorna apenas perfis cuja moderação está ativa
                profs_stream = db.collection("profissionais")\
                    .where("area", "==", categoria_resolvida)\
                    .where("aprovado", "==", True).stream()
                
                lista_ranking = []
                for doc in profs_stream:
                    p = doc.to_dict()
                    p['id'] = doc.id
                    distancia = calcular_distancia_real(LAT_REF, LON_REF, p.get('lat', LAT_REF), p.get('lon', LON_REF))
                    
                    if distancia <= raio_km:
                        p['dist'] = distancia
                        p['score_vip'] = (5000 if p.get('saldo', 0) > 0 else 0)
                        lista_ranking.append(p)
                
                lista_ranking.sort(key=lambda x: (x['dist'], -x['score_vip']))

                if not lista_ranking:
                    st.info(f"Nenhum fornecedor verificado de '{categoria_resolvida}' localizado neste perímetro.")
                else:
                    for p in lista_ranking:
                        cor_destaque = "#10B981" if p['score_vip'] > 0 else "#2563EB"
                        f_img = p.get('foto_url', "https://cdn-icons-png.flaticon.com/512/149/149071.png")
                        
                        st.markdown(f"""
                        <div style="background:{cor_bloco}; border-radius:12px; border-left:5px solid {cor_destaque}; padding:14px; margin-bottom:10px; box-shadow:0 1px 3px rgba(0,0,0,0.05); display:flex; align-items:center; gap:12px;">
                            <img src="{f_img}" style="width:45px; height:45px; border-radius:50%; object-fit:cover; border:1px solid {cor_borda};">
                            <div style="flex-grow:1;">
                                <h5 style="margin:0; color:{cor_texto}; font-size:14px; font-weight:700;">{p.get('nome').upper()}</h5>
                                <p style="margin:1px 0; color:{cor_subtexto}; font-size:11px;">{p.get('descricao')[:100]}</p>
                                <span style="font-size:11px; color:#2563EB; font-weight:bold;">📍 Distância Estimada: {p['dist']:.1f} KM</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Exposição Unificada do Portfólio de Itens do Parceiro
                        with st.expander(f"📦 Cardápio / Catálogo de Ofertas de {p.get('nome')}"):
                            produtos_stream = db.collection("profissionais").document(p['id']).collection("produtos").stream()
                            ha_produtos = False
                            for prod_doc in produtos_stream:
                                ha_produtos = True
                                prod = prod_doc.to_dict()
                                c_pd1, c_pd2 = st.columns([8, 2])
                                c_pd1.markdown(f"**{prod.get('nome')}** — <span style='color:#F59E0B; font-weight:700;'>R$ {prod.get('preco'):.2f}</span><br><small style='color:{cor_subtexto};'>{prod.get('descricao')}</small>", unsafe_allow_html=True)
                                
                                if c_pd2.button("➕ Comprar", key=f"add_{p['id']}_{prod.get('id')}"):
                                    loja_id = p['id']
                                    if loja_id not in st.session_state.carrinho:
                                        st.session_state.carrinho[loja_id] = {"nome_loja": p.get('nome'), "whatsapp": p.get('whatsapp'), "itens": {}}
                                    prod_id = prod.get('id')
                                    if prod_id in st.session_state.carrinho[loja_id]["itens"]:
                                        st.session_state.carrinho[loja_id]["itens"][prod_id]["qtd"] += 1
                                    else:
                                        st.session_state.carrinho[loja_id]["itens"][prod_id] = {"nome": prod.get('nome'), "preco": prod.get('preco'), "qtd": 1}
                                    st.toast("Item adicionado à sua sacola!")
                            if not ha_produtos:
                                st.caption("Este parceiro comercial ainda não disponibilizou produtos digitais.")
                        
                        link_direto = f"https://wa.me/{limpar_whatsapp(p.get('whatsapp'))}?text=Olá! Encontrei sua empresa no catálogo do GeralJá."
                        st.markdown(f'<a href="{link_direto}" target="_blank" style="display:block; text-align:center; background:#2563EB; color:white; padding:6px; border-radius:6px; font-weight:700; text-decoration:none; margin-bottom:15px; font-size:12px;">💬 CONVERSAR DIRETOR VIA WHATSAPP</a>', unsafe_allow_html=True)

            # Renderização em Tempo Real da Sacola Multi-Vendor Descentralizada
            if st.session_state.carrinho:
                st.markdown('<div class="bloco" style="border: 2px solid #F59E0B !important;">', unsafe_allow_html=True)
                st.markdown("<h4 style='margin-top:0; color:#F59E0B; font-weight:800;'>🛒 Seus Pedidos Prontos para Envio</h4>", unsafe_allow_html=True)
                for l_id, sacola in list(st.session_state.carrinho.items()):
                    if not sacola["itens"]: continue
                    st.markdown(f"🏪 Fornecedor: **{sacola['nome_loja']}**")
                    total_pedido = 0.0
                    corpo_mensagem = f"Olá {sacola['nome_loja']}! Gostaria de fechar este pedido originado no GeralJá:\n\n"
                    
                    for item_id, inf in list(sacola["itens"].items()):
                        sub_total = inf["preco"] * inf["qtd"]
                        total_pedido += sub_total
                        st.markdown(f"▪️ *{inf['qtd']}x* {inf['nome']} — R$ {inf['preco']:.2f}")
                        corpo_mensagem += f"- {inf['qtd']}x {inf['nome']} (R$ {inf['preco']:.2f})\n"
                    
                    corpo_mensagem += f"\n💰 Total Acumulado: R$ {total_pedido:.2f}\n🌐 Pedido efetuado via geralja.com.br"
                    st.markdown(f"**Subtotal do Estabelecimento: R$ {total_pedido:.2f}**")
                    
                    link_checkout = f"https://wa.me/{limpar_whatsapp(sacola['whatsapp'])}?text={urllib.parse.quote(corpo_mensagem)}"
                    c_sk1, c_sk2 = st.columns(2)
                    c_sk1.markdown(f'<a href="{link_checkout}" target="_blank" style="display:block; text-align:center; background:#10B981; color:white; padding:8px; border-radius:6px; text-decoration:none; font-weight:bold; font-size:12px;">🚀 TRANSMITIR PEDIDO NO WHATSAPP</a>', unsafe_allow_html=True)
                    if c_sk2.button("🗑️ Esvaziar Sacola", key=f"clean_box_{l_id}"):
                        del st.session_state.carrinho[l_id]
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            # Central Noticiosa em Tempo Real via RSS - Grajaú Tem
            st.markdown("<h4 style='font-weight:800;'>📰 Plantão Informativo Regional - Grajaú Tem</h4>", unsafe_allow_html=True)
            try:
                feed = feedparser.parse("https://news.google.com/rss/search?q=Grajaú+São+Paulo&hl=pt-BR&gl=BR&ceid=BR:pt-419")
                noticias = feed.entries[:2]
                cols_not = st.columns(2)
                for index, nw in enumerate(noticias):
                    with cols_not[index]:
                        st.markdown(f"""
                        <div class="bloco" style="height:140px; overflow:hidden; border-top: 4px solid #EF4444 !important;">
                            <span style="background:#EF4444; color:white; font-size:9px; padding:1px 5px; border-radius:3px; font-weight:bold;">🚨 PLANTÃO</span>
                            <h5 style="margin:4px 0; font-size:12px; font-weight:700;"><a href="{nw.link}" target="_blank" style="color:{cor_texto}; text-decoration:none;">{nw.title.split(' - ')[0]}</a></h5>
                            <small style="color:{cor_subtexto};">Canal: {nw.source.get('title','Google News')}</small>
                        </div>
                        """, unsafe_allow_html=True)
            except:
                st.caption("Central de notícias regional atualizando dados...")

        # ======================================================================
        # INTERFACE: 🚀 CADASTRAR NOVO PERFIL COMERCIANTE
        # ======================================================================
        elif aba_atual == "🚀 CADASTRAR PERFIL":
            st.markdown('<div class="bloco">', unsafe_allow_html=True)
            st.markdown("<h4 style='margin-top:0; font-weight:700;'>🚀 Entre para a Vitrine de Prestadores</h4>", unsafe_allow_html=True)
            
            with st.form("cadastro_fornecedor_core", clear_on_submit=True):
                col_fd1, col_fd2 = st.columns(2)
                reg_nome = col_fd1.text_input("Nome Comercial / Marca da Empresa")
                reg_zap = col_fd2.text_input("WhatsApp para Contato (DDD + Número)")
                
                col_fd3, col_fd4 = st.columns(2)
                reg_area = col_fd3.selectbox("Especialidade ou Segmento Ativo", CATEGORIAS_OFICIAIS)
                reg_senha = col_fd4.text_input("Crie uma Senha Administrativa", type="password")
                
                reg_desc = st.text_area("Descreva seus Serviços, Portfólio e Diferenciais")
                reg_foto = st.file_uploader("Carregar Imagem de Logotipo ou Fachada", type=['png', 'jpg', 'jpeg'])
                
                if st.form_submit_button("💾 CONCLUIR CADASTRO E ATIVAR CONTA"):
                    if not reg_nome or not reg_zap or not reg_senha:
                        st.error("⚠️ Preencha obrigatoriamente os campos de Nome, WhatsApp e Senha.")
                    else:
                        img_b64 = "https://cdn-icons-png.flaticon.com/512/149/149071.png"
                        if reg_foto:
                            img_b64 = otimizar_imagem_local(reg_foto)
                            
                        db.collection("profissionais").document(reg_zap).set({
                            "nome": reg_nome, "whatsapp": reg_zap, "area": reg_area, "senha": reg_senha,
                            "descricao": reg_desc, "foto_url": img_b64, "saldo": BONUS_WELCOME,
                            "cliques": 0, "status": "Ativo", "aprovado": True, "data_registro": datetime.now(engine.fuso).strftime("%d/%m/%Y"),
                            "lat": LAT_REF, "lon": LON_REF
                        })
                        st.balloons()
                        st.success(f"🎊 Perfil ativado com sucesso no GeralJá! Seu negócio recebeu um bônus inicial de {BONUS_WELCOME} créditos🪙 para impulsionamento.")
            st.markdown('</div>', unsafe_allow_html=True)

        # ======================================================================
        # INTERFACE: 👤 PAINEL PRIVADO DO PERFIL DO LOJISTA
        # ======================================================================
        elif aba_atual == "👤 PAINEL PERFIL":
            st.markdown('<div class="bloco">', unsafe_allow_html=True)
            if not st.session_state.auth:
                st.markdown("<h4 style='margin-top:0; font-weight:700;'>👤 Login Gerencial do Parceiro</h4>", unsafe_allow_html=True)
                col_lg1, col_lg2 = st.columns(2)
                ent_zap = col_lg1.text_input("WhatsApp de Acesso")
                ent_senha = col_lg2.text_input("Sua Senha GeralJá", type="password")
                
                if st.button("🔓 LOGAR NO MEU PAINEL", use_container_width=True):
                    doc_parceiro = db.collection("profissionais").document(ent_zap).get()
                    if doc_parceiro.exists:
                        dados = doc_parceiro.to_dict()
                        if str(dados.get('senha')) == str(ent_senha):
                            # SISTEMA DE SEGURANÇA MÁXIMA: Bloqueados são retidos na entrada
                            if dados.get('status') == "Bloqueado":
                                st.error("🚫 Acesso Bloqueado: Este estabelecimento comercial encontra-se suspenso pela Moderação.")
                            else:
                                st.session_state.auth = True
                                st.session_state.user_id = ent_zap
                                st.success("Autenticação realizada com sucesso!"); time.sleep(0.4); st.rerun()
                        else: 
                            st.error("Inconsistência de senha. Tente novamente.")
                    else: 
                        st.error("Nenhuma conta vinculada a este número foi identificada.")
            else:
                p_doc_ref = db.collection("profissionais").document(st.session_state.user_id)
                p_info = p_doc_ref.get().to_dict()
                
                st.markdown(f"<h4 style='margin-top:0; font-weight:800;'>Gerenciamento de: {p_info.get('nome')}</h4>", unsafe_allow_html=True)
                
                # Alerta dinâmico de status comercial
                if p_info.get('status') == "De Gelo":
                    st.warning("🧊 **Status Suspenso:** Seu perfil comercial foi colocado 'De Gelo' pela moderação. Seus anúncios e vitrines estão temporariamente ocultos dos motores de busca de clientes.")
                
                met_c1, met_c2, met_c3 = st.columns(3)
                met_c1.metric("Créditos de Impulsionamento", f"{p_info.get('saldo', 0)} 🪙")
                met_c2.metric("Cliques / Visualizações", f"{p_info.get('cliques', 0)} 📈")
                met_c3.metric("Moderação Comercial", str(p_info.get('status')).upper())
                
                # Atualizador de Geolocalização Integrado
                if st.button("📍 VINCULAR COORDENADAS DE GPS DO ESTABELECIMENTO EM TEMPO REAL", use_container_width=True):
                    p_doc_ref.update({"lat": LAT_REF, "lon": LON_REF})
                    st.success("Geolocalização atualizada instantaneamente nos servidores!"); time.sleep(0.4); st.rerun()

                st.markdown("---")
                st.markdown("<h5 style='font-weight:700;'>📦 Inserir Item ou Produto ao seu Catálogo de Ofertas</h5>", unsafe_allow_html=True)
                with st.form("form_novo_produto_merchant", clear_on_submit=True):
                    item_nome = st.text_input("Nome do Produto / Serviço")
                    item_preco = st.number_input("Preço de Venda ao Consumidor (R$)", min_value=0.0, step=1.0)
                    item_desc = st.text_input("Breve descrição/detalhes da oferta")
                    if st.form_submit_button("🚀 PUBLICAR ITEM IMEDIATAMENTE"):
                        if item_nome and item_preco > 0:
                            novo_item_id = f"item_{int(time.time())}"
                            db.collection("profissionais").document(st.session_state.user_id).collection("produtos").document(novo_item_id).set({
                                "id": novo_item_id, "nome": item_nome, "preco": float(item_preco), "descricao": item_desc
                            })
                            st.success("Produto indexado com sucesso no catálogo de vendas!"); time.sleep(0.4); st.rerun()

                # NOVO RECURSO: Assistente de Copywriting Nátivo baseado na lógica do seu buscador local
                st.markdown("---")
                st.markdown("<h5 style='font-weight:700;'>🔴 Gerador de Criativos para o Grajaú Tem</h5>", unsafe_allow_html=True)
                st.caption("Rascunhe anúncios chamativos estruturados para alavancar suas postagens na Vitrine de Ofertas:")
                copy_prod = st.text_input("Produto / Oferta Principal", placeholder="Ex: Filé de Sassami")
                copy_val = st.text_input("Preço Promocional", placeholder="Ex: 15,48")
                if st.button("✨ RASCUNHAR ANÚNCIO DE AUTO-CONVERSÃO"):
                    if copy_prod and copy_val:
                        texto_gerado = f"🚨 URGENTE E CHAMATIVO\n📍 OFERTA DO DIA NO GRAJAÚ: {copy_prod.upper()} por apenas R$ {copy_val}!\n🔥 Corre para aproveitar as melhores condições do bairro. Seu bolso agradece!\n\nServiço: Fale direto com o fornecedor no GeralJá!"
                        st.info(texto_gerado)
                    else:
                        st.warning("Preencha o produto e o valor para estruturar a cópia promocional.")

                if st.button("🚪 ENCERRAR SESSÃO / LOGOUT", type="secondary"):
                    st.session_state.auth = False
                    st.session_state.user_id = None
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # ======================================================================
        # INTERFACE: ⭐ FEEDBACK E MELHORIAS NO APP
        # ======================================================================
        elif aba_atual == "⭐ FEEDBACK":
            st.markdown('<div class="bloco">', unsafe_allow_html=True)
            st.markdown("<h4 style='margin-top:0; font-weight:700;'>⭐ Central de Sugestões e Ouvidoria</h4>", unsafe_allow_html=True)
            with st.form("feedback_ouvidoria_system"):
                f_usr_nome = st.text_input("Informe seu Nome (Opcional)")
                f_usr_msg = st.text_area("O que você sugere para aperfeiçoar o ecossistema?")
                if st.form_submit_button("REGISTRAR SUGESTÃO") and f_usr_msg:
                    db.collection("feedbacks").add({
                        "nome": f_usr_nome if f_usr_nome else "Morador Anônimo",
                        "mensagem": f_usr_msg, "data": datetime.now(engine.fuso).strftime("%d/%m/%Y")
                    })
                    st.success("Obrigado pelo seu feedback! Seus apontamentos foram catalogados com sucesso.")
            st.markdown('</div>', unsafe_allow_html=True)

        # ======================================================================
        # INTERFACE PRIVADA: 👑 ADMIN PRO (MODERAÇÃO DE FLUXO TOTAL EM TEMPO REAL)
        # ======================================================================
        elif aba_atual == "👑 ADMIN PRO":
            st.markdown('<div class="bloco" style="border: 1px solid #10B981 !important;">', unsafe_allow_html=True)
            st.markdown("<h4 style='margin-top:0; color:#10B981; font-weight:900;'>👑 Central Administrativa de Moderação e Punições Comerciais</h4>", unsafe_allow_html=True)
            
            # Streaming em tempo real de todas as contas cadastradas na base de dados
            profissionais_gerais = db.collection("profissionais").stream()
            
            for doc in profissionais_gerais:
                usr_data = doc.to_dict()
                usr_id = doc.id
                status_atual = usr_data.get("status", "Ativo")
                
                # Marcação de cor por nível de moderação comercial
                if status_atual == "Ativo": lbl_color = "#10B981"
                elif status_atual == "De Gelo": lbl_color = "#38BDF8"
                else: lbl_color = "#EF4444"
                
                st.markdown(f"""
                <div style="background:{cor_bg}; padding:10px; border-left: 5px solid {lbl_color}; border-radius:6px; margin-bottom:8px;">
                    <b style="color:{cor_texto}; font-size:13px;">🏪 Estabelecimento: {usr_data.get('nome')}</b> | ID ID Técnico: <code>{usr_id}</code><br>
                    Especialidade Comercial: {usr_data.get('area')} | Status de Moderação: <span style="color:{lbl_color}; font-weight:800;">{status_atual.upper()}</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Barra de Botões Finos Interativos para Controle Administrativo Total
                adm_c1, adm_c2, adm_c3, adm_c4 = st.columns(4)
                
                with adm_c1:
                    if status_atual != "Ativo":
                        if st.button("🟢 Ativar", key=f"cmd_atv_{usr_id}"):
                            db.collection("profissionais").document(usr_id).update({"aprovado": True, "status": "Ativo"})
                            st.success("Status: Ativo!"); time.sleep(0.4); st.rerun()
                with adm_c2:
                    if status_atual != "De Gelo":
                        if st.button("🧊 De Gelo", key=f"cmd_gel_{usr_id}", help="Oculta o prestador das buscas gerais, mas mantém seu login ativo."):
                            db.collection("profissionais").document(usr_id).update({"aprovado": False, "status": "De Gelo"})
                            st.warning("Status: No Gelo!"); time.sleep(0.4); st.rerun()
                with adm_c3:
                    if status_atual != "Bloqueado":
                        if st.button("🚫 Bloquear", key=f"cmd_blk_{usr_id}", help="Oculta dos clientes e barra a tela de login imediatamente."):
                            db.collection("profissionais").document(usr_id).update({"aprovado": False, "status": "Bloqueado"})
                            st.error("Status: Bloqueado!"); time.sleep(0.4); st.rerun()
                with adm_c4:
                    if st.button("❌ Banir", key=f"cmd_ban_{usr_id}", help="Remove permanentemente o registro da base de dados."):
                        db.collection("profissionais").document(usr_id).delete()
                        st.error("Status: Banido do Banco!"); time.sleep(0.4); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # ======================================================================
        # INTERFACE PRIVADA: 📊 FINANCEIRO E FATURAMENTO
        # ======================================================================
        elif aba_atual == "📊 FINANCEIRO":
            st.markdown('<div class="bloco">', unsafe_allow_html=True)
            st.markdown("<h4 style='margin-top:0; font-weight:700;'>📊 Monitoramento Comercial e Receitas da Vitrine</h4>", unsafe_allow_html=True)
            st.metric("Faturamento Estimado com Inserções de Mídia", "R$ 14.820,00", "Meta Mensal Ativa")
            
            st.markdown("##### 🔴 Grade Oficial de Pacotes de Venda - Grajaú Tem")
            st.markdown("""
            * **🔴 Vitrine de Ofertas (Giro Diário):** R$ 100 (Unitário) | R$ 600 (Mensal com 8 inserções)
            * **🥉 Pacote Bronze:** 1 post = R$ 150
            * **🥈 Pacote Prata:** 3 posts = R$ 400
            * **🥇 Pacote Ouro:** 10 posts = R$ 700
            * **📻 Anúncios Rádio Grajaú Tem:** R$ 300/mês
            """)
            st.caption(f"WhatsApp Oficial de Vendas: {PIX_OFICIAL}")
            st.markdown('</div>', unsafe_allow_html=True)

        # 🎯 FOOTER INSTITUCIONAL DE ALTA CONVERSÃO
        st.markdown(f"""
        <div style="text-align:center; padding:10px; opacity:0.6; font-size:11px; color:{cor_texto}; margin-top:20px;">
            <p>🎯 <b>GeralJá - Conectando Soluções Locais</b></p>
            <p>© 2026 geralja.com.br | Grajaú, São Paulo</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
