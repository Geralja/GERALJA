# ==============================================================================
# ============================================================================== 
# GERALJÁ SP - ENTERPRISE EDITION v19.0 
# O SISTEMA MAIS COMPLETO JÁ DESENVOLVIDO PARA GESTÃO DE SERVIÇOS 
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
import pandas as pd 
from io import BytesIO 

# ------------------------------------------------------------------------------ 
# 1. ARQUITETURA DE SISTEMA (CONFIGURAÇÃO GLOBAL) 
# ------------------------------------------------------------------------------ 
st.set_page_config( 
    page_title="GeralJá | Ecossistema Profissional SP", 
    page_icon="🏙️", 
    layout="wide",  # Layout expandido para ferramentas profissionais 
    initial_sidebar_state="collapsed" 
) 

# ------------------------------------------------------------------------------ 
# 2. CONEXÃO E INFRAESTRUTURA DE DADOS (FIREBASE CORE) 
# ------------------------------------------------------------------------------ 
@st.cache_resource 
def conectar_banco_master(): 
    """Inicializa a conexão com o Google Firebase via Service Account.""" 
    if not firebase_admin._apps: 
        try: 
            b64_key = st.secrets["FIREBASE_BASE64"] 
            decoded_json = base64.b64decode(b64_key).decode("utf-8") 
            cred_dict = json.loads(decoded_json) 
            cred = credentials.Certificate(cred_dict) 
            return firebase_admin.initialize_app(cred) 
        except Exception as e: 
            st.error(f"❌ ERRO CRÍTICO NA CONEXÃO: {e}") 
            st.stop() 
    return firebase_admin.get_app() 

app_engine = conectar_banco_master() 
db = firestore.client() 

# ------------------------------------------------------------------------------ 
# 3. CONSTANTES E PARÂMETROS DE GOVERNANÇA 
# ------------------------------------------------------------------------------ 
# Dados de Operação Financeira 
PIX_OFICIAL = "11991853488" 
ZAP_ADMIN = "5511991853488" 
CHAVE_ADMIN = "mumias" 
VALOR_MOEDA_REAL = 1.00  # R$ 1,00 por moeda 
TAXA_CONTATO = 1  # 1 moeda por clique de cliente 
BONUS_WELCOME = 5  # Moedas grátis no cadastro 

# Geocoordenadas de São Paulo (Marco Zero - Praça da Sé) 
LAT_REF_SP = -23.5505 
LON_REF_SP = -46.6333 

CATEGORIAS_OFICIAIS = [
    "Encanador", "Eletricista", "Pintor", "Pedreiro", "Gesseiro",
    "Telhadista", "Mecânico", "Borracheiro", "Guincho 24h", "Diarista",
    "Jardineiro", "Piscineiro", "TI", "Refrigeração", "Ajudante Geral"
]

# ------------------------------------------------------------------------------ 
# 4. MOTOR DE INTELIGÊNCIA ARTIFICIAL (MAPEAMENTO SEMÂNTICO) 
# ------------------------------------------------------------------------------ 
CONCEITOS_EXPANDIDOS = { 
    # HIDRÁULICA 
    "vazamento": "Encanador", 
    "cano": "Encanador", 
    "torneira": "Encanador", 
    "esgoto": "Encanador", 
    "pia": "Encanador", 
    "caixa": "Encanador", 
    "infiltração": "Encanador", 
    "registro": "Encanador", 
    # ELÉTRICA 
    "curto": "Eletricista", 
    "luz": "Eletricista", 
    "tomada": "Eletricista", 
    "chuveiro": "Eletricista", 
    "fiação": "Eletricista", 
    "disjuntor": "Eletricista", 
    "lâmpada": "Eletricista", 
    "fio": "Eletricista", 
    # CONSTRUÇÃO E REFORMA 
    "pintar": "Pintor", 
    "parede": "Pintor", 
    "massa": "Pintor", 
    "grafiato": "Pintor", 
    "verniz": "Pintor", 
    "reforma": "Pedreiro", 
    "laje": "Pedreiro", 
    "tijolo": "Pedreiro", 
    "piso": "Pedreiro", 
    "azulejo": "Pedreiro", 
    "gesso": "Gesseiro", 
    "drywall": "Gesseiro", 
    "forro": "Gesseiro", 
    "telhado": "Telhadista", 
    "calha": "Telhadista", 
    # AUTOMOTIVO 
    "carro": "Mecânico", 
    "motor": "Mecânico", 
    "embreagem": "Mecânico", 
    "freio": "Mecânico", 
    "óleo": "Mecânico", 
    "pneu": "Borracheiro", 
    "borracharia": "Borracheiro", 
    "guincho": "Guincho 24h", 
    "reboque": "Guincho 24h", 
    # SERVIÇOS DOMÉSTICOS 
    "faxina": "Diarista", 
    "limpeza": "Diarista", 
    "passar": "Diarista", 
    "doméstica": "Diarista", 
    "jardim": "Jardineiro", 
    "grama": "Jardineiro", 
    "poda": "Jardineiro", 
    "piscina": "Piscineiro", 
    # TECNOLOGIA 
    "computador": "TI", 
    "celular": "TI", 
    "formatar": "TI", 
    "wifi": "TI", 
    "rede": "TI", 
    "ar": "Refrigeração", 
    "geladeira": "Refrigeração", 
    "freezer": "Refrigeração" 
} 

def processar_ia_avancada(texto): 
    if not texto: 
        return "Ajudante Geral" 
    t_clean = texto.lower().strip() 
    for chave, categoria in CONCEITOS_EXPANDIDOS.items(): 
        if re.search(rf"\b{chave}\b", t_clean): 
            return categoria 
    return "Ajudante Geral" 

def calcular_distancia_real(lat1, lon1, lat2, lon2): 
    """Cálculo de Haversine para precisão métrica.""" 
    if None in [lat1, lon1, lat2, lon2]: 
        return 999.0 
    R = 6371 
    dlat = math.radians(lat2 - lat1) 
    dlon = math.radians(lon2 - lon1) 
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2 
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)) 
    return round(R * c, 1) 

def converter_img_b64(file): 
    return base64.b64encode(file.read()).decode() 

# ------------------------------------------------------------------------------ 
# 5. DESIGN SYSTEM (INTERFACE PREMIUM SÃO PAULO) 
# ------------------------------------------------------------------------------ 
st.markdown(f""" 
<style> 
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap'); 
    * {{ font-family: 'Inter', sans-serif; }} 
    .stApp {{ background-color: #F8FAFC; }} 
    /* Header Estilizado */ 
    .header-container {{ background: white; padding: 40px; border-radius: 0 0 60px 60px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.05); border-bottom: 8px solid #FF8C00; }} 
    .logo-azul {{ color: #0047AB; font-weight: 900; font-size: 60px; letter-spacing: -2px; }} 
    .logo-laranja {{ color: #FF8C00; font-weight: 900; font-size: 60px; letter-spacing: -2px; }} 
    /* Cards de Profissionais */ 
    .pro-card {{ background: white; border-radius: 30px; padding: 25px; margin-bottom: 20px; border-left: 15px solid #0047AB; box-shadow: 0 10px 20px rgba(0,0,0,0.03); display: flex; align-items: center; transition: 0.3s; }} 
    .pro-card:hover {{ transform: translateY(-5px); box-shadow: 0 15px 35px rgba(0,0,0,0.08); }} 
    .pro-img {{ width: 100px; height: 100px; border-radius: 50%; object-fit: cover; border: 4px solid #F1F5F9; margin-right: 25px; }} 
    /* Bad
# GERALJÁ SP - ENTERPRISE EDITION v19.0
# O SISTEMA MAIS COMPLETO JÁ DESENVOLVIDO PARA GESTÃO DE SERVIÇOS
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
import pandas as pd
from io import BytesIO

# ------------------------------------------------------------------------------
# 1. ARQUITETURA DE SISTEMA (CONFIGURAÇÃO GLOBAL)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="GeralJá | Ecossistema Profissional SP",
    page_icon="🏙️",
    layout="wide", # Layout expandido para ferramentas profissionais
    initial_sidebar_state="collapsed"
)

# ------------------------------------------------------------------------------
# 2. CONEXÃO E INFRAESTRUTURA DE DADOS (FIREBASE CORE)
# ------------------------------------------------------------------------------
@st.cache_resource
def conectar_banco_master():
    """Inicializa a conexão com o Google Firebase via Service Account."""
    if not firebase_admin._apps:
        try:
            b64_key = st.secrets["FIREBASE_BASE64"]
            decoded_json = base64.b64decode(b64_key).decode("utf-8")
            cred_dict = json.loads(decoded_json)
            cred = credentials.Certificate(cred_dict)
            return firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"❌ ERRO CRÍTICO NA CONEXÃO: {e}")
            st.stop()
    return firebase_admin.get_app()

app_engine = conectar_banco_master()
db = firestore.client()

# ------------------------------------------------------------------------------
# 3. CONSTANTES E PARÂMETROS DE GOVERNANÇA
# ------------------------------------------------------------------------------
# Dados de Operação Financeira
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ADMIN = "mumias"
VALOR_MOEDA_REAL = 1.00  # R$ 1,00 por moeda
TAXA_CONTATO = 1         # 1 moeda por clique de cliente
BONUS_WELCOME = 5        # Moedas grátis no cadastro

# Geocoordenadas de São Paulo (Marco Zero - Praça da Sé)
LAT_REF_SP = -23.5505
LON_REF_SP = -46.6333

# ------------------------------------------------------------------------------
# 4. MOTOR DE INTELIGÊNCIA ARTIFICIAL (MAPEAMENTO SEMÂNTICO)
# ------------------------------------------------------------------------------
CONCEITOS_EXPANDIDOS = {
    # HIDRÁULICA
    "vazamento": "Encanador", "cano": "Encanador", "torneira": "Encanador", "esgoto": "Encanador", 
    "pia": "Encanador", "caixa": "Encanador", "infiltração": "Encanador", "registro": "Encanador",
    # ELÉTRICA
    "curto": "Eletricista", "luz": "Eletricista", "tomada": "Eletricista", "chuveiro": "Eletricista", 
    "fiação": "Eletricista", "disjuntor": "Eletricista", "lâmpada": "Eletricista", "fio": "Eletricista",
    # CONSTRUÇÃO E REFORMA
    "pintar": "Pintor", "parede": "Pintor", "massa": "Pintor", "grafiato": "Pintor", "verniz": "Pintor",
    "reforma": "Pedreiro", "laje": "Pedreiro", "tijolo": "Pedreiro", "piso": "Pedreiro", "azulejo": "Pedreiro",
    "gesso": "Gesseiro", "drywall": "Gesseiro", "forro": "Gesseiro", "telhado": "Telhadista", "calha": "Telhadista",
    # AUTOMOTIVO
    "carro": "Mecânico", "motor": "Mecânico", "embreagem": "Mecânico", "freio": "Mecânico", "óleo": "Mecânico",
    "pneu": "Borracheiro", "borracharia": "Borracheiro", "guincho": "Guincho 24h", "reboque": "Guincho 24h",
    # SERVIÇOS DOMÉSTICOS
    "faxina": "Diarista", "limpeza": "Diarista", "passar": "Diarista", "doméstica": "Diarista",
    "jardim": "Jardineiro", "grama": "Jardineiro", "poda": "Jardineiro", "piscina": "Piscineiro",
    # TECNOLOGIA
    "computador": "TI", "celular": "TI", "formatar": "TI", "wifi": "TI", "rede": "TI",
    "ar": "Refrigeração", "geladeira": "Refrigeração", "freezer": "Refrigeração"
}

def processar_ia_avancada(texto):
    if not texto: return "Ajudante Geral"
    t_clean = texto.lower().strip()
    for chave, categoria in CONCEITOS_EXPANDIDOS.items():
        if re.search(rf"\b{chave}\b", t_clean):
            return categoria
    return "Ajudante Geral"

def calcular_distancia_real(lat1, lon1, lat2, lon2):
    """Cálculo de Haversine para precisão métrica."""
    if None in [lat1, lon1, lat2, lon2]: return 999.0
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return round(R * c, 1)

# ------------------------------------------------------------------------------
# 5. DESIGN SYSTEM (INTERFACE PREMIUM SÃO PAULO)
# ------------------------------------------------------------------------------
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    * {{ font-family: 'Inter', sans-serif; }}
    .stApp {{ background-color: #F8FAFC; }}
    
    /* Header Estilizado */
    .header-container {{ background: white; padding: 40px; border-radius: 0 0 60px 60px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.05); border-bottom: 8px solid #FF8C00; }}
    .logo-azul {{ color: #0047AB; font-weight: 900; font-size: 60px; letter-spacing: -2px; }}
    .logo-laranja {{ color: #FF8C00; font-weight: 900; font-size: 60px; letter-spacing: -2px; }}
    
    /* Cards de Profissionais */
    .pro-card {{ background: white; border-radius: 30px; padding: 25px; margin-bottom: 20px; border-left: 15px solid #0047AB; box-shadow: 0 10px 20px rgba(0,0,0,0.03); display: flex; align-items: center; transition: 0.3s; }}
    .pro-card:hover {{ transform: translateY(-5px); box-shadow: 0 15px 35px rgba(0,0,0,0.08); }}
    .pro-img {{ width: 100px; height: 100px; border-radius: 50%; object-fit: cover; border: 4px solid #F1F5F9; margin-right: 25px; }}
    
    /* Badges e Botões */
    .badge-dist {{ background: #DBEAFE; color: #1E40AF; padding: 6px 14px; border-radius: 12px; font-weight: 900; font-size: 11px; text-transform: uppercase; }}
    .badge-area {{ background: #FFEDD5; color: #9A3412; padding: 6px 14px; border-radius: 12px; font-weight: 900; font-size: 11px; text-transform: uppercase; margin-left: 5px; }}
    .btn-zap {{ background: #22C55E; color: white !important; padding: 16px; border-radius: 18px; text-decoration: none; font-weight: 900; display: block; text-align: center; font-size: 16px; margin-top: 10px; }}
    
    /* Painel de Métricas */
    .metric-box {{ background: #1E293B; color: white; padding: 25px; border-radius: 25px; text-align: center; border-bottom: 5px solid #FF8C00; }}
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 6. NÚCLEO DE NAVEGAÇÃO (ESTRUTURA DE 4 NÍVEIS)
# ------------------------------------------------------------------------------
st.markdown('<div class="header-container"><span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span><br><small style="letter-spacing:8px; color:#64748B;">SÃO PAULO ELITE</small></div>', unsafe_allow_html=True)

menu_abas = st.tabs(["🔍 ENCONTRAR ESPECIALISTA", "💼 CENTRAL DO PROFISSIONAL", "📝 NOVO CADASTRO", "🛡️ TERMINAL ADMIN"])

# ------------------------------------------------------------------------------
# ABA 1: MOTOR DE BUSCA (CLIENTE)
# ------------------------------------------------------------------------------
with menu_abas[0]:
    st.write("### 🏙️ O que você precisa resolver hoje?")
    col_s1, col_s2 = st.columns([3, 1])
    termo_busca = col_s1.text_input("Digite o problema (Ex: Vazamento na pia, conserto de disjuntor...)", key="user_query")
    raio_km = col_s2.select_slider("Raio de Busca (KM)", options=[1, 5, 10, 20, 50, 100], value=20)
    
    if termo_busca:
        ia_categoria = processar_ia_avancada(termo_busca)
        st.info(f"✨ IA: Identificamos que você precisa de um **{ia_categoria}**")
        
        # Filtro Firestore
        docs = db.collection("profissionais").where("area", "==", ia_categoria).where("aprovado", "==", True).stream()
        
        lista_final = []
        for d in docs:
            p = d.to_dict()
            p['id'] = d.id
            # Cálculo de distância dinâmico
            dist = calcular_distancia_real(LAT_REF_SP, LON_REF_SP, p.get('lat', LAT_REF_SP), p.get('lon', LON_REF_SP))
            if dist <= raio_km:
                p['dist'] = dist
                lista_final.append(p)
        
        # Ordenação por Proximidade
        lista_final.sort(key=lambda x: x['dist'])
        
        if not lista_final:
            st.warning("⚠️ Nenhum profissional qualificado encontrado neste raio de busca.")
        else:
            for pro in lista_final:
                st.markdown(f"""
                <div class="pro-card">
                    <img src="{pro.get('foto_url') or 'https://api.dicebear.com/7.x/avataaars/svg?seed='+pro['id']}" class="pro-img">
                    <div style="flex-grow:1;">
                        <span class="badge-dist">📍 {pro['dist']} KM DE DISTÂNCIA</span>
                        <span class="badge-area">💎 {pro['area']}</span>
                        <h3 style="margin:10px 0; color:#1E293B;">{pro['nome'].upper()}</h3>
                        <p style="color:#64748B; font-size:14px; margin-bottom:10px;">⭐ {pro.get('rating', 5.0)} | 🏙️ {pro.get('localizacao', 'São Paulo - SP')}</p>
                        <p style="color:#334155; font-size:13px; font-style:italic;">"{pro.get('descricao', 'Sem descrição disponível.')}"</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Regra de Negócio: Verificação de Saldo para contato
                if pro.get('saldo', 0) >= TAXA_CONTATO:
                    if st.button(f"CONTATAR {pro['nome'].split()[0].upper()}", key=f"call_{pro['id']}"):
                        # Débito em tempo real
                        db.collection("profissionais").document(pro['id']).update({
                            "saldo": firestore.Increment(-TAXA_CONTATO),
                            "cliques": firestore.Increment(1)
                        })
                        st.balloons()
                        st.markdown(f'<a href="https://wa.me/55{pro["whatsapp"]}?text=Olá {pro["nome"]}, vi seu perfil no GeralJá e preciso de {ia_categoria}!" class="btn-zap">ABRIR WHATSAPP AGORA</a>', unsafe_allow_html=True)
                else:
                    st.error("📉 Este profissional atingiu o limite de atendimentos gratuitos.")

# ------------------------------------------------------------------------------
# ABA 2: CENTRAL DO PROFISSIONAL (LOGIN + EDIÇÃO + FINANCEIRO)
# ------------------------------------------------------------------------------
with menu_abas[1]:
    if 'auth' not in st.session_state:
        st.session_state.auth = False

    if not st.session_state.auth:
        st.subheader("🔐 Acesso Restrito ao Parceiro")
        c_l1, c_l2 = st.columns(2)
        zap_login = c_l1.text_input("WhatsApp (Login)", placeholder="11999998888")
        pass_login = c_l2.text_input("Senha", type="password")
        
        if st.button("ACESSAR MINHA CONTA", use_container_width=True):
            user_ref = db.collection("profissionais").document(zap_login).get()
            if user_ref.exists and user_ref.to_dict().get('senha') == pass_login:
                st.session_state.auth = True
                st.session_state.user_id = zap_login
                st.rerun()
            else:
                st.error("❌ Credenciais incorretas.")
    else:
        # ÁREA LOGADA
        uid = st.session_state.user_id
        dados = db.collection("profissionais").document(uid).get().to_dict()
        
        st.success(f"Logado como: **{dados.get('nome')}**")
        
        # DASHBOARD DE PERFORMANCE
        st.write("### 📊 Seu Desempenho")
        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(f'<div class="metric-box"><small>SALDO ATUAL</small><br><b style="font-size:30px;">{dados.get("saldo", 0)} 🪙</b></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric-box" style="background:#334155;"><small>LEADS RECEBIDOS</small><br><b style="font-size:30px;">{dados.get("cliques", 0)} 🚀</b></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric-box" style="background:#334155;"><small>AVALIAÇÃO</small><br><b style="font-size:30px;">{dados.get("rating", 5.0)} ⭐</b></div>', unsafe_allow_html=True)
        m4.markdown(f'<div class="metric-box" style="background:#059669;"><small>STATUS</small><br><b style="font-size:20px;">{"ATIVO" if dados.get("aprovado") else "EM ANÁLISE"}</b></div>', unsafe_allow_html=True)

        st.divider()
        
      # --- BLOCO DE EDIÇÃO CORRIGIDO (v22.1) ---
        with st.expander("📝 ATUALIZAR MEUS DADOS E PERFIL"):
            with st.form("edit_form"):
                st.markdown("### 🛠️ Informações do Profissional")
                
                # Campos de Texto e Seleção
                ed_nome = st.text_input("Nome Profissional", value=dados.get('nome'))
                
                # Nova Funcionalidade: Escolha de Profissão (Sem erro de digitação)
                ed_cat = st.selectbox(
                    "Sua Profissão Principal", 
                    CATEGORIAS_OFICIAIS, 
                    index=CATEGORIAS_OFICIAIS.index(dados.get('area')) if dados.get('area') in CATEGORIAS_OFICIAIS else 0
                )
                
                ed_desc = st.text_area("Descrição dos seus Serviços", value=dados.get('descricao'))
                
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    ed_zap = st.text_input("WhatsApp (Visualização)", value=dados.get('whatsapp'))
                with col_f2:
                    ed_bairro = st.text_input("Bairro/Cidade Principal", value=dados.get('localizacao'))

                st.divider()
                
                # Nova Funcionalidade: Carregar Foto Real
                st.write("📸 **Foto de Perfil**")
                if dados.get('foto_url'):
                    st.image(dados['foto_url'], width=100, caption="Foto Atual")
                
                uploaded_file = st.file_uploader("Escolher nova foto (JPG/PNG)", type=['jpg', 'jpeg', 'png'])

                # Botão de Envio
                submitted = st.form_submit_button("SALVAR ALTERAÇÕES")
                
                if submitted:
                    # Lógica de processamento dos dados
                    payload = {
                        "nome": ed_nome,
                        "area": ed_cat,
                        "descricao": ed_desc,
                        "whatsapp": ed_zap,
                        "localizacao": ed_bairro,
                        "ultima_edicao": datetime.datetime.now()
                    }
                    
                    # Se subiu foto nova, converte e adiciona ao payload
                    if uploaded_file is not None:
                        foto_b64 = converter_img_b64(uploaded_file)
                        payload["foto_url"] = foto_b64
                    
                    # Atualiza o Firebase
                    db.collection("profissionais").document(uid).update(payload)
                    
                    st.success("✅ Perfil atualizado com sucesso!")
                    time.sleep(1)
                    st.rerun() # Comando de reinicialização sem o parêntese extra
                
                st.write("📍 **Ajustar Minha Localização (GPS)**")
                c_gps1, c_gps2 = st.columns(2)
                ed_lat = c_gps1.number_input("Latitude", value=float(dados.get('lat', LAT_REF_SP)), format="%.6f")
                ed_lon = c_gps2.number_input("Longitude", value=float(dados.get('lon', LON_REF_SP)), format="%.6f")
                
                if st.form_submit_button("SALVAR ALTERAÇÕES"):
                    # Reclassifica categoria caso mude a descrição
                    nova_cat = processar_ia_avancada(ed_desc)
                    db.collection("profissionais").document(uid).update({
                        "nome": ed_nome, "descricao": ed_desc, "whatsapp": ed_zap,
                        "foto_url": ed_foto, "localizacao": ed_bairro,
                        "lat": ed_lat, "lon": ed_lon, "area": nova_cat
                    })
                    st.success("✅ Perfil atualizado! Recarregando...")
                    time.sleep(1)
                    st.rerun()

        # RECARGA FINANCEIRA
        with st.expander("🪙 COMPRAR MOEDAS (RECARGA)"):
            st.write("### Sistema de Recarga Instantânea")
            st.info("Cada moeda custa R$ 1,00. Elas nunca expiram.")
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={PIX_OFICIAL}")
            st.code(f"CHAVE PIX: {PIX_OFICIAL}")
            st.markdown(f'<a href="https://wa.me/{ZAP_ADMIN}?text=Fiz o PIX de recarga para o WhatsApp: {uid}" class="btn-zap">ENVIAR COMPROVANTE NO WHATSAPP</a>', unsafe_allow_html=True)

        if st.button("DESCONECTAR / LOGOUT", use_container_width=True):
            st.session_state.auth = False
            st.rerun()

# ------------------------------------------------------------------------------
# ABA 3: CADASTRO DE NOVOS PARCEIROS
# ------------------------------------------------------------------------------
with menu_abas[2]:
    st.write("### 🚀 Comece a receber serviços hoje mesmo!")
    st.write("Preencha os dados abaixo. Após o cadastro, o admin irá liberar seu acesso.")
    
    with st.form("reg_form_main"):
        c_n1, c_n2 = st.columns(2)
        reg_nome = c_n1.text_input("Nome Completo ou Nome Fantasia")
        reg_zap = c_n2.text_input("WhatsApp com DDD (Somente Números)")
        reg_pass = st.text_input("Crie uma Senha de Acesso", type="password")
        reg_bairro = st.text_input("Em qual bairro/região você atua?")
        reg_desc = st.text_area("Descreva detalhadamente o que você faz (IA vai te classificar)")
        
        st.warning("📍 O sistema usará sua posição atual de São Paulo para buscas por GPS. Você pode ajustar isso depois no seu perfil.")
        
        if st.form_submit_button("FINALIZAR MEU CADASTRO"):
            if not reg_nome or not reg_zap or not reg_pass:
                st.error("⚠️ Preencha todos os campos obrigatórios.")
            else:
                cat_detectada = processar_ia_avancada(reg_desc)
                db.collection("profissionais").document(reg_zap).set({
                    "nome": reg_nome, "whatsapp": reg_zap, "senha": reg_pass,
                    "descricao": reg_desc, "area": cat_detectada, "localizacao": reg_bairro,
                    "saldo": BONUS_WELCOME, "cliques": 0, "rating": 5.0,
                    "aprovado": False, "foto_url": "",
                    "lat": LAT_REF_SP + random.uniform(-0.05, 0.05),
                    "lon": LON_REF_SP + random.uniform(-0.05, 0.05),
                    "data_cadastro": datetime.datetime.now()
                })
                st.success(f"✅ Cadastro realizado! Você foi classificado como: **{cat_detectada}**.")
                st.markdown(f'<a href="https://wa.me/{ZAP_ADMIN}?text=Quero aprovação do meu perfil: {reg_nome}" class="btn-zap">CHAMAR ADMIN PARA LIBERAÇÃO</a>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# ABA 4: TERMINAL ADMIN (GESTOR MASTER)
# ------------------------------------------------------------------------------
with menu_abas[3]:
    adm_pass = st.text_input("Senha do Diretor", type="password")
    
    if adm_pass == CHAVE_ADMIN:
        st.subheader("🛡️ Painel de Controle Governamental")
        
        # 1. Auditoria e Limpeza
        if st.button("🔄 EXECUTAR AUDITORIA DE INTEGRIDADE", use_container_width=True):
            all_profs = db.collection("profissionais").stream()
            count = 0
            for doc in all_profs:
                d = doc.to_dict()
                upd = {}
                if "saldo" not in d: upd["saldo"] = BONUS_WELCOME
                if "aprovado" not in d: upd["aprovado"] = False
                if upd: 
                    db.collection("profissionais").document(doc.id).update(upd)
                    count +=1
            st.success(f"Auditado com sucesso: {count} registros corrigidos.")

        # 2. Gestão de Contas
        st.write("### 👥 Gerenciar Parceiros")
        busca_adm = st.text_input("Filtrar por Nome ou WhatsApp")
        
        profs_ref = db.collection("profissionais").stream()
        
        for p_doc in profs_ref:
            p = p_doc.to_dict()
            pid = p_doc.id
            
if not busca_adm or busca_adm.lower() in p['nome'].lower() or busca_adm in pid:
    status_icon = "✅" if p.get('aprovado') else "⏳"
    with st.expander(f"{status_icon} {p['nome']} | Moedas: {p['saldo']} | {p['area']}"):
        st.write(f"**WhatsApp:** {pid} | **Local:** {p.get('localizacao')}")
                    
                    c_ad1, c_ad2, c_ad3 = st.columns(3)
                    if c_ad1.button("APROVAR PERFIL", key=f"ok_{pid}"):
                        db.collection("profissionais").document(pid).update({"aprovado": True})
                        st.rerun()
                    
                    add_moedas = c_ad2.number_input("Add Moedas", value=10, key=f"num_{pid}")
                    if c_ad2.button(f"CREDITAR {add_moedas}", key=f"add_{pid}"):
                        db.collection("profissionais").document(pid).update({"saldo": firestore.Increment(add_moedas)})
                        st.rerun()
                        
                    if c_ad3.button("BANIR CONTA", key=f"del_{pid}"):
                        db.collection("profissionais").document(pid).delete()
                        st.rerun()
                    
                    st.divider()
                    st.write("⚙️ **Configurações Avançadas**")
                    nova_senha_adm = st.text_input("Nova Senha", key=f"pw_{pid}")
                    if st.button("RESETAR SENHA", key=f"res_{pid}"):
                        db.collection("profissionais").document(pid).update({"senha": nova_senha_adm})
                        st.success("Senha alterada!")

# ------------------------------------------------------------------------------
# RODAPÉ TÉCNICO
# ------------------------------------------------------------------------------
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown(f"""
    <center>
        <p style="color:#64748B; font-size:12px;">GERALJÁ SP v19.0 - Motor de Gestão de Alta Performance</p>
        <p style="color:#94A3B8; font-size:10px;">Cloud: Google Firebase | Logic: Python 3.10 | UI: Streamlit Carbon</p>
    </center>
""", unsafe_allow_html=True)










