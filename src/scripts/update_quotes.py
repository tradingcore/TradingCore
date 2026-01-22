#!/usr/bin/env python3
"""
Script para atualizar cotações de mercado e B3 no Firestore.
Roda via GitHub Actions a cada 15 minutos durante o pregão.
"""

import os
import json
import csv
import yfinance as yf
from datetime import datetime
import pytz
import firebase_admin
from firebase_admin import credentials, firestore

# Mapeamento de setores Yahoo Finance -> PT-BR
SECTOR_TRANSLATION = {
    'Financial Services': 'Financeiro',
    'Financials': 'Financeiro',
    'Energy': 'Energia',
    'Basic Materials': 'Materiais Básicos',
    'Materials': 'Materiais Básicos',
    'Consumer Cyclical': 'Consumo Cíclico',
    'Consumer Defensive': 'Consumo Básico',
    'Industrials': 'Indústria',
    'Healthcare': 'Saúde',
    'Technology': 'Tecnologia',
    'Communication Services': 'Comunicações',
    'Utilities': 'Utilidades',
    'Real Estate': 'Imobiliário',
    '': 'Outros',
    None: 'Outros'
}


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


def fetch_heatmap_data(db, now):
    """Busca dados para o mapa de calor - top 100 ações B3 organizadas por setor."""
    print('\n🗺️ Mapa de Calor - Top 100 ações B3:')
    
    # Caminho do CSV (relativo ao script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, '..', '..', 'docs', 'acoes-listadas-b3.csv')
    
    # Ler todos os tickers do CSV (já ordenado por volume)
    all_tickers = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ticker = row.get('Ticker', '').strip()
                if ticker:
                    all_tickers.append(ticker)
        print(f'  → {len(all_tickers)} tickers carregados do CSV')
    except Exception as e:
        print(f'  ✗ Erro ao ler CSV: {e}')
        return {}
    
    # Buscar cotações e setores
    heatmap_data = {}  # setor -> [ações]
    
    for i, ticker in enumerate(all_tickers):
        try:
            ticker_yahoo = f'{ticker}.SA'
            stock = yf.Ticker(ticker_yahoo)
            
            # Buscar histórico
            hist = stock.history(period='2d')
            if hist.empty:
                continue
            
            price = float(hist['Close'].iloc[-1])
            change_pct = 0
            if len(hist) >= 2:
                prev = float(hist['Close'].iloc[-2])
                change_pct = ((price - prev) / prev) * 100
            
            # Buscar setor e market cap
            info = stock.info
            sector_en = info.get('sector', '') or info.get('industry', '') or ''
            sector_pt = SECTOR_TRANSLATION.get(sector_en, 'Outros')
            market_cap = info.get('marketCap', 0) or 0
            
            # Adicionar ao setor
            if sector_pt not in heatmap_data:
                heatmap_data[sector_pt] = []
            
            heatmap_data[sector_pt].append({
                'ticker': ticker,
                'price': round(price, 2),
                'change': round(change_pct, 2),
                'sector': sector_pt,
                'marketCap': market_cap
            })
            
            # Log a cada 25 ações
            if (i + 1) % 25 == 0:
                print(f'  → Processado {i + 1}/{len(all_tickers)} ações...')
                
        except Exception as e:
            print(f'  ✗ {ticker}: {e}')
            continue
    
    # Ordenar ações dentro de cada setor por market cap (maior primeiro)
    for sector in heatmap_data:
        heatmap_data[sector].sort(key=lambda x: x['marketCap'], reverse=True)
    
    # Salvar no Firestore
    if heatmap_data:
        total_acoes = sum(len(acoes) for acoes in heatmap_data.values())
        db.collection('market_data').document('heatmap').set({
            'data': heatmap_data,
            'totalAcoes': total_acoes,
            'updatedAt': now.isoformat()
        })
        print(f'  ✓ Mapa de calor salvo: {len(heatmap_data)} setores, {total_acoes} ações')
    
    return heatmap_data


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
    fetch_heatmap_data(db, now)
    
    print('\n✅ Atualização concluída!')


if __name__ == '__main__':
    main()
