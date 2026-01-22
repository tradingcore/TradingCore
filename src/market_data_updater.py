"""
Script para atualizar cotações de mercado no Firestore.
Roda periodicamente para manter o ticker tape atualizado.
"""
import yfinance as yf
from datetime import datetime
import pytz
from .firebase_client import _init_firestore


# Cotações gerais de mercado
MARKET_TICKERS = {
    "^BVSP": "IBOV",
    "USDBRL=X": "Dólar",
    "EURBRL=X": "Euro",
    "GC=F": "Ouro",
    "BTC-USD": "Bitcoin"
}


def atualizar_cotacoes_mercado():
    """
    Atualiza cotações de mercado no Firestore.
    """
    print("\n📊 Atualizando cotações de mercado...")
    
    try:
        db = _init_firestore()
        quotes = {}
        
        for symbol, name in MARKET_TICKERS.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                
                if not hist.empty and len(hist) >= 1:
                    price = float(hist['Close'].iloc[-1])
                    
                    if len(hist) >= 2:
                        prev_price = float(hist['Close'].iloc[-2])
                        change = price - prev_price
                        change_pct = (change / prev_price) * 100
                    else:
                        change = 0
                        change_pct = 0
                    
                    quotes[symbol] = {
                        "price": price,
                        "change": round(change, 4),
                        "changePercent": round(change_pct, 2),
                        "name": name,
                        "updatedAt": datetime.now(pytz.timezone('America/Sao_Paulo')).isoformat()
                    }
                    
                    print(f"  ✓ {name}: {price:.2f} ({change_pct:+.2f}%)")
                    
            except Exception as e:
                print(f"  ✗ Erro ao buscar {name}: {e}")
        
        # Salvar no Firestore
        if quotes:
            db.collection("market_data").document("quotes").set(quotes, merge=True)
            print(f"\n✓ {len(quotes)} cotações salvas no Firestore")
        
        return quotes
        
    except Exception as e:
        print(f"✗ Erro ao atualizar cotações: {e}")
        return {}


def atualizar_cotacoes_b3(tickers):
    """
    Atualiza cotações de ações da B3 no Firestore.
    
    Args:
        tickers: Lista de tickers da B3 (sem .SA)
    """
    if not tickers:
        return {}
    
    print(f"\n📈 Atualizando cotações de {len(tickers)} ações da B3...")
    
    try:
        db = _init_firestore()
        quotes = {}
        
        for ticker in tickers:
            try:
                ticker_yahoo = f"{ticker}.SA" if not ticker.endswith('.SA') else ticker
                stock = yf.Ticker(ticker_yahoo)
                hist = stock.history(period="2d")
                
                if not hist.empty and len(hist) >= 1:
                    price = float(hist['Close'].iloc[-1])
                    
                    if len(hist) >= 2:
                        prev_price = float(hist['Close'].iloc[-2])
                        change = price - prev_price
                        change_pct = (change / prev_price) * 100
                    else:
                        change = 0
                        change_pct = 0
                    
                    # Usar ticker sem .SA como chave
                    ticker_key = ticker.replace('.SA', '')
                    quotes[ticker_key] = {
                        "price": round(price, 2),
                        "change": round(change, 2),
                        "changePercent": round(change_pct, 2),
                        "updatedAt": datetime.now(pytz.timezone('America/Sao_Paulo')).isoformat()
                    }
                    
                    print(f"  ✓ {ticker_key}: R$ {price:.2f} ({change_pct:+.2f}%)")
                    
            except Exception as e:
                print(f"  ✗ Erro ao buscar {ticker}: {e}")
        
        # Salvar no Firestore
        if quotes:
            db.collection("market_data").document("b3_quotes").set(quotes, merge=True)
            print(f"\n✓ {len(quotes)} cotações B3 salvas no Firestore")
        
        return quotes
        
    except Exception as e:
        print(f"✗ Erro ao atualizar cotações B3: {e}")
        return {}


def coletar_todos_tickers_usuarios():
    """
    Coleta todos os tickers únicos de todos os usuários.
    """
    try:
        db = _init_firestore()
        all_tickers = set()
        
        for doc in db.collection("users").stream():
            data = doc.to_dict() or {}
            tickers = data.get("tickers", [])
            
            if isinstance(tickers, list):
                for t in tickers:
                    if t and str(t).strip():
                        all_tickers.add(str(t).strip().upper())
        
        return list(all_tickers)
        
    except Exception as e:
        print(f"✗ Erro ao coletar tickers: {e}")
        return []


def atualizar_todas_cotacoes():
    """
    Atualiza todas as cotações (mercado + B3 dos usuários).
    """
    print("\n" + "="*60)
    print("💹 ATUALIZANDO TODAS AS COTAÇÕES")
    print("="*60)
    
    # Atualizar cotações de mercado
    atualizar_cotacoes_mercado()
    
    # Coletar e atualizar cotações B3 dos usuários
    tickers_usuarios = coletar_todos_tickers_usuarios()
    if tickers_usuarios:
        atualizar_cotacoes_b3(tickers_usuarios)
    
    print("\n✓ Atualização concluída!")


if __name__ == "__main__":
    atualizar_todas_cotacoes()
