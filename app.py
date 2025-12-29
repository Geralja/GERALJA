# ==============================================================================
# GERALJÁ BRASIL - OMNIVERSAL EDITION v2.000 (INTEGRAÇÃO TOTAL E ABSOLUTA)
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

# ------------------------------------------------------------------------------
# 1. METADADOS E CONFIGURAÇÃO DA ENGINE
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="GeralJá | Ecossistema Nacional de Serviços",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://wa.me/5511991853488',
        'About': "GeralJá v2.000 - O auge da tecnologia de serviços."
    }
)

# ------------------------------------------------------------------------------
# 2. CONEXÃO FIREBASE (SINGLETON SEGURO)
# ------------------------------------------------------------------------------
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
            st.error(f"❌ ERRO CRÍTICO NA INFRAESTRUTURA: {erro_fatal}")
            st.stop()
    return firebase_admin.get_app()

app_engine = inicializar_infraestrutura_dados()
db = firestore.client()

# ------------------------------------------------------------------------------
# 3. CONSTANTES, REGRAS FINANCEIRAS E PARÂMETROS
# ------------------------------------------------------------------------------
PIX_OFICIAL = "11991853488"
ZAP_ADMIN = "5511991853488"
CHAVE_ACESSO_ADMIN = "mumias"
TAXA_CONTATO = 1
BONUS_WELCOME = 5
LAT_SP_REF, LON_SP_REF = -23.5505, -46.6333
LISTA_ESTADOS = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]

# ------------------------------------------------------------------------------
# 4. MOTOR DE IA E MAPEAMENTO DE CATEGORIAS (EXPANSÃO MÁXIMA)
# ------------------------------------------------------------------------------
CONCEITOS_SERVICOS = {
    # HIDRÁULICA
    "vazamento": "Encanador", "cano": "Encanador", "torneira": "Encanador", "esgoto": "Encanador", 
    "pia": "Encanador", "privada": "Encanador", "caixa d'água": "Encanador", "infiltração": "Encanador",
    "desentupir": "Desentupidora", "rallo": "Desentupidora", "fossa": "Desentupidora",
    # ELÉTRICA
    "curto": "Eletricista", "luz": "Eletricista", "tomada": "Eletricista", "chuveiro": "Eletricista", 
    "fiação": "Eletricista", "disjuntor": "Eletricista", "lâmpada": "Eletricista", "interfone": "Eletricista",
    "ar condicionado": "Refrigeração", "geladeira": "Refrigeração", "freezer": "Refrigeração",
    # CONSTRUÇÃO
    "pintar": "Pintor", "parede": "Pintor", "massa": "Pintor", "grafiato": "Pintor", "verniz": "Pintor",
    "reforma": "Pedreiro", "laje": "Pedreiro", "tijolo": "Pedreiro", "reboco": "Pedreiro", "piso": "Pedreiro", 
    "azulejo": "Pedreiro", "cimento": "Pedreiro", "muro": "Pedreiro", "telhado": "Telhadista",
    "calha": "Telhadista", "goteira": "Telhadista", "gesso": "Gesseiro", "drywall": "Gesseiro",
    "serralheiro": "Serralheiro", "portão": "Serralheiro", "solda": "Serralheiro",
    # DOMÉSTICOS / BELEZA
    "faxina": "Diarista", "limpeza": "Diarista", "passar": "Diarista", "jardim": "Jardineiro", 
    "piscina": "Piscineiro", "babá": "Babá", "cozinheira": "Cozinheira", "unha": "Manicure", 
    "cabelo": "Cabeleireiro", "barba": "Barbeiro", "sobrancelha": "Esteticista", "massagem": "Massagista",
    # AUTO E TECH
    "pneu": "Borracheiro", "carro": "Mecânico", "motor": "Mecânico", "moto": "Mecânico de Motos", 
    "guincho": "Guincho 24h", "computador": "TI / Informática", "celular": "Técnico de Celular",
    "notebook": "TI / Informática", "wifi": "TI / Informática", "aula": "Professor Particular",
    "montar": "Montador de Móveis", "armário": "Montador de Móveis"
}

# ------------------------------------------------------------------------------
# 5. FUNÇÕES CORE (LÓGICA, SEGURANÇA E MATEMÁTICA)
# ------------------------------------------------------------------------------
def processar_servico_ia(texto):
    if not texto: return "Ajudante Geral"
    t_clean = texto.lower().strip()
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

def tabela_precos_auto(categoria):
    precos = {
        "Encanador": "R$ 90 - R$ 400", "Eletricista": "R$ 100 - R$ 500",
        "Diarista": "R$ 160 - R$ 300", "Mecânico": "R$ 150 - R$ 900",
        "Manicure": "R$ 50 - R$ 150", "Pedreiro": "R$ 180 - R$ 350/dia"
    }
    return precos.get(categoria, "Sob consulta via WhatsApp")

def executar_auditoria_seguranca(db_instancia):
    try:
        profs_ref = db_instancia.collection("profissionais").stream()
        c = 0
        for doc in profs_ref:
            d, upd = doc.to_dict(), {}
            for campo, valor in {"rating": 5.0, "saldo": BONUS_WELCOME, "cliques": 0, "aprovado": False, "foto_url": ""}.items():
                if campo not in d: upd[campo] = valor
            if upd:
                db_instancia.collection("profissionais").document(doc.id).update(upd)
                c += 1
        return f"✅ Auditoria Concluída: {c} registros sanitizados."
    except Exception as e: return f"❌ Erro na varredura: {e}"

# ------------------------------------------------------------------------------
# 6. DESIGN SYSTEM (CSS PREMIUM)
# ------------------------------------------------------------------------------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap');
    * { font-family: 'Montserrat', sans-serif; }
    .stApp { background-color: #F8FAFC; }
    .header-box { text-align: center; padding: 30px; background: white; border-bottom: 8px solid #FF8C00; border-radius: 0 0 40px 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); }
    .txt-azul { color: #0047AB; font-size: 60px; font-weight: 900; letter-spacing: -3px; }
    .txt-laranja { color: #FF8C00; font-size: 60px; font-weight: 900; letter-spacing: -3px; }
    .card-vazado { background: white; border-radius: 25px; padding: 25px; margin-bottom: 20px; border-left: 15px solid #0047AB; box-shadow: 0 10px 25px rgba(0,0,0,0.05); display: flex; align-items: center; }
    .avatar-pro { width: 100px; height: 100px; border-radius: 50%; object-fit: cover; margin-right: 25px; border: 4px solid #F1F5F9; }
    .btn-wpp { background: #22C55E; color: white !important; padding: 15px; border-radius: 15px; text-decoration: none; display: block; text-align: center; font-weight: 900; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-box"><span class="txt-azul">GERAL</span><span class="txt-laranja">JÁ</span><br><small style="color:#64748B; letter-spacing:8px; font-size:14px; font-weight:700;">BRASIL PROFISSIONAL</small></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 7. NAVEGAÇÃO INTEGRADA (SISTEMA DE ABAS BLINDADO)
# ------------------------------------------------------------------------------
UI_ABAS = st.tabs(["🔍 BUSCAR", "💼 CONTA", "📝 CADASTRAR", "🛡️ ADMIN"])

# ABA 1: CLIENTE (BUSCA E RESULTADOS)
with UI_ABAS[0]:
    st.write("### 🏙️ O que você precisa resolver agora?")
    col_c, col_t = st.columns([1, 2])
    cidade_alvo = col_c.text_input("Sua Cidade", placeholder="Ex: São Paulo")
    termo_busca = col_t.text_input("O que você procura?", placeholder="Ex: Consertar chuveiro, pintar...")
    
    if termo_busca:
        cat_ia = processar_servico_ia(termo_busca)
        media_preco = tabela_precos_auto(cat_ia)
        st.info(f"✨ IA: Localizamos profissionais em **{cat_ia}**. Média de preço: **{media_preco}**")
        
        query = db.collection("profissionais").where("area", "==", cat_ia).where("aprovado", "==", True).stream()
        profs_list = []
        for d in query:
            p = d.to_dict()
            p['id'] = d.id
            if not cidade_alvo or cidade_alvo.lower() in p.get('cidade', '').lower():
                p['dist'] = calcular_km_real(LAT_SP_REF, LON_SP_REF, p.get('lat', LAT_SP_REF), p.get('lon', LON_SP_REF))
                profs_list.append(p)
        
        profs_list.sort(key=lambda x: x['dist'])
        
        for pro in profs_list:
            foto = pro.get('foto_url')
            img_tag = f'<img src="{foto}" class="avatar-pro">' if foto else '<div class="avatar-pro" style="background:#E2E8F0; display:flex; align-items:center; justify-content:center; font-size:40px;">👤</div>'
            st.markdown(f'''
                <div class="card-vazado">
                    {img_tag}
                    <div style="flex-grow:1;">
                        <h3 style="margin:0;">{pro['nome'].upper()}</h3>
                        <p style="color:#64748B; margin:5px 0;">📍 {pro.get('cidade')} | 📏 {pro['dist']}km | ⭐ {pro.get('rating')}</p>
                        <p><b>Especialidade:</b> {pro.get('area')}</p>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
            if pro.get('saldo', 0) >= TAXA_CONTATO:
                if st.button(f"FALAR COM {pro['nome'].split()[0]}", key=f"call_{pro['id']}"):
                    db.collection("profissionais").document(pro['id']).update({"saldo": firestore.Increment(-TAXA_CONTATO), "cliques": firestore.Increment(1)})
                    st.markdown(f'<a href="https://wa.me/55{pro["whatsapp"]}?text=Olá, vi seu perfil no GeralJá!" class="btn-wpp">ABRIR WHATSAPP</a>', unsafe_allow_html=True)
            else: st.error("Este profissional está temporariamente indisponível.")

# ABA 2: PROFISSIONAL (DASHBOARD E PERFIL)
with UI_ABAS[1]:
    if 'logado' not in st.session_state: st.session_state.logado = False
    if not st.session_state.logado:
        st.subheader("🔑 Acesso ao Painel")
        l_zap = st.text_input("WhatsApp (Login)")
        l_pass = st.text_input("Senha", type="password")
        if st.button("ENTRAR NO PAINEL"):
            user_ref = db.collection("profissionais").document(l_zap).get()
            if user_ref.exists and user_ref.to_dict().get('senha') == l_pass:
                st.session_state.logado, st.session_state.uid = True, l_zap
                st.rerun()
            else: st.error("Dados incorretos.")
    else:
        dados = db.collection("profissionais").document(st.session_state.uid).get().to_dict()
        st.success(f"Bem-vindo, {dados['nome']}!")
        col1, col2, col3 = st.columns(3)
        col1.metric("Moedas", dados.get('saldo'))
        col2.metric("Avaliação", dados.get('rating'))
        col3.metric("Leads Ganhos", dados.get('cliques'))
        
        st.divider()
        nova_foto = st.text_input("Link da Foto de Perfil", value=dados.get('foto_url'))
        if st.button("Salvar Perfil"):
            db.collection("profissionais").document(st.session_state.uid).update({"foto_url": nova_foto})
            st.success("Foto atualizada!")
        
        st.write("### 💳 Recarga PIX")
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={PIX_OFICIAL}")
        st.code(f"Chave PIX: {PIX_OFICIAL}")
        st.markdown(f'<a href="https://wa.me/{ZAP_ADMIN}?text=Fiz o PIX de recarga para: {st.session_state.uid}" class="btn-wpp">ENVIAR COMPROVANTE</a>', unsafe_allow_html=True)
        if st.button("SAIR"): 
            st.session_state.logado = False
            st.rerun()

# ABA 3: CADASTRO (FORMULÁRIO NACIONAL)
with UI_ABAS[2]:
    st.subheader("📝 Junte-se ao GeralJá Brasil")
    with st.form("reg_form"):
        f_n = st.text_input("Nome/Empresa")
        f_z = st.text_input("WhatsApp (DDD + Número)")
        f_s = st.text_input("Senha de Acesso", type="password")
        f_c = st.text_input("Sua Cidade")
        f_u = st.selectbox("Estado", LISTA_ESTADOS)
        f_d = st.text_area("Descreva seu serviço detalhadamente:")
        if st.form_submit_button("CADASTRAR E GANHAR 5 MOEDAS"):
            if f_n and f_z and f_s:
                cat_ia_auto = processar_servico_ia(f_d)
                db.collection("profissionais").document(f_z).set({
                    "nome": f_n, "whatsapp": f_z, "senha": f_s, "cidade": f_c, "uf": f_u,
                    "area": cat_ia_auto, "descricao": f_d, "saldo": BONUS_WELCOME, "cliques": 0,
                    "rating": 5.0, "aprovado": False, "foto_url": "", "timestamp": datetime.datetime.now(),
                    "lat": LAT_SP_REF + random.uniform(-0.1, 0.1), "lon": LON_SP_REF + random.uniform(-0.1, 0.1)
                })
                st.success(f"Cadastro realizado! Categoria: **{cat_ia_auto}**.")
                st.markdown(f'<a href="https://wa.me/{ZAP_ADMIN}?text=Fiz o cadastro: {f_n}" class="btn-wpp">AVISAR ADMIN PARA APROVAR</a>', unsafe_allow_html=True)

# =============================================================
# MÓDULO ADMINISTRATIVO GERALJÁ - GESTÃO TOTAL
# =============================================================
with UI_ABAS[3]:
    acesso_cod = st.text_input("Chave Administrativa:", type="password", key="adm_key")
    
    if acesso_cod == CHAVE_ACESSO_ADMIN:
        st.subheader("🛡️ Painel de Controle e Gestão")
        
        # --- FERRAMENTAS DE MANUTENÇÃO ---
        col_m1, col_m2 = st.columns(2)
        if col_m1.button("🚀 EXECUTAR VARREDURA DE SEGURANÇA", use_container_width=True):
            try:
                # Sanitização automática para evitar KeyError
                all_docs = db.collection("profissionais").stream()
                count = 0
                for doc in all_docs:
                    d_ref = doc.to_dict()
                    upd_data = {}
                    if "area" not in d_ref: upd_data["area"] = "Ajudante Geral"
                    if "saldo" not in d_ref: upd_data["saldo"] = 0
                    if upd_data:
                        db.collection("profissionais").document(doc.id).update(upd_data)
                        count += 1
                st.success(f"Sanitização concluída! {count} perfis corrigidos.")
            except Exception as e:
                st.error(f"Erro na varredura: {e}")

        st.divider()
        
        # --- FILTRO DE BUSCA ---
        busca_term = st.text_input("Filtrar por Nome, Zap ou Cidade:", key="adm_search").lower()
        
        # --- LISTAGEM DE PROFISSIONAIS ---
        try:
            profs_stream = db.collection("profissionais").stream()
            
            for doc in profs_stream:
                p = doc.to_dict()
                pid = doc.id
                nome_atual = p.get('nome', 'Sem Nome').upper()
                zap_atual = p.get('whatsapp', pid)
                area_atual = p.get('area', 'Não Classificada')
                cidade_atual = p.get('cidade', 'Não Informada')
                
                # Filtro lógico
                if not busca_term or busca_term in nome_atual.lower() or busca_term in zap_atual or busca_term in cidade_atual.lower():
                    status_icon = "✅" if p.get('aprovado', False) else "⏳"
                    
                    with st.expander(f"{status_icon} {nome_atual} | {area_atual} ({p.get('saldo', 0)} 🪙)"):
                        
                        # --- SEÇÃO 1: EDIÇÃO DE PERFIL ---
                        st.markdown("#### 📝 Editar Perfil")
                        with st.form(key=f"edit_pro_{pid}"):
                            e_col1, e_col2 = st.columns(2)
                            edit_nome = e_col1.text_input("Nome/Empresa", value=p.get('nome', ''))
                            edit_area = e_col2.text_input("Área de Atuação", value=p.get('area', ''))
                            
                            e_col3, e_col4 = st.columns(2)
                            edit_cidade = e_col3.text_input("Cidade", value=p.get('cidade', ''))
                            edit_zap = e_col4.text_input("WhatsApp (Login)", value=p.get('whatsapp', ''))
                            
                            edit_desc = st.text_area("Descrição do Serviço", value=p.get('descricao', ''))
                            
                            if st.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                                db.collection("profissionais").document(pid).update({
                                    "nome": edit_nome,
                                    "area": edit_area,
                                    "cidade": edit_cidade,
                                    "descricao": edit_desc,
                                    "whatsapp": edit_zap
                                })
                                st.success("Perfil atualizado!")
                                st.rerun()

                        # --- SEÇÃO 2: FINANCEIRO E ACESSO ---
                        st.markdown("#### ⚙️ Controle e Financeiro")
                        c_act1, c_act2, c_act3, c_act4 = st.columns(4)
                        
                        # Botão de Aprovação Dinâmico
                        if p.get('aprovado', False):
                            if c_act1.button("REMOVER ACESSO 🚫", key=f"dis_{pid}", use_container_width=True):
                                db.collection("profissionais").document(pid).update({"aprovado": False})
                                st.rerun()
                        else:
                            if c_act1.button("APROVAR ✅", key=f"app_{pid}", use_container_width=True):
                                db.collection("profissionais").document(pid).update({"aprovado": True})
                                st.rerun()

                        # Punição Financeira
                        if c_act2.button("PUNIR -5 🪙", key=f"pun_{pid}", use_container_width=True):
                            db.collection("profissionais").document(pid).update({"saldo": firestore.Increment(-5)})
                            st.rerun()

                        # Reset de Credenciais
                        if c_act3.button("RESET SENHA 🔑", key=f"pw_{pid}", use_container_width=True):
                            db.collection("profissionais").document(pid).update({"senha": "123"})
                            st.info("Senha resetada para: 123")

                        # Exclusão Definitiva
                        if c_act4.button("EXCLUIR PERFIL 🗑️", key=f"del_{pid}", use_container_width=True):
                            db.collection("profissionais").document(pid).delete()
                            st.rerun()

                        # Adição de Moedas
                        st.write("---")
                        s_col1, s_col2 = st.columns([1, 2])
                        qtd_moedas = s_col1.number_input("Qtd Moedas", 1, 1000, 10, key=f"num_{pid}")
                        if s_col2.button(f"ADICIONAR +{qtd_moedas} MOEDAS", key=f"add_{pid}", use_container_width=True):
                            db.collection("profissionais").document(pid).update({"saldo": firestore.Increment(qtd_moedas)})
                            st.rerun()
                            
        except Exception as e:
            st.error(f"Erro ao carregar lista: {e}")

    elif acesso_cod:
        st.error("Chave Administrativa Inválida.")

# RODAPÉ TÉCNICO
st.markdown("<br><hr><center><p style='color:#64748B; font-size:12px;'>GeralJá Brasil v2.000 © 2025 | Build: Nacional Premium</p></center>", unsafe_allow_html=True)

