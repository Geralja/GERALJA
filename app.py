==============================================================================
GERALJÁ: PLATAFORMA DE SERVIÇOS LOCAIS
Sistema completo de marketplace com geolocalização, IA e Firebase
Versão: 2.0 - Refatorado e Otimizado
==============================================================================
"""

# ==============================================================================
# 1. IMPORTS E DEPENDÊNCIAS
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
from streamlit_js_eval import streamlit_js_eval, get_geolocation
from typing import Optional, Dict, List, Tuple
import pytz
from urllib.parse import quote


# ==============================================================================
# 2. CONFIGURAÇÕES GLOBAIS E CONSTANTES
# ==============================================================================

# Configuração da página
st.set_page_config(
    page_title="GeralJá | Criando Soluções",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Constantes do Sistema
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ADMIN = "mumias"
TAXA_CONTATO = 1
BONUS_WELCOME = 5
LAT_REF = -23.5505  # Latitude padrão (São Paulo)
LON_REF = -46.6333  # Longitude padrão (São Paulo)

# Categorias oficiais do sistema
CATEGORIAS_OFICIAIS = [
    "Academia", "Acompanhante de Idosos", "Açougue", "Adega", "Adestrador de Cães", 
    "Advocacia", "Agropecuária", "Ajudante Geral", "Animador de Festas", "Arquiteto(a)", 
    "Armarinho/Aviamentos", "Assistência Técnica", "Aulas Particulares", "Auto Elétrica", 
    "Auto Peças", "Babá (Nanny)", "Banho e Tosa", "Barbearia/Salão", "Barman / Bartender", 
    "Bazar", "Borracheiro", "Cabeleireiro(a)", "Cafeteria", "Calçados", "Carreto", 
    "Celulares", "Chaveiro", "Churrascaria", "Clínica Médica", "Comida Japonesa", 
    "Confeiteiro(a)", "Contabilidade", "Costureira / Alfaiate", "Cozinheiro(a) Particular", 
    "Cuidador de Idosos", "Dançarino(a) / Entretenimento", "Decorador(a) de Festas", 
    "Destaque de Eventos", "Diarista / Faxineira", "Doceria", "Eletrodomésticos", 
    "Eletricista", "Eletrônicos", "Encanador", "Escola Infantil", "Estética Automotiva", 
    "Estética Facial", "Esteticista", "Farmácia", "Fisioterapia", "Fitness", "Floricultura", 
    "Fotógrafo(a)", "Freteiro", "Funilaria e Pintura", "Garçom e garçonete", "Gesseiro", 
    "Guincho 24h", "Hamburgueria", "Hortifruti", "Idiomas", "Imobiliária", "Informática", 
    "Instalador de Ar-condicionado", "Internet de fibra óptica", "Jardineiro", "Joalheria", 
    "Lanchonete", "Lava Jato", "Lavagem de Sofás / Estofados", "Loja de Roupas", 
    "Loja de Variedades", "Madeireira", "Manicure e Pedicure", "Maquiador(a)", "Marceneiro", 
    "Marido de Aluguel", "Material de Construção", "Mecânico de Autos", "Montador de Móveis", 
    "Motoboy/Entregas", "Motorista Particular", "Móveis", "Moto Peças", "Nutricionista", 
    "Odontologia", "Ótica", "Outro (Personalizado)", "Padaria", "Papelaria", 
    "Passeador de Cães", "Pastelaria", "Pedreiro", "Pet Shop", "Pintor", "Piscineiro", 
    "Pizzaria", "Professor(a) Particular", "Psicologia", "Recepcionista de Eventos", 
    "Reforço Escolar", "Refrigeração", "Relojoaria", "Salgadeiro(a)", "Segurança / Vigilante", 
    "Seguros", "Som e Alarme", "Sorveteria", "Tatuagem/Piercing", "Técnico de Celular", 
    "Técnico de Fogão", "Técnico de Geladeira", "Técnico de Lavadora", "Técnico de Notebook/PC", 
    "Telhadista", "TI (Tecnologia)", "Tintas", "Veterinário(a)", "Web Designer"
]

# Dicionário de IA - Mapeamento de palavras-chave para categorias
CONCEITOS_EXPANDIDOS = {
    # ALIMENTAÇÃO E GASTRONOMIA
    "pizza": "Pizzaria", "pizzaria": "Pizzaria", "fome": "Pizzaria", "massa": "Pizzaria",
    "lanche": "Lanchonete", "hamburguer": "Lanchonete", "burger": "Lanchonete", 
    "x-tudo": "Lanchonete", "hot dog": "Lanchonete", "cachorro quente": "Lanchonete",
    "comida": "Churrascaria", "almoco": "Churrascaria", "marmita": "Churrascaria",
    "doce": "Confeiteiro(a)", "bolo": "Confeiteiro(a)", "festa": "Confeiteiro(a)",
    "pao": "Padaria", "padaria": "Padaria", "cafe": "Padaria",
    "cerveja": "Adega", "bebida": "Adega", "vinho": "Adega",
    
    # SAÚDE E BELEZA
    "remedio": "Farmácia", "farmacia": "Farmácia", "saude": "Farmácia",
    "cabelo": "Barbearia/Salão", "barba": "Barbearia/Salão", "corte": "Barbearia/Salão",
    "unha": "Manicure e Pedicure", "manicure": "Manicure e Pedicure",
    "dentista": "Odontologia", "dente": "Odontologia",
    
    # TECNOLOGIA
    "celular": "Assistência Técnica", "iphone": "Assistência Técnica", 
    "tela": "Técnico de Celular", "carregador": "Celulares",
    "computador": "TI (Tecnologia)", "notebook": "Técnico de Notebook/PC",
    "internet": "Internet de fibra óptica", "wifi": "TI (Tecnologia)",
    
    # PETS
    "pet": "Pet Shop", "racao": "Pet Shop", "cachorro": "Pet Shop", 
    "gato": "Pet Shop", "banho e tosa": "Banho e Tosa", "veterinario": "Veterinário(a)",
    
    # MANUTENÇÃO E REFORMA
    "vazamento": "Encanador", "cano": "Encanador", "torneira": "Encanador",
    "curto": "Eletricista", "luz": "Eletricista", "chuveiro": "Eletricista",
    "pintar": "Pintor", "pintura": "Pintor", "parede": "Pintor",
    "reforma": "Pedreiro", "obra": "Pedreiro", "tijolo": "Pedreiro",
    "gesso": "Gesseiro", "drywall": "Gesseiro",
    "chave": "Chaveiro", "fechadura": "Chaveiro",
    
    # AUTOMOTIVO
    "carro": "Mecânico de Autos", "motor": "Mecânico de Autos", "oficina": "Mecânico de Autos",
    "pneu": "Borracheiro", "estepe": "Borracheiro", "furou": "Borracheiro",
    "guincho": "Guincho 24h", "reboque": "Guincho 24h",
    "lavajato": "Lava Jato", "lavagem": "Estética Automotiva",
    
    # SERVIÇOS GERAIS
    "frete": "Freteiro", "mudanca": "Freteiro", "carreto": "Carreto",
    "montar": "Montador de Móveis", "armario": "Montador de Móveis",
    "faxina": "Diarista / Faxineira", "limpeza": "Diarista / Faxineira",
    "jardim": "Jardineiro", "grama": "Jardineiro", "poda": "Jardineiro",
}


# ==============================================================================
# 3. CONEXÃO COM FIREBASE (SEGURO)
# ==============================================================================

@st.cache_resource
def inicializar_firebase() -> firebase_admin.App:
    """
    Inicializa conexão segura com Firebase usando credenciais em Base64
    
    Returns:
        firebase_admin.App: Instância do app Firebase
        
    Raises:
        Exception: Se credenciais não forem encontradas ou inválidas
    """
    if not firebase_admin._apps:
        try:
            # Valida presença da chave secreta
            if "FIREBASE_BASE64" not in st.secrets:
                st.error("🔑 Chave de segurança FIREBASE_BASE64 não configurada!")
                st.stop()
            
            # Decodifica credenciais do Firebase
            base64_key = st.secrets["FIREBASE_BASE64"]
            decoded_json = base64.b64decode(base64_key).decode("utf-8")
            cred_dict = json.loads(decoded_json)
            
            # Inicializa Firebase
            cred = credentials.Certificate(cred_dict)
            return firebase_admin.initialize_app(cred)
            
        except Exception as e:
            st.error(f"❌ Erro ao conectar Firebase: {e}")
            st.stop()
    
    return firebase_admin.get_app()


# Inicialização global do Firebase
app_engine = inicializar_firebase()
db = firestore.client()


# ==============================================================================
# 4. FUNÇÕES UTILITÁRIAS
# ==============================================================================

def converter_img_b64(file) -> Optional[str]:
    """
    Converte arquivo de imagem para Base64
    
    Args:
        file: Arquivo uploadado via Streamlit
        
    Returns:
        str: String Base64 da imagem ou None se falhar
    """
    if file is None:
        return None
    
    try:
        file.seek(0)  # Reset do ponteiro do arquivo
        return base64.b64encode(file.read()).decode()
    except Exception as e:
        st.warning(f"Erro ao processar imagem: {e}")
        return None


def normalizar_texto(texto: str) -> str:
    """
    Remove acentos e normaliza texto para busca
    
    Args:
        texto: Texto a ser normalizado
        
    Returns:
        str: Texto normalizado em lowercase sem acentos
    """
    if not texto:
        return ""
    
    # Remove acentos (NFD decomposition)
    nfd = unicodedata.normalize('NFD', str(texto))
    texto_sem_acento = ''.join(
        char for char in nfd 
        if unicodedata.category(char) != 'Mn'
    )
    
    return texto_sem_acento.lower().strip()


def validar_telefone(telefone: str) -> bool:
    """
    Valida formato de telefone brasileiro
    
    Args:
        telefone: Número de telefone
        
    Returns:
        bool: True se válido, False caso contrário
    """
    # Remove caracteres não numéricos
    numeros = re.sub(r'\D', '', telefone)
    
    # Valida: deve ter 10 ou 11 dígitos (com DDD)
    return len(numeros) in [10, 11]


def sanitizar_input(texto: str) -> str:
    """
    Remove caracteres perigosos para prevenir XSS e injeção
    
    Args:
        texto: Texto a ser sanitizado
        
    Returns:
        str: Texto limpo e seguro
    """
    if not texto:
        return ""
    
    # Remove tags HTML
    texto = re.sub(r'<[^>]+>', '', texto)
    
    # Remove javascript:
    texto = re.sub(r'javascript:', '', texto, flags=re.IGNORECASE)
    
    # Remove SQL injection patterns
    texto = re.sub(r'(DROP|DELETE|INSERT|UPDATE|SELECT)\s+(TABLE|FROM|INTO)', 
                   '', texto, flags=re.IGNORECASE)
    
    return texto.strip()


# ==============================================================================
# 5. MOTOR DE IA - PROCESSAMENTO DE LINGUAGEM NATURAL
# ==============================================================================

def processar_ia_avancada(texto: str) -> str:
    """
    Processa entrada do usuário e identifica categoria usando IA
    
    Args:
        texto: Termo de busca do usuário
        
    Returns:
        str: Categoria identificada ou "NAO_ENCONTRADO"
    """
    if not texto:
        return "NAO_ENCONTRADO"
    
    texto_normalizado = normalizar_texto(texto)
    
    # 1. Busca exata no dicionário de conceitos
    for palavra_chave, categoria in CONCEITOS_EXPANDIDOS.items():
        chave_normalizada = normalizar_texto(palavra_chave)
        
        # Usa word boundary para evitar falsos positivos
        if re.search(rf"\b{chave_normalizada}\b", texto_normalizado):
            return categoria
    
    # 2. Verifica se usuário digitou categoria oficial diretamente
    for categoria in CATEGORIAS_OFICIAIS:
        if normalizar_texto(categoria) in texto_normalizado:
            return categoria
    
    # 3. Nenhuma correspondência encontrada
    return "NAO_ENCONTRADO"


# ==============================================================================
# 6. SISTEMA DE GEOLOCALIZAÇÃO
# ==============================================================================

def calcular_distancia(lat1: float, lon1: float, 
                       lat2: float, lon2: float) -> float:
    """
    Calcula distância entre dois pontos usando fórmula de Haversine
    
    Args:
        lat1, lon1: Coordenadas do ponto 1
        lat2, lon2: Coordenadas do ponto 2
        
    Returns:
        float: Distância em quilômetros
    """
    try:
        # Valida entradas
        if None in [lat1, lon1, lat2, lon2]:
            return 999.0
        
        # Raio da Terra em km
        R = 6371
        
        # Converte para radianos
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        # Fórmula de Haversine
        a = (math.sin(dlat/2)**2 + 
             math.cos(math.radians(lat1)) * 
             math.cos(math.radians(lat2)) * 
             math.sin(dlon/2)**2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distancia = R * c
        
        return round(distancia, 1)
        
    except Exception as e:
        st.warning(f"Erro ao calcular distância: {e}")
        return 999.0


def obter_localizacao_usuario() -> Tuple[float, float]:
    """
    Obtém localização GPS do usuário
    
    Returns:
        Tuple[float, float]: (latitude, longitude)
    """
    try:
        loc = get_geolocation()
        
        if loc and 'coords' in loc:
            latitude = loc['coords']['latitude']
            longitude = loc['coords']['longitude']
            return latitude, longitude
        
    except Exception as e:
        st.warning(f"GPS não disponível: {e}")
    
    # Retorna localização padrão (São Paulo)
    return LAT_REF, LON_REF


# ==============================================================================
# 7. SISTEMA DE NOTIFICAÇÕES
# ==============================================================================

def enviar_notificacao_admin(nome: str, categoria: str, 
                             whatsapp: str) -> str:
    """
    Gera link de WhatsApp para notificar administrador sobre novo cadastro
    
    Args:
        nome: Nome do profissional
        categoria: Categoria/área de atuação
        whatsapp: Telefone do profissional
        
    Returns:
        str: URL do WhatsApp com mensagem pré-preenchida
    """
    mensagem = (
        f"🚀 *NOVO CADASTRO NO GERALJÁ*\n\n"
        f"👤 *Nome:* {nome}\n"
        f"🛠️ *Área:* {categoria}\n"
        f"📱 *Telefone:* {whatsapp}\n\n"
        f"Acesse o Painel Admin para aprovar!"
    )
    
    # Codifica mensagem para URL
    mensagem_encoded = quote(mensagem)
    
    return f"https://wa.me/{ZAP_ADMIN}?text={mensagem_encoded}"


# ==============================================================================
# 8. SISTEMA DE SEGURANÇA E AUDITORIA
# ==============================================================================

def verificar_seguranca_dados() -> List[str]:
    """
    Escaneia banco de dados em busca de vulnerabilidades e dados maliciosos
    
    Returns:
        List[str]: Lista de alertas de segurança
    """
    alertas = []
    
    try:
        # Padrões de ataque conhecidos
        padroes_perigosos = [
            r"<script>", r"javascript:", r"DROP\s+TABLE", 
            r"OR\s+1\s*=\s*1", r"UNION\s+SELECT", r"<iframe"
        ]
        
        # Escaneia todos os profissionais
        profissionais = db.collection("profissionais").stream()
        
        for doc in profissionais:
            dados = doc.to_dict()
            doc_id = doc.id
            
            # Concatena campos de texto para análise
            conteudo_texto = " ".join([
                str(dados.get('nome', '')),
                str(dados.get('descricao', '')),
                str(dados.get('link_catalogo', ''))
            ])
            
            # Verifica cada padrão perigoso
            for padrao in padroes_perigosos:
                if re.search(padrao, conteudo_texto, re.IGNORECASE):
                    alerta = f"⚠️ AMEAÇA DETECTADA: ID {doc_id} - Padrão: {padrao}"
                    alertas.append(alerta)
                    
                    # Bloqueia profissional preventivamente
                    db.collection("profissionais").document(doc_id).update({
                        "aprovado": False,
                        "bloqueado_seguranca": True
                    })
        
        return alertas if alertas else ["✅ Sistema seguro - Nenhuma ameaça detectada"]
        
    except Exception as e:
        return [f"❌ Erro no scanner: {e}"]


def corrigir_inconsistencias_dados() -> List[str]:
    """
    Varre e corrige dados inconsistentes no banco
    
    Returns:
        List[str]: Log das correções realizadas
    """
    log_correcoes = []
    
    try:
        profissionais = db.collection("profissionais").stream()
        
        for doc in profissionais:
            dados = doc.to_dict()
            doc_id = doc.id
            correcoes = {}
            
            # 1. Validação de categoria
            if not dados.get('area') or dados.get('area') not in CATEGORIAS_OFICIAIS:
                correcoes['area'] = "Ajudante Geral"
            
            # 2. Descrição obrigatória
            if not dados.get('descricao'):
                correcoes['descricao'] = "Profissional parceiro do GeralJá Brasil."
            
            # 3. Saldo não pode ser nulo
            if dados.get('saldo') is None:
                correcoes['saldo'] = 0
            
            # 4. Coordenadas padrão se ausentes
            if dados.get('lat') is None or dados.get('lon') is None:
                correcoes['lat'] = LAT_REF
                correcoes['lon'] = LON_REF
            
            # 5. Inicializa contador de cliques
            if dados.get('cliques') is None:
                correcoes['cliques'] = 0
            
            # Aplica correções se necessário
            if correcoes:
                db.collection("profissionais").document(doc_id).update(correcoes)
                log_correcoes.append(f"✅ Corrigido: {doc_id}")
        
        return log_correcoes if log_correcoes else ["✅ Dados íntegros"]
        
    except Exception as e:
        return [f"❌ Erro: {e}"]


# ==============================================================================
# 9. DESIGN SYSTEM - CSS CUSTOMIZADO
# ==============================================================================

def aplicar_design_system():
    """Aplica CSS personalizado para interface moderna"""
    
    st.markdown("""
    <style>
        /* Importação de fonte */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
        
        /* Reset e Base */
        * {
            font-family: 'Inter', sans-serif;
        }
        
        .stApp {
            background-color: #F8FAFC;
        }
        
        /* Header Principal */
        .header-container {
            background: linear-gradient(135deg, #0047AB 0%, #0059D1 100%);
            padding: 40px 20px;
            border-radius: 0 0 50px 50px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,71,171,0.2);
            margin-bottom: 30px;
            position: relative;
            overflow: hidden;
        }
        
        .header-container::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: pulse 15s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
        
        .logo-azul {
            color: #FFFFFF;
            font-weight: 900;
            font-size: 50px;
            letter-spacing: -2px;
            text-shadow: 0 4px 6px rgba(0,0,0,0.2);
            position: relative;
            z-index: 1;
        }
        
        .logo-laranja {
            color: #FF8C00;
            font-weight: 900;
            font-size: 50px;
            letter-spacing: -2px;
            text-shadow: 0 4px 6px rgba(0,0,0,0.2);
            position: relative;
            z-index: 1;
        }
        
        .subtitle {
            color: rgba(255,255,255,0.9);
            font-weight: 700;
            font-size: 14px;
            letter-spacing: 2px;
            margin-top: 10px;
            position: relative;
            z-index: 1;
        }
        
        /* Cards de Profissionais */
        .pro-card {
            background: white;
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 20px;
            border-left: 8px solid #0047AB;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            transition: all 0.3s ease;
        }
        
        .pro-card:hover {
            box-shadow: 0 8px 24px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }
        
        .pro-card-elite {
            border-left: 8px solid #FFD700;
            background: linear-gradient(135deg, #FFFEF5 0%, #FFFFFF 100%);
        }
        
        /* Botões */
        .btn-whatsapp {
            background: linear-gradient(135deg, #25D366 0%, #20BA5A 100%);
            color: white !important;
            padding: 15px 25px;
            border-radius: 15px;
            text-decoration: none;
            font-weight: 800;
            font-size: 16px;
            display: block;
            text-align: center;
            margin-top: 15px;
            box-shadow: 0 4px 12px rgba(37,211,102,0.3);
            transition: all 0.3s ease;
        }
        
        .btn-whatsapp:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(37,211,102,0.4);
        }
        
        /* Badges */
        .badge-verificado {
            background: #1DA1F2;
            color: white;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 700;
            margin-left: 8px;
        }
        
        .badge-elite {
            background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
            color: #000;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 700;
            margin-left: 8px;
        }
        
        /* Métricas */
        .metric-card {
            background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
            color: white;
            padding: 25px;
            border-radius: 20px;
            text-align: center;
            border-bottom: 5px solid #FF8C00;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        .metric-value {
            font-size: 32px;
            font-weight: 900;
            margin: 10px 0;
        }
        
        .metric-label {
            font-size: 14px;
            opacity: 0.8;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* Status Indicators */
        .status-aberto {
            color: #22C55E;
            font-weight: 700;
        }
        
        .status-fechado {
            color: #EF4444;
            font-weight: 700;
        }
        
        /* Formulários */
        .stTextInput > div > div > input {
            border-radius: 12px;
            border: 2px solid #E2E8F0;
            padding: 12px;
            transition: all 0.3s ease;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #0047AB;
            box-shadow: 0 0 0 3px rgba(0,71,171,0.1);
        }
        
        /* Remover elementos do Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Responsividade */
        @media (max-width: 768px) {
            .logo-azul, .logo-laranja {
                font-size: 36px;
            }
            
            .pro-card {
                padding: 15px;
            }
        }
    </style>
    """, unsafe_allow_html=True)


# ==============================================================================
# 10. COMPONENTES UI REUTILIZÁVEIS
# ==============================================================================

def renderizar_header():
    """Renderiza header principal da aplicação"""
    st.markdown(
        '<div class="header-container">'
        '<span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span><br>'
        '<div class="subtitle">BRASIL ELITE EDITION</div>'
        '</div>',
        unsafe_allow_html=True
    )


def renderizar_card_profissional(profissional: Dict, distancia: float):
    """
    Renderiza card de profissional na busca
    
    Args:
        profissional: Dados do profissional
        distancia: Distância em km do usuário
    """
    is_elite = profissional.get('verificado') and profissional.get('saldo', 0) > 0
    card_class = "pro-card-elite" if is_elite else "pro-card"
    
    # Container do card
    st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
    
    # Header com distância
    col_dist, col_status = st.columns([3, 1])
    with col_dist:
        st.caption(f"📍 {distancia:.1f} km de você")
    with col_status:
        if is_elite:
            st.markdown('<span class="badge-elite">⭐ DESTAQUE</span>', unsafe_allow_html=True)
    
    # Foto e informações
    col_img, col_info = st.columns([1, 4])
    
    with col_img:
        foto_url = profissional.get('foto_url', 'https://via.placeholder.com/150')
        st.image(foto_url, width=100)
    
    with col_info:
        # Nome e verificação
        nome = profissional.get('nome', 'Profissional').upper()
        if profissional.get('verificado'):
            st.markdown(f"**{nome}** <span class='badge-verificado'>✓ Verificado</span>", 
                       unsafe_allow_html=True)
        else:
            st.markdown(f"**{nome}**")
        
        # Área e descrição
        st.caption(f"🛠️ {profissional.get('area', '')}")
        st.write(profissional.get('descricao', '')[:150] + "...")
        
        # Status de horário (se for comércio)
        if profissional.get('tipo') == "🏢 Comércio/Loja":
            fuso = pytz.timezone('America/Sao_Paulo')
            hora_atual = datetime.datetime.now(fuso).strftime('%H:%M')
            h_abre = profissional.get('h_abre', '08:00')
            h_fecha = profissional.get('h_fecha', '18:00')
            
            if h_abre <= hora_atual <= h_fecha:
                st.markdown("🟢 <span class='status-aberto'>ABERTO AGORA</span>", 
                           unsafe_allow_html=True)
            else:
                st.markdown("🔴 <span class='status-fechado'>FECHADO</span>", 
                           unsafe_allow_html=True)
    
    # Portfólio (se existir)
    if profissional.get('portfolio_imgs'):
        st.markdown("**📸 Portfólio:**")
        cols = st.columns(3)
        for i, img_b64 in enumerate(profissional.get('portfolio_imgs')[:3]):
            with cols[i]:
                st.image(f"data:image/png;base64,{img_b64}", use_container_width=True)
    
    # Botão WhatsApp
    telefone_id = profissional.get('id', '')
    numero_limpo = re.sub(r'\D', '', str(telefone_id))
    if not numero_limpo.startswith('55'):
        numero_limpo = f"55{numero_limpo}"
    
    mensagem = quote(f"Olá {profissional.get('nome')}, vi seu perfil no GeralJá!")
    link_whatsapp = f"https://wa.me/{numero_limpo}?text={mensagem}"
    
    st.markdown(
        f'<a href="{link_whatsapp}" target="_blank" class="btn-whatsapp">'
        f'💬 FALAR COM {profissional.get("nome", "PROFISSIONAL").split()[0].upper()}'
        f'</a>',
        unsafe_allow_html=True
    )
    
    st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# 11. APLICAÇÃO PRINCIPAL
# ==============================================================================

def main():
    """Função principal da aplicação"""
    
    # Aplicar design system
    aplicar_design_system()
    
    # Renderizar header
    renderizar_header()
    
    # Configuração de abas
    comando_secreto = st.sidebar.text_input("🔐 Comando Secreto", type="password")
    
    abas_base = ["🔍 BUSCAR", "🚀 CADASTRAR", "👤 MEU PERFIL", "👑 ADMIN", "⭐ FEEDBACK"]
    
    # Adiciona aba financeira se comando correto
    if comando_secreto == "abracadabra":
        abas_base.append("📊 FINANCEIRO")
    
    abas = st.tabs(abas_base)
    
    # =========================================================================
    # ABA 1: BUSCA
    # =========================================================================
    with abas[0]:
        st.markdown("### 🏙️ O que você precisa?")
        
        # Geolocalização
        with st.expander("📍 Sua Localização (GPS)", expanded=False):
            minha_lat, minha_lon = obter_localizacao_usuario()
            
            if minha_lat == LAT_REF and minha_lon == LON_REF:
                st.warning("GPS não disponível. Usando localização padrão (São Paulo).")
            else:
                st.success("✅ Localização detectada com sucesso!")
        
        # Campos de busca
        col_busca, col_raio = st.columns([3, 1])
        
        with col_busca:
            termo_busca = st.text_input(
                "Buscar por:",
                placeholder="Ex: 'Cano estourado', 'Pizza', 'Cortar cabelo'",
                key="busca_principal"
            )
        
        with col_raio:
            raio_km = st.select_slider(
                "Raio (km)",
                options=[1, 3, 5, 10, 20, 50, 100, 500, 2000],
                value=10
            )
        
        # Processamento da busca
        if termo_busca:
            # IA identifica categoria
            categoria_ia = processar_ia_avancada(termo_busca)
            
            if categoria_ia == "NAO_ENCONTRADO":
                st.warning(f"🤔 Não encontramos '{termo_busca}' em nossas categorias.")
                st.info("💡 Tente termos como: pizza, encanador, cortar cabelo, mecânico...")
                
            else:
                st.info(f"✨ Buscando **{categoria_ia}** próximo a você...")
                
                # Busca no Firebase
                try:
                    profissionais_query = (
                        db.collection("profissionais")
                        .where("area", "==", categoria_ia)
                        .where("aprovado", "==", True)
                        .stream()
                    )
                    
                    resultados = []
                    
                    for doc in profissionais_query:
                        prof = doc.to_dict()
                        prof['id'] = doc.id
                        
                        # Calcula distância
                        distancia = calcular_distancia(
                            minha_lat, minha_lon,
                            prof.get('lat', LAT_REF),
                            prof.get('lon', LON_REF)
                        )
                        
                        # Filtra por raio
                        if distancia <= raio_km:
                            prof['distancia'] = distancia
                            
                            # Calcula score de ranking
                            score = 0
                            score += 500 if prof.get('verificado', False) else 0
                            score += prof.get('saldo', 0) * 10
                            score += prof.get('rating', 5) * 20
                            
                            prof['score'] = score
                            resultados.append(prof)
                    
                    # Ordena: maior score primeiro, depois menor distância
                    resultados.sort(key=lambda x: (-x['score'], x['distancia']))
                    
                    # Renderiza resultados
                    if not resultados:
                        st.warning(f"😕 Nenhum **{categoria_ia}** encontrado nesta região.")
                        st.markdown("""
                        <div style="background: #FFF4E5; padding: 20px; border-radius: 15px; 
                                    border-left: 5px solid #FF8C00; margin-top: 20px;">
                            <h4 style="color: #856404;">📣 Ajude a expandir o GeralJá!</h4>
                            <p style="color: #856404;">
                                Compartilhe com profissionais da sua região.
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        link_compartilhar = (
                            "https://wa.me/?text="
                            "Ei!%20Cadastre-se%20no%20GeralJá%20e%20receba%20clientes:%20"
                            "https://geralja.com.br"
                        )
                        
                        st.link_button(
                            "📲 COMPARTILHAR NO WHATSAPP",
                            link_compartilhar,
                            use_container_width=True
                        )
                    
                    else:
                        st.success(f"✅ Encontramos {len(resultados)} profissionais!")
                        
                        # Renderiza cards
                        for prof in resultados:
                            renderizar_card_profissional(prof, prof['distancia'])
                            
                            # Registra visualização
                            if prof.get('saldo', 0) > 0:
                                db.collection("profissionais").document(prof['id']).update({
                                    "cliques": prof.get('cliques', 0) + 1
                                })
                
                except Exception as e:
                    st.error(f"❌ Erro na busca: {e}")
    
    # =========================================================================
    # ABA 2: CADASTRO
    # =========================================================================
    with abas[1]:
        st.markdown("### 🚀 Cadastro de Profissional")
        st.info("📝 Preencha os dados para entrar no ecossistema GeralJá")
        
        with st.form("form_cadastro", clear_on_submit=False):
            col1, col2 = st.columns(2)
            
            with col1:
                nome = st.text_input(
                    "Nome Profissional ou Loja *",
                    placeholder="Ex: João Silva - Encanador"
                )
                
            with col2:
                whatsapp = st.text_input(
                    "WhatsApp (com DDD) *",
                    placeholder="Ex: 11987654321"
                )
            
            # Categoria
            categoria = st.selectbox(
                "Área de Atuação *",
                options=CATEGORIAS_OFICIAIS,
                index=0
            )
            
            # Tipo de perfil
            tipo_perfil = st.radio(
                "Tipo de Perfil *",
                options=["👤 Pessoa Física (Autônomo)", "🏢 Comércio/Loja"],
                horizontal=True
            )
            
            # Descrição
            descricao = st.text_area(
                "Descrição do Serviço *",
                placeholder="Descreva sua experiência, serviços oferecidos e diferenciais...",
                max_chars=500
            )
            
            # Link catálogo
            link_catalogo = st.text_input(
                "Link do Catálogo/Instagram (opcional)",
                placeholder="https://instagram.com/seuperfil"
            )
            
            # Horários (se for comércio)
            if tipo_perfil == "🏢 Comércio/Loja":
                st.markdown("**⏰ Horário de Funcionamento**")
                col_h1, col_h2 = st.columns(2)
                
                with col_h1:
                    hora_abre = st.text_input("Abre às:", value="08:00")
                    
                with col_h2:
                    hora_fecha = st.text_input("Fecha às:", value="18:00")
            else:
                hora_abre = "00:00"
                hora_fecha = "23:59"
            
            # Foto de perfil
            foto_perfil = st.file_uploader(
                "📸 Foto de Perfil",
                type=['jpg', 'png', 'jpeg'],
                help="Fotos profissionais aumentam credibilidade"
            )
            
            # Portfolio
            portfolio = st.file_uploader(
                "🖼️ Portfólio (até 3 fotos)",
                type=['jpg', 'png', 'jpeg'],
                accept_multiple_files=True,
                help="Mostre seus melhores trabalhos"
            )
            
            # Senha
            col_s1, col_s2 = st.columns(2)
            
            with col_s1:
                senha = st.text_input("Senha *", type="password")
                
            with col_s2:
                confirma_senha = st.text_input("Confirmar Senha *", type="password")
            
            # Termos
            aceite_termos = st.checkbox(
                "Li e aceito os termos de uso e política de privacidade *",
                value=False
            )
            
            # Botão de envio
            submitted = st.form_submit_button(
                "🚀 CRIAR MINHA CONTA",
                use_container_width=True
            )
            
            # Processamento do formulário
            if submitted:
                # Validações
                erros = []
                
                if not nome or len(nome) < 3:
                    erros.append("❌ Nome deve ter pelo menos 3 caracteres")
                
                if not whatsapp or not validar_telefone(whatsapp):
                    erros.append("❌ WhatsApp inválido (use apenas números com DDD)")
                
                if not descricao or len(descricao) < 20:
                    erros.append("❌ Descrição deve ter pelo menos 20 caracteres")
                
                if not senha or len(senha) < 6:
                    erros.append("❌ Senha deve ter pelo menos 6 caracteres")
                
                if senha != confirma_senha:
                    erros.append("❌ Senhas não conferem")
                
                if not aceite_termos:
                    erros.append("❌ É necessário aceitar os termos")
                
                # Sanitização de inputs
                nome_limpo = sanitizar_input(nome)
                descricao_limpa = sanitizar_input(descricao)
                link_catalogo_limpo = sanitizar_input(link_catalogo)
                
                # Se houver erros, exibe
                if erros:
                    for erro in erros:
                        st.error(erro)
                
                else:
                    try:
                        # Prepara dados
                        whatsapp_limpo = re.sub(r'\D', '', whatsapp)
                        
                        # Verifica se já existe
                        doc_existente = db.collection("profissionais").document(whatsapp_limpo).get()
                        
                        if doc_existente.exists:
                            st.error("❌ Este WhatsApp já está cadastrado!")
                        
                        else:
                            # Converte fotos para base64
                            foto_b64 = None
                            if foto_perfil:
                                foto_b64 = f"data:image/png;base64,{converter_img_b64(foto_perfil)}"
                            
                            portfolio_b64 = []
                            if portfolio:
                                for img in portfolio[:3]:
                                    img_b64 = converter_img_b64(img)
                                    if img_b64:
                                        portfolio_b64.append(img_b64)
                            
                            # Obtém localização
                            lat, lon = obter_localizacao_usuario()
                            
                            # Monta documento
                            novo_profissional = {
                                "nome": nome_limpo,
                                "area": categoria,
                                "descricao": descricao_limpa,
                                "tipo": tipo_perfil,
                                "link_catalogo": link_catalogo_limpo,
                                "h_abre": hora_abre,
                                "h_fecha": hora_fecha,
                                "foto_url": foto_b64,
                                "portfolio_imgs": portfolio_b64,
                                "senha": senha,  # ⚠️ Em produção, usar hash (bcrypt)
                                "lat": lat,
                                "lon": lon,
                                "saldo": BONUS_WELCOME,
                                "cliques": 0,
                                "rating": 5.0,
                                "verificado": False,
                                "aprovado": False,
                                "data_cadastro": datetime.datetime.now().isoformat()
                            }
                            
                            # Salva no Firebase
                            db.collection("profissionais").document(whatsapp_limpo).set(
                                novo_profissional
                            )
                            
                            # Sucesso!
                            st.success("✅ Cadastro realizado com sucesso!")
                            st.balloons()
                            
                            # Notifica admin
                            link_notificacao = enviar_notificacao_admin(
                                nome_limpo, categoria, whatsapp_limpo
                            )
                            
                            st.info(
                                "📩 Seu cadastro está em análise. "
                                "Você receberá aprovação em até 24h!"
                            )
                            
                            # Limpa formulário
                            time.sleep(2)
                            st.rerun()
                    
                    except Exception as e:
                        st.error(f"❌ Erro ao cadastrar: {e}")
    
    # =========================================================================
    # ABA 3: MEU PERFIL
    # =========================================================================
    with abas[2]:
        # Sistema de autenticação
        if 'autenticado' not in st.session_state:
            st.session_state.autenticado = False
        
        if not st.session_state.autenticado:
            st.markdown("### 🔐 Acesso ao Painel")
            
            col_login1, col_login2 = st.columns(2)
            
            with col_login1:
                login_whatsapp = st.text_input(
                    "WhatsApp",
                    placeholder="11987654321",
                    key="login_wpp"
                )
            
            with col_login2:
                login_senha = st.text_input(
                    "Senha",
                    type="password",
                    key="login_pwd"
                )
            
            if st.button("ENTRAR NO PAINEL", use_container_width=True):
                try:
                    whatsapp_limpo = re.sub(r'\D', '', login_whatsapp)
                    usuario = db.collection("profissionais").document(whatsapp_limpo).get()
                    
                    if usuario.exists:
                        dados_usuario = usuario.to_dict()
                        
                        # Verifica senha
                        if dados_usuario.get('senha') == login_senha:
                            st.session_state.autenticado = True
                            st.session_state.user_id = whatsapp_limpo
                            st.success("✅ Login realizado!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ Senha incorreta!")
                    else:
                        st.error("❌ WhatsApp não cadastrado!")
                
                except Exception as e:
                    st.error(f"❌ Erro no login: {e}")
        
        else:
            # Usuário autenticado - mostra painel
            try:
                doc_ref = db.collection("profissionais").document(st.session_state.user_id)
                dados = doc_ref.get().to_dict()
                
                # Header do painel
                st.markdown(f"### 👋 Olá, {dados.get('nome', 'Parceiro')}!")
                
                # Métricas
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                
                with col_m1:
                    st.metric("💰 Saldo", f"{dados.get('saldo', 0)} moedas")
                
                with col_m2:
                    st.metric("👁️ Visualizações", dados.get('cliques', 0))
                
                with col_m3:
                    st.metric("⭐ Avaliação", f"{dados.get('rating', 5.0):.1f}")
                
                with col_m4:
                    status = "🟢 ATIVO" if dados.get('aprovado') else "🟡 PENDENTE"
                    st.metric("📊 Status", status)
                
                st.divider()
                
                # Atualizar GPS
                if st.button("📍 ATUALIZAR LOCALIZAÇÃO GPS", use_container_width=True):
                    lat, lon = obter_localizacao_usuario()
                    
                    doc_ref.update({
                        "lat": lat,
                        "lon": lon,
                        "ultima_atualizacao_gps": datetime.datetime.now().isoformat()
                    })
                    
                    st.success("✅ Localização atualizada!")
                    time.sleep(1)
                    st.rerun()
                
                st.divider()
                
                # Compra de moedas
                with st.expander("💎 COMPRAR MOEDAS", expanded=False):
                    st.markdown(f"**Chave PIX:** `{PIX_OFICIAL}`")
                    st.caption("Após fazer o PIX, envie o comprovante:")
                    
                    col_p1, col_p2, col_p3 = st.columns(3)
                    
                    with col_p1:
                        st.info("**10 Moedas**\nR$ 10,00")
                    
                    with col_p2:
                        st.info("**50 Moedas**\nR$ 40,00")
                    
                    with col_p3:
                        st.info("**100 Moedas**\nR$ 70,00")
                    
                    mensagem_pix = quote(
                        f"Olá! Fiz um PIX para compra de moedas. "
                        f"WhatsApp: {st.session_state.user_id}"
                    )
                    
                    st.link_button(
                        "📲 ENVIAR COMPROVANTE",
                        f"https://wa.me/{ZAP_ADMIN}?text={mensagem_pix}",
                        use_container_width=True
                    )
                
                st.divider()
                
                # Editar perfil
                with st.expander("✏️ EDITAR PERFIL", expanded=True):
                    with st.form("form_editar_perfil"):
                        edit_nome = st.text_input(
                            "Nome",
                            value=dados.get('nome', '')
                        )
                        
                        # Categoria atual
                        try:
                            idx_cat = CATEGORIAS_OFICIAIS.index(dados.get('area'))
                        except:
                            idx_cat = 0
                        
                        edit_area = st.selectbox(
                            "Área de Atuação",
                            options=CATEGORIAS_OFICIAIS,
                            index=idx_cat
                        )
                        
                        edit_desc = st.text_area(
                            "Descrição",
                            value=dados.get('descricao', ''),
                            max_chars=500
                        )
                        
                        edit_link = st.text_input(
                            "Link Catálogo/Instagram",
                            value=dados.get('link_catalogo', '')
                        )
                        
                        # Horários
                        col_h1, col_h2 = st.columns(2)
                        
                        with col_h1:
                            edit_abre = st.text_input(
                                "Abre às:",
                                value=dados.get('h_abre', '08:00')
                            )
                        
                        with col_h2:
                            edit_fecha = st.text_input(
                                "Fecha às:",
                                value=dados.get('h_fecha', '18:00')
                            )
                        
                        # Fotos
                        edit_foto = st.file_uploader(
                            "Nova Foto de Perfil",
                            type=['jpg', 'png', 'jpeg']
                        )
                        
                        edit_portfolio = st.file_uploader(
                            "Novo Portfólio (até 3 fotos)",
                            type=['jpg', 'png', 'jpeg'],
                            accept_multiple_files=True
                        )
                        
                        # Botão salvar
                        if st.form_submit_button("💾 SALVAR ALTERAÇÕES", use_container_width=True):
                            try:
                                # Prepara atualizações
                                atualizacoes = {
                                    "nome": sanitizar_input(edit_nome),
                                    "area": edit_area,
                                    "descricao": sanitizar_input(edit_desc),
                                    "link_catalogo": sanitizar_input(edit_link),
                                    "h_abre": edit_abre,
                                    "h_fecha": edit_fecha,
                                    "ultima_atualizacao": datetime.datetime.now().isoformat()
                                }
                                
                                # Foto de perfil
                                if edit_foto:
                                    foto_b64 = converter_img_b64(edit_foto)
                                    if foto_b64:
                                        atualizacoes["foto_url"] = f"data:image/png;base64,{foto_b64}"
                                
                                # Portfolio
                                if edit_portfolio:
                                    portfolio_b64 = []
                                    for img in edit_portfolio[:3]:
                                        img_b64 = converter_img_b64(img)
                                        if img_b64:
                                            portfolio_b64.append(f"data:image/png;base64,{img_b64}")
                                    
                                    atualizacoes["portfolio_imgs"] = portfolio_b64
                                
                                # Salva
                                doc_ref.update(atualizacoes)
                                
                                st.success("✅ Perfil atualizado com sucesso!")
                                time.sleep(1)
                                st.rerun()
                            
                            except Exception as e:
                                st.error(f"❌ Erro ao atualizar: {e}")
                
                # Logout
                st.divider()
                if st.button("🚪 SAIR DA CONTA", use_container_width=True):
                    st.session_state.autenticado = False
                    st.session_state.user_id = None
                    st.rerun()
            
            except Exception as e:
                st.error(f"❌ Erro ao carregar perfil: {e}")
    
    # =========================================================================
    # ABA 4: ADMIN
    # =========================================================================
    with abas[3]:
        st.markdown("### 👑 Painel Administrativo")
        
        # Autenticação admin
        if 'admin_autenticado' not in st.session_state:
            st.session_state.admin_autenticado = False
        
        if not st.session_state.admin_autenticado:
            senha_admin = st.text_input(
                "🔑 Senha de Administrador",
                type="password",
                key="admin_pwd"
            )
            
            if st.button("ACESSAR PAINEL ADMIN"):
                if senha_admin == CHAVE_ADMIN:
                    st.session_state.admin_autenticado = True
                    st.success("✅ Acesso concedido!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ Senha incorreta!")
        
        else:
            # Admin autenticado
            st.success("✅ Modo Administrador Ativo")
            
            # Estatísticas gerais
            st.markdown("#### 📊 Estatísticas do Sistema")
            
            try:
                # Conta profissionais
                total_profs = len(list(db.collection("profissionais").stream()))
                profs_aprovados = len(list(
                    db.collection("profissionais")
                    .where("aprovado", "==", True)
                    .stream()
                ))
                profs_pendentes = total_profs - profs_aprovados
                
                col_s1, col_s2, col_s3 = st.columns(3)
                
                with col_s1:
                    st.metric("👥 Total Profissionais", total_profs)
                
                with col_s2:
                    st.metric("✅ Aprovados", profs_aprovados)
                
                with col_s3:
                    st.metric("⏳ Pendentes", profs_pendentes)
                
                st.divider()
                
                # Ferramentas de segurança
                st.markdown("#### 🛡️ Segurança do Sistema")
                
                col_seg1, col_seg2 = st.columns(2)
                
                with col_seg1:
                    if st.button("🔍 ESCANEAR VULNERABILIDADES", use_container_width=True):
                        with st.spinner("Escaneando..."):
                            alertas = verificar_seguranca_dados()
                            
                            for alerta in alertas:
                                if "✅" in alerta:
                                    st.success(alerta)
                                elif "⚠️" in alerta:
                                    st.warning(alerta)
                                else:
                                    st.error(alerta)
                
                with col_seg2:
                    if st.button("🔧 CORRIGIR INCONSISTÊNCIAS", use_container_width=True):
                        with st.spinner("Corrigindo..."):
                            log = corrigir_inconsistencias_dados()
                            
                            for entrada in log:
                                if "✅" in entrada:
                                    st.success(entrada)
                                else:
                                    st.error(entrada)
                
                st.divider()
                
                # Gerenciamento de profissionais
                st.markdown("#### 👤 Gerenciar Profissionais")
                
                # Lista pendentes
                pendentes = db.collection("profissionais").where("aprovado", "==", False).stream()
                
                lista_pendentes = []
                for doc in pendentes:
                    prof = doc.to_dict()
                    prof['id'] = doc.id
                    lista_pendentes.append(prof)
                
                if not lista_pendentes:
                    st.info("✅ Nenhum cadastro pendente de aprovação")
                
                else:
                    st.warning(f"⏳ {len(lista_pendentes)} cadastros aguardando aprovação")
                    
                    for prof in lista_pendentes:
                        with st.expander(f"📋 {prof.get('nome')} - {prof.get('area')}"):
                            col_info, col_acao = st.columns([2, 1])
                            
                            with col_info:
                                st.write(f"**Nome:** {prof.get('nome')}")
                                st.write(f"**Área:** {prof.get('area')}")
                                st.write(f"**WhatsApp:** {prof.get('id')}")
                                st.write(f"**Descrição:** {prof.get('descricao')}")
                                
                                if prof.get('foto_url'):
                                    st.image(prof.get('foto_url'), width=150)
                            
                            with col_acao:
                                if st.button(f"✅ APROVAR", key=f"apr_{prof['id']}"):
                                    db.collection("profissionais").document(prof['id']).update({
                                        "aprovado": True
                                    })
                                    
                                    st.success("Aprovado!")
                                    time.sleep(1)
                                    st.rerun()
                                
                                if st.button(f"❌ REJEITAR", key=f"rej_{prof['id']}"):
                                    db.collection("profissionais").document(prof['id']).delete()
                                    
                                    st.warning("Rejeitado!")
                                    time.sleep(1)
                                    st.rerun()
                
                st.divider()
                
                # Gerenciar saldos
                st.markdown("#### 💰 Gerenciar Saldos")
                
                col_gs1, col_gs2, col_gs3 = st.columns(3)
                
                with col_gs1:
                    whatsapp_saldo = st.text_input(
                        "WhatsApp",
                        placeholder="11987654321"
                    )
                
                with col_gs2:
                    valor_saldo = st.number_input(
                        "Adicionar Moedas",
                        min_value=0,
                        value=10
                    )
                
                with col_gs3:
                    st.write("")  # Espaçamento
                    st.write("")
                    
                    if st.button("💎 CREDITAR", use_container_width=True):
                        if whatsapp_saldo:
                            try:
                                wpp_limpo = re.sub(r'\D', '', whatsapp_saldo)
                                doc = db.collection("profissionais").document(wpp_limpo)
                                dados_doc = doc.get().to_dict()
                                
                                if dados_doc:
                                    novo_saldo = dados_doc.get('saldo', 0) + valor_saldo
                                    doc.update({"saldo": novo_saldo})
                                    
                                    st.success(f"✅ {valor_saldo} moedas creditadas!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("❌ Profissional não encontrado!")
                            
                            except Exception as e:
                                st.error(f"❌ Erro: {e}")
                
                # Logout admin
                st.divider()
                if st.button("🚪 SAIR DO ADMIN", use_container_width=True):
                    st.session_state.admin_autenticado = False
                    st.rerun()
            
            except Exception as e:
                st.error(f"❌ Erro no painel admin: {e}")
    
    # =========================================================================
    # ABA 5: FEEDBACK
    # =========================================================================
    with abas[4]:
        st.markdown("### ⭐ Deixe seu Feedback")
        st.info("💬 Sua opinião é muito importante para melhorarmos!")
        
        with st.form("form_feedback"):
            feedback_nome = st.text_input("Seu Nome (opcional)")
            
            feedback_tipo = st.selectbox(
                "Tipo de Feedback",
                ["Sugestão", "Elogio", "Reclamação", "Bug/Erro", "Outro"]
            )
            
            feedback_mensagem = st.text_area(
                "Sua Mensagem",
                placeholder="Conte-nos o que você achou...",
                max_chars=1000
            )
            
            feedback_avaliacao = st.slider(
                "Avaliação Geral",
                min_value=1,
                max_value=5,
                value=5
            )
            
            if st.form_submit_button("📤 ENVIAR FEEDBACK", use_container_width=True):
                if not feedback_mensagem:
                    st.error("❌ Por favor, escreva uma mensagem!")
                
                else:
                    try:
                        # Salva feedback
                        feedback_doc = {
                            "nome": sanitizar_input(feedback_nome) if feedback_nome else "Anônimo",
                            "tipo": feedback_tipo,
                            "mensagem": sanitizar_input(feedback_mensagem),
                            "avaliacao": feedback_avaliacao,
                            "data": datetime.datetime.now().isoformat()
                        }
                        
                        db.collection("feedbacks").add(feedback_doc)
                        
                        st.success("✅ Feedback enviado com sucesso! Obrigado!")
                        st.balloons()
                        time.sleep(2)
                        st.rerun()
                    
                    except Exception as e:
                        st.error(f"❌ Erro ao enviar: {e}")
    
    # =========================================================================
    # ABA 6: FINANCEIRO (SECRETA)
    # =========================================================================
    if len(abas) > 5:
        with abas[5]:
            st.markdown("### 📊 Painel Financeiro")
            st.info("🔐 Área restrita - Comando secreto ativado")
            
            try:
                # Estatísticas financeiras
                profissionais = db.collection("profissionais").stream()
                
                total_saldo_sistema = 0
                total_cliques = 0
                
                for doc in profissionais:
                    dados = doc.to_dict()
                    total_saldo_sistema += dados.get('saldo', 0)
                    total_cliques += dados.get('cliques', 0)
                
                col_f1, col_f2, col_f3 = st.columns(3)
                
                with col_f1:
                    st.metric("💰 Moedas em Circulação", f"{total_saldo_sistema:,}")
                
                with col_f2:
                    st.metric("👁️ Total de Cliques", f"{total_cliques:,}")
                
                with col_f3:
                    receita_estimada = total_cliques * TAXA_CONTATO * 0.10  # 10 centavos por clique
                    st.metric("💵 Receita Estimada", f"R$ {receita_estimada:.2f}")
                
                st.divider()
                
                # Gráfico de engajamento (simples)
                st.markdown("#### 📈 Profissionais com Maior Engajamento")
                
                profs_list = []
                profs_stream = db.collection("profissionais").stream()
                
                for doc in profs_stream:
                    dados = doc.to_dict()
                    profs_list.append({
                        "Nome": dados.get('nome', 'N/A'),
                        "Área": dados.get('area', 'N/A'),
                        "Cliques": dados.get('cliques', 0),
                        "Saldo": dados.get('saldo', 0)
                    })
                
                if profs_list:
                    df = pd.DataFrame(profs_list)
                    df_sorted = df.sort_values('Cliques', ascending=False).head(10)
                    
                    st.dataframe(df_sorted, use_container_width=True)
                
            except Exception as e:
                st.error(f"❌ Erro ao carregar dados financeiros: {e}")


# ==============================================================================
# 12. EXECUÇÃO PRINCIPAL
# ==============================================================================

if __name__ == "__main__":
    main()
# ------------------------------------------------------------------------------
# 16. FINALIZADOR DE LAYOUT E RODAPÉ AUTOMÁTICO (O "VARREDOR 3.0")
# ------------------------------------------------------------------------------
def finalizar_e_alinhar_layout():
    """
    Versão 3.0: Além de alinhar, ele limpa erros de floats e garante
    que o rodapé fique sempre no final, independente do tamanho da tela.
    """
    # 1. Força uma quebra de qualquer elemento flutuante anterior
    st.markdown('<div style="clear: both;"></div>', unsafe_allow_html=True)
    st.write("---") 
    
    # 2. CSS Avançado para travar o layout
    estilo_blindado = """
        <style>
            /* Evita que o conteúdo cole nas bordas em celulares */
            @media (max-width: 640px) {
                .main .block-container {
                    padding-left: 1rem !important;
                    padding-right: 1rem !important;
                }
            }

            /* Estilização do Rodapé */
            .footer-container {
                text-align: center;
                padding: 40px 20px;
                background-color: #f9f9f9;
                border-radius: 20px 20px 0 0;
                margin-top: 50px;
                border-top: 1px solid #eee;
            }

            .footer-brand {
                color: #0047AB;
                font-weight: bold;
                font-size: 1.2rem;
                margin-bottom: 5px;
            }

            .footer-tagline {
                color: #666;
                font-size: 0.9rem;
                margin-bottom: 15px;
            }
        </style>
        
        <div class="footer-container">
            <div class="footer-brand">🎯 GeralJá</div>
            <div class="footer-tagline">Conectando o Grajaú com inteligência e tecnologia.</div>
            <div style="opacity: 0.5; font-size: 0.7rem;">
                v2.0 | © 2026 Sistema de Inteligência Local<br>
                Orgulhosamente desenvolvido para a comunidade.
            </div>
        </div>
    """
    st.markdown(estilo_blindado, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# EXECUÇÃO FINAL
# ------------------------------------------------------------------------------
try:
    finalizar_e_alinhar_layout()
except Exception as e:
    # Se até o varredor der erro, ele não derruba o site
    st.write("---")
    st.caption("GeralJá 2026")
# ------------------------------------------------------------------------------
