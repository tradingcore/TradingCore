#!/usr/bin/env python3
"""
Script para atualizar cotações de mercado e B3 no Firestore.
Roda via GitHub Actions a cada 15 minutos durante o pregão.
"""

import os
import json
import yfinance as yf
from datetime import datetime
import pytz
import firebase_admin
from firebase_admin import credentials, firestore


def init_firebase():
    """Inicializa Firebase se ainda não estiver inicializado."""
    if firebase_admin._apps:
        return firestore.client()
    
    cred_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON')
    if not cred_json:
        raise ValueError("FIREBASE_SERVICE_ACCOUNT_JSON não configurado")
    
    cred = credentials.Certificate(json.loads(cred_json))
    firebase_admin.initialize_app(cred)
    return firestore.client()


def fetch_market_quotes(db, now):
    """Busca cotações de mercado (IBOV, Dólar, etc)."""
    MARKET_TICKERS = {
        '^BVSP': 'IBOV',
        'USDBRL=X': 'Dólar',
        'EURBRL=X': 'Euro',
        'GC=F': 'Ouro',
        'BTC-USD': 'Bitcoin'
    }
    
    print('\n📊 Cotações de mercado:')
    quotes = {}
    
    for symbol, name in MARKET_TICKERS.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='2d')
            
            if not hist.empty and len(hist) >= 1:
                price = float(hist['Close'].iloc[-1])
                
                if len(hist) >= 2:
                    prev = float(hist['Close'].iloc[-2])
                    change = price - prev
                    change_pct = (change / prev) * 100
                else:
                    change = 0
                    change_pct = 0
                
                quotes[symbol] = {
                    'price': price,
                    'change': round(change, 4),
                    'changePercent': round(change_pct, 2),
                    'name': name,
                    'updatedAt': now.isoformat()
                }
                print(f'  ✓ {name}: {price:.2f} ({change_pct:+.2f}%)')
        except Exception as e:
            print(f'  ✗ {name}: {e}')
    
    if quotes:
        db.collection('market_data').document('quotes').set(quotes, merge=True)
        print(f'  → {len(quotes)} cotações salvas')
    
    return quotes


def fetch_b3_quotes(db, now):
    """Busca cotações B3 de todos os tickers dos usuários."""
    print('\n📈 Coletando tickers dos usuários...')
    all_tickers = set()
    
    for doc in db.collection('users').stream():
        data = doc.to_dict() or {}
        tickers = data.get('tickers', [])
        if isinstance(tickers, list):
            for t in tickers:
                if t and str(t).strip():
                    all_tickers.add(str(t).strip().upper())
    
    print(f'  → {len(all_tickers)} tickers únicos: {sorted(all_tickers)}')
    
    if not all_tickers:
        return {}
    
    print('\n💹 Cotações B3:')
    b3_quotes = {}
    
    for ticker in sorted(all_tickers):
        try:
            ticker_yahoo = f'{ticker}.SA'
            stock = yf.Ticker(ticker_yahoo)
            hist = stock.history(period='2d')
            
            if not hist.empty and len(hist) >= 1:
                price = float(hist['Close'].iloc[-1])
                
                if len(hist) >= 2:
                    prev = float(hist['Close'].iloc[-2])
                    change = price - prev
                    change_pct = (change / prev) * 100
                else:
                    change = 0
                    change_pct = 0
                
                b3_quotes[ticker] = {
                    'price': round(price, 2),
                    'change': round(change, 2),
                    'changePercent': round(change_pct, 2),
                    'updatedAt': now.isoformat()
                }
                print(f'  ✓ {ticker}: R$ {price:.2f} ({change_pct:+.2f}%)')
        except Exception as e:
            print(f'  ✗ {ticker}: {e}')
    
    if b3_quotes:
        db.collection('market_data').document('b3_quotes').set(b3_quotes, merge=True)
        print(f'  → {len(b3_quotes)} cotações B3 salvas')
    
    return b3_quotes


def main():
    """Função principal."""
    tz = pytz.timezone('America/Sao_Paulo')
    now = datetime.now(tz)
    print(f'🕐 Atualizando cotações: {now.strftime("%d/%m/%Y %H:%M")}')
    
    try:
        db = init_firebase()
    except Exception as e:
        print(f'❌ Erro ao inicializar Firebase: {e}')
        exit(1)
    
    fetch_market_quotes(db, now)
    fetch_b3_quotes(db, now)
    
    print('\n✅ Atualização concluída!')


if __name__ == '__main__':
    main()
