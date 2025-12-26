import streamlit as st
import random
import time

# --- CONFIGURAÇÃO E DESIGN ---
st.set_page_config(page_title="GeralJá | O HUB do Grajaú", layout="wide")

# Link da imagem que geramos (Você pode trocar pela URL da imagem final)
LOGO_URL = "https://img.freepik.com/vetores-premium/logotipo-de-servicos-domesticos-com-encanador-e-cliente_origem.jpg" 

st.markdown(f"""
    <style>
    .stApp {{ background: #050a10; color: white; }}
    
    /* Container da Logo tipo Google */
    .logo-container {{
        text-align: center;
        padding: 20px;
        margin-bottom: 10px;
    }}
    
    .logo-img {{
        width: 250px; /* Ajuste o tamanho aqui */
        border-radius: 15px;
        filter: drop-shadow(0px 4px 10px rgba(243, 156, 18, 0.3));
    }}

    .checkout-card {{ 
        background: white; color: black; padding: 25px; 
        border-radius: 20px; text-align: center; border: 4px solid #27ae60; 
    }}
    </style>
    
    <div class="logo-container">
        <img src="{LOGO_URL}" class="logo-img">
        <h1 style="color:#f39c12; margin-top:10px; font-family: sans-serif;">GERAL<span style="color:white">JÁ</span></h1>
    </div>
""", unsafe_allow_html=True)

# ... (Restante do código de busca e 10% de taxa que já fizemos)
