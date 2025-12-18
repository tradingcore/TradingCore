"""
Configurações e constantes do sistema TradingCore.
"""
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))

# Event Registry API
EVENT_REGISTRY_API_KEY = os.getenv("EVENT_REGISTRY_API_KEY")

# Email Configuration
REMETENTE_EMAIL = os.getenv("REMETENTE_EMAIL")
REMETENTE_SENHA = os.getenv("REMETENTE_SENHA")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))

# Google Sheets Configuration
SHEET_ID = os.getenv("SHEET_ID")

# Processing Parameters
MAX_NOTICIAS_POR_TICKER = int(os.getenv("MAX_NOTICIAS_POR_TICKER", "20"))
TOP_N_RELEVANTES = int(os.getenv("TOP_N_RELEVANTES", "5"))
RELEVANCIA_MIN = float(os.getenv("RELEVANCIA_MIN", "0.0"))
HORAS_RETROATIVAS = int(os.getenv("HORAS_RETROATIVAS", "24"))


def validar_configuracoes():
    """Valida se todas as configurações obrigatórias estão presentes."""
    required = [
        ("OPENAI_API_KEY", OPENAI_API_KEY),
        ("EVENT_REGISTRY_API_KEY", EVENT_REGISTRY_API_KEY),
        ("REMETENTE_EMAIL", REMETENTE_EMAIL),
        ("REMETENTE_SENHA", REMETENTE_SENHA),
        ("SHEET_ID", SHEET_ID),
    ]
    
    missing = [name for name, value in required if not value]
    
    if missing:
        raise ValueError(
            f"Configurações obrigatórias ausentes: {', '.join(missing)}\n"
            "Verifique seu arquivo .env"
        )
    
    print("✓ Todas as configurações foram carregadas com sucesso!")

