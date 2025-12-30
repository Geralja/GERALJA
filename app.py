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
    "Encanador", "Eletricista", "Pintor", "Pedreiro", "Gesseiro",
    "Telhadista", "Mecânico", "Borracheiro", "Guincho 24h", "Diarista",
    "Jardineiro", "Piscineiro", "TI", "Refrigeração", "Serralheiro",
    "Montador", "Freteiro", "Chaveiro", "Técnico de Fogão", "Técnico de Lavadora",
    "Ajudante Geral", "Outro (Personalizado)"
]

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

menu_abas = st.tabs(["🔍 BUSCAR", "💼 MEU PERFIL", "📝 CADASTRAR", "🛡️ ADMIN"])

# --- ABA 1: BUSCA ---
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
                lista_ranking.append(p)
        
      # --- LOGICA DE RANKING PREMIUM (SOMA DE PODER) ---
        try:
            # Ordena por: 1º Mais perto, 2º Mais saldo (quem investe mais), 3º Melhor nota
            lista_ranking.sort(key=lambda x: (x['dist'], -x.get('saldo', 0), -x.get('rating', 5.0)))
        except:
            lista_ranking.sort(key=lambda x: x['dist'])

        # --- LOOP DE EXIBIÇÃO DOS CARDS ---
        for pro in lista_ranking:
            with st.container():
                # Preparação segura dos dados para não travar o HTML
                foto_fix = pro.get('foto_url') or f"https://api.dicebear.com/7.x/avataaars/svg?seed={pro['id']}"
                desc_fix = (pro.get('descricao') or "Especialista parceiro GeralJá Brasil.")[:150]
                nome_fix = pro.get('nome', 'Profissional').upper()

                # Card HTML Clean & Professional
                st.markdown(f"""
                <div class="pro-card">
                    <img src="{foto_fix}" class="pro-img">
                    <div style="flex-grow:1;">
                        <small>📍 {pro['dist']} KM | 💎 {pro['area']}</small>
                        <h3 style="margin:5px 0; color:#1E293B;">{nome_fix}</h3>
                        <p style="font-size:14px; color:#475569; margin-bottom:0;">{desc_fix}...</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # --- BLOCO DE DEPOIMENTOS (FOTOS DO PORTFÓLIO) ---
                if pro.get('portfolio_imgs'):
                    with st.expander("📸 Ver fotos de serviços realizados"):
                        cols_fotos = st.columns(3)
                        for i, img_data in enumerate(pro['portfolio_imgs'][:3]):
                            cols_fotos[i%3].image(img_data, use_container_width=True)

                # --- BOTÃO DE CONTATO COM COBRANÇA DE LEAD ---
                if pro.get('saldo', 0) >= TAXA_CONTATO:
                    if st.button(f"FALAR COM {nome_fix.split()[0]}", key=f"z_{pro['id']}", use_container_width=True):
                        # Registra o clique e debita o saldo em tempo real
                        db.collection("profissionais").document(pro['id']).update({
                            "saldo": firestore.Increment(-TAXA_CONTATO),
                            "cliques": firestore.Increment(1)
                        })
                        st.balloons()
                        st.markdown(f'<a href="https://wa.me/55{pro["whatsapp"]}?text=Olá, vi seu perfil no GeralJá!" class="btn-zap">ABRIR WHATSAPP AGORA</a>', unsafe_allow_html=True)
                else:
                    st.warning("⏳ Este profissional atingiu o limite de atendimentos diários.")
# --- ABA 2: CENTRAL PARCEIRO (VERSÃO PORTFÓLIO & BLINDADA) ---
with menu_abas[1]:
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
        # Puxamos os dados atualizados
        doc_ref = db.collection("profissionais").document(st.session_state.user_id)
        d = doc_ref.get().to_dict()
        
        # --- CABEÇALHO DE MÉTRICAS ---
        m1, m2, m3 = st.columns(3)
        m1.markdown(f'<div class="metric-box">SALDO: {d.get("saldo", 0)} 🪙</div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric-box">CLIQUES: {d.get("cliques", 0)} 🚀</div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric-box">STATUS: {"🟢 ATIVO" if d.get("aprovado") else "🟡 PENDENTE"}</div>', unsafe_allow_html=True)
        
        st.divider()
        
        # --- FORMULÁRIO DE EDIÇÃO + PORTFÓLIO ---
        with st.expander("📝 MEU PERFIL & PORTFÓLIO", expanded=True):
            with st.form("ed"):
                col_f1, col_f2 = st.columns(2)
                n_nome = col_f1.text_input("Nome Profissional", d.get('nome'))
                
                try:
                    idx_at = CATEGORIAS_OFICIAIS.index(d.get('area', 'Ajudante Geral'))
                except:
                    idx_at = 0
                
                n_area = col_f2.selectbox("Sua Especialidade", CATEGORIAS_OFICIAIS, index=idx_at)
                n_desc = st.text_area("Descrição (Conte sua experiência)", d.get('descricao', ''), help="Dica: Clientes preferem descrições detalhadas.")
                
                col_f3, col_f4 = st.columns(2)
                n_foto = col_f3.file_uploader("Trocar Foto de Perfil", type=['jpg', 'png', 'jpeg'])
                
                # --- SOMANDO: UPLOAD DE PORTFÓLIO ---
                n_portfolio = col_f4.file_uploader("Portfólio (Até 3 fotos de serviços)", type=['jpg', 'png', 'jpeg'], accept_multiple_files=True)
                
                st.info("💡 Fotos de alta qualidade aumentam suas chances de fechamento em 70%!")

                if st.form_submit_button("SALVAR TODAS AS ALTERAÇÕES", use_container_width=True):
                    up = {
                        "nome": n_nome,
                        "area": n_area,
                        "descricao": n_desc
                    }
                    
                    # Processa Foto de Perfil
                    if n_foto:
                        up["foto_url"] = f"data:image/png;base64,{converter_img_b64(n_foto)}"
                    
                    # Processa Fotos do Portfólio (Soma até 3)
                    if n_portfolio:
                        lista_b64 = []
                        for foto in n_portfolio[:3]:
                            img_b64 = converter_img_b64(foto)
                            if img_b64:
                                lista_b64.append(f"data:image/png;base64,{img_b64}")
                        up["portfolio_imgs"] = lista_b64
                    
                    # Gravação Blindada
                    doc_ref.update(up)
                    st.success("✅ Perfil e Portfólio atualizados com sucesso!")
                    time.sleep(1)
                    st.rerun()

        # Botão de Logoff
        if st.button("SAIR DO PAINEL", use_container_width=True):
            st.session_state.auth = False
            st.rerun()

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

# --- ABA 4: TERMINAL ADMIN (VERSÃO SOMAR & ALINHADA) ---
with menu_abas[3]:
    access_adm = st.text_input("Senha Master", type="password", key="adm_auth_final")
    
    if access_adm == CHAVE_ADMIN:
        st.markdown("### 👑 Painel de Controle Supremo")
        
        # 1. MÉTRICAS TOTAIS (SOMANDO INTELIGÊNCIA)
        all_profs_lista = list(db.collection("profissionais").stream())
        total_moedas = sum([p.to_dict().get('saldo', 0) for p in all_profs_lista])
        
        c_fin1, c_fin2, c_fin3 = st.columns(3)
        c_fin1.metric("💰 Moedas no Ecossistema", f"{total_moedas} 🪙")
        c_fin2.metric("📈 Valor Previsto", f"R$ {total_moedas:,.2f}")
        c_fin3.metric("🤝 Parceiros Cadastrados", len(all_profs_lista))
        st.divider()

        # 2. ABAS DE COMANDO (ALINHAMENTO PRECISO)
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
                                st.rerun()
                        
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
            st.info("📩 Central de Feedbacks vazia. Os comentários dos clientes aparecerão aqui.")

    elif access_adm != "":
        st.error("🚫 Acesso negado. Senha incorreta.")
# ------------------------------------------------------------------------------
# RODAPÉ ÚNICO (Final do Arquivo)
# ------------------------------------------------------------------------------
st.markdown(f'<div style="text-align:center; padding:20px; color:#94A3B8; font-size:10px;">GERALJÁ v20.0 © {datetime.datetime.now().year}</div>', unsafe_allow_html=True)













