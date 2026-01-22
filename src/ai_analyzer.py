"""
Módulo para análise de notícias usando OpenAI GPT.
Otimizado com análise em batch para reduzir chamadas de API.
"""
import json
import requests
from .config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_TEMPERATURE,
    TOP_N_RELEVANTES
)

# Tamanho do batch para análise
BATCH_SIZE_ANALISE = 5


def _limpar_json_response(conteudo):
    """Remove markdown code blocks e limpa resposta JSON."""
    conteudo = conteudo.strip()
    if conteudo.startswith("```"):
        partes = conteudo.split("```")
        if len(partes) >= 2:
            conteudo = partes[1]
            if conteudo.startswith("json"):
                conteudo = conteudo[4:]
            conteudo = conteudo.strip()
    return conteudo


def analisar_com_gpt(artigos, ticker, contexto=None):
    """
    Analisa lista de artigos usando OpenAI GPT, considerando o contexto estratégico.
    Mantida para compatibilidade - usa a versão batch internamente.

    Args:
        artigos: Lista de dicionários de artigos
        ticker: Ticker sendo analisado
        contexto: Texto com a tese estratégica da empresa

    Returns:
        Lista de dicionários com análises
    """
    return analisar_noticias_batch(artigos, ticker, contexto)


def analisar_noticias_batch(artigos, ticker, contexto=None, batch_size=None):
    """
    Analisa múltiplas notícias em batches para reduzir chamadas de API.
    
    Args:
        artigos: Lista de dicionários de artigos
        ticker: Ticker sendo analisado
        contexto: Texto com a tese estratégica da empresa
        batch_size: Número de notícias por chamada (default: BATCH_SIZE_ANALISE)

    Returns:
        Lista de dicionários com análises
    """
    if not artigos:
        return []

    if batch_size is None:
        batch_size = BATCH_SIZE_ANALISE

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }

    contexto_str = f"\nCONTEXTO ESTRATÉGICO DA EMPRESA:\n{contexto}\n" if contexto else ""
    todas_analises = []

    # Processar em batches
    for i in range(0, len(artigos), batch_size):
        batch = artigos[i:i + batch_size]
        
        # Preparar notícias do batch
        noticias_formatadas = []
        titulos_batch = []
        
        for idx, artigo in enumerate(batch):
            body = artigo.get('body', '')[:2000]  # Limite por notícia
            titulo = artigo.get('title', 'Sem título')
            
            if not body:
                continue
            
            titulos_batch.append(titulo)
            noticias_formatadas.append(f"""
NOTÍCIA {idx + 1}:
Título: {titulo}
Texto: {body}
""")
        
        if not noticias_formatadas:
            continue

        noticias_texto = "\n---\n".join(noticias_formatadas)

        prompt = f"""Você é um analista sênior de ações da B3.
Sua tarefa é analisar as {len(noticias_formatadas)} notícias abaixo e determinar sua relevância para investidores de {ticker}.
{contexto_str}
Analise cada notícia considerando se ela impacta os KPIs ou a tese de investimento.

{noticias_texto}

Responda EXCLUSIVAMENTE em JSON, com um array de análises na mesma ordem das notícias:

{{
  "analises": [
    {{
      "noticia_idx": 1,
      "relevante": true ou false,
      "relevancia_score": número de 0 a 10 (10 = impacto crítico, 0 = ruído),
      "resumo": "resuma em 1-2 frases o impacto real para {ticker}",
      "sentimento": número entre -1 e 1 (-1=muito negativo, 0=neutro, 1=muito positivo)
    }},
    ...
  ]
}}

Não escreva nada fora do JSON. Retorne exatamente {len(noticias_formatadas)} análises."""

        try:
            data = {
                "model": OPENAI_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": OPENAI_TEMPERATURE,
            }

            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            response_json = response.json()

            conteudo = response_json["choices"][0]["message"]["content"]
            conteudo = _limpar_json_response(conteudo)

            resultado = json.loads(conteudo)
            analises_batch = resultado.get('analises', [])

            # Adicionar metadados
            for analise in analises_batch:
                idx = analise.get('noticia_idx', 1) - 1
                if 0 <= idx < len(titulos_batch):
                    analise['titulo'] = titulos_batch[idx]
                analise['ticker'] = ticker
                todas_analises.append(analise)

        except json.JSONDecodeError as e:
            print(f"  ⚠ Erro ao parsear JSON do batch: {e}")
            # Fallback: processar individualmente
            for artigo in batch:
                analise = _analisar_artigo_individual(artigo, ticker, contexto)
                if analise:
                    todas_analises.append(analise)
        except Exception as e:
            print(f"  ⚠ Erro ao analisar batch: {e}")
            continue

    print(f"  ✓ {ticker}: {len(todas_analises)} artigos analisados")
    return todas_analises


def _analisar_artigo_individual(artigo, ticker, contexto=None):
    """Fallback para analisar um artigo individualmente."""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }

    try:
        body = artigo.get('body', '')[:3000]
        titulo = artigo.get('title', 'Sem título')

        if not body:
            return None

        contexto_str = f"\nCONTEXTO ESTRATÉGICO DA EMPRESA:\n{contexto}\n" if contexto else ""

        prompt = f"""
Você é um analista sênior de ações da B3.
Sua tarefa é analisar se a notícia abaixo é relevante para um investidor de {ticker}.
{contexto_str}
Analise a notícia considerando se ela impacta os KPIs ou a tese de investimento citada no contexto.

Notícia:
\"\"\"{body}\"\"\"

Responda EXCLUSIVAMENTE em JSON, no seguinte formato:

{{
  "relevante": true ou false (se é realmente impactante para a tese de {ticker}),
  "relevancia_score": número de 0 a 10 (onde 10 é impacto crítico na tese e 0 é ruído),
  "resumo": "resuma em 1-2 frases o impacto real para {ticker} baseado no contexto",
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
        response.raise_for_status()
        response_json = response.json()

        conteudo = response_json["choices"][0]["message"]["content"]
        conteudo = _limpar_json_response(conteudo)

        resultado = json.loads(conteudo)
        resultado['titulo'] = titulo
        resultado['ticker'] = ticker

        return resultado

    except Exception as e:
        print(f"  ⚠ Erro ao analisar artigo '{titulo[:30]}...': {e}")
        return None


def filtrar_top_relevantes(analises, top_n=None):
    """
    Filtra e retorna as top N análises mais relevantes.
    Agora prioriza o relevancia_score sobre o sentimento absoluto.
    """
    if top_n is None:
        top_n = TOP_N_RELEVANTES

    # Filtra apenas o que a IA marcou como relevante
    relevantes = [a for a in analises if a.get('relevante', False)]
    
    # Ordena primariamente por score de relevância e secundariamente por força do sentimento
    relevantes_ordenadas = sorted(
        relevantes,
        key=lambda x: (x.get('relevancia_score', 0), abs(x.get('sentimento', 0))),
        reverse=True
    )

    return relevantes_ordenadas[:top_n]


def gerar_resumo_executivo(analises_agrupadas, contexto=None):
    """
    Gera resumo executivo compacto para cada ticker, considerando o contexto estratégico.

    Args:
        analises_agrupadas: Lista de análises filtradas
        contexto: Dicionário {ticker: contexto_texto}

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

            ctx_ticker = contexto.get(ticker, "") if contexto else ""
            ctx_str = f"\nConsidere este contexto da empresa:\n{ctx_ticker}\n" if ctx_ticker else ""

            prompt = f"""Você é um analista sênior de ações. 
Compile as notícias abaixo sobre {ticker} em um resumo executivo MUITO compacto de no máximo 2 linhas.
{ctx_str}
Foque no que é realmente estrutural para a tese de investimento, ignorando ruídos passageiros.

Notícias:
{noticias_texto}

Responda apenas com o resumo de 2 linhas, sem formatação adicional."""

            data = {
                "model": OPENAI_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": OPENAI_TEMPERATURE,
            }

            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            response_json = response.json()

            resumo = response_json["choices"][0]["message"]["content"].strip()
            resumos_executivos[ticker] = resumo

            print(f"  ✓ Resumo executivo gerado para {ticker}")

        except Exception as e:
            print(f"  ⚠ Erro ao gerar resumo executivo de {ticker}: {e}")
            resumos_executivos[ticker] = "Resumo não disponível."

    return resumos_executivos


def gerar_analise_consolidada(analises_por_ticker, contexto=None):
    """
    Gera análise consolidada dividida em blocos positivos e negativos.
    
    Args:
        analises_por_ticker: Dict {ticker: [lista_de_analises]}
        contexto: Dict {ticker: contexto_texto}
    
    Returns:
        Dict {ticker: {'positivo': str, 'negativo': str}}
    """
    if not analises_por_ticker:
        return {}
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }
    
    analises_consolidadas = {}
    
    for ticker, analises in analises_por_ticker.items():
        if not analises:
            continue
        
        try:
            # Separar notícias por sentimento
            positivas = [a for a in analises if a.get('sentimento', 0) > 0]
            negativas = [a for a in analises if a.get('sentimento', 0) < 0]
            
            ctx_ticker = contexto.get(ticker, "") if contexto else ""
            ctx_str = f"\nContexto da empresa:\n{ctx_ticker}\n" if ctx_ticker else ""
            
            resultado = {'positivo': '', 'negativo': ''}
            
            # Consolidar notícias positivas
            if positivas:
                noticias_texto = "\n".join([
                    f"- {a.get('titulo', '')}: {a.get('resumo', '')}"
                    for a in positivas
                ])
                
                prompt = f"""Você é um analista sênior de ações.
Consolide as notícias POSITIVAS abaixo sobre {ticker} em um único bloco coeso.
{ctx_str}
Crie uma narrativa fluida (não liste bullet points) de até 10 linhas que:
- Integre os pontos principais sem repetir informações similares
- Destaque o impacto real para a tese de investimento
- Seja direta e informativa

Notícias:
{noticias_texto}

Responda apenas com o texto consolidado, sem título ou formatação."""

                data = {
                    "model": OPENAI_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": OPENAI_TEMPERATURE,
                }
                
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
                resultado['positivo'] = response.json()["choices"][0]["message"]["content"].strip()
            
            # Consolidar notícias negativas
            if negativas:
                noticias_texto = "\n".join([
                    f"- {a.get('titulo', '')}: {a.get('resumo', '')}"
                    for a in negativas
                ])
                
                prompt = f"""Você é um analista sênior de ações.
Consolide as notícias NEGATIVAS abaixo sobre {ticker} em um único bloco coeso.
{ctx_str}
Crie uma narrativa fluida (não liste bullet points) de até 10 linhas que:
- Integre os pontos principais sem repetir informações similares
- Destaque os riscos reais para a tese de investimento
- Seja direta e informativa

Notícias:
{noticias_texto}

Responda apenas com o texto consolidado, sem título ou formatação."""

                data = {
                    "model": OPENAI_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": OPENAI_TEMPERATURE,
                }
                
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
                resultado['negativo'] = response.json()["choices"][0]["message"]["content"].strip()
            
            if resultado['positivo'] or resultado['negativo']:
                analises_consolidadas[ticker] = resultado
                print(f"  ✓ Análise consolidada gerada para {ticker}")
        
        except Exception as e:
            print(f"  ⚠ Erro ao gerar análise consolidada de {ticker}: {e}")
            continue
    
    return analises_consolidadas


def gerar_analise_ticker_global(artigos, ticker):
    """
    Gera análise completa de um ticker para armazenamento global.
    Otimizado para processar todas as notícias de uma vez.
    
    Args:
        artigos: Lista de artigos do ticker
        ticker: Código do ticker
    
    Returns:
        Dict com análise completa ou None se não houver notícias relevantes
    """
    if not artigos:
        return None
    
    # Analisar todas as notícias em batch
    analises = analisar_noticias_batch(artigos, ticker)
    
    if not analises:
        return None
    
    # Filtrar relevantes
    relevantes = filtrar_top_relevantes(analises)
    
    if not relevantes:
        return None
    
    # Calcular sentimento médio
    sentimentos = [a.get('sentimento', 0) for a in relevantes]
    sentimento_medio = sum(sentimentos) / len(sentimentos) if sentimentos else 0
    
    # Determinar sentimento textual
    if sentimento_medio > 0.3:
        sentimento_texto = "Positivo"
    elif sentimento_medio < -0.3:
        sentimento_texto = "Negativo"
    else:
        sentimento_texto = "Neutro"
    
    # Separar por sentimento
    positivas = [a for a in relevantes if a.get('sentimento', 0) > 0]
    negativas = [a for a in relevantes if a.get('sentimento', 0) < 0]
    
    # Gerar consolidado
    consolidado = gerar_analise_consolidada({ticker: relevantes})
    
    # Extrair fontes
    fontes = []
    for a in relevantes[:5]:  # Top 5 fontes
        fontes.append({
            'titulo': a.get('titulo', ''),
            'resumo': a.get('resumo', '')
        })
    
    return {
        'ticker': ticker,
        'sentimento': sentimento_texto,
        'sentimento_score': round(sentimento_medio, 2),
        'positivo': consolidado.get(ticker, {}).get('positivo', ''),
        'negativo': consolidado.get(ticker, {}).get('negativo', ''),
        'fontes': fontes,
        'total_noticias': len(artigos),
        'noticias_relevantes': len(relevantes)
    }
