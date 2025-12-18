"""
Módulo para análise de notícias usando OpenAI GPT.
"""
import json
import requests
from .config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_TEMPERATURE,
    TOP_N_RELEVANTES
)


def analisar_com_gpt(artigos, ticker):
    """
    Analisa lista de artigos usando OpenAI GPT.

    Args:
        artigos: Lista de dicionários de artigos
        ticker: Ticker sendo analisado

    Returns:
        Lista de dicionários com análises
    """
    if not artigos:
        return []

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }

    analises = []

    for artigo in artigos:
        try:
            body = artigo.get('body', '')
            titulo = artigo.get('title', 'Sem título')

            if not body:
                continue

            prompt = f"""
Você é um analista de ações da B3.
Analise o texto a seguir sobre {ticker}.

Texto:
\"\"\"{body}\"\"\"

Responda EXCLUSIVAMENTE em JSON, no seguinte formato:

{{
  "relevante": true ou false (se é relevante para investidores de {ticker}),
  "resumo": "resuma em 1-2 frases o principal do texto focado na ação {ticker}",
  "sentimento": número entre -1 e 1 (-1=muito negativo, 0=neutro, 1=muito positivo)
}}

Não escreva nada fora do JSON.
"""

            data = {
                "model": OPENAI_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": OPENAI_TEMPERATURE,
            }

            response = requests.post(url, headers=headers, json=data)
            response_json = response.json()

            conteudo = response_json["choices"][0]["message"]["content"]

            # Remove markdown code blocks se existirem
            conteudo = conteudo.strip()
            if conteudo.startswith("```"):
                conteudo = conteudo.split("```")[1]
                if conteudo.startswith("json"):
                    conteudo = conteudo[4:]
                conteudo = conteudo.strip()

            resultado = json.loads(conteudo)
            resultado['titulo'] = titulo
            resultado['ticker'] = ticker

            analises.append(resultado)

        except Exception as e:
            print(f"  ⚠ Erro ao analisar artigo: {e}")
            continue

    print(f"  ✓ {ticker}: {len(analises)} artigos analisados")
    return analises


def filtrar_top_relevantes(analises, top_n=None):
    """Filtra e retorna as top N análises mais relevantes."""
    if top_n is None:
        top_n = TOP_N_RELEVANTES

    relevantes = [a for a in analises if a.get('relevante', False)]
    relevantes_ordenadas = sorted(
        relevantes,
        key=lambda x: abs(x.get('sentimento', 0)),
        reverse=True
    )

    return relevantes_ordenadas[:top_n]


def gerar_resumo_executivo(analises_agrupadas):
    """
    Gera resumo executivo compacto para cada ticker.
    Segunda chamada ao GPT compilando as notícias já analisadas.

    Args:
        analises_agrupadas: Lista de análises com campo 'ticker' e 'resumo'

    Returns:
        Dicionário {ticker: resumo_compacto}
    """
    if not analises_agrupadas:
        return {}

    por_ticker = {}
    for analise in analises_agrupadas:
        ticker = analise.get('ticker', 'Unknown')
        if ticker not in por_ticker:
            por_ticker[ticker] = []
        por_ticker[ticker].append(analise.get('resumo', ''))

    resumos_executivos = {}
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }

    for ticker, resumos in por_ticker.items():
        try:
            noticias_texto = "\n".join([f"- {r}" for r in resumos if r])

            if not noticias_texto:
                continue

            prompt = f"""Você é um analista de ações. Compile as notícias abaixo sobre {ticker} em um resumo MUITO compacto de no máximo 2 linhas.
Foque no que é mais relevante para o investidor.

Notícias:
{noticias_texto}

Responda apenas com o resumo de 2 linhas, sem formatação adicional."""

            data = {
                "model": OPENAI_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": OPENAI_TEMPERATURE,
            }

            response = requests.post(url, headers=headers, json=data)
            response_json = response.json()

            resumo = response_json["choices"][0]["message"]["content"].strip()
            resumos_executivos[ticker] = resumo

            print(f"  ✓ Resumo executivo gerado para {ticker}")

        except Exception as e:
            print(f"  ⚠ Erro ao gerar resumo executivo de {ticker}: {e}")
            resumos_executivos[ticker] = "Resumo não disponível."

    return resumos_executivos

