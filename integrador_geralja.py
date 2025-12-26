import pandas as pd
import sqlite3
from persistencia_geralja import HistoricoGeralJa
from matching_geralja import AlgoritmoMatching

def integrar_sistema():
    print("?? [GERALJÁ] Iniciando Integração do HUB Grajaú...")
    
    # 1. Carregar Dados do CSV
    try:
        # Usando o separador ';' que vi no seu arquivo candidatos.csv
        df = pd.read_csv('candidatos.csv', sep=';')
        print(f"?? {len(df)} Candidatos encontrados no CSV.")
    except Exception as e:
        print(f"? Erro ao ler CSV: {e}")
        return

    # 2. Instanciar a Inteligência e o Banco
    db = HistoricoGeralJa("geralja_v1.db")
    ia = AlgoritmoMatching()
    
    # 3. Processar e Salvar no Banco Master
    # Vamos garantir que a tabela de prestadores existe no banco master
    with sqlite3.connect("geralja_v1.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prestadores_ativos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                whatsapp TEXT,
                categoria TEXT,
                regiao TEXT,
                score_ia REAL,
                status_seguranca TEXT
            )
        ''')
        
        print("?? Verificando segurança e calculando Scores...")
        for _, row in df.iterrows():
            # Simulação de verificação de antecedentes para o integrador
            status_seguranca = "APROVADO" if "Analise" not in str(row['Regioes']) else "PENDENTE"
            
            # Cálculo de Score Inicial usando sua IA (matching_geralja)
            # Como ainda não temos rating real, iniciamos com 4.5 e distância média
            score_inicial = ia.calcular_score({'rating': 4.5, 'antecedentes': status_seguranca}, 1.5)
            
            cursor.execute('''
                INSERT INTO prestadores_ativos (nome, whatsapp, categoria, regiao, score_ia, status_seguranca)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (row['Nome'], row['WhatsApp'], row['Categoria'], row['Regioes'], score_inicial, status_seguranca))
            
        conn.commit()
    
    print("? [SUCESSO] HUB GeralJá sincronizado com o Banco de Dados!")

if __name__ == "__main__":
    integrar_sistema()