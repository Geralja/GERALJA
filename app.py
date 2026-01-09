# ==============================================================================
# GERALJÁ: SISTEMA INTEGRADO (BLINDADO E ORGANIZADO)
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
import requests
from streamlit_js_eval import streamlit_js_eval, get_geolocation

# ------------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DE PÁGINA (ÚNICA E BLINDADA)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="GeralJá | Soluções Rápidas",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ------------------------------------------------------------------------------
# 2. SISTEMA DE TEMA E ESTILO VISUAL (CSS MESTRE)
# ------------------------------------------------------------------------------
if 'tema_claro' not in st.session_state:
    st.session_state.tema_claro = False

def aplicar_estilo():
    # Esconde elementos nativos do Streamlit para parecer um App profissional
    hide_style = """
        <style>
            header[data-testid="stHeader"] { visibility: hidden !important; height: 0; }
            footer { visibility: hidden !important; }
            #MainMenu { visibility: hidden !important; }
            .stDeployButton { display:none !important; }
            .block-container { padding-top: 2rem !important; }
            .stButton>button { border-radius: 10px; font-weight: bold; width: 100%; }
        </style>
    """
    st.markdown(hide_style, unsafe_allow_html=True)
    
    if st.session_state.tema_claro:
        st.markdown("""
            <style>
                .stApp { background-color: white !important; }
                * { color: #1E293B !important; }
            </style>
        """, unsafe_allow_html=True)

aplicar_estilo()

# Interface de topo
with st.sidebar:
    st.session_state.tema_claro = st.toggle("☀️ Modo Claro Force", value=st.session_state.tema_claro)
    st.write("---")

st.markdown("<h1 style='text-align: center; color: #0047AB;'>🎯 GERAL<span style='color: #FF8C00;'>JÁ</span></h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; margin-top: -15px;'>Tudo o que você precisa, onde você estiver.</p>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 3. FUNÇÕES DE NORMALIZAÇÃO (O FILTRO DA IA)
# ------------------------------------------------------------------------------
def remover_acentos(texto):
    if not texto: return ""
    texto = str(texto)
    nfkd_form = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in nfkd_form if not unicodedata.category(c) == 'Mn']).lower().strip()

# ------------------------------------------------------------------------------
# 4. FUNÇÕES GEOGRÁFICAS (MOTOR GPS)
# ------------------------------------------------------------------------------
def calcular_distancia(lat1, lon1, lat2, lon2):
    try:
        if None in [lat1, lon1, lat2, lon2]: return 0.0
        R = 6371.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return round(R * c, 1)
    except:
        return 0.0

# ------------------------------------------------------------------------------
# 5. CONVERSOR DE IMAGENS (SISTEMA DE FOTOS)
# ------------------------------------------------------------------------------
def converter_img_b64(file):
    if file is not None:
        try:
            return base64.b64encode(file.getvalue()).decode()
        except:
            return None
    return None

# ------------------------------------------------------------------------------
# 6. CONEXÃO FIREBASE (BLINDADA COM CACHE)
# ------------------------------------------------------------------------------
@st.cache_resource
def conectar_banco():
    if not firebase_admin._apps:
        try:
            b64_key = st.secrets["FIREBASE_BASE64"]
            decoded_json = base64.b64decode(b64_key).decode("utf-8")
            cred_dict = json.loads(decoded_json)
            cred = credentials.Certificate(cred_dict)
            return firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"🚨 Erro de Conexão: {e}")
            st.stop()
    return firebase_admin.get_app()

db = firestore.client() if conectar_banco() else None

# ------------------------------------------------------------------------------
# 7. FUNÇÃO DE CARGA DE INTELIGÊNCIA (EM MASSA)
# ------------------------------------------------------------------------------
def carregar_ia_em_massa():
    conhecimento = {
        "vazamento": "Encanador", "desentupir": "Encanador", "torneira": "Encanador", "privada": "Encanador",
        "fio": "Eletricista", "curto": "Eletricista", "chuveiro": "Eletricista", "disjuntor": "Eletricista",
        "tijolo": "Pedreiro", "cimento": "Pedreiro", "telhado": "Pedreiro", "reforma": "Pedreiro",
        "pintar": "Pintor", "parede": "Pintor", "grafiato": "Pintor",
        "iphone": "Técnico de Celular", "android": "Técnico de Celular", "quebrou": "Técnico de Celular",
        "computador": "Informática", "notebook": "Informática", "formatar": "Informática", "wifi": "Informática",
        "limpeza": "Diarista", "faxina": "Diarista", "passar roupa": "Diarista",
        "jardim": "Jardineiro", "grama": "Jardineiro", "piscina": "Piscineiro"
    }
    try:
        db.collection("configuracoes").document("dicionario_ia").set(conhecimento)
        return True
    except:
        return False

# ------------------------------------------------------------------------------
# 8. SISTEMA GUARDIÃO (AUTO-REPARO)
# ------------------------------------------------------------------------------
def guardia_escanear_e_corrigir():
    logs = []
    try:
        profs = db.collection("profissionais").stream()
        for p in profs:
            d = p.to_dict()
            reparos = {}
            if 'saldo' not in d: reparos['saldo'] = 5.0
            if 'status' not in d: reparos['status'] = 'pendente'
            if 'ranking_elite' not in d: reparos['ranking_elite'] = 0
            if reparos:
                db.collection("profissionais").document(p.id).update(reparos)
                logs.append(f"✅ {d.get('nome', p.id)} reparado.")
        return logs if logs else ["🛡️ Sistema íntegro."]
    except Exception as e:
        return [f"❌ Erro: {e}"]
        # ------------------------------------------------------------------------------
# 9. MOTOR DE BUSCA COM IA DO BANCO (CONSCIÊNCIA VIVA)
# ------------------------------------------------------------------------------
def ia_busca_consciente_v2(termo_usuario):
    """
    Lê o dicionário que você criou no Firebase e traduz o que o usuário quer.
    Se o banco falhar, ela usa o termo digitado como padrão.
    """
    termo_limpo = remover_acentos(termo_usuario)
    try:
        # Busca o documento 'dicionario_ia' que configuramos juntos
        doc = db.collection("configuracoes").document("dicionario_ia").get()
        if doc.exists:
            dicionario_vivo = doc.to_dict()
            # Varredura inteligente: procura a palavra-chave dentro da frase
            for palavra_chave, categoria in dicionario_vivo.items():
                if remover_acentos(palavra_chave) in termo_limpo:
                    return categoria
    except Exception as e:
        st.sidebar.error(f"Erro na IA: {e}")
            
    return termo_usuario.title()

# ------------------------------------------------------------------------------
# 10. ESTRUTURA DE NAVEGAÇÃO (AS ABAS DO GERALJÁ)
# ------------------------------------------------------------------------------

# Títulos das abas - Aqui recuperamos todas as funções do seu app(5).py
titulos_abas = ["🔍 BUSCAR", "🚀 CADASTRAR", "👤 MEU PERFIL", "👑 ADMIN", "⭐ FEEDBACK"]

# Criando as abas de forma limpa
tabs = st.tabs(titulos_abas)

# ------------------------------------------------------------------------------
# 11. CONTEÚDO DA ABA ADMIN (ONDE ESTÁ A CHAVE DO MOTOR)
# ------------------------------------------------------------------------------
with tabs[3]: # Aba ADMIN
    st.header("👑 Painel de Controle Master")
    
    # Campo de senha blindado
    acesso_admin = st.text_input("Digite a Senha Master", type="password", key="admin_key")
    
    if acesso_admin == "mumias":
        st.success("Acesso Liberado, Comandante!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Inteligência")
            # O BOTÃO QUE ALIMENTA O FIREBASE AUTOMATICAMENTE
            if st.button("🚀 INICIALIZAR INTELIGÊNCIA EM MASSA"):
                if carregar_ia_em_massa():
                    st.balloons()
                    st.success("Dicionário enviado ao Firebase! Agora a IA já sabe tudo.")
        
        with col2:
            st.subheader("Manutenção")
            # O BOTÃO QUE CONSERTA O BANCO DE DADOS
            if st.button("🛡️ EXECUTAR SISTEMA GUARDIÃO"):
                relatorio = guardia_escanear_e_corrigir()
                for item in relatorio:
                    st.write(item)

# ------------------------------------------------------------------------------
# 12. CONTEÚDO DA ABA FEEDBACK (SISTEMA DE AVALIAÇÃO)
# ------------------------------------------------------------------------------
with tabs[4]: # Aba FEEDBACK
    st.header("⭐ Sua opinião é fundamental")
    
    nota = st.slider("Qual sua nota para o GeralJá?", 1, 5, 5)
    comentario = st.text_area("O que podemos melhorar?", placeholder="Escreva aqui...")
    
    if st.button("ENVIAR AVALIAÇÃO", use_container_width=True):
        if comentario.strip():
            try:
                agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                db.collection("feedbacks").add({
                    "data": agora,
                    "nota": nota,
                    "mensagem": comentario,
                    "lido": False
                })
                st.success("🙏 Obrigado! Feedback enviado com sucesso.")
            except Exception as e:
                st.error(f"Erro ao salvar feedback: {e}")
        else:
            st.warning("⚠️ Por favor, escreva uma mensagem.")
            # ------------------------------------------------------------------------------
# 13. ABA BUSCAR: O MOTOR PRINCIPAL (GPS + RANKING + WHATSAPP)
# ------------------------------------------------------------------------------
with tabs[0]: # Aba BUSCAR
    # 1. PEGAR LOCALIZAÇÃO DO CLIENTE (BLINDADO)
    loc_cliente = get_geolocation()
    lat_c, lon_c = None, None
    
    if loc_cliente and 'coords' in loc_cliente:
        lat_c = loc_cliente['coords']['latitude']
        lon_c = loc_cliente['coords']['longitude']
        st.success(f"📍 Sua localização foi detectada com precisão.")
    else:
        st.info("💡 Ative o GPS para ver a distância dos profissionais.")

    # 2. CAMPO DE BUSCA INTELIGENTE
    busca_raw = st.text_input("O que você precisa hoje?", placeholder="Ex: meu cano estourou, consertar iphone, faxina...")
    
    if busca_raw:
        # A IA traduz o que o cliente quer usando o banco de dados
        categoria_alvo = ia_busca_consciente_v2(busca_raw)
        st.subheader(f"🔍 Resultados para: {categoria_alvo}")
        
        # 3. BUSCA NO FIREBASE
        try:
            # Pega profissionais da categoria ou que tenham o termo no nome/descrição
            profs_ref = db.collection("profissionais").where("status", "==", "ativo").stream()
            lista_resultados = []
            
            for p in profs_ref:
                d = p.to_dict()
                # Filtro lógico: Categoria exata OU termo contido no nome/serviço
                if (remover_acentos(categoria_alvo) in remover_acentos(d.get('categoria', '')) or 
                    remover_acentos(busca_raw) in remover_acentos(d.get('nome', ''))):
                    
                    # Calcula distância se tiver GPS
                    dist = 0.0
                    if lat_c and lon_c and 'latitude' in d and 'longitude' in d:
                        dist = calcular_distancia(lat_c, lon_c, d['latitude'], d['longitude'])
                    
                    d['distancia_calc'] = dist
                    d['id_doc'] = p.id
                    lista_resultados.append(d)
            
            if lista_resultados:
                # 4. RANKING ELITE (Ordena por: 1º Ranking Elite, 2º Menor Distância)
                df = pd.DataFrame(lista_resultados)
                df = df.sort_values(by=['ranking_elite', 'distancia_calc'], ascending=[False, True])
                
                # 5. MOSTRAR CARDS DOS PROFISSIONAIS
                for _, prof in df.iterrows():
                    with st.container():
                        # Layout do Card
                        c1, c2, c3 = st.columns([1, 2, 1])
                        
                        with c1:
                            # Foto com fallback (se não tiver foto, usa ícone)
                            if prof.get('foto'):
                                st.image(f"data:image/png;base64,{prof['foto']}", width=120)
                            else:
                                st.markdown("👤", help="Sem foto disponível")
                        
                        with c2:
                            # Selo de Elite
                            elite = "👑 **ELITE** | " if prof.get('ranking_elite', 0) > 0 else ""
                            st.markdown(f"### {prof['nome']}")
                            st.markdown(f"{elite}{prof.get('categoria', 'Geral')}")
                            st.write(f"📍 {prof.get('distancia_calc', 0.0)} km de você")
                            st.write(f"📝 {prof.get('descricao', '')[:100]}...")
                        
                        with c3:
                            st.write("\n")
                            # Botão WhatsApp Direto
                            tel = re.sub(r'\D', '', str(prof.get('whatsapp', '')))
                            link_wa = f"https://wa.me/55{tel}?text=Olá%20{prof['nome']},%20vi%20seu%20perfil%20no%20GeralJá!"
                            st.link_button("🟢 WHATSAPP", link_wa, use_container_width=True)
                            
                            # Contador de Visualizações (Soma 1 no banco)
                            if st.button(f"📄 VER PERFIL", key=f"perfil_{prof['id_doc']}"):
                                db.collection("profissionais").document(prof['id_doc']).update({
                                    "visualizacoes": firestore.Increment(1)
                                })
                                st.session_state.perfil_id = prof['id_doc'] # Para abrir detalhado depois
                        
                        st.markdown("---")
            else:
                st.warning("😕 Nenhum profissional encontrado para este termo ainda.")
                
        except Exception as e:
            st.error(f"Erro ao buscar: {e}")
    else:
        # Se não houver busca, mostra sugestões ou banner
        st.info("👋 Digite acima o que você procura para encontrarmos os melhores profissionais perto de você!")
        # ------------------------------------------------------------------------------
# 14. ABA CADASTRAR: FILTRO DE PERFIL E CATEGORIAS ROBUSTAS
# ------------------------------------------------------------------------------
with tabs[1]: # Aba CADASTRAR
    st.header("🚀 Cadastre seu Negócio ou Serviço")
    st.write("Preencha os dados abaixo para aparecer no mapa do GeralJá.")

    # 1. ESCOLHA DO TIPO DE PERFIL
    tipo_cadastro = st.radio(
        "Você é um profissional ou possui um comércio?",
        ["Profissional Liberal (Serviços)", "Comércio / Loja (Produtos)"],
        horizontal=True
    )

    # 2. DEFINIÇÃO DE CATEGORIAS ROBUSTAS (ORDEM ALFABÉTICA)
    categorias_profissionais = sorted([
        "Adestrador", "Babá", "Chaveiro", "Confeiteira", "Costureira", "Cozinheiro", 
        "Diarista", "Eletricista", "Encanador", "Esteticista", "Fisioterapeuta", 
        "Fretes e Mudanças", "Informática / TI", "Jardineiro", "Manicure", 
        "Marceneiro", "Mecânico", "Montador de Móveis", "Motorista", "Pedreiro", 
        "Pintor", "Piscineiro", "Professor Particular", "Técnico de Celular", 
        "Técnico de Geladeira", "Técnico de TV", "Veterinário"
    ])

    categorias_comercio = sorted([
        "Açougue", "Adega", "Armarinho", "Auto Peças", "Barbearia", "Bazar", 
        "Bicicletaria", "Casa de Rações", "Depósito de Material", "Doceria", 
        "Drogaria / Farmácia", "Floricultura", "Hortifruti", "Lanchonete", 
        "Loja de Roupas", "Mercado", "Padaria", "Papelaria", "Perfumaria", 
        "Pet Shop", "Pizzaria", "Restaurante", "Salão de Beleza", "Sorveteria"
    ])

    # 3. FORMULÁRIO DE DADOS
    with st.form("form_cadastro", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        
        with col_a:
            nome_negocio = st.text_input("Nome do Negócio / Profissional*", placeholder="Ex: João Elétrica")
            whatsapp = st.text_input("WhatsApp (com DDD)*", placeholder="11999999999")
            
            # Seleção Dinâmica baseada no Rádio anterior
            if "Profissional" in tipo_cadastro:
                categoria_final = st.selectbox("Sua Especialidade*", categorias_profissionais)
            else:
                categoria_final = st.selectbox("Tipo de Comércio*", categorias_comercio)
        
        with col_b:
            foto_perfil = st.file_uploader("Foto de Perfil ou Logo", type=['png', 'jpg', 'jpeg'])
            descricao = st.text_area("Descrição do Serviço/Produtos*", placeholder="Conte o que você faz...")

        st.write("---")
        st.subheader("📍 Localização do Negócio")
        st.info("Clique no botão abaixo para capturar sua localização atual (onde o serviço é prestado).")
        
        # Captura de Localização no Formulário
        loc_cadastro = get_geolocation()
        lat_cad, lon_cad = None, None
        if loc_cadastro and 'coords' in loc_cadastro:
            lat_cad = loc_cadastro['coords']['latitude']
            lon_cad = loc_cadastro['coords']['longitude']
            st.success(f"📍 GPS Capturado: {lat_cad}, {lon_cad}")

        btn_enviar = st.form_submit_button("FINALIZAR CADASTRO", use_container_width=True)

        if btn_enviar:
            if not nome_negocio or not whatsapp or not lat_cad:
                st.error("⚠️ Por favor, preencha o nome, WhatsApp e capture sua localização!")
            else:
                try:
                    # Converte foto para string
                    foto_b64 = converter_img_b64(foto_perfil)
                    
                    # Salva no Firebase
                    novo_registro = {
                        "nome": nome_negocio,
                        "whatsapp": whatsapp,
                        "categoria": categoria_final,
                        "tipo": "comercio" if "Comércio" in tipo_cadastro else "profissional",
                        "descricao": descricao,
                        "foto": foto_b64,
                        "latitude": lat_cad,
                        "longitude": lon_cad,
                        "status": "ativo",
                        "saldo": 5.0,
                        "ranking_elite": 0,
                        "visualizacoes": 0,
                        "data_cadastro": datetime.datetime.now().strftime("%Y-%m-%d")
                    }
                    
                    db.collection("profissionais").add(novo_registro)
                    st.balloons()
                    st.success("✅ Cadastro realizado com sucesso! Você já está aparecendo nas buscas.")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
                    # ------------------------------------------------------------------------------
# 16. ABA MEU PERFIL: ONDE O MÁGICO ACONTECE
# ------------------------------------------------------------------------------
with tabs[2]: # Aba MEU PERFIL
    st.header("👤 Gerenciar Meu Perfil")
    
    id_acesso = st.text_input("Digite seu WhatsApp para acessar seu painel", type="password")
    
    if id_acesso:
        # Busca o profissional no banco pelo WhatsApp
        profs = db.collection("profissionais").where("whatsapp", "==", id_acesso).limit(1).stream()
        perfil_encontrado = None
        for p in profs:
            perfil_encontrado = p.to_dict()
            id_doc_perfil = p.id
            
        if perfil_encontrado:
            st.success(f"Bem-vindo de volta, {perfil_encontrado['nome']}!")
            
            # --- SEÇÃO RADAR LIVE ---
            st.markdown("---")
            st.subheader("⚡ Lançar Grito no Radar (Oferta Relâmpago)")
            st.write("Sua oferta aparecerá na página inicial por 24 horas.")
            
            msg_radar = st.text_input("O que você quer anunciar?", placeholder="Ex: Promoção de pizza hoje! / Tenho horário livre agora!")
            
            if st.button("🚀 DISPARAR NO RADAR"):
                if msg_radar:
                    if criar_oferta_live(id_doc_perfil, perfil_encontrado['nome'], msg_radar):
                        st.balloons()
                        st.success("Grito lançado! Todos os clientes verão sua oferta na busca.")
                    else:
                        st.error("Erro ao lançar oferta.")
                else:
                    st.warning("Escreva algo para o seu público.")
            
            # --- SEÇÃO FINANCEIRA / ELITE ---
            st.markdown("---")
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                st.metric("Seu Saldo", f"R$ {perfil_encontrado.get('saldo', 0.0):.2f}")
                st.write("O saldo é usado para destacar seu perfil.")
            with col_f2:
                st.metric("Visualizações", perfil_encontrado.get('visualizacoes', 0))
                
            if st.button("💎 ATIVAR RANKING ELITE (R$ 1,00/dia)"):
                if perfil_encontrado.get('saldo', 0) >= 1.0:
                    db.collection("profissionais").document(id_doc_perfil).update({
                        "saldo": firestore.Increment(-1.0),
                        "ranking_elite": 1
                    })
                    st.success("Você agora é ELITE! Seu perfil subiu no ranking.")
                    st.rerun()
                else:
                    st.error("Saldo insuficiente. Chame o Admin para recarregar.")

        else:
            st.error("Profissional não encontrado com esse WhatsApp.")

# ------------------------------------------------------------------------------
# 17. FINALIZAÇÃO DA ABA BUSCAR (INCLUINDO O RADAR)
# ------------------------------------------------------------------------------
# Importante: No seu código, coloque a função mostrar_radar_live() 
# logo no início da Aba BUSCAR (tabs[0]), para ser a primeira coisa que o cliente vê.
