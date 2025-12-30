# ==============================================================================
# GERALJÁ BRASIL - ENTERPRISE EDITION v20.0 (FULL & UNIFIED)
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
import pandas as pd
import unicodedata

# ------------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DE AMBIENTE E PERFORMANCE
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="GeralJá | Ecossistema Profissional Brasil",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="collapsed"
)
# --- DESIGN SISTEMA PODEROSO (CSS CUSTOMIZADO) ---
st.markdown("""
<style>
    /* Estilo dos Cards de Profissionais */
    .pro-card {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 15px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        display: flex;
        align-items: center;
        gap: 20px;
        transition: transform 0.2s;
    }
    .pro-card:hover {
        transform: scale(1.02);
        border-color: #3b82f6;
    }
    
    /* Foto do Profissional */
    .pro-img {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid #3b82f6;
    }

    /* Botão do WhatsApp Estilizado */
    .btn-zap {
        display: block;
        width: 100%;
        background-color: #25D366;
        color: white !important;
        text-align: center;
        padding: 12px;
        border-radius: 10px;
        text-decoration: none;
        font-weight: bold;
        margin-top: 10px;
        box-shadow: 0 4px 10px rgba(37, 211, 102, 0.3);
    }
    .btn-zap:hover {
        background-color: #1eb954;
        text-decoration: none;
    }

    /* Box de Métricas do Parceiro (Aba 2) */
    .metric-box {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        color: #f8fafc;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        font-weight: bold;
        font-size: 18px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    /* Ajuste para Mobile */
    @media (max-width: 640px) {
        .pro-card {
            flex-direction: column;
            text-align: center;
        }
        .pro-img {
            margin: 0 auto;
        }
    }
</style>
""", unsafe_allow_html=True)
# ------------------------------------------------------------------------------
# 2. CAMADA DE PERSISTÊNCIA (FIREBASE)
# ------------------------------------------------------------------------------
@st.cache_resource
def conectar_banco_master():
    if not firebase_admin._apps:
        try:
            if "FIREBASE_BASE64" not in st.secrets:
                st.error("🔑 Chave de segurança FIREBASE_BASE64 não encontrada.")
                st.stop()
            b64_key = st.secrets["FIREBASE_BASE64"]
            decoded_json = base64.b64decode(b64_key).decode("utf-8")
            cred_dict = json.loads(decoded_json)
            cred = credentials.Certificate(cred_dict)
            return firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"❌ FALHA NA INFRAESTRUTURA: {e}")
            st.stop()
    return firebase_admin.get_app()

app_engine = conectar_banco_master()
db = firestore.client()

# ------------------------------------------------------------------------------
# 3. POLÍTICAS E CONSTANTES
# ------------------------------------------------------------------------------
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ADMIN = "mumias"
TAXA_CONTATO = 1
BONUS_WELCOME = 5
LAT_REF = -23.5505
LON_REF = -46.6333

# --- EXPANSÃO MASSIVA DE CATEGORIAS GERALJÁ (MULTIPLICADOR DE BUSCAS) ---
CATEGORIAS_OFICIAIS = sorted([
    # 🏠 CONSTRUÇÃO, ESTRUTURA E REFORMAS
    "Ajudante de Pedreiro", "Azulejista", "Armador de Ferragens", "Arquitetura e Urbanismo",
    "Bombeiro Civil", "Calceteiro", "Carpinteiro de Formas", "Colocador de Pisos",
    "Demolidor", "Eletricista Predial", "Eletricista Industrial", "Encanador Hidráulico",
    "Engenheiro Civil", "Gesseiro Acartonado", "Gesseiro Revestidor", "Impermeabilizador de Lajes",
    "Instalador de Drywall", "Ladrilheiro", "Marmorista", "Mestre de Obras",
    "Montador de Estrutura Metálica", "Pedreiro de Alvenaria", "Pedreiro de Acabamento",
    "Pintor Residencial", "Pintor de Letreiros", "Pintor Industrial", "Serralheiro de Alumínio",
    "Serralheiro de Ferro", "Telhadista", "Vidraceiro de Sacadas",

    # 🛠️ MANUTENÇÃO, INSTALAÇÃO E MARIDO DE ALUGUEL
    "Afiador de Ferramentas", "Chaveiro Residencial", "Chaveiro Automotivo", "Desentupidor de Esgoto",
    "Instalador de Ar Condicionado", "Instalador de Papel de Parede", "Instalador de Redes de Proteção",
    "Instalador de Ventilador de Teto", "Instalador de Câmeras/CFTV", "Instalador de Alarme",
    "Limpeza de Caixa d'Água", "Limpeza de Calhas", "Marido de Aluguel", "Montador de Móveis",
    "Refrigeração Comercial", "Reparo de Micro-ondas", "Técnico de Fogão a Gás",
    "Técnico de Máquina de Lavar", "Técnico de Geladeira/Freezer", "Técnico de TV",

    # 🧹 SERVIÇOS DOMÉSTICOS E CUIDADOS
    "Babá (Folguista)", "Babá (Mensalista)", "Banhista de Pets", "Cozinheira Particular",
    "Cuidador de Idosos", "Cuidador de Pessoas com Deficiência", "Diarista", "Dog Walker",
    "Faxineira de Pós-Obra", "Faxineira Residencial", "Gardener (Paisagista)", "Governança",
    "Jardineiro", "Lavadeira", "Limpador de Vidros", "Passadeira", "Piscineiro",
    "Personal Organizer", "Pet Sitter",

    # 🚗 SETOR AUTOMOTIVO E TRANSPORTE
    "Auto Elétrico", "Borracheiro 24h", "Carreto e Mudanças", "Entregador Motoboy",
    "Funileiro", "Guincho Leve", "Guincho Pesado", "Instalador de Insulfilm",
    "Lava Jato a Seco", "Martelinho de Ouro", "Mecânico de Motos", "Mecânico de Suspensão",
    "Mecânico Diesel", "Motorista Particular", "Pintor Automotivo", "Tapeceiro Automotivo",

    # 💻 TECNOLOGIA, DESIGN E ESCRITÓRIO
    "Analista de Redes", "Assistência Técnica de Celular", "Assistência Técnica de Tablet",
    "Designer de Logotipos", "Desenvolvedor Mobile", "Desenvolvedor Web", "Editor de Vídeos",
    "Gestor de Tráfego Pago", "Gestor de Redes Sociais", "Programador Python",
    "Suporte de TI Remoto", "Técnico de Impressoras", "Técnico de Notebooks",

    # 💇 BELEZA, ESTÉTICA E BEM-ESTAR
    "Barbeiro Visagista", "Cabeleireiro Especialista", "Designer de Sobrancelhas",
    "Depiladora a Laser", "Esteticista Facial", "Esteticista Corporal", "Extensionista de Cílios",
    "Maquiadora Social", "Manicure e Pedicure", "Massagista Terapêutico", "Nail Designer (Unhas de Gel)",
    "Penteadista", "Podóloga", "Tatuador", "Piercer",

    # 🎤 EVENTOS, GASTRONOMIA E LAZER
    "Animador de Festas", "Buffet Completo", "Barman/Bartender", "Churrasqueiro Profissional",
    "Confeiteira de Bolos Artísticos", "DJ para Eventos", "Fotógrafo de Casamento",
    "Fotógrafo de Produtos", "Garçom e Garçonete", "Recepcionista de Eventos",
    "Segurança Particular", "Salgadeira",

    # 🔧 OUTROS SERVIÇOS ESPECIALIZADOS
    "Ajudante Geral", "Alfaiate/Costureira", "Adestrador de Cães", "Consultor Jurídico",
    "Detetive Particular", "Investigador Particular", "Professor de Reforço Escolar",
    "Professor de Música", "Sapateiro", "Tapeceiro de Móveis", "Tradutor/Intérprete",
    "Outro (Personalizado)"
])

# DICIONÁRIO EXPANDIDO (Soma de inteligência)
CONCEITOS_EXPANDIDOS = {
    # Hidráulica
    "vazamento": "Encanador", "cano": "Encanador", "torneira": "Encanador", "descarga": "Encanador", 
    "caixa dagua": "Encanador", "esgoto": "Encanador", "pia": "Encanador", "entupiu": "Encanador",
    # Elétrica
    "curto": "Eletricista", "fiacao": "Eletricista", "luz": "Eletricista", "chuveiro": "Eletricista", 
    "tomada": "Eletricista", "disjuntor": "Eletricista", "energia": "Eletricista", "lampada": "Eletricista",
    # Reforma
    "pintar": "Pintor", "pintura": "Pintor", "reforma": "Pedreiro", "piso": "Pedreiro", "azulejo": "Pedreiro", 
    "tijolo": "Pedreiro", "cimento": "Pedreiro", "telhado": "Telhadista", "goteira": "Telhadista",
    "gesso": "Gesseiro", "drywall": "Gesseiro", "solda": "Serralheiro", "portao": "Serralheiro",
    # Automotivo
    "carro": "Mecânico", "motor": "Mecânico", "oleo": "Mecânico", "guincho": "Guincho 24h", 
    "reboque": "Guincho 24h", "pneu": "Borracheiro", "estepe": "Borracheiro", "furou": "Borracheiro",
    # Domésticos
    "faxina": "Diarista", "limpeza": "Diarista", "passar": "Diarista", "jardim": "Jardineiro", 
    "grama": "Jardineiro", "piscina": "Piscineiro", "cloro": "Piscineiro",
    # Tecnologia/Eletros
    "computador": "TI", "notebook": "TI", "formatar": "TI", "wifi": "TI", "internet": "TI",
    "ar": "Refrigeração", "geladeira": "Refrigeração", "freezer": "Refrigeração",
    "fogao": "Técnico de Fogão", "maquina de lavar": "Técnico de Lavadora",
    # Logística/Montagem
    "montar": "Montador", "armario": "Montador", "moveis": "Montador",
    "frete": "Freteiro", "mudanca": "Freteiro", "carreto": "Freteiro",
    "chave": "Chaveiro", "fechadura": "Chaveiro"
}

# ------------------------------------------------------------------------------
# 4. MOTORES DE IA E GEOLOCALIZAÇÃO
# ------------------------------------------------------------------------------
def normalizar_para_ia(texto):
    if not texto: return ""
    return "".join(c for c in unicodedata.normalize('NFD', str(texto)) 
                  if unicodedata.category(c) != 'Mn').lower().strip()

def processar_ia_avancada(texto):
    if not texto: return "Ajudante Geral"
    t_clean = normalizar_para_ia(texto)
    for chave, categoria in CONCEITOS_EXPANDIDOS.items():
        chave_norm = normalizar_para_ia(chave)
        if re.search(rf"\b{chave_norm}\b", t_clean):
            return categoria
    return "Ajudante Geral"

def calcular_distancia_real(lat1, lon1, lat2, lon2):
    try:
        if None in [lat1, lon1, lat2, lon2]: return 999.0
        R = 6371 
        dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)
    except: return 999.0

def converter_img_b64(file):
    if file is None: return ""
    try: return base64.b64encode(file.read()).decode()
    except: return ""
# ==============================================================================
# SISTEMA GUARDIAO - IA DE AUTORRECUPERAÇÃO E SEGURANÇA
# ==============================================================================

def guardia_escanear_e_corrigir():
    """Varre o banco de dados em busca de erros de estrutura e corrige na hora."""
    status_log = []
    try:
        profs = db.collection("profissionais").stream()
        for p_doc in profs:
            dados = p_doc.to_dict()
            id_pro = p_doc.id
            correcoes = {}

            # 1. Verifica campos nulos que causam travamentos
            if not dados.get('area') or dados.get('area') not in CATEGORIAS_OFICIAIS:
                correcoes['area'] = "Ajudante Geral"
            
            if not dados.get('descricao'):
                correcoes['descricao'] = "Profissional parceiro do ecossistema GeralJá Brasil."
            
            if dados.get('saldo') is None:
                correcoes['saldo'] = 0
            
            if dados.get('lat') is None or dados.get('lon') is None:
                correcoes['lat'] = LAT_REF
                correcoes['lon'] = LON_REF

            # 2. Se houver algo errado, aplica a cura automática
            if correcoes:
                db.collection("profissionais").document(id_pro).update(correcoes)
                status_log.append(f"✅ Corrigido: {id_pro}")
        
        return status_log if status_log else ["SISTEMA ÍNTEGRO: Nenhum erro encontrado."]
    except Exception as e:
        return [f"❌ Erro no Scanner: {e}"]

def scan_virus_e_scripts():
    """Detecta se há tentativas de injeção de scripts maliciosos nos campos de texto."""
    alertas = []
    profs = db.collection("profissionais").stream()
    # Padrões comuns de ataque XSS e Injeção
    padroes_perigosos = [r"<script>", r"javascript:", r"DROP TABLE", r"OR 1=1"]
    
    for p_doc in profs:
        dados = p_doc.to_dict()
        conteudo = str(dados.get('nome', '')) + str(dados.get('descricao', ''))
        
        for padrao in padroes_perigosos:
            if re.search(padrao, conteudo, re.IGNORECASE):
                alertas.append(f"⚠️ PERIGO: Conteúdo suspeito no ID {p_doc.id}")
                # Bloqueia o profissional preventivamente
                db.collection("profissionais").document(p_doc.id).update({"aprovado": False})
    
    return alertas if alertas else ["LIMPO: Nenhum script malicioso detectado."]
# ------------------------------------------------------------------------------
# 5. DESIGN SYSTEM
# ------------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F8FAFC; }
    .header-container { background: white; padding: 40px 20px; border-radius: 0 0 50px 50px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.05); border-bottom: 8px solid #FF8C00; margin-bottom: 25px; }
    .logo-azul { color: #0047AB; font-weight: 900; font-size: 50px; letter-spacing: -2px; }
    .logo-laranja { color: #FF8C00; font-weight: 900; font-size: 50px; letter-spacing: -2px; }
    .pro-card { background: white; border-radius: 25px; padding: 25px; margin-bottom: 20px; border-left: 15px solid #0047AB; box-shadow: 0 10px 20px rgba(0,0,0,0.04); display: flex; align-items: center; }
    .pro-img { width: 100px; height: 100px; border-radius: 50%; object-fit: cover; margin-right: 25px; border: 4px solid #F1F5F9; }
    .btn-zap { background: #22C55E; color: white !important; padding: 15px; border-radius: 15px; text-decoration: none; font-weight: 800; display: block; text-align: center; margin-top: 10px; }
    .metric-box { background: #1E293B; color: white; padding: 20px; border-radius: 20px; text-align: center; border-bottom: 4px solid #FF8C00; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-container"><span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span><br><small style="color:#64748B; font-weight:700;">BRASIL ELITE EDITION</small></div>', unsafe_allow_html=True)

# --- LISTA DE ABAS ---
# O Financeiro não aparece aqui, ele é somado depois pelo comando secreto
lista_abas = ["🔍 BUSCAR", "🚀 CADASTRAR", "👤 MEU PERFIL", "👑 ADMIN", "⭐ FEEDBACK"]

# Comando Secreto para revelar o Financeiro em último
comando_secreto = st.sidebar.text_input("Comando de Diretor", type="password")
if comando_secreto == "abracadabra":
    lista_abas.append("📊 FINANCEIRO")

menu_abas = st.tabs(lista_abas)

# --- ABA 1: BUSCA INTELIGENTE (MOTOR DE SINÔNIMOS) ---
with menu_abas[0]:
    st.markdown("### 🏙️ O que você precisa hoje?")
    
    # 1. MAPA DE SINÔNIMOS (O Cérebro da Busca)
    # Isso faz com que termos populares levem às categorias oficiais
    DICIONARIO_SINONIMOS = {
        "cano": "Encanador", "vazamento": "Encanador", "torneira": "Encanador", "esgoto": "Encanador",
        "fio": "Eletricista", "luz": "Eletricista", "tomada": "Eletricista", "disjuntor": "Eletricista",
        "parede": "Pedreiro", "reforma": "Pedreiro", "tijolo": "Pedreiro", "obra": "Pedreiro",
        "grama": "Jardineiro", "poda": "Jardineiro", "árvore": "Jardineiro",
        "computador": "Técnico de Informática (TI)", "notebook": "Técnico de Informática (TI)", "wifi": "Técnico de Informática (TI)",
        "geladeira": "Técnico de Geladeira/Freezer", "ar": "Instalador de Ar Condicionado", "clima": "Instalador de Ar Condicionado",
        "festa": "Garçom e Garçonete", "churrasco": "Churrasqueiro Profissional", "casamento": "Fotógrafo de Casamento",
        "unha": "Manicure e Pedicure", "cabelo": "Cabeleireiro Especialista", "barba": "Barbeiro Visagista",
        "mudança": "Carreto e Mudanças", "frete": "Carreto e Mudanças", "entrega": "Entregador Motoboy"
    }

    c1, c2 = st.columns([3, 1])
    
    # Campo de busca livre
    termo_busca = c1.text_input("Ex: 'Cano estourado' ou 'Eletricista'", key="main_search", placeholder="O que quebrou?")
    raio_km = c2.select_slider("Raio (KM)", options=[1, 3, 5, 10, 20, 50, 100, 500], value=50)

    # LÓGICA DE FILTRAGEM
    if termo_busca:
        # 2. Processamento do Termo (Transforma 'Cano' em 'Encanador' se existir no dicionário)
        termo_processado = termo_busca.lower().strip()
        categoria_alvo = DICIONARIO_SINONIMOS.get(termo_processado, termo_busca)

        with st.spinner(f"Buscando especialistas em {categoria_alvo}..."):
            # Busca no Firebase (Somando filtros de Categoria e Aprovação)
            profs_ref = db.collection("profissionais").where("aprovado", "==", True)
            todos_profs = profs_ref.stream()
            
            encontrados = []
            for doc in todos_profs:
                p = doc.to_dict()
                # Busca por categoria oficial ou pelo nome do profissional
                if (categoria_alvo.lower() in p.get('area', '').lower()) or \
                   (termo_processado in p.get('nome', '').lower()):
                    encontrados.append(p)

            if encontrados:
                st.success(f"🎉 Encontramos {len(encontrados)} profissionais próximos a você!")
                
                # Exibição em Cards Modernos
                for p in encontrados:
                    with st.container(border=True):
                        col_foto, col_info = st.columns([1, 3])
                        with col_foto:
                            st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
                        with col_info:
                            st.subheader(p.get('nome', 'Profissional').upper())
                            st.caption(f"📍 {p.get('cidade', 'Sua Região')} | ⭐⭐⭐⭐⭐")
                            st.write(f"**Especialidade:** {p.get('area')}")
                            
                            # Botão do WhatsApp com Mensagem Pronta
                            link_zap = f"https://wa.me/{doc.id}?text=Olá%20{p.get('nome')},%20vi%20seu%20perfil%20no%20GeralJá%20e%20preciso%20de%20um%20orçamento!"
                            st.markdown(f'''<a href="{link_zap}" target="_blank">
                                <button style="width:100%; background-color:#25D366; color:white; border:none; padding:10px; border-radius:5px; font-weight:bold; cursor:pointer;">
                                ✅ CHAMAR NO WHATSAPP</button></a>''', unsafe_allow_html=True)
            else:
                st.warning(f"Ainda não temos '{termo_busca}' nesta região. Tente termos como 'Pedreiro' ou 'Eletricista'.")
    else:
        st.info("👋 Digite o que você precisa acima para ver os melhores profissionais da sua região.")
# --- ABA 3: CADASTRO (VERSÃO SOMAR) ---
with menu_abas[2]:
    st.header("🚀 Seja um Parceiro GeralJá")
    st.write("Preencha seus dados para começar a receber serviços na sua região.")
    
    with st.form("reg"):
        col_c1, col_c2 = st.columns(2)
        r_n = col_c1.text_input("Nome Completo")
        r_z = col_c2.text_input("WhatsApp (Apenas números)", help="Ex: 11999999999")
        
        col_c3, col_c4 = st.columns(2)
        r_s = col_c3.text_input("Crie uma Senha", type="password")
        r_a = col_c4.selectbox("Sua Especialidade Principal", CATEGORIAS_OFICIAIS)
        
        r_d = st.text_area("Descreva seus serviços (Isso atrai clientes!)")
        
        st.info("📌 Ao se cadastrar, você ganha um bônus inicial para testar a plataforma!")
        
        if st.form_submit_button("FINALIZAR MEU CADASTRO", use_container_width=True):
            if len(r_z) < 10 or len(r_n) < 3:
                st.error("⚠️ Por favor, preencha Nome e WhatsApp corretamente.")
            else:
                # Criando o documento com a estrutura SOMAR (Tudo o que precisamos)
                try:
                    db.collection("profissionais").document(r_z).set({
                        "nome": r_n,
                        "whatsapp": r_z,
                        "senha": r_s,
                        "area": r_a,
                        "descricao": r_d,
                        "saldo": BONUS_WELCOME, # Bônus de entrada
                        "cliques": 0,
                        "rating": 5.0,         # Começa com nota máxima
                        "aprovado": False,      # Aguarda sua aprovação no Admin
                        "lat": LAT_REF,         # Localização padrão inicial
                        "lon": LON_REF,
                        "foto_url": "",         # Ele poderá subir no painel dele
                        "portfolio_imgs": [],    # Lista de fotos vazia inicial
                        "data_registro": datetime.datetime.now()
                    })
                    st.success("✅ Cadastro enviado com sucesso! Aguarde a aprovação do administrador para aparecer nas buscas.")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro ao cadastrar: {e}")

# --- ABA 4: TERMINAL ADMIN (VERSÃO RECUPERADA & ALINHADA) ---
with menu_abas[3]:
    access_adm = st.text_input("Senha Master", type="password", key="adm_auth_final")
    
    if access_adm == CHAVE_ADMIN:
        st.markdown("### 👑 Painel de Controle Supremo")
        
        # 📩 1. LISTAGEM DE FEEDBACKS (RECUPERADO E ALINHADO)
        with st.expander("📩 Ver Feedbacks Recentes", expanded=False):
            feedbacks = list(db.collection("feedbacks").order_by("data", direction="DESCENDING").limit(10).stream())
            if feedbacks:
                for f in feedbacks:
                    dados_f = f.to_dict()
                    st.write(f"⭐ **{dados_f.get('nota')}**: {dados_f.get('mensagem')}")
            else:
                st.write("Nenhum feedback novo.")

        st.divider()
        
        # 📊 2. MÉTRICAS TOTAIS (SOMA DE INTELIGÊNCIA)
        all_profs_lista = list(db.collection("profissionais").stream())
        total_moedas = sum([p.to_dict().get('saldo', 0) for p in all_profs_lista])
        
        c_fin1, c_fin2, c_fin3 = st.columns(3)
        c_fin1.metric("💰 Moedas no Sistema", f"{total_moedas} 🪙")
        c_fin2.metric("📈 Valor Previsto", f"R$ {total_moedas:,.2f}")
        c_fin3.metric("🤝 Parceiros Atuais", len(all_profs_lista))
        
        st.divider()

        # 🛠️ 3. ABAS DE COMANDO INTERNAS
        t_geral, t_seg, t_feed = st.tabs(["👥 GESTÃO DE PERFIS", "🛡️ IA SEGURANÇA", "📩 MENSAGENS"])
        
        with t_geral:
            search_pro = st.text_input("🔍 Buscar por Nome ou WhatsApp")
            for p_doc in all_profs_lista:
                p, pid = p_doc.to_dict(), p_doc.id
                if not search_pro or search_pro.lower() in p.get('nome', '').lower() or search_pro in pid:
                    status_emoji = "🟢" if p.get('aprovado') else "🟡"
                    with st.expander(f"{status_emoji} {p.get('nome', 'Sem Nome').upper()} | {p.get('saldo', 0)} 🪙"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Área:** {p.get('area')}")
                            st.write(f"**WhatsApp:** {pid}")
                            bonus = st.number_input("Adicionar Moedas", value=0, key=f"add_{pid}")
                            if st.button("CREDITAR", key=f"btn_c_{pid}"):
                                db.collection("profissionais").document(pid).update({"saldo": firestore.Increment(bonus)})
                                st.success("Saldo atualizado!"); time.sleep(1); st.rerun()
                        
                        with col2:
                            st.write("**Ações Rápidas:**")
                            if st.button("✅ APROVAR AGORA", key=f"ok_{pid}", use_container_width=True):
                                db.collection("profissionais").document(pid).update({"aprovado": True}); st.rerun()
                            if st.button("⚠️ SUSPENDER", key=f"sus_{pid}", use_container_width=True):
                                db.collection("profissionais").document(pid).update({"aprovado": False}); st.rerun()
                            if st.button("🗑️ REMOVER", key=f"del_{pid}", use_container_width=True):
                                db.collection("profissionais").document(pid).delete(); st.rerun()

        with t_seg:
            st.markdown("#### 🛡️ Central de Proteção IA")
            s_col1, s_col2 = st.columns(2)
            if s_col1.button("🔍 ESCANEAR BANCO", use_container_width=True):
                with st.spinner("Buscando ameaças..."):
                    alertas = scan_virus_e_scripts()
                    for a in alertas:
                        if "⚠️" in str(a): st.error(str(a))
                        else: st.success(str(a))
            
            if s_col2.button("🛠️ REPARAR ESTRUTURAS", use_container_width=True):
                with st.spinner("IA Corrigindo..."):
                    reparos = guardia_escanear_e_corrigir()
                    for r in reparos: st.write(str(r))
                st.balloons()

        with t_feed:
            st.info("📩 Central de Mensagens: Utilize esta aba para logs do sistema.")

    elif access_adm != "":
        st.error("🚫 Acesso negado. Senha incorreta.")
        
       # --- ABA: FEEDBACK (A VOZ DO CLIENTE) ---
# Se o Financeiro estiver invisível, esta é a aba [4]. 
# Se o Financeiro aparecer, ela continua sendo acessada corretamente pelo índice.
with menu_abas[4]:
    st.markdown("### ⭐ Sua opinião é fundamental")
    st.write("Conte-nos como foi a sua experiência com o GeralJá.")
    
    # Criamos um formulário para organizar o envio
    with st.form("feedback_form", clear_on_submit=True):
        # 1. Escala de Satisfação
        nota = st.select_slider(
            "Qual a sua satisfação geral?",
            options=["Muito Insatisfeito", "Insatisfeito", "Regular", "Satisfeito", "Muito Satisfeito"],
            value="Muito Satisfeito"
        )
        
        # 2. CAIXA DE TEXTO (O que você pediu)
        comentario = st.text_area(
            "Descreva a sua experiência ou deixe uma sugestão:",
            placeholder="Ex: O profissional foi muito atencioso, mas o app poderia carregar mais rápido...",
            height=150
        )
        
        # Botão de envio
        btn_enviar = st.form_submit_button("ENVIAR AVALIAÇÃO", use_container_width=True)
        
        if btn_enviar:
            if comentario.strip() != "":
                try:
                    # Somando o feedback ao banco de dados
                    db.collection("feedbacks").add({
                        "data": datetime.datetime.now(),
                        "nota": nota,
                        "mensagem": comentario,
                        "lido": False
                    })
                    st.success("🙏 Muito obrigado! A sua mensagem foi enviada diretamente para a nossa equipa.")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro ao enviar: {e}")
            else:
                st.warning("⚠️ Por favor, escreva algo na caixa de texto antes de enviar.")

    st.divider()
    st.caption("O GeralJá utiliza os seus feedbacks para melhorar a segurança e a qualidade dos prestadores de serviço.")
# --- ABA 6: FINANCEIRO (SÓ APARECE SOB COMANDO) ---
# Este 'if' evita o IndexError: ele só executa se a aba financeira existir
if len(menu_abas) > 5:
    with menu_abas[5]:
        st.markdown("### 📊 Gestão de Capital GeralJá")
        
        # Chave de segurança extra para abrir o cofre
        senha_cofre = st.text_input("Chave do Cofre", type="password", key="cofre_vFinal")
        
        if senha_cofre == "riqueza2025":
            all_p = list(db.collection("profissionais").stream())
            vendas = sum([p.to_dict().get('total_comprado', 0) for p in all_p])
            
            c1, c2 = st.columns(2)
            c1.metric("💰 FATURAMENTO REAL", f"R$ {vendas:,.2f}")
            c2.metric("🤝 TOTAL PARCEIROS", len(all_p))
            
            st.divider()
            # Tabela de conferência
            st.write("**Histórico de Vendas:**")
            tabela = [{"Profissional": p.to_dict().get('nome'), "Total Pago": p.to_dict().get('total_comprado', 0)} for p in all_p]
            st.dataframe(tabela, use_container_width=True)
        else:
            st.info("Aguardando chave mestra para exibir dados sensíveis.")
# ------------------------------------------------------------------------------
# RODAPÉ ÚNICO (Final do Arquivo)
# ------------------------------------------------------------------------------
st.markdown(f'<div style="text-align:center; padding:20px; color:#94A3B8; font-size:10px;">GERALJÁ v20.0 © {datetime.datetime.now().year}</div>', unsafe_allow_html=True)































