# ==============================================================================
# GERALJÁ SP - ENTERPRISE EDITION v19.0 (STABLE & EXPANDED)
# O SISTEMA MAIS COMPLETO JÁ DESENVOLVIDO PARA GESTÃO DE SERVIÇOS EM SÃO PAULO
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
# 1. CONFIGURAÇÃO DE AMBIENTE E PERFORMANCE
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="GeralJá | Ecossistema Profissional SP",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ------------------------------------------------------------------------------
# 2. CAMADA DE PERSISTÊNCIA (FIREBASE)
# ------------------------------------------------------------------------------
@st.cache_resource
def conectar_banco_master():
    """Inicializa a conexão com segurança e tratamento de falhas."""
    if not firebase_admin._apps:
        try:
            if "FIREBASE_BASE64" not in st.secrets:
                st.error("🔑 Chave de segurança FIREBASE_BASE64 não encontrada nos Secrets.")
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

# ------------------------------------------------------------------------------
# 3. POLÍTICAS DE GOVERNANÇA E CONSTANTES
# ------------------------------------------------------------------------------
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ADMIN = "mumias"
TAXA_CONTATO = 1
BONUS_WELCOME = 5

# Localização Referência: São Paulo - SP
LAT_REF_SP = -23.5505
LON_REF_SP = -46.6333

CATEGORIAS_OFICIAIS = [
    "Encanador", "Eletricista", "Pintor", "Pedreiro", "Gesseiro",
    "Telhadista", "Mecânico", "Borracheiro", "Guincho 24h", "Diarista",
    "Jardineiro", "Piscineiro", "TI", "Refrigeração", "Ajudante Geral"
]

# ------------------------------------------------------------------------------
# 4. MOTOR DE IA E GEOLOCALIZAÇÃO
# ------------------------------------------------------------------------------
CONCEITOS_EXPANDIDOS = {
    "vazamento": "Encanador", "cano": "Encanador", "torneira": "Encanador", "esgoto": "Encanador",
    "curto": "Eletricista", "fiação": "Eletricista", "disjuntor": "Eletricista", "luz": "Eletricista",
    "pintar": "Pintor", "reforma": "Pedreiro", "piso": "Pedreiro", "gesso": "Gesseiro",
    "carro": "Mecânico", "motor": "Mecânico", "guincho": "Guincho 24h", "pneu": "Borracheiro",
    "faxina": "Diarista", "jardim": "Jardineiro", "piscina": "Piscineiro",
    "computador": "TI", "celular": "TI", "wifi": "TI", "ar": "Refrigeração"
}

def processar_ia_avancada(texto):
    """Analisa a intenção do cliente e mapeia para a categoria correta."""
    if not texto: return "Ajudante Geral"
    t_clean = texto.lower().strip()
    for chave, categoria in CONCEITOS_EXPANDIDOS.items():
        if re.search(rf"\b{chave}\b", t_clean):
            return categoria
    return "Ajudante Geral"

def calcular_distancia_real(lat1, lon1, lat2, lon2):
    """Cálculo Matemático de Haversine para Precisão Geográfica."""
    try:
        if None in [lat1, lon1, lat2, lon2]: return 999.0
        R = 6371 # Raio da Terra em KM
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return round(R * c, 1)
    except:
        return 999.0

def converter_img_b64(file):
    """Converte arquivos de imagem para armazenamento Base64 no Firebase."""
    if file is None: return ""
    return base64.b64encode(file.read()).decode()

# ------------------------------------------------------------------------------
# 5. DESIGN SYSTEM - CSS CUSTOMIZADO (EXPANDIDO)
# ------------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    
    * { font-family: 'Inter', sans-serif; transition: all 0.2s ease-in-out; }
    .stApp { background-color: #F8FAFC; }
    
    /* Header Container */
    .header-container { 
        background: white; padding: 50px 20px; border-radius: 0 0 60px 60px; 
        text-align: center; box-shadow: 0 10px 40px rgba(0,0,0,0.08); 
        border-bottom: 10px solid #FF8C00; margin-bottom: 30px;
    }
    
    .logo-azul { color: #0047AB; font-weight: 900; font-size: 70px; letter-spacing: -3px; }
    .logo-laranja { color: #FF8C00; font-weight: 900; font-size: 70px; letter-spacing: -3px; }
    
    /* Cards Profissionais */
    .pro-card { 
        background: white; border-radius: 35px; padding: 30px; margin-bottom: 25px; 
        border-left: 20px solid #0047AB; box-shadow: 0 15px 30px rgba(0,0,0,0.05); 
        display: flex; align-items: center; border-right: 1px solid #E2E8F0;
    }
    
    .pro-card:hover { transform: scale(1.01); box-shadow: 0 20px 40px rgba(0,0,0,0.1); }
    
    .pro-img { 
        width: 120px; height: 120px; border-radius: 50%; object-fit: cover; 
        border: 5px solid #F1F5F9; margin-right: 30px; box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    /* Badges */
    .badge-dist { background: #DBEAFE; color: #1E40AF; padding: 8px 16px; border-radius: 15px; font-weight: 800; font-size: 12px; text-transform: uppercase; }
    .badge-area { background: #FFEDD5; color: #9A3412; padding: 8px 16px; border-radius: 15px; font-weight: 800; font-size: 12px; text-transform: uppercase; margin-left: 10px; }
    
    /* Botoes */
    .btn-zap { 
        background: #22C55E; color: white !important; padding: 18px; border-radius: 20px; 
        text-decoration: none; font-weight: 900; display: block; text-align: center; 
        font-size: 18px; margin-top: 15px; box-shadow: 0 4px 14px 0 rgba(34, 197, 94, 0.39);
    }
    .btn-zap:hover { background: #16a34a; transform: translateY(-2px); }

    /* Painel Admin e Metricas */
    .metric-box { 
        background: #1E293B; color: white; padding: 30px; border-radius: 30px; 
        text-align: center; border-bottom: 6px solid #FF8C00; box-shadow: 0 10px 20px rgba(0,0,0,0.15);
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 6. LAYOUT E ABAS DE NAVEGAÇÃO (VERSÃO FINAL UNIFICADA - SEM REPETIÇÕES)
# ------------------------------------------------------------------------------
st.markdown('<div class="header-container"><span class="logo-azul">GERAL</span><span class="logo-laranja">JÁ</span><br><small style="letter-spacing:10px; color:#64748B; font-weight:700;">SÃO PAULO ELITE EDITION</small></div>', unsafe_allow_html=True)

# Criamos as 4 abas oficiais
menu_abas = st.tabs([
    "🔍 ENCONTRAR ESPECIALISTA", 
    "💼 CENTRAL DO PARCEIRO", 
    "📝 NOVO CADASTRO", 
    "🛡️ TERMINAL ADMIN"
])

# --- ABA 1: BUSCA DO CLIENTE ---
with menu_abas[0]:
    st.markdown("### 🏙️ Qual problema resolveremos agora?")
    c1, c2 = st.columns([3, 1])
    
    # Campo de busca e Slider de 5km (APENAS UMA VEZ)
    termo_busca = c1.text_input("Ex: 'Cano estourado', 'Instalar ventilador'", key="search_final_v1")
    raio_km = c2.select_slider("Raio de Busca (KM)", options=[1, 5, 10, 20, 50, 100], value=5, key="slider_final_v1")
    
    if termo_busca:
        cat_ia = processar_ia_avancada(termo_busca)
        st.info(f"✨ **IA:** Buscando especialistas em **{cat_ia}** próximo a você.")
        
        profs = db.collection("profissionais").where("area", "==", cat_ia).where("aprovado", "==", True).stream()
        lista_ranking = []
        
        for p_doc in profs:
            p = p_doc.to_dict()
            p['id'] = p_doc.id
            dist = calcular_distancia_real(LAT_REF_SP, LON_REF_SP, p.get('lat', LAT_REF_SP), p.get('lon', LON_REF_SP))
            if dist <= raio_km:
                p['dist'] = dist
                lista_ranking.append(p)
        
        lista_ranking.sort(key=lambda x: x['dist'])
        
        if not lista_ranking:
            st.warning("📍 Nenhum profissional encontrado neste raio de 5km.")
        else:
            for pro in lista_ranking:
                with st.container():
                    st.markdown(f"""
                    <div class="pro-card">
                        <img src="{pro.get('foto_url') or 'https://api.dicebear.com/7.x/avataaars/svg?seed='+pro['id']}" class="pro-img">
                        <div style="flex-grow:1;">
                            <span class="badge-dist">📍 {pro['dist']} KM</span>
                            <span class="badge-area">💎 {pro['area']}</span>
                            <h2 style="margin:15px 0; color:#1E293B;">{pro.get('nome', 'Profissional').upper()}</h2>
                            <p style="color:#475569; font-size:14px;">{pro.get('descricao', 'Especialista em SP.')}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if pro.get('saldo', 0) >= TAXA_CONTATO:
                        if st.button(f"CONTATAR {pro['nome'].split()[0].upper()}", key=f"btn_c_{pro['id']}"):
                            db.collection("profissionais").document(pro['id']).update({
                                "saldo": firestore.Increment(-TAXA_CONTATO),
                                "cliques": firestore.Increment(1)
                            })
                            st.balloons()
                            st.markdown(f'<a href="https://wa.me/55{pro["whatsapp"]}" class="btn-zap">ABRIR WHATSAPP</a>', unsafe_allow_html=True)

# --- ABA 2: CENTRAL DO PARCEIRO ---
with menu_abas[1]:
    # (Inserir aqui o código de login do parceiro que você já tem)
    st.write("Acesse seu painel para gerenciar créditos e leads.")

# --- ABA 3: NOVO CADASTRO ---
with menu_abas[2]:
    # (Inserir aqui o código de cadastro com categoria manual que revisamos)
    st.write("Crie seu perfil profissional no GeralJá.")

# --- ABA 4: TERMINAL ADMIN + FEEDBACK ---
with menu_abas[3]:
    access_adm = st.text_input("Senha Master", type="password", key="adm_auth_final")
    if access_adm == CHAVE_ADMIN:
        tab_pro, tab_feed = st.tabs(["👥 PROFISSIONAIS", "📩 FEEDBACKS"])
        
        with tab_pro:
            st.write("Gerenciar aprovações e moedas.")
            # (Inserir código de gestão aqui)
            
        with tab_feed:
            st.write("### 📩 Feedbacks dos Usuários")
            # Aqui você verá as mensagens do menu Feedback
# ------------------------------------------------------------------------------
# ABA 1: MOTOR DE BUSCA (Ajustado para 5km padrão)
# ------------------------------------------------------------------------------
with menu_abas[0]:
    st.markdown("### 🏙️ Qual problema resolveremos agora?")
    c1, c2 = st.columns([3, 1])
    
    # Campo de busca com chave única
    termo_busca = c1.text_input("Ex: 'Cano estourado', 'Instalar ventilador'", key="search_input_unique_v1")
    
    # Linha corrigida: o recuo (espaço à esquerda) está agora alinhado corretamente
    raio_km = c2.select_slider("Raio de Busca (KM)", options=[1, 5, 10, 20, 50, 100], value=5)
    
    if termo_busca:
        cat_ia = processar_ia_avancada(termo_busca)
        st.info(f"✨ **Análise da IA:** Filtrando os melhores profissionais em **{cat_ia}** próximo a você.")
        
        profs = db.collection("profissionais").where("area", "==", cat_ia).where("aprovado", "==", True).stream()
        lista_ranking = []
        
        for p_doc in profs:
            p = p_doc.to_dict()
            p['id'] = p_doc.id
            dist = calcular_distancia_real(LAT_REF_SP, LON_REF_SP, p.get('lat', LAT_REF_SP), p.get('lon', LON_REF_SP))
            if dist <= raio_km:
                p['dist'] = dist
                lista_ranking.append(p)
        
        lista_ranking.sort(key=lambda x: x['dist'])
        
        if not lista_ranking:
            st.warning("📍 Nenhum profissional desta categoria atende neste raio no momento.")
        else:
            for pro in lista_ranking:
                with st.container():
                    st.markdown(f"""
                    <div class="pro-card">
                        <img src="{pro.get('foto_url') or 'https://api.dicebear.com/7.x/avataaars/svg?seed='+pro['id']}" class="pro-img">
                        <div style="flex-grow:1;">
                            <span class="badge-dist">📍 {pro['dist']} KM DE VOCÊ</span>
                            <span class="badge-area">💎 {pro['area']}</span>
                            <h2 style="margin:15px 0; color:#1E293B;">{pro.get('nome', 'Profissional').upper()}</h2>
                            <p style="color:#475569; font-size:15px; line-height:1.6;">{pro.get('descricao', 'Especialista em serviços gerais pronto para te atender.')}</p>
                            <p style="color:#64748B; font-size:13px;">⭐ {pro.get('rating', 5.0)} | 🏙️ {pro.get('localizacao', 'São Paulo - SP')}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if pro.get('saldo', 0) >= TAXA_CONTATO:
                        if st.button(f"FALAR COM {pro['nome'].split()[0].upper()}", key=f"contact_btn_{pro['id']}"):
                            db.collection("profissionais").document(pro['id']).update({
                                "saldo": firestore.Increment(-TAXA_CONTATO),
                                "cliques": firestore.Increment(1)
                            })
                            st.balloons()
                            st.markdown(f'<a href="https://wa.me/55{pro["whatsapp"]}?text=Olá {pro["nome"]}, vi seu anúncio no GeralJá!" class="btn-zap">ABRIR CONVERSA NO WHATSAPP</a>', unsafe_allow_html=True)
                    else:
                        st.error("⏳ Este profissional está com a agenda lotada.")
    
    # ... (O restante do código da busca continua abaixo daqui)
# ------------------------------------------------------------------------------
# ABA 1: MOTOR DE BUSCA (REVISADA E ALINHADA)
# ------------------------------------------------------------------------------
with menu_abas[0]:
    st.markdown("### 🏙️ Qual problema resolveremos agora?")
    c1, c2 = st.columns([3, 1])
    
    # Campo de busca com chave única para evitar erro de duplicidade
    termo_busca = c1.text_input(
        "Ex: 'Cano estourado', 'Instalar ventilador'", 
        key="main_search_input_unique"
    )
    
    # ESTA LINHA ABAIXO ESTAVA CAUSANDO O ERRO NO SEU LINK:
    # Ela deve ter exatamente o mesmo recuo (espaço) que a linha de cima.
    raio_km = c2.select_slider(
        "Raio de Busca (KM)", 
        options=[1, 5, 10, 20, 50, 100], 
        value=5, 
        key="main_slider_raio_unique"
    )
    
    if termo_busca:
        cat_ia = processar_ia_avancada(termo_busca)
        st.info(f"✨ **Análise da IA:** Filtrando profissionais em **{cat_ia}**.")
        
        # Filtro de busca no banco de dados
        profs = db.collection("profissionais").where("area", "==", cat_ia).where("aprovado", "==", True).stream()
        lista_ranking = []
        
        for p_doc in profs:
            p = p_doc.to_dict()
            p['id'] = p_doc.id
            dist = calcular_distancia_real(LAT_REF_SP, LON_REF_SP, p.get('lat', LAT_REF_SP), p.get('lon', LON_REF_SP))
            if dist <= raio_km:
                p['dist'] = dist
                lista_ranking.append(p)
        
        lista_ranking.sort(key=lambda x: x['dist'])
        
        if not lista_ranking:
            st.warning("📍 Nenhum profissional encontrado neste raio de 5km.")
        else:
            for pro in lista_ranking:
                with st.container():
                    # Card visual do profissional
                    st.markdown(f"""
                    <div class="pro-card">
                        <img src="{pro.get('foto_url') or 'https://api.dicebear.com/7.x/avataaars/svg?seed='+pro['id']}" class="pro-img">
                        <div style="flex-grow:1;">
                            <span class="badge-dist">📍 {pro['dist']} KM</span>
                            <span class="badge-area">💎 {pro['area']}</span>
                            <h2 style="margin:15px 0; color:#1E293B;">{pro.get('nome', 'Profissional').upper()}</h2>
                            <p style="font-size:14px; color:#475569;">{pro.get('descricao', 'Especialista disponível.')}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if pro.get('saldo', 0) >= TAXA_CONTATO:
                        if st.button(f"CONTATAR {pro['nome'].split()[0].upper()}", key=f"call_{pro['id']}"):
                            db.collection("profissionais").document(pro['id']).update({
                                "saldo": firestore.Increment(-TAXA_CONTATO),
                                "cliques": firestore.Increment(1)
                            })
                            st.markdown(f'<a href="https://wa.me/55{pro["whatsapp"]}" class="btn-zap">ABRIR WHATSAPP</a>', unsafe_allow_html=True)

# --- ADICIONE "Outro" NAS CATEGORIAS OFICIAIS NO TOPO DO CODIGO ---
if "Outro (Personalizado)" not in CATEGORIAS_OFICIAIS:
    CATEGORIAS_OFICIAIS.append("Outro (Personalizado)")

# ------------------------------------------------------------------------------
# ABA 2: CENTRAL DO PROFISSIONAL (LOGIN / DASHBOARD) - ATUALIZADA
# ------------------------------------------------------------------------------
with menu_abas[1]:
    if 'auth' not in st.session_state: st.session_state.auth = False
    
    if not st.session_state.auth:
        st.subheader("🔑 Login do Parceiro")
        col_l1, col_l2 = st.columns(2)
        login_zap = col_l1.text_input("WhatsApp (Login)", placeholder="11999998888")
        login_pw = col_l2.text_input("Senha", type="password")
        
        if st.button("ENTRAR NO PAINEL", use_container_width=True):
            user_doc = db.collection("profissionais").document(login_zap).get()
            if user_doc.exists and user_doc.to_dict().get('senha') == login_pw:
                st.session_state.auth = True
                st.session_state.user_id = login_zap
                st.rerun()
            else:
                st.error("❌ Credenciais inválidas.")
    else:
        uid = st.session_state.user_id
        dados = db.collection("profissionais").document(uid).get().to_dict()
        
        st.success(f"### Bem-vindo, {dados.get('nome')}!")
        
        # Dashboard de Métricas
        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(f'<div class="metric-box"><small>SALDO</small><br><b style="font-size:35px;">{dados.get("saldo", 0)} 🪙</b></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric-box"><small>LEADS</small><br><b style="font-size:35px;">{dados.get("cliques", 0)} 🚀</b></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric-box"><small>NOTA</small><br><b style="font-size:35px;">{dados.get("rating", 5.0)} ⭐</b></div>', unsafe_allow_html=True)
        m4.markdown(f'<div class="metric-box" style="background:{"#059669" if dados.get("aprovado") else "#B91C1C"}"><small>STATUS</small><br><b style="font-size:25px;">{"ATIVO" if dados.get("aprovado") else "BLOQUEADO"}</b></div>', unsafe_allow_html=True)
        
        st.divider()
        
        # Edição de Perfil
        with st.expander("🛠️ EDITAR MEUS DADOS PÚBLICOS"):
            with st.form("edit_form_final"):
                ed_nome = st.text_input("Nome de Exibição", value=dados.get('nome'))
                
                # Lógica de Categoria Dinâmica
                cat_atual = dados.get('area')
                index_cat = CATEGORIAS_OFICIAIS.index(cat_atual) if cat_atual in CATEGORIAS_OFICIAIS else (len(CATEGORIAS_OFICIAIS)-1)
                
                ed_cat_sel = st.selectbox("Sua Categoria", CATEGORIAS_OFICIAIS, index=index_cat)
                
                # Campo extra aparece apenas se selecionar "Outro"
                ed_cat_custom = ""
                if ed_cat_sel == "Outro (Personalizado)":
                    ed_cat_custom = st.text_input("Escreva sua categoria personalizada", value=cat_atual if cat_atual not in CATEGORIAS_OFICIAIS else "")
                
                ed_desc = st.text_area("Descrição do Perfil", value=dados.get('descricao'), height=150)
                ed_loc = st.text_input("Bairro/Cidade", value=dados.get('localizacao'))
                
                up_foto = st.file_uploader("Trocar Foto de Perfil", type=['jpg','png','jpeg'])
                
                if st.form_submit_button("SALVAR TODAS AS ALTERAÇÕES"):
                    # Define qual categoria salvar
                    categoria_final = ed_cat_custom if ed_cat_sel == "Outro (Personalizado)" else ed_cat_sel
                    
                    if ed_cat_sel == "Outro (Personalizado)" and not ed_cat_custom:
                        st.error("⚠️ Por favor, digite o nome da sua categoria personalizada.")
                    else:
                        upd_payload = {
                            "nome": ed_nome, 
                            "area": categoria_final, 
                            "descricao": ed_desc, 
                            "localizacao": ed_loc, 
                            "ultima_att": datetime.datetime.now()
                        }
                        if up_foto: upd_payload["foto_url"] = f"data:image/png;base64,{converter_img_b64(up_foto)}"
                        
                        db.collection("profissionais").document(uid).update(upd_payload)
                        st.success("✅ Perfil atualizado com sucesso!")
                        time.sleep(1)
                        st.rerun()

        # Botao de Logout
        if st.button("SAIR DA CONTA", type="secondary"):
            st.session_state.auth = False
            st.rerun()

# ------------------------------------------------------------------------------
# ABA 3: CADASTRO DE NOVOS PARCEIROS (COM CATEGORIA PERSONALIZADA)
# ------------------------------------------------------------------------------
with menu_abas[2]:
    st.markdown("### 🚀 Junte-se à elite dos profissionais")
    st.info("Preencha seus dados abaixo. Você pode escolher uma categoria existente ou criar uma nova!")

    with st.form("cadastro_form_v2"):
        col_reg1, col_reg2 = st.columns(2)
        reg_nome = col_reg1.text_input("Nome Completo ou Nome Fantasia")
        reg_zap = col_reg1.text_input("WhatsApp (Ex: 11999998888)")
        reg_pw = col_reg2.text_input("Crie uma Senha de Acesso", type="password")
        reg_loc = col_reg2.text_input("Bairro/Região de Atendimento", placeholder="Ex: Santana, ZN")
        
        st.divider()
        
        # Sistema de Categoria Manual
        st.write("**Selecione sua Especialidade:**")
        if "Outra (Escrever Manualmente)" not in CATEGORIAS_OFICIAIS:
            CATEGORIAS_OFICIAIS.append("Outra (Escrever Manualmente)")
            
        reg_cat_sel = st.selectbox("Categoria Principal", CATEGORIAS_OFICIAIS)
        
        reg_cat_custom = ""
        if reg_cat_sel == "Outra (Escrever Manualmente)":
            reg_cat_custom = st.text_input("Digite sua profissão/especialidade:", placeholder="Ex: Instalador de Câmeras, Tapeceiro, etc.")
        
        reg_desc = st.text_area("Descrição dos seus serviços (O que você faz de melhor?)", height=100)
        
        # Upload de Foto opcional no cadastro
        reg_foto = st.file_uploader("Sua Foto Profissional (Opcional)", type=['jpg', 'png', 'jpeg'])

        enviar_cad = st.form_submit_button("CRIAR MEU PERFIL AGORA")

        if enviar_cad:
            # Validação da Categoria
            categoria_final = reg_cat_custom if reg_cat_sel == "Outra (Escrever Manualmente)" else reg_cat_sel
            
            if not reg_nome or not reg_zap or not reg_pw:
                st.error("⚠️ Nome, WhatsApp e Senha são obrigatórios!")
            elif reg_cat_sel == "Outra (Escrever Manualmente)" and not reg_cat_custom:
                st.error("⚠️ Por favor, digite o nome da sua categoria personalizada.")
            else:
                with st.spinner("Processando seu cadastro..."):
                    # Processamento de Imagem se houver
                    foto_b64 = ""
                    if reg_foto:
                        foto_b64 = f"data:image/png;base64,{converter_img_b64(reg_foto)}"
                    
                    # Salva no Firebase
                    db.collection("profissionais").document(reg_zap).set({
                        "nome": reg_nome,
                        "whatsapp": reg_zap,
                        "senha": reg_pw,
                        "descricao": reg_desc,
                        "area": categoria_final,
                        "localizacao": reg_loc,
                        "saldo": BONUS_WELCOME, # Ganha bônus ao entrar
                        "cliques": 0,
                        "rating": 5.0,
                        "aprovado": False, # Aguarda admin liberar
                        "foto_url": foto_b64,
                        "lat": LAT_REF_SP,
                        "lon": LON_REF_SP,
                        "data_registro": datetime.datetime.now()
                    })
                    
                    st.success(f"✅ Cadastro realizado! Você foi registrado como **{categoria_final}**.")
                    st.warning("📍 Seu perfil está em análise. Assim que o administrador aprovar, você aparecerá nas buscas!")
                    st.balloons()
# ------------------------------------------------------------------------------
# ABA 4: TERMINAL ADMIN (GESTOR + FEEDBACKS INTEGRADOS)
# ------------------------------------------------------------------------------
with menu_abas[3]:
    # 'key' única para evitar o erro de DuplicateElementKey
    access_adm = st.text_input("Senha Master", type="password", key="master_adm_auth")
    
    if access_adm == CHAVE_ADMIN:
        st.markdown("## 🛡️ Central de Comando GeralJá")
        
        # Sub-abas para separar Gestão de Profissionais dos Feedbacks
        sub_tab_pro, sub_tab_feed = st.tabs(["👥 GESTÃO DE PARCEIROS", "📩 FEEDBACKS E RESPOSTAS"])
        
        # --- PARTE 1: GESTÃO DE PROFISSIONAIS ---
        with sub_tab_pro:
            st.subheader("Controle de Profissionais")
            busca_adm = st.text_input("Procurar por Nome ou WhatsApp", key="filter_adm_pro")
            
            profs_all = db.collection("profissionais").stream()
            for p_doc in profs_all:
                p, pid = p_doc.to_dict(), p_doc.id
                if not busca_adm or busca_adm.lower() in p.get('nome','').lower() or busca_adm in pid:
                    status_txt = "🟢 ATIVO" if p.get('aprovado') else "🟡 PENDENTE"
                    with st.expander(f"{status_txt} | {p.get('nome')} | ID: {pid}"):
                        st.write(f"**Área:** {p.get('area')} | **Saldo:** {p.get('saldo')} 🪙")
                        
                        ca1, ca2, ca3 = st.columns(3)
                        # Botão Aprovar
                        if ca1.button("APROVAR", key=f"ap_sys_{pid}"):
                            db.collection("profissionais").document(pid).update({"aprovado": True})
                            st.success(f"{p.get('nome')} aprovado!")
                            time.sleep(0.5)
                            st.rerun()
                        
                        # Adicionar Moedas
                        val_add = ca2.number_input("Adicionar Moedas", 1, 500, 10, key=f"val_sys_{pid}")
                        if ca2.button("CREDITAR", key=f"cr_sys_{pid}"):
                            db.collection("profissionais").document(pid).update({"saldo": firestore.Increment(val_add)})
                            st.success(f"Creditado {val_add} moedas!")
                            time.sleep(0.5)
                            st.rerun()
                            
                        # Remover Conta
                        if ca3.button("REMOVER CONTA", key=f"del_sys_{pid}"):
                            db.collection("profissionais").document(pid).delete()
                            st.warning("Conta removida.")
                            time.sleep(0.5)
                            st.rerun()

        # --- PARTE 2: RESPOSTAS DIRECIONADAS (FEEDBACKS) ---
        with sub_tab_feed:
            st.subheader("📩 Mensagens dos Usuários")
            feedbacks = db.collection("feedbacks").order_by("data", direction="DESCENDING").stream()
            
            count_fb = 0
            for f_doc in feedbacks:
                count_fb += 1
                f = f_doc.to_dict()
                fid = f_doc.id
                is_lido = f.get('lido', False)
                
                status_icon = "🆕" if not is_lido else "✅"
                with st.expander(f"{status_icon} {f.get('tipo')} - {f.get('nome')}"):
                    st.markdown(f"**Mensagem:** {f.get('mensagem')}")
                    st.markdown(f"**Contato:** {f.get('contato', 'Não informado')}")
                    st.caption(f"Data: {f.get('data').strftime('%d/%m/%Y %H:%M')}")
                    
                    if not is_lido:
                        if st.button("Marcar como Lido", key=f"read_fb_{fid}"):
                            db.collection("feedbacks").document(fid).update({"lido": True})
                            st.rerun()
            
            if count_fb == 0:
                st.info("Nenhum feedback recebido ainda.")

# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# RODAPÉ
# ------------------------------------------------------------------------------
st.markdown(f"""
    <div style="text-align:center; padding:40px; color:#94A3B8; font-size:12px;">
        GERALJÁ SP v19.0 © {datetime.datetime.now().year}<br>
        Infraestrutura Distribuída | Google Cloud & Firebase Firestore
    </div>
""", unsafe_allow_html=True)

























