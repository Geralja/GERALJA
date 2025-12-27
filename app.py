import streamlit as st
# ... (mantenha suas importações anteriores)

# --- CONFIGURAÇÕES FIXAS (DADOS BLINDADOS) ---
PIX_CHAVE = "11991853488"
ZAP_ADMIN = "5511991853488"
VALOR_GC = 1.00 # R$ 1,00 por GeralCoin

# Função para gerar o link do QR Code (Estático)
def gerar_qr_pix(valor):
    # Link gerador de QR Code simples para visualização
    return f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={PIX_CHAVE}"

# --- LISTA DE PROFISSÕES FIXA (CONSOLIDADA) ---
# Esta lista agora é tratada como constante para não ser alterada por engano
LISTA_PROFISSOES = sorted(list(set([
    "Acupuncturista", "Barman", "Bartender", "Garçom", "Garçonete", 
    "Churrasqueiro", "Cozinheiro(a)", "Pintor", "Eletricista", "Encanador", 
    "Pedreiro", "Diarista", "Mecânico", "Motorista", "Barbeiro", 
    "Cabeleireiro(a)", "Desenvolvedor Mobile", "Especialista em IA"
    # ... adicione as demais profissões aqui
])))

# --- NA ABA DE CARTEIRA (TAB 2) ---
with tab2:
    if login:
        # ... (lógica de login existente)
        st.markdown("### 💳 Recarga Instantânea")
        col_pix, col_info = st.columns([1, 2])
        
        with col_pix:
            st.image(gerar_qr_pix(10), caption="Aponte a câmera do celular")
            
        with col_info:
            st.markdown(f"""
            **Chave PIX (Celular):** `{PIX_CHAVE}`  
            
            **Instruções:**
            1. Escolha o valor da recarga.
            2. Pague via PIX (QR Code ao lado ou Chave).
            3. Envie o comprovante pelo botão abaixo.
            """)
            
            st.info("O saldo será liberado em até 15 minutos após o envio do comprovante.")
