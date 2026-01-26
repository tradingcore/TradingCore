"""
Script principal do TradingCore.
Processa empresas listadas na B3 e salva globalmente.
Depois distribui para cada usuário com base na sua carteira.

OTIMIZADO:
- Busca de notícias em batch (50 tickers por chamada)
- Análise de notícias em batch (5 notícias por chamada)
- Armazenamento global (não duplica por usuário)
- Usa apenas empresas listadas (1 ticker por empresa)
"""
from src.config import validar_configuracoes
from src.utils import calcular_periodo_24h, parsear_tickers
from src.firebase_client import (
    carregar_usuarios_firestore, 
    buscar_uid_por_email,
    salvar_noticia_global,
    buscar_noticias_globais
)
from src.news_fetcher import buscar_noticias_todos_tickers
from src.ai_analyzer import gerar_analise_ticker_global
from src.email_sender import gerar_email_html, enviar_email
from src.price_fetcher import buscar_precos_multiplos
from src.context_manager import carregar_contexto
from src.ticker_loader import carregar_tickers_listados


def carregar_tickers_b3():
    """Carrega tickers de empresas listadas (1 por empresa, priorizando final 3)."""
    tickers = carregar_tickers_listados()
    print(f"✓ {len(tickers)} tickers carregados (empresas listadas)")
    return tickers


def processar_noticias_globais(tickers, data_inicio, data_fim, data_referencia):
    """
    Processa notícias de todos os tickers e salva globalmente.
    
    Args:
        tickers: Lista de todos os tickers B3
        data_inicio: Data início da busca
        data_fim: Data fim da busca
        data_referencia: Data de referência para salvar (YYYY-MM-DD)
        
    Returns:
        Dict {ticker: dados_analise} com tickers que tiveram notícias
    """
    print(f"\n{'='*60}")
    print(f"📰 FASE 1: BUSCANDO NOTÍCIAS DE {len(tickers)} TICKERS")
    print(f"{'='*60}")
    
    # Buscar todas as notícias em batch
    noticias_por_ticker = buscar_noticias_todos_tickers(tickers, data_inicio, data_fim)
    
    # Contar tickers com notícias
    tickers_com_noticias = [t for t, artigos in noticias_por_ticker.items() if artigos]
    print(f"\n✓ {len(tickers_com_noticias)} tickers com notícias encontradas")
    
    if not tickers_com_noticias:
        print("⚠ Nenhuma notícia encontrada para nenhum ticker!")
        return {}
    
    print(f"\n{'='*60}")
    print(f"🤖 FASE 2: ANALISANDO {len(tickers_com_noticias)} TICKERS COM NOTÍCIAS")
    print(f"{'='*60}")
    
    # Analisar e salvar cada ticker
    analises_globais = {}
    processados = 0
    
    for ticker in tickers_com_noticias:
        artigos = noticias_por_ticker[ticker]
        processados += 1
        
        try:
            print(f"\n[{processados}/{len(tickers_com_noticias)}] Analisando {ticker} ({len(artigos)} artigos)...")
            
            # Carregar contexto estratégico (se disponível)
            contexto = carregar_contexto(ticker)
            if contexto:
                print(f"  📋 Contexto carregado para {ticker}")
            
            # Gerar análise completa (com contexto)
            analise = gerar_analise_ticker_global(artigos, ticker, contexto)
            
            if analise:
                # Salvar no Firebase globalmente
                salvar_noticia_global(data_referencia, ticker, analise)
                analises_globais[ticker] = analise
                print(f"  ✓ {ticker}: Análise salva ({analise.get('noticias_relevantes', 0)} relevantes)")
            else:
                print(f"  ⚠ {ticker}: Nenhuma notícia relevante")
                
        except Exception as e:
            print(f"  ✗ Erro ao processar {ticker}: {e}")
            continue
    
    print(f"\n{'='*60}")
    print(f"✓ FASE 2 CONCLUÍDA")
    print(f"  Tickers analisados: {len(tickers_com_noticias)}")
    print(f"  Análises salvas: {len(analises_globais)}")
    print(f"{'='*60}")
    
    return analises_globais


def enviar_emails_usuarios(data_referencia, periodo_noticias):
    """
    Envia emails para todos os usuários buscando notícias da coleção global.
    
    Args:
        data_referencia: Data de referência (YYYY-MM-DD)
        periodo_noticias: Tupla (data_inicio, data_fim)
    """
    print(f"\n{'='*60}")
    print(f"📧 FASE 3: ENVIANDO EMAILS")
    print(f"{'='*60}")
    
    # Carregar usuários
    print(f"\n📊 Carregando usuários...")
    df_usuarios = carregar_usuarios_firestore()
    
    if df_usuarios.empty:
        print("⚠ Nenhum usuário encontrado!")
        return
    
    print(f"✓ {len(df_usuarios)} usuários carregados")
    
    # Coletar todos os tickers dos usuários para buscar preços
    todos_tickers = set()
    for _, row in df_usuarios.iterrows():
        ticker_str = row.get('Ticker 1', '')
        tickers = parsear_tickers(ticker_str)
        todos_tickers.update(tickers)
    
    # Buscar preços
    print(f"\n💰 Buscando preços de {len(todos_tickers)} tickers...")
    precos_dados = buscar_precos_multiplos(todos_tickers)
    
    # Estatísticas
    usuarios_sucesso = 0
    usuarios_erro = 0
    total_noticias = 0
    
    # Processar cada usuário
    for idx, row in df_usuarios.iterrows():
        try:
            usuario_dict = row.to_dict()
            nome = usuario_dict.get('Qual seu nome completo?', 'N/A')
            email = usuario_dict.get('Qual seu e-mail?', '')
            ticker_str = usuario_dict.get('Ticker 1', '')
            
            print(f"\n  Processando: {nome} ({email})")
            
            # Validar email
            if not email or '@' not in email:
                print(f"    ✗ Email inválido")
                usuarios_erro += 1
                continue
            
            # Parsear tickers
            tickers = parsear_tickers(ticker_str)
            if not tickers:
                print(f"    ⚠ Nenhum ticker")
                html = gerar_email_html(usuario_dict, [], {}, {}, {})
                enviar_email(email, "TradingCore - Análise Diária", html)
                usuarios_sucesso += 1
                continue
            
            print(f"    Tickers: {', '.join(tickers)}")
            
            # Buscar notícias globais dos tickers do usuário
            noticias_usuario = buscar_noticias_globais(data_referencia, tickers)
            
            # Montar dados para o email
            todas_analises = []
            resumo_executivo = {}
            consolidadas_usuario = {}
            precos_usuario = {}
            
            for ticker in tickers:
                dados_ticker = noticias_usuario.get(ticker, {})
                precos_usuario[ticker] = precos_dados.get(ticker, {'sucesso': False})
                
                if dados_ticker:
                    # Resumo executivo (usar positivo + negativo resumidos)
                    resumo_parts = []
                    if dados_ticker.get('positivo'):
                        resumo_parts.append(dados_ticker['positivo'][:200])
                    if dados_ticker.get('negativo'):
                        resumo_parts.append(dados_ticker['negativo'][:200])
                    
                    if resumo_parts:
                        resumo_executivo[ticker] = " | ".join(resumo_parts)
                    
                    # Consolidadas
                    consolidadas_usuario[ticker] = {
                        'positivo': dados_ticker.get('positivo', ''),
                        'negativo': dados_ticker.get('negativo', '')
                    }
                    
                    # Adicionar fontes como "análises" para contagem
                    for fonte in dados_ticker.get('fontes', []):
                        todas_analises.append({
                            'titulo': fonte.get('titulo', ''),
                            'resumo': fonte.get('resumo', ''),
                            'ticker': ticker,
                            'relevante': True,
                            'sentimento': 0
                        })
            
            # Gerar e enviar email
            html = gerar_email_html(
                usuario_dict, 
                todas_analises, 
                resumo_executivo, 
                precos_usuario, 
                consolidadas_usuario, 
                periodo_noticias
            )
            
            sucesso = enviar_email(
                email,
                f"TradingCore - Análise Diária ({len(todas_analises)} notícias)",
                html
            )
            
            if sucesso:
                print(f"    ✓ Email enviado! {len(todas_analises)} notícias")
                usuarios_sucesso += 1
                total_noticias += len(todas_analises)
            else:
                usuarios_erro += 1
                
        except Exception as e:
            print(f"    ✗ Erro: {e}")
            usuarios_erro += 1
            continue
    
    # Resumo
    print(f"\n{'='*60}")
    print(f"📊 RESUMO DOS EMAILS")
    print(f"{'='*60}")
    print(f"✓ Sucesso: {usuarios_sucesso}")
    print(f"✗ Erro: {usuarios_erro}")
    print(f"📰 Total de notícias enviadas: {total_noticias}")
    print(f"{'='*60}")


def main():
    """Função principal que executa o processamento completo."""
    print("\n" + "="*60)
    print("🚀 TRADINGCORE - PROCESSAMENTO GLOBAL")
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
    
    # Data de referência para salvar (hoje)
    from datetime import datetime
    import pytz
    tz = pytz.timezone('America/Sao_Paulo')
    data_referencia = datetime.now(tz).strftime('%Y-%m-%d')
    print(f"📅 Data de referência: {data_referencia}")

    # =========================================================
    # FASE 1-2: Carregar tickers e processar notícias globais
    # =========================================================
    tickers_b3 = carregar_tickers_b3()
    
    if not tickers_b3:
        print("✗ Nenhum ticker B3 encontrado!")
        return
    
    # Processar todas as notícias e salvar globalmente
    analises_globais = processar_noticias_globais(
        tickers_b3, 
        data_inicio, 
        data_fim, 
        data_referencia
    )
    
    # =========================================================
    # FASE 3: Atualizar cotações no Firestore (para ticker tape e heatmap)
    # =========================================================
    print(f"\n{'='*60}")
    print(f"📈 ATUALIZANDO COTAÇÕES")
    print(f"{'='*60}")
    
    try:
        from src.market_data_updater import atualizar_cotacoes_mercado, atualizar_cotacoes_b3
        atualizar_cotacoes_mercado()
        atualizar_cotacoes_b3(set(tickers_b3))
    except Exception as e:
        print(f"⚠ Erro ao atualizar cotações: {e}")
    
    # =========================================================
    # FASE 4: Enviar emails para usuários
    # =========================================================
    periodo_noticias = (data_inicio, data_fim)
    enviar_emails_usuarios(data_referencia, periodo_noticias)
    
    # Resumo final
    print("\n" + "="*60)
    print("✅ PROCESSAMENTO GLOBAL CONCLUÍDO!")
    print(f"  Tickers B3 processados: {len(tickers_b3)}")
    print(f"  Análises globais salvas: {len(analises_globais)}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
