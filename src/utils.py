"""
Funções utilitárias do TradingCore.
"""
from datetime import datetime, timedelta
import pytz
from .config import HORAS_RETROATIVAS


def calcular_periodo_24h():
    """
    Calcula o período das últimas N horas em formato YYYY-MM-DD.
    Usa timezone de São Paulo.
    """
    tz = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(tz)
    inicio = agora - timedelta(hours=HORAS_RETROATIVAS)

    data_inicio = inicio.strftime('%Y-%m-%d')
    data_fim = agora.strftime('%Y-%m-%d')

    return data_inicio, data_fim


def parsear_tickers(ticker_str):
    """
    Converte string de tickers separados por vírgula em lista.
    Exemplo: "ABEV3, PETR4, VALE3" -> ["ABEV3", "PETR4", "VALE3"]
    """
    import pandas as pd
    
    if not ticker_str or pd.isna(ticker_str):
        return []

    tickers = [t.strip().upper() for t in ticker_str.split(',')]
    return [t for t in tickers if t]


def formatar_timestamp():
    """Retorna timestamp formatado no timezone de São Paulo."""
    tz = pytz.timezone('America/Sao_Paulo')
    return datetime.now(tz).strftime('%d/%m/%Y %H:%M')


def extrair_tickers_unicos(df_usuarios):
    """
    Extrai todos os tickers únicos de todos os usuários.
    
    Args:
        df_usuarios: DataFrame com coluna 'Ticker 1' contendo tickers separados por vírgula
        
    Returns:
        Set de tickers únicos (ex: {'PETR4', 'VALE3', 'BBAS3'})
    """
    todos_tickers = set()
    
    for _, row in df_usuarios.iterrows():
        ticker_str = row.get('Ticker 1', '')
        tickers = parsear_tickers(ticker_str)
        todos_tickers.update(tickers)
    
    return todos_tickers

