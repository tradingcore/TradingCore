#!/bin/bash
# Script simples para rodar o TradingCore

echo "🚀 Iniciando TradingCore..."
echo ""

# Voltar para raiz do projeto
cd "$(dirname "$0")/.."

# Definir credenciais do Firebase
export FIREBASE_SERVICE_ACCOUNT="config/firebase_service_account.json"

# Rodar sistema
python3 main.py

echo ""
echo "✅ Concluído!"

