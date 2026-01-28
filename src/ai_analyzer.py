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
    TOP_N_RELEVANTES,
    FILTRO_ESPECIFICIDADE_BATCH_SIZE
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


def filtrar_noticias_especificas(artigos, ticker, nome_empresa=None):
    """
    Filtro 1: Descarta notícias genéricas de mercado antes da análise complexa.
    
    Este filtro é BARATO e RÁPIDO - usa prompt simples sem contexto estratégico.
    Objetivo: remover ruído como "Ibovespa sobe e beneficia bancos" antes de
    gastar tokens com análise profunda.
    
    Args:
        artigos: Lista de dicionários de artigos
        ticker: Ticker sendo analisado (ex: "BBDC4")
        nome_empresa: Nome da empresa (opcional, ex: "Bradesco")
    
    Returns:
        Lista de artigos que são específicos sobre a empresa/setor
    """
    if not artigos:
        return []
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }
    
    batch_size = FILTRO_ESPECIFICIDADE_BATCH_SIZE
    artigos_especificos = []
    
    # Nome para usar no prompt
    empresa_str = f" ({nome_empresa})" if nome_empresa else ""
    
    for i in range(0, len(artigos), batch_size):
        batch = artigos[i:i + batch_size]
        
        # Preparar notícias do batch (texto resumido para economizar tokens)
        noticias_formatadas = []
        artigos_batch = []
        
        for idx, artigo in enumerate(batch):
            titulo = artigo.get('title', 'Sem título')
            body = artigo.get('body', '')[:500]  # Apenas 500 chars para filtro rápido
            
            if not titulo and not body:
                continue
            
            artigos_batch.append(artigo)
            noticias_formatadas.append(f"""
NOTÍCIA {idx + 1}:
Título: {titulo}
Texto: {body}...
""")
        
        if not noticias_formatadas:
            continue
        
        noticias_texto = "\n---\n".join(noticias_formatadas)
        
        prompt = f"""Para cada notícia, RACIOCINE PASSO A PASSO antes de classificar para {ticker}{empresa_str}:

PERGUNTAS A RESPONDER PARA CADA NOTÍCIA:
1. Qual o FOCO PRINCIPAL da notícia? (qual empresa/tema é o assunto central?)
2. {ticker} é o ASSUNTO PRINCIPAL ou apenas MENCIONADA de passagem/em lista?
3. A notícia traz informação ESPECÍFICA sobre {ticker} (resultados, eventos, decisões, operações)?

REGRAS DE CLASSIFICAÇÃO:
- ESPECIFICA: {ticker} é o foco principal OU tem informação específica dela (resultados, CEO, operações, contratos)
- GENERICA: {ticker} só aparece em lista/ranking, é mencionada como exemplo, ou a notícia é sobre mercado/índices em geral

EXEMPLO DE RACIOCÍNIO:
Título: "Vale avança, enquanto Hapvida cai: veja os destaques do dia"
Analisando para DIRR3:
1. Foco: Vale e Hapvida são os assuntos principais do título
2. DIRR3: apenas mencionada numa lista de ações pressionadas no meio do texto
3. Informação específica: NÃO, só diz que "está pressionada" sem detalhes
→ GENERICA (mencionada em lista, sem informação específica sobre a empresa)

{noticias_texto}

Responda EXCLUSIVAMENTE em JSON:
{{
  "classificacoes": [
    {{
      "noticia_idx": 1,
      "raciocinio": "1. Foco: [tema central]. 2. {ticker}: [assunto principal/mencionada em lista]. 3. Info específica: [sim/não, qual]",
      "especifica": true ou false
    }},
    ...
  ]
}}

Retorne exatamente {len(noticias_formatadas)} classificações."""

        try:
            data = {
                "model": OPENAI_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,  # Baixa temperatura para classificação consistente
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            response_json = response.json()
            
            conteudo = response_json["choices"][0]["message"]["content"]
            conteudo = _limpar_json_response(conteudo)
            
            resultado = json.loads(conteudo)
            classificacoes = resultado.get('classificacoes', [])
            
            # Filtrar apenas específicas
            for classif in classificacoes:
                idx = classif.get('noticia_idx', 1) - 1
                if classif.get('especifica', False) and 0 <= idx < len(artigos_batch):
                    artigos_especificos.append(artigos_batch[idx])
        
        except Exception as e:
            print(f"  ⚠ Erro no filtro de especificidade: {e}")
            # Em caso de erro, passa todos os artigos do batch (fail-safe)
            artigos_especificos.extend(artigos_batch)
    
    return artigos_especificos


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

    contexto_str = f"""
SEU CONHECIMENTO PRÉVIO SOBRE A EMPRESA (use apenas como referência interna, NÃO inclua no output):
{contexto}
--- FIM DO CONHECIMENTO PRÉVIO ---
""" if contexto else ""
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
{contexto_str}
REGRA CRÍTICA: Seu output deve ser EXCLUSIVAMENTE sobre o conteúdo das notícias abaixo.
O conhecimento prévio serve apenas para você entender a relevância - NÃO copie, resuma ou mencione dados do conhecimento prévio no seu output.
Analise APENAS o que está escrito nas notícias.

Sua tarefa é analisar as {len(noticias_formatadas)} notícias abaixo e determinar sua relevância para investidores de {ticker}.

{noticias_texto}

Responda EXCLUSIVAMENTE em JSON, com um array de análises na mesma ordem das notícias:

{{
  "analises": [
    {{
      "noticia_idx": 1,
      "relevante": true ou false,
      "relevancia_score": número de 0 a 10 (10 = impacto crítico, 0 = ruído),
      "resumo": "resuma em 1-2 frases o que A NOTÍCIA diz e seu impacto para {ticker} (baseado APENAS no texto da notícia)",
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

        contexto_str = f"""
SEU CONHECIMENTO PRÉVIO SOBRE A EMPRESA (use apenas como referência interna, NÃO inclua no output):
{contexto}
--- FIM DO CONHECIMENTO PRÉVIO ---
""" if contexto else ""

        prompt = f"""
Você é um analista sênior de ações da B3.
{contexto_str}
REGRA CRÍTICA: Seu output deve ser EXCLUSIVAMENTE sobre o conteúdo da notícia abaixo.
O conhecimento prévio serve apenas para você entender a relevância - NÃO copie, resuma ou mencione dados do conhecimento prévio no seu output.

Sua tarefa é analisar se a notícia abaixo é relevante para um investidor de {ticker}.

Notícia:
\"\"\"{body}\"\"\"

Responda EXCLUSIVAMENTE em JSON, no seguinte formato:

{{
  "relevante": true ou false (se é realmente impactante para {ticker}),
  "relevancia_score": número de 0 a 10 (onde 10 é impacto crítico e 0 é ruído),
  "resumo": "resuma em 1-2 frases o que A NOTÍCIA diz e seu impacto (baseado APENAS no texto da notícia)",
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
            ctx_str = f"""
SEU CONHECIMENTO PRÉVIO (use apenas como referência, NÃO inclua no output):
{ctx_ticker}
--- FIM DO CONHECIMENTO PRÉVIO ---
""" if ctx_ticker else ""

            prompt = f"""Você é um analista sênior de ações.
{ctx_str}
REGRA CRÍTICA: O resumo deve conter APENAS informações das notícias abaixo.
NÃO inclua números, dados ou informações do seu conhecimento prévio.

Compile as notícias abaixo sobre {ticker} em um resumo executivo MUITO compacto de no máximo 2 linhas.
Use APENAS o conteúdo das notícias.

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
            ctx_str = f"""
SEU CONHECIMENTO PRÉVIO (use apenas como referência, NÃO inclua no output):
{ctx_ticker}
--- FIM DO CONHECIMENTO PRÉVIO ---
""" if ctx_ticker else ""
            
            resultado = {'positivo': '', 'negativo': ''}
            
            # Consolidar notícias positivas
            if positivas:
                noticias_texto = "\n".join([
                    f"- {a.get('titulo', '')}: {a.get('resumo', '')}"
                    for a in positivas
                ])
                
                prompt = f"""Você é um analista sênior de ações.
{ctx_str}
REGRA CRÍTICA: Escreva APENAS sobre o que está nas notícias abaixo.
NÃO inclua números, dados ou informações do seu conhecimento prévio no texto.
O conhecimento prévio serve apenas para você entender a relevância, não para ser incluído.

Consolide as notícias POSITIVAS abaixo sobre {ticker} em um único bloco coeso.
Crie uma narrativa fluida (não liste bullet points) de até 10 linhas que:
- Integre os pontos principais DAS NOTÍCIAS sem repetir informações similares
- Seja direta e informativa
- Use APENAS informações que estão nas notícias

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
{ctx_str}
REGRA CRÍTICA: Escreva APENAS sobre o que está nas notícias abaixo.
NÃO inclua números, dados ou informações do seu conhecimento prévio no texto.
O conhecimento prévio serve apenas para você entender a relevância, não para ser incluído.

Consolide as notícias NEGATIVAS abaixo sobre {ticker} em um único bloco coeso.
Crie uma narrativa fluida (não liste bullet points) de até 10 linhas que:
- Integre os pontos principais DAS NOTÍCIAS sem repetir informações similares
- Seja direta e informativa
- Use APENAS informações que estão nas notícias

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


def gerar_analise_ticker_global(artigos, ticker, contexto=None):
    """
    Gera análise completa de um ticker para armazenamento global.
    Usa filtro duplo:
    1. Filtro de especificidade (barato, sem contexto) - descarta notícias genéricas
    2. Análise completa (com contexto estratégico) - analisa notícias específicas
    
    Args:
        artigos: Lista de artigos do ticker
        ticker: Código do ticker
        contexto: Texto com contexto estratégico da empresa (opcional)
    
    Returns:
        Dict com análise completa ou None se não houver notícias relevantes
    """
    if not artigos:
        return None
    
    # FILTRO 1: Descartar notícias genéricas de mercado (barato, sem contexto)
    artigos_especificos = filtrar_noticias_especificas(artigos, ticker)
    
    descartadas = len(artigos) - len(artigos_especificos)
    if descartadas > 0:
        print(f"  🔍 Filtro especificidade: {len(artigos)} → {len(artigos_especificos)} ({descartadas} genéricas descartadas)")
    
    if not artigos_especificos:
        print(f"  ⚠ {ticker}: Todas as notícias eram genéricas de mercado")
        return None
    
    # FILTRO 2: Análise completa com contexto estratégico (caro)
    analises = analisar_noticias_batch(artigos_especificos, ticker, contexto)
    
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
    
    # Gerar consolidado (com contexto)
    contexto_dict = {ticker: contexto} if contexto else None
    consolidado = gerar_analise_consolidada({ticker: relevantes}, contexto_dict)
    
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
