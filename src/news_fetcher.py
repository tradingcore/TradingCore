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

        # Construir lista de keywords (nomes das empresas)
        keywords_list = []
        ticker_to_keyword = {}
        
        for ticker in tickers:
            # Usar nome da empresa se disponível, senão usar o ticker
            nome = TICKER_NOMES.get(ticker, [ticker])[0]
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
    Processa todas as 400 ações.

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
