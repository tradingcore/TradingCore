"""
Módulo para buscar preços e variações do Yahoo Finance.
Considera feriados ANBIMA para identificar dias úteis corretos.
"""
import yfinance as yf
from datetime import datetime, timedelta
import json
import os
import pytz


def carregar_feriados():
    """
    Carrega a lista de feriados ANBIMA do arquivo JSON.
    """
    try:
        caminho = os.path.join(os.path.dirname(__file__), 'feriados_anbima.json')
        with open(caminho, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"  ⚠ Erro ao carregar feriados: {e}")
        return {}


def eh_dia_util(data, feriados_ano):
    """
    Verifica se uma data é dia útil (não é fim de semana nem feriado).
    """
    # Verifica fim de semana
    if data.weekday() >= 5:  # 5 = sábado, 6 = domingo
        return False
    
    # Verifica feriado
    mes_dia = data.strftime('%m-%d')
    ano = str(data.year)
    
    if ano in feriados_ano and mes_dia in feriados_ano[ano]:
        return False
    
    return True


def obter_ultimo_dia_util(data_referencia=None):
    """
    Retorna o último dia útil antes de hoje (ou da data de referência).
    Considera fins de semana e feriados ANBIMA.
    """
    feriados = carregar_feriados()
    tz = pytz.timezone('America/Sao_Paulo')
    
    if data_referencia is None:
        data = datetime.now(tz).date()
    else:
        data = data_referencia
    
    # Voltar um dia inicialmente
    data = data - timedelta(days=1)
    
    # Encontrar o último dia útil
    while not eh_dia_util(data, feriados):
        data = data - timedelta(days=1)
    
    return data


def buscar_preco_e_variacao(ticker):
    """
    Busca preço de fechamento e variação percentual do dia anterior de um ticker.
    
    Args:
        ticker: Código do ticker da B3 (ex: "ABEV3")
        
    Returns:
        Dicionário com:
            - preco_fechamento: Preço de fechamento (float ou None)
            - variacao_percentual: Variação % (float ou None)
            - data_referencia: Data de referência do preço/variação
            - sucesso: Boolean indicando se a busca foi bem-sucedida
    """
    try:
        # Adiciona .SA para tickers da B3
        ticker_yahoo = f"{ticker}.SA" if not ticker.endswith('.SA') else ticker
        
        # Buscar dados dos últimos 10 dias (para garantir que pegamos dias úteis)
        stock = yf.Ticker(ticker_yahoo)
        hist = stock.history(period="10d")
        
        if hist.empty or len(hist) < 2:
            print(f"  ⚠ {ticker}: Dados insuficientes no Yahoo Finance")
            return {
                'preco_fechamento': None,
                'variacao_percentual': None,
                'data_referencia': None,
                'sucesso': False
            }
        
        # Pegar os dois últimos dias úteis disponíveis
        preco_atual = hist['Close'].iloc[-1]
        preco_anterior = hist['Close'].iloc[-2]
        
        # Data de referência é o último dia útil (o dia do preço atual)
        data_referencia = hist.index[-1].strftime("%Y-%m-%d")
        
        # Calcular variação percentual
        variacao_pct = ((preco_atual - preco_anterior) / preco_anterior) * 100
        
        print(f"  ✓ {ticker}: R$ {preco_atual:.2f} ({variacao_pct:+.2f}%) ref. {data_referencia}")
        
        return {
            'preco_fechamento': float(preco_atual),
            'variacao_percentual': float(variacao_pct),
            'data_referencia': data_referencia,  # Uma única data de referência
            'sucesso': True
        }
        
    except Exception as e:
        print(f"  ✗ Erro ao buscar preço de {ticker}: {e}")
        return {
            'preco_fechamento': None,
            'variacao_percentual': None,
            'data_referencia': None,
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
