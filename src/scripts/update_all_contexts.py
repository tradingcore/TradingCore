import os
import sys

# Adicionar a raiz do projeto ao path para importar src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.sheets_client import carregar_usuarios_sheets
from src.utils import extrair_tickers_unicos
from src.context_manager import gerar_contexto_ia

def main():
    print("\n" + "="*60)
    print("🔄 INICIANDO ATUALIZAÇÃO GLOBAL DE CONTEXTOS")
    print("="*60)
    
    # 1. Carregar usuários para descobrir todos os tickers
    print("📊 Carregando tickers da planilha...")
    df_usuarios = carregar_usuarios_sheets()
    
    if df_usuarios.empty:
        print("✗ Nenhum usuário encontrado!")
        return
        
    tickers_unicos = extrair_tickers_unicos(df_usuarios)
    print(f"✓ {len(tickers_unicos)} tickers únicos encontrados.")
    
    # 2. Forçar a regeneração de todos os contextos
    for ticker in sorted(tickers_unicos):
        try:
            gerar_contexto_ia(ticker)
        except Exception as e:
            print(f"✗ Erro ao atualizar {ticker}: {e}")
            
    print("\n" + "="*60)
    print("✅ ATUALIZAÇÃO CONCLUÍDA!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()

