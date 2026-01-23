"""
Módulo para busca de notícias usando Event Registry API.
Otimizado com busca em batch para reduzir chamadas de API.
"""
import re
from eventregistry import EventRegistry, QueryArticlesIter
from .config import EVENT_REGISTRY_API_KEY, MAX_NOTICIAS_POR_TICKER

# Mapeamento de tickers para nomes de empresas (para melhorar a busca)
TICKER_NOMES = {
    # Energia / Petróleo
    "PETR4": ["Petrobras"],
    "PETR3": ["Petrobras"],
    "PRIO3": ["PetroRio", "PRIO"],
    "CSAN3": ["Cosan"],
    "RAIZ4": ["Raízen", "Raizen"],
    "VBBR3": ["Vibra", "Vibra Energia"],
    "BRAV3": ["3R Petroleum"],
    
    # Mineração
    "VALE3": ["Vale"],
    "CSNA3": ["CSN", "Siderúrgica Nacional"],
    "GGBR4": ["Gerdau"],
    "USIM5": ["Usiminas"],
    
    # Bancos
    "ITUB4": ["Itaú", "Itau Unibanco"],
    "BBDC4": ["Bradesco"],
    "BBAS3": ["Banco do Brasil"],
    "SANB11": ["Santander Brasil"],
    "BPAC11": ["BTG Pactual"],
    
    # Varejo
    "MGLU3": ["Magazine Luiza", "Magalu"],
    "LREN3": ["Lojas Renner", "Renner"],
    "AMER3": ["Americanas"],
    "PCAR3": ["Pão de Açúcar", "GPA"],
    "ASAI3": ["Assaí"],
    "CEAB3": ["C&A Brasil"],
    
    # Telecomunicações
    "VIVT3": ["Vivo", "Telefônica Brasil"],
    "TIMS3": ["TIM Brasil", "TIM"],
    
    # Serviços
    "B3SA3": ["B3", "Bolsa Brasil"],
    "RENT3": ["Localiza"],
    "RAIL3": ["Rumo"],
    "ECOR3": ["EcoRodovias"],
    
    # Alimentos / Bebidas
    "ABEV3": ["Ambev"],
    "JBSS3": ["JBS"],
    "MRFG3": ["Marfrig"],
    "BEEF3": ["Minerva Foods"],
    
    # Tecnologia / Indústria
    "WEGE3": ["WEG"],
    "TOTS3": ["Totvs"],
    "POSI3": ["Positivo"],
    
    # Utilities
    "ELET3": ["Eletrobras"],
    "ELET6": ["Eletrobras"],
    "SBSP3": ["Sabesp"],
    "CPFE3": ["CPFL Energia"],
    "EQTL3": ["Equatorial"],
    "ENEV3": ["Eneva"],
    "ENGI11": ["Energisa"],
    "TAEE11": ["Taesa"],
    "CMIG4": ["Cemig"],
    "CPLE6": ["Copel"],
    
    # Saúde
    "HAPV3": ["Hapvida"],
    "RDOR3": ["Rede D'Or"],
    "FLRY3": ["Fleury"],
    "QUAL3": ["Qualicorp"],
    
    # Construção / Imóveis
    "CYRE3": ["Cyrela"],
    "MRVE3": ["MRV"],
    "EZTC3": ["EZTEC"],
    "EVEN3": ["Even"],
    
    # Educação
    "COGN3": ["Cogna"],
    "YDUQ3": ["Yduqs"],
    "ANIM3": ["Ânima Educação"],
    
    # Outros
    "CVCB3": ["CVC"],
    "SUZB3": ["Suzano"],
    "KLBN11": ["Klabin"],
    "ITSA4": ["Itaúsa"],
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


def buscar_noticias_individual(ticker, data_inicio, data_fim, max_items=10):
    """
    Busca notícias de um ticker específico.
    
    Args:
        ticker: Código do ticker
        data_inicio: Data início no formato YYYY-MM-DD
        data_fim: Data fim no formato YYYY-MM-DD
        max_items: Número máximo de artigos

    Returns:
        Lista de artigos
    """
    try:
        er = EventRegistry(apiKey=EVENT_REGISTRY_API_KEY)
        
        # Buscar pelo ticker e nome da empresa se disponível
        termos = TICKER_NOMES.get(ticker, [ticker])
        if ticker not in termos:
            termos.append(ticker)
        
        # Usar o primeiro termo (mais relevante)
        keyword = termos[0] if termos else ticker
        
        query = {
            "$query": {
                "$and": [
                    {
                        "keyword": keyword,
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

        return artigos

    except Exception as e:
        return []


def buscar_noticias_todos_tickers(tickers, data_inicio, data_fim, limite_tickers=100):
    """
    Busca notícias de todos os tickers individualmente.
    Limitado aos top N tickers para otimizar tempo.

    Args:
        tickers: Lista completa de tickers (já ordenada por importância)
        data_inicio: Data início no formato YYYY-MM-DD
        data_fim: Data fim no formato YYYY-MM-DD
        limite_tickers: Número máximo de tickers a processar

    Returns:
        Dicionário {ticker: [lista de artigos]}
    """
    # Limitar aos top tickers
    tickers_limitados = tickers[:limite_tickers]
    
    resultado_final = {}
    total = len(tickers_limitados)

    print(f"\n📰 Buscando notícias de {total} tickers (top {limite_tickers} mais negociados)...")

    for i, ticker in enumerate(tickers_limitados):
        try:
            artigos = buscar_noticias_individual(ticker, data_inicio, data_fim)
            resultado_final[ticker] = artigos
            
            if artigos:
                print(f"  [{i+1}/{total}] ✓ {ticker}: {len(artigos)} notícias")
            
            # Log de progresso a cada 20 tickers
            if (i + 1) % 20 == 0:
                tickers_com_noticias = sum(1 for t in resultado_final if resultado_final[t])
                print(f"  → Progresso: {i+1}/{total} processados, {tickers_com_noticias} com notícias")
                
        except Exception as e:
            print(f"  [{i+1}/{total}] ✗ {ticker}: {e}")
            resultado_final[ticker] = []
            continue

    # Resumo final
    tickers_com_noticias = sum(1 for t in resultado_final if resultado_final[t])
    total_noticias = sum(len(v) for v in resultado_final.values())
    print(f"\n✅ Busca concluída: {tickers_com_noticias} tickers com notícias ({total_noticias} artigos)")

    return resultado_final
