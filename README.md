# 📊 TradingCore

Sistema que envia emails diários com análise de notícias sobre suas ações.

---

## 🚀 Como Funciona

```
┌─────────────────────────────────────────────────────────────┐
│                    FASE 1 (APIs)                            │
├─────────────────────────────────────────────────────────────┤
│  1. Carrega usuários do Google Sheets                       │
│  2. Extrai tickers ÚNICOS de todos os usuários              │
│  3. Para cada ticker (1x apenas):                           │
│     ├─ Busca notícias (Event Registry API)                  │
│     ├─ Analisa com IA (OpenAI GPT)                          │
│     └─ Gera resumo executivo (OpenAI GPT)                   │
│  4. Armazena tudo em cache                                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    FASE 2 (Emails)                          │
├─────────────────────────────────────────────────────────────┤
│  Para cada usuário:                                         │
│     ├─ Pega análises do cache (0 chamadas API)              │
│     ├─ Pega resumos do cache (0 chamadas API)               │
│     └─ Envia email personalizado                            │
└─────────────────────────────────────────────────────────────┘
```

**Otimização:** Se 10 usuários têm PETR4, o sistema busca e analisa PETR4 apenas 1 vez, economizando chamadas de API.

---

## ⚡ Como Usar

### 1️⃣ Rodar Agora (Local)

```bash
# Instalar dependências (primeira vez)
pip install -r requirements.txt

# Executar
./config/rodar.sh
```

**Pronto!** Emails serão enviados para todos os usuários da planilha.

---

### 2️⃣ Rodar Automático (GitHub Actions)

**Suba para o GitHub:**

```bash
git init
git add .
git commit -m "TradingCore"
git remote add origin https://github.com/SEU_USUARIO/TradingCore.git
git push -u origin main
```

**Configure Secrets no GitHub** (Settings → Secrets → Actions):

```
OPENAI_API_KEY
EVENT_REGISTRY_API_KEY  
REMETENTE_EMAIL
REMETENTE_SENHA
SHEET_ID
GOOGLE_CREDENTIALS (conteúdo do config/credentials.json)
```

**Ative o Workflow:**
- Actions → TradingCore - Análise Diária → Enable workflow

✅ **Pronto!** Rodará automaticamente todo dia às **9h da manhã (Brasília)**.

---

## 📁 Estrutura

```
TradingCore/
├── main.py                      # 🚀 Script principal (2 fases otimizadas)
├── requirements.txt             # 📦 Dependências
├── .env                         # 🔑 Suas senhas (local)
├── .github/workflows/           # ⏰ GitHub Actions
│   └── daily-analysis.yml       # Cron job (9h Brasília)
├── config/                      # ⚙️ Configurações
│   ├── credentials.json         # Google Cloud
│   └── rodar.sh                 # Script para rodar
└── src/                         # 💻 Código
    ├── config.py                # Configurações e variáveis
    ├── sheets_client.py         # Integração Google Sheets
    ├── news_fetcher.py          # Busca notícias (Event Registry)
    ├── ai_analyzer.py           # Análise com GPT (OpenAI)
    ├── email_sender.py          # Geração e envio de emails
    └── utils.py                 # Funções utilitárias
```

---

## 🔧 Configuração

### `.env` - Suas Credenciais

Já está configurado com suas chaves. Se precisar alterar algo:

```bash
nano .env
```

### Google Sheets - Usuários

Planilha ID: `1rhQCLpOboojr9CNYXyisEQ-U8OnQAtqiU3kDq3nT-_o`

**Colunas necessárias:**
- `Qual seu nome completo?`
- `Qual seu e-mail?`
- `Ticker 1` (ex: "PETR4, VALE3, BBAS3")

---

## 📅 Alterar Horário

Edite `.github/workflows/daily-analysis.yml`:

```yaml
cron: '0 12 * * *'  # 12:00 UTC = 9:00 Brasília
```

**Exemplos:**
- `'0 9 * * *'` = 6h da manhã (Brasília)
- `'0 12 * * *'` = 9h da manhã (Brasília) ← **atual**
- `'0 15 * * *'` = 12h (meio-dia Brasília)
- `'0 */6 * * *'` = A cada 6 horas
- `'0 12 * * 1-5'` = Dias úteis às 9h

---

## 💰 Custos

| Serviço | Custo |
|---------|-------|
| GitHub Actions | **Grátis** (repo público) |
| OpenAI (GPT-4o-mini) | ~$0.10-0.30/mês |
| Event Registry | **Grátis** |
| Gmail | **Grátis** |

**Total estimado: ~$0.20/mês** 💰

*A otimização de cache reduz significativamente as chamadas à OpenAI quando há tickers repetidos entre usuários.*

---

## 🆘 Problemas?

**Google Sheets não funciona:**
- Compartilhe a planilha com: `tradingcore@tradingcore-481623.iam.gserviceaccount.com`

**Email não envia:**
- Use senha de app do Gmail (não a senha normal)
- Gere em: https://myaccount.google.com/apppasswords

**GitHub Actions não roda:**
- Verifique se todos os Secrets estão configurados
- Actions → Habilite o workflow se estiver desabilitado

---

**✨ Sistema criado por Eduardo Fleischmann**
