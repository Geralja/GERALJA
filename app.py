import streamlit as st
import pandas as pd
from datetime import datetime
from urllib.parse import quote
import unicodedata
import difflib
import base64
from io import BytesIO
from PIL import Image
from google.cloud import firestore

# ==============================================================================
# 1. CONFIGURAÇÕES INICIAIS E CONSTANTES
# ==============================================================================
st.set_page_config(
    page_title="GeralJá - Serviços no Grajaú",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

PIX_OFICIAL = "11980168513"
ZAP_ADMIN = "5511980168513"
CHAVE_ADMIN = "grajautem2026"
LAT_REF = -23.7542  # Coordenada base do Grajaú
LON_REF = -46.6908

CATEGORIAS_OFICIAIS = [
    "Eletricista", "Encanador", "Pintor", "Pedreiro",
    "Mecânico", "Diarista", "Cabeleireiro/Barbeiro",
    "Manicure", "Técnico de Informática", "Frete e Mudanças"
]

# ==============================================================================
# 2. CONEXÃO COM O BANCO DE DADOS (FIRESTORE)
# ==============================================================================
@st.cache_resource
def iniciar_banco():
    try:
        return firestore.Client()
    except Exception:
        st.warning("⚠️ Firestore não conectado. Verifique suas credenciais de ambiente.")
        return None

db = iniciar_banco()

# ==============================================================================
# 3. FUNÇÕES AUXILIARES DE SUPORTE
# ==============================================================================
def limpar_whatsapp(numero: str) -> str:
    """Remove caracteres não numéricos do telefone."""
    if not numero:
        return ""
    return "".join(filter(str.isdigit, str(numero)))

def normalizar_texto(texto: str) -> str:
    """Remove acentos e converte para minúsculas para buscas eficientes."""
    if not texto:
        return ""
    nfkd = unicodedata.normalize('NFD', texto)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower()

def otimizar_e_converter_b64(uploaded_file, max_largura=500, qualidade=75) -> str:
    """Otimiza o tamanho da imagem e converte para Base64."""
    try:
        img = Image.open(uploaded_file)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        
        ratio = max_largura / float(img.size[0])
        if ratio < 1.0:
            altura = int((float(img.size[1]) * float(ratio)))
            img = img.resize((max_largura, altura), Image.Resampling.LANCZOS)
            
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=qualidade, optimize=True)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/jpeg;base64,{img_str}"
    except Exception as e:
        st.error(f"Erro ao processar imagem: {e}")
        return ""

def obter_coords_google(endereco: str):
    """Simulação de geocodificação padrão para o Grajaú."""
    if not endereco:
        return LAT_REF, LON_REF, "Grajaú, São Paulo - SP"
    return LAT_REF, LON_REF, f"{endereco}, Grajaú, São Paulo - SP"

def buscar_opcoes_dinamicas(colecao: str, padrao: list) -> list:
    """Busca categorias ou opções personalizadas salvas no Firestore."""
    if not db:
        return padrao
    try:
        doc = db.collection("configuracoes").document(colecao).get()
        if doc.exists and "lista" in doc.to_dict():
            return doc.to_dict()["lista"]
    except Exception:
        pass
    return padrao

def finalizar_e_alinhar_layout():
    """Renderiza o rodapé institucional do portal."""
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #666; padding: 20px 0;">
            <p><b>GeralJá - Conectando Moradores e Profissionais no Grajaú</b></p>
            <p>© 2026 Grajaú Tem - A maior vitrine da região</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# ==============================================================================
# 4. GERENCIAMENTO DE SESSÃO
# ==============================================================================
if "auth" not in st.session_state:
    st.session_state.auth = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None

# Leitura de parâmetros de URL (ex: ?cmd=abracadabra)
comando = st.query_params.get("cmd", "")

# ==============================================================================
# 5. ESTRUTURA DE NAVEGAÇÃO DAS ABAS
# ==============================================================================
titulos_abas = [
    "🔍 Buscar Serviços",
    "📝 Cadastro / Login",
    "👤 Perfil & Pagamentos",
    "👑 Admin Master",
    "⭐ Feedback"
]

if comando == "abracadabra":
    titulos_abas.append("📊 Financeiro")

menu_abas = st.tabs(titulos_abas)

# ==============================================================================
# ABA 1: BUSCAR SERVIÇOS (MORADOR)
# ==============================================================================
with menu_abas[0]:
    st.title("🛠️ Serviços no Grajaú")
    st.caption("Encontre profissionais verificados pertinho de você")

    col_busca1, col_busca2 = st.columns([2, 1])
    termo_busca = col_busca1.text_input("O que você precisa?", placeholder="Ex: Eletricista, Encanador, Pintor...")
    cat_selecionada = col_busca2.selectbox("Filtrar Categoria", ["Todas"] + sorted(buscar_opcoes_dinamicas("categorias", CATEGORIAS_OFICIAIS)))

    st.markdown("---")

    if db:
        query = db.collection("profissionais").where("aprovado", "==", True)
        
        if cat_selecionada != "Todas":
            query = query.where("area", "==", cat_selecionada)
            
        resultados = list(query.stream())

        # Filtragem por texto tolerante
        if termo_busca:
            termo_norm = normalizar_texto(termo_busca)
            filtrados = []
            for doc in resultados:
                dados = doc.to_dict()
                nome_n = normalizar_texto(dados.get("nome", ""))
                desc_n = normalizar_texto(dados.get("descricao", ""))
                area_n = normalizar_texto(dados.get("area", ""))
                
                if (termo_norm in nome_n) or (termo_norm in desc_n) or (termo_norm in area_n):
                    filtrados.append(doc)
                else:
                    match_ratio = difflib.SequenceMatcher(None, termo_norm, area_n).ratio()
                    if match_ratio > 0.6:
                        filtrados.append(doc)
            resultados = filtrados

        if not resultados:
            st.info("Nenhum profissional encontrado para esta busca no momento.")
        else:
            for doc in resultados:
                p = doc.to_dict()
                p_id = doc.id
                
                with st.container():
                    c_img, c_info, c_acao = st.columns([1, 2.5, 1.5])
                    
                    with c_img:
                        imgs = p.get("portfolio_imgs", [])
                        if imgs:
                            st.image(imgs[0], use_container_width=True)
                        else:
                            st.image("https://via.placeholder.com/150?text=GeralJá", use_container_width=True)

                    with c_info:
                        selo = "☑️ *Verificado*" if p.get("verificado") else ""
                        st.markdown(f"### {p.get('nome')} {selo}")
                        st.markdown(f"**Área:** {p.get('area')}")
                        st.write(p.get("descricao", "Sem descrição disponível."))
                        st.caption(f"📍 {p.get('endereco_digitado', 'Grajaú, SP')}")

                    with c_acao:
                        st.write(f"👁️ {p.get('cliques', 0)} visualizações")
                        msg_zap = quote(f"Olá {p.get('nome')}, vi seu anúncio no GeralJá e gostaria de um orçamento!")
                        link_zap = f"https://api.whatsapp.com/send?phone=55{p_id}&text={msg_zap}"
                        
                        if st.link_button("📲 Chamar no WhatsApp", link_zap, use_container_width=True):
                            db.collection("profissionais").document(p_id).update({"cliques": firestore.Increment(1)})

                    st.markdown("---")

# ==============================================================================
# ABA 2: CADASTRO DE PROFISSIONAIS & LOGIN
# ==============================================================================
with menu_abas[1]:
    st.title("📝 Área do Profissional")

    t_login, t_cad = st.tabs(["🔑 Já tenho conta (Entrar)", "🚀 Cadastrar Meu Negócio"])

    with t_login:
        st.subheader("Acessar seu Painel")
        zap_login = st.text_input("Seu WhatsApp cadastrado (somente números com DDD)", placeholder="Ex: 11991853488")
        
        if st.button("ENTRAR NO PAINEL", use_container_width=True):
            zap_limpo = limpar_whatsapp(zap_login)
            if db:
                doc = db.collection("profissionais").document(zap_limpo).get()
                if doc.exists:
                    st.session_state.auth = True
                    st.session_state.user_id = zap_limpo
                    st.success("Login efetuado com sucesso!")
                    st.rerun()
                else:
                    st.error("WhatsApp não cadastrado. Faça seu cadastro na aba ao lado.")

    with t_cad:
        st.subheader("Crie sua conta no GeralJá")
        with st.form("form_cadastro"):
            c_nome = st.text_input("Seu Nome Profissional / Nome da Empresa")
            c_zap = st.text_input("WhatsApp para Contato (com DDD)", placeholder="11991853488")
            c_area = st.selectbox("Área de Atuação principal", sorted(buscar_opcoes_dinamicas("categorias", CATEGORIAS_OFICIAIS)))
            c_end = st.text_input("Endereço / Bairro no Grajaú", placeholder="Ex: R. Belmira Marin, 1000 - Grajaú")
            c_desc = st.text_area("Descreva seus serviços e diferenciais")

            btn_cadastrar = st.form_submit_button("🚀 FINALIZAR CADASTRO", use_container_width=True)

            if btn_cadastrar:
                zap_f = limpar_whatsapp(c_zap)
                if not c_nome or not zap_f or len(zap_f) < 10:
                    st.error("Preencha o nome e um WhatsApp válido com DDD!")
                elif db:
                    ref = db.collection("profissionais").document(zap_f)
                    if ref.get().exists:
                        st.warning("Este WhatsApp já está cadastrado. Faça login!")
                    else:
                        lat, lon, end_oficial = obter_coords_google(c_end)
                        ref.set({
                            "nome": c_nome,
                            "area": c_area,
                            "descricao": c_desc,
                            "endereco_digitado": c_end,
                            "endereco_oficial": end_oficial,
                            "lat": lat,
                            "lon": lon,
                            "saldo": 5,  # Bônus inicial de 5 moedas
                            "aprovado": True,
                            "verificado": False,
                            "cliques": 0,
                            "portfolio_imgs": [],
                            "data_cadastro": datetime.now().strftime("%d/%m/%Y %H:%M")
                        })
                        st.session_state.auth = True
                        st.session_state.user_id = zap_f
                        st.success("🎉 Cadastro realizado! Você ganhou 5 moedas de bônus.")
                        st.rerun()

# ==============================================================================
# ABA 3: PERFIL & RECARGA DE MOEDAS
# ==============================================================================
with menu_abas[2]:
    if not st.session_state.auth or not st.session_state.user_id:
        st.warning("🔒 Faça login ou cadastre-se na aba 'Cadastro / Login' para acessar o seu perfil.")
    elif db:
        doc_ref = db.collection("profissionais").document(st.session_state.user_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            st.error("Perfil não encontrado.")
            st.session_state.auth = False
            st.session_state.user_id = None
        else:
            d = doc.to_dict()
            st.title(f"👋 Olá, {d.get('nome')}!")
            
            # PAINEL DE SALDO DE MOEDAS
            col_m1, col_m2 = st.columns([1, 2])
            with col_m1:
                st.metric("Seu Saldo Atual", f"{d.get('saldo', 0)} 🪙")
            
            with col_m2:
                st.write("**Gaste moedas para ter destaque ou renovar anúncios.**")
                st.caption("Compre mais moedas diretamente via PIX com ativação rápida.")

            # COMPRA DE PACOTES DE MOEDAS
            with st.expander("💳 COMPRAR MOEDAS VIA PIX", expanded=True):
                t_pix, t_stripe = st.tabs(["⚡ Pagamento PIX (Rápido)", "💳 Cartão de Crédito"])
                
                with t_pix:
                    st.warning(f"Chave PIX Oficial (Celular/CNPJ): `{PIX_OFICIAL}`")
                    c1, c2, c3 = st.columns(3)
                    
                    with c1:
                        st.markdown("##### 🪙 10 Moedas")
                        st.write("**R$ 10,00**")
                        msg_pix10 = quote(f"Olá! Fiz um PIX de R$ 10,00 para recarregar 10 moedas no GeralJá. Meu ID/WhatsApp: {st.session_state.user_id}")
                        st.link_button("📲 Enviar Comprovante", f"https://api.whatsapp.com/send?phone={ZAP_ADMIN}&text={msg_pix10}", use_container_width=True)
                    
                    with c2:
                        st.markdown("##### 🪙 50 Moedas")
                        st.write("**R$ 45,00** *(Com Desconto)*")
                        msg_pix50 = quote(f"Olá! Fiz um PIX de R$ 45,00 para recarregar 50 moedas no GeralJá. Meu ID/WhatsApp: {st.session_state.user_id}")
                        st.link_button("📲 Enviar Comprovante", f"https://api.whatsapp.com/send?phone={ZAP_ADMIN}&text={msg_pix50}", use_container_width=True)
                    
                    with c3:
                        st.markdown("##### 🪙 100 Moedas")
                        st.write("**R$ 80,00** *(Melhor Valor)*")
                        msg_pix100 = quote(f"Olá! Fiz um PIX de R$ 80,00 para recarregar 100 moedas no GeralJá. Meu ID/WhatsApp: {st.session_state.user_id}")
                        st.link_button("📲 Enviar Comprovante", f"https://api.whatsapp.com/send?phone={ZAP_ADMIN}&text={msg_pix100}", use_container_width=True)

                with t_stripe:
                    st.info("Para pagamentos no cartão de crédito, solicite o link direto pelo suporte do WhatsApp.")

            st.divider()

            # EDIÇÃO DE DADOS E PORTFÓLIO DE FOTOS
            with st.expander("✏️ EDITAR PERFIL E GALERIA DE FOTOS", expanded=False):
                with st.form("form_edicao_perfil"):
                    e_nome = st.text_input("Nome Profissional", value=d.get("nome", ""))
                    e_area = st.selectbox("Área de Atuação", sorted(buscar_opcoes_dinamicas("categorias", CATEGORIAS_OFICIAIS)), index=0 if d.get("area") not in CATEGORIAS_OFICIAIS else sorted(buscar_opcoes_dinamicas("categorias", CATEGORIAS_OFICIAIS)).index(d.get("area")))
                    e_desc = st.text_area("Descrição do Serviço", value=d.get("descricao", ""))
                    e_end = st.text_input("Endereço", value=d.get("endereco_digitado", ""))
                    
                    st.markdown("---")
                    st.write("📸 **Adicionar Fotos ao Portfólio/Vitrine (Até 6 fotos)**")
                    fotos_novas = st.file_uploader("Selecione imagens do seu trabalho", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
                    
                    btn_salvar_edicao = st.form_submit_button("💾 SALVAR ALTERAÇÕES", use_container_width=True)

                    if btn_salvar_edicao:
                        novas_imgs_b64 = d.get("portfolio_imgs", [])
                        
                        if fotos_novas:
                            novas_imgs_b64 = []
                            for f in fotos_novas[:6]:
                                b64 = otimizar_e_converter_b64(f, max_largura=500, qualidade=75)
                                if b64:
                                    novas_imgs_b64.append(b64)

                        lat_alt, lon_alt, end_alt = d.get("lat", LAT_REF), d.get("lon", LON_REF), e_end
                        if e_end and e_end != d.get("endereco_digitado"):
                            glat, glon, gend = obter_coords_google(e_end)
                            if glat and glon:
                                lat_alt, lon_alt, end_alt = glat, glon, gend

                        doc_ref.update({
                            "nome": e_nome,
                            "area": e_area,
                            "descricao": e_desc,
                            "endereco_digitado": e_end,
                            "endereco_oficial": end_alt,
                            "lat": lat_alt,
                            "lon": lon_alt,
                            "portfolio_imgs": novas_imgs_b64
                        })
                        st.success("✅ Perfil atualizado com sucesso!")
                        st.rerun()

            if st.button("🔴 SAIR DA CONTA", use_container_width=True):
                st.session_state.auth = False
                st.session_state.user_id = None
                st.rerun()

# ==============================================================================
# ABA 4: ADMINISTRAÇÃO MASTER
# ==============================================================================
with menu_abas[3]:
    st.markdown("### 👑 Painel do Administrador GeralJá")
    
    senha_adm = st.text_input("Digite a chave de acesso MÁSTER", type="password", key="adm_pass")
    
    if senha_adm == CHAVE_ADMIN:
        st.success("🔑 Acesso administrativo concedido!")
        
        tab_adm1, tab_adm2, tab_adm3 = st.tabs(["👥 Gerenciar Parceiros", "➕ Injetar Moedas", "⚙️ Categorias"])

        with tab_adm1:
            st.subheader("Lista de Profissionais Cadastrados")
            if db:
                todos_profs = list(db.collection("profissionais").stream())
                
                for doc in todos_profs:
                    p = doc.to_dict()
                    p_id = doc.id
                    
                    with st.expander(f"{'✅' if p.get('aprovado') else '⏳'} {p.get('nome')} ({p.get('area')}) - WhatsApp: {p_id}"):
                        st.write(f"**Saldo Atual:** {p.get('saldo', 0)} moedas")
                        st.write(f"**Verificado:** {'Sim ☑️' if p.get('verificado') else 'Não ❌'}")
                        st.write(f"**Visitas:** {p.get('cliques', 0)}")
                        st.write(f"**Descrição:** {p.get('descricao', '')}")
                        
                        col_b1, col_b2, col_b3 = st.columns(3)
                        
                        if col_b1.button(f"{'Desativar' if p.get('aprovado') else 'Aprovar'}##{p_id}"):
                            db.collection("profissionais").document(p_id).update({"aprovado": not p.get('aprovado')})
                            st.rerun()

                        if col_b2.button(f"{'Remover Selo' if p.get('verificado') else 'Dar Selo ☑️'}##{p_id}"):
                            db.collection("profissionais").document(p_id).update({"verificado": not p.get('verificado')})
                            st.rerun()

                        if col_b3.button(f"🗑️ Excluir Perfil##{p_id}"):
                            db.collection("profissionais").document(p_id).delete()
                            st.success(f"Perfil {p_id} removido!")
                            st.rerun()

        with tab_adm2:
            st.subheader("Recarga Manual de Moedas")
            col_m1, col_m2 = st.columns(2)
            alvo_zap = col_m1.text_input("WhatsApp do Parceiro (com DDD)", placeholder="Ex: 11991853488")
            qtd_moedas = col_m2.number_input("Quantidade de Moedas", min_value=-500, max_value=500, value=10)

            if st.button("⚡ CREDITAR MOEDAS AGORA", use_container_width=True):
                zap_f = limpar_whatsapp(alvo_zap)
                if db:
                    ref_user = db.collection("profissionais").document(zap_f)
                    doc_u = ref_user.get()
                    
                    if doc_u.exists:
                        saldo_atual = doc_u.to_dict().get("saldo", 0)
                        novo_saldo = saldo_atual + qtd_moedas
                        ref_user.update({"saldo": novo_saldo})
                        st.balloons()
                        st.success(f"Saldo atualizado de {saldo_atual} para {novo_saldo} moedas!")
                    else:
                        st.error("Usuário não encontrado.")

        with tab_adm3:
            st.subheader("Gerenciar Categorias Oficiais")
            cats_atuais = buscar_opcoes_dinamicas("categorias", CATEGORIAS_OFICIAIS)
            nova_cat = st.text_input("Nova Categoria")
            
            if st.button("➕ Adicionar Categoria") and nova_cat:
                if nova_cat not in cats_atuais:
                    cats_atuais.append(nova_cat)
                    if db:
                        db.collection("configuracoes").document("categorias").set({"lista": sorted(cats_atuais)})
                        st.success(f"Categoria '{nova_cat}' adicionada!")
                        st.rerun()
                else:
                    st.warning("Categoria já existe.")
    elif senha_adm:
        st.error("Chave incorreta!")

# ==============================================================================
# ABA 5: FEEDBACK E AVALIAÇÕES
# ==============================================================================
with menu_abas[4]:
    st.markdown("### ⭐ Avalie a Plataforma ou Deixe uma Sugestão")
    
    with st.form("form_feedback"):
        f_nome = st.text_input("Seu Nome ou Nome do Seu Negócio")
        f_rating = st.slider("Nota para o GeralJá", 1, 5, 5)
        f_mensagem = st.text_area("O que podemos melhorar no sistema?")
        
        btn_feedback = st.form_submit_button("📩 ENVIAR FEEDBACK", use_container_width=True)
        
        if btn_feedback:
            if f_mensagem and db:
                db.collection("feedbacks").add({
                    "nome": f_nome or "Anônimo",
                    "rating": f_rating,
                    "mensagem": f_mensagem,
                    "data": datetime.now().strftime("%d/%m/%Y %H:%M")
                })
                st.balloons()
                st.success("Obrigado pelo seu feedback! Sua opinião ajuda o GeralJá a evoluir.")
            else:
                st.error("Por favor, escreva uma mensagem antes de enviar.")

# ==============================================================================
# ABA 6: MÉTRICAS FINANCEIRAS (HABILITADA VIA COMANDO SECRET ?cmd=abracadabra)
# ==============================================================================
if comando == "abracadabra":
    with menu_abas[5]:
        st.markdown("### 📊 Dashboard Financeiro & Métricas Master")
        
        if db:
            profs_all = list(db.collection("profissionais").stream())
            total_parceiros = len(profs_all)
            total_moedas_circulacao = sum([doc.to_dict().get("saldo", 0) for doc in profs_all])
            total_visitas_geral = sum([doc.to_dict().get("cliques", 0) for doc in profs_all])
            
            f1, f2, f3 = st.columns(3)
            f1.metric("Total de Parceiros Cadastrados", f"{total_parceiros}")
            f2.metric("Moedas em Circulação", f"{total_moedas_circulacao} 🪙")
            f3.metric("Total de Visitas em Perfis", f"{total_visitas_geral} 👀")
            
            st.divider()
            st.markdown("#### Resumo dos Cadastros Recentes")
            
            dados_tabela = []
            for doc in profs_all:
                d_p = doc.to_dict()
                dados_tabela.append({
                    "Nome": d_p.get("nome"),
                    "Categoria": d_p.get("area"),
                    "WhatsApp": doc.id,
                    "Saldo (Moedas)": d_p.get("saldo", 0),
                    "Aprovado": "Sim" if d_p.get("aprovado") else "Não",
                    "Data Cadastro": d_p.get("data_cadastro", "N/I")
                })
                
            if dados_tabela:
                st.dataframe(pd.DataFrame(dados_tabela), use_container_width=True)

# ==============================================================================
# RENDERIZAÇÃO DO RODAPÉ INSTITUCIONAL
# ==============================================================================
finalizar_e_alinhar_layout()

```
