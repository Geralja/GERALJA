# ==============================================================================
# GERALJÁ BRASIL - SUPREME EDITION v25.0 (INTEGRAÇÃO TOTAL E SEM CORTES)
# ==============================================================================
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

# 1. ARQUITETURA E METADADOS
st.set_page_config(
    page_title="GeralJá | Profissionais do Brasil",
    page_icon="🏙️",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://wa.me/5511991853488',
        'Report a bug': 'https://wa.me/5511991853488',
        'About': "GeralJá v25.0 - Ecossistema Nacional de Serviços."
    }
)

# 2. CAMADA DE PERSISTÊNCIA (FIREBASE SINGLETON)
@st.cache_resource
def inicializar_infraestrutura_dados():
    if not firebase_admin._apps:
        try:
            b64_key = st.secrets["FIREBASE_BASE64"]
            decoded_json = base64.b64decode(b64_key).decode("utf-8")
            cred_dict = json.loads(decoded_json)
            credenciais = credentials.Certificate(cred_dict)
            return firebase_admin.initialize_app(credenciais)
        except Exception as erro_fatal:
            st.error(f"⚠️ FALHA DE INFRAESTRUTURA: {erro_fatal}")
            st.stop()
    return firebase_admin.get_app()

app_engine = inicializar_infraestrutura_dados()
db = firestore.client()

# 3. CONSTANTES E REGRAS FINANCEIRAS (ORIGINAIS)
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ACESSO_ADMIN = "mumias"
TAXA_CONTATO = 1
BONUS_WELCOME = 5
URL_APLICATIVO = "https://geralja.streamlit.app"
DISTINTIVO_SISTEMA = "BUILD 2025.25 - NACIONAL GOLD"
LAT_SP_REF, LON_SP_REF = -23.5505, -46.6333
LISTA_ESTADOS = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]

# 4. MOTOR DE IA (PROFISSÕES MASSIVAS)
CONCEITOS_SERVICOS = {
    # INFRA E HIDRÁULICA
    "vazamento": "Encanador", "cano": "Encanador", "torneira": "Encanador", "esgoto": "Encanador", "pia": "Encanador", 
    "privada": "Encanador", "caixa d'água": "Encanador", "infiltração": "Encanador", "registro": "Encanador",
    "hidrante": "Bombeiro Civil", "bombeiro": "Bombeiro Civil", "desentupir": "Desentupidora",
    # ELÉTRICA
    "curto": "Eletricista", "luz": "Eletricista", "tomada": "Eletricista", "chuveiro": "Eletricista", "fiação": "Eletricista", 
    "disjuntor": "Eletricista", "lâmpada": "Eletricista", "ar condicionado": "Técnico de Ar Condicionado",
    # CONSTRUÇÃO
    "pintar": "Pintor", "parede": "Pintor", "massa": "Pintor", "grafiato": "Pintor", "verniz": "Pintor", "pintura": "Pintor", 
    "reforma": "Pedreiro", "laje": "Pedreiro", "tijolo": "Pedreiro", "reboco": "Pedreiro", "piso": "Pedreiro", 
    "azulejo": "Pedreiro", "cimento": "Pedreiro", "muro": "Pedreiro", "pedreiro": "Pedreiro", "gesso": "Gesseiro",
    "drywall": "Gesseiro", "sanca": "Gesseiro", "moldura": "Gesseiro", "porcelanato": "Pedreiro", "telhado": "Telhadista", 
    "calha": "Telhadista", "goteira": "Telhadista", "telha": "Telhadista", "serralheiro": "Serralheiro", "portão": "Serralheiro",
    # BELEZA E PESSOAL
    "unha": "Manicure", "pé": "Manicure", "mão": "Manicure", "esmalte": "Manicure", "gel": "Manicure", 
    "alongamento": "Manicure", "cabelo": "Cabeleireiro", "corte": "Cabeleireiro", "escova": "Cabeleireiro", 
    "tintura": "Cabeleireiro", "luzes": "Cabeleireiro", "barba": "Barbeiro", "degradê": "Barbeiro", "navalha": "Barbeiro",
    # DOMÉSTICOS
    "faxina": "Diarista", "limpeza": "Diarista", "passar": "Diarista", "lavar": "Diarista", "doméstica": "Doméstica", 
    "babá": "Babá", "jardim": "Jardineiro", "grama": "Jardineiro", "piscina": "Piscineiro",
    # AUTOMOTIVO
    "pneu": "Borracheiro", "estepe": "Borracheiro", "furou": "Borracheiro", "carro": "Mecânico", "motor": "Mecânico", 
    "óleo": "Mecânico", "moto": "Mecânico de Motos", "guincho": "Guincho / Socorro 24h",
    # TECNOLOGIA E OUTROS
    "computador": "Técnico de TI", "celular": "Técnico de TI", "geladeira": "Refrigeração", "festa": "Eventos", 
    "bolo": "Confeiteira", "aula": "Professor Particular", "montar": "Montador de Móveis", "armário": "Montador de Móveis"
}

# 5. FUNÇÕES CORE E AUDITORIA (RECUPERADAS)
def processar_servico_ia(texto_cliente):
    if not texto_cliente: return "Ajudante Geral"
    t_clean = texto_cliente.lower().strip()
    for key, prof in CONCEITOS_SERVICOS.items():
        if re.search(rf"\b{key}\b", t_clean): return prof
    return "Ajudante Geral"

def calcular_km_sp(lat1, lon1, lat2, lon2):
    R_RAIO = 6371 
    d_lat, d_lon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2)**2)
    return round(R_RAIO * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))), 1)

def tabela_precos_sp(categoria_ia):
    precos = {
        "Encanador": "R$ 90 - R$ 350", "Eletricista": "R$ 100 - R$ 450",
        "Diarista": "R$ 160 - R$ 250", "Mecânico": "R$ 150 - R$ 800",
        "Manicure": "R$ 50 - R$ 130", "Pedreiro": "R$ 160 - R$ 300/dia"
    }
    return precos.get(categoria_ia, "Sob consulta")

def executar_limpeza_banco(db_instancia):
    try:
        profs_ref = db_instancia.collection("profissionais").stream()
        correcoes = 0
        for doc in profs_ref:
            d, upd = doc.to_dict(), {}
            if "rating" not in d: upd["rating"] = 5.0
            if "saldo" not in d: upd["saldo"] = BONUS_WELCOME
            if "cliques" not in d: upd["cliques"] = 0
            if "foto_url" not in d: upd["foto_url"] = ""
            if "aprovado" not in d: upd["aprovado"] = False
            if upd:
                db_instancia.collection("profissionais").document(doc.id).update(upd)
                correcoes += 1
        return f"✔️ Integridade Garantida: {correcoes} perfis ajustados."
    except Exception as e: return f"⚠️ Erro na auditoria: {e}"

# 6. ESTILIZAÇÃO CSS (ORIGINAL PREMIUM)
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap');
    * {{ font-family: 'Montserrat', sans-serif; }}
    .stApp {{ background-color: #FAFAFA; }}
    .header-box {{ text-align: center; padding: 20px 0; }}
    .txt-azul {{ color: #0047AB !important; font-size: 55px; font-weight: 900; letter-spacing: -3px; }}
    .txt-laranja {{ color: #FF8C00 !important; font-size: 55px; font-weight: 900; letter-spacing: -3px; }}
    .txt-sub-sp {{ color: #555; font-size: 14px; font-weight: 700; text-transform: uppercase; letter-spacing: 6px; margin-top: -20px; }}
    .card-vazado {{ background: #FFFFFF; border-radius: 25px; padding: 25px; margin-bottom: 20px; box-shadow: 0 8px 25px rgba(0,0,0,0.05); border-left: 15px solid #0047AB; display: flex; align-items: center; transition: 0.3s; }}
    .avatar-pro {{ width: 95px; height: 95px; border-radius: 50%; object-fit: cover; margin-right: 25px; border: 5px solid #F8F9FA; }}
    .badge-km {{ background: #EBF4FF; color: #0047AB; padding: 5px 15px; border-radius: 12px; font-size: 11px; font-weight: 900; }}
    .btn-wpp-link {{ background-color: #25D366; color: white !important; padding: 15px; border-radius: 15px; text-decoration: none; display: block; text-align: center; font-weight: 900; margin-top: 15px; font-size: 15px; }}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-box"><span class="txt-azul">GERAL</span><span class="txt-laranja">JÁ</span></div>', unsafe_allow_html=True)
st.markdown('<center><p class="txt-sub-sp">Brasil Profissional</p></center>', unsafe_allow_html=True)

# 7. NAVEGAÇÃO BLINDADA (UI_ABAS)
UI_ABAS = st.tabs(["🔍 BUSCAR SERVIÇO", "💼 MINHA CONTA", "📝 CADASTRAR", "🛡️ ADMIN"])

# --- ABA 1: CLIENTE (BUSCA) ---
with UI_ABAS[0]:
    st.write("### 🏙️ O que você procura hoje?")
    col_cid, col_ser = st.columns([1, 2])
    busca_cidade = col_cid.text_input("Sua Cidade", placeholder="Ex: São Paulo")
    termo_busca = col_ser.text_input("Ex: Chuveiro, Pintor ou Borracheiro", key="main_search")
    
    if termo_busca:
        classe_servico = processar_servico_ia(termo_busca)
        valor_referencia = tabela_precos_sp(classe_servico)
        st.info(f"🤖 IA: Localizamos profissionais de **{classe_servico}**.\n\n💰 Média: **{valor_referencia}**")
        
        query = db.collection("profissionais").where("area", "==", classe_servico).where("aprovado", "==", True).stream()
        lista_profs = []
        for doc in query:
            p = doc.to_dict()
            p['doc_id'] = doc.id
            if not busca_cidade or busca_cidade.lower() in p.get('localizacao', '').lower() or busca_cidade.lower() in p.get('cidade', '').lower():
                p['distancia'] = calcular_km_sp(LAT_SP_REF, LON_SP_REF, p.get('lat', LAT_SP_REF), p.get('lon', LON_SP_REF))
                lista_profs.append(p)
        
        lista_profs.sort(key=lambda x: (x['distancia'], -x.get('rating', 5.0)))
        
        for pro_item in lista_profs:
            url_img = pro_item.get('foto_url', '')
            img_html = f'<img src="{url_img}" class="avatar-pro">' if url_img else '<div class="avatar-pro" style="background:#eee; display:flex; align-items:center; justify-content:center; font-size:35px;">👤</div>'
            estrelas = "⭐" * int(pro_item.get('rating', 5.0))
            
            st.markdown(f'''
                <div class="card-vazado">
                    {img_html}
                    <div style="flex-grow: 1;">
                        <span class="badge-km">📍 {pro_item.get('localizacao', 'Brasil')} | {pro_item['distancia']} KM</span>
                        <h4 style="margin:5px 0; color:#333;">{pro_item['nome']}</h4>
                        <div style="color:#FFB400; font-size:12px;">{estrelas} ({round(pro_item.get('rating', 5.0), 1)})</div>
                        <p style="margin:5px 0; color:#666; font-size:13px;">🛠️ <b>{pro_item['area']}</b></p>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
            
            if pro_item.get('saldo', 0) >= TAXA_CONTATO:
                if st.button(f"FALAR COM {pro_item['nome'].upper()}", key=f"act_{pro_item['doc_id']}"):
                    db.collection("profissionais").document(pro_item['doc_id']).update({"saldo": firestore.Increment(-TAXA_CONTATO), "cliques": firestore.Increment(1)})
                    st.markdown(f'<a href="https://wa.me/55{pro_item["whatsapp"]}?text=Olá, vi seu perfil no GeralJá!" class="btn-wpp-link">ABRIR WHATSAPP</a>', unsafe_allow_html=True)
            else: st.error("Profissional atingiu o limite de contatos por hoje.")

# --- ABA 2: PROFISSIONAL (FINANCEIRO/LOGIN) ---
with UI_ABAS[1]:
    st.subheader("💼 Área do Parceiro")
    col_l1, col_l2 = st.columns(2)
    zap_login = col_l1.text_input("WhatsApp:", placeholder="11999998888", key="login_z")
    pass_login = col_l2.text_input("Senha:", type="password", key="login_p")
    
    if zap_login and pass_login:
        ref_p = db.collection("profissionais").document(zap_login).get()
        if ref_p.exists and ref_p.to_dict()['senha'] == pass_login:
            dados_p = ref_p.to_dict()
            st.success(f"Logado: {dados_p['nome']}")
            m1, m2, m3 = st.columns(3)
            m1.metric("Minhas Moedas 🪙", dados_p.get('saldo', 0))
            m2.metric("Avaliação ⭐", round(dados_p.get('rating', 5.0), 1))
            m3.metric("Leads Ganhos 📈", dados_p.get('cliques', 0))
            
            st.divider()
            nova_f = st.text_input("Link da Foto de Perfil:", value=dados_p.get('foto_url', ''))
            if st.button("Salvar Foto"):
                db.collection("profissionais").document(zap_login).update({"foto_url": nova_f})
                st.success("Foto atualizada!")
            
            st.write("### 💰 Adicionar Moedas")
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={PIX_OFICIAL}")
            st.code(f"Chave PIX: {PIX_OFICIAL}")
            st.markdown(f'<a href="https://wa.me/{ZAP_ADMIN}?text=Fiz o PIX de recarga para: {zap_login}" class="btn-wpp-link">ENVIAR COMPROVANTE</a>', unsafe_allow_html=True)
        else: st.error("WhatsApp ou Senha incorretos.")

# --- ABA 3: CADASTRO ---
with UI_ABAS[2]:
    st.subheader("📝 Junte-se a nós")
    with st.form("form_reg", clear_on_submit=True):
        f_nome = st.text_input("Nome Completo / Empresa")
        f_zap = st.text_input("WhatsApp (Ex: 11988887777)")
        f_pass = st.text_input("Crie sua Senha", type="password")
        f_cidade = st.text_input("Cidade e Bairro")
        f_uf = st.selectbox("Estado", LISTA_ESTADOS)
        f_desc = st.text_area("Descrição do seu serviço:")
        
        if st.form_submit_button("CRIAR MEU PERFIL"):
            if len(f_zap) >= 11 and f_nome:
                cat_ia = processar_servico_ia(f_desc)
                db.collection("profissionais").document(f_zap).set({
                    "nome": f_nome, "whatsapp": f_zap, "senha": f_pass, "area": cat_ia,
                    "localizacao": f_cidade, "cidade": f_cidade, "uf": f_uf, "saldo": BONUS_WELCOME,
                    "rating": 5.0, "cliques": 0, "aprovado": False, "foto_url": "",
                    "lat": LAT_SP_REF + random.uniform(-0.1, 0.1), "lon": LON_SP_REF + random.uniform(-0.1, 0.1),
                    "timestamp": datetime.datetime.now()
                })
                st.balloons()
                st.success(f"Excelente! Pré-classificado como: {cat_ia}.")
                st.markdown(f'<a href="https://wa.me/{ZAP_ADMIN}?text=Fiz o cadastro: {f_nome}" class="btn-wpp-link">AVISAR ADMIN PARA APROVAR</a>', unsafe_allow_html=True)

# --- ABA 4: ADMIN MASTER (FUNÇÕES TOTAIS) ---
with UI_ABAS[3]:
    adm_access = st.text_input("Senha Admin:", type="password", key="adm_in")
    if adm_access == CHAVE_ACESSO_ADMIN:
        st.subheader("🛡️ Painel de Controle Master")
        if st.button("🚀 EXECUTAR SECURITY AUDIT (VARREDURA)", use_container_width=True):
            st.success(executar_limpeza_banco(db))
        
        st.divider()
        busca_adm = st.text_input("🔍 Buscar por Nome ou Zap:", key="s_adm").lower()
        docs = db.collection("profissionais").stream()
        lista_adm = [d.to_dict() | {"id": d.id} for d in docs]
        
        for p in lista_adm:
            if not busca_adm or busca_adm in p['nome'].lower() or busca_adm in p['id']:
                with st.expander(f"{'✅' if p['aprovado'] else '⏳'} {p['nome']} ({p.get('saldo')} 🪙)"):
                    c1, c2 = st.columns(2)
                    if c1.button("APROVAR ✅", key=f"ok_{p['id']}"):
                        db.collection("profissionais").document(p['id']).update({"aprovado": True})
                        st.rerun()
                    if c2.button("EXCLUIR 🗑️", key=f"del_{p['id']}"):
                        db.collection("profissionais").document(p['id']).delete()
                        st.rerun()
                    
                    st.write("---")
                    v_moedas = st.number_input("Adicionar Moedas", 1, 100, 10, key=f"num_{p['id']}")
                    if st.button(f"DAR +{v_moedas} MOEDAS", key=f"add_{p['id']}"):
                        db.collection("profissionais").document(p['id']).update({"saldo": firestore.Increment(v_moedas)})
                        st.rerun()
                    
                    if st.button("PUNIR -5 ❌", key=f"pun_{p['id']}"):
                        db.collection("profissionais").document(p['id']).update({"saldo": firestore.Increment(-5)})
                        st.rerun()

# 9. RODAPÉ
st.markdown("<br><hr><center><p style='color:#888; font-size:12px;'>GeralJá Brasil v25.0 - Build 2025</p></center>", unsafe_allow_html=True)


