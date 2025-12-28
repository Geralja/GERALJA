import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime

# --- 1. CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="GeralJá | Oficial", page_icon="⚡", layout="centered")

# --- 2. CONEXÃO FIREBASE (Original Preservada) ---
if not firebase_admin._apps:
    try:
        b64_data = st.secrets["FIREBASE_BASE64"]
        json_data = base64.b64decode(b64_data).decode("utf-8")
        info_chave = json.loads(json_data)
        cred = credentials.Certificate(info_chave)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Erro de Conexão: {e}")
        st.stop()

db = firestore.client()

# --- 3. CONFIGURAÇÕES FIXAS ---
PIX_CHAVE = "11991853488"
ZAP_ADMIN = "5511991853488"
SENHA_ADMIN = "mumias"
VALOR_CLIQUE = 1 
BONUS_INICIAL = 5
LINK_APP = "https://geralja.streamlit.app" 

# --- 4. LISTA DE PROFISSÕES ---
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

# --- 5. MAPEAMENTO DA IA (O SEU MOTOR ORIGINAL COMPLETO) ---
MAPEAMENTO_IA = {
    "vazamento": "Encanador", "cano": "Encanador", "torneira": "Encanador", "esgoto": "Encanador", "pia": "Encanador", "privada": "Encanador", "infiltração": "Encanador",
    "curto": "Eletricista", "luz": "Eletricista", "tomada": "Eletricista", "chuveiro": "Eletricista", "fiação": "Eletricista", "disjuntor": "Eletricista", "lâmpada": "Eletricista",
    "pintar": "Pintor", "parede": "Pintor", "massa": "Pintor", "grafiato": "Pintor", "verniz": "Pintor", "pintor": "Pintor", "pintura": "Pintor",
    "reforma": "Pedreiro", "laje": "Pedreiro", "tijolo": "Pedreiro", "reboco": "Pedreiro", "piso": "Pedreiro", "azulejo": "Pedreiro", "cimento": "Pedreiro", "muro": "Pedreiro", "pedreiro": "Pedreiro",
    "telhado": "Telhadista", "calha": "Telhadista", "goteira": "Telhadista",
    "montar": "Montador de Móveis", "armário": "Montador de Móveis", "guarda-roupa": "Montador de Móveis", "cozinha": "Montador de Móveis",
    "unha": "Manicure", "pé": "Manicure", "mão": "Manicure", "esmalte": "Manicure", "gel": "Manicure", "manicure": "Manicure",
    "cabelo": "Cabeleireiro", "corte": "Cabeleireiro", "escova": "Cabeleireiro", "tintura": "Cabeleireiro", "luzes": "Cabeleireiro",
    "barba": "Barbeiro", "degradê": "Barbeiro", "navalha": "Barbeiro", "barbeiro": "Barbeiro",
    "sobrancelha": "Esteticista", "cílios": "Esteticista", "maquiagem": "Esteticista", "depilação": "Esteticista", "pele": "Esteticista",
    "faxina": "Diarista", "limpeza": "Diarista", "passar": "Diarista", "lavar": "Diarista", "organizar": "Diarista", "diarista": "Diarista",
    "carreto": "Ajudante Geral", "mudança": "Ajudante Geral", "entulho": "Ajudante Geral", "carregar": "Ajudante Geral", "bico": "Ajudante Geral",
    "jardim": "Jardineiro", "grama": "Jardineiro", "poda": "Jardineiro",
    "computador": "Técnico de TI", "celular": "Técnico de TI", "formatar": "Técnico de TI", "notebook": "Técnico de TI", "tela": "Técnico de TI", "wifi": "Técnico de TI", "internet": "Técnico de TI",
    "televisão": "Técnico de Eletrônicos", "tv": "Técnico de Eletrônicos", "som": "Técnico de Eletrônicos", "microondas": "Técnico de Eletrônicos",
    "geladeira": "Refrigeração", "ar condicionado": "Refrigeração", "freezer": "Refrigeração",
    "frete": "Motorista", "transporte": "Motorista", "viagem": "Motorista", "motorista": "Motorista",
    "aula": "Professor Particular", "reforço": "Professor Particular", "inglês": "Professor Particular", "matemática": "Professor Particular",
    "cachorro": "Pet Shop/Passeador", "gato": "Pet Shop/Passeador", "banho": "Pet Shop/Passeador", "tosa": "Pet Shop/Passeador",
    "pneu": "Borracheiro", "estepe": "Borracheiro", "furou": "Borracheiro", "vulc": "Borracheiro", "borracharia": "Borracheiro",
    "carro": "Mecânico", "motor": "Mecânico", "óleo": "Mecânico", "freio": "Mecânico", "bateria": "Mecânico",
    "moto": "Mecânico de Motos", "corrente": "Mecânico de Motos",
    "guincho": "Guincho / Socorro 24h", "reboque": "Guincho / Socorro 24h",
    "lavar carro": "Lava Rápido", "polimento": "Lava Rápido", "estética automotiva": "Lava Rápido",
    "festa": "Eventos", "bolo": "Confeiteira", "doce": "Confeiteira", "salgado": "Salgadeira",
    "música": "DJ / Músico", "som": "DJ / Músico", "fotógrafo": "Fotógrafo"
}

# --- 6. ESTILIZAÇÃO CSS (SOMANDO: BLINDAGEM PARA IPHONE) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;900&display=swap');
    body {{ background-color: #f0f2f6; font-family: 'Roboto', sans-serif; }}
    .azul {{ color: #0047AB !important; font-size: 45px; font-weight: 900; letter-spacing: -2px; }}
    .laranja {{ color: #FF8C00 !important; font-size: 45px; font-weight: 900; letter-spacing: -2px; }}
    
    .card-pro {{ 
        background: #ffffff !important; padding: 25px; border-radius: 20px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.05); margin-bottom: 20px; 
        border-left: 10px solid #0047AB; 
    }}
    .card-pro h4 {{ color: #1a1a1a !important; font-weight: bold; }}
    .card-pro p {{ color: #444444 !important; font-weight: 500; }}

    .coin-box {{ 
        background: linear-gradient(135deg, #FFF9C4 0%, #FFF176 100%); 
        color: #F57F17 !important; padding: 20px; border-radius: 15px; 
        text-align: center; font-size: 24px; font-weight: bold; border: 2px solid #F57F17; 
    }}
    .btn-zap {{ 
        background-color: #25D366; color: white !important; 
        padding: 15px; border-radius: 12px; text-decoration: none; 
        display: block; text-align: center; font-weight: bold; font-size: 18px;
    }}
    .share-btn {{
        background: linear-gradient(135deg, #0047AB 0%, #002e6e 100%);
        color: white !important; padding: 18px; border-radius: 12px; text-decoration: none; 
        display: block; text-align: center; font-weight: bold; margin-top: 20px;
    }}
    .stTabs [aria-selected="true"] {{ background-color: #0047AB !important; color: white !important; }}
    </style>
""", unsafe_allow_html=True)

st.markdown('<center><span class="azul">GERAL</span><span class="laranja">JÁ</span><br><small>Serviços num Estalo ⚡</small></center>', unsafe_allow_html=True)
st.markdown("---")

aba1, aba2, aba3, aba4 = st.tabs(["🔍 BUSCAR", "🏦 CARTEIRA", "📝 CADASTRO", "🔐 ADMIN"])

# --- ABA 1: BUSCA ---
with aba1:
    st.markdown("### 🔍 O que você precisa hoje?")
    pergunta = st.text_input("Diga o que aconteceu:", placeholder="Ex: Meu cano quebrou", key="main_search")
    
    if pergunta:
        busca_limpa = pergunta.lower()
        categoria_detectada = None
        for chave, profissao in MAPEAMENTO_IA.items():
            if chave in busca_limpa:
                categoria_detectada = profissao
                break
        if not categoria_detectada:
            for p_nome in LISTA_FINAL:
                if p_nome.lower() in busca_limpa:
                    categoria_detectada = p_nome
                    break

        if categoria_detectada:
            st.success(f"🤖 **GeralJá:** Buscando: **{categoria_detectada}**")
            profs = db.collection("profissionais").where("area", "==", categoria_detectada).where("aprovado", "==", True).stream()
            count = 0
            for doc in profs:
                count += 1
                d = doc.to_dict()
                st.markdown(f'''
                    <div class="card-pro">
                        <h4>👤 {d["nome"]}</h4>
                        <p>📍 <b>Local:</b> {d.get("localizacao", "Grajaú e Região")}</p>
                        <p>💼 <b>Especialidade:</b> {d["area"]}</p>
                    </div>
                ''', unsafe_allow_html=True)
                if d.get("saldo", 0) >= VALOR_CLIQUE:
                    if st.button(f"VER WHATSAPP DE {d['nome'].upper()}", key=f"btn_{doc.id}"):
                        db.collection("profissionais").document(doc.id).update({"saldo": firestore.Increment(-VALOR_CLIQUE)})
                        st.markdown(f'<a href="https://wa.me/55{d["whatsapp"]}?text=Olá, vi seu perfil no GeralJá!" class="btn-zap">CHAMAR NO WHATSAPP</a>', unsafe_allow_html=True)
                else: st.warning("Este profissional está offline.")
            if count == 0: st.info(f"Sem profissionais aprovados para {categoria_detectada} ainda.")

    # SOMANDO: BOTÃO VIRAL COM SUA FRASE ORIGINAL
    st.markdown("---")
    msg_viral = "Não importa o que você faz e nem onde está. Tem sempre alguém precisando de você, GeralJá. Aonde eu estiver voces tambem estarão."
    st.markdown(f'<a href="https://api.whatsapp.com/send?text={msg_viral} {LINK_APP}" target="_blank" class="share-btn">🚀 DIVULGAR O GERALJÁ</a>', unsafe_allow_html=True)

# --- ABA 2: CARTEIRA (QR CODE RESTAURADO) ---
with aba2:
    st.markdown("### 🏦 Área do Profissional")
    c_zap = st.text_input("WhatsApp cadastrado:", key="wallet_zap")
    c_pass = st.text_input("Sua Senha:", type="password", key="wallet_pass")
    if c_zap and c_pass:
        u_doc = db.collection("profissionais").document(c_zap).get()
        if u_doc.exists and u_doc.to_dict().get("senha") == c_pass:
            dados = u_doc.to_dict()
            st.markdown(f'## Bem-vindo, {dados["nome"]}!')
            st.markdown(f'<div class="coin-box">SALDO: {dados.get("saldo", 0)} Moedas</div>', unsafe_allow_html=True)
            st.divider()
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={PIX_CHAVE}")
            st.code(f"Chave PIX: {PIX_CHAVE}")
            st.markdown(f'<a href="https://wa.me/{ZAP_ADMIN}?text=Fiz o PIX para: {c_zap}" class="btn-zap">ENVIAR COMPROVANTE</a>', unsafe_allow_html=True)

# --- ABA 3: CADASTRO (LÓGICA IA RESTAURADA) ---
with aba3:
    st.markdown("### 📝 Junte-se ao GeralJá")
    with st.form("cad_form", clear_on_submit=True):
        n = st.text_input("Nome Completo")
        z = st.text_input("WhatsApp (só números)")
        s = st.text_input("Crie uma Senha")
        l = st.text_input("Sua Localização")
        a = st.selectbox("Especialidade Principal", LISTA_FINAL)
        desc = st.text_area("Descreva seu trabalho (IA ajuda a te classificar)")
        if st.form_submit_button("FINALIZAR CADASTRO"):
            if n and z and s:
                # Sua lógica original de detecção automática na descrição
                area_final = a
                for k, v in MAPEAMENTO_IA.items():
                    if k in desc.lower(): area_final = v; break
                db.collection("profissionais").document(z).set({
                    "nome": n, "whatsapp": z, "senha": s, "area": area_final,
                    "localizacao": l, "saldo": BONUS_INICIAL, "aprovado": False, "data": datetime.datetime.now()
                })
                st.balloons()
                st.success(f"✅ Sucesso! Cadastrado como {area_final}. Aguarde ativação.")

# --- ABA 4: ADMIN ---
with aba4:
    st.markdown("### 🔐 Painel Master")
    adm_pass = st.text_input("Senha Master:", type="password")
    if adm_pass == SENHA_ADMIN:
        col1, col2 = st.columns(2)
        with col1:
            target = st.text_input("Zap do Profissional:")
            if target:
                p_ref = db.collection("profissionais").document(target)
                if p_ref.get().exists:
                    if st.button("PUNIR (-5)"): p_ref.update({"saldo": firestore.Increment(-5)}); st.rerun()
                    if st.button("RESET SENHA (1234)"): p_ref.update({"senha": "1234"}); st.success("Senha: 1234")
        with col2:
            pendentes = db.collection("profissionais").where("aprovado", "==", False).stream()
            for p in pendentes:
                if st.button(f"APROVAR {p.to_dict()['nome']}", key=f"ap_{p.id}"):
                    db.collection("profissionais").document(p.id).update({"aprovado": True}); st.rerun()

st.markdown("<br><center>© 2025 GeralJá Oficial - O maior portal do Grajaú</center>", unsafe_allow_html=True)
