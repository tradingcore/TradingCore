"""
Script para gerar contextos estratégicos das ações B3 via OpenAI.
Roda uma vez para popular o arquivo contextos-acoes.json.

Uso: python src/scripts/gerar_contextos.py
"""
import os
import sys
import json
import csv
import time
import requests
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o-mini"

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
CSV_PATH = PROJECT_ROOT / "docs" / "acoes-listadas-b3.csv"
JSON_PATH = PROJECT_ROOT / "docs" / "contextos-acoes.json"


def carregar_tickers_csv():
    """Carrega lista de tickers do CSV."""
    tickers = []
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticker = row.get('Ticker', '').strip()
            nome = row.get('Nome', '').strip()
            if ticker:
                tickers.append({'ticker': ticker, 'nome': nome})
    return tickers


def carregar_contextos_existentes():
    """Carrega contextos já gerados."""
    if JSON_PATH.exists():
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def salvar_contextos(contextos):
    """Salva contextos no JSON."""
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(contextos, f, ensure_ascii=False, indent=2)


def gerar_contexto_openai(ticker, nome):
    """Gera contexto via OpenAI API."""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }
    
    prompt = f"""Você é um analista de ações brasileiro experiente.
Gere um contexto estratégico COMPACTO para a ação {ticker} ({nome}) da B3.

Responda em JSON exatamente neste formato:
{{
  "nome": "{nome}",
  "setor": "Setor da empresa",
  "modelo": "Descrição compacta do modelo de negócio em 1-2 frases",
  "kpis": ["KPI1", "KPI2", "KPI3", "KPI4"],
  "tese": "Tese de investimento em 1-2 frases",
  "riscos": ["Risco1", "Risco2", "Risco3"],
  "buscar": ["Tema1", "Tema2", "Tema3", "Tema4", "Tema5"]
}}

Seja conciso e focado em informações relevantes para análise de notícias.
Responda APENAS o JSON, sem explicações."""

    data = {
        "model": OPENAI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        conteudo = response.json()["choices"][0]["message"]["content"]
        
        # Limpar markdown
        conteudo = conteudo.strip()
        if conteudo.startswith("```"):
            conteudo = conteudo.split("```")[1]
            if conteudo.startswith("json"):
                conteudo = conteudo[4:]
            conteudo = conteudo.strip()
        
        return json.loads(conteudo)
        
    except Exception as e:
        print(f"  ✗ Erro ao gerar contexto para {ticker}: {e}")
        return None


def gerar_contexto_generico(ticker, nome):
    """Gera contexto genérico para empresas sem informações específicas."""
    return {
        "nome": nome,
        "setor": "Não classificado",
        "modelo": f"{nome} é uma empresa listada na B3.",
        "kpis": ["Receita", "EBITDA", "Lucro líquido", "Endividamento"],
        "tese": "Empresa listada na B3 com informações limitadas.",
        "riscos": ["Liquidez", "Governança", "Informações limitadas"],
        "buscar": [nome, ticker, "Resultados", "Aquisições", "Reestruturação"]
    }


def main():
    print("="*60)
    print("🔧 GERADOR DE CONTEXTOS DE AÇÕES B3")
    print("="*60)
    
    if not OPENAI_API_KEY:
        print("✗ OPENAI_API_KEY não configurada!")
        return
    
    # Carregar dados
    tickers = carregar_tickers_csv()
    contextos = carregar_contextos_existentes()
    
    print(f"\n📊 {len(tickers)} tickers no CSV")
    print(f"📄 {len(contextos) - 1} contextos já existentes")  # -1 para _metadata
    
    # Identificar tickers sem contexto
    tickers_sem_contexto = [
        t for t in tickers 
        if t['ticker'] not in contextos and not t['ticker'].startswith('_')
    ]
    
    print(f"🔍 {len(tickers_sem_contexto)} tickers sem contexto")
    
    if not tickers_sem_contexto:
        print("\n✅ Todos os tickers já têm contexto!")
        return
    
    print(f"\n📝 Gerando contextos para {len(tickers_sem_contexto)} tickers...")
    print("   (Ctrl+C para parar a qualquer momento)\n")
    
    gerados = 0
    erros = 0
    
    try:
        for i, t in enumerate(tickers_sem_contexto):
            ticker = t['ticker']
            nome = t['nome']
            
            print(f"[{i+1}/{len(tickers_sem_contexto)}] {ticker} ({nome})...", end=" ")
            
            # Gerar via OpenAI
            contexto = gerar_contexto_openai(ticker, nome)
            
            if contexto:
                contextos[ticker] = contexto
                gerados += 1
                print("✓")
            else:
                # Usar genérico
                contextos[ticker] = gerar_contexto_generico(ticker, nome)
                erros += 1
                print("⚠ (genérico)")
            
            # Salvar a cada 10 contextos
            if (i + 1) % 10 == 0:
                salvar_contextos(contextos)
                print(f"   💾 Salvo ({gerados} gerados, {erros} genéricos)")
            
            # Rate limit
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n\n⏹ Interrompido pelo usuário")
    
    # Salvar final
    salvar_contextos(contextos)
    
    print(f"\n{'='*60}")
    print(f"✅ CONCLUÍDO")
    print(f"   Contextos gerados: {gerados}")
    print(f"   Contextos genéricos: {erros}")
    print(f"   Total no arquivo: {len(contextos) - 1}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
