"""
Módulo para busca de notícias usando Event Registry API.
"""
from eventregistry import EventRegistry, QueryArticlesIter
from .config import EVENT_REGISTRY_API_KEY, MAX_NOTICIAS_POR_TICKER


def buscar_noticias(ticker, data_inicio, data_fim, max_items=None):
    """
    Busca notícias sobre um ticker específico usando Event Registry API.

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

