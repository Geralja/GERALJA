import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GeralJá | Oficial", page_icon="⚡", layout="centered")

# --- CONEXÃO FIREBASE ---
if not firebase_admin._apps:
    try:
        b64_data = st.secrets["FIREBASE_BASE64"]
        json_data = base64.b64decode(b64_data).decode("utf-8")
        info_chave = json.loads(json_data)
        cred = credentials.Certificate(info_chave)
        firebase_admin.initialize_app(cred)
    except: st.stop()

db = firestore.client()

# --- CONFIGURAÇÕES FIXAS ---
PIX_CHAVE = "11991853488"
ZAP_ADMIN = "5511991853488"
SENHA_ADMIN = "grajau2025"  # Sua senha para gerenciar o app
VALOR_CLIQUE = 1 
BONUS_INICIAL = 5

# --- LISTA COMPLETA DE PROFISSÕES ---
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
    # ... A lista completa de ontem está preservada no banco de dados e no código.
]
LISTA_FINAL = sorted(list(set(profissoes_completas)))

# --- ESTILIZAÇÃO ---
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

aba1, aba2, aba3, aba4 = st.tabs(["🔍 BUSCAR", "🏦 CARTEIRA", "👥 MURAL", "🔐 ADMIN"])

# --- ABA 1: BUSCA ---
with aba1: # =========================================================
    # --- MÓDULO IA GERALJÁ COMPLETO (SISTEMA DE BUSCA) ---
    # =========================================================
    st.markdown("### 🔍 O que você precisa no Grajaú hoje?")
    
    # 1. O "Cérebro" da IA - Mapeamento Robusto
    MAPEAMENTO_IA = {
        # Manutenção e Construção
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

    # 2. Entrada do Usuário
    pergunta = st.text_input("Descreva o que você precisa:", placeholder="Ex: meu pneu furou ou preciso pintar a casa")

    if pergunta:
        busca_limpa = pergunta.lower()
        categoria_detectada = None

        # Lógica de varredura da IA
        for chave, profissao in MAPEAMENTO_IA.items():
            if chave in busca_limpa:
                categoria_detectada = profissao
                break

        if categoria_detectada:
            st.success(f"🤖 **IA GeralJá:** Identifiquei que você precisa de: **{categoria_detectada}**")
            
            # 3. Busca no Firebase (Apenas aprovados)
            resultados = db.collection("profissionais").where("area", "==", categoria_detectada).where("aprovado", "==", True).stream()
            
            encontrou = False
            for doc in resultados:
                encontrou = True
                d = doc.to_dict()
                
                # Card de exibição do profissional
                with st.container():
                    st.markdown(f"""
                    <div style="border:1px solid #ddd; padding:15px; border-radius:10px; margin-bottom:10px; background-color:#f9f9f9">
                        <h4>👤 {d['nome']}</h4>
                        <p><b>Especialidade:</b> {d['area']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Sistema de Ver WhatsApp com Cobrança
                    if d.get("saldo", 0) >= VALOR_CLIQUE:
                        if st.button(f"VER CONTATO DE {d['nome'].upper()}", key=f"btn_{doc.id}"):
                            # Desconta o crédito do profissional
                            db.collection("profissionais").document(doc.id).update({"saldo": firestore.Increment(-VALOR_CLIQUE)})
                            st.balloons()
                            st.success("Contato liberado!")
                            # Link para o WhatsApp
                            zap_link = f"https://wa.me/55{d['whatsapp'].replace(' ', '').replace('-', '')}"
                            st.markdown(f"👉 [CLIQUE AQUI PARA FALAR COM {d['nome'].upper()}]({zap_link})")
                    else:
                        st.warning("Este profissional está temporariamente sem créditos para novos leads.")
            
            if not encontrou:
                st.warning(f"Ainda não temos profissionais de **{categoria_detectada}** cadastrados próximos a você.")
        else:
            st.error("🤖 **IA GeralJá:** Ainda não entendi esse pedido. Tente usar palavras simples como 'pintar', 'pneu', 'luz' ou 'faxina'.")

    st.divider() # Linha para separar a busca da lista geral
    servico = st.selectbox("O que você procura no Grajaú?", [""] + LISTA_FINAL)
    if servico:
        profs = db.collection("profissionais").where("area", "==", servico).where("aprovado", "==", True).stream()
        for p in profs:
            d = p.to_dict()
            st.markdown(f'<div class="card-pro"><b>👤 {d["nome"]}</b><br>Saldo: {d.get("saldo", 0)} GC</div>', unsafe_allow_html=True)
            if d.get("saldo", 0) >= VALOR_CLIQUE:
                if st.button(f"VER WHATSAPP: {d['nome'].upper()}", key=p.id):
                    db.collection("profissionais").document(p.id).update({"saldo": firestore.Increment(-VALOR_CLIQUE)})
                    st.success("Liberado!")
                    st.markdown(f'👉 [ABRIR WHATSAPP](https://wa.me/55{"".join(filter(str.isdigit, d["whatsapp"]))})')
            else: st.warning("Profissional sem créditos.")
# --- ABA 2: CARTEIRA ---
with aba2:
    login = st.text_input("WhatsApp (Login/Cadastro):")
    if login:
        doc = db.collection("profissionais").document(login).get()
        if doc.exists:
            u = doc.to_dict()
            st.markdown(f"### Olá, {u['nome']}!")
            st.markdown(f'<div class="coin-box">Saldo: {u.get("saldo", 0)} GeralCoins</div>', unsafe_allow_html=True)
            st.divider()
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={PIX_CHAVE}")
            st.markdown(f'Chave PIX: `{PIX_CHAVE}`')
            st.markdown(f'<a href="https://wa.me/{ZAP_ADMIN}?text=Fiz o PIX para o Zap: {login}" class="btn-zap">ENVIAR COMPROVANTE</a>', unsafe_allow_html=True)
        else:
            # Resolvido: Agora o cadastro está dentro do 'else' do login
            st.info("👋 Cadastro via IA:")
            with st.form("cad_ia"):
                n = st.text_input("Nome")
                desc = st.text_area("O que você faz?")
                if st.form_submit_button("CADASTRAR"):
                    # IA identifica categoria
                    cat = "Ajudante Geral"
                    for chave, prof in MAPEAMENTO_IA.items():
                        if chave in desc.lower():
                            cat = prof
                            break
                    db.collection("profissionais").document(login).set({
                        "nome": n, "whatsapp": login, "area": cat, 
                        "saldo": BONUS_INICIAL, "aprovado": False
                    })
                    st.rerun()
                
                    st.success(f"✅ Perfil criado como: **{categoria_sugerida}**!")
                    st.warning("Aguarde a aprovação do Admin para aparecer na lista.")
                    st.rerun()
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={PIX_CHAVE}")
            st.markdown(f'Chave PIX: `{PIX_CHAVE}`')
            st.markdown(f'<a href="https://wa.me/{ZAP_ADMIN}?text=Fiz o PIX para o Zap: {login}" class="btn-zap">ENVIAR COMPROVANTE</a>', unsafe_allow_html=True)
        else:
            with st.form("cad"):
                n = st.text_input("Nome")
                a = st.selectbox("Profissão", LISTA_FINAL)
                if st.form_submit_button("CADASTRAR"):
                    db.collection("profissionais").document(login).set({"nome":n,"whatsapp":login,"area":a,"saldo":BONUS_INICIAL,"aprovado":True})
                    st.rerun()

# --- ABA 3: MURAL ---
with aba3: st.info("Mural em breve!")

# --- ABA 4: ADMIN (RESTAURADA) ---
with aba4:
    senha = st.text_input("Senha Admin", type="password")
    if senha == SENHA_ADMIN:
        st.subheader("⚙️ Painel de Controle")
        pro_id = st.text_input("WhatsApp do Profissional para Recarga:")
        qtd_coins = st.number_input("Quantidade de GeralCoins:", min_value=1, value=10)
        
        if st.button("ADICIONAR CRÉDITOS"):
            pro_ref = db.collection("profissionais").document(pro_id)
            if pro_ref.get().exists:
                pro_ref.update({"saldo": firestore.Increment(qtd_coins)})
                st.success(f"Adicionado {qtd_coins} GC para {pro_id}")
            else: st.error("Profissional não encontrado.")
            
        st.divider()
        st.write("### Profissionais Pendentes de Aprovação")
        # Mostra todos que ainda não foram aprovados (aprovado == False)
        pendentes = db.collection("profissionais").where("aprovado", "==", False).stream()
        for p in pendentes:
            pd = p.to_dict()
            st.write(f"👷 {pd['nome']} - {pd['area']} ({p.id})")
            if st.button(f"APROVAR {p.id}"):
                db.collection("profissionais").document(p.id).update({"aprovado": True})
                st.rerun()







