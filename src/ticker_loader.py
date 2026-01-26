"""
Módulo centralizado para carregamento de tickers e dados de empresas.
Usa o arquivo empresas-cnpj-cvm-ticker-atualizado.csv como fonte única.
"""
import csv
from pathlib import Path
from functools import lru_cache

# Caminho do CSV
CSV_PATH = Path(__file__).parent.parent / "docs" / "empresas-cnpj-cvm-ticker-atualizado.csv"

# Prioridade de tickers (menor = maior prioridade)
TICKER_PRIORITY = {
    '3': 1,   # Ordinárias (ON)
    '4': 2,   # Preferenciais (PN)
    '5': 3,   # Preferenciais classe A
    '6': 4,   # Preferenciais classe B
    '11': 5,  # Units
}


def _get_ticker_suffix(ticker: str) -> str:
    """Extrai o sufixo numérico do ticker (ex: PETR3 -> 3, BPAC11 -> 11)."""
    # Remove letras do início
    suffix = ''.join(c for c in ticker if c.isdigit())
    return suffix


def _get_ticker_priority(ticker: str) -> int:
    """Retorna prioridade do ticker (menor = melhor)."""
    suffix = _get_ticker_suffix(ticker)
    return TICKER_PRIORITY.get(suffix, 99)


def priorizar_ticker(tickers_str: str) -> str:
    """
    Dado uma string com múltiplos tickers, retorna o prioritário.
    
    Prioridade: final 3 > 4 > 5 > 6 > 11
    
    Args:
        tickers_str: String com tickers separados por vírgula (ex: "PETR3, PETR4")
        
    Returns:
        Ticker prioritário (ex: "PETR3")
    """
    if not tickers_str or tickers_str == "Não listada":
        return ""
    
    tickers = [t.strip() for t in tickers_str.split(',') if t.strip()]
    
    if not tickers:
        return ""
    
    if len(tickers) == 1:
        return tickers[0]
    
    # Ordenar por prioridade e retornar o primeiro
    return sorted(tickers, key=_get_ticker_priority)[0]


@lru_cache(maxsize=1)
def _carregar_dados_csv():
    """Carrega e cacheia os dados do CSV."""
    dados = []
    
    try:
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                dados.append(row)
    except Exception as e:
        print(f"Erro ao carregar CSV de empresas: {e}")
        return []
    
    return dados


def carregar_tickers_listados() -> list:
    """
    Retorna lista de tickers únicos de empresas listadas.
    
    - Ignora linhas com Ticker = "Não listada"
    - Aplica priorização quando há múltiplos tickers (1 por empresa)
    
    Returns:
        Lista de tickers (ex: ["PETR3", "VALE3", "ITUB4", ...])
    """
    dados = _carregar_dados_csv()
    tickers = []
    
    for row in dados:
        ticker_str = row.get('Ticker', '').strip()
        
        if not ticker_str or ticker_str == "Não listada":
            continue
        
        # Priorizar quando há múltiplos
        ticker = priorizar_ticker(ticker_str)
        if ticker:
            tickers.append(ticker)
    
    return tickers


def carregar_todos_tickers() -> list:
    """
    Retorna lista de TODOS os tickers válidos (incluindo múltiplos por empresa).
    Útil para o frontend (autocomplete) onde o usuário pode escolher PETR3 ou PETR4.
    
    Returns:
        Lista de tickers (ex: ["PETR3", "PETR4", "VALE3", ...])
    """
    dados = _carregar_dados_csv()
    tickers = []
    
    for row in dados:
        ticker_str = row.get('Ticker', '').strip()
        
        if not ticker_str or ticker_str == "Não listada":
            continue
        
        # Expandir múltiplos
        for t in ticker_str.split(','):
            t = t.strip()
            if t and t not in tickers:
                tickers.append(t)
    
    return tickers


def carregar_catalogo_empresas() -> dict:
    """
    Retorna dicionário {ticker: nome_curto} para todas empresas listadas.
    Inclui todos os tickers (múltiplos por empresa).
    
    Útil para:
    - Busca de notícias (usar nome_curto)
    - Autocomplete no frontend
    - Exibição de nomes
    
    Returns:
        Dict {ticker: nome_curto} (ex: {"PETR3": "Petrobras", "PETR4": "Petrobras"})
    """
    dados = _carregar_dados_csv()
    catalogo = {}
    
    for row in dados:
        ticker_str = row.get('Ticker', '').strip()
        nome_curto = row.get('Nome_Curto', '').strip()
        nome_formal = row.get('Nome', '').strip()
        
        if not ticker_str or ticker_str == "Não listada":
            continue
        
        # Usar nome_curto ou fallback para nome formal
        nome = nome_curto if nome_curto else nome_formal
        
        # Mapear todos os tickers para o mesmo nome
        for t in ticker_str.split(','):
            t = t.strip()
            if t:
                catalogo[t] = nome
    
    return catalogo


def carregar_dados_empresas() -> list:
    """
    Retorna lista completa de dados das empresas listadas.
    
    Returns:
        Lista de dicts com: CNPJ, Nome, Nome_Curto, Codigo_CVM, Ticker, ticker_principal
    """
    dados = _carregar_dados_csv()
    empresas = []
    
    for row in dados:
        ticker_str = row.get('Ticker', '').strip()
        
        if not ticker_str or ticker_str == "Não listada":
            continue
        
        empresa = {
            'cnpj': row.get('CNPJ', ''),
            'nome': row.get('Nome', ''),
            'nome_curto': row.get('Nome_Curto', ''),
            'codigo_cvm': row.get('Codigo_CVM', ''),
            'tickers': ticker_str,
            'ticker_principal': priorizar_ticker(ticker_str)
        }
        empresas.append(empresa)
    
    return empresas


# Função para limpar cache (útil em testes)
def limpar_cache():
    """Limpa o cache de dados do CSV."""
    _carregar_dados_csv.cache_clear()


if __name__ == "__main__":
    # Teste das funções
    print("=" * 60)
    print("TESTE DO MÓDULO ticker_loader")
    print("=" * 60)
    
    tickers = carregar_tickers_listados()
    print(f"\n✓ Tickers listados (1 por empresa): {len(tickers)}")
    print(f"  Primeiros 10: {tickers[:10]}")
    
    todos = carregar_todos_tickers()
    print(f"\n✓ Todos os tickers: {len(todos)}")
    
    catalogo = carregar_catalogo_empresas()
    print(f"\n✓ Catálogo: {len(catalogo)} entradas")
    print(f"  PETR3 -> {catalogo.get('PETR3', 'N/A')}")
    print(f"  PETR4 -> {catalogo.get('PETR4', 'N/A')}")
    print(f"  VALE3 -> {catalogo.get('VALE3', 'N/A')}")
    
    empresas = carregar_dados_empresas()
    print(f"\n✓ Empresas: {len(empresas)}")
    
    # Teste de priorização
    print(f"\n✓ Priorização:")
    print(f"  'PETR3, PETR4' -> {priorizar_ticker('PETR3, PETR4')}")
    print(f"  'ELET6, ELET3' -> {priorizar_ticker('ELET6, ELET3')}")
    print(f"  'BPAC11, BPAC3, BPAC5' -> {priorizar_ticker('BPAC11, BPAC3, BPAC5')}")
