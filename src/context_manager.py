import os
import requests
from .config import OPENAI_API_KEY

CONTEXT_DIR = os.path.join(os.path.dirname(__file__), "contexts")

def carregar_contexto(ticker):
    """
    Carrega o contexto de um ticker do arquivo local .txt.
    """
    file_path = os.path.join(CONTEXT_DIR, f"{ticker}.txt")
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"  ⚠ Erro ao ler arquivo de contexto para {ticker}: {e}")
            return None
    return None

def gerar_contexto_ia(ticker):
    """
    Usa o GPT-4o (modelo inteligente) para gerar uma tese estratégica para o ticker.
    Salva o resultado em um arquivo .txt local.
    """
    print(f"  🧠 Gerando tese estratégica para {ticker} via GPT-4o...")
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }
    
    prompt = f"""
Você é um analista sênior de Equity Research da B3. 
Sua tarefa é criar um guia de contexto estratégico para a empresa {ticker}. 
Este guia será usado por outra IA para filtrar e analisar notícias diárias.

Por favor, forneça as seguintes informações de forma concisa e estruturada:

1. MODELO DE NEGÓCIO: Como a empresa ganha dinheiro? Quais as principais linhas de receita?
2. KPIs CHAVE: O que move o resultado? (Ex: Preço de commodity, Câmbio, IPCA, Selic, Inadimplência, etc.)
3. TESES DE INVESTIMENTO: Qual o momento atual? (Crescimento, Dividendos, Turnaround?)
4. RISCOS PRINCIPAIS: O que mais pode afetar negativamente a tese?
5. O QUE BUSCAR EM NOTÍCIAS: O que é realmente impacto e o que é apenas ruído para esta empresa específica?

Limite a resposta a no máximo 500 palavras. Seja direto e focado no mercado financeiro.
"""
    
    data = {
        "model": "gpt-4o", # Usamos o modelo forte para inteligência estratégica
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        response_json = response.json()
        
        contexto = response_json["choices"][0]["message"]["content"].strip()
        
        # Salvar o arquivo
        os.makedirs(CONTEXT_DIR, exist_ok=True)
        file_path = os.path.join(CONTEXT_DIR, f"{ticker}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(contexto)
            
        print(f"  ✓ Contexto para {ticker} gerado e salvo com sucesso.")
        return contexto
        
    except Exception as e:
        print(f"  ✗ Erro ao gerar contexto para {ticker}: {e}")
        return None

def garantir_contexto(ticker):
    """
    Tenta carregar o contexto localmente. Se não existir, gera via IA.
    """
    contexto = carregar_contexto(ticker)
    if contexto:
        return contexto
    return gerar_contexto_ia(ticker)

