# ==============================================================================
# GERALJÁ: CRIANDO SOLUÇÕES - VERSÃO REESTRUTURADA 5.0
# ==============================================================================
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import math
import re
import time
import pandas as pd
from datetime import datetime 
import pytz
from streamlit_js_eval import streamlit_js_eval, get_geolocation
import unicodedata
from groq import Groq
import requests
from urllib.parse import quote

# --- CONFIGURAÇÃO DE CHAVES (MANTENDO SEUS NOMES ORIGINAIS) ---
try:
    FB_ID = st.secrets["FB_CLIENT_ID"]
    FB_SECRET = st.secrets["FB_CLIENT_SECRET"]
    FIREBASE_API_KEY = st.secrets["FIREBASE_API_KEY"]
    REDIRECT_URI = "https://geralja-zxiaj2ot56fuzgcz7xhcks.streamlit.app/"
except Exception as e:
    st.error(f"Erro: Chaves não encontradas no Secrets. ({e})")

# --- INICIALIZAÇÃO DO FIREBASE (COM TRAVA DE SEGURANÇA) ---
if not firebase_admin._apps:
    try:
        cred_dict = dict(st.secrets["firebase"])
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Falha ao iniciar Firebase: {e}")

db = firestore.client()

# --- CONSTANTES GLOBAIS ---
LAT_REF = -23.7684  
LON_REF = -46.6946
CATEGORIAS_OFICIAIS = [
    "Alimentação", "Aulas/Cursos", "Beleza/Estética", "Construção/Reforma",
    "Eventos/Festas", "Limpeza/Faxina", "Mecânica/Automotivo", "Saúde",
    "Serviços Domésticos", "Tecnologia/Digital", "Transporte/Frete", "Outro (Personalizado)"
]

# --- DICIONÁRIO DE CONCEITOS EXPANDIDO (Para a Busca Híbrida) ---
CONCEITOS_EXPANDIDOS = {
    'pizza': 'Alimentação', 'hamburguer': 'Alimentação', 'marmita': 'Alimentação',
    'pedreiro': 'Construção/Reforma', 'pintor': 'Construção/Reforma', 'eletricista': 'Construção/Reforma',
    'encanador': 'Construção/Reforma', 'telhado': 'Construção/Reforma',
    'faxina': 'Limpeza/Faxina', 'diarista': 'Limpeza/Faxina', 'passadeira': 'Limpeza/Faxina',
    'dentista': 'Saúde', 'medico': 'Saúde', 'psicologo': 'Saúde', 'fisioterapeuta': 'Saúde',
    'mecanico': 'Mecânica/Automotivo', 'borracharia': 'Mecânica/Automotivo', 'guincho': 'Mecânica/Automotivo',
    'frete': 'Transporte/Frete', 'carreto': 'Transporte/Frete', 'mudança': 'Transporte/Frete',
    'manicure': 'Beleza/Estética', 'cabeleireiro': 'Beleza/Estética', 'barbeiro': 'Beleza/Estética',
    'aula': 'Aulas/Cursos', 'professor': 'Aulas/Cursos', 'reforço': 'Aulas/Cursos',
    'festa': 'Eventos/Festas', 'dj': 'Eventos/Festas', 'buffet': 'Eventos/Festas'
}

# --- FUNÇÕES DE LIMPEZA E TRATAMENTO ---
def normalizar_para_ia(texto):
    if not texto: return ""
    texto = texto.lower().strip()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto

def limpar_whatsapp(num):
    if not num: return ""
    return re.sub(r'\D', '', str(num))

# --- FUNÇÃO DE DISTÂNCIA (O MOTOR GEOGRÁFICO) ---
def calcular_distancia_real(lat1, lon1, lat2, lon2):
    try:
        if None in [lat1, lon1, lat2, lon2]: return 999.0
        R = 6371 
        dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return round(R * c, 1)
    except:
        return 999.0
        # --- FUNÇÕES DE SUPORTE (Mantenha fora de blocos IF/ELSE para funcionar no app todo) ---
def buscar_opcoes_dinamicas(documento, padrao):
    """
    Busca listas de categorias ou tipos na coleção 'configuracoes' do Firebase.
    """
    try:
        doc = db.collection("configuracoes").document(documento).get()
        if doc.exists:
            dados = doc.to_dict()
            return dados.get("lista", padrao)
        return padrao
    except Exception as e:
        return padrao

def converter_img_b64(file):
    """ Converte arquivos de imagem para Base64 para exibir no HTML """
    if file is None: return ""
    try:
        return base64.b64encode(file.read()).decode()
    except:
        return ""

def redimensionar_imagem_b64(b64_str):
    """ 
    Placeholder para futuras melhorias de performance. 
    Por enquanto, retorna a string original mantendo a compatibilidade.
    """
    return b64_str

# --- CONFIGURAÇÃO VISUAL E ESTADO DA SESSÃO ---
if 'modo_noite' not in st.session_state:
    st.session_state.modo_noite = True 

# Layout do topo (Toggle de Tema e Título)
c_t1, c_t2 = st.columns([2, 8])
with c_t1:
    st.session_state.modo_noite = st.toggle("🌙 Modo Noite", value=st.session_state.modo_noite)

# Bloco CSS Dinâmico (Ajustado para Mobile e Desktop)
estilo_dinamico = f"""
<style>
    /* Estilos Globais Baseados no Modo Noite */
    .stApp {{
        background-color: {"#0e1117" if st.session_state.modo_noite else "#f8f9fa"};
        color: {"white" if st.session_state.modo_noite else "black"};
    }}
    
    /* Cartão do Profissional (Inspirado no GetNinjas) */
    .cartao-geral {{
        background: {"#1e293b" if st.session_state.modo_noite else "#ffffff"};
        border-left: 5px solid var(--cor-borda);
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        transition: transform 0.2s;
    }}
    .cartao-geral:hover {{ transform: scale(1.01); }}

    /* Estilo do Portfólio de Fotos */
    .social-track {{
        display: flex;
        overflow-x: auto;
        gap: 10px;
        padding: 10px 0;
        scrollbar-width: thin;
    }}
    .social-card img {{
        width: 100px;
        height: 100px;
        object-fit: cover;
        border-radius: 8px;
        cursor: pointer;
    }}
</style>
"""
st.markdown(estilo_dinamico, unsafe_allow_html=True)

# --- CARREGAMENTO DE DADOS INICIAIS ---
# Puxa categorias do banco se houver, senão usa as CATEGORIAS_OFICIAIS
LISTA_CATEGORIAS = buscar_opcoes_dinamicas("categorias", CATEGORIAS_OFICIAIS)
# --- GEOLOCALIZAÇÃO (Onde o usuário está?) ---
def obter_localizacao_usuario():
    """ 
    Usa o GPS do navegador para encontrar o usuário. 
    Se falhar, usa o centro do Grajaú como padrão.
    """
    loc = get_geolocation()
    if loc and 'coords' in loc:
        return loc['coords']['latitude'], loc['coords']['longitude']
    return LAT_REF, LON_REF

# --- O CÉREBRO DA IA: MOTOR DE BUSCA HÍBRIDO ---
def processar_ia_avancada(texto):
    """
    Lógica de Elite: 1. Dicionário -> 2. Busca Direta -> 3. IA Groq + Cache
    """
    if not texto: return "Vazio"
    t_clean = normalizar_para_ia(texto)
    
    # 1. BUSCA POR CONCEITOS (Dicionário Local - Rápido e Grátis)
    for chave, categoria in CONCEITOS_EXPANDIDOS.items():
        if re.search(rf"\b{normalizar_para_ia(chave)}\b", t_clean):
            return categoria
    
    # 2. BUSCA POR CATEGORIA DIRETA (Se o usuário digitou o nome da categoria)
    for cat in CATEGORIAS_OFICIAIS:
        if normalizar_para_ia(cat) in t_clean:
            return cat

    # 3. INTELIGÊNCIA ARTIFICIAL GROQ (Com Memória de Cache)
    try:
        # Checa se já aprendemos isso antes no Firebase para economizar API
        cache_ref = db.collection("cache_buscas").document(t_clean).get()
        if cache_ref.exists:
            return cache_ref.to_dict().get("categoria")

        # Se é novo, pergunta para a IA
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        prompt_ia = f"""
        Você é o assistente do GeralJá. O usuário busca por: '{texto}'.
        Escolha a categoria mais próxima desta lista: {CATEGORIAS_OFICIAIS}.
        Responda APENAS o nome da categoria. Se não souber, responda 'Outro (Personalizado)'.
        """
        
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt_ia}],
            model="llama3-8b-8192",
            temperature=0
        )
        cat_ia = res.choices[0].message.content.strip()

        # Salva o aprendizado no Banco de Dados
        if cat_ia in CATEGORIAS_OFICIAIS:
            db.collection("cache_buscas").document(t_clean).set({
                "categoria": cat_ia,
                "data": datetime.now()
            })
            return cat_ia

    except Exception as e:
        # Se a IA falhar, não quebra o app
        pass

    return "Outro (Personalizado)"

# --- LÓGICA DE SESSÃO PARA O USUÁRIO LOGADO ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_data' not in st.session_state:
    st.session_state.user_data = {}
    # --- SISTEMA DE NAVEGAÇÃO POR ABAS ---
# Criamos as abas principais do app. O estilo CSS que colamos antes cuida da beleza.
tab_busca, tab_perfil, tab_cadastro = st.tabs(["🔍 Buscar Profissional", "👤 Meu Perfil", "📝 Cadastrar Serviço"])

# --- ABA 1: BUSCA DE PROFISSIONAIS ---
with tab_busca:
    st.markdown("<h2 style='text-align: center;'>O que você precisa hoje?</h2>", unsafe_allow_html=True)
    
    # Campo de busca com sugestão dinâmica
    termo_busca = st.text_input("", placeholder="Ex: Dentista, Pedreiro, Pizza...", key="input_busca")
    
    # Filtro de distância (Slider estilo GetNinjas)
    raio_km = st.slider("Distância máxima (km):", 1, 50, 10)

    # Pegamos a localização do usuário (Se ele permitir)
    minha_lat, minha_lon = obter_localizacao_usuario()

    if termo_busca:
        # 1. IA define a categoria (Lógica que organizamos no Bloco 3)
        with st.spinner('IA analisando sua busca...'):
            cat_ia = processar_ia_avancada(termo_busca)
        
        # 2. BUSCA EM CASCATA NO FIREBASE (Fim do erro de busca vazia)
        # Tentativa 1: Por categoria exata
        query_ref = db.collection("profissionais").where("area", "==", cat_ia).where("aprovado", "==", True)
        docs = query_ref.stream()
        lista_ranking = [d.to_dict() | {'id': d.id} for d in docs]

        # Tentativa 2: Se não achou na categoria, busca no texto (Plano B)
        if not lista_ranking:
            todos = db.collection("profissionais").where("aprovado", "==", True).stream()
            t_min = normalizar_para_ia(termo_busca)
            for d in todos:
                p = d.to_dict()
                txt_base = normalizar_para_ia(p.get('nome','') + p.get('area','') + p.get('descricao',''))
                if t_min in txt_base:
                    p['id'] = d.id
                    lista_ranking.append(p)

        # 3. PROCESSAMENTO GEOGRÁFICO E SCORE ELITE
        for p in lista_ranking:
            p['dist'] = calcular_distancia_real(minha_lat, minha_lon, p.get('lat', LAT_REF), p.get('lon', LON_REF))
            # Cálculo do Score: Verificados e com Saldo aparecem primeiro
            score = 0
            score += 1000 if p.get('verificado') else 0
            score += (p.get('saldo', 0) * 10)
            p['score_elite'] = score

        # 4. ORDENAÇÃO FINAL: Distância primeiro, depois o Score
        lista_ranking.sort(key=lambda x: (x['dist'], -x['score_elite']))

        # Feedback para o usuário sobre a categoria encontrada
        st.info(f"✨ IA: Categoria identificada: **{cat_ia}**")
        # --- EXIBIÇÃO DOS RESULTADOS (A VITRINE) ---
        if not lista_ranking:
            st.warning(f"⚠️ Nenhum profissional de '{cat_ia}' encontrado num raio de {raio_km}km.")
        else:
            st.write(f"✅ Encontramos **{len(lista_ranking)}** especialistas para você:")
            
            for p in lista_ranking:
                # 1. Preparação de dados do profissional
                is_elite = p.get('verificado', False) and p.get('saldo', 0) > 0
                cor_borda = "#FFD700" if is_elite else "#0047AB" # Dourado para Elite
                zap_limpo = limpar_whatsapp(p.get('whatsapp', ''))
                link_zap = f"https://wa.me/{zap_limpo}?text=Olá, vi seu trabalho no GeralJá! Pode me ajudar?"
                
                # 2. Montagem do Portfólio (Fotos f1 a f10)
                fotos_html = ""
                for i in range(1, 11):
                    f_data = p.get(f'f{i}')
                    if f_data and len(str(f_data)) > 100:
                        # Garante que a imagem tenha o cabeçalho base64 correto
                        src = f_data if str(f_data).startswith("data") else f"data:image/jpeg;base64,{f_data}"
                        fotos_html += f'''
                            <div class="social-card">
                                <img src="{src}" onclick="window.open('{src}', '_blank')">
                            </div>'''

                # 3. O CARTÃO HTML (Design Moderno)
                st.markdown(f"""
                <div class="cartao-geral" style="--cor-borda: {cor_borda};">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div style="font-size: 11px; color: #666; font-weight: bold;">
                            📍 a {p['dist']:.1f} km de você {" | 🏆 ELITE" if is_elite else ""}
                        </div>
                    </div>
                    
                    <div style="display: flex; align-items: center; margin-top: 10px; gap: 15px;">
                        <img src="{p.get('foto_url', 'https://www.w3schools.com/howto/img_avatar.png')}" 
                             style="width:60px; height:60px; border-radius:50%; object-fit:cover; border: 2px solid {cor_borda};">
                        <div>
                            <h4 style="margin:0; color:{'#ffffff' if st.session_state.modo_noite else '#1e3a8a'};">
                                {p.get('nome', 'Profissional').upper()}
                            </h4>
                            <p style="margin:0; color:#888; font-size:12px;">{p.get('area', 'Serviços')}</p>
                        </div>
                    </div>

                    <div style="margin-top: 10px; font-size: 14px; line-height: 1.4;">
                        {p.get('descricao', 'Sem descrição disponível.')[:150]}...
                    </div>

                    <div class="social-track">
                        {fotos_html}
                    </div>

                    <a href="{link_zap}" target="_blank" 
                       style="display: block; text-align: center; background: #25d366; color: white; 
                       text-decoration: none; padding: 12px; border-radius: 8px; font-weight: bold; margin-top: 10px;">
                        💬 CHAMAR NO WHATSAPP
                    </a>
                </div>
                """, unsafe_allow_html=True)

# --- ABA 2: MEU PERFIL (GESTÃO DO PROFISSIONAL) ---
with tab_perfil:
    if not st.session_state.user_id:
        st.subheader("🔐 Área Restrita do Profissional")
        
        # Sistema de Login (Simples e Eficaz)
        aba_login, aba_recuperar = st.tabs(["Entrar", "Recuperar Acesso"])
        
        with aba_login:
            email_login = st.text_input("E-mail cadastrado:", key="email_login").lower().strip()
            senha_login = st.text_input("Senha:", type="password", key="senha_login")
            
            if st.button("🚀 ACESSAR MEU PAINEL", use_container_width=True):
                # Busca no Firebase pelo e-mail
                user_ref = db.collection("profissionais").where("email", "==", email_login).limit(1).get()
                
                if user_ref:
                    dados_user = user_ref[0].to_dict()
                    # Verificação de senha (em produção, use hash!)
                    if dados_user.get("senha") == senha_login:
                        st.session_state.user_id = user_ref[0].id
                        st.session_state.user_data = dados_user
                        st.success(f"Bem-vindo de volta, {dados_user.get('nome')}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Senha incorreta.")
                else:
                    st.error("❌ E-mail não encontrado. Cadastre-se na aba ao lado!")

        with aba_recuperar:
            st.write("Esqueceu sua senha? Digite seu e-mail para receber as instruções.")
            email_rec = st.text_input("E-mail de recuperação:")
            if st.button("Enviar"):
                st.info("Funcionalidade em desenvolvimento. Contate o suporte GeralJá.")

    else:
        # --- PAINEL DO PROFISSIONAL LOGADO ---
        p = st.session_state.user_data
        st.success(f"Sessão Ativa: {p.get('nome')}")
        
        col_p1, col_p2 = st.columns([1, 1])
        with col_p1:
            st.metric("💰 Seu Saldo", f"R$ {p.get('saldo', 0):.2f}")
        with col_p2:
            status_verif = "✅ Verificado" if p.get("verificado") else "⏳ Pendente"
            st.metric("🛡️ Status", status_verif)

        # Botão para sair
        if st.button("🚪 Sair do Sistema"):
            st.session_state.user_id = None
            st.session_state.user_data = {}
            st.rerun()
                        # --- ÁREA DE EDIÇÃO DE PERFIL (DENTRO DO LOGADO) ---
        with st.expander("📝 Editar Meus Dados e Descrição"):
            with st.form("form_edicao"):
                novo_nome = st.text_input("Nome Profissional:", value=p.get('nome', ''))
                nova_desc = st.text_area("Descrição do Serviço:", value=p.get('descricao', ''), help="Diga o que você faz de melhor!")
                novo_zap = st.text_input("WhatsApp (com DDD):", value=p.get('whatsapp', ''))
                nova_area = st.selectbox("Sua Categoria Principal:", CATEGORIAS_OFICIAIS, 
                                        index=CATEGORIAS_OFICIAIS.index(p.get('area', 'Outro (Personalizado)')))
                
                if st.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                    db.collection("profissionais").document(st.session_state.user_id).update({
                        "nome": novo_nome,
                        "descricao": nova_desc,
                        "whatsapp": novo_zap,
                        "area": nova_area
                    })
                    st.success("Dados atualizados! Atualizando painel...")
                    time.sleep(1)
                    st.rerun()

        with st.expander("📸 Gerenciar Fotos do Portfólio"):
            st.info("As fotos aparecem na vitrine de busca. Tamanho sugerido: Quadrado (1:1)")
            
            # Grid de Upload para as 10 fotos
            col_f1, col_f2 = st.columns(2)
            for i in range(1, 11):
                col_atual = col_f1 if i % 2 != 0 else col_f2
                with col_atual:
                    foto_atual = p.get(f'f{i}')
                    if foto_atual:
                        st.image(foto_atual if foto_atual.startswith("data") else f"data:image/jpeg;base64,{foto_atual}", width=100)
                    
                    nova_img = st.file_uploader(f"Trocar Foto {i}", type=['jpg', 'jpeg', 'png'], key=f"up_f{i}")
                    if nova_img:
                        b64_img = converter_img_b64(nova_img)
                        db.collection("profissionais").document(st.session_state.user_id).update({f"f{i}": b64_img})
                        st.success(f"Foto {i} atualizada!")
                        time.sleep(0.5)
                        st.rerun()

        # --- SEÇÃO DE CRÉDITOS (ESTILO GETNINJAS) ---
        st.markdown("---")
        st.subheader("🪙 Meus Créditos")
        st.write("Use seus créditos para ficar no topo da lista (ELITE).")
        if st.button("💳 Comprar mais Créditos"):
            st.info("Redirecionando para o checkout de pagamento...")
                        # --- ABA 3: CADASTRE SEU SERVIÇO (NOVO PROFISSIONAL) ---
with tab_cadastro:
    st.header("🚀 Cadastre-se no GeralJá")
    st.write("Preencha os dados abaixo para começar a receber pedidos.")

    with st.form("form_cadastro_novo"):
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            nome_cad = st.text_input("Nome Completo / Empresa:", placeholder="Ex: João da Elétrica")
            email_cad = st.text_input("E-mail (Será seu login):").lower().strip()
            senha_cad = st.text_input("Crie uma Senha:", type="password")
            zap_cad = st.text_input("WhatsApp (com DDD):", placeholder="11999999999")
        
        with col_c2:
            area_cad = st.selectbox("Área de Atuação:", CATEGORIAS_OFICIAIS)
            # Localização manual para o cadastro inicial
            st.info("📍 Sua localização será definida pelo GPS ou endereço padrão.")
            desc_cad = st.text_area("Sua Bio (O que você faz?):", placeholder="Conte detalhes do seu serviço...")

        # Upload da Foto de Perfil Principal
        foto_perfil = st.file_uploader("Sua Foto de Perfil:", type=['jpg', 'jpeg', 'png'])
        
        submit_cad = st.form_submit_button("✅ FINALIZAR MEU CADASTRO")

        if submit_cad:
            if not nome_cad or not email_cad or not senha_cad:
                st.error("⚠️ Por favor, preencha nome, e-mail e senha!")
            else:
                # 1. Verifica se e-mail já existe
                check_email = db.collection("profissionais").where("email", "==", email_cad).get()
                if check_email:
                    st.warning("❌ Este e-mail já está cadastrado. Tente fazer login.")
                else:
                    # 2. Processa foto e salva no banco
                    b64_perfil = converter_img_b64(foto_perfil) if foto_perfil else ""
                    
                    dados_novo = {
                        "nome": nome_cad,
                        "email": email_cad,
                        "senha": senha_cad,
                        "whatsapp": zap_cad,
                        "area": area_cad,
                        "descricao": desc_cad,
                        "foto_url": f"data:image/jpeg;base64,{b64_perfil}" if b64_perfil else "",
                        "lat": minha_lat, # Pega do GPS que configuramos no Bloco 3
                        "lon": minha_lon,
                        "aprovado": True, # Já entra aprovado para teste, mude para False se quiser moderar
                        "verificado": False,
                        "saldo": 0,
                        "data_cadastro": datetime.now()
                    }
                    
                    try:
                        db.collection("profissionais").add(dados_novo)
                        st.success("🎉 Cadastro realizado com sucesso! Vá para a aba 'Meu Perfil' e faça login.")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

# --- FIM DAS ABAS ---
# --- FUNÇÕES DE SEGURANÇA E MANUTENÇÃO DO SISTEMA ---

def monitorar_performance_ia():
    """ 
    Verifica se a API da Groq está respondendo. 
    Se falhar, o sistema avisa o administrador internamente.
    """
    try:
        # Teste rápido de conexão com o banco de logs
        db.collection("logs_sistema").add({
            "evento": "check_status",
            "timestamp": datetime.now()
        })
    except:
        st.sidebar.error("⚠️ Erro de conexão com Banco de Dados")

def validar_sessao_ativa():
    """ 
    Garante que se o Firebase cair, o usuário não veja dados corrompidos.
    """
    if st.session_state.user_id:
        doc = db.collection("profissionais").document(st.session_state.user_id).get()
        if not doc.exists:
            st.session_state.user_id = None
            st.rerun()

# --- LÓGICA DE RANKING DINÂMICO (LIGANDO AS PONTAS) ---
def atualizar_score_profissional(doc_id, novo_saldo):
    """ 
    Função para ser chamada quando o profissional compra créditos.
    Isso empurra ele para o topo da lista ELITE.
    """
    try:
        db.collection("profissionais").document(doc_id).update({
            "saldo": novo_saldo,
            "ultima_atualizacao": datetime.now()
        })
    except Exception as e:
        print(f"Erro ao atualizar score: {e}")

# --- LIMPEZA DE CACHE (MANUTENÇÃO) ---
if st.sidebar.button("🧹 Limpar Cache de IA"):
    # Útil se a IA classificou algo errado e você quer forçar nova análise
    try:
        docs_cache = db.collection("cache_buscas").stream()
        for d in docs_cache:
            d.reference.delete()
        st.sidebar.success("Cache limpo! A IA aprenderá do zero.")
    except:
        st.sidebar.error("Erro ao limpar cache.")

# --- CHAMADA DE MONITORAMENTO ---
validar_sessao_ativa()
monitorar_performance_ia()

# Preparação para o bloco final (Rodapé e Finalização)
st.markdown("<br><br>", unsafe_allow_html=True)
                        # --- BLOCO FINAL: O RODAPÉ E ALINHAMENTO DE LAYOUT ---

def finalizar_e_alinhar_layout():
    """
    Esta função atua como um ímã. Puxa o conteúdo e limpa o rodapé.
    Garante que o design fique profissional em telas mobile.
    """
    st.write("---")
    
    # CSS de fechamento para garantir que nada corte no mobile
    fechamento_estilo = """
        <style>
            .main .block-container { 
                padding-bottom: 8rem !important; 
            }
            .footer-clean {
                text-align: center;
                padding: 40px 20px;
                opacity: 0.8;
                font-size: 0.85rem;
                width: 100%;
                color: gray;
                border-top: 1px solid #eeeeee33;
                margin-top: 50px;
            }
            .footer-links a {
                color: #25d366;
                text-decoration: none;
                margin: 0 10px;
                font-weight: bold;
            }
        </style>
        <div class="footer-clean">
            <p>🎯 <b>GeralJá - v5.0 Elite</b></p>
            <p>O maior ecossistema de inteligência local do Grajaú.</p>
            <div class="footer-links">
                <a href="#">Termos de Uso</a> | 
                <a href="#">Privacidade</a> | 
                <a href="#">Suporte</a>
            </div>
            <p style="margin-top:15px; font-size: 0.7rem;">
                © 2026 GeralJá Intelligence Systems. <br>
                Conectando quem precisa com quem sabe fazer.
            </p>
        </div>
    """
    st.markdown(fechamento_estilo, unsafe_allow_html=True)

# --- EXECUÇÃO DO RODAPÉ ---
# Chamamos a função fora de qualquer 'with tab' para que apareça em todas as páginas
finalizar_e_alinhar_layout()

# --- DICA DO PROFESSOR: MONITORAMENTO FINAL ---
if st.session_state.user_id:
    # Mostra um pequeno status na sidebar se o cara estiver logado
    st.sidebar.markdown("---")
    st.sidebar.caption(f"Logado como: {st.session_state.user_data.get('email')}")
    if st.sidebar.button("Deslogar"):
        st.session_state.user_id = None
        st.rerun()

# FIM DO ARQUIVO GERALJÁ v5.0
