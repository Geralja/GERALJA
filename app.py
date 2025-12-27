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
        json_data = base64.decode(b64_data).decode("utf-8")
        info_chave = json.loads(json_data)
        cred = credentials.Certificate(info_chave)
        firebase_admin.initialize_app(cred)
    except: st.stop()

db = firestore.client()

# --- CONFIGURAÇÕES FIXAS (NÃO REMOVER) ---
PIX_CHAVE = "11991853488"
ZAP_ADMIN = "5511991853488"
VALOR_CLIQUE = 1 
BONUS_INICIAL = 5

# --- LISTA COMPLETA DE PROFISSÕES (RESTAURADA) ---
LISTA_PROFISSOES = sorted(list(set([
    "Ajudante Geral", "Almoxarife", "Antropólogo", "Arquiteto", "Azulejista", "Babá", "Barbeiro", 
    "Barman", "Bartender", "Bibliotecário", "Borracheiro", "Cabeleireiro", "Carpinteiro", "Churrasqueiro",
    "Confeiteira", "Costureira", "Cozinheira", "Curador de Museu", "Diarista", "Doméstica", "Eletricista", 
    "Encanador", "Esteticista", "Fisioterapeuta", "Geógrafo", "Gesseiro", "Guia Turístico", "Historiador", 
    "Jardineiro", "Manicure", "Marceneiro", "Marinheiro", "Mecânico", "Montador de Móveis", "Motorista", 
    "Nutricionista", "Padeiro", "Pedreiro", "Piloto de Avião", "Pintor", "Psicólogo", "Serralheiro", 
    "Sociólogo", "Técnico em TI", "Vendedor", "Vigilante", "Guarda Florestal", "Agente de Tráfico",
    "Especialista em IA", "Desenvolvedor Mobile", "Analista de Redes", "Especialista em UX/UI", "Game Designer",
    "Fonoaudiólogo", "Terapeuta Holístico", "Massagista", "Acupuncturista", "Médico Especialista", "Enfermeiro Chefe", 
    "Executivo de Vendas", "Gerente de Projetos", "Analista de RH", "Consultor de Gestão", "Economista", 
    "Ator/Atriz de Teatro", "Dançarino", "Coreógrafo", "Produtor de Vídeo", "Roteirista", "Compositor", "Cantor(a)",
    "Atleta Profissional", "Treinador", "Árbitro", "Professor Universitário", "Tutor", "Biólogo", "Engenheiro Ambiental",
    "Segurança Pessoal", "Consultor de Segurança", "Perito Forense", "Investigador"
])))

# --- ESTILO ---
st.markdown(f"""
    <style>
    .azul {{ color: #0047AB; font-size: 40px; font-weight: 900; }}
    .laranja {{ color: #FF8C00; font-size: 40px; font-weight: 900; }}
    .card-pro {{ background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px; border-left: 8px solid #0047AB; }}
    .coin-box {{ background: #FFF9C4; color: #F57F17; padding: 20px; border-radius: 15px; text-align: center; font-weight: bold; font-size: 28px; border: 2px solid #F57F17; }}
    .btn-zap {{ background-color: #25D366; color: white !important; padding: 12px; border-radius: 10px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; }}
    </style>
""", unsafe_allow_html=True)

st.markdown('<center><span class="azul">GERAL</span><span class="laranja">JÁ</span></center>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🔍 BUSCAR SERVIÇO", "🏦 MINHA CARTEIRA", "👥 MURAL"])

# --- TAB 1: BUSCA ---
with tab1:
    escolha = st.selectbox("O que você procura no Grajaú?", [""] + LISTA_PROFISSOES)
    if escolha:
        profs = db.collection("profissionais").where("area", "==", escolha).where("aprovado", "==", True).stream()
        for p in profs:
            d = p.to_dict()
            pid, saldo = p.id, d.get("saldo", 0)
            st.markdown(f'<div class="card-pro"><b>👤 {d["nome"]}</b><br>Saldo disponível: {saldo} GC</div>', unsafe_allow_html=True)
            if saldo >= VALOR_CLIQUE:
                if st.button(f"LIBERAR WHATSAPP: {d['nome'].upper()}", key=pid):
                    db.collection("profissionais").document(pid).update({"saldo": firestore.Increment(-VALOR_CLIQUE)})
                    st.success("Contato Liberado!")
                    st.markdown(f'👉 [ABRIR WHATSAPP](https://wa.me/55{"".join(filter(str.isdigit, d["whatsapp"]))})')
            else: st.warning("Este profissional está sem créditos no momento.")

# --- TAB 2: CARTEIRA + CADASTRO UNIFICADO ---
with tab2:
    st.subheader("🏦 Portal do Profissional")
    login = st.text_input("Acesse ou Cadastre-se com seu WhatsApp:", placeholder="Ex: 11991853488")
    
    if login:
        user_doc = db.collection("profissionais").document(login).get()
        
        if user_doc.exists:
            # --- TELA DE SALDO (USUÁRIO JÁ CADASTRADO) ---
            u = user_doc.to_dict()
            st.markdown(f"### Bem-vindo, {u['nome']}!")
            st.markdown(f'<div class="coin-box">{u.get("saldo", 0)} GeralCoins</div>', unsafe_allow_html=True)
            
            st.divider()
            st.write("### 🛒 Recarregar Saldo")
            c_qr, c_txt = st.columns([1,1])
            with c_qr:
                qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={PIX_CHAVE}"
                st.image(qr_url, caption="QR CODE PIX")
            with c_txt:
                st.markdown(f"**PIX Celular:** `{PIX_CHAVE}`")
                st.write("Após pagar, envie o comprovante:")
                link_comprovante = f"https://wa.me/{ZAP_ADMIN}?text=Envio comprovante de recarga para o Zap: {login}"
                st.markdown(f'<a href="{link_comprovante}" class="btn-zap">ENVIAR COMPROVANTE</a>', unsafe_allow_html=True)
        
        else:
            # --- TELA DE CADASTRO (USUÁRIO NOVO) ---
            st.warning("WhatsApp não encontrado. Cadastre seu perfil profissional abaixo:")
            with st.form("unificado_cad"):
                novo_nome = st.text_input("Seu Nome Completo")
                nova_area = st.selectbox("Sua Profissão", LISTA_PROFISSOES)
                st.info(f"🎁 Ao se cadastrar, você ganha {BONUS_INICIAL} GeralCoins de bônus!")
                
                if st.form_submit_button("CRIAR MEU PERFIL"):
                    if novo_nome:
                        db.collection("profissionais").document(login).set({
                            "nome": novo_nome, "whatsapp": login, "area": nova_area,
                            "saldo": BONUS_INICIAL, "aprovado": True, "data": datetime.datetime.now()
                        })
                        st.success("Cadastro realizado com sucesso! Atualizando sua carteira...")
                        st.rerun()
                    else: st.error("Por favor, preencha seu nome.")

# --- TAB 3: MURAL ---
with tab3:
    st.info("O Mural Social está em manutenção.")
