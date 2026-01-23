"""
Gerenciador de contextos estratégicos das ações.
Usa o arquivo JSON com descrições do Yahoo Finance.
"""
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
                print(f"✓ {len(_contextos_cache)} contextos carregados")
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
    Carrega o contexto (descrição) de um ticker do arquivo JSON.
    
    Args:
        ticker: Código do ticker (ex: "PETR4")
        
    Returns:
        String com a descrição do Yahoo Finance ou None
    """
    contextos = _carregar_contextos()
    
    if ticker not in contextos:
        return None
    
    descricao = contextos[ticker]
    
    # Se for string, é o formato novo (apenas descrição)
    if isinstance(descricao, str):
        return f"CONTEXTO DA EMPRESA ({ticker}):\n{descricao}"
    
    # Se for dict, é o formato antigo (retrocompatibilidade)
    if isinstance(descricao, dict):
        ctx = descricao
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
    
    return None


def carregar_contexto_dict(ticker):
    """
    Carrega o contexto de um ticker como dicionário ou string.
    
    Args:
        ticker: Código do ticker
        
    Returns:
        Dict/String com o contexto ou None
    """
    contextos = _carregar_contextos()
    return contextos.get(ticker)


def garantir_contexto(ticker):
    """
    Tenta carregar o contexto. Retorna None se não existir.
    
    Args:
        ticker: Código do ticker
        
    Returns:
        String com o contexto ou None
    """
    return carregar_contexto(ticker)


def listar_tickers_com_contexto():
    """Retorna lista de tickers que têm contexto."""
    contextos = _carregar_contextos()
    return list(contextos.keys())


def obter_buscar_noticias(ticker):
    """
    Retorna palavras-chave para buscar notícias.
    No formato novo, retorna apenas o ticker.
    
    Args:
        ticker: Código do ticker
        
    Returns:
        Lista de strings para busca
    """
    ctx = carregar_contexto_dict(ticker)
    
    if ctx is None:
        return [ticker]
    
    # Formato antigo com lista de temas
    if isinstance(ctx, dict) and 'buscar' in ctx:
        return ctx['buscar']
    
    # Formato novo - retorna apenas o ticker
    return [ticker]
