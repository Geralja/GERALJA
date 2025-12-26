# LÓGICA DE BUSCA (Versão Nuvem/Celular)
    if st.button("🚀 ATIVAR RADAR GERALJÁ"):
        with st.spinner("Buscando profissionais verificados..."):
            # Apenas um pequeno delay para dar sensação de busca
            time.sleep(1.5)
        
        # CARD DO RESULTADO (Aparece direto, sem limpar o espaço, para evitar o erro de Node)
        valor_simulado = random.randint(180, 290)
        st.markdown(f"""
            <div class="glass-card">
                <div style="display: flex; justify-content: space-between;">
                    <span class="trust-badge">🛡️ PARCEIRO VERIFICADO</span>
                    <span style="color:#f39c12;">📍 1.5 km de distância</span>
                </div>
                <h2 style="margin: 15px 0 5px 0;">Bony Silva</h2>
                <p style="color:#bdc3c7;">Especialista Master em Pintura Residencial</p>
                <div style="background: rgba(243, 156, 18, 0.1); padding: 15px; border-radius: 10px; margin: 15px 0;">
                    <p style="margin:0; font-size:12px; color:gray;">PREÇO FINAL (COM SEGURO GERALJÁ)</p>
                    <h1 style="margin:0; color:#f39c12;">R$ {valor_simulado},00</h1>
                </div>
            </div>
        """, unsafe_allow_html=True)
