"""
Gerenciador de contextos estratégicos das ações.
Usa o arquivo JSON com contextos pré-gerados.
"""
import os
import json
from pathlib import Path

# Path do arquivo de contextos
CONTEXTOS_PATH = Path(__file__).parent.parent / "docs" / "contextos-acoes.json"

# Cache de contextos em memória
_contextos_cache = None


def _carregar_contextos():
    """Carrega o arquivo JSON de contextos."""
    global _contextos_cache
    
    if _contextos_cache is not None:
        return _contextos_cache
    
    if CONTEXTOS_PATH.exists():
        try:
            with open(CONTEXTOS_PATH, 'r', encoding='utf-8') as f:
                _contextos_cache = json.load(f)
                print(f"✓ {len(_contextos_cache) - 1} contextos carregados")  # -1 para _metadata
                return _contextos_cache
        except Exception as e:
            print(f"⚠ Erro ao carregar contextos: {e}")
            _contextos_cache = {}
    else:
        print(f"⚠ Arquivo de contextos não encontrado: {CONTEXTOS_PATH}")
        _contextos_cache = {}
    
    return _contextos_cache


def carregar_contexto(ticker):
    """
    Carrega o contexto de um ticker do arquivo JSON.
    
    Args:
        ticker: Código do ticker (ex: "PETR4")
        
    Returns:
        String formatada com o contexto ou None
    """
    contextos = _carregar_contextos()
    
    if ticker not in contextos:
        return None
    
    ctx = contextos[ticker]
    
    # Formatar como texto para a IA
    texto = f"""
EMPRESA: {ctx.get('nome', ticker)}
SETOR: {ctx.get('setor', 'N/A')}

MODELO DE NEGÓCIO:
{ctx.get('modelo', 'N/A')}

KPIs CHAVE:
{', '.join(ctx.get('kpis', []))}

TESE DE INVESTIMENTO:
{ctx.get('tese', 'N/A')}

RISCOS PRINCIPAIS:
{', '.join(ctx.get('riscos', []))}

O QUE BUSCAR EM NOTÍCIAS:
{', '.join(ctx.get('buscar', []))}
"""
    return texto.strip()


def carregar_contexto_dict(ticker):
    """
    Carrega o contexto de um ticker como dicionário.
    
    Args:
        ticker: Código do ticker
        
    Returns:
        Dict com o contexto ou None
    """
    contextos = _carregar_contextos()
    return contextos.get(ticker)


def garantir_contexto(ticker):
    """
    Tenta carregar o contexto. Retorna None se não existir.
    (Não gera mais via IA - usa apenas contextos pré-carregados)
    
    Args:
        ticker: Código do ticker
        
    Returns:
        String com o contexto ou None
    """
    return carregar_contexto(ticker)


def listar_tickers_com_contexto():
    """Retorna lista de tickers que têm contexto."""
    contextos = _carregar_contextos()
    return [k for k in contextos.keys() if not k.startswith('_')]


def obter_buscar_noticias(ticker):
    """
    Retorna a lista de temas a buscar em notícias para um ticker.
    Útil para melhorar a busca de notícias.
    
    Args:
        ticker: Código do ticker
        
    Returns:
        Lista de strings ou [ticker] se não houver contexto
    """
    ctx = carregar_contexto_dict(ticker)
    if ctx and 'buscar' in ctx:
        return ctx['buscar']
    return [ticker]
