# ==============================================================================
# GERALJÁ: CRIANDO SOLUÇÕES - MÓDULO INTEGRADO E CORRIGIDO (2026)
# ==============================================================================
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import math
import re
import time
import pandas as pd
from datetime import datetime 
import pytz
import unicodedata
import requests
import sys
import os
import io
import urllib.parse
import feedparser
from PIL import Image

# ==============================================================================
# 🛡️ 1. CONFIGURAÇÃO DE ALTO NÍVEL & CORE ENGINE
# ==============================================================================
class GeralJaEngine:
    def __init__(self):
        self.fuso = pytz.timezone('America/Sao_Paulo')
    
    def sanitizar(self, codigo_bruto):
        """Mata caracteres fantasmas e lixo de codificação instantaneamente"""
        if not codigo_bruto: return ""
        limpo = codigo_bruto.replace('\u00a0', ' ').replace('\xa0', ' ')
        return re.sub(r'[^\x20-\x7E\n\t\r]', '', limpo)

    def injetar_modulo(self, nome_arquivo, conteudo):
        """Instala novos códigos no servidor de forma independente"""
        try:
            conteudo_limpo = self.sanitizar(conteudo)
            db.collection("configuracoes").document("layout_ia").set({
                "codigo_injetado": conteudo_limpo,
                "atualizado_em": datetime.now(self.fuso),
                "modulo_origem": nome_arquivo
            })
            return True
        except:
            return False

# Inicialização da Engine
engine = GeralJaEngine()

st.set_page_config(
    page_title="GeralJá | Plataforma Suprema",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constantes Estratégicas de Negócio
CHAVE_ADMIN_ARQUITETO = "123" 
BONUS_WELCOME = 50
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
LAT_REF = -23.5505
LON_REF = -46.6333

CATEGORIAS_OFICIAIS = [
    "Açougue", "Pizzaria", "Mecânico", "Eletricista", "Moda", "Beleza", "Encanador", 
    "Pintor", "Pedreiro", "Diarista", "Lanchonete", "Restaurante", "Adega", 
    "TI", "Assistência Técnica", "Pet Shop", "Freteiro", "Chaveiro", "Outros"
]

CONCEITOS_MAPPING = {
    "carne": "Açougue", "açougue": "Açougue", "acougue": "Açougue",
    "pizza": "Pizzaria", "lanche": "Lanchonete", "comida": "Restaurante", 
    "remedio": "Farmácia", "cabelo": "Beleza", "unha": "Beleza",
    "celular": "Assistência Técnica", "vazamento": "Encanador", 
    "curto": "Eletricista", "carro": "Mecânico", "frete": "Freteiro"
}

# Inicialização de Estados Universais Seguros (Padrão: Modo Dia)
if 'modo_noite' not in st.session_state:
    st.session_state.modo_noite = False  
if 'auth' not in st.session_state:
    st.session_state.auth = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'minha_lat' not in st.session_state:
    st.session_state.minha_lat = LAT_REF
if 'minha_lon' not in st.session_state:
    st.session_state.minha_lon = LON_REF
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = {}

# Conexão Isolada do Banco Firestore
if not firebase_admin._apps:
    try:
        if "FIREBASE_BASE64" in st.secrets:
            fb_dict = json.loads(base64.b64decode(st.secrets["FIREBASE_BASE64"]).decode("utf-8"))
            firebase_admin.initialize_app(credentials.Certificate(fb_dict))
    except Exception as e:
        st.error(f"Aviso de Inicialização Firebase: {e}")

db = firestore.client()

# ==============================================================================
# 🧰 2. AUXILIARES DE PROCESSAMENTO DE DADOS
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
    except: return 999.0

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

# ==============================================================================
# 🏗 3. DESIGN SYSTEM INTEGRADO E RENDERIZADOR MASTER
# ==============================================================================
def main():
    # Definição de Cores Dinâmicas
    cor_bg = "#F8FAFC" if not st.session_state.modo_noite else "#0D1117"
    cor_texto = "#1A1A1B" if not st.session_state.modo_noite else "#FFFFFF"
    cor_bloco = "#FFFFFF" if not st.session_state.modo_noite else "#161B22"
    cor_borda = "#E2E8F0" if not st.session_state.modo_noite else "#30363D"

    # Redução máxima de margens e controle do layout limpo
    st.markdown(f"""
    <style>
        #MainMenu, footer, header {{ visibility: hidden; }}
        .stApp {{ background-color: {cor_bg} !important; color: {cor_texto} !important; }}
        .block-container {{ padding-top: 0.5rem !important; padding-bottom: 3rem !important; }}
        
        .bloco {{ 
            background: {cor_bloco} !important; 
            border-radius: 15px; 
            padding: 20px; 
            margin-bottom: 25px; 
            border: 1px solid {cor_borda} !important; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.02); 
            color: {cor_texto} !important;
        }}
        
        .floating-toggle-box {{
            margin-top: -50px !important;
            margin-right: 15px !important;
            float: right !important;
            position: relative !important;
            z-index: 99999 !important;
        }}
        .floating-toggle-box div[data-testid="stWidgetLabel"] p {{
            font-size: 0.75rem !important;
            font-weight: bold !important;
            color: rgba(255, 255, 255, 0.9) !important;
        }}
        .floating-toggle-box .stToggle {{
            scale: 0.75 !important;
            transform-origin: right center;
        }}
    </style>
    """, unsafe_allow_html=True)

    col_lateral, col_central = st.columns([1, 2.6])

    # 🧭 NAVEGADOR FIXO ESQUERDO
    with col_lateral:
        st.markdown('<div class="bloco">', unsafe_allow_html=True)
        st.markdown("<h3 style='margin-top:0;'>🧭 Painel GeralJá</h3>", unsafe_allow_html=True)
        
        opcoes_navegacao = ["🔍 BUSCAR", "🚀 CADASTRAR", "👤 MEU PERFIL", "⭐ FEEDBACK"]
        
        comando_secreto = st.text_input("Acesso Estrutural", type="password", help="Comandos de engenharia")
        if comando_secreto == "abracadabra":
            opcoes_navegacao.append("📊 FINANCEIRO")
        elif comando_secreto == "admin99":
            opcoes_navegacao.append("👑 ADMIN")
            
        aba_atual = st.radio("Selecione:", opcoes_navegacao, label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<br>', unsafe_allow_html=True)
        with st.expander("🛠️ MODO ARQUITETO (ENGINE STRUCT)"):
            senha_arq = st.text_input("Chave Solda", type="password")
            if senha_arq == CHAVE_ADMIN_ARQUITETO:
                novo_cod = st.text_area("Injetor de Fluxo Volátil", height=200)
                if st.button("🚀 SOLDAR CÓDIGO NO FIREBASE"):
                    if engine.injetar_modulo("Canteiro_Local", novo_cod):
                        st.success("Soldado e normalizado com sucesso!"); time.sleep(0.4); st.rerun()

    # 🏢 PAINEL CENTRAL DE EXECUÇÃO DE INTERFACES
    with col_central:
        # Capa Moderna em Degradê Azul Real
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1d4ed8 0%, #1e3a8a 100%); border-radius: 15px; padding: 22px; color: white;">
            <h1 style="color: white; margin: 0; font-size: 2rem; font-weight: 900; letter-spacing: -1px;">GeralJá Turbo 🎯</h1>
            <small style="color: #BFDBFE; font-weight: bold; letter-spacing: 0.5px;">SISTEMA INTEGRADO DE INTELIGÊNCIA LOCAL</small>
        </div>
        """, unsafe_allow_html=True)

        # Acoplamento do Botão Slim de Tema dentro do Banner
        st.markdown('<div class="floating-toggle-box">', unsafe_allow_html=True)
        st.session_state.modo_noite = st.toggle("Modo Escuro", value=st.session_state.modo_noite)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div style="clear: both; margin-bottom: 10px;"></div>', unsafe_allow_html=True)

        # Execução Condicional do Bloco Injetado se Existir
        codigo_da_ia = carregar_bloco_dinamico()
        if codigo_da_ia:
            try:
                exec(codigo_da_ia)
            except Exception as e:
                st.caption(f"Aviso no barramento volátil: {e}")

        # --- ABA: 🔍 BUSCAR ---
        if aba_atual == "🔍 BUSCAR":
            st.markdown('<div class="bloco">', unsafe_allow_html=True)
            st.markdown("<h3 style='margin-top:0;'>🏙️ Encontre Profissionais no Bairro</h3>", unsafe_allow_html=True)
            c_gps1, c_gps2 = st.columns([7, 3])
            termo_busca = c_gps1.text_input("O que você precisa hoje?", placeholder="Ex: Açougue, Chaveiro, Marmita...")
            raio_km = c_gps2.select_slider("Distância Máxima (KM)", options=[1, 3, 5, 10, 30, 100], value=5)
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

                profs_stream = db.collection("profissionais").where("area", "==", categoria_resolvida).where("aprovado", "==", True).stream()
                lista_ranking = []
                
                for doc in profs_stream:
                    p = doc.to_dict()
                    p['id'] = doc.id
                    distancia = calcular_distancia_real(st.session_state.minha_lat, st.session_state.minha_lon, p.get('lat', LAT_REF), p.get('lon', LON_REF))
                    if distancia <= raio_km:
                        p['dist'] = distancia
                        p['score_premium'] = (1000 if p.get('saldo', 0) > 0 else 0)
                        lista_ranking.append(p)
                
                lista_ranking.sort(key=lambda x: (x['dist'], -x['score_premium']))

                if not lista_ranking:
                    st.info("Nenhum profissional localizado nesta área dentro do raio escolhido.")
                else:
                    for p in lista_ranking:
                        cor_borda_card = "#FF8C00" if p['score_premium'] > 0 else "#1d4ed8"
                        f_url = p.get('foto_url', "https://cdn-icons-png.flaticon.com/512/149/149071.png")
                        
                        st.markdown(f"""
                        <div style="background:{cor_bloco}; border-radius:12px; border-left:5px solid {cor_borda_card}; padding:15px; margin-bottom:12px; display:flex; align-items:center; gap:15px; border-top:1px solid {cor_borda}; border-right:1px solid {cor_borda}; border-bottom:1px solid {cor_borda};">
                            <img src="{f_url}" style="width:45px; height:45px; border-radius:50%; object-fit:cover;">
                            <div style="flex-grow:1;">
                                <h4 style="margin:0; color:{cor_texto}; font-size:14px;">{p.get('nome').upper()}</h4>
                                <p style="margin:2px 0; color:gray; font-size:12px;">{p.get('descricao')[:100]}</p>
                                <span style="font-size:11px; color:#1d4ed8; font-weight:bold;">📍 Raio: {p['dist']:.1f} KM</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        with st.expander(f"📦 Catálogo / Vitrine de Ofertas de {p.get('nome')}"):
                            produtos_stream = db.collection("profissionais").document(p['id']).collection("produtos").stream()
                            tem_item = False
                            for prod_doc in produtos_stream:
                                tem_item = True
                                prod = prod_doc.to_dict()
                                c_p1, c_p2 = st.columns([8, 2])
                                c_p1.markdown(f"**{prod.get('nome')}** — <span style='color:#FF8C00; font-weight:bold;'>R$ {prod.get('preco'):.2f}</span><br><small>{prod.get('descricao')}</small>", unsafe_allow_html=True)
                                if c_p2.button("➕ Adicionar", key=f"add_{p['id']}_{prod.get('id')}"):
                                    loja_id = p['id']
                                    if loja_id not in st.session_state.carrinho:
                                        st.session_state.carrinho[loja_id] = {"nome_loja": p.get('nome'), "whatsapp": p.get('whatsapp'), "itens": {}}
                                    p_id = prod.get('id')
                                    if p_id in st.session_state.carrinho[loja_id]["itens"]:
                                        st.session_state.carrinho[loja_id]["itens"][p_id]["qtd"] += 1
                                    else:
                                        st.session_state.carrinho[loja_id]["itens"][p_id] = {"nome": prod.get('nome'), "preco": prod.get('preco'), "qtd": 1}
                                    st.toast("Adicionado à sacola!")
                            if not tem_item:
                                st.caption("Este parceiro ainda não listou ofertas diretas.")
                        
                        link_zap = f"https://wa.me/{limpar_whatsapp(p.get('whatsapp'))}?text=Olá! Encontrei seu contato no GeralJá."
                        st.markdown(f'<a href="{link_zap}" target="_blank" style="display:block; text-align:center; background:#1d4ed8; color:white; padding:6px; border-radius:6px; font-weight:bold; text-decoration:none; font-size:12px; margin-bottom:15px;">💬 NEGOCIAR DIRETO NO WHATSAPP</a>', unsafe_allow_html=True)

            if st.session_state.carrinho:
                st.markdown('<div class="bloco" style="border: 2px solid #FF8C00 !important;">', unsafe_allow_html=True)
                st.markdown("### 🛒 Sua Sacola de Compras Ativa</h3>", unsafe_allow_html=True)
                for l_id, sacola in list(st.session_state.carrinho.items()):
                    if not sacola["itens"]: continue
                    st.markdown(f"🏪 Estabelecimento: **{sacola['nome_loja']}**")
                    total_pedido = 0.0
                    texto_zap = f"Olá {sacola['nome_loja']}! Gostaria de fazer o seguinte pedido pelo GeralJá:\n\n"
                    
                    for item_id, inf in list(sacola["itens"].items()):
                        sub = inf["preco"] * inf["qtd"]
                        total_pedido += sub
                        st.markdown(f"▪️ *{inf['qtd']}x* {inf['nome']} — R$ {inf['preco']:.2f}")
                        texto_zap += f"- {inf['qtd']}x {inf['nome']} (R$ {inf['preco']:.2f})\n"
                    
                    texto_zap += f"\n💰 Total: R$ {total_pedido:.2f}\n💻 Via: geralja.com.br"
                    link_checkout = f"https://wa.me/{limpar_whatsapp(sacola['whatsapp'])}?text={urllib.parse.quote(texto_zap)}"
                    
                    c_s1, c_s2 = st.columns(2)
                    c_s1.markdown(f'<a href="{link_checkout}" target="_blank" style="display:block; text-align:center; background:#25D366; color:white; padding:8px; border-radius:6px; text-decoration:none; font-weight:bold; font-size:13px;">🚀 CONFIRMAR PEDIDO NO ZAP</a>', unsafe_allow_html=True)
                    if c_s2.button("🗑️ Esvaziar Sacola", key=f"clear_{l_id}"):
                        del st.session_state.carrinho[l_id]
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("### 📰 Plantão Noticioso - Grajaú Tem")
            try:
                feed = feedparser.parse("https://news.google.com/rss/search?q=Grajaú+São+Paulo&hl=pt-BR&gl=BR&ceid=BR:pt-419")
                entries = feed.entries[:2]
                cols_noticia = st.columns(2)
                for i, ent in enumerate(entries):
                    with cols_noticia[i]:
                        st.markdown(f"""
                        <div class="bloco" style="height:140px; overflow:hidden; border-top: 3px solid #e11d48;">
                            <span style="background:#e11d48; color:white; font-size:9px; padding:1px 5px; border-radius:3px; font-weight:bold;">🚨 INFORMAÇÃO LOCAL</span>
                            <h5 style="margin:5px 0; font-size:12px;"><a href="{ent.link}" target="_blank" style="color:{cor_texto}; text-decoration:none;">{ent.title.split(' - ')[0]}</a></h5>
                        </div>
                        """, unsafe_allow_html=True)
            except:
                st.caption("Plantão de notícias em sincronização com o feed do portal.")

        # --- ABA: 🚀 CADASTRAR (CORRIGIDA) ---
        elif aba_atual == "🚀 CADASTRAR":
            st.markdown('<div class="bloco">', unsafe_allow_html=True)
            st.markdown("<h3 style='margin-top:0;'>🚀 Inclusão de Profissional / Empresa</h3>", unsafe_allow_html=True)
            
            with st.form("form_cadastro_master"):
                col_c1, col_c2 = st.columns(2)
                c_nome = col_c1.text_input("Nome Fantasia ou Seu Nome")
                c_zap = col_c2.text_input("WhatsApp com DDD (Apenas números)")
                
                col_c3, col_c4 = st.columns(2)
                c_area = col_c3.selectbox("Segmento de Atuação", CATEGORIAS_OFICIAIS)
                c_senha = col_c4.text_input("Senha para alterar seu perfil depois", type="password")
                
                c_desc = st.text_area("Descreva seus serviços e promoções")
                c_foto = st.file_uploader("Sua Logo ou Foto de Perfil", type=['png', 'jpg', 'jpeg'])
                
                cadastrar_acionado = st.form_submit_button("💾 FINALIZAR E SALVAR CADASTRO")
                
                if cadastrar_acionado:
                    if not c_nome.strip() or not c_zap.strip() or not c_senha.strip():
                        st.error("Por favor, preencha todos os campos obrigatórios (Nome, WhatsApp e Senha).")
                    else:
                        img_b64 = "https://cdn-icons-png.flaticon.com/512/149/149071.png"
                        if c_foto:
                            img_b64 = otimizar_imagem_local(c_foto)
                            
                        db.collection("profissionais").document(c_zap.strip()).set({
                            "nome": c_nome.strip(), "whatsapp": c_zap.strip(), "area": c_area, "senha": c_senha.strip(),
                            "descricao": c_desc, "foto_url": img_b64, "saldo": BONUS_WELCOME,
                            "cliques": 0, "status": "Ativo", "aprovado": True, "data_cadastro": datetime.now().strftime("%d/%m/%Y"),
                            "lat": st.session_state.minha_lat, "lon": st.session_state.minha_lon
                        })
                        st.success(f"Cadastro efetuado! Você recebeu um bônus inicial de {BONUS_WELCOME} créditos🪙")
            st.markdown('</div>', unsafe_allow_html=True)

        # --- ABA: 👤 MEU PERFIL ---
        elif aba_atual == "👤 MEU PERFIL":
            st.markdown('<div class="bloco">', unsafe_allow_html=True)
            if not st.session_state.auth:
                st.markdown("<h3 style='margin-top:0;'>🔓 Autenticação do Comerciante</h3>", unsafe_allow_html=True)
                log_zap = st.text_input("WhatsApp")
                log_senha = st.text_input("Senha", type="password")
                if st.button("ACESSAR DASHBOARD", use_container_width=True):
                    doc = db.collection("profissionais").document(log_zap).get()
                    if doc.exists:
                        dados = doc.to_dict()
                        if dados.get("status") == "Bloqueado":
                            st.error("🔒 Conta bloqueada por descumprimento dos termos de moderação.")
                        elif str(dados.get("senha")) == str(log_senha):
                            st.session_state.auth = True
                            st.session_state.user_id = log_zap
                            st.rerun()
                        else: st.error("Senha inválida.")
                    else: st.error("Usuário inexistente.")
            else:
                p_ref = db.collection("profissionais").document(st.session_state.user_id)
                p_data = p_ref.get().to_dict()
                
                st.markdown(f"<h3>Painel de Controle — {p_data.get('nome')}</h3>", unsafe_allow_html=True)
                if p_data.get('status') == "De Gelo":
                    st.warning("🧊 Seu perfil está em modo 'De Gelo'. Ele está invisível nas buscas públicas por decisão administrativa.")
                
                c_m1, c_m2, c_m3 = st.columns(3)
                c_m1.metric("Créditos de Impulsionamento", f"{p_data.get('saldo', 0)} 🪙")
                c_m2.metric("Cliques Recebidos", f"{p_data.get('cliques', 0)}")
                c_m3.metric("Status Comercial", str(p_data.get('status')).upper())
                
                if st.button("📌 RE-SINCRONIZAR LOCALIZAÇÃO DA LOJA PELO MEU GPS ATUAL", use_container_width=True):
                    p_ref.update({"lat": st.session_state.minha_lat, "lon": st.session_state.minha_lon})
                    st.success("Coordenadas atualizadas com sucesso!")

                st.markdown("---")
                st.markdown("#### 📦 Adicionar Oferta ao seu Catálogo")
                with st.form("form_vitrine_item", clear_on_submit=True):
                    it_nome = st.text_input("Nome do Produto/Serviço")
                    it_preco = st.number_input("Preço Final (R$)", min_value=0.0)
                    it_desc = st.text_input("Diferencial do produto")
                    if st.form_submit_button("ADICIONAR ITEM NA VITRINE"):
                        if it_nome and it_preco > 0:
                            id_gerado = f"item_{int(time.time())}"
                            db.collection("profissionais").document(st.session_state.user_id).collection("produtos").document(id_gerado).set({
                                "id": id_gerado, "nome": it_nome, "preco": float(it_preco), "descricao": it_desc
                            })
                            st.success("Item publicado!"); time.sleep(0.4); st.rerun()

                if st.button("🚪 DESCONECTAR DA MINHA CONTA", type="secondary"):
                    st.session_state.auth = False
                    st.session_state.user_id = None
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # --- ABA: ⭐ FEEDBACK ---
        elif aba_atual == "⭐ FEEDBACK":
            st.markdown('<div class="bloco">', unsafe_allow_html=True)
            st.markdown("<h3 style='margin-top:0;'>⭐ Enviar Críticas ou Sugestões</h3>", unsafe_allow_html=True)
            with st.form("f_form"):
                n = st.text_input("Nome")
                m = st.text_area("O que podemos evoluir na plataforma?")
                if st.form_submit_button("REGISTRAR SUGESTÃO"):
                    db.collection("feedbacks").add({"nome": n or "Anônimo", "mensagem": m, "data": datetime.now().strftime("%d/%m/%Y")})
                    st.success("Enviado com sucesso!")
            st.markdown('</div>', unsafe_allow_html=True)

        # --- ABA OCULTA: 👑 ADMIN ---
        elif aba_atual == "👑 ADMIN":
            st.markdown('<div class="bloco" style="border: 2px solid #10b981 !important;">', unsafe_allow_html=True)
            st.markdown("<h3 style='margin-top:0; color:#10b981;'>👑 Moderação Fina & Punições Comerciais</h3>", unsafe_allow_html=True)
            
            usuarios_stream = db.collection("profissionais").stream()
            for doc in usuarios_stream:
                u = doc.to_dict()
                uid = doc.id
                ust = u.get("status", "Ativo")
                
                lbl_c = "#10b981" if ust == "Ativo" else ("#38bdf8" if ust == "De Gelo" else "#ef4444")
                st.markdown(f"""
                <div style="background:{cor_bg}; padding:10px; border-left:4px solid {lbl_c}; margin-bottom:8px; border-radius:5px;">
                    <b>🏪 {u.get('nome')}</b> (<code>{uid}</code>) — Segmento: {u.get('area')} | Status atual: <span style="color:{lbl_c}; font-weight:bold;">{ust.upper()}</span>
                </div>
                """, unsafe_allow_html=True)
                
                b1, b2, b3, b4 = st.columns(4)
                with b1:
                    if ust != "Ativo" and st.button("🟢 Ativar", key=f"at_{uid}"):
                        db.collection("profissionais").document(uid).update({"aprovado": True, "status": "Ativo"})
                        st.rerun()
                with b2:
                    if ust != "De Gelo" and st.button("🧊 Gelo", key=f"ge_{uid}"):
                        db.collection("profissionais").document(uid).update({"aprovado": False, "status": "De Gelo"})
                        st.rerun()
                with b3:
                    if ust != "Bloqueado" and st.button("🚫 Bloquear", key=f"bl_{uid}"):
                        db.collection("profissionais").document(uid).update({"aprovado": False, "status": "Bloqueado"})
                        st.rerun()
                with b4:
                    if st.button("❌ Banir", key=f"bn_{uid}"):
                        db.collection("profissionais").document(uid).delete()
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # --- ABA OCULTA: 📊 FINANCEIRO ---
        elif aba_atual == "📊 FINANCEIRO":
            st.markdown('<div class="bloco">', unsafe_allow_html=True)
            st.markdown("<h3 style='margin-top:0;'>📊 Painel Comercial de Parcerias</h3>", unsafe_allow_html=True)
            st.metric("Faturamento Líquido Estimado", "R$ 14.820,00", "Meta Mensal Corrente")
            st.markdown("""
            * **🔴 Vitrine de Ofertas (Giro Diário):** R$ 100 Unitário | R$ 600 Mensal
            * **🥉 Bronze:** R$ 150 (1 post)
            * **🥈 Prata:** R$ 400 (3 posts)
            * **🥇 Ouro:** R$ 700 (10 posts)
            * **📻 Rádio Grajaú Tem:** R$ 300/mês
            """)
            st.markdown('</div>', unsafe_allow_html=True)

        # Rodapé Oficial Unificado
        st.markdown(f"""
        <div style="text-align:center; padding:15px; opacity:0.6; font-size:11px; color:{cor_texto}; margin-top:25px;">
            <p>🎯 <b>GeralJá Brasil</b> — Sistema Operacional de Conexões de Bairro</p>
            <p>© 2026 geralja.com.br | Grajaú, São Paulo</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
