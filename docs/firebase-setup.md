# Firebase Setup - TradingCore

Guia de configuração do Firebase (Authentication + Firestore).

## 1. Criar Projeto no Firebase

1. Acesse [Firebase Console](https://console.firebase.google.com)
2. Clique em "Adicionar projeto"
3. Nome: `tradingcore-db`
4. Desative Google Analytics (opcional)
5. Clique em "Criar projeto"

## 2. Ativar Authentication

1. No menu lateral: **Build → Authentication**
2. Clique em "Começar"
3. Aba "Sign-in method" → Ative **Email/Senha**

## 3. Criar Firestore Database

1. No menu lateral: **Build → Firestore Database**
2. Clique em "Criar banco de dados"
3. Selecione "Iniciar no modo de produção"
4. Escolha região: `southamerica-east1` (São Paulo)

## 4. Configurar Regras de Segurança

No Firestore, vá em **Regras** e cole:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Usuários podem ler/escrever apenas seus próprios dados
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
      
      // Subcoleção de notícias do usuário
      match /news/{newsId} {
        allow read: if request.auth != null && request.auth.uid == userId;
      }
    }
    
    // Dados de mercado (cotações) - leitura pública
    match /market_data/{document=**} {
      allow read: if true;
      allow write: if false; // Apenas backend escreve
    }
    
    // Notícias globais - leitura pública
    match /news_global/{document=**} {
      allow read: if true;
      allow write: if false; // Apenas backend escreve
    }
  }
}
```

## 5. Registrar App Web

1. Na página inicial do projeto, clique no ícone **Web** (`</>`)
2. Nome: `TradingCore Web`
3. Copie o objeto de configuração
4. Cole no `index.html` em `window.FIREBASE_CONFIG`:

```javascript
window.FIREBASE_CONFIG = {
  apiKey: "AIza...",
  authDomain: "tradingcore-db.firebaseapp.com",
  projectId: "tradingcore-db",
  storageBucket: "tradingcore-db.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abc123"
};
```

## 6. Gerar Service Account (Backend)

1. Vá em **Configurações do projeto** (engrenagem)
2. Aba **Contas de serviço**
3. Clique em "Gerar nova chave privada"
4. Salve como `config/firebase_service_account.json` (local)
5. No GitHub Actions, adicione o conteúdo JSON como secret `FIREBASE_SERVICE_ACCOUNT_JSON`

## 7. Estrutura de Dados

### Coleção `users/{uid}`
```json
{
  "name": "João Silva",
  "email": "joao@email.com",
  "phone": "11999999999",
  "address": "São Paulo, SP",
  "birthdate": "1990-01-01",
  "tickers": ["PETR4", "VALE3", "ITUB4"]
}
```

### Coleção `market_data/quotes`
```json
{
  "IBOV": { "price": 130000, "change": 1.5, "changePercent": 1.17 },
  "USDBRL": { "price": 5.20, "change": -0.05, "changePercent": -0.95 },
  "updated_at": "2026-01-23T10:00:00Z"
}
```

### Coleção `news_global/{data}/tickers/{ticker}`
```json
{
  "ticker": "PETR4",
  "data": "2026-01-23",
  "noticias": [...],
  "sentimento_medio": 0.5,
  "resumo_consolidado": "..."
}
```

## 8. Variáveis de Ambiente

### Local (`.env`)
```
FIREBASE_SERVICE_ACCOUNT=config/firebase_service_account.json
OPENAI_API_KEY=sk-...
EVENT_REGISTRY_API_KEY=...
REMETENTE_EMAIL=seu@gmail.com
REMETENTE_SENHA=xxxx xxxx xxxx xxxx
```

### GitHub Actions (Secrets)
- `FIREBASE_SERVICE_ACCOUNT_JSON` - Conteúdo completo do JSON
- `OPENAI_API_KEY`
- `EVENT_REGISTRY_API_KEY`
- `REMETENTE_EMAIL`
- `REMETENTE_SENHA`

## 9. Testar Localmente

```bash
# Configurar credenciais
export FIREBASE_SERVICE_ACCOUNT="config/firebase_service_account.json"

# Rodar sistema
python main.py
```

Ou use o script:
```bash
./config/rodar.sh
```
