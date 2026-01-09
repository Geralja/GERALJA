# ==============================================================================
# GERALJÁ: SISTEMA DE INTELIGÊNCIA LOCAL (v2.0) - BLINDADO
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
from groq import Groq  
from PIL import Image  
import io

# 1. CONFIGURAÇÃO ÚNICA (Deve ser a primeira linha Streamlit)
st.set_page_config(page_title="GeralJá | Criando Soluções", page_icon="🎯", layout="wide")

# 2. FUNÇÕES DE UTILIDADE (Soma de tudo que você pediu)
def remover_acentos(texto):
    if not texto: return ""
    return "".join(c for c in unicodedata.normalize('NFD', texto)
                  if unicodedata.category(c) != 'Mn').lower()

def converter_img_b64(file):
    """Soma a PIL para reduzir fotos e base64 para o banco"""
    if file is not None:
        try:
            img = Image.open(file)
            img.thumbnail((600, 600)) 
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=80)
            return base64.b64encode(buffer.getvalue()).decode()
        except Exception as e:
            st.error(f"Erro na imagem: {e}")
    return None

def injetar_estilo_visual():
    """Soma o corretor de modo claro/escuro e limpa o layout"""
    st.markdown("""
        <style>
            #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {display: none !important;}
            .stApp { background-color: white !important; }
            * { color: black !important; }
            [data-testid="stExpander"], input, textarea {
                background-color: #ffffff !important; border: 1px solid #ddd !important; color: black !important;
            }
        </style>
    """, unsafe_allow_html=True)

# 3. CONEXÕES (Soma de Firebase + Groq via Secrets)
@st.cache_resource
def inicializar_conexoes():
    # Firebase
    if not firebase_admin._apps:
        fb_json = json.loads(base64.b64decode(st.secrets["FIREBASE_BASE64"]).decode('utf-8'))
        firebase_admin.initialize_app(credentials.Certificate(fb_json))
    
    # Groq IA
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    return firestore.client(), groq_client

db, ai_engine = inicializar_conexoes()
injetar_estilo_visual()

# 4. POLÍTICAS E CATEGORIAS (Manteve o que é essencial)
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CATEGORIAS_OFICIAIS = [
    "Academia", "Açougue", "Adega", "Ajudante Geral", "Assistência Técnica", 
    "Barbearia/Salão", "Carreto", "Chaveiro", "Confeiteiro(a)", "Diarista / Faxineira", 
    "Eletricista", "Encanador", "Lanchonete", "Mecânico de Autos", "Montador de Móveis", 
    "Pedreiro", "Pet Shop", "Pintor", "Pizzaria", "Técnico de Celular"
] # Reduzi aqui para exemplo, mas você pode manter sua lista completa.
# ==============================================================================
# 2. CAMADA DE PERSISTÊNCIA (FIREBASE) - VERSÃO CORREÇÃO CRÍTICA
# ==============================================================================
@st.cache_resource
def conectar_banco_master():
    if not firebase_admin._apps:
        try:
            # Tenta pegar dos Secrets, se não achar, avisa sem travar tudo
            if "FIREBASE_BASE64" not in st.secrets:
                st.error("⚠️ Configuração Incompleta: FIREBASE_BASE64 não encontrada nos Secrets.")
                st.stop()
            
            b64_key = st.secrets["FIREBASE_BASE64"]
            decoded_json = base64.b64decode(b64_key).decode("utf-8")
            cred_dict = json.loads(decoded_json)
            cred = credentials.Certificate(cred_dict)
            return firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"❌ Erro de Conexão: {e}")
            st.stop()
    return firebase_admin.get_app()

# Inicializa o banco
try:
    app_engine = conectar_banco_master()
    db = firestore.client()
except:
    st.warning("Aguardando conexão com o banco de dados...")

# --- INICIALIZAÇÃO DA GROQ (IA) ---
try:
    if "GROQ_API_KEY" in st.secrets:
        ai_engine = Groq(api_key=st.secrets["GROQ_API_KEY"])
    else:
        ai_engine = None
except Exception as e:
    ai_engine = None
    st.info("Nota: O motor de busca inteligente está em modo básico.")
# ------------------------------------------------------------------------------
# 4. MOTORES DE IA E GEOLOCALIZAÇÃO
# ------------------------------------------------------------------------------
def normalizar_para_ia(texto):
    if not texto: return ""
    return "".join(c for c in unicodedata.normalize('NFD', str(texto)) 
                  if unicodedata.category(c) != 'Mn').lower().strip()

def processar_ia_avancada(texto):
    if not texto: return "Vazio"
    t_clean = normalizar_para_ia(texto)
    
    # 1. Busca exata no dicionário de conceitos (Pizzaria, Mecânico, etc.)
    for chave, categoria in CONCEITOS_EXPANDIDOS.items():
        chave_norm = normalizar_para_ia(chave)
        if re.search(rf"\b{chave_norm}\b", t_clean):
            return categoria
            
    # 2. Verifica se o usuário digitou exatamente uma categoria oficial
    for cat in CATEGORIAS_OFICIAIS:
        if normalizar_para_ia(cat) in t_clean:
            return cat
            
    # 3. MUDANÇA AQUI: Se não encontrar NADA, retorna um termo que force o "vazio"
    # Isso fará com que o app mostre sua frase de compartilhamento!
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
    """
    Gera um link de notificação para o Admin. 
    Nota: Para automação 100% invisível, seria necessária uma API paga (como Twilio ou Z-API).
    Esta versão gera um log e um alerta visual imediato no painel.
    """
    msg_alerta = f"🚀 *NOVO CADASTRO NO GERALJÁ*\n\n" \
                 f"👤 *Nome:* {nome_prof}\n" \
                 f"🛠️ *Área:* {categoria_prof}\n" \
                 f"📱 *Zap:* {whatsapp_prof}\n\n" \
                 f"Acesse o Painel Admin para aprovar!"
    
    # Codifica a mensagem para URL
    msg_encoded = msg_alerta.replace('\n', '%0A').replace(' ', '%20')
    link_zap_admin = f"https://wa.me/{ZAP_ADMIN}?text={msg_encoded}"
    
    return link_zap_admin
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

# 1. Defina a lista básica
lista_abas = ["🔍 BUSCAR", "🚀 CADASTRAR", "👤 MEU PERFIL", "👑 ADMIN", "⭐ FEEDBACK"]

# 2. Verifique o comando secreto na barra lateral
comando = st.sidebar.text_input("Comando Secreto", type="password")

# 3. Se o comando estiver certo, soma a aba financeira
if comando == "abracadabra":
    lista_abas.append("📊 FINANCEIRO")

# 4. Cria as abas no Streamlit
menu_abas = st.tabs(lista_abas)

# --- ABA 1: BUSCA (SISTEMA GPS + RANKING ELITE + VITRINE) ---
with menu_abas[0]:
    st.markdown("### 🏙️ O que você precisa?")
    
    # --- MOTOR DE LOCALIZAÇÃO EM TEMPO REAL ---
    with st.expander("📍 Sua Localização (GPS)", expanded=False):
        loc = get_geolocation()
        if loc:
            minha_lat = loc['coords']['latitude']
            minha_lon = loc['coords']['longitude']
            st.success(f"Localização detectada!")
        else:
            minha_lat = LAT_REF
            minha_lon = LON_REF
            st.warning("GPS desativado. Usando localização padrão (SP).")

    c1, c2 = st.columns([3, 1])
    termo_busca = c1.text_input("Ex: 'Cano estourado' ou 'Pizza'", key="main_search")
    raio_km = c2.select_slider("Raio (KM)", options=[1, 3, 5, 10, 20, 50, 100, 500, 2000], value=10)
    
    if termo_busca:
        # Processamento via IA para identificar a categoria
        cat_ia = processar_ia_avancada(termo_busca)
        st.info(f"✨ IA: Buscando por **{cat_ia}** próximo a você")
        
        # Lógica de Horário em tempo real
        from datetime import datetime
        import pytz
        import re
        from urllib.parse import quote
        
        fuso = pytz.timezone('America/Sao_Paulo')
        hora_atual = datetime.now(fuso).strftime('%H:%M')

        # Busca no Firebase (Filtra apenas aprovados e da categoria certa)
        profs = db.collection("profissionais").where("area", "==", cat_ia).where("aprovado", "==", True).stream()
        
        lista_ranking = []
        for p_doc in profs:
            p = p_doc.to_dict()
            p['id'] = p_doc.id
            
            # CALCULA DISTÂNCIA REAL (GPS vs Profissional)
            dist = calcular_distancia_real(minha_lat, minha_lon, p.get('lat', LAT_REF), p.get('lon', LON_REF))
            
            if dist <= raio_km:
                p['dist'] = dist
                # MOTOR DE SCORE ELITE (Ranking)
                score = 0
                score += 500 if p.get('verificado', False) else 0
                score += (p.get('saldo', 0) * 10)
                score += (p.get('rating', 5) * 20)
                p['score_elite'] = score
                lista_ranking.append(p)

        # Ordenação: Elite primeiro (maior score), depois os mais próximos (menor distância)
        lista_ranking.sort(key=lambda x: (-x['score_elite'], x['dist']))

        if not lista_ranking:
            st.markdown(f"""
            <div style="background-color: #FFF4E5; padding: 20px; border-radius: 15px; border-left: 5px solid #FF8C00;">
                <h3 style="color: #856404;">🔍 Essa profissão ainda não foi preenchida nesta região.</h3>
                <p style="color: #856404;">Compartilhe o <b>GeralJá</b> e ajude a crescer sua rede local!</p>
            </div>
            """, unsafe_allow_html=True)
            
            link_share = "https://wa.me/?text=Ei!%20Procurei%20um%20serviço%20no%20GeralJá%20e%20vi%20que%20ainda%20temos%20vagas!%20Cadastre-se:%20https://geralja.streamlit.app"
            st.markdown(f'<a href="{link_share}" target="_blank" style="text-decoration:none;"><div style="background:#22C55E; color:white; padding:15px; border-radius:10px; text-align:center; font-weight:bold; margin-top:10px;">📲 COMPARTILHAR NO WHATSAPP</div></a>', unsafe_allow_html=True)
        
        else:
            # --- RENDERIZAÇÃO DOS CARDS (LOOP) ---
            for p in lista_ranking:
                pid = p['id']
                is_elite = p.get('verificado') and p.get('saldo', 0) > 0
                
                with st.container():
                    # Cores dinâmicas baseadas no tipo de conta
                    cor_borda = "#FFD700" if is_elite else ("#FF8C00" if p.get('tipo') == "🏢 Comércio/Loja" else "#0047AB")
                    bg_card = "#FFFDF5" if is_elite else "#FFFFFF"
                    
                    st.markdown(f"""
                    <div style="border-left: 8px solid {cor_borda}; padding: 15px; background: {bg_card}; border-radius: 15px; margin-bottom: 5px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                        <span style="font-size: 12px; color: gray; font-weight: bold;">📍 a {p['dist']:.1f} km de você {" | 🏆 DESTAQUE" if is_elite else ""}</span>
                    </div>
                    """, unsafe_allow_html=True)

                    col_img, col_txt = st.columns([1, 4])
                    with col_img:
                        foto = p.get('foto_url', 'https://via.placeholder.com/150')
                        st.markdown(f'<img src="{foto}" style="width:75px; height:75px; border-radius:50%; object-fit:cover; border:3px solid {cor_borda}">', unsafe_allow_html=True)
                    
                    with col_txt:
                        nome_exibicao = p.get('nome', '').upper()
                        if p.get('verificado', False): nome_exibicao += " <span style='color:#1DA1F2;'>☑️</span>"
                        
                        status_loja = ""
                        if p.get('tipo') == "🏢 Comércio/Loja":
                            h_ab, h_fe = p.get('h_abre', '08:00'), p.get('h_fecha', '18:00')
                            status_loja = " 🟢 <b style='color:green;'>ABERTO</b>" if h_ab <= hora_atual <= h_fe else " 🔴 <b style='color:red;'>FECHADO</b>"
                        
                        st.markdown(f"**{nome_exibicao}** {status_loja}", unsafe_allow_html=True)
                        st.caption(f"{p.get('descricao', '')[:120]}...")

                    # Vitrine de Fotos do Portfólio
                    if p.get('portfolio_imgs'):
                        cols_v = st.columns(3)
                        for i, img_b64 in enumerate(p.get('portfolio_imgs')[:3]):
                            cols_v[i].image(img_b64, use_container_width=True)

                    # --- LÓGICA DO BOTÃO DE WHATSAPP (AQUI DENTRO DO LOOP) ---
                    nome_curto = p.get('nome', 'Profissional').split()[0].upper()
                    
                    # Limpeza do número de telefone (ID do documento)
                    numero_limpo = re.sub(r'\D', '', str(pid))
                    if not numero_limpo.startswith('55'):
                        numero_limpo = f"55{numero_limpo}"
                    
                    texto_zap = quote(f"Olá {p.get('nome')}, vi seu perfil no GeralJá!")
                    link_final = f"https://wa.me/{numero_limpo}?text={texto_zap}"

                    # --- BOTÃO ÚNICO (VISUAL TOP + ABRE SEMPRE) ---
                    import re
                    from urllib.parse import quote
                    
                    # 1. Preparação dos dados
                    num_limpo = re.sub(r'\D', '', str(pid))
                    if not num_limpo.startswith('55'): num_limpo = f"55{num_limpo}"
                    texto_zap = quote(f"Olá {p.get('nome')}, vi seu perfil no GeralJá!")
                    link_final = f"https://wa.me/{num_limpo}?text={texto_zap}"
                    nome_btn = p.get('nome', 'Profissional').split()[0].upper()
                    
                    # 2. BOTÃO HTML (Ocupa o lugar do st.button)
                    # Este botão abre o WhatsApp instantaneamente e não é bloqueado
                    st.markdown(f"""
                        <a href="{link_final}" target="_blank" style="text-decoration: none;">
                            <div style="
                                background-color: #25D366;
                                color: white;
                                padding: 15px;
                                border-radius: 12px;
                                text-align: center;
                                font-weight: bold;
                                font-size: 18px;
                                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                                transition: 0.3s;
                                cursor: pointer;
                                margin-top: 10px;
                            ">
                                💬 FALAR COM {nome_btn}
                            </div>
                        </a>
                    """, unsafe_allow_html=True)
                    
                    # 3. LÓGICA DE DÉBITO E SEGURANÇA
                # Verifica se tem saldo antes de processar
                if p.get('saldo', 0) <= 0:
                    continue  # <--- AGORA ESTÁ DENTRO DO IF (4 espaços)

                # Se passou pelo if acima, registra o clique/visualização
                db.collection("profissionais").document(pid).update({
                    "cliques": p.get('cliques', 0) + 1
                })
# --- ABA 2: PAINEL DO PARCEIRO (VERSÃO COM TEMA MANUAL) ---
with menu_abas[2]:
    if 'auth' not in st.session_state: st.session_state.auth = False
    
    if not st.session_state.auth:
        st.subheader("🚀 Acesso ao Painel")
        col1, col2 = st.columns(2)
        l_zap = col1.text_input("WhatsApp (números)", key="login_zap_v7")
        l_pw = col2.text_input("Senha", type="password", key="login_pw_v7")
        
        if st.button("ENTRAR NO PAINEL", use_container_width=True, key="btn_entrar_v7"):
            u = db.collection("profissionais").document(l_zap).get()
            if u.exists and u.to_dict().get('senha') == l_pw:
                st.session_state.auth, st.session_state.user_id = True, l_zap
                st.rerun()
            else: st.error("Dados incorretos.")
    else:
        doc_ref = db.collection("profissionais").document(st.session_state.user_id)
        d = doc_ref.get().to_dict()
        
        # 1. MÉTRICAS (Usando colunas nativas para evitar conflito de CSS)
        st.write(f"### Olá, {d.get('nome', 'Parceiro')}!")
        m1, m2, m3 = st.columns(3)
        m1.metric("Saldo 🪙", f"{d.get('saldo', 0)}")
        m2.metric("Cliques 🚀", f"{d.get('cliques', 0)}")
        m3.metric("Status", "🟢 ATIVO" if d.get('aprovado') else "🟡 PENDENTE")

        # 2. GPS (Função preservada)
        if st.button("📍 ATUALIZAR LOCALIZAÇÃO GPS", use_container_width=True, key="gps_v7"):
            loc = streamlit_js_eval(js_expressions="navigator.geolocation.getCurrentPosition(s => s)", key='gps_v7_eval')
            if loc and 'coords' in loc:
                doc_ref.update({"lat": loc['coords']['latitude'], "lon": loc['coords']['longitude']})
                st.success("✅ Localização salva!")
            else: st.info("Aguardando sinal... Clique novamente.")

        st.divider()

        # 3. COMPRA DE MOEDAS (PIX - Variáveis oficiais preservadas)
        with st.expander("💎 COMPRAR MOEDAS (PIX)", expanded=False):
            st.warning(f"Chave PIX: {PIX_OFICIAL}")
            c1, c2, c3 = st.columns(3)
            if c1.button("10 Moedas", key="p10_v7"): st.code(PIX_OFICIAL)
            if c2.button("50 Moedas", key="p50_v7"): st.code(PIX_OFICIAL)
            if c3.button("100 Moedas", key="p100_v7"): st.code(PIX_OFICIAL)
            
            st.link_button("🚀 ENVIAR COMPROVANTE AGORA", f"https://wa.me/{ZAP_ADMIN}?text=Fiz o PIX: {st.session_state.user_id}", use_container_width=True)

        # 4. EDIÇÃO DE PERFIL (FOTOS, HORÁRIOS E SEGMENTO)
        with st.expander("📝 EDITAR MEU PERFIL & VITRINE", expanded=True):
            with st.form("perfil_v7"):
                n_nome = st.text_input("Nome Profissional", d.get('nome', ''))
                
                # --- VOLTANDO A FUNÇÃO DE MUDAR SEGMENTO ---
                # Procura a categoria atual na lista para deixar selecionada
                try:
                    index_cat = CATEGORIAS_OFICIAIS.index(d.get('area', 'Ajudante Geral'))
                except:
                    index_cat = 0
                n_area = st.selectbox("Mudar meu Segmento/Área", CATEGORIAS_OFICIAIS, index=index_cat)
                # ------------------------------------------

                n_desc = st.text_area("Descrição", d.get('descricao', ''))
                n_cat = st.text_input("Link Catálogo/Instagram", d.get('link_catalogo', ''))
                
                h1, h2 = st.columns(2)
                n_abre = h1.text_input("Abre às (ex: 08:00)", d.get('h_abre', '08:00'))
                n_fecha = h2.text_input("Fecha às (ex: 18:00)", d.get('h_fecha', '18:00'))
                
                n_foto = st.file_uploader("Trocar Foto Perfil", type=['jpg','png','jpeg'], key="f_v7")
                n_portfolio = st.file_uploader("Vitrine (Até 3 fotos)", type=['jpg','png','jpeg'], accept_multiple_files=True, key="p_v7")
                
                if st.form_submit_button("SALVAR ALTERAÇÕES", use_container_width=True):
                    # Adicionei 'area' no dicionário de update
                    up = {
                        "nome": n_nome, 
                        "area": n_area, # <--- Agora ele salva a nova categoria!
                        "descricao": n_desc, 
                        "link_catalogo": n_cat, 
                        "h_abre": n_abre, 
                        "h_fecha": n_fecha
                    }
                    
                    if n_foto: 
                        up["foto_url"] = f"data:image/png;base64,{converter_img_b64(n_foto)}"
                    
                    if n_portfolio:
                        up["portfolio_imgs"] = [f"data:image/png;base64,{converter_img_b64(f)}" for f in n_portfolio[:3]]
                    
                    doc_ref.update(up)
                    st.success("✅ Perfil e Segmento atualizados com sucesso!")
                    time.sleep(1) # Pequena pausa para o usuário ver a mensagem
                    st.rerun()
# --- ABA 1: CADASTRAR (SISTEMA DE ADMISSÃO DE ELITE) ---
with menu_abas[1]:
    st.markdown("### 🚀 Cadastro de Profissional")
    st.info("Preencha os dados abaixo para entrar no ecossistema GeralJá.")

    # Início do Formulário - O 'with' garante que tudo aqui dentro pertença ao botão de salvar
    with st.form("form_novo_profissional", clear_on_submit=False):
        col_id1, col_id2 = st.columns(2)
        nome_input = col_id1.text_input("Nome do Profissional ou Loja", placeholder="Ex: João Mecânico")
        zap_input = col_id2.text_input("WhatsApp (DDD + Número)", placeholder="Ex: 11991853488")
        
        col_id3, col_id4 = st.columns(2)
        categoria_input = col_id3.selectbox("Sua Área Principal", CATEGORIAS_OFICIAIS)
        senha_input = col_id4.text_input("Crie uma Senha", type="password", help="Para editar seu perfil depois")
        
        descricao_input = st.text_area("Descrição do Serviço", placeholder="Conte o que você faz, diferenciais e experiência...")
        
        tipo_input = st.radio("Tipo de Cadastro", ["👨‍🔧 Profissional Autônomo", "🏢 Comércio/Loja"], horizontal=True)
        
        foto_upload = st.file_uploader("Foto de Perfil ou Logo", type=['jpg', 'jpeg', 'png'])

        st.markdown("---")
        st.caption("📍 A sua localização atual será capturada automaticamente para te mostrar nos resultados próximos aos clientes.")
        
        # O BOTÃO DE SALVAR PRECISA ESTAR AQUI DENTRO DO FORM
        btn_finalizar = st.form_submit_button("✅ FINALIZAR E SALVAR CADASTRO", use_container_width=True)

    # Lógica que acontece APÓS o clique no botão
    if btn_finalizar:
        if not nome_input or not zap_input or not senha_input:
            st.error("⚠️ ERRO: Nome, WhatsApp e Senha são obrigatórios!")
        else:
            with st.spinner("Conectando ao banco de dados..."):
                try:
                    # 1. Processamento da Imagem
                    foto_final = ""
                    if foto_upload:
                        foto_final = f"data:image/png;base64,{converter_img_b64(foto_upload)}"
                    
                    # 2. Garantia de Localização (Se o GPS falhar, usa a LAT_REF/LON_REF que você definiu)
                    # Use as variáveis que o seu script já detectou no topo da página
                    lat_salvar = minha_lat if 'minha_lat' in locals() else LAT_REF
                    lon_salvar = minha_lon if 'minha_lon' in locals() else LON_REF

                    # 3. Montagem do Objeto (Sem apagar nada do que você já usa)
                    novo_pro = {
                        "nome": nome_input,
                        "area": categoria_input,
                        "descricao": descricao_input,
                        "senha": senha_input,
                        "tipo": tipo_input,
                        "whatsapp": zap_input,
                        "foto_url": foto_final,
                        "saldo": BONUS_WELCOME, # Dá os 5 créditos iniciais
                        "aprovado": True,        # Já nasce ativo conforme seu fluxo
                        "verificado": False,
                        "cliques": 0,
                        "rating": 5,
                        "lat": lat_salvar,
                        "lon": lon_salvar,
                        "data_cadastro": datetime.datetime.now().strftime("%d/%m/%Y")
                    }

                    # 4. Envio para o Firestore usando o WhatsApp como ID (Evita duplicados)
                    db.collection("profissionais").document(zap_input).set(novo_pro)
                    
                    st.balloons()
                    st.success(f"🎊 BEM-VINDO, {nome_input.upper()}! Seu cadastro foi concluído com sucesso.")
                    st.info("💡 DICA: Vá na aba '👤 MEU PERFIL' para fazer login e ver seu saldo de moedas.")
                    
                    # Alerta para o Admin (Usando sua função existente)
                    link_admin = enviar_alerta_admin(nome_input, categoria_input, zap_input)
                    st.markdown(f'[📢 Avisar Administração via WhatsApp]({link_admin})')

                except Exception as e:
                    st.error(f"❌ Erro técnico ao salvar: {e}")
with menu_abas[3]:
    st.markdown("### 🔒 Terminal de Administração")
    access_adm = st.text_input("Senha Master", type="password", key="adm_auth_final")
    
    # BLOQUEIO DE SEGURANÇA REFORÇADO
    if access_adm != CHAVE_ADMIN:
        if access_adm != "":
            st.error("🚫 Acesso negado. Senha incorreta.")
        else:
            st.info("Aguardando chave master para liberar sistemas...")
        st.stop() 

    # --- DAQUI PARA BAIXO TUDO ESTÁ PROTEGIDO PELA SENHA ---
    st.success("👑 Acesso Autorizado! Bem-vindo ao Painel Supremo.")
    
    # 1. BUSCA DE DADOS E TELEMETRIA
    all_profs_lista = list(db.collection("profissionais").stream())
    total_cadastros = len(all_profs_lista)
    pendentes_lista = [p for p in all_profs_lista if not p.to_dict().get('aprovado', False)]
    total_moedas = sum([p.to_dict().get('saldo', 0) for p in all_profs_lista])
    total_cliques = sum([p.to_dict().get('cliques', 0) for p in all_profs_lista])

    # Painel de Indicadores
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Moedas", f"{total_moedas} 🪙")
    c2.metric("📈 Parceiros", total_cadastros)
    c3.metric("🤝 Cliques", total_cliques)
    c4.metric("🟡 Pendentes", len(pendentes_lista), delta_color="inverse")
    
    st.divider()

    # 2. ABAS DE COMANDO INTERNAS
    t_gestao, t_aprova, t_seguranca, t_feed = st.tabs([
        "👥 GESTÃO DE ATIVOS", "🆕 NOVOS (APROVAÇÃO)", "🛡️ SEGURANÇA IA", "📩 FEEDBACKS"
    ])

    # --- ABA INTERNA: GESTÃO DE ATIVOS (BUSCA E EDIÇÃO) ---
    with t_gestao:
        search_pro = st.text_input("🔍 Buscar parceiro por Nome ou WhatsApp", placeholder="Ex: João ou 11999...")
        for p_doc in all_profs_lista:
            p, pid = p_doc.to_dict(), p_doc.id
            # Filtro de Busca
            if not search_pro or search_pro.lower() in p.get('nome', '').lower() or search_pro in pid:
                status_cor = "🟢" if p.get('aprovado') else "🟡"
                with st.expander(f"{status_cor} {p.get('nome', 'Sem Nome').upper()} | {p.get('area')}"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"**WhatsApp/ID:** {pid}")
                        st.write(f"**Saldo Atual:** {p.get('saldo', 0)} moedas")
                        
                        # Controle de Verificado (Selo)
                        is_verif = p.get('verificado', False)
                        if st.toggle("Selo Verificado", value=is_verif, key=f"tgl_{pid}"):
                            if not is_verif: db.collection("profissionais").document(pid).update({"verificado": True}); st.rerun()
                        else:
                            if is_verif: db.collection("profissionais").document(pid).update({"verificado": False}); st.rerun()
                    
                    with col_b:
                        # Adicionar Moedas
                        bonus = st.number_input("Adicionar Moedas", value=0, key=f"num_{pid}")
                        if st.button("💰 CREDITAR", key=f"cbtn_{pid}", use_container_width=True):
                            db.collection("profissionais").document(pid).update({"saldo": p.get('saldo', 0) + bonus})
                            st.success("Creditado!"); time.sleep(0.5); st.rerun()
                        
                        if st.button("🗑️ BANIR/REMOVER", key=f"del_{pid}", use_container_width=True):
                            db.collection("profissionais").document(pid).delete()
                            st.error("Removido!"); time.sleep(0.5); st.rerun()

    # --- ABA INTERNA: FILA DE APROVAÇÃO ---
    with t_aprova:
        if not pendentes_lista:
            st.info("Nenhum cadastro pendente.")
        else:
            for p_doc in pendentes_lista:
                p, pid = p_doc.to_dict(), p_doc.id
                st.warning(f"SOLICITAÇÃO: {p.get('nome')} ({p.get('area')})")
                if st.button(f"✅ APROVAR {p.get('nome').upper()}", key=f"ok_{pid}"):
                    db.collection("profissionais").document(pid).update({"aprovado": True, "saldo": 10})
                    st.success("Aprovado com bônus!"); time.sleep(0.5); st.rerun()

    # --- ABA INTERNA: SEGURANÇA IA ---
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

# --- ABA INTERNA: FEEDBACKS (DENTRO DA CENTRAL DE COMANDO) ---
    with t_feed:
        try:
            feedbacks = list(db.collection("feedbacks").order_by("data", direction="DESCENDING").limit(20).stream())
            if feedbacks:
                for f in feedbacks:
                    df = f.to_dict()
                    
                    # CORREÇÃO DO ERRO: Converte para string antes de cortar os 10 caracteres
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

    st.divider()
    st.caption("O GeralJá utiliza os seus feedbacks para melhorar a segurança e a qualidade dos prestadores de serviço.")
# --- ABA 6: FINANCEIRO (SÓ APARECE SOB COMANDO) ---
# Este 'if' evita o IndexError: ele só executa se a aba financeira existir
if len(menu_abas) > 5:
    with menu_abas[4]:
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
            # --- ABA: FEEDBACK (A VOZ DO CLIENTE) ---
with menu_abas[4]: # Verifique se o índice da sua aba de feedback é 4 ou 5
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
                    # Salvando com data formatada para evitar erros de leitura
                    agora = datetime.datetime.now()
                    data_string = agora.strftime("%Y-%m-%d %H:%M:%S")
                    
                    db.collection("feedbacks").add({
                        "data": data_string, # Salva como texto padrão
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



















