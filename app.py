import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime
import math
import requests

# ------------------------------------------------------------------------------
# 1. CONFIGURAÇÃO E INFRAESTRUTURA (FIREBASE)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="GeralJá | Ecossistema Profissional",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

@st.cache_resource
def inicializar_infraestrutura_dados():
    if not firebase_admin._apps:
        try:
            # Puxa a chave Base64 dos Secrets do Streamlit
            b64_key = st.secrets["FIREBASE_BASE64"]
            decoded_json = base64.b64decode(b64_key).decode("utf-8")
            cred_dict = json.loads(decoded_json)
            credenciais = credentials.Certificate(cred_dict)
            return firebase_admin.initialize_app(credenciais)
        except Exception as e:
            st.error(f"Erro Crítico de Conexão: {e}")
            st.stop()
    return firebase_admin.get_app()

app_engine = inicializar_infraestrutura_dados()
db = firestore.client()

# ------------------------------------------------------------------------------
# 2. PARÂMETROS E INTELIGÊNCIA DE CATEGORIAS
# ------------------------------------------------------------------------------
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ACESSO_ADMIN = "mumias"
TAXA_CONTATO = 1        # Custo por clique em GeralCoins
BONUS_WELCOME = 5       # Moedas grátis ao cadastrar

MAPA_PROFISSOES = {
    "Encanador": ["vazamento", "cano", "torneira", "esgoto", "hidraulico", "caixa d'água", "pia", "privada", "infiltração"],
    "Eletricista": ["fio", "luz", "chuveiro", "tomada", "disjuntor", "curto", "energia", "fiação", "lâmpada"],
    "Pintor": ["pintar", "parede", "verniz", "massa corrida", "textura", "grafiato", "pintura"],
    "Pedreiro": ["reforma", "construção", "tijolo", "cimento", "piso", "azulejo", "alvenaria", "muro", "laje"],
    "Marceneiro": ["madeira", "móvel", "armário", "porta", "guarda-roupa", "restauração"],
    "Mecânico": ["carro", "motor", "freio", "suspensão", "oficina", "veículo", "bateria"],
    "Diarista": ["limpeza", "faxina", "passar roupa", "organização", "casa", "lavar"],
    "Manicure": ["unha", "esmalte", "mão", "pé", "cutícula", "gel"],
    "Cabeleireiro": ["cabelo", "corte", "tintura", "escova", "progressiva", "luzes"],
    "Barbeiro": ["barba", "degrade", "navalha", "cabelo masculino"],
    "Técnico TI": ["computador", "notebook", "celular", "wi-fi", "formatar", "software", "internet", "wifi"],
    "Refrigeração": ["ar condicionado", "geladeira", "freezer", "carregar gás"],
    "Montador": ["montar", "desmontar", "móveis", "guarda-roupa", "armário"],
    "Freteiro": ["frete", "mudança", "transporte", "carreto", "entrega", "vuc"],
    "Jardineiro": ["grama", "jardim", "planta", "poda", "adubo", "roçagem"],
    "Gesseiro": ["gesso", "drywall", "sanca", "forro", "moldura"]
}

LISTA_AREAS_DROP = sorted(list(MAPA_PROFISSOES.keys()) + ["Ajudante Geral"])
LISTA_ESTADOS = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]

# ------------------------------------------------------------------------------
# 3. MOTORES DE LÓGICA (IA E BUSCA)
# ------------------------------------------------------------------------------
def processar_servico_ia(texto):
    if not texto: return None
    t_clean = texto.lower()
    for prof, palavras in MAPA_PROFISSOES.items():
        if any(p in t_clean for p in palavras): return prof
    # Busca secundária por nome direto
    for prof in LISTA_AREAS_DROP:
        if prof.lower() in t_clean: return prof
    return "Ajudante Geral"

# ------------------------------------------------------------------------------
# 4. DESIGN SYSTEM PREMIUM (CSS)
# ------------------------------------------------------------------------------
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap');
    * {{ font-family: 'Montserrat', sans-serif; }}
    .stApp {{ background-color: #F1F5F9; }}
    
    .header-box {{ 
        text-align: center; padding: 30px; background: white; 
        border-bottom: 6px solid #FF8C00; border-radius: 0 0 40px 40px; 
        box-shadow: 0 10px 20px rgba(0,0,0,0.05); margin-bottom: 25px;
    }}
    .txt-azul {{ color: #0047AB; font-size: 45px; font-weight: 900; letter-spacing: -2px; }}
    .txt-laranja {{ color: #FF8C00; font-size: 45px; font-weight: 900; letter-spacing: -2px; }}
    
    .card-pro {{ 
        background: white; border-radius: 20px; padding: 20px; margin-bottom: 15px; 
        border-left: 12px solid #0047AB; box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        transition: 0.3s;
    }}
    .card-pro:hover {{ transform: scale(1.01); }}
    
    .coin-badge {{
        background: #FEF3C7; color: #D97706; padding: 5px 15px; 
        border-radius: 20px; font-weight: bold; font-size: 14px;
        border: 1px solid #FCD34D;
    }}
    
    .btn-zap {{ 
        background: #25D366; color: white !important; padding: 12px; border-radius: 12px; 
        text-decoration: none; display: block; text-align: center; font-weight: 700;
        margin-top: 10px;
    }}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-box"><span class="txt-azul">GERAL</span><span class="txt-laranja">JÁ</span><br><small style="color:#64748B; font-weight:700;">SERVIÇOS NUM ESTALO</small></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 5. SISTEMA DE NAVEGAÇÃO (ABAS)
# ------------------------------------------------------------------------------
UI_ABAS = st.tabs(["🔍 BUSCAR", "💼 CARTEIRA", "📝 CADASTRAR", "🛡️ ADMIN"])

# --- ABA 1: CLIENTE (BUSCA) ---
with UI_ABAS[0]:
    col_c, col_t = st.columns([1, 2])
    
    # Adicionamos KEY para estabilidade
    cidade_filtro = col_c.text_input("📍 Localização", placeholder="Cidade ou bairro", key="cidade_input")
    termo_busca = col_t.text_input("🛠️ O que você precisa?", placeholder="Ex: Meu cano quebrou", key="busca_input")
    
    if termo_busca:
        cat_detectada = processar_servico_ia(termo_busca)
        st.info(f"✨ **IA GeralJá:** Buscando por especialistas em **{cat_detectada}**")
        
        # Chamada ao banco
        query = db.collection("profissionais").where("area", "==", cat_detectada).where("aprovado", "==", True).stream()
        
        encontrados = 0
        for d in query:
            p = d.to_dict()
            
            # Filtro de cidade
            match_cidade = not cidade_filtro or cidade_filtro.lower() in p.get('cidade', '').lower()
            
            if match_cidade:
                encontrados += 1
                st.markdown(f'''
                    <div class="card-pro">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div>
                                <h3 style="margin:0; color:#1E293B;">{p['nome'].upper()}</h3>
                                <p style="color:#64748B; margin: 4px 0;">📍 {p.get('cidade', 'Região não informada')}</p>
                                <p style="font-size: 14px;">{p.get('descricao', '')}</p>
                            </div>
                            <span class="coin-badge">⭐ {p.get('rating', 5.0)}</span>
                        </div>
                    </div>
                ''', unsafe_allow_html=True)
                
                if p.get('saldo', 0) >= TAXA_CONTATO:
                    # Chave única combinando ID e Categoria
                    if st.button(f"VER WHATSAPP DE {p['nome'].split()[0].upper()}", key=f"btn_{d.id}"):
                        # Executa a cobrança no Firebase
                        db.collection("profissionais").document(d.id).update({
                            "saldo": firestore.Increment(-TAXA_CONTATO),
                            "cliques": firestore.Increment(1)
                        })
                        
                        # Link direto e chamativo
                        st.success(f"✅ Saldo de {p['nome']} atualizado!")
                        st.markdown(f'''
                            <a href="https://wa.me/55{p["whatsapp"]}?text=Olá, vi seu perfil no GeralJá!" target="_blank" 
                               style="text-decoration:none; display:block; background:#25D366; color:white; text-align:center; padding:15px; border-radius:10px; font-weight:bold; margin-top:10px;">
                                📱 CHAMAR NO WHATSAPP AGORA
                            </a>
                        ''', unsafe_allow_html=True)
                else:
                    st.warning("Profissional temporariamente offline.")

        if encontrados == 0:
            st.warning("Nenhum profissional encontrado para esta categoria nesta região.")

# --- ABA 2: PROFISSIONAL (CARTEIRA) ---
with UI_ABAS[1]:
    if 'logado' not in st.session_state: st.session_state.logado = False
    
    if not st.session_state.logado:
        st.subheader("🔑 Acesso do Profissional")
        login_zap = st.text_input("WhatsApp (apenas números)", key="login_z")
        login_sen = st.text_input("Sua Senha", type="password", key="login_s")
        
        if st.button("ACESSAR MINHA CONTA"):
            doc = db.collection("profissionais").document(login_zap).get()
            if doc.exists and doc.to_dict().get('senha') == login_sen:
                st.session_state.logado = True
                st.session_state.user_id = login_zap
                st.rerun()
            else:
                st.error("Dados de acesso incorretos.")
    else:
        # Painel do Usuário Logado
        u_data = db.collection("profissionais").document(st.session_state.user_id).get().to_dict()
        st.markdown(f"### Bem-vindo, {u_data['nome']}! 👋")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Saldo Atual", f"{u_data.get('saldo', 0)} Moedas")
        with c2:
            st.metric("Contatos Recebidos", u_data.get('cliques', 0))
        with c3:
            st.metric("Sua Nota", u_data.get('rating', 5.0))
            
        st.divider()
        st.subheader("💳 Recarregar Créditos")
        st.write("Cada vez que um cliente clicar no seu WhatsApp, você investe 1 GeralCoin.")
        st.code(f"CHAVE PIX: {PIX_OFICIAL}", language="text")
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={PIX_OFICIAL}")
        st.markdown(f'<a href="https://wa.me/{ZAP_ADMIN}?text=Fiz o PIX para o usuário: {st.session_state.user_id}" class="btn-zap" style="background:#0047AB;">ENVIAR COMPROVANTE</a>', unsafe_allow_html=True)
        
        if st.button("DESLOGAR"):
            st.session_state.logado = False
            st.rerun()

# --- ABA 3: CADASTRO ---
with UI_ABAS[2]:
    st.subheader("📝 Cadastre-se e Ganhe 5 Moedas")
    with st.form("form_cadastro", clear_on_submit=True):
        f_nome = st.text_input("Nome Completo ou Nome da Empresa")
        f_zap = st.text_input("WhatsApp (com DDD, apenas números)")
        f_senha = st.text_input("Crie uma Senha", type="password")
        f_area = st.selectbox("Especialidade Principal", LISTA_AREAS_DROP)
        f_city = st.text_input("Sua Cidade")
        f_uf = st.selectbox("Estado", LISTA_ESTADOS, index=24) # Default SP
        f_desc = st.text_area("Descreva seu serviço (Dica: Use palavras-chave como 'Pintura', 'Vazamento', etc)")
        
        btn_cad = st.form_submit_button("FINALIZAR MEU CADASTRO")
        
        if btn_cad:
            if f_nome and f_zap and f_senha:
                # Verificação se já existe
                if db.collection("profissionais").document(f_zap).get().exists:
                    st.error("Este WhatsApp já está cadastrado.")
                else:
                    db.collection("profissionais").document(f_zap).set({
                        "nome": f_nome, "whatsapp": f_zap, "senha": f_senha,
                        "area": f_area, "cidade": f_city, "uf": f_uf,
                        "descricao": f_desc, "saldo": BONUS_WELCOME,
                        "cliques": 0, "rating": 5.0, "aprovado": False,
                        "data_cadastro": datetime.datetime.now()
                    })
                    st.success("Cadastro realizado! Você ganhou 5 moedas de bônus. Aguarde a aprovação do Admin para aparecer nas buscas.")
                    st.balloons()
            else:
                st.warning("Preencha todos os campos obrigatórios.")

# --- ABA 4: ADMIN ---
with UI_ABAS[3]:
    adm_pass = st.text_input("Senha Master", type="password")
    if adm_pass == CHAVE_ACESSO_ADMIN:
        st.subheader("🛡️ Painel de Controle Administrativo")
        
        # Lista Pendentes
        pendentes = db.collection("profissionais").where("aprovado", "==", False).stream()
        st.write("#### Aprovações Pendentes")
        for p_doc in pendentes:
            pd = p_doc.to_dict()
            col1, col2 = st.columns([3, 1])
            col1.write(f"👤 {pd['nome']} | 🛠️ {pd['area']} | 📍 {pd['cidade']}")
            if col2.button("APROVAR", key=f"aprova_{p_doc.id}"):
                db.collection("profissionais").document(p_doc.id).update({"aprovado": True})
                st.rerun()
        
        st.divider()
        st.write("#### Gestão de Saldo")
        target_zap = st.text_input("WhatsApp do Profissional para recarga:")
        valor_recarga = st.number_input("Moedas a adicionar:", min_value=1, value=10)
        if st.button("CONFIRMAR RECARGA"):
            ref = db.collection("profissionais").document(target_zap)
            if ref.get().exists:
                ref.update({"saldo": firestore.Increment(valor_recarga)})
                st.success(f"Recarga de {valor_recarga} moedas concluída!")
            else:
                st.error("Usuário não encontrado.")

# --- RODAPÉ ---
st.markdown("<br><hr><center><p style='color:#64748B; font-size:12px;'>GeralJá Brasil v3.000 © 2025 | Sistema de Alta Performance Profissional</p></center>", unsafe_allow_html=True)

