#!/bin/bash
# Script simples para rodar o TradingCore

echo "🚀 Iniciando TradingCore..."
echo ""

# Voltar para raiz do projeto
cd "$(dirname "$0")/.."

# Definir credenciais do Google
export GOOGLE_APPLICATION_CREDENTIALS="config/credentials.json"

# Rodar sistema
python3 main.py

echo ""
echo "✅ Concluído!"

