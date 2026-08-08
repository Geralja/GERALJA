# ==============================================================================
# GERALJÁ: CRIANDO SOLUÇÕES
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
import pytz

# ------------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DE AMBIENTE E PERFORMANCE
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="GeralJá | Criando Soluções",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Oculta elementos padrão do Streamlit
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {display: none !important;}
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

CATEGORIAS_OFICIAIS = [
    # --- MANUTENÇÃO E REFORMAS ---
    "Encanador", "Eletricista", "Pintor", "Pedreiro", "Gesseiro", "Telhadista", 
    "Serralheiro", "Vidraceiro", "Marceneiro", "Marmoraria", "Calhas e Rufos", 
    "Dedetização", "Desentupidora", "Piscineiro", "Jardineiro", "Limpeza de Estofados",

    # --- AUTOMOTIVO ---
    "Mecânico", "Borracheiro", "Guincho 24h", "Estética Automotiva", "Lava Jato", 
    "Auto Elétrica", "Funilaria e Pintura", "Som e Alarme", "Moto Peças", "Auto Peças",

    # --- COMÉRCIOS E LOJAS ---
    "Loja de Roupas", "Calçados", "Loja de Variedades", "Relojoaria", "Joalheria", 
    "Ótica", "Armarinho/Aviamentos", "Papelaria", "Floricultura", "Bazar", 
    "Material de Construção", "Tintas", "Madeireira", "Móveis", "Eletrodomésticos",

    # --- ALIMENTAÇÃO E BEBIDAS ---
    "Pizzaria", "Lanchonete", "Restaurante", "Confeitaria", "Padaria", "Açaí", 
    "Sorveteria", "Adega", "Doceria", "Hortifruti", "Açougue", "Pastelaria", 
    "Churrascaria", "Hamburgueria", "Comida Japonesa", "Cafeteria",

    # --- SAÚDE E BELEZA ---
    "Farmácia", "Barbearia/Salão", "Manicure/Pedicure", "Estética Facial", 
    "Tatuagem/Piercing", "Fitness", "Academia", "Fisioterapia", "Odontologia", 
    "Clínica Médica", "Psicologia", "Nutricionista",

    # --- TECNOLOGIA E SERVIÇOS ---
    "TI", "Assistência Técnica", "Celulares", "Informática", "Refrigeração", 
    "Técnico de Fogão", "Técnico de Lavadora", "Eletrônicos", "Chaveiro", 
    "Montador", "Freteiro", "Carreto", "Motoboy/Entregas",

    # --- PETS E AGRO ---
    "Pet Shop", "Veterinário", "Banho e Tosa", "Adestrador", "Agropecuária",

    # --- EDUCAÇÃO E OUTROS ---
    "Aulas Particulares", "Escola Infantil", "Reforço Escolar", "Idiomas", 
    "Advocacia", "Contabilidade", "Imobiliária", "Seguros", "Ajudante Geral", 
    "Diarista", "Cuidador de Idosos", "Babá", "Outro (Personalizado)"
]

CONCEITOS_EXPANDIDOS = {
    # --- ALIMENTAÇÃO, BARES E GASTRONOMIA ---
    "pizza": "Pizzaria", "pizzaria": "Pizzaria", "fome": "Pizzaria", "massa": "Pizzaria", "calzone": "Pizzaria",
    "lanche": "Lanchonete", "hamburguer": "Lanchonete", "burger": "Lanchonete", "x-tudo": "Lanchonete", "hot dog": "Lanchonete", "cachorro quente": "Lanchonete", "salgado": "Lanchonete", "coxinha": "Lanchonete", "pastel": "Lanchonete",
    "comida": "Restaurante", "almoco": "Restaurante", "marmita": "Restaurante", "jantar": "Restaurante", "restaurante": "Restaurante", "self service": "Restaurante", "churrasco": "Restaurante", "espetinho": "Restaurante",
    "doce": "Confeitaria", "bolo": "Confeitaria", "festa": "Confeitaria", "salgadinho": "Confeitaria", "brigadeiro": "Confeitaria", "sobremesa": "Confeitaria", "aniversario": "Confeitaria",
    "pao": "Padaria", "padaria": "Padaria", "cafe": "Padaria", "padoca": "Padaria", "leite": "Padaria", "biscoito": "Padaria",
    "acai": "Açaí", "cupuacu": "Açaí", "sorvete": "Sorveteria", "picole": "Sorveteria", "gelateria": "Sorveteria",
    "cerveja": "Adega", "bebida": "Adega", "gelo": "Adega", "adega": "Adega", "vinho": "Adega", "destilado": "Adega", "vodka": "Adega", "refrigerante": "Adega",
    "churros": "Doceria", "crepe": "Doceria", "tapioca": "Lanchonete",

    # --- VAREJO, MODA E PRESENTES ---
    "roupa": "Loja de Roupas", "vestuario": "Loja de Roupas", "moda": "Loja de Roupas", "camiseta": "Loja de Roupas", "calca": "Loja de Roupas", "blusa": "Loja de Roupas", "boutique": "Loja de Roupas", "brecho": "Loja de Roupas",
    "sapato": "Calçados", "tenis": "Calçados", "chinelo": "Calçados", "sandalia": "Calçados", "bota": "Calçados", "sapataria": "Calçados",
    "presente": "Loja de Variedades", "brinquedo": "Loja de Variedades", "utilidades": "Loja de Variedades", "papelaria": "Loja de Variedades", "caderno": "Loja de Variedades",
    "relogio": "Relojoaria", "joia": "Joalheria", "anel": "Joalheria", "brinco": "Joalheria",
    "otica": "Ótica", "oculos": "Ótica", "lente": "Ótica",

    # --- SAÚDE, BELEZA E BEM-ESTAR ---
    "remedio": "Farmácia", "farmacia": "Farmácia", "drogaria": "Farmácia", "saude": "Farmácia", "medicamento": "Farmácia",
    "cabelo": "Barbearia/Salão", "barba": "Barbearia/Salão", "corte": "Barbearia/Salão", "cabeleireiro": "Barbearia/Salão", "manicure": "Barbearia/Salão", "unha": "Barbearia/Salão", "pedicure": "Barbearia/Salão", "sobrancelha": "Barbearia/Salão", "maquiagem": "Barbearia/Salão",
    "academia": "Fitness", "treino": "Fitness", "musculacao": "Fitness", "crossfit": "Fitness", "suplemento": "Fitness",
    "dentista": "Odontologia", "dente": "Odontologia", "aparelho": "Odontologia",

    # --- TECNOLOGIA E ELETRODOMÉSTICOS ---
    "celular": "Assistência Técnica", "iphone": "Assistência Técnica", "tela": "Assistência Técnica", "carregador": "Assistência Técnica", "android": "Assistência Técnica", "bateria": "Assistência Técnica",
    "computador": "TI", "notebook": "TI", "formatar": "TI", "wifi": "TI", "internet": "TI", "pc": "TI", "gamer": "TI", "impressora": "TI",
    "geladeira": "Refrigeração", "ar condicionado": "Refrigeração", "freezer": "Refrigeração", "ar": "Refrigeração", "climatizador": "Refrigeração",
    "fogao": "Técnico de Fogão", "forno": "Técnico de Fogão", "cooktop": "Técnico de Fogão",
    "maquina de lavar": "Técnico de Lavadora", "lavadora": "Técnico de Lavadora", "lava e seca": "Técnico de Lavadora",
    "tv": "Eletrônicos", "televisao": "Eletrônicos", "som": "Eletrônicos", "video game": "Eletrônicos",

    # --- PETS E AGRO ---
    "pet": "Pet Shop", "racao": "Pet Shop", "cachorro": "Pet Shop", "gato": "Pet Shop", "banho e tosa": "Pet Shop", "veterinario": "Pet Shop", "viva": "Pet Shop", "aquario": "Pet Shop",

    # --- MANUTENÇÃO, REFORMA E CONSTRUÇÃO ---
    "vazamento": "Encanador", "cano": "Encanador", "torneira": "Encanador", "desentupir": "Encanador", "caixa dagua": "Encanador", "esgoto": "Encanador", "hidraulica": "Encanador",
    "curto": "Eletricista", "fiacao": "Eletricista", "luz": "Eletricista", "chuveiro": "Eletricista", "tomada": "Eletricista", "disjuntor": "Eletricista", "energia": "Eletricista", "fio": "Eletricista",
    "pintar": "Pintor", "pintura": "Pintor", "parede": "Pintor", "massa corrida": "Pintor", "verniz": "Pintor",
    "reforma": "Pedreiro", "piso": "Pedreiro", "azulejo": "Pedreiro", "obra": "Pedreiro", "tijolo": "Pedreiro", "cimento": "Pedreiro", "reboco": "Pedreiro", "alicerce": "Pedreiro",
    "gesso": "Gesseiro", "drywall": "Gesseiro", "sanca": "Gesseiro", "forro": "Gesseiro",
    "telhado": "Telhadista", "goteira": "Telhadista", "calha": "Telhadista",
    "solda": "Serralheiro", "portao": "Serralheiro", "grade": "Serralheiro", "aluminio": "Serralheiro", "ferro": "Serralheiro",
    "vidro": "Vidraceiro", "janela": "Vidraceiro", "box": "Vidraceiro", "espelho": "Vidraceiro",
    "chave": "Chaveiro", "fechadura": "Chaveiro", "tranca": "Chaveiro", "copia": "Chaveiro", "abertura": "Chaveiro",

    # --- AUTOMOTIVO ---
    "carro": "Mecânico", "motor": "Mecânico", "oficina": "Mecânico", "freio": "Mecânico", "suspensao": "Mecânico", "cambio": "Mecânico",
    "pneu": "Borracheiro", "estepe": "Borracheiro", "furou": "Borracheiro", "vulcanizacao": "Borracheiro", "balanceamento": "Borracheiro",
    "guincho": "Guincho 24h", "reboque": "Guincho 24h", "plataforma": "Guincho 24h",
    "lavajato": "Estética Automotiva", "lavagem": "Estética Automotiva", "polimento": "Estética Automotiva", "limpeza de banco": "Estética Automotiva",

    # --- LOGÍSTICA E SERVIÇOS GERAIS ---
    "frete": "Freteiro", "mudanca": "Freteiro", "carreto": "Freteiro", "transporte": "Freteiro",
    "montar": "Montador", "armario": "Montador", "moveis": "Montador", "guarda roupa": "Montador", "cozinha": "Montador",
    "faxina": "Diarista", "limpeza": "Diarista", "passar": "Diarista", "arrumadeira": "Diarista",
    "jardim": "Jardineiro", "grama": "Jardineiro", "poda": "Jardineiro", "rocar": "Jardineiro",
    "piscina": "Piscineiro", "cloro": "Piscineiro", "limpeza de piscina": "Piscineiro",
    "ajudante": "Ajudante Geral", "braco": "Ajudante Geral", "carga": "Ajudante Geral"
}

# ------------------------------------------------------------------------------
# 4. MOTORES DE IA, GEOLOCALIZAÇÃO E SEGURANÇA
# ------------------------------------------------------------------------------
def normalizar_para_ia(texto):
    if not texto: return ""
    return "".join(c for c in unicodedata.normalize('NFD', str(texto)) 
                  if unicodedata.category(c) != 'Mn').lower().strip()

def processar_ia_avancada(texto):
    if not texto: return "Vazio"
    t_clean = normalizar_para_ia(texto)
    
    for chave, categoria in CONCEITOS_EXPANDIDOS.items():
        chave_norm = normalizar_para_ia(chave)
        if re.search(rf"\b{chave_norm}\b", t_clean):
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

def enviar_alerta_admin(nome_prof, categoria_prof, whatsapp_prof):
    msg_alerta = f"🚀 *NOVO CADASTRO NO GERALJÁ*\n\n" \
                 f"👤 *Nome:* {nome_prof}\n" \
                 f"🛠️ *Área:* {categoria_prof}\n" \
                 f"📱 *Zap:* {whatsapp_prof}\n\n" \
                 f"Acesse o Painel Admin para aprovar!"
    
    msg_encoded = msg_alerta.replace('\n', '%0A').replace(' ', '%20')
    return f"https://wa.me/{ZAP_ADMIN}?text={msg_encoded}"

def guardia_escanear_e_corrigir():
    status_log = []
    try:
        profs = db.collection("profissionais").stream()
        for p_doc in profs:
            dados = p_doc.to_dict()
            id_pro = p_doc.id
            correcoes = {}

            if not dados.get('area') or dados.get('area') not in CATEGORIAS_OFICIAIS:
                correcoes['area'] = "Ajudante Geral"
            
            if not dados.get('descricao'):
                correcoes['descricao'] = "Profissional parceiro do ecossistema GeralJá Brasil."
            
            if dados.get('saldo') is None:
                correcoes['saldo'] = 0
            
            if dados.get('lat') is None or dados.get('lon') is None:
                correcoes['lat'] = LAT_REF
                correcoes['lon'] = LON_REF

            if correcoes:
                db.collection("profissionais").document(id_pro).update(correcoes)
                status_log.append(f"✅ Corrigido: {id_pro}")
        
        return status_log if status_log else ["SISTEMA ÍNTEGRO: Nenhum erro encontrado."]
    except Exception as e:
        return [f"❌ Erro no Scanner: {e}"]

def scan_virus_e_scripts():
    alertas = []
    profs = db.collection("profissionais").stream()
    padroes_perigosos = [r"<script>", r"javascript:", r"DROP TABLE", r"OR 1=1"]
    
    for p_doc in profs:
        dados = p_doc.to_dict()
        conteudo = str(dados.get('nome', '')) + str(dados.get('descricao', ''))
        
        for padrao in padroes_perigosos:
            if re.search(padrao, conteudo, re.IGNORECASE):
                alertas.append(f"⚠️ PERIGO: Conteúdo suspeito no ID {p_doc.id}")
                db.collection("profissionais").document(p_doc.id).update({"aprovado": False})
    
    return alertas if alertas else ["LIMPO: Nenhum script malicioso detectado."]

# ------------------------------------------------------------------------------
# 5. DESIGN SYSTEM & ESTILIZAÇÃO VISUAL
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

# ------------------------------------------------------------------------------
# 6. ESTRUTURA DE ABAS
# ------------------------------------------------------------------------------
lista_abas = ["🔍 BUSCAR", "🚀 CADASTRAR", "👤 MEU PERFIL", "👑 ADMIN", "⭐ FEEDBACK"]

comando = st.sidebar.text_input("Comando Secreto", type="password")
if comando == "abracadabra":
    lista_abas.append("📊 FINANCEIRO")

menu_abas = st.tabs(lista_abas)

# ==============================================================================
# ABA 0: BUSCA
# ==============================================================================
with menu_abas[0]:
    st.markdown("### 🏙️ O que você precisa?")
    c1, c2 = st.columns([3, 1])
    termo_busca = c1.text_input("Ex: 'Cano estourado'", key="main_search")
    raio_km = c2.select_slider("Raio (KM)", options=[1, 3, 5, 10, 20, 50, 100, 500], value=3)
    
    if termo_busca:
        cat_ia = processar_ia_avancada(termo_busca)
        st.info(f"✨ IA: Buscando por **{cat_ia}**")
        profs = db.collection("profissionais").where("area", "==", cat_ia).where("aprovado", "==", True).stream()
        
        lista_ranking = []
        for p_doc in profs:
            p = p_doc.to_dict()
            p['id'] = p_doc.id
            dist = calcular_distancia_real(LAT_REF, LON_REF, p.get('lat', LAT_REF), p.get('lon', LON_REF))
            if dist <= raio_km:
                p['dist'] = dist
                
                score = 0
                score += 500 if p.get('verificado', False) else 0
                score += (p.get('saldo', 0) * 10)
                score += (p.get('rating', 5) * 20)
                p['score_elite'] = score
                
                lista_ranking.append(p)

        lista_ranking.sort(key=lambda x: (-x['score_elite'], x['dist']))

        try:
            hora_atual = datetime.datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%H:%M')
        except:
            hora_atual = datetime.datetime.now().strftime('%H:%M')

        if not lista_ranking:
            st.markdown(f"""
            <div style="background-color: #FFF4E5; padding: 20px; border-radius: 15px; border-left: 5px solid #FF8C00;">
                <h3 style="color: #856404;">🔍 Essa profissão ainda não foi preenchida por enquanto.</h3>
                <p style="color: #856404;">Portanto, se você <b>compartilhar o GeralJá</b>, quando você voltar, 
                mostraremos o que já temos perto de você!</p>
            </div>
            """, unsafe_allow_html=True)
            
            link_share = "https://wa.me/?text=Ei!%20Procurei%20um%20serviço%20no%20GeralJá%20e%20vi%20que%20ainda%20temos%20vagas%20para%20profissionais%20da%20nossa%20região!%20Cadastre-se:%20https://geralja.streamlit.app"
            st.markdown(f'<a href="{link_share}" target="_blank" style="text-decoration:none;"><div style="background:#22C55E; color:white; padding:15px; border-radius:10px; text-align:center; font-weight:bold; margin-top:10px;">📲 COMPARTILHAR NO WHATSAPP</div></a>', unsafe_allow_html=True)
        
        else:
            for p in lista_ranking:
                pid = p['id']
                is_elite = p.get('verificado') and p.get('saldo', 0) > 0
                
                with st.container():
                    cor_borda = "#FFD700" if is_elite else ("#FF8C00" if p.get('tipo') == "🏢 Comércio/Loja" else "#0047AB")
                    bg_card = "#FFFDF5" if is_elite else "#FFFFFF"
                    
                    st.markdown(f"""
                    <div style="border-left: 8px solid {cor_borda}; padding: 15px; background: {bg_card}; border-radius: 15px; margin-bottom: 5px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                        <span style="font-size: 12px; color: gray; font-weight: bold;">📍 a {p['dist']:.1f} km de você {" | 🏆 DESTAQUE" if is_elite else ""}</span>
                    </div>
                    """, unsafe_allow_html=True)

                    col_img, col_txt = st.columns([1, 4])
                    with col_img:
                        foto = p.get('foto_url') if p.get('foto_url') else 'https://via.placeholder.com/150'
                        st.markdown(f'<img src="{foto}" style="width:75px; height:75px; border-radius:50%; object-fit:cover; border:3px solid {cor_borda}">', unsafe_allow_html=True)
                    
                    with col_txt:
                        nome_exibicao = p.get('nome', '').upper()
                        if p.get('verificado', False): 
                            nome_exibicao += " <span style='color:#1DA1F2;'>☑️</span>"
                        
                        status_loja = ""
                        if p.get('tipo') == "🏢 Comércio/Loja":
                            h_ab, h_fe = p.get('h_abre', '08:00'), p.get('h_fecha', '18:00')
                            status_loja = " 🟢 <b style='color:green;'>ABERTO</b>" if h_ab <= hora_atual <= h_fe else " 🔴 <b style='color:red;'>FECHADO</b>"
                        
                        st.markdown(f"**{nome_exibicao}** {status_loja}", unsafe_allow_html=True)
                        st.caption(f"{p.get('descricao', '')[:120]}...")

                    if p.get('portfolio_imgs'):
                        imgs = p.get('portfolio_imgs')
                        cols_v = st.columns(3)
                        for i, img_b64 in enumerate(imgs[:3]):
                            cols_v[i].image(img_b64, use_container_width=True)

                    if st.button(f"FALAR COM {p.get('nome').split()[0].upper()}", key=f"unique_btn_{pid}", use_container_width=True):
                        if p.get('saldo', 0) > 0:
                            db.collection("profissionais").document(pid).update({
                                "saldo": p.get('saldo') - 1,
                                "cliques": p.get('cliques', 0) + 1
                            })
                        link_zap = f"https://wa.me/55{pid}?text=Olá!%20Vi%20seu%20perfil%20no%20GeralJá."
                        st.markdown(f'<meta http-equiv="refresh" content="0;URL={link_zap}">', unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)

# ==============================================================================
# ABA 1: CADASTRO
# ==============================================================================
with menu_abas[1]:
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
                try:
                    db.collection("profissionais").document(r_z).set({
                        "nome": r_n,
                        "whatsapp": r_z,
                        "senha": r_s,
                        "area": r_a,
                        "descricao": r_d,
                        "saldo": BONUS_WELCOME,
                        "cliques": 0,
                        "rating": 5.0,
                        "aprovado": False,
                        "lat": LAT_REF,
                        "lon": LON_REF,
                        "foto_url": "",
                        "portfolio_imgs": [],
                        "data_registro": datetime.datetime.now()
                    })
                    st.success("✅ Cadastro enviado com sucesso! Aguarde a aprovação do administrador para aparecer nas buscas.")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro ao cadastrar: {e}")

# ==============================================================================
# ABA 2: MEU PERFIL (CENTRAL DO PARCEIRO)
# ==============================================================================
with menu_abas[2]:
    if 'auth' not in st.session_state: st.session_state.auth = False
    
    if not st.session_state.auth:
        st.subheader("🚀 Acesso ao Painel do Parceiro")
        col1, col2 = st.columns(2)
        l_zap = col1.text_input("WhatsApp (Somente números)")
        l_pw = col2.text_input("Senha", type="password")
        
        if st.button("ENTRAR NO PAINEL", use_container_width=True):
            u = db.collection("profissionais").document(l_zap).get()
            if u.exists and u.to_dict().get('senha') == l_pw:
                st.session_state.auth, st.session_state.user_id = True, l_zap
                st.rerun()
            else:
                st.error("❌ Dados incorretos. Tente novamente.")
    else:
        doc_ref = db.collection("profissionais").document(st.session_state.user_id)
        d = doc_ref.get().to_dict()
        
        st.markdown(f"""
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 20px;">
                <div style="background:#1E293B; color:white; padding:15px; border-radius:15px; text-align:center;">
                    <small>MEU SALDO</small><br><b style="font-size:20px;">{d.get('saldo', 0)} 🪙</b>
                </div>
                <div style="background:#1E293B; color:white; padding:15px; border-radius:15px; text-align:center;">
                    <small>CLIQUES</small><br><b style="font-size:20px;">{d.get('cliques', 0)} 🚀</b>
                </div>
                <div style="background:#1E293B; color:white; padding:15px; border-radius:15px; text-align:center;">
                    <small>STATUS</small><br><b style="font-size:14px;">{"🟢 ATIVO" if d.get('aprovado') else "🟡 PENDENTE"}</b>
                </div>
            </div>
        """, unsafe_allow_html=True)

        with st.expander("💎 COMPRAR MOEDAS E GANHAR DESTAQUE", expanded=True):
            st.markdown("<p style='text-align:center; color:gray;'>Escolha um pacote para subir no ranking e receber mais chamados.</p>", unsafe_allow_html=True)
            cv1, cv2, cv3 = st.columns(3)
            
            with cv1:
                st.markdown('<div style="border:1px solid #ddd; padding:10px; border-radius:10px; text-align:center;"><b>BRONZE</b><br>10 moedas<br><b>R$ 25</b></div>', unsafe_allow_html=True)
                if st.button("COMPRAR 🥉", key="btn_b10", use_container_width=True):
                    msg = f"Olá! Quero o Pacote BRONZE (10 moedas) para o Zap: {st.session_state.user_id}"
                    st.markdown(f'<meta http-equiv="refresh" content="0;URL=https://wa.me/{ZAP_ADMIN}?text={msg.replace(" ", "%20")}">', unsafe_allow_html=True)

            with cv2:
                st.markdown('<div style="border:2px solid #FFD700; background:#FFFDF5; padding:10px; border-radius:10px; text-align:center;"><b>PRATA</b><br>30 moedas<br><b>R$ 60</b></div>', unsafe_allow_html=True)
                if st.button("COMPRAR 🥈", key="btn_p30", use_container_width=True):
                    msg = f"Olá! Quero o Pacote PRATA (30 moedas) para o Zap: {st.session_state.user_id}"
                    st.markdown(f'<meta http-equiv="refresh" content="0;URL=https://wa.me/{ZAP_ADMIN}?text={msg.replace(" ", "%20")}">', unsafe_allow_html=True)

            with cv3:
                st.markdown('<div style="border:1px solid #ddd; padding:10px; border-radius:10px; text-align:center;"><b>OURO</b><br>100 moedas<br><b>R$ 150</b></div>', unsafe_allow_html=True)
                if st.button("COMPRAR 🥇", key="btn_o100", use_container_width=True):
                    msg = f"Olá! Quero o Pacote OURO (100 moedas) para o Zap: {st.session_state.user_id}"
                    st.markdown(f'<meta http-equiv="refresh" content="0;URL=https://wa.me/{ZAP_ADMIN}?text={msg.replace(" ", "%20")}">', unsafe_allow_html=True)
        
        st.divider()
        
        with st.expander("📝 MEU PERFIL & VITRINE", expanded=True):
            with st.form("ed"):
                col_f1, col_f2 = st.columns(2)
                n_nome = col_f1.text_input("Nome Profissional/Loja", d.get('nome', ''))
                
                try:
                    idx_at = CATEGORIAS_OFICIAIS.index(d.get('area', 'Ajudante Geral'))
                except:
                    idx_at = 0
                
                n_area = col_f2.selectbox("Sua Especialidade", CATEGORIAS_OFICIAIS, index=idx_at)
                n_desc = st.text_area("Descrição (Conte sua experiência ou sobre sua loja)", d.get('descricao', ''))

                st.markdown("---")
                col_c1, col_c2 = st.columns(2)
                n_tipo = col_c1.selectbox("Tipo de Conta", ["👤 Profissional", "🏢 Comércio/Loja"], 
                                         index=0 if d.get('tipo') == "👤 Profissional" else 1)
                n_catalogo = col_c2.text_input("Link do Catálogo/Instagram", d.get('link_catalogo', ''))

                col_h1, col_h2 = st.columns(2)
                n_h_abre = col_h1.text_input("Horário Abre (ex: 08:00)", d.get('h_abre', '08:00'))
                n_h_fecha = col_h2.text_input("Horário Fecha (ex: 18:00)", d.get('h_fecha', '18:00'))
                
                st.markdown("---")
                col_f3, col_f4 = st.columns(2)
                n_foto = col_f3.file_uploader("Trocar Foto de Perfil", type=['jpg', 'png', 'jpeg'])
                n_portfolio = col_f4.file_uploader("Vitrine (Até 3 fotos)", type=['jpg', 'png', 'jpeg'], accept_multiple_files=True)
                
                if st.form_submit_button("SALVAR TODAS AS ALTERAÇÕES", use_container_width=True):
                    up = {
                        "nome": n_nome,
                        "area": n_area,
                        "descricao": n_desc,
                        "tipo": n_tipo,
                        "link_catalogo": n_catalogo,
                        "h_abre": n_h_abre,
                        "h_fecha": n_h_fecha
                    }
                    
                    if n_foto:
                        up["foto_url"] = f"data:image/png;base64,{converter_img_b64(n_foto)}"
                    
                    if n_portfolio:
                        lista_b64 = []
                        for foto in n_portfolio[:3]:
                            img_str = converter_img_b64(foto)
                            if img_str:
                                lista_b64.append(f"data:image/png;base64,{img_str}")
                        up["portfolio_imgs"] = lista_b64
                    
                    doc_ref.update(up)
                    st.success("✅ Vitrine atualizada com sucesso!")
                    time.sleep(1)
                    st.rerun()

        if st.button("SAIR DO PAINEL", use_container_width=True):
            st.session_state.auth = False
            st.rerun()

# ==============================================================================
# ABA 3: ADMIN (TERMINAL DE ADMINISTRAÇÃO SUPREMO)
# ==============================================================================
with menu_abas[3]:
    st.markdown("### 🔒 Terminal de Administração")
    access_adm = st.text_input("Senha Master", type="password", key="adm_auth_final")
    
    if access_adm != CHAVE_ADMIN:
        if access_adm != "":
            st.error("🚫 Acesso negado. Senha incorreta.")
        else:
            st.info("Aguardando chave master para liberar sistemas...")
        st.stop() 

    st.success("👑 Acesso Autorizado! Bem-vindo ao Painel Supremo.")
    
    all_profs_lista = list(db.collection("profissionais").stream())
    total_cadastros = len(all_profs_lista)
    pendentes_lista = [p for p in all_profs_lista if not p.to_dict().get('aprovado', False)]
    total_moedas = sum([p.to_dict().get('saldo', 0) for p in all_profs_lista])
    total_cliques = sum([p.to_dict().get('cliques', 0) for p in all_profs_lista])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Moedas", f"{total_moedas} 🪙")
    c2.metric("📈 Parceiros", total_cadastros)
    c3.metric("🤝 Cliques", total_cliques)
    c4.metric("🟡 Pendentes", len(pendentes_lista), delta_color="inverse")
    
    st.divider()

    t_gestao, t_aprova, t_seguranca, t_feed = st.tabs([
        "👥 GESTÃO DE ATIVOS", "🆕 NOVOS (APROVAÇÃO)", "🛡️ SEGURANÇA IA", "📩 FEEDBACKS"
    ])

    with t_gestao:
        search_pro = st.text_input("🔍 Buscar parceiro por Nome ou WhatsApp", placeholder="Ex: João ou 11999...")
        for p_doc in all_profs_lista:
            p, pid = p_doc.to_dict(), p_doc.id
            if not search_pro or search_pro.lower() in p.get('nome', '').lower() or search_pro in pid:
                status_cor = "🟢" if p.get('aprovado') else "🟡"
                with st.expander(f"{status_cor} {p.get('nome', 'Sem Nome').upper()} | {p.get('area')}"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"**WhatsApp/ID:** {pid}")
                        st.write(f"**Saldo Atual:** {p.get('saldo', 0)} moedas")
                        
                        is_verif = p.get('verificado', False)
                        if st.toggle("Selo Verificado", value=is_verif, key=f"tgl_{pid}"):
                            if not is_verif: 
                                db.collection("profissionais").document(pid).update({"verificado": True})
                                st.rerun()
                        else:
                            if is_verif: 
                                db.collection("profissionais").document(pid).update({"verificado": False})
                                st.rerun()
                    
                    with col_b:
                        bonus = st.number_input("Adicionar Moedas", value=0, key=f"num_{pid}")
                        if st.button("💰 CREDITAR", key=f"cbtn_{pid}", use_container_width=True):
                            db.collection("profissionais").document(pid).update({"saldo": p.get('saldo', 0) + bonus})
                            st.success("Creditado!")
                            time.sleep(0.5)
                            st.rerun()
                        
                        if st.button("🗑️ BANIR/REMOVER", key=f"del_{pid}", use_container_width=True):
                            db.collection("profissionais").document(pid).delete()
                            st.error("Removido!")
                            time.sleep(0.5)
                            st.rerun()

    with t_aprova:
        if not pendentes_lista:
            st.info("Nenhum cadastro pendente.")
        else:
            for p_doc in pendentes_lista:
                p, pid = p_doc.to_dict(), p_doc.id
                st.warning(f"SOLICITAÇÃO: {p.get('nome')} ({p.get('area')})")
                if st.button(f"✅ APROVAR {p.get('nome').upper()}", key=f"ok_{pid}"):
                    db.collection("profissionais").document(pid).update({"aprovado": True, "saldo": 10})
                    st.success("Aprovado com bônus!")
                    time.sleep(0.5)
                    st.rerun()

    with t_seguranca:
        st.markdown("#### 🛡️ Central de Proteção e Auto-Cura")
        s_col1, s_col2 = st.columns(2)
        if s_col1.button("🔍 ESCANEAR AMEAÇAS", use_container_width=True):
            alertas = scan_virus_e_scripts()
            for a in alertas: st.write(a)
            
        if s_col2.button("🛠️ REPARAR BANCO", use_container_width=True):
            reparos = guardia_escanear_e_corrigir()
            for r in reparos: st.write(r)
            st.balloons()

    with t_feed:
        try:
            feedbacks = list(db.collection("feedbacks").order_by("data", direction=firestore.Query.DESCENDING).limit(20).stream())
            if feedbacks:
                for f in feedbacks:
                    df = f.to_dict()
                    data_bruta = df.get('data', 'Sem data')
                    data_txt = str(data_bruta)[:10] 
                    
                    nota = df.get('nota', 'S/N')
                    msg = df.get('mensagem', '')
                    
                    st.markdown(f"""
                        <div style="background-color: #f0f2f6; padding: 10px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #0047AB;">
                            <small>📅 {data_txt}</small><br>
                            <b>⭐ {nota}</b><br>
                            <p style="margin:0;">{msg}</p>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Nenhuma nova mensagem na caixa de entrada.")
        except Exception as e:
            st.error(f"Erro ao carregar mensagens: {e}")

# ==============================================================================
# ABA 4: FEEDBACK (PÚBLICO)
# ==============================================================================
with menu_abas[4]:
    st.markdown("### ⭐ Sua opinião é fundamental")
    st.write("Conte-nos como foi a sua experiência com o GeralJá.")
    
    with st.form("feedback_form", clear_on_submit=True):
        nota = st.select_slider(
            "Qual a sua satisfação geral?",
            options=["Muito Insatisfeito", "Insatisfeito", "Regular", "Satisfeito", "Muito Satisfeito"],
            value="Muito Satisfeito"
        )
        
        comentario = st.text_area(
            "Descreva a sua experiência ou deixe uma sugestão:",
            placeholder="Ex: O profissional foi muito atencioso...",
            height=150
        )
        
        btn_enviar = st.form_submit_button("ENVIAR AVALIAÇÃO", use_container_width=True)
        
        if btn_enviar:
            if comentario.strip() != "":
                try:
                    agora = datetime.datetime.now()
                    data_string = agora.strftime("%Y-%m-%d %H:%M:%S")
                    
                    db.collection("feedbacks").add({
                        "data": data_string,
                        "nota": nota,
                        "mensagem": comentario,
                        "lido": False
                    })
                    st.success("🙏 Muito obrigado! Sua mensagem foi enviada.")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro ao enviar: {e}")
            else:
                st.warning("⚠️ Por favor, escreva algo antes de enviar.")

# ==============================================================================
# ABA 5: FINANCEIRO (COMANDO SELETO)
# ==============================================================================
if len(menu_abas) > 5:
    with menu_abas[5]:
        st.markdown("### 📊 Gestão de Capital GeralJá")
        senha_cofre = st.text_input("Chave do Cofre", type="password", key="cofre_vFinal")
        
        if senha_cofre == "riqueza2025":
            all_p = list(db.collection("profissionais").stream())
            vendas = sum([p.to_dict().get('total_comprado', 0) for p in all_p])
            
            c1, c2 = st.columns(2)
            c1.metric("💰 FATURAMENTO REAL", f"R$ {vendas:,.2f}")
            c2.metric("🤝 TOTAL PARCEIROS", len(all_p))
            
            st.divider()
            st.write("**Histórico de Vendas:**")
            tabela = [{"Profissional": p.to_dict().get('nome'), "Total Pago": p.to_dict().get('total_comprado', 0)} for p in all_p]
            st.dataframe(pd.DataFrame(tabela), use_container_width=True)
        else:
            st.info("Aguardando chave mestra para exibir dados sensíveis.")

# ------------------------------------------------------------------------------
# RODAPÉ
# ------------------------------------------------------------------------------
try:
    ano_atual = datetime.datetime.now().year
except:
    ano_atual = 2026

st.markdown(f'<div style="text-align:center; padding:20px; color:#94A3B8; font-size:10px;">GERALJÁ v20.0 © {ano_atual}</div>', unsafe_allow_html=True)
