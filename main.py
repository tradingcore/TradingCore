"""
Script principal do TradingCore.
Processa todos os usuários e envia análises diárias.
"""
from src.config import validar_configuracoes
from src.utils import calcular_periodo_24h, parsear_tickers
from src.sheets_client import carregar_usuarios_sheets
from src.news_fetcher import buscar_noticias
from src.ai_analyzer import (
    analisar_com_gpt,
    filtrar_top_relevantes,
    gerar_resumo_executivo
)
from src.email_sender import gerar_email_html, enviar_email


def processar_usuario(usuario_dict, data_inicio, data_fim):
    """
    Processa um único usuário: busca notícias, analisa e envia email.

    Args:
        usuario_dict: Dicionário com dados do usuário
        data_inicio: Data início da busca
        data_fim: Data fim da busca

    Returns:
        Tupla (sucesso: bool, num_noticias: int)
    """
    nome = usuario_dict.get('Qual seu nome completo?', 'N/A')
    email = usuario_dict.get('Qual seu e-mail?', '')
    ticker_str = usuario_dict.get('Ticker 1', '')

    print(f"\n{'='*60}")
    print(f"Processando: {nome} ({email})")
    print(f"{'='*60}")

    # Validar email
    if not email or '@' not in email:
        print(f"  ✗ Email inválido: {email}")
        return False, 0

    # Parsear tickers
    tickers = parsear_tickers(ticker_str)
    if not tickers:
        print(f"  ⚠ Nenhum ticker encontrado para {nome}")
        html = gerar_email_html(usuario_dict, [], {})
        enviar_email(email, "TradingCore - Análise Diária", html)
        return True, 0

    print(f"  Tickers: {', '.join(tickers)}")
    todas_analises = []

    # Processar cada ticker
    for ticker in tickers:
        try:
            print(f"\n  Processando {ticker}...")

            # Buscar notícias
            artigos = buscar_noticias(ticker, data_inicio, data_fim)

            if not artigos:
                print(f"  ⚠ {ticker}: Nenhuma notícia encontrada")
                continue

            # Analisar com GPT
            analises = analisar_com_gpt(artigos, ticker)

            if not analises:
                print(f"  ⚠ {ticker}: Nenhuma análise gerada")
                continue

            # Filtrar top relevantes
            top_analises = filtrar_top_relevantes(analises)

            print(f"  ✓ {ticker}: {len(top_analises)} notícias relevantes selecionadas")

            todas_analises.extend(top_analises)

        except Exception as e:
            print(f"  ✗ Erro ao processar {ticker}: {e}")
            continue

    # Gerar resumo executivo (2ª chamada ao GPT)
    resumo_executivo = {}
    if todas_analises:
        print(f"\n  Gerando resumo executivo...")
        resumo_executivo = gerar_resumo_executivo(todas_analises)

    # Gerar e enviar email
    try:
        print(f"\n  Gerando email...")
        html = gerar_email_html(usuario_dict, todas_analises, resumo_executivo)

        sucesso = enviar_email(
            email,
            f"TradingCore - Análise Diária ({len(todas_analises)} notícias)",
            html
        )

        if sucesso:
            print(f"  ✓ Processamento completo! {len(todas_analises)} notícias enviadas")

        return sucesso, len(todas_analises)

    except Exception as e:
        print(f"  ✗ Erro ao enviar email: {e}")
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

    # Estatísticas
    total_usuarios = len(df_usuarios)
    usuarios_sucesso = 0
    usuarios_erro = 0
    total_noticias = 0

    # Processar cada usuário
    for idx, row in df_usuarios.iterrows():
        try:
            usuario_dict = row.to_dict()
            sucesso, num_noticias = processar_usuario(
                usuario_dict, data_inicio, data_fim
            )

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

