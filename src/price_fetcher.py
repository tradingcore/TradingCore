"""
Módulo para buscar preços e variações do Yahoo Finance.
"""
import yfinance as yf
from datetime import datetime, timedelta


def buscar_preco_e_variacao(ticker):
    """
    Busca preço de fechamento e variação percentual do dia anterior de um ticker.
    
    Args:
        ticker: Código do ticker da B3 (ex: "ABEV3")
        
    Returns:
        Dicionário com:
            - preco_fechamento: Preço de fechamento (float ou None)
            - variacao_percentual: Variação % (float ou None)
            - sucesso: Boolean indicando se a busca foi bem-sucedida
    """
    try:
        # Adiciona .SA para tickers da B3
        ticker_yahoo = f"{ticker}.SA" if not ticker.endswith('.SA') else ticker
        
        # Buscar dados dos últimos 5 dias (para garantir que pegamos o último dia útil)
        stock = yf.Ticker(ticker_yahoo)
        hist = stock.history(period="5d")
        
        if hist.empty or len(hist) < 2:
            print(f"  ⚠ {ticker}: Dados insuficientes no Yahoo Finance")
            return {
                'preco_fechamento': None,
                'variacao_percentual': None,
                'sucesso': False
            }
        
        # Pegar os dois últimos dias úteis
        preco_atual = hist['Close'].iloc[-1]
        preco_anterior = hist['Close'].iloc[-2]
        
        # Calcular variação percentual
        variacao_pct = ((preco_atual - preco_anterior) / preco_anterior) * 100
        
        print(f"  ✓ {ticker}: R$ {preco_atual:.2f} ({variacao_pct:+.2f}%)")
        
        return {
            'preco_fechamento': float(preco_atual),
            'variacao_percentual': float(variacao_pct),
            'sucesso': True
        }
        
    except Exception as e:
        print(f"  ✗ Erro ao buscar preço de {ticker}: {e}")
        return {
            'preco_fechamento': None,
            'variacao_percentual': None,
            'sucesso': False
        }


def buscar_precos_multiplos(tickers):
    """
    Busca preços e variações para múltiplos tickers.
    
    Args:
        tickers: Lista ou set de tickers
        
    Returns:
        Dicionário {ticker: {preco_fechamento, variacao_percentual, sucesso}}
    """
    if not tickers:
        return {}
    
    print(f"\n{'='*60}")
    print(f"💰 BUSCANDO PREÇOS DE {len(tickers)} TICKERS")
    print(f"{'='*60}")
    
    precos = {}
    for ticker in sorted(tickers):
        precos[ticker] = buscar_preco_e_variacao(ticker)
    
    # Estatísticas
    sucessos = sum(1 for p in precos.values() if p['sucesso'])
    print(f"\n✓ Preços obtidos: {sucessos}/{len(tickers)}")
    
    return precos

