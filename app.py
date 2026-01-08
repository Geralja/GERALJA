import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import base64
import json
from datetime import datetime
import pytz
from streamlit_js_eval import streamlit_js_eval

# ==============================================================================
# 1. CONFIGURAÇÃO VISUAL ELITE (CSS PERSONALIZADO)
# ==============================================================================
st.set_page_config(page_title="GeralJá - Conectando Você", page_icon="🎯", layout="centered")

st.markdown("""
    <style>
        /* Remove o cabeçalho padrão e marca d'água */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Fundo e Fontes */
        .stApp { background-color: #f0f2f5; }
        
        /* Estilo dos Cards de Profissionais */
        .prof-card {
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            border-left: 6px solid #1E3A8A;
            margin-bottom: 20px;
        }
        
        /* Botões de WhatsApp */
        .btn-wpp {
            background-color: #25D366;
            color: white !important;
            padding: 10px 20px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: bold;
            display: inline-block;
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CONEXÃO SEGURA COM FIREBASE (VIA SECRETS)
# ==============================================================================
@st.cache_resource
def conectar_banco_master():
    if not firebase_admin._apps:
        try:
            if "FIREBASE_BASE64" not in st.secrets:
                st.error("🔑 Chave FIREBASE_BASE64 não configurada nos Secrets.")
                st.stop()
            b64_key = st.secrets["FIREBASE_BASE64"]
            decoded_json = base64.b64decode(b64_key).decode("utf-8")
            cred_dict = json.loads(decoded_json)
            cred = credentials.Certificate(cred_dict)
            return firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"❌ Falha crítica de conexão: {e}")
            st.stop()
    return firebase_admin.get_app()

app_engine = conectar_banco_master()
db = firestore.client()
# ==============================================================================
# 3. DICIONÁRIO E CATEGORIAS TURBINADAS (SEM REMOVER NADA)
# ==============================================================================
CATEGORIAS_OFICIAIS = [
    "Academia", "Acompanhante de Idosos", "Açougue", "Adega", "Adestrador de Cães", "Advocacia", "Agropecuária", 
    "Ajudante Geral", "Animador de Festas", "Arquiteto(a)", "Armarinho/Aviamentos", "Assistência Técnica", 
    "Aulas Particulares", "Auto Elétrica", "Auto Peças", "Babá (Nanny)", "Banho e Tosa", "Barbearia/Salão", 
    "Barman / Bartender", "Bazar", "Borracheiro", "Cabeleireiro(a)", "Cafeteria", "Calçados", "Carreto", 
    "Celulares", "Chaveiro", "Churrascaria", "Clínica Médica", "Comida Japonesa", "Confeiteiro(a)", 
    "Contabilidade", "Costureira / Alfaiate", "Cozinheiro(a) Particular", "Cuidador de Idosos", 
    "Dançarino(a)", "Decorador(a) de Festas", "Destaque de Eventos", "Diarista / Faxineira", "Doceria", 
    "Eletrodomésticos", "Eletricista", "Eletrônicos", "Encanador", "Escola Infantil", "Estética Automotiva", 
    "Estética Facial", "Esteticista", "Farmácia", "Fisioterapia", "Fitness", "Floricultura", "Fotógrafo(a)", 
    "Freteiro", "Fretista / Mudanças", "Funilaria e Pintura", "Garçom e garçonete", "Gesseiro", "Guincho 24h", 
    "Hamburgueria", "Hortifruti", "Idiomas", "Imobiliária", "Informática", "Instalador de Ar-condicionado", 
    "Internet de fibra óptica", "Jardineiro", "Joalheria", "Lanchonete", "Lava Jato", "Lavagem de Sofás", 
    "Loja de Roupas", "Loja de Variedades", "Madeireira", "Manicure e Pedicure", "Maquiador(a)", "Marceneiro", 
    "Marido de Aluguel", "Material de Construção", "Mecânico de Autos", "Montador de Móveis", "Motoboy/Entregas", 
    "Motorista Particular", "Móveis", "Moto Peças", "Nutricionista", "Odontologia", "Ótica", "Padaria", 
    "Papelaria", "Passeador de Cães", "Pastelaria", "Pedreiro", "Pet Shop", "Pintor", "Piscineiro", "Pizzaria", 
    "Professor(a) Particular", "Psicologia", "Recepcionista de Eventos", "Reforço Escolar", "Refrigeração", 
    "Relojoaria", "Salgadeiro(a)", "Segurança / Vigilante", "Seguros", "Som e Alarme", "Sorveteria", 
    "Tatuagem/Piercing", "Técnico de Celular", "Técnico de Fogão", "Técnico de Geladeira", "Técnico de Lavadora", 
    "Técnico de Notebook/PC", "Telhadista", "TI (Tecnologia)", "Tintas", "Veterinário(a)", "Web Designer"
]

CONCEITOS_EXPANDIDOS = {
    "celular": "Técnico de Celular", "iphone": "Técnico de Celular", "tela": "Técnico de Celular",
    "fogao": "Técnico de Fogão", "forno": "Técnico de Fogão",
    "geladeira": "Técnico de Geladeira", "freezer": "Técnico de Geladeira",
    "maquina de lavar": "Técnico de Lavadora", "lavadora": "Técnico de Lavadora",
    "computador": "Técnico de Notebook/PC", "notebook": "Técnico de Notebook/PC", "formatar": "Técnico de Notebook/PC",
    "telhado": "Telhadista", "goteira": "Telhadista", "telha": "Telhadista",
    "ti": "TI (Tecnologia)", "software": "TI (Tecnologia)", "rede": "TI (Tecnologia)",
    "tinta": "Tintas", "pintura": "Tintas", "vete": "Veterinário(a)", "cachorro": "Veterinário(a)",
    "site": "Web Designer", "criar site": "Web Designer", "vazamento": "Encanador", "cano": "Encanador",
    "curto": "Eletricista", "chuveiro": "Eletricista", "fome": "Lanchonete", "pizza": "Pizzaria"
}
# --- CONTEÚDO DA ABA BUSCAR ---
with tab_busca:
    st.write("### O que você precisa hoje?")
    
    # Atalhos Visuais (UX Profissional)
    c1, c2, c3, c4 = st.columns(4)
    atalho = ""
    if c1.button("📱 Celular"): atalho = "Técnico de Celular"
    if c2.button("🔧 Reparos"): atalho = "Marido de Aluguel"
    if c3.button("🏠 Obra"): atalho = "Pedreiro"
    if c4.button("🍔 Fome"): atalho = "Lanchonete"
    
    busca_input = st.text_input("Busque por serviço ou categoria", value=atalho, placeholder="Ex: consertar telhado")
    
    if busca_input:
        busca_limpa = remover_acentos(busca_input)
        # Verifica se o termo está no dicionário expandido
        categoria_alvo = CONCEITOS_EXPANDIDOS.get(busca_limpa, busca_input)
        
        st.subheader(f"📍 Profissionais de '{categoria_alvo}' próximos a você")
        
        # Simulação de Card Profissional (Aqui entra o loop do seu Firestore)
        st.markdown(f"""
            <div class="prof-card">
                <h4>João da Silva - {categoria_alvo}</h4>
                <p>⭐ 5.0 | 📍 A 2.5km de você</p>
                <p>Especialista em atendimento rápido e garantia de serviço.</p>
                <a href="https://wa.me/5511999999999" class="btn-wpp" target="_blank">CHAMAR NO WHATSAPP</a>
            </div>
        """, unsafe_allow_html=True)
        # --- CONTEÚDO DA ABA CADASTRAR ---
with tab_cad:
    st.markdown("### 🚀 Cadastre seu Serviço")
    st.info("Aumente sua visibilidade e receba chamados diretos no WhatsApp.")
    
    with st.form("form_registro"):
        col_nome, col_cat = st.columns(2)
        with col_nome:
            nome_prof = st.text_input("Nome Completo ou Empresa")
        with col_cat:
            cat_prof = st.selectbox("Selecione sua Categoria", CATEGORIAS_OFICIAIS)
        
        wpp_prof = st.text_input("WhatsApp (ex: 11999999999)")
        bio_prof = st.text_area("Descreva seu serviço (Bio)", help="Destaque seus diferenciais aqui.")
        
        st.write("---")
        st.markdown("#### 📍 Sua Localização")
        st.caption(f"Capturado automaticamente: {lat_usuario}, {lon_usuario}")
        
        btn_finalizar = st.form_submit_button("CRIAR MEU PERFIL")
        
        if btn_finalizar:
            if nome_prof and wpp_prof:
                # Proteção contra scripts
                nome_limpo = scan_virus_e_scripts(nome_prof)
                
                dados = {
                    "nome": nome_limpo,
                    "categoria": cat_prof,
                    "whatsapp": wpp_prof,
                    "bio": bio_prof,
                    "lat": lat_usuario,
                    "lon": lon_usuario,
                    "moedas": 0,
                    "status": "pendente",
                    "data": datetime.now(pytz.timezone('America/Sao_Paulo'))
                }
                
                # Salva no Firestore
                db.collection("profissionais").add(dados)
                st.success("✅ Cadastro enviado com sucesso! Aguarde a aprovação do Admin.")
            else:
                st.warning("⚠️ Por favor, preencha o Nome e o WhatsApp.")

# --- CONTEÚDO DA ABA PERFIL ---
with tab_perfil:
    st.write("### 👤 Meu Perfil")
    st.write("Em breve: Gerencie seus dados e veja seu saldo de moedas aqui.")
    # --- CONTEÚDO DA ABA ADMIN ---
with tab_admin:
    st.write("### 👑 Painel de Controle (ADMIN)")
    acesso_adm = st.text_input("Senha Administrativa", type="password", key="sec_adm")
    
    if acesso_adm == "mumias":
        st.success("Acesso autorizado, Mestre!")
        # Busca cadastros pendentes
        pendentes = db.collection("profissionais").where("status", "==", "pendente").stream()
        
        cont = 0
        for p in pendentes:
            cont += 1
            item = p.to_dict()
            with st.expander(f"Aprovar: {item['nome']}"):
                st.write(f"**Categoria:** {item['categoria']}")
                st.write(f"**Bio:** {item['bio']}")
                if st.button(f"APROVAR {item['nome']}", key=p.id):
                    db.collection("profissionais").document(p.id).update({"status": "ativo"})
                    st.rerun()
        if cont == 0:
            st.info("Não há novos profissionais aguardando aprovação.")
    elif acesso_adm:
        st.error("Senha incorreta.")

# --- CONTEÚDO DA ABA FINANCEIRA (COMANDO SECRETO) ---
if "📊 FINANCEIRO" in lista_abas:
    with tab_extra[0]:
        st.markdown("## 📊 Gestão Financeira")
        col_f1, col_f2 = st.columns(2)
        col_f1.metric("Total de Moedas em Circulação", "1,250 🪙")
        col_f2.metric("Conversão de Leads (Mês)", "85%", "+5%")
        
        st.write("---")
        st.write("Aqui você poderá gerenciar pagamentos e planos de destaque em breve.")

# Rodapé Profissional
st.markdown("---")
st.caption("© 2026 GeralJá - Transformando a busca por serviços locais.")
