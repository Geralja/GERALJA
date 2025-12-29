# ==============================================================================
# GERALJÁ - AQUI VOCÊ ENCONTRA TUDO v20.0 (ESTÁVEL E INTEGRADA)
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

# ==============================================================================
# 1. ARQUITETURA DE SISTEMA E METADADOS (ENGINEERING HEADER)
# ==============================================================================
st.set_page_config(
    page_title="GeralJá | Ecossistema Profissional do Brasil",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://wa.me/5511991853488',
        'Report a bug': 'https://wa.me/5511991853488',
        'About': "GeralJá v20.0 - Ecossistema Nacional de Serviços."
    }
)

# ==============================================================================
# 2. CAMADA DE PERSISTÊNCIA: CONEXÃO FIREBASE (BLINDAGEM DE DADOS)
# ==============================================================================
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
            st.error(f"❌ FALHA DE INFRAESTRUTURA: {erro_fatal}")
            st.stop()
    return firebase_admin.get_app()

app_engine = inicializar_infraestrutura_dados()
db = firestore.client()

# ==============================================================================
# 3. DICIONÁRIO DE CONSTANTES E REGRAS FINANCEIRAS
# ==============================================================================
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ACESSO_ADMIN = "mumias"
TAXA_CONTATO = 1
BONUS_WELCOME = 5
URL_APLICATIVO = "https://geralja.streamlit.app"
DISTINTIVO_SISTEMA = "BUILD 2025.20 - BRASIL GOLD"

# Marco Zero (São Paulo) para fallback de distância
LAT_SP_REF = -23.5505
LON_SP_REF = -46.6333

LISTA_ESTADOS = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]

# ==============================================================================
# 4. MOTOR DE INTELIGÊNCIA ARTIFICIAL (MAPEAMENTO MASSIVO NLP)
# ==============================================================================
CONCEITOS_SERVICOS = {
    "vazamento": "Encanador", "cano": "Encanador", "torneira": "Encanador", 
    "esgoto": "Encanador", "pia": "Encanador", "privada": "Encanador", 
    "curto": "Eletricista", "luz": "Eletricista", "tomada": "Eletricista", 
    "chuveiro": "Eletricista", "fiação": "Eletricista", "disjuntor": "Eletricista", 
    "pintar": "Pintor", "parede": "Pintor", "massa": "Pintor", "reforma": "Pedreiro", 
    "piso": "Pedreiro", "azulejo": "Pedreiro", "gesso": "Gesseiro", "drywall": "Gesseiro",
    "telhado": "Telhadista", "calha": "Telhadista", "goteira": "Telhadista", 
    "montar": "Montador de Móveis", "armário": "Montador de Móveis", 
    "unha": "Manicure", "pé": "Manicure", "cabelo": "Cabeleireiro", "barba": "Barbeiro",
    "faxina": "Diarista", "limpeza": "Diarista", "passar": "Diarista", 
    "jardim": "Jardineiro", "piscina": "Piscineiro", "pneu": "Borracheiro",
    "carro": "Mecânico", "motor": "Mecânico", "guincho": "Guincho 24h",
    "computador": "TI", "celular": "TI", "ar condicionado": "Refrigeração"
}

# ==============================================================================
# 5. FUNÇÕES CORE (LÓGICA E MATEMÁTICA)
# ==============================================================================
def processar_servico_ia(texto_cliente):
    if not texto_cliente: return "Ajudante Geral"
    t_clean = texto_cliente.lower().strip()
    for key, prof in CONCEITOS_SERVICOS.items():
        if re.search(rf"\b{key}\b", t_clean): return prof
    return "Ajudante Geral"

def calcular_km_real(lat1, lon1, lat2, lon2):
    try:
        if None in [lat1, lon1, lat2, lon2]: return 999.0
        R = 6371 
        d_lat, d_lon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(d_lat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon/2)**2
        return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)
    except: return 999.0

def executar_limpeza_banco(db_instancia):
    profs_ref = db_instancia.collection("profissionais").stream()
    correcoes = 0
    for doc in profs_ref:
        d, upd = doc.to_dict(), {}
        if "rating" not in d: upd["rating"] = 5.0
        if "saldo" not in d: upd["saldo"] = BONUS_WELCOME
        if "cliques" not in d: upd["cliques"] = 0
        if "aprovado" not in d: upd["aprovado"] = False
        if upd:
            db_instancia.collection("profissionais").document(doc.id).update(upd)
            correcoes += 1
    return f"✅ Integridade Garantida: {correcoes} perfis ajustados."

# ==============================================================================
# 6. ESTILIZAÇÃO CSS (LAYOUT BRASIL PREMIUM)
# ==============================================================================
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap');
    * {{ font-family: 'Montserrat', sans-serif; }}
    .stApp {{ background-color: #FAFAFA; }}
    .header-box {{ text-align: center; padding: 30px 0; background: white; border-radius: 0 0 40px 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); border-bottom: 8px solid #FF8C00; }}
    .txt-azul {{ color: #0047AB !important; font-size: 60px; font-weight: 900; letter-spacing: -3px; }}
    .txt-laranja {{ color: #FF8C00 !important; font-size: 60px; font-weight: 900; letter-spacing: -3px; }}
    .card-vazado {{ background: white; border-radius: 25px; padding: 25px; margin-bottom: 20px; border-left: 15px solid #0047AB; box-shadow: 0 8px 25px rgba(0,0,0,0.05); display: flex; align-items: center; }}
    .avatar-pro {{ width: 100px; height: 100px; border-radius: 50%; object-fit: cover; margin-right: 25px; border: 4px solid #F1F5F9; }}
    .badge-km {{ background: #EBF4FF; color: #0047AB; padding: 6px 14px; border-radius: 10px; font-size: 11px; font-weight: 900; }}
    .btn-zap {{ background: #22C55E; color: white !important; padding: 15px; border-radius: 15px; text-decoration: none; display: block; text-align: center; font-weight: 900; margin-top: 10px; }}
    .metric-box {{ background: #1E293B; color: white; padding: 20px; border-radius: 20px; text-align: center; }}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-box"><span class="txt-azul">GERAL</span><span class="txt-laranja">JÁ</span><br><p style="color:#555; font-size:14px; font-weight:700; text-transform:uppercase; letter-spacing:8px; margin-top:10px;">Brasil Profissional</p></div>', unsafe_allow_html=True)

# ==============================================================================
# 7. SISTEMA DE NAVEGAÇÃO
# ==============================================================================
UI_ABAS = st.tabs(["🔍 BUSCAR SERVIÇO", "💼 MINHA CONTA", "📝 CADASTRAR", "🛡️ ADMIN"])

# --- ABA 1: BUSCA NACIONAL ---
with UI_ABAS[0]:
    st.write("### 🏙️ O que você procura hoje?")
    col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
    busca_cidade = col_c1.text_input("Cidade", placeholder="Ex: São Paulo")
    termo_busca = col_c2.text_input("Qual serviço?", placeholder="Ex: Chuveiro, Pintor...")
    raio_km = col_c3.select_slider("Raio (KM)", options=[1, 5, 10, 50, 100, "Brasil"], value=50)

    if termo_busca:
        classe_servico = processar_servico_ia(termo_busca)
        st.info(f"✨ IA: Buscando profissionais de **{classe_servico}**.")
        
        query = db.collection("profissionais").where("area", "==", classe_servico).where("aprovado", "==", True).stream()
        lista_final = []
        
        for doc in query:
            p = doc.to_dict()
            p['id'] = doc.id
            dist = calcular_km_real(LAT_SP_REF, LON_SP_REF, p.get('lat', LAT_SP_REF), p.get('lon', LON_SP_REF))
            p['distancia'] = dist
            
            # Lógica de Filtro Nacional Somada
            if raio_km == "Brasil":
                lista_final.append(p)
            elif busca_cidade and busca_cidade.lower() in p.get('cidade', '').lower():
                lista_final.append(p)
            elif isinstance(raio_km, int) and dist <= raio_km:
                lista_final.append(p)

        lista_final.sort(key=lambda x: x.get('distancia', 0))

        if not lista_final:
            st.warning("Nenhum profissional encontrado com estes critérios.")
        else:
            for pro in lista_final:
                loc_txt = f"{pro.get('cidade', 'SP')} | {pro['distancia']} KM"
                st.markdown(f'''
                    <div class="card-vazado">
                        <img src="{pro.get('foto_url') or 'https://api.dicebear.com/7.x/avataaars/svg?seed='+pro['id']}" class="avatar-pro">
                        <div style="flex-grow: 1;">
                            <span class="badge-km">📍 {loc_txt}</span>
                            <h3 style="margin:5px 0;">{pro['nome'].upper()}</h3>
                            <p style="color:#666; font-size:14px;">⭐ {pro.get('rating', 5.0)} | <b>{pro['area']}</b></p>
                            <p style="font-size:13px;">{pro.get('descricao', '')}</p>
                        </div>
                    </div>
                ''', unsafe_allow_html=True)
                
                if pro.get('saldo', 0) >= TAXA_CONTATO:
                    if st.button(f"CONTATAR {pro['nome'].split()[0].upper()}", key=f"btn_{pro['id']}"):
                        db.collection("profissionais").document(pro['id']).update({
                            "saldo": firestore.Increment(-TAXA_CONTATO),
                            "cliques": firestore.Increment(1)
                        })
                        st.balloons()
                        st.markdown(f'<a href="https://wa.me/55{pro["whatsapp"]}?text=Olá, vi seu perfil no GeralJá!" class="btn-zap">ABRIR WHATSAPP</a>', unsafe_allow_html=True)
                else:
                    st.error("Limite de contatos atingido por este profissional.")

# --- ABA 2: MINHA CONTA (DASHBOARD) ---
with UI_ABAS[1]:
    if 'auth' not in st.session_state: st.session_state.auth = False
    
    if not st.session_state.auth:
        c1, c2 = st.columns(2)
        l_zap = c1.text_input("WhatsApp", key="login_z")
        l_pw = c2.text_input("Senha", type="password", key="login_p")
        if st.button("ACESSAR PAINEL"):
            doc = db.collection("profissionais").document(l_zap).get()
            if doc.exists and doc.to_dict().get('senha') == l_pw:
                st.session_state.auth, st.session_state.user_id = True, l_zap
                st.rerun()
            else: st.error("Acesso negado.")
    else:
        dados = db.collection("profissionais").document(st.session_state.user_id).get().to_dict()
        st.success(f"Bem-vindo, {dados['nome']}!")
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.markdown(f'<div class="metric-box">MOEDAS<br><b>{dados.get("saldo")}</b></div>', unsafe_allow_html=True)
        col_m2.markdown(f'<div class="metric-box">CLIQUES<br><b>{dados.get("cliques")}</b></div>', unsafe_allow_html=True)
        col_m3.markdown(f'<div class="metric-box">AVALIAÇÃO<br><b>{dados.get("rating")} ⭐</b></div>', unsafe_allow_html=True)
        
        with st.expander("🛠️ EDITAR MEU PERFIL"):
            nova_foto = st.text_input("URL da Foto", value=dados.get('foto_url', ''))
            nova_desc = st.text_area("Descrição", value=dados.get('descricao', ''))
            if st.button("SALVAR ALTERAÇÕES"):
                db.collection("profissionais").document(st.session_state.user_id).update({"foto_url": nova_foto, "descricao": nova_desc})
                st.rerun()

        st.divider()
        st.write("### 💰 Recarga PIX")
        st.code(f"Chave PIX: {PIX_OFICIAL}")
        st.markdown(f'<a href="https://wa.me/{ZAP_ADMIN}?text=Fiz o PIX de recarga para: {st.session_state.user_id}" class="btn-zap">ENVIAR COMPROVANTE AGORA</a>', unsafe_allow_html=True)
        
        if st.button("SAIR DA CONTA"):
            st.session_state.auth = False
            st.rerun()

# --- ABA 3: CADASTRO (EXPANDIDO BRASIL) ---
with menu_abas[2]:
    st.markdown("### 🚀 Cadastro Nacional de Profissionais")
    with st.form("cad_f"):
        # ... (campos de nome, zap, senha que você já tem) ...
        
        col_loc1, col_loc2 = st.columns(2)
        r_cidade = col_loc1.text_input("Cidade", placeholder="Ex: Curitiba")
        r_uf = col_loc2.selectbox("Estado", ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"])
        
        # Campo oculto ou IA para converter cidade em Lat/Lon 
        # (Para simplicidade agora, usaremos a cidade como texto)
        
        if st.form_submit_button("CADASTRAR"):
            db.collection("profissionais").document(r_zap).set({
                "nome": r_nome,
                "cidade": r_cidade.strip().title(),
                "uf": r_uf,
                "localizacao_string": f"{r_cidade} - {r_uf}",
                # ... (restante dos dados) ...
            })
# --- ABA 4: ADMIN MASTER ---
with UI_ABAS[3]:
    adm_pass = st.text_input("Senha Master", type="password")
    if adm_pass == CHAVE_ACESSO_ADMIN:
        if st.button("🔍 EXECUTAR AUDITORIA DE SEGURANÇA", use_container_width=True):
            st.success(executar_limpeza_banco(db))
        
        st.divider()
        busca_adm = st.text_input("Buscar Profissional (Nome/Zap)")
        docs = db.collection("profissionais").stream()
        
        for doc in docs:
            d = doc.to_dict()
            pid = doc.id
            if not busca_adm or busca_adm.lower() in d['nome'].lower() or busca_adm in pid:
                with st.expander(f"{'✅' if d['aprovado'] else '⏳'} {d['nome']} | {d['area']} | {d.get('cidade')}"):
                    c1, c2, c3 = st.columns(3)
                    if c1.button("APROVAR", key=f"ap_{pid}"):
                        db.collection("profissionais").document(pid).update({"aprovado": True})
                        st.rerun()
                    
                    qtd = c2.number_input("Moedas", 1, 100, 10, key=f"moe_{pid}")
                    if c2.button("DAR MOEDAS", key=f"add_{pid}"):
                        db.collection("profissionais").document(pid).update({"saldo": firestore.Increment(qtd)})
                        st.rerun()
                    
                    if c3.button("EXCLUIR", key=f"del_{pid}"):
                        db.collection("profissionais").document(pid).delete()
                        st.rerun()

# ==============================================================================
# 9. RODAPÉ TÉCNICO
# ==============================================================================
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown(f'''
    <center>
        <p style="color:#888; font-size:12px;">© 2025 GeralJá Brasil - {DISTINTIVO_SISTEMA}</p>
        <a href="https://wa.me/?text=Precisa de serviços? Use o GeralJá! {URL_APLICATIVO}" style="text-decoration:none; color:#0047AB; font-weight:bold;">📲 COMPARTILHAR</a>
    </center>
''', unsafe_allow_html=True)


