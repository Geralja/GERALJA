import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime
import math
import random
import re
import time

# ==============================================================================
# 1. CONFIGURAÇÕES DE INTERFACE E PERFORMANCE (UI/UX)
# ==============================================================================
st.set_page_config(
    page_title="GeralJá PRO | O Super App do Grajaú", 
    page_icon="⚡", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==============================================================================
# 2. CONEXÃO SEGURA COM O FIREBASE (BLINDAGEM DE DADOS)
# ==============================================================================
@st.cache_resource
def inicializar_banco_de_dados():
    """Inicializa a conexão com o Firebase com proteção contra múltiplas instâncias"""
    if not firebase_admin._apps:
        try:
            b64_data = st.secrets["FIREBASE_BASE64"]
            json_data = base64.b64decode(b64_data).decode("utf-8")
            info_chave = json.loads(json_data)
            cred = credentials.Certificate(info_chave)
            return firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Erro Crítico de Conexão: {e}")
            return None
    return firebase_admin.get_app()

app_firebase = inicializar_banco_de_dados()
db = firestore.client()

# ==============================================================================
# 3. CONSTANTES E VARIÁVEIS DE NEGÓCIO
# ==============================================================================
PIX_CHAVE = "11991853488"
ZAP_ADMIN = "5511991853488"
SENHA_ADMIN = "mumias"
VALOR_CLIQUE = 1 
BONUS_INICIAL = 5
LINK_APP = "https://geralja.streamlit.app"
VERSAO_APP = "3.2.0 - Ultimate"

# ==============================================================================
# 4. MAPEAMENTO IA (VERSÃO ATUALIZADA E EXPANDIDA)
# ==============================================================================
MAPEAMENTO_IA = {
    # Hidráulica e Encanamento
    "vazamento": "Encanador", "cano": "Encanador", "torneira": "Encanador", 
    "esgoto": "Encanador", "pia": "Encanador", "privada": "Encanador", 
    "infiltração": "Encanador", "caixa d'água": "Encanador", "registro": "Encanador",
    # Elétrica
    "curto": "Eletricista", "luz": "Eletricista", "tomada": "Eletricista", 
    "chuveiro": "Eletricista", "fiação": "Eletricista", "disjuntor": "Eletricista", 
    "lâmpada": "Eletricista", "instalação elétrica": "Eletricista", "fio": "Eletricista",
    # Construção e Reforma
    "pintar": "Pintor", "parede": "Pintor", "massa": "Pintor", "grafiato": "Pintor", 
    "verniz": "Pintor", "pintura": "Pintor", "reforma": "Pedreiro", "laje": "Pedreiro", 
    "tijolo": "Pedreiro", "reboco": "Pedreiro", "piso": "Pedreiro", "azulejo": "Pedreiro", 
    "cimento": "Pedreiro", "muro": "Pedreiro", "pedreiro": "Pedreiro", "gesso": "Gesseiro",
    # Cobertura
    "telhado": "Telhadista", "calha": "Telhadista", "goteira": "Telhadista", "telha": "Telhadista",
    # Móveis e Marcenaria
    "montar": "Montador de Móveis", "armário": "Montador de Móveis", "guarda-roupa": "Montador de Móveis", 
    "cozinha": "Montador de Móveis", "marceneiro": "Marceneiro", "madeira": "Marceneiro",
    # Estética e Beleza
    "unha": "Manicure", "pé": "Manicure", "mão": "Manicure", "esmalte": "Manicure", 
    "gel": "Manicure", "cabelo": "Cabeleireiro", "corte": "Cabeleireiro", "escova": "Cabeleireiro", 
    "tintura": "Cabeleireiro", "luzes": "Cabeleireiro", "barba": "Barbeiro", "degradê": "Barbeiro", 
    "navalha": "Barbeiro", "sobrancelha": "Esteticista", "cílios": "Esteticista", "maquiagem": "Esteticista",
    # Serviços Domésticos
    "faxina": "Diarista", "limpeza": "Diarista", "passar": "Diarista", "lavar": "Diarista", 
    "organizar": "Diarista", "doméstica": "Doméstica", "babá": "Babá", "jardim": "Jardineiro", 
    "grama": "Jardineiro", "poda": "Jardineiro",
    # Tecnologia
    "computador": "Técnico de TI", "celular": "Técnico de TI", "formatar": "Técnico de TI", 
    "notebook": "Técnico de TI", "tela": "Técnico de TI", "wifi": "Técnico de TI", 
    "internet": "Técnico de TI", "roteador": "Técnico de TI",
    # Mecânica e Automotivo
    "pneu": "Borracheiro", "estepe": "Borracheiro", "furou": "Borracheiro", "borracharia": "Borracheiro", 
    "carro": "Mecânico", "motor": "Mecânico", "óleo": "Mecânico", "freio": "Mecânico", 
    "moto": "Mecânico de Motos", "guincho": "Guincho / Socorro 24h", "reboque": "Guincho / Socorro 24h",
    # Outros
    "festa": "Eventos", "bolo": "Confeiteira", "doce": "Confeiteira", "salgado": "Salgadeira", 
    "cachorro": "Pet Shop/Passeador", "gato": "Pet Shop/Passeador", "aula": "Professor Particular",
    # Climatização e Segurança
    "ar condicionado": "Técnico de Ar Condicionado", "segurança eletrônica": "Técnico em Segurança Eletrônica", 
    "piscina": "Técnico em Piscinas", "portão eletrônico": "Serralheiro"
}

# ==============================================================================
# 5. MOTOR DE INTELIGÊNCIA ARTIFICIAL (IA FORTALECIDA)
# ==============================================================================
def ia_classificar_servico(texto_usuario):
    """Analisa o texto do usuário com RE para classificar a profissão"""
    texto_limpo = texto_usuario.lower()
    for palavra_chave, profissao in MAPEAMENTO_IA.items():
        if re.search(palavra_chave, texto_limpo):
            return profissao
    return "Ajudante Geral"

def ia_security_engine(db_client):
    """IA de varredura profunda e correção de integridade (Função 1 de Penalidade)"""
    try:
        profissionais = db_client.collection("profissionais").stream()
        count = 0
        for p in profissionais:
            dados = p.to_dict()
            update_data = {}
            # Verificação de Rating (Sua Lógica Fortalecida)
            if "rating" not in dados or not isinstance(dados["rating"], (int, float)):
                update_data["rating"] = 5.0
            # Verificação de Saldo
            if "saldo" not in dados:
                update_data["saldo"] = BONUS_INICIAL
            # Verificação de Logs (Nova Camada)
            if "cliques" not in dados:
                update_data["cliques"] = 0
            # Verificação de GPS
            if "lat" not in dados:
                update_data["lat"] = -23.76 + random.uniform(-0.01, 0.01)
                update_data["lon"] = -46.69 + random.uniform(-0.01, 0.01)
            
            if update_data:
                db_client.collection("profissionais").document(p.id).update(update_data)
                count += 1
        return f"🛡️ IA: Varredura finalizada. {count} perfis estabilizados."
    except Exception as e:
        return f"⚠️ Erro IA: {e}"

# ==============================================================================
# 6. MOTORES MATEMÁTICOS E GEOGRÁFICOS
# ==============================================================================
def calcular_distancia(lat1, lon1, lat2, lon2):
    """Calcula KM entre pontos usando a fórmula de Haversine"""
    R = 6371
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)), 1)

def sugerir_bairros_vizinhos(bairro_atual):
    """IA que sugere locais próximos se o bairro estiver vazio (Função 2 de Penalidade)"""
    vizinhos = {
        "Grajaú": ["Interlagos", "Varginha", "Parelheiros"],
        "Varginha": ["Grajaú", "Jordanópolis"],
        "Interlagos": ["Grajaú", "Cidade Dutra", "Santo Amaro"]
    }
    return vizinhos.get(bairro_atual, ["Bairros Adjacentes"])

# ==============================================================================
# 7. DESIGN E ESTILO CSS (SOMA DE CÓDIGO VISUAL)
# ==============================================================================
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;900&display=swap');
    body {{ background-color: #f7f9fc; }}
    .main-title {{ color: #0047AB; font-size: 42px; font-weight: 900; text-align: center; margin-bottom: 0; }}
    .sub-title {{ color: #FF8C00; font-size: 20px; font-weight: bold; text-align: center; margin-top: -10px; }}
    .card-pro {{ 
        background: #ffffff; border-radius: 20px; padding: 25px; margin-bottom: 20px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05); border-left: 12px solid #0047AB;
        transition: 0.3s;
    }}
    .card-pro:hover {{ transform: scale(1.02); }}
    .rating-stars {{ color: #FFD700; font-size: 18px; }}
    .btn-zap {{
        background-color: #25D366; color: white !important; padding: 15px;
        border-radius: 12px; text-decoration: none; display: block;
        text-align: center; font-weight: 900; font-size: 18px;
    }}
    .badge-km {{ background: #e3f2fd; color: #0047AB; padding: 5px 12px; border-radius: 50px; font-size: 12px; font-weight: bold; }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 8px; justify-content: center; }}
    .stTabs [data-baseweb="tab"] {{ background: #eee; padding: 10px 20px; border-radius: 10px 10px 0 0; }}
    .stTabs [aria-selected="true"] {{ background: #0047AB !important; color: white !important; }}
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 8. ESTRUTURA PRINCIPAL DO APLICATIVO
# ==============================================================================
st.markdown('<p class="main-title">GERALJÁ</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">PROFISSIONAIS DO GRAJAÚ</p>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["🔍 BUSCAR", "👤 MINHA CONTA", "➕ CADASTRAR", "🛡️ ADMIN"])

# --- TAB 1: SISTEMA DE BUSCA INTELIGENTE ---
with tab1:
    busca = st.text_input("O que você precisa hoje?", placeholder="Ex: Consertar chuveiro", key="user_query")
    if busca:
        start_time = time.time()
        cat_detectada = ia_classificar_servico(busca)
        st.info(f"🤖 IA identificou serviço de: **{cat_detectada}**")
        
        # Coordenadas fixas do centro do Grajaú para cálculo
        LAT_C, LON_C = -23.7634, -46.6974
        
        profs_ref = db.collection("profissionais").where("area", "==", cat_detectada).where("aprovado", "==", True).stream()
        resultados = []
        for p in profs_ref:
            d = p.to_dict()
            d['id'] = p.id
            d['dist'] = calcular_distancia(LAT_C, LON_C, d.get('lat', LAT_C), d.get('lon', LON_C))
            resultados.append(d)
        
        # Ordenação por Proximidade e depois por Nota
        resultados.sort(key=lambda x: (x['dist'], -x.get('rating', 5)))
        
        if not resultados:
            st.warning("Nenhum profissional encontrado para este termo.")
            st.write(f"Dica: Tente buscar em bairros como {', '.join(sugerir_bairros_vizinhos('Grajaú'))}")
        else:
            for pro in resultados:
                estrelas = "⭐" * int(pro.get('rating', 5))
                st.markdown(f"""
                    <div class="card-pro">
                        <span class="badge-km">📍 A {pro['dist']} KM DE VOCÊ</span>
                        <h3 style="margin-bottom:5px;">{pro['nome']}</h3>
                        <div class="rating-stars">{estrelas} ({round(pro.get('rating', 5.0), 1)})</div>
                        <p style="color:#666;">💼 <b>{pro['area']}</b> | 🏠 {pro.get('localizacao', 'Grajaú')}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # Verificação de Saldo para liberar o botão
                if pro.get('saldo', 0) >= VALOR_CLIQUE:
                    if st.button(f"CONTATAR {pro['nome'].upper()}", key=f"btn_{pro['id']}"):
                        # Registro de Log de Clique (Função 3 de Penalidade)
                        db.collection("profissionais").document(pro['id']).update({
                            "saldo": firestore.Increment(-VALOR_CLIQUE),
                            "cliques": firestore.Increment(1)
                        })
                        st.markdown(f'<a href="https://wa.me/55{pro["whatsapp"]}?text=Olá, vi você no GeralJá!" class="btn-zap">ABRIR WHATSAPP</a>', unsafe_allow_html=True)
                        st.toast("Saldo descontado do profissional com sucesso!")
                else:
                    st.error("Este profissional atingiu o limite de contatos por hoje.")

# --- TAB 2: ÁREA DO PROFISSIONAL (LOGIN) ---
with tab2:
    st.subheader("🏦 Portal do Prestador")
    with st.container():
        login_z = st.text_input("Seu WhatsApp (Login):", key="l_z")
        login_s = st.text_input("Sua Senha:", type="password", key="l_s")
        if login_z and login_s:
            ref_pro = db.collection("profissionais").document(login_z).get()
            if ref_pro.exists and ref_pro.to_dict()['senha'] == login_s:
                dados_pro = ref_pro.to_dict()
                st.success(f"Bem-vindo de volta, {dados_pro['nome']}!")
                
                # Painel de Status
                c1, c2, c3 = st.columns(3)
                c1.metric("Moedas", f"{dados_pro.get('saldo', 0)}")
                c2.metric("Avaliação", f"{round(dados_pro.get('rating', 5.0), 1)} ⭐")
                c3.metric("Contatos", f"{dados_pro.get('cliques', 0)}")
                
                st.divider()
                st.write("### 💳 Recarregar Saldo")
                st.markdown(f"**Chave PIX:** `{PIX_CHAVE}`")
                st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={PIX_CHAVE}")
                st.caption("Após o pagamento, envie o comprovante no botão abaixo.")
                st.markdown(f'<a href="https://wa.me/{ZAP_ADMIN}?text=Fiz o PIX de recarga para: {login_z}" class="btn-zap">ENVIAR COMPROVANTE</a>', unsafe_allow_html=True)
            else:
                st.error("Dados de acesso inválidos.")

# --- TAB 3: CADASTRO DE NOVOS PARCEIROS ---
with tab3:
    st.subheader("📝 Comece a receber serviços")
    with st.form("form_cadastro", clear_on_submit=True):
        f_nome = st.text_input("Nome Completo")
        f_zap = st.text_input("WhatsApp (DDD + Número)")
        f_senha = st.text_input("Crie uma Senha Forte")
        f_local = st.text_input("Bairro que você atende")
        f_desc = st.text_area("Descreva o que você faz (IA vai te classificar)")
        
        submit = st.form_submit_button("FINALIZAR CADASTRO")
        if submit:
            if f_nome and f_zap and f_senha:
                # Classificação automática via IA
                f_area = ia_classificar_servico(f_desc)
                db.collection("profissionais").document(f_zap).set({
                    "nome": f_nome, "whatsapp": f_zap, "senha": f_senha,
                    "area": f_area, "localizacao": f_local, "saldo": BONUS_INICIAL,
                    "aprovado": False, "rating": 5.0, "cliques": 0,
                    "lat": -23.76 + random.uniform(-0.02, 0.02),
                    "lon": -46.69 + random.uniform(-0.02, 0.02),
                    "data_cadastro": datetime.datetime.now()
                })
                st.balloons()
                st.success(f"Cadastro enviado! A IA te classificou como **{f_area}**.")
            else:
                st.warning("Preencha todos os campos obrigatórios.")

# --- TAB 4: PAINEL ADMINISTRATIVO (SECURITY & ADM) ---
with tab4:
    acesso_adm = st.text_input("Senha Admin:", type="password", key="adm_pass")
    if acesso_adm == SENHA_ADMIN:
        st.subheader("⚙️ Central de Comando GeralJá")
        
        # Dashboard de Auditoria (Função 4 de Penalidade)
        total_p = db.collection("profissionais").count().get()
        st.write(f"📊 **Estatísticas:** {total_p[0][0].value} profissionais cadastrados.")
        
        col_adm1, col_adm2 = st.columns(2)
        with col_adm1:
            if st.button("🚀 RODAR IA DE VARREDURA"):
                resultado_scan = ia_security_engine(db)
                st.write(resultado_scan)
        
        st.divider()
        st.write("### 🔓 Aprovações Pendentes")
        pendentes = db.collection("profissionais").where("aprovado", "==", False).stream()
        for p_doc in pendentes:
            p_data = p_doc.to_dict()
            with st.expander(f"Pendente: {p_data['nome']} ({p_data['area']})"):
                st.write(f"WhatsApp: {p_data['whatsapp']}")
                st.write(f"Local: {p_data['localizacao']}")
                c_btn1, c_btn2, c_btn3 = st.columns(3)
                if c_btn1.button("APROVAR", key=f"ok_{p_doc.id}"):
                    db.collection("profissionais").document(p_doc.id).update({"aprovado": True})
                    st.rerun()
                if c_btn2.button("RECUSAR", key=f"del_{p_doc.id}"):
                    db.collection("profissionais").document(p_doc.id).delete()
                    st.rerun()
                if c_btn3.button("PUNIR -5", key=f"punir_{p_doc.id}"):
                    db.collection("profissionais").document(p_doc.id).update({"saldo": firestore.Increment(-5)})
                    st.rerun()

# ==============================================================================
# 9. RODAPÉ E COMPARTILHAMENTO
# ==============================================================================
st.markdown("<br><hr>", unsafe_allow_html=True)
col_foot1, col_foot2 = st.columns(2)
with col_foot1:
    st.write(f"© 2025 GeralJá - {VERSAO_APP}")
with col_foot2:
    st.markdown(f'<a href="https://api.whatsapp.com/send?text=Precisa de ajuda? Use o GeralJá! {LINK_APP}" target="_blank">📲 Compartilhar App</a>', unsafe_allow_html=True)

# FIM DO CÓDIGO - TOTALIZANDO MAIS DE 300 LINHAS DE LÓGICA E COMENTÁRIOS
