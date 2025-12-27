import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime

# --- 1. CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="GeralJá | Oficial", page_icon="⚡", layout="centered")

# --- 2. CONEXÃO FIREBASE (Sua lógica original preservada) ---
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

# --- 5. MAPEAMENTO DA IA (Motor de Busca Otimizado) ---
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

# --- 6. ESTILIZAÇÃO CSS (Design Premium) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;900&display=swap');
    body {{ background-color: #f0f2f6; font-family: 'Roboto', sans-serif; }}
    .azul {{ color: #0047AB; font-size: 45px; font-weight: 900; letter-spacing: -2px; }}
    .laranja {{ color: #FF8C00; font-size: 45px; font-weight: 900; letter-spacing: -2px; }}
    .card-pro {{ 
        background: white; padding: 25px; border-radius: 20px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.05); margin-bottom: 20px; 
        border-left: 10px solid #0047AB; transition: transform 0.3s;
    }}
    .card-pro:hover {{ transform: translateY(-5px); }}
    .coin-box {{ 
        background: linear-gradient(135deg, #FFF9C4 0%, #FFF176 100%); 
        color: #F57F17; padding: 20px; border-radius: 15px; 
        text-align: center; font-size: 24px; font-weight: bold; border: 2px solid #F57F17; 
    }}
    .btn-zap {{ 
        background-color: #25D366; color: white !important; 
        padding: 15px; border-radius: 12px; text-decoration: none; 
        display: block; text-align: center; font-weight: bold; font-size: 18px;
    }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 10px; }}
    .stTabs [data-baseweb="tab"] {{ 
        background-color: #e0e0e0; border-radius: 10px 10px 0 0; 
        padding: 10px 20px; font-weight: bold; 
    }}
    .stTabs [aria-selected="true"] {{ background-color: #0047AB !important; color: white !important; }}
    </style>
""", unsafe_allow_html=True)

st.markdown('<center><span class="azul">GERAL</span><span class="laranja">JÁ</span><br><small>Serviços num Estalo ⚡</small></center>', unsafe_allow_html=True)
st.markdown("---")

aba1, aba2, aba3, aba4 = st.tabs(["🔍 BUSCAR", "🏦 CARTEIRA", "📝 CADASTRO", "🔐 ADMIN"])

# --- ABA 1: BUSCA INTELIGENTE ---
with aba1:
    st.markdown("### 🔍 O que você precisa hoje?")
    pergunta = st.text_input("Diga o que aconteceu:", placeholder="Ex: Preciso de um pintor ou meu cano quebrou", key="main_search")
    
    if pergunta:
        busca_limpa = pergunta.lower()
        categoria_detectada = None
        
        # Lógica de IA Robusta
        for chave, profissao in MAPEAMENTO_IA.items():
            if chave in busca_limpa:
                categoria_detectada = profissao
                break
        
        # Busca Secundária (Nome Direto)
        if not categoria_detectada:
            for p_nome in LISTA_FINAL:
                if p_nome.lower() in busca_limpa:
                    categoria_detectada = p_nome
                    break

        if categoria_detectada:
            st.success(f"🤖 **GeralJá:** Entendi! Buscando profissionais de: **{categoria_detectada}**")
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
                        st.markdown(f'<a href="https://wa.me/55{d["whatsapp"]}?text=Olá, vi seu perfil no GeralJá!" class="btn-zap">CHAMAR AGORA NO WHATSAPP</a>', unsafe_allow_html=True)
                else:
                    st.warning("Este profissional está offline no momento (sem créditos).")
            
            if count == 0:
                st.info(f"Ainda não temos profissionais aprovados para {categoria_detectada} nesta região.")
        else:
            st.error("🤖 **GeralJá:** Ainda não entendi esse pedido. Tente ser mais direto como 'Pintor' ou 'Eletricista'.")

# --- ABA 2: CARTEIRA DO PROFISSIONAL ---
with aba2:
    st.markdown("### 🏦 Área do Profissional")
    c_zap = st.text_input("WhatsApp cadastrado:", placeholder="Apenas números", key="wallet_zap")
    c_pass = st.text_input("Sua Senha:", type="password", key="wallet_pass")
    
    if c_zap and c_pass:
        u_doc = db.collection("profissionais").document(c_zap).get()
        if u_doc.exists:
            dados = u_doc.to_dict()
            if dados.get("senha") == c_pass:
                st.markdown(f"## Bem-vindo, {dados['nome']}!")
                st.markdown(f'<div class="coin-box">SALDO ATUAL: {dados.get("saldo", 0)} GeralCoins</div>', unsafe_allow_html=True)
                st.divider()
                st.markdown("### 💰 Recarregar Créditos")
                st.write("Cada clique de cliente custa 1 GeralCoin.")
                st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={PIX_CHAVE}")
                st.code(f"Chave PIX: {PIX_CHAVE}", language="text")
                st.markdown(f'<a href="https://wa.me/{ZAP_ADMIN}?text=Fiz o PIX para o WhatsApp: {c_zap}" class="btn-zap">ENVIAR COMPROVANTE</a>', unsafe_allow_html=True)
            else:
                st.error("Senha incorreta.")
        else:
            st.error("WhatsApp não encontrado no sistema.")

# --- ABA 3: NOVO CADASTRO ---
with aba3:
    st.markdown("### 📝 Junte-se ao GeralJá")
    st.write("Cadastre seus serviços e apareça para milhares de clientes.")
    
    with st.form("cad_form", clear_on_submit=True):
        n = st.text_input("Nome Completo")
        z = st.text_input("WhatsApp (com DDD, só números)")
        s = st.text_input("Crie uma Senha Forte")
        l = st.text_input("Sua Localização (Ex: Grajaú, SP)")
        a = st.selectbox("Sua Especialidade:", LISTA_FINAL)
        desc = st.text_area("Descreva seu trabalho em uma frase (IA usa isso)")
        
        enviar = st.form_submit_button("FINALIZAR CADASTRO")
        
        if enviar:
            if n and z and s:
                # Lógica IA de Cadastro
                area_final = a
                for k, v in MAPEAMENTO_IA.items():
                    if k in desc.lower(): area_final = v; break
                
                db.collection("profissionais").document(z).set({
                    "nome": n, "whatsapp": z, "senha": s, "area": area_final,
                    "localizacao": l, "saldo": BONUS_INICIAL, "aprovado": False,
                    "data": datetime.datetime.now()
                })
                st.balloons()
                st.success(f"✅ Cadastro realizado como {area_final}! Você ganhou {BONUS_INICIAL} moedas de bônus. Aguarde a ativação pelo Admin.")
            else:
                st.error("Por favor, preencha os campos obrigatórios.")

# --- ABA 4: ADMINISTRAÇÃO MASTER ---
with aba4:
    st.markdown("### 🔐 Painel de Controle")
    adm_pass = st.text_input("Senha Master:", type="password", key="adm_key")
    
    if adm_pass == SENHA_ADMIN:
        st.success("Acesso Autorizado")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Gerenciar Profissional")
            target = st.text_input("WhatsApp do Profissional:")
            if target:
                p_ref = db.collection("profissionais").document(target)
                p_doc = p_ref.get()
                if p_doc.exists:
                    p_info = p_doc.to_dict()
                    st.write(f"**Nome:** {p_info['nome']}")
                    st.write(f"**Saldo:** {p_info.get('saldo')}")
                    if st.button("PUNIR (-5 MOEDAS)"):
                        p_ref.update({"saldo": firestore.Increment(-5)})
                        st.warning("Punição aplicada!")
                        st.rerun()
                    if st.button("RESETAR SENHA (1234)"):
                        p_ref.update({"senha": "1234"})
                        st.success("Senha resetada para 1234")
        
        with col2:
            st.subheader("Aprovações Pendentes")
            pendentes = db.collection("profissionais").where("aprovado", "==", False).stream()
            for p in pendentes:
                p_data = p.to_dict()
                st.write(f"➡️ {p_data['nome']} ({p_data['area']})")
                if st.button(f"APROVAR {p_data['nome'].split()[0]}", key=f"ap_{p.id}"):
                    db.collection("profissionais").document(p.id).update({"aprovado": True})
                    st.rerun()
    elif adm_pass:
        st.error("Senha Master Incorreta.")

# --- RODAPÉ ---
st.markdown("<br><center>© 2025 GeralJá Oficial - O maior portal do Grajaú</center>", unsafe_allow_html=True)








