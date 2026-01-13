# ============================================================================== 
# GERALJÁ: CRIANDO SOLUÇÕES - VERSÃO FINAL CORRIGIDA 
# ============================================================================== 
import streamlit as st 
# import firebase_admin
# from firebase_admin import credentials, firestore
# import base64
# import json
# import math
# import re
# import time
# import pandas as pd
# import unicodedata
# import pytz
# from datetime import datetime

# [2] CONFIGURAÇÃO INICIAL (Sempre antes de qualquer comando de UI)
st.set_page_config(page_title="GeralJá v3.0", layout="wide")
LAT_PADRAO = -23.5505
LON_PADRAO = -46.6333

# [3] O MOTOR MESTRE
# ============================================================================== 
# MOTOR MESTRE GERALJÁ v3.0 - O ORQUESTRADOR FINAL 
# ============================================================================== 
class MotorGeralJa:
    @staticmethod
    def normalizar(texto):
        """Remove acentos e padroniza o texto (IA Utils)"""
        if not texto:
            return ""
        return "".join(c for c in unicodedata.normalize('NFD', str(texto)) 
                      if unicodedata.category(c) != 'Mn').lower().strip()

    @staticmethod
    def processar_intencao(termo):
        """Versão turbinada que usa Normalização e Conceitos Expandidos"""
        if not termo:
            return "NAO_ENCONTRADO"
        t_clean = MotorGeralJa.normalizar(termo)
        # MAPA EXPANDIDO: Mais palavras-chave para não perder nenhum cliente
        mapa = {
            "Pintor": ["pint", "parede", "tinta", "grafite", "verniz", "massa corrida", "textura"],
            "Encanador": ["cano", "vazamento", "pia", "esgoto", "torneira", "hidraulico", "caixa d'agua", "desentup"],
            "Eletricista": ["luz", "fio", "tomada", "disjuntor", "choque", "curto", "padrao", "eletrica", "lampada"],
            "Mecânico": ["carro", "motor", "pneu", "freio", "revisao", "oleo", "suspensao", "oficina", "alinhamento"],
            "Alimentação": ["fome", "comida", "pizza", "lanche", "marmita", "restaurante", "doce", "salgado", "bolo"],
            "Pedreiro": ["obra", "reforma", "cimento", "tijolo", "telhado", "piso", "azulejo", "alicerce", "constru"],
            "Limpeza": ["faxina", "limpar", "casa", "diarista", "organiza", "lavar", "pos-obra"],
            "Ar Condicionado": ["gelar", "ar", "climatiza", "split", "instalacao ar"],
            "Marido de Aluguel": ["conserto", "montagem", "pendurar", "furo", "reparos gerais"]
        }
        # Busca por radical (Pega "pintar", "pintura" e "pintor" apenas com "pint")
        for categoria, palavras in mapa.items():
            for p in palavras:
                # Se o radical da palavra-chave estiver no termo buscado
                if MotorGeralJa.normalizar(p) in t_clean:
                    return categoria
        # Se não achar no mapa, tenta retornar o termo original para ver se bate com o banco
        return termo.capitalize()

    @staticmethod
    def calcular_distancia(lat1, lon1, lat2, lon2):
        """Cálculo preciso com conversão de tipos e limpeza de erro"""
        try:
            # Converte tudo para float caso venha como texto do banco/input
            l1, o1 = float(lat1), float(lon1)
            l2, o2 = float(lat2), float(lon2)
            # Se for coordenada 0,0 provavelmente está errado, joga pra longe
            if l1 == 0 or l2 == 0:
                return 999.0
            R = 6371 # Raio da Terra em KM
            dlat = math.radians(l2 - l1)
            dlon = math.radians(o2 - o1)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(l1)) * \
                math.cos(math.radians(l2)) * math.sin(dlon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            return round(R * c, 1)
        except (ValueError, TypeError, Exception):
            # Se qualquer dado falhar, retorna 999km para o profissional ir pro fim da lista
            return 999.0

    @staticmethod
    def renderizar_vitrine(p, pid):
        """Design Luxo Blindado"""
        foto = p.get('f1', '')
        img = f"data:image/jpeg;base64,{foto}" if len(foto) > 100 else "https://via.placeholder.com/400"
        dist = p.get('dist', 0.0)
        html = f"""
        <div style="border-radius:20px; padding:15px; background:white; box-shadow:0px 4px 15px rgba(0,0,0,0.1); margin-bottom:20px; border-left: 8px solid #FFD700;">
            <div style="display:flex; align-items:center; gap:15px;">
                <img src="{img}" style="width:70px; height:70px; border-radius:50%; object-fit:cover; border:2px solid #FFD700;">
                <div>
                    <h3 style="margin:0; font-size:18px; color:#1A1C23;">{p.get('nome', 'Profissional').upper()} {'✅' if p.get('verificado') else ''}</h3>
                    <span style="color:#FF4B4B; font-weight:bold; font-size:13px;">📍 a {dist:.1f} km de você</span>
                </div>
            </div>
            <p style="margin-top:10px; color:#555; font-size:14px;">{p.get('area', 'Geral')} • {p.get('descricao', '')[:110]}...</p>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)
        if st.button(f"Falar com {p.get('nome', '').split()[0]}", key=f"btn_{pid}", use_container_width=True):
            st.link_button("🚀 Abrir WhatsApp", f"https://wa.me/55{p.get('whatsapp', pid)}")

    @staticmethod
    def finalizar_layout():
        """O VARREDOR (Seu rodapé automático agora dentro do mestre)"""
        st.write("---")
        fechamento_estilo = """
        <style>
        .main .block-container {
            padding-bottom: 5rem !important;
        }
        .footer-clean {
            text-align: center;
            padding: 20px;
            opacity: 0.7;
            font-size: 0.8rem;
            width: 100%;
            color: gray;
        }
        </style>
        <div class="footer-clean">
            <p>🎯 <b>GeralJá</b> - Sistema de Inteligência Local</p>
            <p>v3.0 | © 2026 Todos os direitos reservados</p>
        </div>
        """
        st.markdown(fechamento_estilo, unsafe_allow_html=True)

# INSTANCIAÇÃO
IA_MESTRE = MotorGeralJa()

# ------------------------------------------------------------------------------ 
# 2. CAMADA DE PERSISTÊNCIA (FIREBASE) 
# ------------------------------------------------------------------------------ 
# @st.cache_resource
# def conectar_banco_master():
#     if not firebase_admin._apps:
#         try:
#             # Tenta pegar dos secrets do Streamlit
#             if "FIREBASE_BASE64" in st.secrets:
#                 b64_key = st.secrets["FIREBASE_BASE64"]
#                 decoded_json = base64.b64decode(b64_key).decode("utf-8")
#                 cred_dict = json.loads(decoded_json)
#                 cred = credentials.Certificate(cred_dict)
#                 return firebase_admin.initialize_app(cred)
#             else:
#                 # Fallback para desenvolvimento local (se houver arquivo json)
#                 # cred = credentials.Certificate("serviceAccountKey.json")
#                 # return firebase_admin.initialize_app(cred)
#                 st.warning("⚠️ Configure a secret FIREBASE_BASE64 para conectar ao banco.")
#                 return None
#         except Exception as e:
#             st.error(f"❌ FALHA NA INFRAESTRUTURA: {e}")
#             st.stop()
#     return firebase_admin.get_app()
# app_engine = conectar_banco_master()
# if app_engine:
#     db = firestore.client()
# else:
#     st.error("Erro ao conectar ao Firebase. Verifique suas configurações.")
#     st.stop()

# --- FUNÇÕES DE SUPORTE (Mantenha fora de blocos IF/ELSE para funcionar no app todo) ---
# def buscar_opcoes_dinamicas(documento, pad
# ==============================================================================
# --- ABA 2: CADASTRO (BLINDAGEM DE DUPLICADOS + 4 FOTOS + BÔNUS) ---
# ==============================================================================
with menu_abas[1]:
    st.markdown("### 🚀 Cadastro de Profissional Elite")
    st.info("🎁 BÔNUS: Novos cadastros ganham **10 GeralCones** de saldo inicial!")

    with st.form("form_cadastro_blindado_v4", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome Completo ou Empresa", placeholder="Ex: João Silva Pinturas")
            telefone = st.text_input("WhatsApp (DDD + Número)", help="Apenas números. Ex: 11999998888")
            area = st.selectbox("Sua Especialidade", CATEGORIAS_OFICIAIS)
        
        with col2:
            cidade = st.text_input("Cidade / UF", placeholder="Ex: São Paulo / SP")
            senha_acesso = st.text_input("Crie uma Senha", type="password", help="Para editar seu perfil no futuro")

        descricao = st.text_area("Descrição (O que você faz?)", placeholder="Conte um pouco sobre sua experiência e serviços...")
        
        st.markdown("---")
        st.write("📷 **Portfólio de Fotos** (Mostre seu trabalho)")
        
        # Grid de fotos 2x2 para ficar bonito no form
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            f1_file = st.file_uploader("Foto 1 (Perfil/Principal)", type=['jpg', 'jpeg', 'png'], key="cad_f1")
            f2_file = st.file_uploader("Foto 2 (Opcional)", type=['jpg', 'jpeg', 'png'], key="cad_f2")
        with f_col2:
            f3_file = st.file_uploader("Foto 3 (Opcional)", type=['jpg', 'jpeg', 'png'], key="cad_f3")
            f4_file = st.file_uploader("Foto 4 (Opcional)", type=['jpg', 'jpeg', 'png'], key="cad_f4")

        submit = st.form_submit_button("🚀 FINALIZAR E GANHAR 10 GERALCONES")

        if submit:
            # 1. LIMPEZA E FORMATAÇÃO DO ID
            tel_id = re.sub(r'\D', '', telefone)
            
            # --- REGRAS DE OURO (VALIDAÇÃO) ---
            if not nome or len(tel_id) < 10:
                st.error("❌ Nome e WhatsApp válidos são obrigatórios!")
            elif not f1_file:
                st.error("❌ Envie pelo menos a Foto Principal para atrair clientes!")
            else:
                try:
                    with st.spinner("Validando Cadastro Único..."):
                        # 2. BLINDAGEM CONTRA DUPLICADOS
                        doc_ref = db.collection("profissionais").document(tel_id).get()
                        
                        if doc_ref.exists:
                            st.warning(f"⚠️ Atenção! O número {tel_id} já está cadastrado no sistema.")
                            st.info("Use a aba de edição ou entre em contato com o suporte.")
                        else:
                            # 3. CONVERSÃO DE IMAGENS (SOMA DA FOTO 4)
                            img1 = converter_img_b64(f1_file)
                            img2 = converter_img_b64(f2_file) if f2_file else ""
                            img3 = converter_img_b64(f3_file) if f3_file else ""
                            img4 = converter_img_b64(f4_file) if f4_file else ""

                            # 4. ESTRUTURA DE DADOS COM BÔNUS DE 10 GERALCONES
                            dados_prof = {
                                "nome": nome.strip().upper(),
                                "telefone": tel_id,
                                "area": area,
                                "descricao": descricao,
                                "cidade": cidade.strip(),
                                "senha": senha_acesso,
                                "f1": img1, "f2": img2, "f3": img3, "f4": img4,
                                "aprovado": False,  # Entra para análise do admin
                                "verificado": False,
                                "saldo": 10.0,      # <--- BÔNUS GERALCONES AQUI
                                "lat": LAT_REF, 
                                "lon": LON_REF,
                                "data_cadastro": datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%d/%m/%Y %H:%M")
                            }

                            # 5. SALVAMENTO FINAL
                            db.collection("profissionais").document(tel_id).set(dados_prof)
                            
                            st.balloons()
                            st.success(f"🎊 PARABÉNS! {nome}, você ganhou 10 GeralCones!")
                            st.info("Seu perfil foi enviado para aprovação. Em breve você estará na vitrine!")
                            
                except Exception as e:
                    st.error(f"❌ Erro Técnico ao cadastrar: {e}")
# ==============================================================================
# ABA 3: MEU PERFIL (VITRINE LUXUOSA ESTILO INSTA)
# ==============================================================================
with menu_abas[2]:
    if 'auth' not in st.session_state: st.session_state.auth = False
    
    if not st.session_state.auth:
        st.markdown("<h2 style='text-align:center;'>🔐 Portal do Parceiro</h2>", unsafe_allow_html=True)
        with st.container():
            l_zap = st.text_input("WhatsApp (ID)", key="login_zap")
            l_pw = st.text_input("Senha", type="password", key="login_pw")
            if st.button("ENTRAR NA MINHA VITRINE", use_container_width=True):
                if l_zap:
                    doc_ref = db.collection("profissionais").document(l_zap)
                    doc = doc_ref.get()
                    if doc.exists and doc.to_dict().get('senha') == l_pw:
                        st.session_state.auth = True
                        st.session_state.user_id = l_zap
                        st.rerun()
                    else:
                        st.error("❌ Credenciais inválidas.")
    else:
        uid = st.session_state.user_id
        doc_ref = db.collection("profissionais").document(uid)
        d = doc_ref.get().to_dict()
        
        # --- HEADER ESTILO INSTAGRAM ---
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 20px; padding: 20px; background: white; border-radius: 20px; border: 1px solid #E2E8F0; margin-bottom: 20px;">
                <div style="position: relative;">
                    <img src="data:image/png;base64,{d.get('foto_b64', '')}" 
                         style="width: 100px; height: 100px; border-radius: 50%; object-fit: cover; border: 3px solid #E1306C;"
                         onerror="this.src='https://ui-avatars.com/api/?name={d.get('nome')}&background=random'">
                    <div style="position: absolute; bottom: 5px; right: 5px; background: #22C55E; width: 15px; height: 15px; border-radius: 50%; border: 2px solid white;"></div>
                </div>
                <div style="flex-grow: 1;">
                    <h2 style="margin: 0; font-size: 22px;">{d.get('nome')}</h2>
                    <p style="margin: 0; color: #64748B; font-size: 14px;">@{d.get('area').lower().replace(' ', '')}</p>
                    <div style="display: flex; gap: 15px; margin-top: 10px;">
                        <div style="text-align: center;"><b style="display: block;">{d.get('cliques', 0)}</b><small style="color: #64748B;">Cliques</small></div>
                        <div style="text-align: center;"><b style="display: block;">⭐ {d.get('rating', 5.0)}</b><small style="color: #64748B;">Nota</small></div>
                        <div style="text-align: center;"><b style="display: block;">{d.get('saldo', 0)}</b><small style="color: #64748B;">Moedas</small></div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # --- DASHBOARD DE PERFORMANCE (LUXUOSA) ---
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Visibilidade", f"{d.get('cliques', 0)} rkt", "Aumento de 12%")
        col_m2.metric("Saldo Atual", f"{d.get('saldo', 0)} 🪙")
        col_m3.metric("Status Perfil", "Elite" if d.get('elite') else "Padrão")

        # --- LOJA DE DESTAQUES (GRID VISUAL) ---
        st.markdown("### 💎 Impulsione sua Vitrine")
        with st.container():
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("<div style='background: linear-gradient(135deg, #FFD700, #FFA500); padding: 15px; border-radius: 15px; color: white; text-align: center;'><b>BRONZE</b><br>10 🪙<br>R$ 25</div>", unsafe_allow_html=True)
                if st.button("Comprar 10", key="buy_10", use_container_width=True):
                     st.markdown(f'<meta http-equiv="refresh" content="0;URL=https://wa.me/{ZAP_ADMIN}?text=Quero 10 moedas para ID: {uid}">', unsafe_allow_html=True)
            with c2:
                st.markdown("<div style='background: linear-gradient(135deg, #C0C0C0, #808080); padding: 15px; border-radius: 15px; color: white; text-align: center;'><b>PRATA</b><br>30 🪙<br>R$ 60</div>", unsafe_allow_html=True)
                if st.button("Comprar 30", key="buy_30", use_container_width=True):
                     st.markdown(f'<meta http-equiv="refresh" content="0;URL=https://wa.me/{ZAP_ADMIN}?text=Quero 30 moedas para ID: {uid}">', unsafe_allow_html=True)
            with c3:
                st.markdown("<div style='background: linear-gradient(135deg, #FFD700, #D4AF37); padding: 15px; border-radius: 15px; color: white; text-align: center;'><b>OURO</b><br>100 🪙<br>R$ 150</div>", unsafe_allow_html=True)
                if st.button("Comprar 100", key="buy_100", use_container_width=True):
                     st.markdown(f'<meta http-equiv="refresh" content="0;URL=https://wa.me/{ZAP_ADMIN}?text=Quero 100 moedas para ID: {uid}">', unsafe_allow_html=True)

        st.divider()

        # --- EDIÇÃO DE DADOS (TURBINADA) ---
        with st.expander("⚙️ CONFIGURAÇÕES DA VITRINE", expanded=False):
            with st.form("edit_v2"):
                st.markdown("#### ✨ Informações Públicas")
                new_foto = st.file_uploader("Trocar Foto de Perfil", type=["jpg", "png", "jpeg"])
                n_nome = st.text_input("Nome da Vitrine", value=d.get('nome'))
                n_desc = st.text_area("Bio (O que você faz de melhor?)", value=d.get('descricao'))
                
                col_e1, col_e2 = st.columns(2)
                n_area = col_e1.selectbox("Categoria", CATEGORIAS_OFICIAIS, index=CATEGORIAS_OFICIAIS.index(d.get('area', 'Ajudante Geral')))
                n_tipo = col_e2.radio("Tipo", ["👤 Profissional", "🏢 Comércio/Loja"], index=0 if d.get('tipo') == "👤 Profissional" else 1, horizontal=True)

                if st.form_submit_button("💾 ATUALIZAR MINHA VITRINE", use_container_width=True):
                    up = {
                        "nome": n_nome, "area": n_area, "descricao": n_desc, "tipo": n_tipo
                    }
                    if new_foto:
                        up["foto_b64"] = converter_img_b64(new_foto)
                    
                    doc_ref.update(up)
                    st.success("Vitrine atualizada! 🚀")
                    time.sleep(1)
                    st.rerun()

        if st.button("LOGOUT", type="secondary"):
            st.session_state.auth = False
            st.rerun()
# ==============================================================================
# ABA 4: 👑 PAINEL DE CONTROLE MASTER (TURBINADO)
# ==============================================================================
with menu_abas[3]:
    st.markdown("## 👑 Gestão Estratégica GeralJá")
    
    access_adm = st.text_input("Chave Mestra", type="password", key="auth_master")

    if access_adm == CHAVE_ADMIN:
        # --- 1. DASHBOARD DE MÉTRICAS ---
        st.markdown("### 📊 Performance da Rede")
        todos_profs = list(db.collection("profissionais").stream())
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Profissionais", len(todos_profs))
        
        # Cálculos rápidos
        total_cliques = sum([p.to_dict().get('cliques', 0) for p in todos_profs])
        saldo_total = sum([p.to_dict().get('saldo', 0) for p in todos_profs])
        pendentes = len([p for p in todos_profs if not p.to_dict().get('aprovado')])
        
        m2.metric("Cliques Totais", total_cliques)
        m3.metric("Saldo em Circulação", f"{saldo_total} 💎")
        m4.metric("Aguardando Aprovação", pendentes, delta_color="inverse", delta=pendentes)

        st.divider()# --- GERENCIADOR DE CATEGORIAS DINÂMICAS ---
        st.divider()
        st.markdown("### 🛠️ Configurações de Expansão")
        st.caption("Adicione novas opções que aparecerão instantaneamente no formulário de cadastro.")
        
        col_adm_1, col_adm_2 = st.columns(2)
        
        with col_adm_1:
            st.write("**✨ Novas Profissões (IA)**")
            nova_cat = st.text_input("Nome da Profissão", placeholder="Ex: Adestrador", key="add_cat_input")
            if st.button("➕ Adicionar Categoria", use_container_width=True):
                if nova_cat:
                    doc_ref = db.collection("configuracoes").document("categorias")
                    lista_atual = buscar_opcoes_dinamicas("categorias", [])
                    if nova_cat not in lista_atual:
                        lista_atual.append(nova_cat)
                        doc_ref.set({"lista": lista_atual})
                        st.success(f"'{nova_cat}' agora faz parte do sistema!")
                        time.sleep(1)
                        st.rerun()

        with col_adm_2:
            st.write("**🏢 Novos Tipos de Negócio**")
            novo_tipo = st.text_input("Tipo de Comércio", placeholder="Ex: Food Truck", key="add_tipo_input")
            if st.button("➕ Adicionar Tipo", use_container_width=True):
                if novo_tipo:
                    doc_ref = db.collection("configuracoes").document("tipos")
                    lista_atual = buscar_opcoes_dinamicas("tipos", [])
                    if novo_tipo not in lista_atual:
                        lista_atual.append(novo_tipo)
                        doc_ref.set({"lista": lista_atual})
                        st.success(f"'{novo_tipo}' adicionado com sucesso!")
                        time.sleep(1)
                        st.rerun()

        # --- 2. LISTA DE GESTÃO ---
        st.markdown("### 📋 Gerenciar Profissionais")
        
        for p_doc in todos_profs:
            p = p_doc.to_dict()
            pid = p_doc.id
            
            with st.expander(f"{'✅' if p.get('aprovado') else '⏳'} {p.get('nome').upper()} - {p.get('area')}"):
                c1, c2, c3 = st.columns([1, 2, 1])
                
                with c1:
                    # Foto de Perfil
                    foto = p.get('foto_b64')
                    if foto:
                        st.image(f"data:image/png;base64,{foto}", width=100)
                    st.write(f"ID: `{pid}`")
                    st.write(f"Saldo: **{p.get('saldo', 0)} 💎**")

                with c2:
                    st.write(f"**Descrição:** {p.get('descricao')}")
                    st.write(f"**Tipo:** {p.get('tipo')}")
                    st.write(f"**Cliques:** {p.get('cliques', 0)}")
                    
                    # Exibir as 3 fotos da vitrine se existirem
                    st.write("🖼️ **Vitrine:**")
                    fv = [p.get('f1'), p.get('f2'), p.get('f3')]
                    cols_f = st.columns(3)
                    for i, f_data in enumerate(fv):
                        if f_data:
                            cols_f[i].image(f"data:image/png;base64,{f_data}", use_container_width=True)

                with c3:
                    st.write("⚡ **Ações Rápidas**")
                    
                    # Aprovação
                    if not p.get('aprovado'):
                        if st.button("✅ APROVAR AGORA", key=f"apr_{pid}", use_container_width=True):
                            db.collection("profissionais").document(pid).update({"aprovado": True})
                            st.rerun()
                    
                    # Verificado/Elite
                    is_ver = p.get('verificado', False)
                    label_ver = "💎 REMOVER ELITE" if is_ver else "🌟 TORNAR ELITE"
                    if st.button(label_ver, key=f"ver_{pid}", use_container_width=True):
                        db.collection("profissionais").document(pid).update({"verificado": not is_ver})
                        st.rerun()

                    # Adicionar Saldo (Pacote de 10)
                    if st.button("➕ ADD 10 SALDO", key=f"plus_{pid}", use_container_width=True):
                        db.collection("profissionais").document(pid).update({"saldo": p.get('saldo', 0) + 10})
                        st.rerun()

                    # Botão de Exclusão (Cuidado!)
                    if st.button("🗑️ EXCLUIR", key=f"del_{pid}", use_container_width=True):
                        db.collection("profissionais").document(pid).delete()
                        st.rerun()

    elif access_adm != "":
        st.error("🚫 Acesso negado. Chave incorreta.")
    else:
        st.info("Aguardando Chave Mestra para liberar os controles.")

# ==============================================================================
# ABA 5: FEEDBACK
# ==============================================================================
with menu_abas[4]:
    st.header("⭐ Avalie a Plataforma")
    st.write("Sua opinião nos ajuda a melhorar.")
    
    nota = st.slider("Nota", 1, 5, 5)
    comentario = st.text_area("O que podemos melhorar?")
    
    if st.button("Enviar Feedback"):
        st.success("Obrigado! Sua mensagem foi enviada para nossa equipe.")
        # Em produção, salvaria em uma coleção 'feedbacks'

# ------------------------------------------------------------------------------
# FINALIZAÇÃO (DO ARQUIVO ORIGINAL)
# ------------------------------------------------------------------------------
finalizar_e_alinhar_layout()









