"""
Script principal do TradingCore.
Processa todos os usuários e envia análises diárias.

OTIMIZADO: Processa cada ticker apenas uma vez, reutilizando
análises para múltiplos usuários que compartilham os mesmos tickers.
"""
from src.config import validar_configuracoes
from src.utils import calcular_periodo_24h, parsear_tickers, extrair_tickers_unicos
from src.sheets_client import carregar_usuarios_sheets
from src.news_fetcher import buscar_noticias
from src.ai_analyzer import (
    analisar_com_gpt,
    filtrar_top_relevantes,
    gerar_resumo_executivo
)
from src.email_sender import gerar_email_html, enviar_email


def processar_todos_tickers(tickers_unicos, data_inicio, data_fim):
    """
    Processa todos os tickers únicos uma única vez.
    
    Args:
        tickers_unicos: Set de tickers únicos
        data_inicio: Data início da busca
        data_fim: Data fim da busca
        
    Returns:
        Tupla (cache_analises, cache_resumos):
            - cache_analises: {ticker: lista_de_analises}
            - cache_resumos: {ticker: resumo_executivo_texto}
    """
    cache_analises = {}
    cache_resumos = {}
    total_tickers = len(tickers_unicos)
    
    print(f"\n{'='*60}")
    print(f"📊 FASE 1: PROCESSANDO {total_tickers} TICKERS ÚNICOS")
    print(f"{'='*60}")
    
    for idx, ticker in enumerate(sorted(tickers_unicos), 1):
        try:
            print(f"\n[{idx}/{total_tickers}] Processando {ticker}...")
            
            # Buscar notícias (1x por ticker)
            artigos = buscar_noticias(ticker, data_inicio, data_fim)
            
            if not artigos:
                print(f"  ⚠ {ticker}: Nenhuma notícia encontrada")
                cache_analises[ticker] = []
                continue
            
            # Analisar com GPT (1x por ticker)
            analises = analisar_com_gpt(artigos, ticker)
            
            if not analises:
                print(f"  ⚠ {ticker}: Nenhuma análise gerada")
                cache_analises[ticker] = []
                continue
            
            # Filtrar top relevantes
            top_analises = filtrar_top_relevantes(analises)
            
            print(f"  ✓ {ticker}: {len(top_analises)} notícias relevantes selecionadas")
            
            # Armazenar no cache
            cache_analises[ticker] = top_analises
            
        except Exception as e:
            print(f"  ✗ Erro ao processar {ticker}: {e}")
            cache_analises[ticker] = []
            continue
    
    # =========================================================
    # Gerar resumos executivos (1x por ticker com notícias)
    # =========================================================
    print(f"\n{'='*60}")
    print(f"📝 GERANDO RESUMOS EXECUTIVOS")
    print(f"{'='*60}")
    
    for ticker, analises in cache_analises.items():
        if analises:
            # Gera resumo executivo para este ticker (1x)
            resumo = gerar_resumo_executivo(analises)
            cache_resumos[ticker] = resumo.get(ticker, "")
    
    # Resumo da fase 1
    tickers_com_noticias = sum(1 for t, a in cache_analises.items() if a)
    total_noticias_cache = sum(len(a) for a in cache_analises.values())
    
    print(f"\n{'='*60}")
    print(f"✓ FASE 1 CONCLUÍDA")
    print(f"  Tickers processados: {total_tickers}")
    print(f"  Tickers com notícias: {tickers_com_noticias}")
    print(f"  Resumos executivos gerados: {len(cache_resumos)}")
    print(f"  Total de análises em cache: {total_noticias_cache}")
    print(f"{'='*60}")
    
    return cache_analises, cache_resumos


def processar_usuario(usuario_dict, cache_analises, cache_resumos):
    """
    Processa um único usuário usando os caches de análises e resumos.
    
    Args:
        usuario_dict: Dicionário com dados do usuário
        cache_analises: Dicionário {ticker: lista_de_analises}
        cache_resumos: Dicionário {ticker: resumo_executivo_texto}
        
    Returns:
        Tupla (sucesso: bool, num_noticias: int)
    """
    nome = usuario_dict.get('Qual seu nome completo?', 'N/A')
    email = usuario_dict.get('Qual seu e-mail?', '')
    ticker_str = usuario_dict.get('Ticker 1', '')

    print(f"\n  Processando: {nome} ({email})")

    # Validar email
    if not email or '@' not in email:
        print(f"    ✗ Email inválido: {email}")
        return False, 0

    # Parsear tickers do usuário
    tickers = parsear_tickers(ticker_str)
    if not tickers:
        print(f"    ⚠ Nenhum ticker encontrado")
        html = gerar_email_html(usuario_dict, [], {})
        enviar_email(email, "TradingCore - Análise Diária", html)
        return True, 0

    print(f"    Tickers: {', '.join(tickers)}")
    
    # Coletar análises do cache para os tickers do usuário
    todas_analises = []
    for ticker in tickers:
        analises_ticker = cache_analises.get(ticker, [])
        todas_analises.extend(analises_ticker)

    # Coletar resumos executivos do cache (sem nova chamada API!)
    resumo_executivo = {}
    for ticker in tickers:
        if ticker in cache_resumos and cache_resumos[ticker]:
            resumo_executivo[ticker] = cache_resumos[ticker]

    # Gerar e enviar email
    try:
        html = gerar_email_html(usuario_dict, todas_analises, resumo_executivo)

        sucesso = enviar_email(
            email,
            f"TradingCore - Análise Diária ({len(todas_analises)} notícias)",
            html
        )

        if sucesso:
            print(f"    ✓ Email enviado! {len(todas_analises)} notícias")

        return sucesso, len(todas_analises)

    except Exception as e:
        print(f"    ✗ Erro ao enviar email: {e}")
        return False, len(todas_analises)


def main():
    """Função principal que executa o processamento completo."""
    print("\n" + "="*60)
    print("🚀 TRADINGCORE - INICIANDO PROCESSAMENTO")
    print("="*60)

    # Validar configurações
    try:
        validar_configuracoes()
    except ValueError as e:
        print(f"\n✗ {e}")
        return

    # Calcular período
    data_inicio, data_fim = calcular_periodo_24h()
    print(f"\n📅 Período: {data_inicio} a {data_fim}")

    # Carregar usuários
    print(f"\n📊 Carregando usuários...")
    df_usuarios = carregar_usuarios_sheets()

    if df_usuarios.empty:
        print("✗ Nenhum usuário encontrado!")
        return

    print(f"✓ {len(df_usuarios)} usuários carregados")

    # =========================================================
    # FASE 1: Extrair e processar tickers únicos
    # =========================================================
    tickers_unicos = extrair_tickers_unicos(df_usuarios)
    
    if not tickers_unicos:
        print("✗ Nenhum ticker encontrado em nenhum usuário!")
        return
    
    print(f"✓ {len(tickers_unicos)} tickers únicos identificados: {', '.join(sorted(tickers_unicos))}")
    
    # Processar todos os tickers uma única vez
    cache_analises, cache_resumos = processar_todos_tickers(tickers_unicos, data_inicio, data_fim)

    # =========================================================
    # FASE 2: Distribuir análises para cada usuário
    # =========================================================
    print(f"\n{'='*60}")
    print(f"📧 FASE 2: ENVIANDO EMAILS PARA {len(df_usuarios)} USUÁRIOS")
    print(f"{'='*60}")

    # Estatísticas
    total_usuarios = len(df_usuarios)
    usuarios_sucesso = 0
    usuarios_erro = 0
    total_noticias = 0

    # Processar cada usuário usando os caches (sem novas chamadas API!)
    for idx, row in df_usuarios.iterrows():
        try:
            usuario_dict = row.to_dict()
            sucesso, num_noticias = processar_usuario(usuario_dict, cache_analises, cache_resumos)

            if sucesso:
                usuarios_sucesso += 1
                total_noticias += num_noticias
            else:
                usuarios_erro += 1

        except Exception as e:
            print(f"\n✗ Erro crítico ao processar usuário {idx}: {e}")
            usuarios_erro += 1
            continue

    # Resumo final
    print("\n" + "="*60)
    print("📊 RESUMO DO PROCESSAMENTO")
    print("="*60)
    print(f"Tickers únicos processados: {len(tickers_unicos)}")
    print(f"Total de usuários: {total_usuarios}")
    print(f"✓ Sucesso: {usuarios_sucesso}")
    print(f"✗ Erro: {usuarios_erro}")
    print(f"📰 Total de notícias enviadas: {total_noticias}")
    print(f"📈 Média de notícias por usuário: {total_noticias/max(usuarios_sucesso,1):.1f}")
    print("="*60)
    print("✅ PROCESSAMENTO CONCLUÍDO!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
