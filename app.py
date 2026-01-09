# ==============================================================================
# GERALJÁ | O ESQUELETO MESTRE (VERSÃO COMPLETA E BLINDADA)
# ==============================================================================
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import datetime
import math
import re
import unicodedata
import pandas as pd
from streamlit_js_eval import get_geolocation

# ------------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DE PÁGINA E ESTILO
# ------------------------------------------------------------------------------
st.set_page_config(page_title="GeralJá | Soluções Rápidas", page_icon="🎯", layout="wide")

if 'tema_claro' not in st.session_state:
    st.session_state.tema_claro = False

def aplicar_estilo():
    hide_style = """
        <style>
            header[data-testid="stHeader"] { visibility: hidden !important; height: 0; }
            footer { visibility: hidden !important; }
            .block-container { padding-top: 2rem !important; }
            .stButton>button { border-radius: 10px; font-weight: bold; width: 100%; }
            .stTabs [data-baseweb="tab-list"] { gap: 10px; }
            .stTabs [data-baseweb="tab"] { 
                background-color: #f0f2f6; border-radius: 5px 5px 0 0; padding: 10px;
            }
        </style>
    """
    st.markdown(hide_style, unsafe_allow_html=True)
    if st.session_state.tema_claro:
        st.markdown("<style>.stApp { background-color: white !important; } * { color: #1E293B !important; }</style>", unsafe_allow_html=True)

aplicar_estilo()

# ------------------------------------------------------------------------------
# 2. FUNÇÕES DE INTELIGÊNCIA E GEOLOCALIZAÇÃO
# ------------------------------------------------------------------------------
def remover_acentos(texto):
    if not texto: return ""
    nfkd_form = unicodedata.normalize('NFKD', str(texto))
    return "".join([c for c in nfkd_form if not unicodedata.category(c) == 'Mn']).lower().strip()

def calcular_distancia(lat1, lon1, lat2, lon2):
    try:
        if None in [lat1, lon1, lat2, lon2]: return 0.0
        R = 6371.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi, dlambda = math.radians(lat2-lat1), math.radians(lon2-lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)
    except: return 0.0

def converter_img_b64(file):
    if file: return base64.b64encode(file.getvalue()).decode()
    return None

# ------------------------------------------------------------------------------
# 3. CONEXÃO FIREBASE E BANCO DE DADOS
# ------------------------------------------------------------------------------
@st.cache_resource
def conectar_banco():
    if not firebase_admin._apps:
        try:
            b64_key = st.secrets["FIREBASE_BASE64"]
            cred = credentials.Certificate(json.loads(base64.b64decode(b64_key).decode("utf-8")))
            return firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Erro Firebase: {e}"); st.stop()
    return firebase_admin.get_app()

db = firestore.client() if conectar_banco() else None

# ------------------------------------------------------------------------------
# 4. FUNÇÕES DE SUPORTE (IA, CARGA E RADAR)
# ------------------------------------------------------------------------------
def ia_busca_consciente_v2(termo_usuario):
    termo_limpo = remover_acentos(termo_usuario)
    try:
        doc = db.collection("configuracoes").document("dicionario_ia").get()
        if doc.exists:
            for k, v in doc.to_dict().items():
                if remover_acentos(k) in termo_limpo: return v
    except: pass
    return termo_usuario.title()

def carregar_ia_em_massa():
    conhecimento = {
        "vazamento": "Encanador", "fio": "Eletricista", "tijolo": "Pedreiro", "pintar": "Pintor",
        "iphone": "Técnico de Celular", "computador": "Informática", "limpeza": "Diarista",
        "jardim": "Jardineiro", "pizza": "Pizzaria", "fome": "Lanchonete", "remedio": "Drogaria / Farmácia"
    }
    db.collection("configuracoes").document("dicionario_ia").set(conhecimento)
    return True

# ------------------------------------------------------------------------------
# 5. INTERFACE PRINCIPAL (ABAS)
# ------------------------------------------------------------------------------
st.markdown("<h1 style='text-align: center; color: #0047AB;'>🎯 GERAL<span style='color: #FF8C00;'>JÁ</span></h1>", unsafe_allow_html=True)

tabs = st.tabs(["🔍 BUSCAR", "🚀 CADASTRAR", "👤 PERFIL", "👑 ADMIN", "⭐ FEEDBACK"])

# --- ABA BUSCAR ---
with tabs[0]:
    st.markdown("### ⚡ RADAR GERALJÁ (Ofertas)")
    try:
        agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ofertas = db.collection("ofertas_live").where("expira_em", ">", agora).stream()
        cols_o = st.columns(3)
        for i, o in enumerate(ofertas):
            d = o.to_dict()
            cols_o[i % 3].info(f"**{d['nome']}**:\n{d['mensagem']}")
    except: st.write("Nenhuma oferta agora.")
    
    loc = get_geolocation()
    lat_c, lon_c = (loc['coords']['latitude'], loc['coords']['longitude']) if loc else (None, None)
    
    busca = st.text_input("O que você precisa?", placeholder="Ex: cano quebrado")
    if busca:
        cat_alvo = ia_busca_consciente_v2(busca)
        profs = db.collection("profissionais").where("status", "==", "ativo").stream()
        res = []
        for p in profs:
            d = p.to_dict()
            if remover_acentos(cat_alvo) in remover_acentos(d.get('categoria','')) or remover_acentos(busca) in remover_acentos(d.get('nome','')):
                d['dist'] = calcular_distancia(lat_c, lon_c, d.get('latitude'), d.get('longitude'))
                d['id'] = p.id
                res.append(d)
        
        if res:
            df = pd.DataFrame(res).sort_values(by=['ranking_elite', 'dist'], ascending=[False, True])
            for _, prof in df.iterrows():
                c1, c2, c3 = st.columns([1, 2, 1])
                with c1: 
                    if prof.get('foto'): st.image(f"data:image/png;base64,{prof['foto']}", width=100)
                    else: st.title("👤")
                with c2:
                    st.markdown(f"**{prof['nome']}** ({prof.get('dist', 0)} km)")
                    st.caption(f"{prof.get('categoria')} | {prof.get('descricao')[:50]}...")
                with c3:
                    tel = re.sub(r'\D', '', str(prof.get('whatsapp', '')))
                    st.link_button("🟢 WHATSAPP", f"https://wa.me/55{tel}")
        else: st.warning("Nada encontrado.")

# --- ABA CADASTRAR ---
with tabs[1]:
    tipo = st.radio("Tipo:", ["Profissional Liberal", "Comércio / Loja"], horizontal=True)
    cats_p = sorted(["Eletricista", "Encanador", "Pedreiro", "Pintor", "Técnico de Celular", "Diarista"])
    cats_c = sorted(["Lanchonete", "Pizzaria", "Drogaria / Farmácia", "Mercado", "Padaria"])
    
    with st.form("cad"):
        nome = st.text_input("Nome*")
        zap = st.text_input("WhatsApp*")
        cat = st.selectbox("Categoria*", cats_p if "Profissional" in tipo else cats_c)
        desc = st.text_area("Descrição")
        foto = st.file_uploader("Foto")
        if st.form_submit_button("CADASTRAR"):
            if nome and zap and lat_c:
                db.collection("profissionais").add({
                    "nome": nome, "whatsapp": zap, "categoria": cat, "descricao": desc,
                    "foto": converter_img_b64(foto), "latitude": lat_c, "longitude": lon_c,
                    "status": "ativo", "saldo": 5.0, "ranking_elite": 0, "visualizacoes": 0
                })
                st.success("Cadastrado!")
            else: st.error("Falta nome, zap ou GPS!")

# --- ABA ADMIN ---
with tabs[3]:
    if st.text_input("Senha Master", type="password") == "mumias":
        if st.button("🚀 INICIALIZAR IA"):
            if carregar_ia_em_massa(): st.success("IA Pronta!")

# --- ABA FEEDBACK ---
with tabs[4]:
    msg_f = st.text_area("Sugestões")
    if st.button("ENVIAR") and msg_f:
        db.collection("feedbacks").add({"mensagem": msg_f, "data": datetime.datetime.now().isoformat()})
        st.success("Valeu!")
# --- DESIGN LAPIDADO DOS RESULTADOS ---
for _, prof in df.iterrows():
    # Container com borda e sombra via CSS
    st.markdown(f"""
        <div style="
            border: 1px solid #e0e0e0;
            border-radius: 15px;
            padding: 15px;
            margin-bottom: 15px;
            background-color: {'#ffffff' if st.session_state.tema_claro else '#1E293B'};
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        ">
            <table style="width:100%; border-collapse: collapse;">
                <tr>
                    <td style="width: 80px; vertical-align: top;">
                        <img src="data:image/png;base64,{prof.get('foto') if prof.get('foto') else ''}" 
                             style="width:70px; height:70px; border-radius:50%; object-fit: cover; border: 2px solid #FF8C00;">
                    </td>
                    <td style="padding-left: 15px;">
                        <h3 style="margin:0; color: #0047AB;">{prof['nome']}</h3>
                        <p style="margin:2px 0; font-weight: bold; color: #FF8C00;">{prof.get('categoria')}</p>
                        <p style="margin:0; font-size: 0.9em; opacity: 0.8;">📍 a {prof.get('dist', 0)} km de você</p>
                    </td>
                </tr>
            </table>
            <p style="margin-top: 10px; font-style: italic;">"{prof.get('descricao')[:120]}..."</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Botões de Ação embaixo do card estilizado
    c1, c2 = st.columns(2)
    with c1:
        tel = re.sub(r'\D', '', str(prof.get('whatsapp', '')))
        st.link_button("💬 CHAMAR AGORA", f"https://wa.me/55{tel}", use_container_width=True)
    with c2:
        if st.button("📄 VER PERFIL", key=f"view_{prof['id']}", use_container_width=True):
            st.toast(f"Abrindo perfil de {prof['nome']}...")
    st.write("") # Espaçador
# ------------------------------------------------------------------------------
# 14. ABA CADASTRAR: DESIGN LAPIDADO E CATEGORIAS ROBUSTAS
# ------------------------------------------------------------------------------
with tabs[1]:
    st.markdown("<h2 style='text-align: center;'>🚀 Comece a Vender Agora</h2>", unsafe_allow_html=True)
    st.write("---") # Linha de separação

    # 1. FILTRO DE TIPO DE NEGÓCIO
    tipo_cadastro = st.radio(
        "Selecione o seu perfil profissional:",
        ["👨‍🔧 Profissional Liberal", "🏪 Comércio / Loja"],
        horizontal=True
    )
    st.write("---") # Linha de separação

    # 2. LISTAS ORGANIZADAS (A-Z)
    cats_prof = sorted(["Adestrador", "Babá", "Chaveiro", "Confeiteira", "Costureira", "Cozinheiro", "Diarista", "Eletricista", "Encanador", "Esteticista", "Fisioterapeuta", "Fretes", "Informática", "Jardineiro", "Manicure", "Marceneiro", "Mecânico", "Montador", "Motorista", "Pedreiro", "Pintor", "Piscineiro", "Professor", "Técnico Celular", "Técnico Geladeira", "Técnico TV", "Veterinário"])
    cats_com = sorted(["Açougue", "Adega", "Armarinho", "Auto Peças", "Barbearia", "Bazar", "Bicicletaria", "Casa de Rações", "Depósito", "Doceria", "Farmácia", "Floricultura", "Hortifruti", "Lanchonete", "Loja de Roupas", "Mercado", "Padaria", "Papelaria", "Perfumaria", "Pet Shop", "Pizzaria", "Restaurante", "Salão de Beleza", "Sorveteria"])

    # 3. FORMULÁRIO COM DESIGN CLEAN
    with st.form("form_cadastro_premium", clear_on_submit=True):
        col_1, col_2 = st.columns(2)
        
        with col_1:
            nome_biz = st.text_input("Nome do Negócio ou Nome Completo*")
            zap_biz = st.text_input("WhatsApp com DDD (Somente números)*")
            if "Profissional" in tipo_cadastro:
                cat_biz = st.selectbox("Sua Especialidade*", cats_prof)
            else:
                cat_biz = st.selectbox("Ramo do Comércio*", cats_com)
        
        with col_2:
            foto_biz = st.file_uploader("Sua Logo ou Foto de Perfil", type=['png', 'jpg', 'jpeg'])
            desc_biz = st.text_area("Descrição (O que você faz de melhor?)")

        st.write("---") # Linha de separação
        st.markdown("### 📍 Localização de Atendimento")
        st.caption("O GPS precisa estar ativo para que os clientes te encontrem por proximidade.")
        
        # Captura automática no form
        loc_cad = get_geolocation()
        st.write("---") # Linha de separação

        # 4. BOTÃO FINAL "BOTANDO PARA TORAR"
        if st.form_submit_button("CONCLUIR MEU CADASTRO AGORA"):
            if nome_biz and zap_biz and loc_cad:
                try:
                    img_data = converter_img_b64(foto_biz)
                    db.collection("profissionais").add({
                        "nome": nome_biz,
                        "whatsapp": zap_biz,
                        "categoria": cat_biz,
                        "tipo": "comercio" if "Comércio" in tipo_cadastro else "profissional",
                        "descricao": desc_biz,
                        "foto": img_data,
                        "latitude": loc_cad['coords']['latitude'],
                        "longitude": loc_cad['coords']['longitude'],
                        "status": "ativo",
                        "saldo": 5.0,
                        "ranking_elite": 0,
                        "visualizacoes": 0,
                        "data": datetime.datetime.now().strftime("%d/%m/%Y")
                    })
                    st.balloons()
                    st.success("🎯 Sucesso! Seu perfil já está ativo e visível no Radar GeralJá.")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("⚠️ Atenção: Nome, WhatsApp e GPS são obrigatórios!")
                # ------------------------------------------------------------------------------
# 1. IDENTIFICAÇÃO E BLINDAGEM DA VERSÃO V2
# ------------------------------------------------------------------------------
VERSION = "2.0.0-PRO"

# Limpeza de Cache para garantir que a V2 não use lixo da V1
if 'versao_sistema' not in st.session_state:
    st.cache_resource.clear()
    st.session_state.versao_sistema = VERSION

# CSS de Transição Suave (Design Moderno V2)
st.markdown("""
    <style>
        /* Badge de Versão no rodapé */
        .version-badge {
            position: fixed;
            bottom: 10px;
            right: 10px;
            font-size: 10px;
            background: #FF8C00;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            z-index: 9999;
        }
    </style>
    <div class="version-badge">GeralJá V2</div>
""", unsafe_allow_html=True)
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# 16. FINALIZADOR DE LAYOUT E RODAPÉ AUTOMÁTICO (O "VARREDOR")
# ------------------------------------------------------------------------------
def finalizar_e_alinhar_layout():
    """
    Esta função atua como um imã. Ela puxa todo o conteúdo anterior para 
    o alinhamento correto e limpa distorções antes de carregar o rodapé.
    """
    st.write("---") # Linha de separação final
    
    # CSS de fechamento e centralização forçada
    fechamento_estilo = """
        <style>
            /* Garante que o último elemento não cole no fundo da tela */
            .main .block-container {
                padding-bottom: 5rem !important;
            }
            
            /* Força o alinhamento central de qualquer texto órfão no final */
            .footer-clean {
                text-align: center;
                padding: 20px;
                opacity: 0.7;
                font-size: 0.8rem;
                width: 100%;
            }
        </style>
        
        <div class="footer-clean">
            <p>🎯 <b>GeralJá</b> - Sistema de Inteligência Local</p>
            <p>Conectando quem precisa com quem sabe fazer.</p>
            <p>v2.0 | © 2026 Todos os direitos reservados</p>
        </div>
    """
    st.markdown(fechamento_estilo, unsafe_allow_html=True)

# CHAMADA FINAL - ESTA DEVE SER A ÚLTIMA LINHA DO SEU APP
finalizar_e_alinhar_layout()
# ------------------------------------------------------------------------------

