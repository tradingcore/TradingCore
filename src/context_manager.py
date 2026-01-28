"""
Gerenciador de contextos estratégicos das ações.
Usa arquivos por ticker em src/contexts (formato JSON com texto completo).
Mantém fallback para o JSON legado em docs/contextos-acoes.json.
"""
import json
from pathlib import Path

# Paths
CONTEXTOS_DIR = Path(__file__).parent / "contexts"
LEGACY_CONTEXTOS_PATH = Path(__file__).parent.parent / "docs" / "contextos-acoes.json"

# Cache de contextos em memória
_contextos_cache = {}
_legacy_contextos_cache = None


def _carregar_contextos_legado():
    """Carrega o arquivo JSON legado de contextos."""
    global _legacy_contextos_cache

    if _legacy_contextos_cache is not None:
        return _legacy_contextos_cache

    if LEGACY_CONTEXTOS_PATH.exists():
        try:
            with open(LEGACY_CONTEXTOS_PATH, 'r', encoding='utf-8') as f:
                _legacy_contextos_cache = json.load(f)
                print(f"✓ {len(_legacy_contextos_cache)} contextos legados carregados")
                return _legacy_contextos_cache
        except Exception as e:
            print(f"⚠ Erro ao carregar contextos legados: {e}")
            _legacy_contextos_cache = {}
    else:
        _legacy_contextos_cache = {}

    return _legacy_contextos_cache


def _carregar_contexto_arquivo(ticker):
    """Carrega o contexto completo do arquivo por ticker."""
    if ticker in _contextos_cache:
        return _contextos_cache[ticker]

    path = CONTEXTOS_DIR / f"{ticker}.json"
    if not path.exists():
        _contextos_cache[ticker] = None
        return None

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            _contextos_cache[ticker] = data
            return data
    except Exception as e:
        print(f"⚠ Erro ao carregar contexto de {ticker}: {e}")
        _contextos_cache[ticker] = None
        return None


def carregar_contexto(ticker):
    """
    Carrega o contexto (descrição) de um ticker do arquivo JSON.
    
    Args:
        ticker: Código do ticker (ex: "PETR4")
        
    Returns:
        String com a descrição do Yahoo Finance ou None
    """
    contexto_arquivo = _carregar_contexto_arquivo(ticker)
    if isinstance(contexto_arquivo, dict):
        texto = contexto_arquivo.get("texto_contexto") or contexto_arquivo.get("contexto")
        if isinstance(texto, str) and texto.strip():
            return texto.strip()

    # Fallback para contexto legado
    contextos = _carregar_contextos_legado()

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
    contexto_arquivo = _carregar_contexto_arquivo(ticker)
    if contexto_arquivo is not None:
        return contexto_arquivo

    contextos = _carregar_contextos_legado()
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
    tickers = set()
    if CONTEXTOS_DIR.exists():
        for path in CONTEXTOS_DIR.glob("*.json"):
            tickers.add(path.stem)

    contextos = _carregar_contextos_legado()
    tickers.update(contextos.keys())

    return list(tickers)


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
