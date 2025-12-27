import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime

# --- 1. CONFIGURAÇÃO (Obrigatório ser o primeiro) ---
st.set_page_config(page_title="GeralJá | Oficial", page_icon="⚡", layout="centered")

# --- 2. CONEXÃO FIREBASE (Sua lógica original preservada) ---
if not firebase_admin._apps:
    try:
        b64_data = st.secrets["FIREBASE_BASE64"]
        json_data = base64.b64decode(b64_data).decode("utf-8")
        info_chave = json.loads(json_data)
        cred = credentials.Certificate(info_chave)
        firebase_admin.initialize_app(cred)
    except: st.stop()

db = firestore.client()

# --- 3. CONFIGURAÇÕES FIXAS ---
PIX_CHAVE = "11991853488"
ZAP_ADMIN = "5511991853488"
SENHA_ADMIN = "grajau2025"
VALOR_CLIQUE = 1 
BONUS_INICIAL = 5

# --- 4. LISTA COMPLETA DE PROFISSÕES (Sua lista devolvida na íntegra) ---
profissoes_completas = [
    "Ajudante Geral", "Almoxarife", "Antropólogo", "Arquiteto", "Azulejista", "Babá", "Barbeiro", 
    "Barman", "Bartender", "Bibliotecário", "Borracheiro", "Cabeleireiro", "Carpinteiro", "Churrasqueiro",
    "Confeiteira", "Costureira", "Cozinheira", "Curador de Museu", "Diarista", "Doméstica", "Eletricista", 
    "Encanador", "Esteticista", "Fonoaudiólogo", "Garçom", "Garçonete", "Geógrafo", "Gesseiro", "Guia Turístico", 
    "Historiador", "Jardineiro", "Manicure", "Marceneiro", "Marinheiro", "Massagista", "Mecânico", 
    "Médico Especialista", "Montador de Móveis", "Motorista", "Nutricionista", "Padeiro", "Pedreiro", 
    "Piloto de Avião", "Pintor", "Psicólogo", "Serralheiro", "Sociólogo", "Técnico em TI", "Vendedor", 
    "Vigilante", "Especialista em IA", "Desenvolvedor Mobile", "Analista de Redes", "Especialista em UX/UI", 
    "Game Designer", "Analista Financeiro", "Contador Público", "Gerente de Projetos", "Atleta Profissional",
    "Professor Universitário", "Biólogo", "Engenheiro Ambiental", "Segurança Pessoal", "Investigador",
    "Jornalista de TV", "Fotógrafo", "DJ", "Cantor(a)", "Designer de Interiores", "Corretor de Imóveis"
]
LISTA_FINAL = sorted(list(set(profissoes_completas)))

# --- 5. MAPEAMENTO DA IA (Todas as chaves originais) ---
MAPEAMENTO_IA = {
   "vazamento": "Encanador", "cano": "Encanador", "torneira": "Encanador", "esgoto": "Encanador", "pia": "Encanador", "privada": "Encanador", "infiltração": "Encanador",
        "curto": "Eletricista", "luz": "Eletricista", "tomada": "Eletricista", "chuveiro": "Eletricista", "fiação": "Eletricista", "disjuntor": "Eletricista", "lâmpada": "Eletricista",
        "pintar": "Pintor", "parede": "Pintor", "massa": "Pintor", "grafiato": "Pintor", "verniz": "Pintor",
        "reforma": "Pedreiro", "laje": "Pedreiro", "tijolo": "Pedreiro", "reboco": "Pedreiro", "piso": "Pedreiro", "azulejo": "Pedreiro", "cimento": "Pedreiro", "muro": "Pedreiro",
        "telhado": "Telhadista", "calha": "Telhadista", "goteira": "Telhadista",
        "montar": "Montador de Móveis", "armário": "Montador de Móveis", "guarda-roupa": "Montador de Móveis", "cozinha": "Montador de Móveis",

        # Beleza e Estética
        "unha": "Manicure", "pé": "Manicure", "mão": "Manicure", "esmalte": "Manicure", "gel": "Manicure",
        "cabelo": "Cabeleireiro", "corte": "Cabeleireiro", "escova": "Cabeleireiro", "tintura": "Cabeleireiro", "luzes": "Cabeleireiro",
        "barba": "Barbeiro", "degradê": "Barbeiro", "navalha": "Barbeiro",
        "sobrancelha": "Esteticista", "cílios": "Esteticista", "maquiagem": "Esteticista", "depilação": "Esteticista", "pele": "Esteticista",

        # Serviços Domésticos
        "faxina": "Diarista", "limpeza": "Diarista", "passar": "Diarista", "lavar": "Diarista", "organizar": "Diarista",
        "carreto": "Ajudante Geral", "mudança": "Ajudante Geral", "entulho": "Ajudante Geral", "carregar": "Ajudante Geral", "bico": "Ajudante Geral",
        "jardim": "Jardineiro", "grama": "Jardineiro", "poda": "Jardineiro",

        # Tecnologia e Eletrônicos
        "computador": "Técnico de TI", "celular": "Técnico de TI", "formatar": "Técnico de TI", "notebook": "Técnico de TI", "tela": "Técnico de TI", "wifi": "Técnico de TI", "internet": "Técnico de TI",
        "televisão": "Técnico de Eletrônicos", "tv": "Técnico de Eletrônicos", "som": "Técnico de Eletrônicos", "microondas": "Técnico de Eletrônicos",
        "geladeira": "Refrigeração", "ar condicionado": "Refrigeração", "freezer": "Refrigeração",

        # Outros e Animais
        "frete": "Motorista", "transporte": "Motorista", "viagem": "Motorista",
        "aula": "Professor Particular", "reforço": "Professor Particular", "inglês": "Professor Particular", "matemática": "Professor Particular",
        "cachorro": "Pet Shop/Passeador", "gato": "Pet Shop/Passeador", "banho": "Pet Shop/Passeador", "tosa": "Pet Shop/Passeador",

        # Automóveis e Mecânica
        "pneu": "Borracheiro", "estepe": "Borracheiro", "furou": "Borracheiro", "vulc": "Borracheiro",
        "carro": "Mecânico", "motor": "Mecânico", "óleo": "Mecânico", "freio": "Mecânico", "bateria": "Mecânico",
        "moto": "Mecânico de Motos", "corrente": "Mecânico de Motos",
        "guincho": "Guincho / Socorro 24h", "reboque": "Guincho / Socorro 24h",
        "lavar carro": "Lava Rápido", "polimento": "Lava Rápido", "estética automotiva": "Lava Rápido",

        # Eventos e Festas
        "festa": "Eventos", "bolo": "Confeiteira", "doce": "Confeiteira", "salgado": "Salgadeira",
        "música": "DJ / Músico", "som": "DJ / Músico", "fotógrafo": "Fotógrafo"
}

# --- 6. ESTILIZAÇÃO CSS ---
st.markdown(f"""
    <style>
    .azul {{ color: #0047AB; font-size: 40px; font-weight: 900; }}
    .laranja {{ color: #FF8C00; font-size: 40px; font-weight: 900; }}
    .card-pro {{ background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px; border-left: 8px solid #0047AB; }}
    .coin-box {{ background: #FFF9C4; color: #F57F17; padding: 15px; border-radius: 10px; text-align: center; font-weight: bold; border: 2px solid #F57F17; }}
    .btn-zap {{ background-color: #25D366; color: white !important; padding: 12px; border-radius: 10px; text-decoration: none; display: block; text-align: center; font-weight: bold; }}
    </style>
""", unsafe_allow_html=True)

st.markdown('<center><span class="azul">GERAL</span><span class="laranja">JÁ</span></center>', unsafe_allow_html=True)

aba1, aba2, aba3, aba4 = st.tabs(["🔍 BUSCAR", "🏦 CARTEIRA", "📝 CADASTRO", "🔐 ADMIN"])

# --- ABA 1: BUSCA COM IA ---
with aba1:
    st.markdown("### 🔍 O que você precisa hoje?")
    pergunta = st.text_input("Descreva o que você precisa:", placeholder="Ex: meu pneu furou")
    
    if pergunta:
        busca_limpa = pergunta.lower()
        categoria_detectada = None
        for chave, profissao in MAPEAMENTO_IA.items():
            if chave in busca_limpa:
                categoria_detectada = profissao
                break

        if categoria_detectada:
            st.success(f"🤖 **GeralJá:** Identifiquei que você precisa de: **{categoria_detectada}**")
            resultados = db.collection("profissionais").where("area", "==", categoria_detectada).where("aprovado", "==", True).stream()
            
            for doc in resultados:
                d = doc.to_dict()
                loc = d.get("localizacao", "Não informada")
                st.markdown(f'<div class="card-pro"><h4>👤 {d["nome"]}</h4><p>📍 <b>Local:</b> {loc}</p><p><b>Especialidade:</b> {d["area"]}</p></div>', unsafe_allow_html=True)
                if d.get("saldo", 0) >= VALOR_CLIQUE:
                    if st.button(f"VER CONTATO: {d['nome'].upper()}", key=f"src_{doc.id}"):
                        db.collection("profissionais").document(doc.id).update({"saldo": firestore.Increment(-VALOR_CLIQUE)})
                        st.success(f"👉 [FALAR NO WHATSAPP](https://wa.me/55{d['whatsapp']})")
                else:
                    st.warning("Profissional sem créditos.")
        else:
            st.error("🤖 **GeralJá:** Ainda não entendi esse pedido. Tente algo como 'Preciso de um Pedreiro'.")

# --- ABA 2: CARTEIRA (Com Senha de Usuário) ---
with aba2:
    st.subheader("🏦 Sua Carteira")
    login = st.text_input("Seu WhatsApp cadastrado:", key="login_carteira")
    senha_user = st.text_input("Sua Senha:", type="password", key="pass_carteira")
    
    if login and senha_user:
        doc = db.collection("profissionais").document(login).get()
        if doc.exists:
            u = doc.to_dict()
            if u.get("senha") == senha_user:
                st.markdown(f"### Olá, {u['nome']}!")
                st.markdown(f'<div class="coin-box">Saldo: {u.get("saldo", 0)} GeralCoins</div>', unsafe_allow_html=True)
                st.divider()
                st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={PIX_CHAVE}")
                st.markdown(f'Chave PIX: {PIX_CHAVE}')
                st.markdown(f'<a href="https://wa.me/{ZAP_ADMIN}?text=Recarga: {login}" class="btn-zap">ENVIAR COMPROVANTE</a>', unsafe_allow_html=True)
            else:
                st.error("Senha incorreta.")
        else:
            st.error("❌ WhatsApp não encontrado.")

# --- ABA 3: CADASTRO COM LISTA E IA ---
with aba3:
    st.subheader("🚀 Novo Cadastro")
    novo_zap = st.text_input("WhatsApp para novo cadastro:", key="novo_cadastro")
    if novo_zap:
        if db.collection("profissionais").document(novo_zap).get().exists:
            st.warning("Você já tem cadastro!")
        else:
            with st.form("form_ia"):
                n = st.text_input("Nome Completo")
                s = st.text_input("Crie uma Senha", type="password")
                l = st.text_input("Localização (Ex: Grajaú, SP)")
                escolha_manual = st.selectbox("Selecione sua Profissão:", LISTA_FINAL)
                desc = st.text_area("Descreva seu serviço para a IA")
                
                if st.form_submit_button("CADASTRAR"):
                    cat_final = escolha_manual
                    for k, v in MAPEAMENTO_IA.items():
                        if k in desc.lower(): cat_final = v; break
                    
                    db.collection("profissionais").document(novo_zap).set({
                        "nome": n, "whatsapp": novo_zap, "senha": s, "area": cat_final,
                        "localizacao": l, "saldo": BONUS_INICIAL, "aprovado": False
                    })
                    st.success(f"✅ Cadastrado como {cat_final}! Aguarde aprovação.")

# --- ABA 4: ADMIN MASTER (Punição e Gestão) ---
with aba4:
    senha = st.text_input("Senha Admin", type="password")
    if senha == SENHA_ADMIN:
        st.subheader("⚙️ Painel Admin")
        
        gerir_zap = st.text_input("WhatsApp para Gerenciar/Punir:")
        if gerir_zap:
            u_ref = db.collection("profissionais").document(gerir_zap)
            u_doc = u_ref.get()
            if u_doc.exists:
                ud = u_doc.to_dict()
                st.write(f"Profissional: {ud['nome']} | Saldo: {ud.get('saldo')}")
                if st.button("PUNIR (-5 COINS)"):
                    u_ref.update({"saldo": firestore.Increment(-5)})
                    st.error("Punição aplicada!")
                if st.button("RESETAR SENHA (1234)"):
                    u_ref.update({"senha": "1234"})
                    st.success("Senha resetada!")

        st.divider()
        st.write("Aprovações Pendentes:")
        pendentes = db.collection("profissionais").where("aprovado", "==", False).stream()
        for p in pendentes:
            pd = p.to_dict()
            if st.button(f"APROVAR {pd['nome']} ({pd.get('localizacao', 'N/A')})"):
                db.collection("profissionais").document(p.id).update({"aprovado": True})
                st.rerun()

