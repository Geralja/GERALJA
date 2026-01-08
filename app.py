import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime
import math
import re
import time
import pandas as pd
import unicodedata
import pytz
from streamlit_js_eval import streamlit_js_eval, get_geolocation
from urllib.parse import quote

# CONFIGURAÇÃO ÚNICA DA PÁGINA (Executada apenas uma vez)
st.set_page_config(
    page_title="GeralJá | Brasil Elite",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def converter_img_b64(file):
    if file is not None:
        return base64.b64encode(file.getvalue()).decode()
    return None
    @st.cache_resourcedef conectar_banco_master():
    if not firebase_admin._apps:
        try:
            if "FIREBASE_BASE64" not in st.secrets:
                st.error("🔑 Chave de segurança FIREBASE_BASE64 não encontrada.")
                st.stop()
            b64_key = st.secrets["FIREBASE_BASE64"]
            decoded_json = base64.b64decode(b64_key).decode("utf-8")
            cred_dict = json.loads(decoded_json)
            cred = credentials.Certificate(cred_dict)
            return firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"❌ FALHA NA INFRAESTRUTURA: {e}")
            st.stop()
    return firebase_admin.get_app()

app_engine = conectar_banco_master()
db = firestore.client()

# POLÍTICAS E CONSTANTES
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ADMIN = "mumias"
TAXA_CONTATO = 1
BONUS_WELCOME = 5
LAT_REF, LON_REF = -23.5505, -46.6333
CATEGORIAS_OFICIAIS = sorted([
    "Academia", "Ajudante Geral", "Assistência Técnica", "Barbearia/Salão", 
    "Chaveiro", "Diarista / Faxineira", "Eletricista", "Encanador", 
    "Estética Automotiva", "Freteiro", "Mecânico de Autos", "Montador de Móveis",
    "Padaria", "Pet Shop", "Pintor", "Pizzaria", "TI (Tecnologia)", "Web Designer"
])

CONCEITOS_EXPANDIDOS = {
    "pizza": "Pizzaria", "fome": "Pizzaria", "vazamento": "Encanador", 
    "curto": "Eletricista", "carro": "Mecânico de Autos", "pneu": "Borracheiro",
    "frete": "Freteiro", "mudanca": "Freteiro", "faxina": "Diarista / Faxineira",
    "iphone": "Assistência Técnica", "geladeira": "Refrigeração"
}
def normalizar_para_ia(texto):
    if not texto: return ""
    return "".join(c for c in unicodedata.normalize('NFD', str(texto)) 
                  if unicodedata.category(c) != 'Mn').lower().strip()

def processar_ia_avancada(texto):
    if not texto: return "Vazio"
    t_clean = normalizar_para_ia(texto)
    for chave, categoria in CONCEITOS_EXPANDIDOS.items():
        if re.search(rf"\b{normalizar_para_ia(chave)}\b", t_clean): return categoria
    for cat in CATEGORIAS_OFICIAIS:
        if normalizar_para_ia(cat) in t_clean: return cat
    return "NAO_ENCONTRADO"

def calcular_distancia_real(lat1, lon1, lat2, lon2):
    try:
        R = 6371 
        dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)
    except: return 999.0
        def guardia_escanear_e_corrigir():
    status_log = []
    try:
        profs = db.collection("profissionais").stream()
        for p_doc in profs:
            dados = p_doc.to_dict()
            id_pro, correcoes = p_doc.id, {}
            if not dados.get('area') or dados.get('area') not in CATEGORIAS_OFICIAIS:
                correcoes['area'] = "Ajudante Geral"
            if dados.get('saldo') is None: correcoes['saldo'] = 0
            if correcoes:
                db.collection("profissionais").document(id_pro).update(correcoes)
                status_log.append(f"✅ Corrigido: {id_pro}")
        return status_log if status_log else ["SISTEMA ÍNTEGRO"]
    except Exception as e: return [f"❌ Erro: {e}"]
        st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: white !important; }
    .header-container { background: white; padding: 30px; border-bottom: 8px solid #FF8C00; text-align: center; }
    .logo-azul { color: #0047AB; font-weight: 900; font-size: 45px; }
    .logo-laranja { color: #FF8C00; font-weight: 900; font-size: 45px; }
    #MainMenu, footer, header { visibility: hidden; display: none !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-container"><span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span><br><small>BRASIL ELITE</small></div>', unsafe_allow_html=True)

abas_lista = ["🔍 BUSCAR", "🚀 CADASTRAR", "👤 MEU PERFIL", "👑 ADMIN", "⭐ FEEDBACK"]
menu_abas = st.tabs(abas_lista)
with menu_abas[0]:
    loc = get_geolocation()
    u_lat = loc['coords']['latitude'] if loc else LAT_REF
    u_lon = loc['coords']['longitude'] if loc else LON_REF
    
    c1, c2 = st.columns([3, 1])
    busca = c1.text_input("O que você precisa hoje?", key="search_bar")
    raio = c2.select_slider("Raio (KM)", options=[1, 5, 10, 50, 100], value=10)

    if busca:
        cat_alvo = processar_ia_avancada(busca)
        profs = db.collection("profissionais").where("area", "==", cat_alvo).where("aprovado", "==", True).stream()
        
        ranking = []
        for d in profs:
            p = d.to_dict()
            p['id'] = d.id
            p['dist'] = calcular_distancia_real(u_lat, u_lon, p.get('lat', LAT_REF), p.get('lon', LON_REF))
            if p['dist'] <= raio:
                p['score'] = (p.get('saldo', 0) * 10) + (500 if p.get('verificado') else 0)
                ranking.append(p)
        
        ranking.sort(key=lambda x: (-x['score'], x['dist']))
        for p in ranking:
            st.markdown(f"### {p['nome'].upper()} (📍 {p['dist']}km)")
            st.link_button(f"Falar com {p['nome']}", f"https://wa.me/{p['id']}")
            with menu_abas[1]:
    st.subheader("🚀 Cadastro de Profissional")
    with st.form("cad_form"):
        n = st.text_input("Nome Completo")
        w = st.text_input("WhatsApp (ex: 11999999999)")
        a = st.selectbox("Área de Atuação", CATEGORIAS_OFICIAIS)
        s = st.text_input("Crie uma Senha", type="password")
        if st.form_submit_button("CADASTRAR AGORA"):
            db.collection("profissionais").document(w).set({
                "nome": n, "area": a, "senha": s, "saldo": BONUS_WELCOME,
                "aprovado": False, "verificado": False, "lat": u_lat, "lon": u_lon
            })
            st.success("Cadastro enviado! Aguarde aprovação.")

with menu_abas[2]:
    st.info("Acesse seu painel para gerenciar seu saldo e localização.")
# --- ABA 4: ADMIN (👑 CENTRAL DE COMANDO) ---
with menu_abas[3]:
    st.markdown("### 🔒 Terminal de Administração")
    access_adm = st.text_input("Senha Master", type="password", key="adm_auth_final")
    
    if access_adm != CHAVE_ADMIN:
        if access_adm != "":
            st.error("🚫 Acesso negado. Senha incorreta.")
        else:
            st.info("Aguardando chave master para liberar sistemas...")
        # Não usamos st.stop() aqui para não travar as outras abas do usuário
    else:
        st.success("👑 Acesso Autorizado! Bem-vindo ao Painel Supremo.")
        
        # 1. TELEMETRIA EM TEMPO REAL
        all_profs_lista = list(db.collection("profissionais").stream())
        total_cadastros = len(all_profs_lista)
        pendentes_lista = [p for p in all_profs_lista if not p.to_dict().get('aprovado', False)]
        total_moedas = sum([p.to_dict().get('saldo', 0) for p in all_profs_lista])
        total_cliques = sum([p.to_dict().get('cliques', 0) for p in all_profs_lista])

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 Moedas", f"{total_moedas} 🪙")
        c2.metric("📈 Parceiros", total_cadastros)
        c3.metric("🤝 Cliques", total_cliques)
        c4.metric("🟡 Pendentes", len(pendentes_lista))
        
        st.divider()

        # 2. SUB-SISTEMAS DO ADMIN
        t_gestao, t_aprova, t_seguranca, t_feed_adm = st.tabs([
            "👥 GESTÃO", "🆕 APROVAÇÃO", "🛡️ SEGURANÇA IA", "📩 MENSAGENS"
        ])

        with t_gestao:
            search_pro = st.text_input("🔍 Buscar por Nome ou Zap", key="search_adm")
            for p_doc in all_profs_lista:
                p, pid = p_doc.to_dict(), p_doc.id
                if not search_pro or search_pro.lower() in p.get('nome', '').lower() or search_pro in pid:
                    with st.expander(f"{'🟢' if p.get('aprovado') else '🟡'} {p.get('nome', 'S/N').upper()}"):
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.write(f"**Zap:** {pid} | **Saldo:** {p.get('saldo', 0)}")
                            is_verif = p.get('verificado', False)
                            if st.checkbox("Selo Verificado", value=is_verif, key=f"chk_{pid}"):
                                if not is_verif: db.collection("profissionais").document(pid).update({"verificado": True}); st.rerun()
                        with col_b:
                            bonus = st.number_input("Crédito", 0, 1000, key=f"in_{pid}")
                            if st.button("💰 CREDITAR", key=f"btn_{pid}"):
                                db.collection("profissionais").document(pid).update({"saldo": p.get('saldo', 0) + bonus})
                                st.rerun()

        with t_aprova:
            if not pendentes_lista: st.info("Nenhum pendente.")
            for p_doc in pendentes_lista:
                p, pid = p_doc.to_dict(), p_doc.id
                if st.button(f"✅ APROVAR {p.get('nome')}", key=f"aprove_{pid}"):
                    db.collection("profissionais").document(pid).update({"aprovado": True, "saldo": 10})
                    st.rerun()

        with t_seguranca:
            st.write("#### 🛡️ Auto-Cura do Sistema")
            if st.button("🔍 ESCANEAR E REPARAR AGORA", use_container_width=True):
                guardia_escanear_e_corrigir()
                scan_virus_e_scripts()
                st.success("Sistema higienizado!")

        with t_feed_adm:
            f_list = db.collection("feedbacks").order_by("data", direction="DESCENDING").limit(10).stream()
            for f in f_list:
                df = f.to_dict()
                st.markdown(f"**{df.get('nota')}** - <small>{str(df.get('data'))[:16]}</small><br>{df.get('mensagem')}", unsafe_allow_html=True)
                st.divider()

# --- ABA 5: FEEDBACK (A VOZ DO CLIENTE) ---
with menu_abas[4]:
    st.markdown("### ⭐ Sua opinião é fundamental")
    with st.form("feedback_publico", clear_on_submit=True):
        f_nota = st.select_slider("Satisfação:", options=["Péssimo", "Regular", "Bom", "Excelente"], value="Excelente")
        f_msg = st.text_area("O que podemos melhorar?")
        if st.form_submit_button("ENVIAR FEEDBACK"):
            if f_msg.strip():
                db.collection("feedbacks").add({
                    "data": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "nota": f_nota, "mensagem": f_msg
                })
                st.success("Obrigado! Sua voz foi ouvida.")
                st.balloons()

# --- ABA 6: FINANCEIRO (DINÂMICO) ---
if "📊 FINANCEIRO" in abas_lista:
    with menu_abas[5]: # Só acessível se o comando 'abracadabra' foi usado
        st.markdown("### 📊 Cofre GeralJá")
        if st.text_input("Chave do Cofre", type="password") == "riqueza2026":
            total_cash = sum([p.to_dict().get('total_comprado', 0) for p in all_profs_lista])
            st.metric("💰 FATURAMENTO BRUTO", f"R$ {total_cash:,.2f}")
            st.dataframe(pd.DataFrame([{"Nome": p.to_dict().get('nome'), "Pago": p.to_dict().get('total_comprado', 0)} for p in all_profs_lista]))

# --- RODAPÉ ---
st.markdown(f'<div style="text-align:center; padding:50px; color:#94A3B8; font-size:12px;">GERALJÁ v20.0 © {datetime.datetime.now().year}</div>', unsafe_allow_html=True)

