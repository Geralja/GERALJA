# ==============================================================================
# MÓDULO DE INTERFACE "HOME GRAJAÚ TEM" (ESTILO BING)
# ==============================================================================

# --- CSS DE FUNDO E BUSCA (ESTILO BING) ---
st.markdown(f"""
<style>
    .stApp {{
        background-image: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('https://images.unsplash.com/photo-1549492423-455208616167');
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    .search-container {{ display: flex; flex-direction: column; align-items: center; justify-content: center; margin-top: 15vh; color: white; }}
    .logo-main {{ font-weight: 900; font-size: 4rem; text-shadow: 2px 2px 15px rgba(0,0,0,0.5); margin-bottom: 20px; }}
    .search-box {{ width: 100%; max-width: 650px; background: white; padding: 15px 25px; border-radius: 50px; display: flex; align-items: center; box-shadow: 0 8px 20px rgba(0,0,0,0.3); }}
    .search-input {{ border: none !important; background: transparent !important; font-size: 1.3rem !important; color: #333 !important; }}
</style>
""", unsafe_allow_html=True)

# --- CABEÇALHO E BUSCA ---
st.markdown('<div class="search-container">', unsafe_allow_html=True)
st.markdown('<div class="logo-main">GRAJAÚ <span style="color:#FF8C00">TEM</span></div>', unsafe_allow_html=True)

col_mid = st.columns([1, 8, 1])[1]
with col_mid:
    # A BUSCA DINÂMICA
    termo = st.text_input("", placeholder="🔍 O que você procura no Grajaú hoje?", label_visibility="collapsed", key="input_busca_bing")

st.markdown('</div>', unsafe_allow_html=True)

# --- LÓGICA DE BUSCA HÍBRIDA (VITRINE + GOOGLE) ---
if termo:
    st.markdown('<div style="background: rgba(255,255,255,0.95); padding: 30px; border-radius: 20px; margin-top: 50px; color: #333;">', unsafe_allow_html=True)
    
    # 1. BUSCA NA SUA VITRINE (SEM ORDER_BY PARA NÃO TRAVAR)
    # Aqui usamos o seu motor de busca, mas sem o order_by que causava o erro.
    st.subheader("🛍️ Vitrine do Grajaú")
    resultados = db.collection("profissionais").where("aprovado", "==", True).stream()
    
    achou = False
    for p_doc in resultados:
        p = p_doc.to_dict()
        if termo.lower() in p.get('area', '').lower() or termo.lower() in p.get('nome', '').lower():
            st.success(f"✅ **{p.get('nome')}** — {p.get('area')}")
            st.write(p.get('descricao', ''))
            st.link_button("💬 Chamar no Zap", criar_link_zap(limpar_whatsapp(p.get('whatsapp','')), "Vi seu perfil no Grajaú Tem"))
            achou = True
    
    if not achou:
        st.warning("Nenhum profissional encontrado na vitrine. Buscando notícias locais...")
        
        # 2. BUSCA NO GOOGLE (RSS) SE NÃO ACHAR NA VITRINE
        st.subheader("📰 Notícias Recentes")
        try:
            url_rss = f"https://news.google.com/rss/search?q={urllib.parse.quote(termo + ' Grajaú')}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
            feed = feedparser.parse(url_rss)
            for n in feed.entries[:3]:
                st.markdown(f"[{n.title}]({n.link})")
        except:
            st.error("Sem notícias disponíveis agora.")

    st.markdown('</div>', unsafe_allow_html=True)

# --- RESTANTE DO CÓDIGO ---
# Aqui você mantém o código das suas abas (menu_abas = st.tabs(...)) 
# para que os outros módulos continuem funcionando.
