"""
Módulo para busca de notícias usando Event Registry API.
Otimizado com busca em batch para reduzir chamadas de API.
Usa nomes curtos das empresas do CSV para melhorar resultados.
"""
import re
from eventregistry import EventRegistry, QueryArticlesIter
from .config import EVENT_REGISTRY_API_KEY, MAX_NOTICIAS_POR_TICKER
from .ticker_loader import carregar_catalogo_empresas

# Catálogo de empresas (ticker -> nome_curto) - carregado do CSV
_CATALOGO_EMPRESAS = None

def _get_catalogo():
    """Retorna catálogo de empresas (com cache)."""
    global _CATALOGO_EMPRESAS
    if _CATALOGO_EMPRESAS is None:
        _CATALOGO_EMPRESAS = carregar_catalogo_empresas()
    return _CATALOGO_EMPRESAS

# Tamanho do batch para busca (limitado pelo plano da API Event Registry - max 15)
BATCH_SIZE = 10


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


def buscar_noticias_batch(tickers, data_inicio, data_fim, max_items_total=200):
    """
    Busca notícias de múltiplos tickers usando nomes de empresas.
    Usa sintaxe correta do Event Registry com $or.
    
    Ref: https://newsapi.ai/blog/how-to-make-complex-queries/

    Args:
        tickers: Lista de tickers (ex: ["PETR4", "VALE3"])
        data_inicio: Data início no formato YYYY-MM-DD
        data_fim: Data fim no formato YYYY-MM-DD
        max_items_total: Número máximo total de artigos

    Returns:
        Dicionário {ticker: [lista de artigos]}
    """
    if not tickers:
        return {}

    try:
        er = EventRegistry(apiKey=EVENT_REGISTRY_API_KEY)

        # Construir lista de keywords (nomes curtos das empresas)
        catalogo = _get_catalogo()
        keywords_list = []
        ticker_to_keyword = {}
        
        for ticker in tickers:
            # Usar nome curto da empresa se disponível, senão usar o ticker
            nome = catalogo.get(ticker, ticker)
            keywords_list.append(nome)
            ticker_to_keyword[ticker] = nome.upper()
        
        # Construir query com $or corretamente
        # Ref: https://newsapi.ai/blog/how-to-make-complex-queries/
        query = {
            "$query": {
                "$and": [
                    {
                        "keyword": {
                            "$or": keywords_list
                        },
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
                keyword = ticker_to_keyword[ticker]
                # Também verificar o código do ticker
                if keyword in texto_completo or ticker in texto_completo:
                    if artigo not in resultado[ticker]:
                        resultado[ticker].append(artigo)

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
    Busca notícias de todos os tickers, dividindo em batches de 10.
    Processa todas as empresas listadas na B3.

    Args:
        tickers: Lista completa de tickers
        data_inicio: Data início no formato YYYY-MM-DD
        data_fim: Data fim no formato YYYY-MM-DD
        batch_size: Tamanho de cada batch (default: BATCH_SIZE = 10)

    Returns:
        Dicionário {ticker: [lista de artigos]}
    """
    if batch_size is None:
        batch_size = BATCH_SIZE

    resultado_final = {}
    total_batches = (len(tickers) + batch_size - 1) // batch_size

    print(f"\n📰 Buscando notícias de {len(tickers)} tickers em {total_batches} batches de {batch_size}...")

    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        print(f"\n  Batch {batch_num}/{total_batches} ({len(batch)} tickers)...")
        
        resultado_batch = buscar_noticias_batch(batch, data_inicio, data_fim)
        resultado_final.update(resultado_batch)
        
        # Log de progresso a cada 10 batches
        if batch_num % 10 == 0:
            tickers_com_noticias = sum(1 for t in resultado_final if resultado_final[t])
            print(f"  → Progresso: {batch_num}/{total_batches} batches, {tickers_com_noticias} tickers com notícias")

    # Resumo final
    tickers_com_noticias = sum(1 for t in resultado_final if resultado_final[t])
    total_noticias = sum(len(v) for v in resultado_final.values())
    print(f"\n✅ Busca concluída: {tickers_com_noticias} tickers com notícias ({total_noticias} artigos)")

    return resultado_final
