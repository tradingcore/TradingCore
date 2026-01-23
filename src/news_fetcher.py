"""
Módulo para busca de notícias usando Event Registry API.
Otimizado com busca em batch para reduzir chamadas de API.
"""
import re
from eventregistry import EventRegistry, QueryArticlesIter
from .config import EVENT_REGISTRY_API_KEY, MAX_NOTICIAS_POR_TICKER

# Mapeamento de tickers para nomes de empresas (para melhorar a busca)
TICKER_NOMES = {
    "PETR4": ["Petrobras", "PETR4", "PETR3"],
    "PETR3": ["Petrobras", "PETR4", "PETR3"],
    "VALE3": ["Vale", "VALE3"],
    "ITUB4": ["Itaú", "Itau", "ITUB4", "ITUB3"],
    "BBDC4": ["Bradesco", "BBDC4", "BBDC3"],
    "BBAS3": ["Banco do Brasil", "BBAS3"],
    "ABEV3": ["Ambev", "ABEV3"],
    "WEGE3": ["WEG", "WEGE3"],
    "RENT3": ["Localiza", "RENT3"],
    "MGLU3": ["Magazine Luiza", "Magalu", "MGLU3"],
    "B3SA3": ["B3", "B3SA3", "bolsa brasileira"],
    "COGN3": ["Cogna", "COGN3"],
    "CVCB3": ["CVC", "CVCB3"],
    # Adicionar mais conforme necessário
}

# Tamanho do batch para busca (limitado pelo plano da API Event Registry)
BATCH_SIZE = 15


def buscar_noticias(ticker, data_inicio, data_fim, max_items=None):
    """
    Busca notícias sobre um ticker específico usando Event Registry API.
    Mantida para compatibilidade.

    Args:
        ticker: Código do ticker (ex: "ABEV3")
        data_inicio: Data início no formato YYYY-MM-DD
        data_fim: Data fim no formato YYYY-MM-DD
        max_items: Número máximo de artigos a retornar

    Returns:
        Lista de dicionários com artigos
    """
    if max_items is None:
        max_items = MAX_NOTICIAS_POR_TICKER

    try:
        er = EventRegistry(apiKey=EVENT_REGISTRY_API_KEY)

        query = {
            "$query": {
                "$and": [
                    {
                        "keyword": ticker,
                        "keywordLoc": "body"
                    },
                    {
                        "dateStart": data_inicio,
                        "dateEnd": data_fim
                    }
                ]
            }
        }

        q = QueryArticlesIter.initWithComplexQuery(query)
        artigos = []

        for article in q.execQuery(er, maxItems=max_items):
            artigos.append(article)

        print(f"  ✓ {ticker}: {len(artigos)} notícias encontradas")
        return artigos

    except Exception as e:
        print(f"  ✗ Erro ao buscar notícias de {ticker}: {e}")
        return []


def buscar_noticias_batch(tickers, data_inicio, data_fim, max_items_total=500):
    """
    Busca notícias de múltiplos tickers em uma única chamada à API.
    Muito mais eficiente que chamar um por um.

    Args:
        tickers: Lista de tickers (ex: ["PETR4", "VALE3", "ITUB4"])
        data_inicio: Data início no formato YYYY-MM-DD
        data_fim: Data fim no formato YYYY-MM-DD
        max_items_total: Número máximo total de artigos a retornar

    Returns:
        Dicionário {ticker: [lista de artigos]}
    """
    if not tickers:
        return {}

    try:
        er = EventRegistry(apiKey=EVENT_REGISTRY_API_KEY)

        # Construir query com OR para todos os tickers
        keywords = " OR ".join(tickers)
        
        query = {
            "$query": {
                "$and": [
                    {
                        "keyword": keywords,
                        "keywordLoc": "body"
                    },
                    {
                        "dateStart": data_inicio,
                        "dateEnd": data_fim
                    }
                ]
            }
        }

        q = QueryArticlesIter.initWithComplexQuery(query)
        artigos_raw = []

        for article in q.execQuery(er, maxItems=max_items_total):
            artigos_raw.append(article)

        print(f"  📰 Batch: {len(artigos_raw)} notícias encontradas para {len(tickers)} tickers")

        # Separar artigos por ticker
        resultado = {ticker: [] for ticker in tickers}
        
        for artigo in artigos_raw:
            body = artigo.get('body', '') or ''
            title = artigo.get('title', '') or ''
            texto_completo = f"{title} {body}".upper()
            
            # Verificar quais tickers são mencionados neste artigo
            for ticker in tickers:
                # Buscar pelo ticker e nomes alternativos
                termos = TICKER_NOMES.get(ticker, [ticker])
                termos.append(ticker)  # Sempre incluir o próprio ticker
                
                for termo in termos:
                    if termo.upper() in texto_completo:
                        # Evitar duplicatas
                        if artigo not in resultado[ticker]:
                            resultado[ticker].append(artigo)
                        break

        # Log de resultados
        tickers_com_noticias = sum(1 for t in resultado if resultado[t])
        total_noticias = sum(len(v) for v in resultado.values())
        print(f"  ✓ {tickers_com_noticias}/{len(tickers)} tickers com notícias ({total_noticias} total)")

        return resultado

    except Exception as e:
        print(f"  ✗ Erro ao buscar notícias em batch: {e}")
        return {ticker: [] for ticker in tickers}


def buscar_noticias_todos_tickers(tickers, data_inicio, data_fim, batch_size=None):
    """
    Busca notícias de todos os tickers, dividindo em batches.

    Args:
        tickers: Lista completa de tickers
        data_inicio: Data início no formato YYYY-MM-DD
        data_fim: Data fim no formato YYYY-MM-DD
        batch_size: Tamanho de cada batch (default: BATCH_SIZE)

    Returns:
        Dicionário {ticker: [lista de artigos]}
    """
    if batch_size is None:
        batch_size = BATCH_SIZE

    resultado_final = {}
    total_batches = (len(tickers) + batch_size - 1) // batch_size

    print(f"\n📰 Buscando notícias de {len(tickers)} tickers em {total_batches} batches...")

    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        print(f"\n  Batch {batch_num}/{total_batches} ({len(batch)} tickers)...")
        
        resultado_batch = buscar_noticias_batch(batch, data_inicio, data_fim)
        resultado_final.update(resultado_batch)

    # Resumo final
    tickers_com_noticias = sum(1 for t in resultado_final if resultado_final[t])
    total_noticias = sum(len(v) for v in resultado_final.values())
    print(f"\n✅ Busca concluída: {tickers_com_noticias} tickers com notícias ({total_noticias} artigos)")

    return resultado_final
