"""
Cliente para integração com Google Sheets.
"""
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import os
from .config import SHEET_ID

# Scopes necessários para Google Sheets
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


def carregar_usuarios_sheets():
    """
    Carrega dados dos usuários do Google Sheets e retorna um DataFrame.
    """
    try:
        # Tentar carregar credenciais do arquivo
        creds_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'config/credentials.json')
        
        if os.path.exists(creds_file):
            creds = Credentials.from_service_account_file(creds_file, scopes=SCOPES)
        else:
            # Fallback para autenticação padrão (para Google Colab)
            from google.auth import default
            creds, _ = default()
        
        gc = gspread.authorize(creds)

        spreadsheet = gc.open_by_key(SHEET_ID)
        worksheet = spreadsheet.get_worksheet(0)
        rows = worksheet.get_all_values()

        df = pd.DataFrame(rows[1:], columns=rows[0])
        print(f"✓ Carregados {len(df)} usuários do Google Sheets")
        return df
    except Exception as e:
        print(f"✗ Erro ao carregar Google Sheets: {e}")
        return pd.DataFrame()

