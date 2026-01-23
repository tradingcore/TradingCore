"""
Script para buscar descrições das ações B3 via Yahoo Finance.
Cria um JSON simples com {ticker: description}.

Uso: python src/scripts/gerar_contextos.py
"""
import csv
import json
import time
from pathlib import Path

import yfinance as yf

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
CSV_PATH = PROJECT_ROOT / "docs" / "acoes-listadas-b3.csv"
JSON_PATH = PROJECT_ROOT / "docs" / "contextos-acoes.json"


def carregar_tickers_csv():
    """Carrega lista de tickers do CSV."""
    tickers = []
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticker = row.get('Ticker', '').strip()
            if ticker and ticker not in tickers:
                tickers.append(ticker)
    return tickers


def carregar_contextos_existentes():
    """Carrega contextos já salvos."""
    if JSON_PATH.exists():
        try:
            with open(JSON_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except:
            pass
    return {}


def salvar_contextos(contextos):
    """Salva contextos no JSON."""
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(contextos, f, ensure_ascii=False, indent=2)


def buscar_description_yahoo(ticker):
    """Busca description do Yahoo Finance."""
    try:
        symbol = f"{ticker}.SA"
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # Pegar description (longBusinessSummary)
        description = info.get('longBusinessSummary', '')
        
        if description:
            return description
        
        return None
        
    except Exception as e:
        return None


def main():
    print("="*60)
    print("📊 BUSCANDO DESCRIÇÕES DO YAHOO FINANCE")
    print("="*60)
    
    # Carregar dados
    tickers = carregar_tickers_csv()
    contextos = carregar_contextos_existentes()
    
    print(f"\n📋 {len(tickers)} tickers únicos no CSV")
    print(f"📄 {len(contextos)} contextos já existentes")
    
    # Identificar tickers sem contexto
    tickers_sem_contexto = [t for t in tickers if t not in contextos]
    
    print(f"🔍 {len(tickers_sem_contexto)} tickers sem descrição\n")
    
    if not tickers_sem_contexto:
        print("✅ Todos os tickers já têm descrição!")
        return
    
    print(f"📝 Buscando descrições para {len(tickers_sem_contexto)} tickers...")
    print("   (Ctrl+C para parar)\n")
    
    encontrados = 0
    nao_encontrados = 0
    
    try:
        for i, ticker in enumerate(tickers_sem_contexto):
            print(f"[{i+1}/{len(tickers_sem_contexto)}] {ticker}...", end=" ", flush=True)
            
            description = buscar_description_yahoo(ticker)
            
            if description:
                contextos[ticker] = description
                encontrados += 1
                print(f"✓ ({len(description)} chars)")
            else:
                nao_encontrados += 1
                print("✗ (sem descrição)")
            
            # Salvar a cada 20 tickers
            if (i + 1) % 20 == 0:
                salvar_contextos(contextos)
                print(f"   💾 Salvo ({encontrados} encontrados, {nao_encontrados} sem descrição)")
            
            # Rate limit
            time.sleep(0.3)
            
    except KeyboardInterrupt:
        print("\n\n⏹ Interrompido pelo usuário")
    
    # Salvar final
    salvar_contextos(contextos)
    
    print(f"\n{'='*60}")
    print(f"✅ CONCLUÍDO")
    print(f"   Descrições encontradas: {encontrados}")
    print(f"   Sem descrição: {nao_encontrados}")
    print(f"   Total no arquivo: {len(contextos)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
