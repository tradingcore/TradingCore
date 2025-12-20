"""
Módulo para geração e envio de emails HTML.
"""
import smtplib
import ssl
from email.message import EmailMessage
from .config import REMETENTE_EMAIL, REMETENTE_SENHA, SMTP_SERVER, SMTP_PORT
from .utils import formatar_timestamp


def gerar_email_html(usuario, analises_agrupadas, resumo_executivo=None, precos_dados=None, analises_consolidadas=None):
    """
    Gera HTML formatado para o email com as análises de notícias.

    Args:
        usuario: Dicionário com dados do usuário (nome, email, etc)
        analises_agrupadas: Lista de análises de todos os tickers
        resumo_executivo: Dicionário {ticker: resumo_compacto}
        precos_dados: Dicionário {ticker: {preco_fechamento, variacao_percentual, sucesso}}
        analises_consolidadas: Dicionário {ticker: {'positivo': str, 'negativo': str}}

    Returns:
        String com HTML formatado
    """
    nome = usuario.get('Qual seu nome completo?', 'Investidor')
    if resumo_executivo is None:
        resumo_executivo = {}
    if precos_dados is None:
        precos_dados = {}
    if analises_consolidadas is None:
        analises_consolidadas = {}

    def sentimento_info(valor):
        """Converte sentimento em emoji e cor."""
        if valor > 0.3:
            return "🟢", "#28a745", "Positivo"
        elif valor < -0.3:
            return "🔴", "#dc3545", "Negativo"
        else:
            return "🟡", "#ffc107", "Neutro"

    # Agrupa por ticker
    por_ticker = {}
    for analise in analises_agrupadas:
        ticker = analise.get('ticker', 'Unknown')
        if ticker not in por_ticker:
            por_ticker[ticker] = []
        por_ticker[ticker].append(analise)

    # Construir HTML
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 10px;
            background-color: #f4f4f4;
            -webkit-text-size-adjust: 100%;
        }}
        .container {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            width: 100%;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 10px 10px 0 0;
            margin: -20px -20px 15px -20px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 20px;
            word-wrap: break-word;
        }}
        .header p {{
            margin: 8px 0 0 0;
            font-size: 14px;
        }}
        .intro {{
            font-size: 14px;
            margin-bottom: 15px;
        }}
        .ticker-section {{
            margin: 15px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .ticker-title {{
            font-size: 18px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 12px;
        }}
        .noticia {{
            background: white;
            padding: 12px;
            margin: 10px 0;
            border-radius: 6px;
            border: 1px solid #e0e0e0;
        }}
        .noticia-titulo {{
            font-weight: bold;
            margin-bottom: 8px;
            color: #333;
            font-size: 14px;
            line-height: 1.4;
            word-wrap: break-word;
        }}
        .noticia-resumo {{
            margin-bottom: 10px;
            color: #666;
            font-size: 13px;
            line-height: 1.5;
        }}
        .noticia.consolidada {{
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 6px;
            border-left: 3px solid #667eea;
        }}
        .noticia.consolidada .noticia-titulo {{
            font-size: 15px;
            margin-bottom: 10px;
        }}
        .noticia.consolidada .noticia-resumo {{
            line-height: 1.7;
            text-align: justify;
        }}
        .sentimento {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: bold;
        }}
        .footer {{
            margin-top: 20px;
            padding-top: 15px;
            border-top: 2px solid #e0e0e0;
            font-size: 11px;
            color: #666;
            text-align: center;
        }}
        .no-news {{
            text-align: center;
            padding: 15px;
            color: #666;
            font-style: italic;
            font-size: 14px;
        }}
        .resumo-executivo {{
            background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            border: 2px solid #667eea;
        }}
        .resumo-executivo h2 {{
            color: #667eea;
            margin: 0 0 12px 0;
            font-size: 16px;
        }}
        .resumo-item {{
            padding: 10px 0;
            border-bottom: 1px solid #ddd;
        }}
        .resumo-item:last-child {{
            border-bottom: none;
        }}
        .resumo-ticker {{
            font-weight: bold;
            color: #333;
            font-size: 14px;
            margin-bottom: 5px;
        }}
        .preco-info {{
            display: inline-block;
            margin-left: 10px;
            font-size: 13px;
            font-weight: normal;
        }}
        .preco-valor {{
            color: #666;
        }}
        .variacao-positiva {{
            color: #28a745;
            font-weight: bold;
        }}
        .variacao-negativa {{
            color: #dc3545;
            font-weight: bold;
        }}
        .variacao-neutra {{
            color: #666;
            font-weight: bold;
        }}
        .resumo-texto {{
            color: #555;
            font-size: 13px;
            margin-top: 5px;
            line-height: 1.5;
        }}
        .section-title {{
            color: #667eea;
            margin: 20px 0 15px 0;
            font-size: 16px;
            font-weight: bold;
        }}
        @media only screen and (max-width: 600px) {{
            body {{
                padding: 5px;
            }}
            .container {{
                padding: 15px;
                border-radius: 8px;
            }}
            .header {{
                padding: 12px;
                margin: -15px -15px 12px -15px;
                border-radius: 8px 8px 0 0;
            }}
            .header h1 {{
                font-size: 18px;
            }}
            .ticker-section {{
                padding: 12px;
                margin: 12px 0;
            }}
            .ticker-title {{
                font-size: 16px;
            }}
            .noticia {{
                padding: 10px;
            }}
            .noticia-titulo {{
                font-size: 13px;
            }}
            .noticia-resumo {{
                font-size: 12px;
            }}
            .resumo-executivo {{
                padding: 12px;
            }}
            .resumo-executivo h2 {{
                font-size: 15px;
            }}
            .resumo-ticker {{
                font-size: 13px;
            }}
            .resumo-texto {{
                font-size: 12px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 TradingCore - Análise Diária</h1>
            <p>Olá, {nome}!</p>
        </div>

        <p class="intro">Aqui está o resumo das notícias mais relevantes sobre suas ações nas últimas 24 horas:</p>
"""

    # Adiciona seção de Resumo Executivo se houver
    if resumo_executivo:
        html += """
        <div class="resumo-executivo">
            <h2>📋 Resumo Executivo</h2>
"""
        for ticker, resumo in resumo_executivo.items():
            # Buscar dados de preço para este ticker
            preco_html = ""
            if ticker in precos_dados and precos_dados[ticker]['sucesso']:
                preco = precos_dados[ticker]['preco_fechamento']
                variacao = precos_dados[ticker]['variacao_percentual']
                
                # Determinar classe CSS baseado na variação
                if variacao > 0:
                    variacao_class = "variacao-positiva"
                    variacao_sinal = "+"
                elif variacao < 0:
                    variacao_class = "variacao-negativa"
                    variacao_sinal = ""
                else:
                    variacao_class = "variacao-neutra"
                    variacao_sinal = ""
                
                preco_html = f"""<span class="preco-info">
                    <span class="preco-valor">R$ {preco:.2f}</span> 
                    <span class="{variacao_class}">({variacao_sinal}{variacao:.2f}%)</span>
                </span>"""
            
            html += f"""
            <div class="resumo-item">
                <div class="resumo-ticker">{ticker}{preco_html}</div>
                <div class="resumo-texto">{resumo}</div>
            </div>
"""
        html += """
        </div>

        <h3 class="section-title">📰 Notícias Detalhadas</h3>
"""

    if not analises_agrupadas:
        html += """
        <div class="no-news">
            <p>😴 Nenhuma notícia relevante encontrada para seus tickers no período.</p>
        </div>
"""
    else:
        # Agrupar por ticker
        por_ticker = {}
        for analise in analises_agrupadas:
            ticker = analise.get('ticker', 'Unknown')
            if ticker not in por_ticker:
                por_ticker[ticker] = []
            por_ticker[ticker].append(analise)
        
        for ticker in por_ticker.keys():
            consolidado = analises_consolidadas.get(ticker, {})
            
            if not consolidado or (not consolidado.get('positivo') and not consolidado.get('negativo')):
                continue
            
            html += f"""
        <div class="ticker-section">
            <div class="ticker-title">{ticker}</div>
"""
            
            # Bloco Positivo
            if consolidado.get('positivo'):
                html += f"""
            <div class="noticia consolidada">
                <div class="noticia-titulo">🟢 Pontos Positivos</div>
                <div class="noticia-resumo">{consolidado['positivo']}</div>
            </div>
"""
            
            # Bloco Negativo
            if consolidado.get('negativo'):
                html += f"""
            <div class="noticia consolidada">
                <div class="noticia-titulo">🔴 Pontos de Atenção</div>
                <div class="noticia-resumo">{consolidado['negativo']}</div>
            </div>
"""
            
            html += """
        </div>
"""

    html += f"""
        <div class="footer">
            <p><strong>TradingCore</strong> - Sistema Automatizado de Análise de Notícias</p>
            <p>Este email foi gerado automaticamente. As análises são baseadas em IA e não constituem recomendação de investimento.</p>
            <p>Data: {formatar_timestamp()}</p>
        </div>
    </div>
</body>
</html>
"""

    return html


def enviar_email(destinatario, assunto, corpo_html):
    """
    Envia email via SMTP do Gmail.

    Args:
        destinatario: Email do destinatário
        assunto: Assunto do email
        corpo_html: Corpo do email em HTML

    Returns:
        True se enviado com sucesso, False caso contrário
    """
    try:
        msg = EmailMessage()
        msg.set_content("Por favor, visualize este email em um cliente que suporte HTML.")
        msg.add_alternative(corpo_html, subtype='html')
        msg['Subject'] = assunto
        msg['From'] = REMETENTE_EMAIL
        msg['To'] = destinatario

        context = ssl.create_default_context()

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(REMETENTE_EMAIL, REMETENTE_SENHA)
            server.send_message(msg)

        print(f"  ✓ Email enviado para {destinatario}")
        return True

    except Exception as e:
        print(f"  ✗ Erro ao enviar email para {destinatario}: {e}")
        return False

