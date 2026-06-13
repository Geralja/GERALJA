# ==============================================================================
# GERALJÁ TURBO: ENGINE MASTER INTEGRADO & MODERADO
# ==============================================================================
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime
import math
import re
import time
import io
import unicodedata
import urllib.parse
import feedparser
from PIL import Image

# ==============================================================================
# 🛡️ 1. CONFIGURAÇÕES INTERNAS, PRESETS E SEGURANÇA
# ==============================================================================
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

# Tabela Oficial de Segmentos Expandidos
CATEGORIAS_OFICIAIS = [
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
    "Churrascaria", "Hamburgueria", "Comida Japonesa", "Cafeteria",
    "Farmácia", "Barbearia/Salão", "Manicure/Pedicure", "Estética Facial", 
    "Tatuagem/Piercing", "Fitness", "Academia", "Fisioterapia", "Odontologia", 
    "Clínica Médica", "Psicologia", "Nutricionista", "TI", "Assistência Técnica", 
    "Celulares", "Informática", "Refrigeração", "Técnico de Fogão", "Técnico de Lavadora", 
    "Eletrônicos", "Chaveiro", "Montador", "Freteiro", "Carreto", "Motoboy/Entregas",
    "Pet Shop", "Veterinário", "Banho e Tosa", "Adestrador", "Agropecuária",
    "Aulas Particulares", "Escola Infantil", "Reforço Escolar", "Idiomas", 
    "Advocacia", "Contabilidade", "Imobiliária", "Seguros", "Ajudante Geral", 
    "Diarista", "Cuidador de Idosos", "Babá", "Outros"
]

CONCEITOS_MAPPING = {
    "pizza": "Pizzaria", "pizzaria": "Pizzaria", "fome": "Pizzaria", "massa": "Pizzaria",
    "lanche": "Lanchonete", "hamburguer": "Lanchonete", "burger": "Lanchonete", "salgado": "Lanchonete",
    "comida": "Restaurante", "almoco": "Restaurante", "marmita": "Restaurante", "jantar": "Restaurante",
    "doce": "Confeitaria", "bolo": "Confeitaria", "pao": "Padaria", "padaria": "Padaria",
    "acai": "Açaí", "sorvete": "Sorveteria", "cerveja": "Adega", "bebida": "Adega",
    "roupa": "Loja de Roupas", "moda": "Loja de Roupas", "sapato": "Calçados", "tenis": "Calçados",
    "presente": "Loja de Variedades", "relogio": "Relojoaria", "joia": "Joalheria",
    "remedio": "Farmácia", "farmacia": "Farmácia", "cabelo": "Barbearia/Salão", "unha": "Barbearia/Salão",
    "celular": "Assistência Técnica", "iphone": "Assistência Técnica", "computador": "TI", "pc": "TI",
    "geladeira": "Refrigeração", "ar condicionado": "Refrigeração", "fogao": "Técnico de Fogão",
    "tv": "Eletrônicos", "pet": "Pet Shop", "racao": "Pet Shop", "cachorro": "Pet Shop",
    "vazamento": "Encanador", "cano": "Encanador", "curto": "Eletricista", "luz": "Eletricista",
    "pintar": "Pintor", "parede": "Pintor", "reforma": "Pedreiro", "piso": "Pedreiro",
    "telhado": "Telhadista", "solda": "Serralheiro", "vidro": "Vidraceiro", "chave": "Chaveiro",
    "carro": "Mecânico", "motor": "Mecânico", "pneu": "Borracheiro", "guincho": "Guincho 24h",
    "frete": "Freteiro", "mudanca": "Freteiro", "faxina": "Diarista", "limpeza": "Diarista",
    "jardim": "Jardineiro", "piscina": "Piscineiro"
}

# Inicialização de Estados Universais Seguros
if 'modo_noite' not in st.session_state:
    st.session_state.modo_noite = False  # PADRÃO MODO DIA ATIVADO
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
        elif "firebase" in st.secrets and "base64" in st.secrets["firebase"]:
            fb_dict = json.loads(base64.b64decode(st.secrets["firebase"]["base64"]).decode("utf-8"))
            firebase_admin.initialize_app(credentials.Certificate(fb_dict))
    except Exception as e:
        st.error(f"Aviso de Inicialização Firebase: {e}")

db = firestore.client()

# ==============================================================================
# 🧰 2. SISTEMA DE UTILITÁRIOS E SEGURANÇA OPERACIONAL
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
        R = 6371  # Raio da Terra em KM
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

# ==============================================================================
# 🧠 3. MOTOR DO ARQUITETO INDEPENDENTE (CONSERVAÇÃO DO FLUXO DO CLIENTE)
# ==============================================================================
def carregar_bloco_dinamico():
    try:
        doc = db.collection("configuracoes").document("layout_ia").get()
        return doc.to_dict().get("codigo_injetado", "") if doc.exists else ""
    except: 
        return ""

def painel_adm_arquiteto():
    st.markdown('<br><hr style="border:1px dashed #cbd5e1;"><br>', unsafe_allow_html=True)
    with st.expander("🔐 MODO ARQUITETO (SISTEMA STRUCT)"):
        senha = st.text_input("Senha Master", type="password", key="master_pass")
        if senha == CHAVE_ADMIN_ARQUITETO:
            novo_cod = st.text_area("Injetor de Código Dinâmico", height=250, key="inj_area")
            if st.button("🚀 SOLDAR E RODAR NO SITE AGORA"):
                db.collection("configuracoes").document("layout_ia").set({
                    "codigo_injetado": novo_cod, 
                    "data": datetime.datetime.now()
                })
                st.success("Código injetado com sucesso no Firebase!"); time.sleep(0.5); st.rerun()

# ==============================================================================
# 🏗️ 4. ESTRUTURAÇÃO DO DESIGN SYSTEM E RENDERIZADOR PRINCIPAL
# ==============================================================================
def main():
    # Definição de Cores Dinâmicas Baseada no Tema Selecionado
    cor_bg = "#F8FAFC" if not st.session_state.modo_noite else "#0D1117"
    cor_texto = "#1A1A1B" if not st.session_state.modo_noite else "#FFFFFF"
    cor_bloco = "#FFFFFF" if not st.session_state.modo_noite else "#161B22"
    cor_borda = "#E2E8F0" if not st.session_state.modo_noite else "#30363D"

    # Injeção Estética Customizada (Redução de Padding e Controle do Botão de Tema)
    st.markdown(f"""
    <style>
        #MainMenu, footer, header {{ visibility: hidden; }}
        .stApp {{ background-color: {cor_bg} !important; color: {cor_texto} !important; }}
        .block-container {{ padding-top: 1.5rem !important; padding-bottom: 3rem !important; }}
        
        /* Blocos de Conteúdo */
        .bloco {{ 
            background: {cor_bloco} !important; 
            border-radius: 15px; 
            padding: 20px; 
            margin-bottom: 25px; 
            border: 1px solid {cor_borda} !important; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.02); 
            color: {cor_texto} !important;
        }}
        
        /* Ajuste de Tamanho e Escala do Botão de Alternância de Tema */
        .floating-toggle-box {{
            margin-top: -65px !important;
            margin-right: 20px !important;
            float: right !important;
            position: relative !important;
            z-index: 99999 !important;
        }}
        .floating-toggle-box div[data-testid="stWidgetLabel"] p {{
            font-size: 0.75rem !important;
            font-weight: bold !important;
            color: white !important;
        }}
        .floating-toggle-box .stToggle {{
            scale: 0.75 !important;
            transform-origin: right center;
        }}
    </style>
    """, unsafe_allow_html=True)

    # Divisão Responsiva Estrutural (Layout Lateral vs Principal)
    col_lateral, col_central = st.columns([1, 2.6])

    # 🧭 NAVEGADOR LATERAL FIXO REESTRUTURADO
    with col_lateral:
        st.markdown('<div class="bloco">', unsafe_allow_html=True)
        st.markdown("<h3 style='margin-top:0;'>🧭 Menu GeralJá</h3>", unsafe_allow_html=True)
        
        # Lista dinâmica Baseada em Autorização e Comandos Secretos
        opcoes_navegacao = ["🔍 BUSCAR", "🚀 CADASTRAR", "👤 MEU PERFIL", "⭐ FEEDBACK"]
        
        comando_secreto = st.text_input("Comando Secreto", type="password", help="Código de Infraestrutura")
        if comando_secreto == "abracadabra":
            opcoes_navegacao.append("📊 FINANCEIRO")
        elif comando_secreto == "admin99":
            opcoes_navegacao.append("👑 ADMIN")
            
        aba_atual = st.radio("Navegar pelas Abas:", opcoes_navegacao, label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Acoplamento de Injetor de Código no final da barra lateral
        painel_adm_arquiteto()

    # 🏢 PAINEL CENTRAL DE OPERAÇÕES REVESTIDO
    with col_central:
        # Capa com Degradê Turbo de Alta Visibilidade
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1d4ed8 0%, #1e3a8a 100%); border-radius: 15px; padding: 25px; color: white;">
            <h1 style="color: white; margin: 0; font-size: 2.1rem; font-weight: 900; letter-spacing: -1px;">GeralJá Turbo 🎯</h1>
            <small style="color: #BFDBFE; font-weight: bold; letter-spacing: 0.5px;">SISTEMA INTEGRADO DE INTELIGÊNCIA LOCAL</small>
        </div>
        """, unsafe_allow_html=True)

        # Injeção Estética do Botão de Modo Noite Dentro da Capa (Layout Flutuante Integrado)
        st.markdown('<div class="floating-toggle-box">', unsafe_allow_html=True)
        st.session_state.modo_noite = st.toggle("🌙 Escuro", value=st.session_state.modo_noite)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div style="clear: both; margin-bottom: 5px;"></div>', unsafe_allow_html=True)

        # --- CANTEIRO DE OBRAS AUTOMÁTICO (EXECUÇÃO EXTERNA SE HOUVER) ---
        codigo_da_ia = carregar_bloco_dinamico()
        if codigo_da_ia:
            try:
                exec(codigo_da_ia)
            except Exception as e:
                st.error(f"Aviso no motor de Injeção Volátil: {e}")

        # ======================================================================
        # MÓDULO RENDER: 🔍 BUSCAR
        # ======================================================================
        if aba_atual == "🔍 BUSCAR":
            st.markdown('<div class="bloco">', unsafe_allow_html=True)
            st.markdown("<h3 style='margin-top:0;'>🏙️ O que você procura no bairro hoje?</h3>", unsafe_allow_html=True)
            
            c_gps1, c_gps2 = st.columns([7, 3])
            termo_busca = c_gps1.text_input("Ex: 'Chaveiro urgência', 'Pizzaria' ou 'Diarista'", key="main_search_v5")
            raio_km = c_gps2.select_slider("Raio de Ação (KM)", options=[1, 3, 5, 10, 20, 100], value=5)
            st.markdown('</div>', unsafe_allow_html=True)

            if termo_busca:
                # Conversor inteligente de Categoria Baseado em Conceito
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

                # Query Filtrada do Firebase: Exclui Automaticamente "De Gelo" ou "Bloqueados"
                profs_stream = db.collection("profissionais")\
                    .where("area", "==", categoria_resolvida)\
                    .where("aprovado", "==", True).stream()
                
                lista_ranking = []
                for doc in profs_stream:
                    p = doc.to_dict()
                    p['id'] = doc.id
                    distancia = calcular_distancia_real(st.session_state.minha_lat, st.session_state.minha_lon, p.get('lat', LAT_REF), p.get('lon', LON_REF))
                    
                    if distancia <= raio_km:
                        p['dist'] = distancia
                        p['score_elite'] = (1000 if p.get('saldo', 0) > 0 else 0)
                        lista_ranking.append(p)
                
                lista_ranking.sort(key=lambda x: (x['dist'], -x['score_elite']))

                if not lista_ranking:
                    st.info(f"Nenhum profissional de '{categoria_resolvida}' ativo foi encontrado dentro deste raio de distância.")
                else:
                    for p in lista_ranking:
                        cor_borda_card = "#FF8C00" if p['score_elite'] > 0 else "#1d4ed8"
                        f_url = p.get('foto_url', "https://cdn-icons-png.flaticon.com/512/149/149071.png")
                        
                        st.markdown(f"""
                        <div style="background:{cor_bloco}; border-radius:15px; border-left:6px solid {cor_borda_card}; padding:15px; margin-bottom:12px; box-shadow:0 2px 8px rgba(0,0,0,0.05); display:flex; align-items:center; gap:15px;">
                            <img src="{f_url}" style="width:50px; height:50px; border-radius:50%; object-fit:cover;">
                            <div style="flex-grow:1;">
                                <h4 style="margin:0; color:{cor_texto}; font-size:15px;">{p.get('nome').upper()}</h4>
                                <p style="margin:2px 0 0 0; color:gray; font-size:12px;">{p.get('descricao')[:90]}...</p>
                                <span style="font-size:11px; color:#1d4ed8; font-weight:bold;">📍 Distância: {p['dist']:.1f} KM</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Sacola de Vendas Diretas Embutida por Profissional
                        with st.expander(f"📦 Ver Vitrine / Catálogo de {p.get('nome')}"):
                            produtos_stream = db.collection("profissionais").document(p['id']).collection("produtos").stream()
                            tem_produto = False
                            for prod_doc in produtos_stream:
                                tem_produto = True
                                prod = prod_doc.to_dict()
                                c_pr1, c_pr2 = st.columns([8, 2])
                                c_pr1.markdown(f"**{prod.get('nome')}** — <span style='color:#FF8C00; font-weight:bold;'>R$ {prod.get('preco'):.2f}</span><br><small>{prod.get('descricao')}</small>", unsafe_allow_html=True)
                                if c_pr2.button("➕ Sacola", key=f"add_{p['id']}_{prod.get('id')}"):
                                    loja_id = p['id']
                                    if loja_id not in st.session_state.carrinho:
                                        st.session_state.carrinho[loja_id] = {"nome_loja": p.get('nome'), "whatsapp": p.get('whatsapp'), "itens": {}}
                                    p_id = prod.get('id')
                                    if p_id in st.session_state.carrinho[loja_id]["itens"]:
                                        st.session_state.carrinho[loja_id]["itens"][p_id]["qtd"] += 1
                                    else:
                                        st.session_state.carrinho[loja_id]["itens"][p_id] = {"nome": prod.get('nome'), "preco": prod.get('preco'), "qtd": 1}
                                    st.toast("Adicionado à sacola!")
                            if not tem_produto:
                                st.caption("Este parceiro não cadastrou produtos para venda direta ainda.")
                        
                        link_direto_zap = f"https://wa.me/{limpar_whatsapp(p.get('whatsapp'))}?text=Olá,%20vi%20seu%20perfil%20no%20GeralJá!"
                        st.markdown(f'<a href="{link_direto_zap}" target="_blank" style="display:block; text-align:center; background:#1d4ed8; color:white; padding:8px; border-radius:8px; font-weight:bold; text-decoration:none; margin-bottom:20px; font-size:13px;">💬 TRATAR DIRETO NO WHATSAPP</a>', unsafe_allow_html=True)

            # Sacola de Compras Ativa Interativa
            if st.session_state.carrinho:
                st.markdown('<div class="bloco" style="border: 2px solid #FF8C00 !important;">', unsafe_allow_html=True)
                st.markdown("### 🛒 Sua Sacola de Pedidos GeralJá</h3>", unsafe_allow_html=True)
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
                    
                    texto_zap += f"\n💰 Total: R$ {total_pedido:.2f}\n💻 Plataforma GeralJá (geralja.com.br)"
                    st.markdown(f"**Total Geral: R$ {total_pedido:.2f}**")
                    
                    link_checkout = f"https://wa.me/{limpar_whatsapp(sacola['whatsapp'])}?text={urllib.parse.quote(texto_zap)}"
                    c_s1, c_s2 = st.columns(2)
                    c_s1.markdown(f'<a href="{link_checkout}" target="_blank" style="display:block; text-align:center; background:#25D366; color:white; padding:10px; border-radius:8px; text-decoration:none; font-weight:bold;">🚀 CONFERIR PEDIDO NO ZAP</a>', unsafe_allow_html=True)
                    if c_s2.button("🗑️ Limpar Sacola", key=f"clear_{l_id}"):
                        del st.session_state.carrinho[l_id]
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            # Plantão Noticioso Grajaú Tem Integrado por RSS
            st.markdown("### 📰 Plantão de Notícias Locais - Grajaú Tem")
            try:
                feed = feedparser.parse("https://news.google.com/rss/search?q=Grajaú+São+Paulo&hl=pt-BR&gl=BR&ceid=BR:pt-419")
                entries = feed.entries[:2]
                cols_noticia = st.columns(2)
                for i, ent in enumerate(entries):
                    with cols_noticia[i]:
                        st.markdown(f"""
                        <div class="bloco" style="height:150px; overflow:hidden;">
                            <span style="background:#e11d48; color:white; font-size:10px; padding:2px 6px; border-radius:4px; font-weight:bold;">🚨 URGENTE</span>
                            <h5 style="margin:5px 0; font-size:13px;"><a href="{ent.link}" target="_blank" style="color:{cor_texto}; text-decoration:none;">{ent.title.split(' - ')[0]}</a></h5>
                            <small style="color:gray;">Fonte: {ent.source.get('title','Google News')}</small>
                        </div>
                        """, unsafe_allow_html=True)
            except:
                st.caption("Plantão de notícias temporariamente offline.")

        # ======================================================================
        # MÓDULO RENDER: 🚀 CADASTRAR
        # ======================================================================
        elif aba_atual == "🚀 CADASTRAR":
            st.markdown('<div class="bloco">', unsafe_allow_html=True)
            st.markdown("<h3 style='margin-top:0;'>🚀 Cadastre sua Empresa ou Serviço Autônomo</h3>", unsafe_allow_html=True)
            
            with st.form("cadastro_form_master", clear_on_submit=True):
                col_c1, col_c2 = st.columns(2)
                c_nome = col_c1.text_input("Nome Comercial / Marca")
                c_zap = col_c2.text_input("WhatsApp (Apenas números com DDD)")
                
                col_c3, col_c4 = st.columns(2)
                c_area = col_c3.selectbox("Sua Categoria de Atuação Principal", CATEGORIAS_OFICIAIS)
                c_senha = col_c4.text_input("Defina sua Senha de Acesso", type="password")
                
                c_desc = st.text_area("Descrição de Serviços e Diferenciais")
                c_foto = st.file_uploader("Upload de Logo ou Foto de Perfil", type=['png', 'jpg', 'jpeg'])
                
                if st.form_submit_button("💾 SALVAR E ATIVAR PERFIL CADAS TRAL"):
                    if not c_nome or not c_zap or not c_senha:
                        st.warning("⚠️ Nome, WhatsApp e Senha de acesso são campos obrigatórios!")
                    else:
                        foto_processada = "https://cdn-icons-png.flaticon.com/512/149/149071.png"
                        if c_foto:
                            foto_processada = otimizar_imagem_local(c_foto)
                            
                        db.collection("profissionais").document(c_zap).set({
                            "nome": c_nome, "whatsapp": c_zap, "area": c_area, "senha": c_senha,
                            "descricao": c_desc, "foto_url": foto_processada, "saldo": BONUS_WELCOME,
                            "cliques": 0, "status": "Ativo", "aprovado": True, "data_cadastro": datetime.datetime.now().strftime("%d/%m/%Y"),
                            "lat": st.session_state.minha_lat, "lon": st.session_state.minha_lon
                        })
                        st.balloons()
                        st.success(f"🎊 Cadastro integrado com sucesso! Você ganhou um bônus de de {BONUS_WELCOME} créditos🪙")
            st.markdown('</div>', unsafe_allow_html=True)

        # ======================================================================
        # MÓDULO RENDER: 👤 MEU PERFIL
        # ======================================================================
        elif aba_atual == "👤 MEU PERFIL":
            st.markdown('<div class="bloco">', unsafe_allow_html=True)
            if not st.session_state.auth:
                st.markdown("<h3 style='margin-top:0;'>👤 Acesso Restrito do Comerciante</h3>", unsafe_allow_html=True)
                col_l1, col_l2 = st.columns(2)
                log_zap = col_l1.text_input("WhatsApp Cadastrado")
                log_senha = col_l2.text_input("Sua Senha", type="password")
                
                if st.button("🔓 ENTRAR NO PAINEL", use_container_width=True):
                    doc_user = db.collection("profissionais").document(log_zap).get()
                    if doc_user.exists:
                        dados = doc_user.to_dict()
                        if str(dados.get('senha')) == str(log_senha):
                            # SISTEMA DE SEGURANÇA: Bloqueado não faz login
                            if dados.get('status') == "Bloqueado":
                                st.error("🚫 Acesso Recusado: Este estabelecimento está BLOQUEADO pela administração.")
                            else:
                                st.session_state.auth = True
                                st.session_state.user_id = log_zap
                                st.success("Acesso autorizado!"); time.sleep(0.5); st.rerun()
                        else: st.error("Senha incorreta.")
                    else: st.error("Conta não localizada no sistema.")
            else:
                # Dashboard do Parceiro Autenticado
                p_ref = db.collection("profissionais").document(st.session_state.user_id)
                p_data = p_ref.get().to_dict()
                
                st.markdown(f"<h3 style='margin-top:0;'>Painel de Gerenciamento de {p_data.get('nome')}</h3>", unsafe_allow_html=True)
                
                if p_data.get('status') == "De Gelo":
                    st.warning("🧊 **Status Suspenso:** Seu perfil está configurado 'De Gelo' pela moderação. Seus anúncios estão temporariamente ocultos das buscas.")
                
                m_c1, m_c2, m_c3 = st.columns(3)
                m_c1.metric("Saldo de Impulsionamento", f"{p_data.get('saldo', 0)} 🪙")
                m_c2.metric("Visualizações Direct", f"{p_data.get('cliques', 0)} 📈")
                m_c3.metric("Moderação Comercial", str(p_data.get('status')).upper())
                
                if st.button("📍 VINCULAR MEU ENDEREÇO ATUAL AO GPS DO SITE", use_container_width=True):
                    p_ref.update({"lat": st.session_state.minha_lat, "lon": st.session_state.minha_lon})
                    st.success("Coordenadas atualizadas em tempo real no servidor!")

                # Inserção de Itens de Vitrine Pro
                st.markdown("---")
                st.markdown("#### 📦 Cadastrar Item em sua Vitrine")
                with st.form("form_add_prod", clear_on_submit=True):
                    pr_nome = st.text_input("Nome do Item / Serviço")
                    pr_preco = st.number_input("Preço de Venda (R$)", min_value=0.0, step=0.50)
                    pr_desc = st.text_input("Breve descrição do item")
                    if st.form_submit_button("🚀 PUBLICAR NO MEU CARDÁPIO"):
                        if pr_nome and pr_preco > 0:
                            id_p = f"item_{int(time.time())}"
                            db.collection("profissionais").document(st.session_state.user_id).collection("produtos").document(id_p).set({
                                "id": id_p, "nome": pr_nome, "preco": float(pr_preco), "descricao": pr_desc
                            })
                            st.success("Item adicionado ao portfólio de vendas!"); time.sleep(0.5); st.rerun()

                if st.button("🚪 LOGOUT / SAIR DO PAINEL", type="secondary"):
                    st.session_state.auth = False
                    st.session_state.user_id = None
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # ======================================================================
        # MÓDULO RENDER: ⭐ FEEDBACK
        # ======================================================================
        elif aba_atual == "⭐ FEEDBACK":
            st.markdown('<div class="bloco">', unsafe_allow_html=True)
            st.markdown("<h3 style='margin-top:0;'>⭐ Fale com o GeralJá / Envie Críticas</h3>", unsafe_allow_html=True)
            with st.form("feedback_system"):
                f_nome = st.text_input("Seu Nome")
                f_texto = st.text_area("O que você gostaria de sugerir para melhorias no app?")
                if st.form_submit_button("ENVIAR SUGESTÃO") and f_texto:
                    db.collection("feedbacks").add({
                        "nome": f_nome if f_nome else "Morador Anônimo",
                        "mensagem": f_texto, "data": datetime.datetime.now().strftime("%d/%m/%Y")
                    })
                    st.success("Feedback registrado com sucesso!")
            st.markdown('</div>', unsafe_allow_html=True)

        # ======================================================================
        # MÓDULO OCULTO RENDER: 👑 ADMIN (CONTROLE TOTAL)
        # ======================================================================
        elif aba_atual == "👑 ADMIN":
            st.markdown('<div class="bloco" style="border:1px solid #10b981 !important;">', unsafe_allow_html=True)
            st.markdown("<h3 style='margin-top:0; color:#10b981;'>👑 Central Administrativa Suprema (Modo Root)</h3>", unsafe_allow_html=True)
            
            # Puxa a listagem em tempo real de todas as contas do Firebase
            todos_usuarios = db.collection("profissionais").stream()
            
            for doc in todos_usuarios:
                usr = doc.to_dict()
                u_id = doc.id
                u_status = usr.get("status", "Ativo")
                
                if u_status == "Ativo": color_lbl = "#10b981"
                elif u_status == "De Gelo": color_lbl = "#38bdf8"
                else: color_lbl = "#ef4444"
                
                st.markdown(f"""
                <div style="background:{cor_bg}; padding:12px; border-left: 5px solid {color_lbl}; border-radius:8px; margin-bottom:10px;">
                    <b style="color:{cor_texto}; font-size:14px;">🏢 Lojista: {usr.get('nome')}</b> | Contato: <code>{u_id}</code><br>
                    Especialidade: {usr.get('area')} | Status: <span style="color:{color_lbl}; font-weight:bold;">{u_status.upper()}</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Botões Finos do Sistema de Punição Comercial e Moderação
                btn_c1, btn_c2, btn_c3, btn_c4 = st.columns(4)
                
                with btn_c1:
                    if u_status != "Ativo":
                        if st.button("🟢 Ativar", key=f"adm_atv_{u_id}"):
                            db.collection("profissionais").document(u_id).update({"aprovado": True, "status": "Ativo"})
                            st.success("Perfil Ativo!"); time.sleep(0.4); st.rerun()
                with btn_c2:
                    if u_status != "De Gelo":
                        if st.button("🧊 De Gelo", key=f"adm_gel_{u_id}", help="Oculta dos clientes na busca, mas permite que ele acesse seu próprio perfil"):
                            db.collection("profissionais").document(u_id).update({"aprovado": False, "status": "De Gelo"})
                            st.warning("No Gelo!"); time.sleep(0.4); st.rerun()
                with btn_c3:
                    if u_status != "Bloqueado":
                        if st.button("🚫 Bloquear", key=f"adm_blk_{u_id}", help="Oculta das buscas e tranca a tela de login dele"):
                            db.collection("profissionais").document(u_id).update({"aprovado": False, "status": "Bloqueado"})
                            st.error("Trancado!"); time.sleep(0.4); st.rerun()
                with btn_c4:
                    if st.button("❌ Banir", key=f"adm_del_{u_id}", help="Deleta permanentemente do Banco de Dados"):
                        db.collection("profissionais").document(u_id).delete()
                        st.error("Deletado do Core!"); time.sleep(0.4); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # ======================================================================
        # MÓDULO OCULTO RENDER: 📊 FINANCEIRO
        # ======================================================================
        elif aba_atual == "📊 FINANCEIRO":
            st.markdown('<div class="bloco">', unsafe_allow_html=True)
            st.markdown("<h3 style='margin-top:0;'>📊 Balanço Financeiro da Vitrine</h3>", unsafe_allow_html=True)
            st.metric("Estimativa de Faturamento com Assinaturas", "R$ 14.820,00", "Elite Scale")
            
            st.markdown("### 🏷️ Tabela Vigente de Pacotes - Grajaú Tem")
            st.markdown("""
            * **🔴 Vitrine de Ofertas (Giro Diário):** R$ 100 Unitário | R$ 600 Mensal
            * **🥉 Pacote Bronze (1 Post):** R$ 150
            * **🥈 Pacote Prata (3 Posts):** R$ 400
            * **🥇 Pacote Ouro (10 Posts):** R$ 700
            * **📻 Anúncio Rádio Grajaú Tem:** R$ 300/mês
            """)
            st.markdown('</div>', unsafe_allow_html=True)

        # 🎯 RODAPÉ COMERCIAL DE ALTA CONVERSÃO
        st.markdown(f"""
        <div style="text-align:center; padding:15px; opacity:0.7; font-size:12px; color:{cor_texto}; margin-top:20px;">
            <p>🎯 <b>GeralJá Brasil</b> — Sistema de Conexões Locais Inteligentes</p>
            <p>© 2026 geralja.com.br | Todos os direitos reservados</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
