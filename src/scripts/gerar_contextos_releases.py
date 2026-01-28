"""
Gera contextos completos das ações usando o release mais recente (PDF) da CVM.
Salva um JSON por ticker em src/contexts.

Uso: python src/scripts/gerar_contextos_releases.py [--limit N] [--ticker PETR3] [--force]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
import requests
from pypdf import PdfReader

from src.config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE
from src.ticker_loader import carregar_dados_empresas
RELEASES_DIR = PROJECT_ROOT / "docs" / "releases"
CONTEXTS_DIR = PROJECT_ROOT / "src" / "contexts"

RELEASE_REGEX = re.compile(r"^(?P<cvm>\d+)_(?P<data>\d{4}-\d{2}-\d{2})_.*\.pdf$", re.IGNORECASE)

MAX_CHARS_POR_CHUNK = 12000
SLEEP_ENTRE_CHAMADAS = 0.5


def _parse_release_filename(filename: str):
    match = RELEASE_REGEX.match(filename)
    if not match:
        return None
    codigo_cvm = match.group("cvm")
    data_str = match.group("data")
    try:
        data_ref = datetime.strptime(data_str, "%Y-%m-%d").date()
    except ValueError:
        return None
    return codigo_cvm, data_ref


def _mapear_release_mais_recente():
    releases = {}
    if not RELEASES_DIR.exists():
        return releases
    for path in RELEASES_DIR.iterdir():
        if not path.is_file() or path.suffix.lower() != ".pdf":
            continue
        parsed = _parse_release_filename(path.name)
        if not parsed:
            continue
        codigo_cvm, data_ref = parsed
        atual = releases.get(codigo_cvm)
        if not atual or data_ref > atual["data"]:
            releases[codigo_cvm] = {"path": path, "data": data_ref}
    return releases


def _extrair_texto_pdf(caminho_pdf: Path) -> str:
    reader = PdfReader(str(caminho_pdf))
    textos_paginas = []
    for page in reader.pages:
        texto = page.extract_text() or ""
        textos_paginas.append(texto)
    return _limpar_texto_paginas(textos_paginas)


def _limpar_texto_paginas(textos_paginas: list[str]) -> str:
    if not textos_paginas:
        return ""

    num_paginas = len(textos_paginas)
    linhas_por_pagina = []
    frequencias = {}

    for texto in textos_paginas:
        linhas = [l.strip() for l in texto.splitlines() if l.strip()]
        unicas = set(linhas)
        linhas_por_pagina.append(linhas)
        for linha in unicas:
            if 3 <= len(linha) <= 80:
                frequencias[linha] = frequencias.get(linha, 0) + 1

    limiar = max(2, int(num_paginas * 0.6))
    repetidas = {linha for linha, count in frequencias.items() if count >= limiar}

    linhas_limpas = []
    for linhas in linhas_por_pagina:
        for linha in linhas:
            if linha in repetidas:
                continue
            linhas_limpas.append(linha)

    texto = "\n".join(linhas_limpas)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def _chunk_texto(texto: str, max_chars: int = MAX_CHARS_POR_CHUNK) -> list[str]:
    if not texto:
        return []
    partes = texto.split("\n\n")
    chunks = []
    atual = []
    tamanho = 0
    for parte in partes:
        if tamanho + len(parte) + 2 > max_chars and atual:
            chunks.append("\n\n".join(atual))
            atual = [parte]
            tamanho = len(parte)
        else:
            atual.append(parte)
            tamanho += len(parte) + 2
    if atual:
        chunks.append("\n\n".join(atual))
    return chunks


def _chamar_openai(prompt: str) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY não configurada.")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }
    data = {
        "model": OPENAI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": OPENAI_TEMPERATURE,
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def _limpar_json_response(conteudo: str) -> str:
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


def _extrair_numeros_referencia(texto: str, ticker: str, nome: str, data_release: str) -> dict:
    """
    Extrai números financeiros e operacionais de referência do release.
    Retorna um dicionário estruturado com os principais KPIs.
    """
    # Pegar apenas os primeiros 20k caracteres (onde geralmente estão os números)
    texto_truncado = texto[:20000]
    
    prompt = f"""Você é um analista financeiro sênior. Extraia os principais números de referência do release da empresa {nome} ({ticker}) com data de referência {data_release}.

TEXTO DO RELEASE:
\"\"\"{texto_truncado}\"\"\"

Retorne EXCLUSIVAMENTE um JSON válido no formato abaixo. Use null para valores não encontrados. Todos os valores monetários devem estar em REAIS (BRL) e em unidades (não milhões/bilhões).

{{
  "periodo_trimestre": "3T2025",
  "financeiros": {{
    "receita_liquida_tri": 124500000000,
    "receita_liquida_ltm": 498000000000,
    "ebitda_tri": 62000000000,
    "ebitda_ltm": 248000000000,
    "lucro_liquido_tri": 32000000000,
    "lucro_liquido_ltm": 128000000000,
    "divida_liquida": 180000000000,
    "divida_bruta": 250000000000,
    "capex_tri": 18000000000,
    "capex_ltm": 72000000000,
    "margem_ebitda_pct": 49.8,
    "margem_liquida_pct": 25.7
  }},
  "operacionais": {{
    "descricao": "produção de 2,7 MM boe/d, capacidade de refino 1,85 MM bpd",
    "metricas": {{}}
  }},
  "moeda": "BRL"
}}

IMPORTANTE:
- Use o período exato do release (ex: 3T2025, 2T2025)
- LTM = últimos 12 meses acumulados
- Converta milhões/bilhões para unidades (ex: R$ 124,5 bi = 124500000000)
- Em "operacionais.metricas", inclua KPIs específicos do setor (produção, vendas, clientes, etc.)
- Em "operacionais.descricao", resuma os principais números operacionais em texto
- Retorne APENAS o JSON, sem explicações"""

    try:
        resposta = _chamar_openai(prompt)
        resposta_limpa = _limpar_json_response(resposta)
        numeros = json.loads(resposta_limpa)
        return numeros
    except json.JSONDecodeError as e:
        print(f"  ⚠ Erro ao parsear JSON de números: {e}")
        return {}
    except Exception as e:
        print(f"  ⚠ Erro ao extrair números: {e}")
        return {}


def _formatar_numero_br(valor, escala="bi") -> str:
    """Formata número para exibição em português."""
    if valor is None:
        return "N/D"
    if escala == "bi":
        return f"R${valor/1e9:.1f} bi"
    elif escala == "mi":
        return f"R${valor/1e6:.1f} mi"
    elif escala == "pct":
        return f"{valor:.1f}%"
    return str(valor)


def _gerar_secao_numeros(numeros: dict) -> str:
    """Gera a seção de números de referência formatada para o contexto."""
    if not numeros:
        return ""
    
    periodo = numeros.get("periodo_trimestre", "N/D")
    fin = numeros.get("financeiros", {})
    oper = numeros.get("operacionais", {})
    
    linhas = [f"\n\nNÚMEROS DE REFERÊNCIA ({periodo}):"]
    
    # Receita
    if fin.get("receita_liquida_tri") or fin.get("receita_liquida_ltm"):
        tri = _formatar_numero_br(fin.get("receita_liquida_tri"))
        ltm = _formatar_numero_br(fin.get("receita_liquida_ltm"))
        linhas.append(f"- Receita Líquida: {tri} (trimestre) | {ltm} (LTM)")
    
    # EBITDA
    if fin.get("ebitda_tri") or fin.get("ebitda_ltm"):
        tri = _formatar_numero_br(fin.get("ebitda_tri"))
        ltm = _formatar_numero_br(fin.get("ebitda_ltm"))
        margem = _formatar_numero_br(fin.get("margem_ebitda_pct"), "pct") if fin.get("margem_ebitda_pct") else ""
        margem_str = f" | Margem {margem}" if margem and margem != "N/D" else ""
        linhas.append(f"- EBITDA: {tri} (trimestre) | {ltm} (LTM){margem_str}")
    
    # Lucro Líquido
    if fin.get("lucro_liquido_tri") or fin.get("lucro_liquido_ltm"):
        tri = _formatar_numero_br(fin.get("lucro_liquido_tri"))
        ltm = _formatar_numero_br(fin.get("lucro_liquido_ltm"))
        linhas.append(f"- Lucro Líquido: {tri} (trimestre) | {ltm} (LTM)")
    
    # Dívida
    if fin.get("divida_liquida"):
        div_liq = _formatar_numero_br(fin.get("divida_liquida"))
        div_bruta = _formatar_numero_br(fin.get("divida_bruta")) if fin.get("divida_bruta") else None
        if div_bruta and div_bruta != "N/D":
            linhas.append(f"- Dívida: {div_liq} (líquida) | {div_bruta} (bruta)")
        else:
            linhas.append(f"- Dívida Líquida: {div_liq}")
    
    # Capex
    if fin.get("capex_tri") or fin.get("capex_ltm"):
        tri = _formatar_numero_br(fin.get("capex_tri"))
        ltm = _formatar_numero_br(fin.get("capex_ltm"))
        linhas.append(f"- Capex: {tri} (trimestre) | {ltm} (LTM)")
    
    # Operacionais
    if oper.get("descricao"):
        linhas.append(f"- Operacional: {oper['descricao']}")
    
    if len(linhas) <= 1:
        return ""
    
    return "\n".join(linhas)


def _gerar_notas_por_chunk(texto: str, ticker: str, nome: str) -> list[str]:
    chunks = _chunk_texto(texto)
    notas = []
    for i, chunk in enumerate(chunks, 1):
        prompt = f"""Você é um analista sênior. Extraia do trecho abaixo apenas informações estruturais e duradouras sobre a empresa {nome} ({ticker}). 
Ignore números pontuais de trimestre e detalhes operacionais de curto prazo.

Trecho {i}/{len(chunks)}:
\"\"\"{chunk}\"\"\"

Responda com um texto objetivo contendo: modelo de negócio, segmentos, KPIs, drivers de valor, riscos, estrutura de capital, regulação e eventos críticos. 
Não use bullet points nem títulos."""
        notas.append(_chamar_openai(prompt))
        time.sleep(SLEEP_ENTRE_CHAMADAS)
    return notas


def _gerar_contexto_final(notas: list[str], ticker: str, nome: str) -> str:
    base = "\n\n".join(notas)
    prompt = f"""Você é um analista sênior. Com base nas notas abaixo, gere um CONTEXTO COMPLETO e longo da empresa {nome} ({ticker}) para enriquecer a análise de notícias.
O texto deve ser único, coeso e aprofundado, cobrindo: modelo de negócio, segmentos, drivers, KPIs, riscos, estrutura de capital, governança, regulação, competição e sensibilidade macro.
Evite números específicos de período e detalhes transitórios.
Não use listas nem títulos. Escreva em português.

Notas:
\"\"\"{base}\"\"\""""
    return _chamar_openai(prompt)


def _carregar_contexto_existente(path: Path):
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--ticker", type=str, default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    CONTEXTS_DIR.mkdir(parents=True, exist_ok=True)

    releases = _mapear_release_mais_recente()
    if not releases:
        print("⚠ Nenhum release encontrado em docs/releases")
        return

    empresas = carregar_dados_empresas()
    total = 0
    gerados = 0
    pulados = 0
    sem_release = 0
    falhas = 0

    for empresa in empresas:
        ticker_principal = empresa.get("ticker_principal", "").strip().upper()
        tickers_str = empresa.get("tickers", "")
        tickers = [t.strip().upper() for t in tickers_str.split(",") if t.strip()]

        if args.ticker:
            target = args.ticker.upper()
            if target not in tickers:
                continue
            ticker = target
        else:
            ticker = ticker_principal

        if not ticker:
            continue

        codigo_cvm = str(empresa.get("codigo_cvm", "")).strip()
        nome = (empresa.get("nome_curto") or empresa.get("nome") or ticker).strip()

        release_info = releases.get(codigo_cvm)
        if not release_info:
            sem_release += 1
            continue

        total += 1
        release_path = release_info["path"]
        data_release = release_info["data"].strftime("%Y-%m-%d")

        context_path = CONTEXTS_DIR / f"{ticker}.json"
        existente = _carregar_contexto_existente(context_path)
        if existente and not args.force:
            if existente.get("data_release") == data_release:
                pulados += 1
                print(f"[{ticker}] Contexto já atualizado ({data_release}).")
                continue

        try:
            print(f"[{ticker}] Extraindo texto do release: {release_path.name}")
            texto = _extrair_texto_pdf(release_path)
            if not texto:
                print(f"[{ticker}] ⚠ Texto vazio no PDF.")
                falhas += 1
                continue

            # Gerar contexto qualitativo
            notas = _gerar_notas_por_chunk(texto, ticker, nome)
            contexto = _gerar_contexto_final(notas, ticker, nome)

            # Extrair números de referência
            print(f"[{ticker}] Extraindo números de referência...")
            numeros = _extrair_numeros_referencia(texto, ticker, nome, data_release)
            
            # Adicionar seção de números ao contexto
            secao_numeros = _gerar_secao_numeros(numeros)
            contexto_completo = contexto + secao_numeros

            payload = {
                "ticker": ticker,
                "codigo_cvm": codigo_cvm,
                "data_release": data_release,
                "fonte_pdf": release_path.name,
                "texto_contexto": contexto_completo,
                "numeros_referencia": numeros,
                "gerado_em": datetime.utcnow().isoformat() + "Z",
            }

            with open(context_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

            gerados += 1
            print(f"[{ticker}] ✓ Contexto gerado e salvo.")
        except Exception as e:
            falhas += 1
            print(f"[{ticker}] ❌ Erro ao gerar contexto: {e}")

        if args.limit and gerados >= args.limit:
            break

    print("\nResumo:")
    print(f"  Processados: {total}")
    print(f"  Gerados: {gerados}")
    print(f"  Pulados: {pulados}")
    print(f"  Sem release: {sem_release}")
    print(f"  Falhas: {falhas}")


if __name__ == "__main__":
    main()
