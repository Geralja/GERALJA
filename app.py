# ==============================================================================
# GERALJÁ: CRIANDO SOLUÇÕES - VERSÃO FINAL CORRIGIDA
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
import unicodedata
import pytz
from datetime import datetime

# 1. CONFIGURAÇÃO DE PÁGINA (Sempre o primeiro comando Streamlit)
st.set_page_config(
    page_title="GeralJá | Criando Soluções",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. CONFIGURAÇÕES GERAIS
LAT_PADRAO = -23.5505 
LON_PADRAO = -46.6333
CATEGORIAS_OFICIAIS = ["Pedreiro", "Encanador", "Eletricista", "Pintor", "Mecânico", "Alimentação", "Outros"]

# ==============================================================================
# 3. MOTOR MESTRE DE INTELIGÊNCIA - GERALJÁ (O CÉREBRO)
# ==============================================================================

class MotorGeralJa:
    @staticmethod
    def processar_intencao(termo):
        termo = termo.lower().strip()
        mapa = {
            "Pintor": ["pinta", "parede", "tinta", "grafite"],
            "Encanador": ["cano", "vazamento", "pia", "esgoto", "torneira"],
            "Eletricista": ["luz", "fio", "tomada", "disjuntor", "choque"],
            "Mecânico": ["carro", "motor", "pneu", "freio", "revisão"],
            "Alimentação": ["fome", "comida", "pizza", "lanche", "marmita"],
            "Pedreiro": ["obra", "reforma", "cimento", "tijolo", "telhado"]
        }
        for categoria, palavras in mapa.items():
            if any(p in termo for p in palavras):
                return categoria
        return termo.capitalize()

    @staticmethod
    def calcular_distancia(lat1, lon1, lat2, lon2):
        try:
            if not all([lat1, lon1, lat2, lon2]): return 999.0
            R = 6371
            d_lat, d_lon = math.radians(lat2-lat1), math.radians(lon2-lon1)
            a = math.sin(d_lat/2)**2 + math.cos(math.radians(lat1)) * \
                math.cos(math.radians(lat2)) * math.sin(d_lon/2)**2
            return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))
        except: return 999.0

    @staticmethod
    def renderizar_vitrine(p, pid):
        # Lógica de Imagem
        foto = p.get('f1', '')
        img = f"data:image/jpeg;base64,{foto}" if len(foto) > 100 else "https://via.placeholder.com/400x400?text=GeralJa"
        
        nome = p.get('nome', 'Profissional').upper()
        dist = p.get('dist', 0.0)
        verificado = p.get('verificado', False)
        badge = "<span style='background:#FFD700; color:black; padding:2px 6px; border-radius:4px; font-size:10px; font-weight:bold;'>ELITE</span>" if verificado else ""

        html = f"""
        <div style="border: 2px solid #FFD700; border-radius: 15px; padding: 15px; margin-bottom: 20px; background-color: white;">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div style="display: flex; align-items: center;">
                    <div style="width: 60px; height: 60px; border-radius: 50%; background: url('{img}') center/cover; border: 2px solid #EEE; margin-right: 12px;"></div>
                    <div>
                        <h4 style="margin: 0; color: #1A1C23;">{nome} ✅</h4>
                        <p style="margin: 0; color: #ff4b4b; font-weight: bold; font-size: 12px;">📍 {dist:.1f} KM DE VOCÊ</p>
                    </div>
                </div>
                {badge}
            </div>
            <div style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 10px;">
                 <p style="font-size: 13px; color: #444;">{p.get('area', 'Geral')} • {p.get('descricao', '')[:100]}...</p>
            </div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)
        
        if st.button(f"📞 CONTATAR {nome}", key=f"btn_{pid}", use_container_width=True):
            zap = p.get('whatsapp', pid)
            st.link_button("🚀 ABRIR WHATSAPP", f"https://wa.me/55{zap}")

    @staticmethod
    def converter_img_b64(file):
        if file is None: return ""
        return base64.b64encode(file.read()).decode()

# INSTANCIAÇÃO OBRIGATÓRIA (Liga o motor)
IA_MESTRE = MotorGeralJa()
# ------------------------------------------------------------------------------
# 2. CAMADA DE PERSISTÊNCIA (FIREBASE)
# ------------------------------------------------------------------------------
@st.cache_resource
def conectar_banco_master():
    if not firebase_admin._apps:
        try:
            # Tenta pegar dos secrets do Streamlit
            if "FIREBASE_BASE64" in st.secrets:
                b64_key = st.secrets["FIREBASE_BASE64"]
                decoded_json = base64.b64decode(b64_key).decode("utf-8")
                cred_dict = json.loads(decoded_json)
                cred = credentials.Certificate(cred_dict)
                return firebase_admin.initialize_app(cred)
            else:
                # Fallback para desenvolvimento local (se houver arquivo json)
                # cred = credentials.Certificate("serviceAccountKey.json")
                # return firebase_admin.initialize_app(cred)
                st.warning("⚠️ Configure a secret FIREBASE_BASE64 para conectar ao banco.")
                return None
        except Exception as e:
            st.error(f"❌ FALHA NA INFRAESTRUTURA: {e}")
            st.stop()
    return firebase_admin.get_app()

app_engine = conectar_banco_master()

if app_engine:
    db = firestore.client()
else:
    st.error("Erro ao conectar ao Firebase. Verifique suas configurações.")
    st.stop()

# --- FUNÇÕES DE SUPORTE (Mantenha fora de blocos IF/ELSE para funcionar no app todo) ---

def buscar_opcoes_dinamicas(documento, padrao):
    """
    Busca listas de categorias ou tipos na coleção 'configuracoes'.
    """
    try:
        doc = db.collection("configuracoes").document(documento).get()
        if doc.exists:
            dados = doc.to_dict()
            return dados.get("lista", padrao)
        return padrao
    except Exception as e:
        # Se houver erro ou o banco estiver vazio, retorna a lista padrão
        return padrao

def exibir_card_profissional(p, pid):
    # 1. Configurações de Elite e Cores
    saldo = float(p.get('saldo', 0))
    is_elite = p.get('verificado', False) and saldo > 0
    cor_borda = "#FFD700" if is_elite else "#E2E8F0"
    
    # 2. Processamento das 4 Fotos (Blindagem de Base64)
    fotos = []
    for i in range(1, 5):
        f = p.get(f'f{i}', '')
        if len(str(f)) > 100: # Verifica se a imagem existe/é válida
            fotos.append(f"data:image/jpeg;base64,{f}")
    
    # Se não houver fotos, usa um placeholder elegante
    img_principal = fotos[0] if len(fotos) > 0 else "https://via.placeholder.com/400x400?text=GeralJa"

    # 3. HTML Estilo Instagram (Design de Luxo)
    st.markdown(f"""
    <div style="background:white; border-radius:20px; margin-bottom:20px; border:2px solid {cor_borda}; box-shadow:0 8px 20px rgba(0,0,0,0.08); overflow:hidden;">
        <div style="padding:12px 15px; display:flex; justify-content:space-between; align-items:center; background:#F8FAFC;">
            <div style="display:flex; align-items:center; gap:10px;">
                <div style="width:40px; height:40px; border-radius:50%; background:url('{img_principal}') center/cover; border:2px solid {cor_borda};"></div>
                <div>
                    <h4 style="margin:0; font-size:15px; color:#1E293B;">{p.get('nome', '').upper()} {"☑️" if p.get('verificado') else ""}</h4>
                    <small style="color:#64748B;">📍 {p.get('dist', 0):.1f} KM DE VOCÊ</small>
                </div>
            </div>
            {"<span style='background:#FFD700; color:black; padding:3px 10px; border-radius:12px; font-size:10px; font-weight:900;'>ELITE</span>" if is_elite else ""}
        </div>

        <div style="display:grid; grid-template-columns: 2.5fr 1fr; gap:4px; height:240px; padding:5px;">
            <div style="background:url('{img_principal}') center/cover; border-radius:12px 0 0 12px;"></div>
            <div style="display:grid; grid-template-rows: repeat(3, 1fr); gap:4px;">
                <div style="background:url('{fotos[1] if len(fotos)>1 else img_principal}') center/cover; border-radius:0 12px 0 0;"></div>
                <div style="background:url('{fotos[2] if len(fotos)>2 else img_principal}') center/cover;"></div>
                <div style="background:url('{fotos[3] if len(fotos)>3 else img_principal}') center/cover; border-radius:0 0 12px 0;"></div>
            </div>
        </div>

        <div style="padding:15px;">
            <span style="background:#F1F5F9; color:#475569; padding:2px 8px; border-radius:6px; font-size:11px; font-weight:bold; text-transform:uppercase;">{p.get('area', 'Serviços')}</span>
            <p style="margin-top:10px; color:#334155; font-size:14px; line-height:1.4;">{p.get('descricao', '')[:150]}...</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. Botão WhatsApp Integrado (Com desconto de saldo)
    if st.button(f"🟢 FALAR COM {p.get('nome','').split()[0].upper()}", key=f"wa_v_{pid}", use_container_width=True):
        if saldo > 0:
            try: db.collection("profissionais").document(pid).update({"saldo": firestore.Increment(-1)})
            except: pass
        
        msg = f"Olá {p.get('nome','')}, vi seu perfil de {p.get('area')} no GeralJá e gostaria de um orçamento!"
        link_zap = f"https://wa.me/55{pid}?text={msg.replace(' ', '%20')}"
        st.link_button("🚀 ABRIR WHATSAPP AGORA", link_zap, use_container_width=True)
    st.markdown("---")
# ------------------------------------------------------------------------------
# 3. POLÍTICAS E CONSTANTES
# ------------------------------------------------------------------------------
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ADMIN = "mumias"
LAT_REF = -23.5505
LON_REF = -46.6333

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
    "Diarista", "Cuidador de Idosos", "Babá", "Outro (Personalizado)"
]

CONCEITOS_EXPANDIDOS = {
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

# ------------------------------------------------------------------------------
# 4. MOTORES DE IA E UTILS
# ------------------------------------------------------------------------------
def normalizar_para_ia(texto):
    if not texto: return ""
    return "".join(c for c in unicodedata.normalize('NFD', str(texto)) 
                   if unicodedata.category(c) != 'Mn').lower().strip()

def processar_ia_avancada(texto):
    if not texto: return "Vazio"
    t_clean = normalizar_para_ia(texto)
    for chave, categoria in CONCEITOS_EXPANDIDOS.items():
        if re.search(rf"\b{normalizar_para_ia(chave)}\b", t_clean):
            return categoria
    for cat in CATEGORIAS_OFICIAIS:
        if normalizar_para_ia(cat) in t_clean:
            return cat
    return "NAO_ENCONTRADO"

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

# --- FUNCIONALIDADE DO ARQUIVO: O VARREDOR (Rodapé Automático) ---
def finalizar_e_alinhar_layout():
    """
    Esta função atua como um ímã. Puxa o conteúdo e limpa o rodapé.
    """
    st.write("---")
    fechamento_estilo = """
        <style>
            .main .block-container { padding-bottom: 5rem !important; }
            .footer-clean {
                text-align: center;
                padding: 20px;
                opacity: 0.7;
                font-size: 0.8rem;
                width: 100%;
                color: gray;
            }
        </style>
        <div class="footer-clean">
            <p>🎯 <b>GeralJá</b> - Sistema de Inteligência Local</p>
            <p>Conectando quem precisa com quem sabe fazer.</p>
            <p>v3.0 | © 2026 Todos os direitos reservados</p>
        </div>
    """
    st.markdown(fechamento_estilo, unsafe_allow_html=True)

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
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-container"><span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span><br><small style="color:#64748B; font-weight:700;">BRASIL ELITE EDITION</small></div>', unsafe_allow_html=True)

lista_abas = ["🔍 BUSCAR", "🚀 CADASTRAR", "👤 MEU PERFIL", "👑 ADMIN", "⭐ FEEDBACK"]
comando = st.sidebar.text_input("Comando Secreto", type="password")
if comando == "abracadabra":
    lista_abas.append("📊 FINANCEIRO")

menu_abas = st.tabs(lista_abas)
# ==============================================================================
# --- ABA 1: VITRINE (SISTEMA DE BUSCA E RANKING DE ELITE) ---
# ==============================================================================
# --- ABA 0: VITRINE INTELIGENTE ---
with menu_abas[0]:
    # Design de cabeçalho impactante
    st.markdown("<h2 style='text-align: center;'>🔍 O que você procura hoje?</h2>", unsafe_allow_html=True)
    
    # Input principal
    termo_busca = st.text_input("", placeholder="Ex: 'alguém para arrumar meu telhado' ou 'pizza artesanal'", key="input_busca_direta")
    
    # Filtros em colunas
    col_raio, col_ordenacao = st.columns([2, 2])
    with col_raio:
        raio_km = st.select_slider("📍 Raio de distância", options=[5, 10, 25, 50, 100, 500], value=50)
    with col_ordenacao:
        modo_ordem = st.selectbox("⭐ Priorizar por", ["Melhores Avaliados", "Mais Próximos", "Destaques (Patrocinados)"])

    st.markdown("---")

    if termo_busca:
        with st.spinner("🧠 IA Analisando sua necessidade..."):
            try:
                # 1. MAPEAMENTO DE INTENÇÃO (IA)
                try:
                    # Tenta converter 'telhado' em 'Pedreiro' ou 'Manutenção'
                    cat_ia = processar_ia_avancada(termo_busca)
                except:
                    cat_ia = termo_busca.capitalize()

                # 2. BUSCA MULTI-FILTRO NO FIREBASE
                # Buscamos apenas ativos. O filtro de categoria/distância fazemos no Python para mais flexibilidade
                profs_ref = db.collection("profissionais").where("aprovado", "==", True).stream()
                
                lista_resultados = []
                termo_min = cat_ia.lower()

                for doc in profs_ref:
                    p = doc.to_dict()
                    p['id'] = doc.id 
                    
                    # Lógica de match (Nome, Área ou Descrição)
                    texto_alvo = f"{p.get('area', '')} {p.get('nome', '')} {p.get('descricao', '')}".lower()
                    
                    if termo_min in texto_alvo:
                        # Cálculo de distância real
                        dist = calcular_distancia(LAT_PADRAO, LON_PADRAO, p.get('lat', LAT_PADRAO), p.get('lon', LON_PADRAO))
                        
                        if dist <= raio_km:
                            p['dist'] = dist
                            
                            # 3. MOTOR DE RANKING (A "Mágica" do Negócio)
                            # Verificados ganham 1000 pontos
                            # Cada R$ 1.00 de saldo (GeralCones) ganha 100 pontos
                            # Rating (estrelas) ganha 500 pontos por estrela
                            score = (10000 if p.get('verificado', False) else 0)
                            score += (float(p.get('saldo', 0)) * 100)
                            score += (float(p.get('rating', 5.0)) * 500)
                            
                            p['ranking_score'] = score
                            lista_resultados.append(p)

                # 4. EXIBIÇÃO ORGANIZADA
                if lista_resultados:
                    # Ordenação dinâmica baseada no selectbox
                    if modo_ordem == "Destaques (Patrocinados)":
                        lista_resultados.sort(key=lambda x: -x['ranking_score'])
                    elif modo_ordem == "Mais Próximos":
                        lista_resultados.sort(key=lambda x: x['dist'])
                    else:
                        lista_resultados.sort(key=lambda x: -x.get('rating', 0))

                    st.success(f"Encontramos {len(lista_resultados)} especialistas para você!")
                    
                    # Grid de exibição
                    for prof in lista_resultados:
                        exibir_card_profissional(prof, prof['id'])
                else:
                    st.warning(f"Ainda não temos profissionais para '{cat_ia}' nesta região.")
                    st.button("Quero ser o primeiro desta categoria! 🚀")

            except Exception as e:
                st.error(f"Erro no motor de busca: {e}")
    else:
        # Vitrine vazia (Exibir sugestões)
        st.info("Sugestões: Eletricista, Encanador, Diarista, Mecânico...")
                
# ==============================================================================
# --- ABA 2: CADASTRO (BLINDAGEM DE DUPLICADOS + 4 FOTOS + BÔNUS) ---
# ==============================================================================
with menu_abas[1]:
    st.markdown("### 🚀 Cadastro de Profissional Elite")
    st.info("🎁 BÔNUS: Novos cadastros ganham **10 GeralCones** de saldo inicial!")

    with st.form("form_cadastro_blindado_v4", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome Completo ou Empresa", placeholder="Ex: João Silva Pinturas")
            telefone = st.text_input("WhatsApp (DDD + Número)", help="Apenas números. Ex: 11999998888")
            area = st.selectbox("Sua Especialidade", CATEGORIAS_OFICIAIS)
        
        with col2:
            cidade = st.text_input("Cidade / UF", placeholder="Ex: São Paulo / SP")
            senha_acesso = st.text_input("Crie uma Senha", type="password", help="Para editar seu perfil no futuro")

        descricao = st.text_area("Descrição (O que você faz?)", placeholder="Conte um pouco sobre sua experiência e serviços...")
        
        st.markdown("---")
        st.write("📷 **Portfólio de Fotos** (Mostre seu trabalho)")
        
        # Grid de fotos 2x2 para ficar bonito no form
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            f1_file = st.file_uploader("Foto 1 (Perfil/Principal)", type=['jpg', 'jpeg', 'png'], key="cad_f1")
            f2_file = st.file_uploader("Foto 2 (Opcional)", type=['jpg', 'jpeg', 'png'], key="cad_f2")
        with f_col2:
            f3_file = st.file_uploader("Foto 3 (Opcional)", type=['jpg', 'jpeg', 'png'], key="cad_f3")
            f4_file = st.file_uploader("Foto 4 (Opcional)", type=['jpg', 'jpeg', 'png'], key="cad_f4")

        submit = st.form_submit_button("🚀 FINALIZAR E GANHAR 10 GERALCONES")

        if submit:
            # 1. LIMPEZA E FORMATAÇÃO DO ID
            tel_id = re.sub(r'\D', '', telefone)
            
            # --- REGRAS DE OURO (VALIDAÇÃO) ---
            if not nome or len(tel_id) < 10:
                st.error("❌ Nome e WhatsApp válidos são obrigatórios!")
            elif not f1_file:
                st.error("❌ Envie pelo menos a Foto Principal para atrair clientes!")
            else:
                try:
                    with st.spinner("Validando Cadastro Único..."):
                        # 2. BLINDAGEM CONTRA DUPLICADOS
                        doc_ref = db.collection("profissionais").document(tel_id).get()
                        
                        if doc_ref.exists:
                            st.warning(f"⚠️ Atenção! O número {tel_id} já está cadastrado no sistema.")
                            st.info("Use a aba de edição ou entre em contato com o suporte.")
                        else:
                            # 3. CONVERSÃO DE IMAGENS (SOMA DA FOTO 4)
                            img1 = converter_img_b64(f1_file)
                            img2 = converter_img_b64(f2_file) if f2_file else ""
                            img3 = converter_img_b64(f3_file) if f3_file else ""
                            img4 = converter_img_b64(f4_file) if f4_file else ""

                            # 4. ESTRUTURA DE DADOS COM BÔNUS DE 10 GERALCONES
                            dados_prof = {
                                "nome": nome.strip().upper(),
                                "telefone": tel_id,
                                "area": area,
                                "descricao": descricao,
                                "cidade": cidade.strip(),
                                "senha": senha_acesso,
                                "f1": img1, "f2": img2, "f3": img3, "f4": img4,
                                "aprovado": False,  # Entra para análise do admin
                                "verificado": False,
                                "saldo": 10.0,      # <--- BÔNUS GERALCONES AQUI
                                "lat": LAT_REF, 
                                "lon": LON_REF,
                                "data_cadastro": datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%d/%m/%Y %H:%M")
                            }

                            # 5. SALVAMENTO FINAL
                            db.collection("profissionais").document(tel_id).set(dados_prof)
                            
                            st.balloons()
                            st.success(f"🎊 PARABÉNS! {nome}, você ganhou 10 GeralCones!")
                            st.info("Seu perfil foi enviado para aprovação. Em breve você estará na vitrine!")
                            
                except Exception as e:
                    st.error(f"❌ Erro Técnico ao cadastrar: {e}")
# ==============================================================================
# ABA 3: MEU PERFIL (VITRINE LUXUOSA ESTILO INSTA)
# ==============================================================================
with menu_abas[2]:
    if 'auth' not in st.session_state: st.session_state.auth = False
    
    if not st.session_state.auth:
        st.markdown("<h2 style='text-align:center;'>🔐 Portal do Parceiro</h2>", unsafe_allow_html=True)
        with st.container():
            l_zap = st.text_input("WhatsApp (ID)", key="login_zap")
            l_pw = st.text_input("Senha", type="password", key="login_pw")
            if st.button("ENTRAR NA MINHA VITRINE", use_container_width=True):
                if l_zap:
                    doc_ref = db.collection("profissionais").document(l_zap)
                    doc = doc_ref.get()
                    if doc.exists and doc.to_dict().get('senha') == l_pw:
                        st.session_state.auth = True
                        st.session_state.user_id = l_zap
                        st.rerun()
                    else:
                        st.error("❌ Credenciais inválidas.")
    else:
        uid = st.session_state.user_id
        doc_ref = db.collection("profissionais").document(uid)
        d = doc_ref.get().to_dict()
        
        # --- HEADER ESTILO INSTAGRAM ---
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 20px; padding: 20px; background: white; border-radius: 20px; border: 1px solid #E2E8F0; margin-bottom: 20px;">
                <div style="position: relative;">
                    <img src="data:image/png;base64,{d.get('foto_b64', '')}" 
                         style="width: 100px; height: 100px; border-radius: 50%; object-fit: cover; border: 3px solid #E1306C;"
                         onerror="this.src='https://ui-avatars.com/api/?name={d.get('nome')}&background=random'">
                    <div style="position: absolute; bottom: 5px; right: 5px; background: #22C55E; width: 15px; height: 15px; border-radius: 50%; border: 2px solid white;"></div>
                </div>
                <div style="flex-grow: 1;">
                    <h2 style="margin: 0; font-size: 22px;">{d.get('nome')}</h2>
                    <p style="margin: 0; color: #64748B; font-size: 14px;">@{d.get('area').lower().replace(' ', '')}</p>
                    <div style="display: flex; gap: 15px; margin-top: 10px;">
                        <div style="text-align: center;"><b style="display: block;">{d.get('cliques', 0)}</b><small style="color: #64748B;">Cliques</small></div>
                        <div style="text-align: center;"><b style="display: block;">⭐ {d.get('rating', 5.0)}</b><small style="color: #64748B;">Nota</small></div>
                        <div style="text-align: center;"><b style="display: block;">{d.get('saldo', 0)}</b><small style="color: #64748B;">Moedas</small></div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # --- DASHBOARD DE PERFORMANCE (LUXUOSA) ---
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Visibilidade", f"{d.get('cliques', 0)} rkt", "Aumento de 12%")
        col_m2.metric("Saldo Atual", f"{d.get('saldo', 0)} 🪙")
        col_m3.metric("Status Perfil", "Elite" if d.get('elite') else "Padrão")

        # --- LOJA DE DESTAQUES (GRID VISUAL) ---
        st.markdown("### 💎 Impulsione sua Vitrine")
        with st.container():
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("<div style='background: linear-gradient(135deg, #FFD700, #FFA500); padding: 15px; border-radius: 15px; color: white; text-align: center;'><b>BRONZE</b><br>10 🪙<br>R$ 25</div>", unsafe_allow_html=True)
                if st.button("Comprar 10", key="buy_10", use_container_width=True):
                     st.markdown(f'<meta http-equiv="refresh" content="0;URL=https://wa.me/{ZAP_ADMIN}?text=Quero 10 moedas para ID: {uid}">', unsafe_allow_html=True)
            with c2:
                st.markdown("<div style='background: linear-gradient(135deg, #C0C0C0, #808080); padding: 15px; border-radius: 15px; color: white; text-align: center;'><b>PRATA</b><br>30 🪙<br>R$ 60</div>", unsafe_allow_html=True)
                if st.button("Comprar 30", key="buy_30", use_container_width=True):
                     st.markdown(f'<meta http-equiv="refresh" content="0;URL=https://wa.me/{ZAP_ADMIN}?text=Quero 30 moedas para ID: {uid}">', unsafe_allow_html=True)
            with c3:
                st.markdown("<div style='background: linear-gradient(135deg, #FFD700, #D4AF37); padding: 15px; border-radius: 15px; color: white; text-align: center;'><b>OURO</b><br>100 🪙<br>R$ 150</div>", unsafe_allow_html=True)
                if st.button("Comprar 100", key="buy_100", use_container_width=True):
                     st.markdown(f'<meta http-equiv="refresh" content="0;URL=https://wa.me/{ZAP_ADMIN}?text=Quero 100 moedas para ID: {uid}">', unsafe_allow_html=True)

        st.divider()

        # --- EDIÇÃO DE DADOS (TURBINADA) ---
        with st.expander("⚙️ CONFIGURAÇÕES DA VITRINE", expanded=False):
            with st.form("edit_v2"):
                st.markdown("#### ✨ Informações Públicas")
                new_foto = st.file_uploader("Trocar Foto de Perfil", type=["jpg", "png", "jpeg"])
                n_nome = st.text_input("Nome da Vitrine", value=d.get('nome'))
                n_desc = st.text_area("Bio (O que você faz de melhor?)", value=d.get('descricao'))
                
                col_e1, col_e2 = st.columns(2)
                n_area = col_e1.selectbox("Categoria", CATEGORIAS_OFICIAIS, index=CATEGORIAS_OFICIAIS.index(d.get('area', 'Ajudante Geral')))
                n_tipo = col_e2.radio("Tipo", ["👤 Profissional", "🏢 Comércio/Loja"], index=0 if d.get('tipo') == "👤 Profissional" else 1, horizontal=True)

                if st.form_submit_button("💾 ATUALIZAR MINHA VITRINE", use_container_width=True):
                    up = {
                        "nome": n_nome, "area": n_area, "descricao": n_desc, "tipo": n_tipo
                    }
                    if new_foto:
                        up["foto_b64"] = converter_img_b64(new_foto)
                    
                    doc_ref.update(up)
                    st.success("Vitrine atualizada! 🚀")
                    time.sleep(1)
                    st.rerun()

        if st.button("LOGOUT", type="secondary"):
            st.session_state.auth = False
            st.rerun()
# ==============================================================================
# ABA 4: 👑 PAINEL DE CONTROLE MASTER (TURBINADO)
# ==============================================================================
with menu_abas[3]:
    st.markdown("## 👑 Gestão Estratégica GeralJá")
    
    access_adm = st.text_input("Chave Mestra", type="password", key="auth_master")

    if access_adm == CHAVE_ADMIN:
        # --- 1. DASHBOARD DE MÉTRICAS ---
        st.markdown("### 📊 Performance da Rede")
        todos_profs = list(db.collection("profissionais").stream())
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Profissionais", len(todos_profs))
        
        # Cálculos rápidos
        total_cliques = sum([p.to_dict().get('cliques', 0) for p in todos_profs])
        saldo_total = sum([p.to_dict().get('saldo', 0) for p in todos_profs])
        pendentes = len([p for p in todos_profs if not p.to_dict().get('aprovado')])
        
        m2.metric("Cliques Totais", total_cliques)
        m3.metric("Saldo em Circulação", f"{saldo_total} 💎")
        m4.metric("Aguardando Aprovação", pendentes, delta_color="inverse", delta=pendentes)

        st.divider()# --- GERENCIADOR DE CATEGORIAS DINÂMICAS ---
        st.divider()
        st.markdown("### 🛠️ Configurações de Expansão")
        st.caption("Adicione novas opções que aparecerão instantaneamente no formulário de cadastro.")
        
        col_adm_1, col_adm_2 = st.columns(2)
        
        with col_adm_1:
            st.write("**✨ Novas Profissões (IA)**")
            nova_cat = st.text_input("Nome da Profissão", placeholder="Ex: Adestrador", key="add_cat_input")
            if st.button("➕ Adicionar Categoria", use_container_width=True):
                if nova_cat:
                    doc_ref = db.collection("configuracoes").document("categorias")
                    lista_atual = buscar_opcoes_dinamicas("categorias", [])
                    if nova_cat not in lista_atual:
                        lista_atual.append(nova_cat)
                        doc_ref.set({"lista": lista_atual})
                        st.success(f"'{nova_cat}' agora faz parte do sistema!")
                        time.sleep(1)
                        st.rerun()

        with col_adm_2:
            st.write("**🏢 Novos Tipos de Negócio**")
            novo_tipo = st.text_input("Tipo de Comércio", placeholder="Ex: Food Truck", key="add_tipo_input")
            if st.button("➕ Adicionar Tipo", use_container_width=True):
                if novo_tipo:
                    doc_ref = db.collection("configuracoes").document("tipos")
                    lista_atual = buscar_opcoes_dinamicas("tipos", [])
                    if novo_tipo not in lista_atual:
                        lista_atual.append(novo_tipo)
                        doc_ref.set({"lista": lista_atual})
                        st.success(f"'{novo_tipo}' adicionado com sucesso!")
                        time.sleep(1)
                        st.rerun()

        # --- 2. LISTA DE GESTÃO ---
        st.markdown("### 📋 Gerenciar Profissionais")
        
        for p_doc in todos_profs:
            p = p_doc.to_dict()
            pid = p_doc.id
            
            with st.expander(f"{'✅' if p.get('aprovado') else '⏳'} {p.get('nome').upper()} - {p.get('area')}"):
                c1, c2, c3 = st.columns([1, 2, 1])
                
                with c1:
                    # Foto de Perfil
                    foto = p.get('foto_b64')
                    if foto:
                        st.image(f"data:image/png;base64,{foto}", width=100)
                    st.write(f"ID: `{pid}`")
                    st.write(f"Saldo: **{p.get('saldo', 0)} 💎**")

                with c2:
                    st.write(f"**Descrição:** {p.get('descricao')}")
                    st.write(f"**Tipo:** {p.get('tipo')}")
                    st.write(f"**Cliques:** {p.get('cliques', 0)}")
                    
                    # Exibir as 3 fotos da vitrine se existirem
                    st.write("🖼️ **Vitrine:**")
                    fv = [p.get('f1'), p.get('f2'), p.get('f3')]
                    cols_f = st.columns(3)
                    for i, f_data in enumerate(fv):
                        if f_data:
                            cols_f[i].image(f"data:image/png;base64,{f_data}", use_container_width=True)

                with c3:
                    st.write("⚡ **Ações Rápidas**")
                    
                    # Aprovação
                    if not p.get('aprovado'):
                        if st.button("✅ APROVAR AGORA", key=f"apr_{pid}", use_container_width=True):
                            db.collection("profissionais").document(pid).update({"aprovado": True})
                            st.rerun()
                    
                    # Verificado/Elite
                    is_ver = p.get('verificado', False)
                    label_ver = "💎 REMOVER ELITE" if is_ver else "🌟 TORNAR ELITE"
                    if st.button(label_ver, key=f"ver_{pid}", use_container_width=True):
                        db.collection("profissionais").document(pid).update({"verificado": not is_ver})
                        st.rerun()

                    # Adicionar Saldo (Pacote de 10)
                    if st.button("➕ ADD 10 SALDO", key=f"plus_{pid}", use_container_width=True):
                        db.collection("profissionais").document(pid).update({"saldo": p.get('saldo', 0) + 10})
                        st.rerun()

                    # Botão de Exclusão (Cuidado!)
                    if st.button("🗑️ EXCLUIR", key=f"del_{pid}", use_container_width=True):
                        db.collection("profissionais").document(pid).delete()
                        st.rerun()

    elif access_adm != "":
        st.error("🚫 Acesso negado. Chave incorreta.")
    else:
        st.info("Aguardando Chave Mestra para liberar os controles.")

# ==============================================================================
# ABA 5: FEEDBACK
# ==============================================================================
with menu_abas[4]:
    st.header("⭐ Avalie a Plataforma")
    st.write("Sua opinião nos ajuda a melhorar.")
    
    nota = st.slider("Nota", 1, 5, 5)
    comentario = st.text_area("O que podemos melhorar?")
    
    if st.button("Enviar Feedback"):
        st.success("Obrigado! Sua mensagem foi enviada para nossa equipe.")
        # Em produção, salvaria em uma coleção 'feedbacks'

# ------------------------------------------------------------------------------
# FINALIZAÇÃO (DO ARQUIVO ORIGINAL)
# ------------------------------------------------------------------------------
finalizar_e_alinhar_layout()








