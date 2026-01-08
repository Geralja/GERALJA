# ==============================================================================
# BLOCO 1: INFRAESTRUTURA E IMPORTAÇÕES
# ==============================================================================
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
from streamlit_js_eval import streamlit_js_eval, get_geolocation
from urllib.parse import quote

# ------------------------------------------------------------------------------
# BLOCO 2: CONFIGURAÇÃO DE PÁGINA E TEMA
# ------------------------------------------------------------------------------
st.set_page_config(page_title="GeralJá | Brasil Elite", page_icon="🇧🇷", layout="wide", initial_sidebar_state="collapsed")

if 'tema_claro' not in st.session_state:
    st.session_state.tema_claro = True

# ------------------------------------------------------------------------------
# BLOCO 3: CONEXÃO COM BANCO DE DADOS (FIREBASE)
# ------------------------------------------------------------------------------
@st.cache_resource
def conectar_banco_master():
    if not firebase_admin._apps:
        try:
            b64_key = st.secrets["FIREBASE_BASE64"]
            decoded_json = base64.b64decode(b64_key).decode("utf-8")
            cred_dict = json.loads(decoded_json)
            cred = credentials.Certificate(cred_dict)
            return firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Erro ao conectar Firebase: {e}")
            st.stop()
    return firebase_admin.get_app()

app_engine = conectar_banco_master()
db = firestore.client()

# ------------------------------------------------------------------------------
# BLOCO 4: SUPER LISTA DE PROFISSÕES E COMÉRCIOS (EXPANDIDA)
# ------------------------------------------------------------------------------
CATEGORIAS_OFICIAIS = sorted([
    # --- SERVIÇOS DOMÉSTICOS ---
    "Acompanhante de Idosos", "Babá (Nanny)", "Diarista / Faxineira", "Cozinheiro(a) Particular",
    "Jardineiro", "Lavagem de Sofás / Estofados", "Piscineiro", "Passadeira", "Pet Shop / Banho e Tosa",
    
    # --- CONSTRUÇÃO E REFORMAS ---
    "Ajudante Geral", "Azulejista", "Chaveiro", "Eletricista", "Encanador", "Gesseiro", "Marceneiro",
    "Marido de Aluguel", "Montador de Móveis", "Pedreiro", "Pintor", "Serralheiro", "Telhadista", "Vidraceiro",
    
    # --- AUTOMOTIVO ---
    "Auto Elétrica", "Borracheiro", "Estética Automotiva / Polimento", "Funilaria e Pintura", 
    "Guincho 24h", "Mecânico de Autos", "Mecânico de Motos", "Lava Jato", "Som e Alarme",
    
    # --- SAÚDE E BEM-ESTAR ---
    "Academia / Personal Trainer", "Barbearia", "Cabeleireiro(a)", "Dentista", "Esteticista", 
    "Fisioterapeuta", "Manicure e Pedicure", "Maquiador(a)", "Nutricionista", "Psicólogo(a)", "Tatuador(a)",
    
    # --- COMÉRCIOS E LOJAS ---
    "Açougue", "Adega / Depósito de Bebidas", "Armarinho / Aviamentos", "Bazar", "Cafeteria", 
    "Doceria / Confeitaria", "Farmácia", "Floricultura", "Hamburgueria", "Hortifruti / Sacolão",
    "Loja de Celulares", "Loja de Roupas", "Loja de Variedades", "Material de Construção", 
    "Padaria", "Papelaria", "Pastelaria", "Pet Shop", "Pizzaria", "Relojoaria / Joalheria", "Sorveteria",
    
    # --- TECNOLOGIA E ESCRITÓRIO ---
    "Advocacia", "Assistência Técnica (Celular/PC)", "Contabilidade", "Marketing Digital",
    "TI (Suporte de Informática)", "Web Designer", "Fotógrafo(a) / Filmagem",
    
    # --- LOGÍSTICA E TRANSPORTE ---
    "Carreto / Mudanças", "Freteiro", "Motoboy / Entregas", "Motorista Particular"
])

# ------------------------------------------------------------------------------
# BLOCO 5: MOTOR DE IA (BUSCA INTELIGENTE)
# ------------------------------------------------------------------------------
CONCEITOS_EXPANDIDOS = {
    "fome": "Pizzaria", "vazamento": "Encanador", "curto": "Eletricista", "carro": "Mecânico de Autos",
    "pneu": "Borracheiro", "mudanca": "Freteiro", "faxina": "Diarista / Faxineira", "unha": "Manicure e Pedicure",
    "barba": "Barbearia", "internet": "TI (Suporte de Informática)", "iphone": "Assistência Técnica (Celular/PC)",
    "pao": "Padaria", "geladeira": "Marido de Aluguel", "festa": "Doceria / Confeitaria"
}

def normalizar_para_ia(texto):
    if not texto: return ""
    return "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn').lower().strip()

def processar_ia_avancada(texto):
    t_clean = normalizar_para_ia(texto)
    for chave, cat in CONCEITOS_EXPANDIDOS.items():
        if chave in t_clean: return cat
    for cat in CATEGORIAS_OFICIAIS:
        if normalizar_para_ia(cat) in t_clean: return cat
    return "NAO_ENCONTRADO"

# ------------------------------------------------------------------------------
# BLOCO 6: CÁLCULO DE DISTÂNCIA REAL
# ------------------------------------------------------------------------------
def calcular_distancia(lat1, lon1, lat2, lon2):
    try:
        R = 6371
        dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
        return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)
    except: return 99.0

# ------------------------------------------------------------------------------
# BLOCO 7: INTERFACE - BUSCA E MONETIZAÇÃO
# ------------------------------------------------------------------------------
st.markdown('<h1 style="text-align:center; color:#FF8C00;">GERALJÁ BRASIL</h1>', unsafe_allow_html=True)
abas = st.tabs(["🔍 BUSCAR", "🚀 CADASTRAR", "👤 MEU PERFIL", "👑 ADMIN"])

with abas[0]:
    loc = get_geolocation()
    u_lat, u_lon = (loc['coords']['latitude'], loc['coords']['longitude']) if loc else (-23.5, -46.6)
    
    busca = st.text_input("O que você precisa hoje?", placeholder="Ex: Preciso de alguém para consertar um cano")
    if busca:
        cat_alvo = processar_ia_avancada(busca)
        profs = list(db.collection("profissionais").where("area", "==", cat_alvo).where("aprovado", "==", True).stream())
        
        if not profs:
            st.warning(f"Ainda não temos '{cat_alvo}' cadastrados.")
            st.info("💡 **GANHE DINHEIRO:** Indique um profissional desta área! Se ele se cadastrar pelo seu link, você ganha 10 moedas.")
            st.button("📲 Compartilhar link de convite")
        else:
            # Lógica de Ranking e Monetização (Exatamente como você tinha)
            for p_doc in profs:
                p = p_doc.to_dict()
                dist = calcular_distancia(u_lat, u_lon, p.get('lat', -23.5), p.get('lon', -46.6))
                with st.expander(f"📍 {dist}km - {p['nome'].upper()}"):
                    st.write(f"Especialista em: {p['area']}")
                    if st.button(f"📞 Ver WhatsApp (1 Moeda)", key=p_doc.id):
                        # Desconta saldo do profissional para ele aparecer para o cliente
                        if p.get('saldo', 0) > 0:
                            db.collection("profissionais").document(p_doc.id).update({"saldo": p['saldo'] - 1})
                            st.success(f"Fale com ele agora: {p_doc.id}")
                            st.link_button("Abrir Conversa", f"https://wa.me/{p_doc.id}")

# ------------------------------------------------------------------------------
# BLOCO 8: INTERFACE - CADASTRO (COM TODAS AS PROFISSÕES)
# ------------------------------------------------------------------------------
with abas[1]:
    st.subheader("🚀 Cadastro de Profissional ou Logista")
    with st.form("cad_completo"):
        c_nome = st.text_input("Nome Completo ou Nome da Loja")
        c_zap = st.text_input("WhatsApp (Ex: 11999999999)")
        c_area = st.selectbox("Em qual segmento você atua?", CATEGORIAS_OFICIAIS)
        c_senha = st.text_input("Crie uma Senha", type="password")
        if st.form_submit_button("CADASTRAR"):
            db.collection("profissionais").document(c_zap).set({
                "nome": c_nome, "area": c_area, "senha": c_senha, "saldo": 5,
                "aprovado": False, "verificado": False, "lat": u_lat, "lon": u_lon
            })
            st.success("✅ Cadastro enviado para análise! Em breve você aparecerá nas buscas.")

# ------------------------------------------------------------------------------
# BLOCO 9: INTERFACE - MEU PERFIL (GESTÃO DO USUÁRIO)
# ------------------------------------------------------------------------------
with abas[2]:
    st.subheader("👤 Painel do Parceiro")
    l_zap = st.text_input("WhatsApp", key="login_z")
    l_pw = st.text_input("Senha", type="password", key="login_p")
    if st.button("ACESSAR"):
        u = db.collection("profissionais").document(l_zap).get()
        if u.exists and u.to_dict().get('senha') == l_pw:
            d = u.to_dict()
            st.success(f"Bem-vindo, {d['nome']}!")
            st.metric("Meu Saldo", f"{d.get('saldo', 0)} Moedas")
            
            # EDIÇÃO DE PERFIL
            with st.expander("📝 Editar Meus Dados"):
                novo_n = st.text_input("Mudar Nome", d['nome'])
                nova_b = st.text_area("Mudar Bio", d.get('bio', ''))
                if st.button("Salvar Alterações"):
                    db.collection("profissionais").document(l_zap).update({"nome": novo_n, "bio": nova_b})
                    st.rerun()
        else:
            st.error("Senha ou WhatsApp inválidos.")

# ------------------------------------------------------------------------------
# BLOCO 10: ADMIN (PODER TOTAL)
# ------------------------------------------------------------------------------
with abas[3]:
    if st.text_input("Chave Master", type="password") == "mumias":
        st.write("### 🔒 Central de Comando")
        profs_all = list(db.collection("profissionais").stream())
        for doc in profs_all:
            d = doc.to_dict()
            with st.expander(f"{'🟢' if d.get('aprovado') else '🟡'} {d['nome']} - {d['area']}"):
                col1, col2 = st.columns(2)
                if col1.button("✅ APROVAR", key=f"ap_{doc.id}"):
                    db.collection("profissionais").document(doc.id).update({"aprovado": True})
                    st.rerun()
                if col2.button("🗑️ EXCLUIR", key=f"ex_{doc.id}"):
                    db.collection("profissionais").document(doc.id).delete()
                    st.rerun()
                new_s = st.number_input("Ajustar Saldo", value=d.get('saldo', 0), key=f"s_{doc.id}")
                if st.button("Atualizar Saldo", key=f"btn_s_{doc.id}"):
                    db.collection("profissionais").document(doc.id).update({"saldo": new_s})
                    st.rerun()

# ------------------------------------------------------------------------------
# RODAPÉ
# ------------------------------------------------------------------------------
st.markdown(f'<div style="text-align:center; padding:20px; color:gray;">GERALJÁ v20.0 © {datetime.datetime.now().year}</div>', unsafe_allow_html=True)
