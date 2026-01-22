# Firebase (Backend + Auth)

Este guia substitui o Google Apps Script pelo Firebase (Auth + Firestore).

## 1) Crie o projeto no Firebase
1. Acesse o Console Firebase e crie um projeto.
2. Ative **Authentication → Email/Password**.
3. Crie um banco **Cloud Firestore** em modo de teste (depois ajuste as regras).

## 2) Crie um app Web e pegue o config
No console, vá em **Project Settings → Your apps → Web** e copie o objeto de configuração.
No `index.html`, substitua o `REPLACE_ME` em `FIREBASE_CONFIG`:

```html
<script>
  window.FIREBASE_CONFIG = {
    apiKey: "REPLACE_ME",
    authDomain: "REPLACE_ME",
    projectId: "REPLACE_ME",
    storageBucket: "REPLACE_ME",
    messagingSenderId: "REPLACE_ME",
    appId: "REPLACE_ME",
  };
</script>
```

## 3) Estrutura de dados no Firestore
Coleção: `users`  
Documento: `users/{uid}`

Campos esperados:
- `name` (string)
- `email` (string)
- `tickers` (array de strings)
- `phone` (string)
- `address` (string)
- `birthdate` (string)

## 4) Service account para o backend Python
1. Vá em **Project Settings → Service accounts**.
2. Gere uma chave JSON e salve como `config/firebase_service_account.json`.
3. Configure a variável de ambiente:

```bash
export FIREBASE_SERVICE_ACCOUNT="config/firebase_service_account.json"
```

Ou, se preferir em CI, use JSON em string:

```bash
export FIREBASE_SERVICE_ACCOUNT_JSON='{"type":"service_account", ... }'
```

## 5) Regras de segurança (exemplo inicial)
Ajuste as regras do Firestore para permitir que cada usuário acesse apenas seu doc:

```txt
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

## 6) Fluxos disponíveis (Frontend)
- Cadastro/login via Firebase Auth
- Leitura/escrita de `users/{uid}` no Firestore
- Atualização de carteira e perfil no próprio doc
