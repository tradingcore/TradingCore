# 📊 TradingCore

Sistema que envia emails diários com análise de notícias sobre suas ações, usando IA para filtrar o que realmente importa baseado na tese fundamentalista de cada empresa.

---

## 🚀 Como Funciona

```
┌─────────────────────────────────────────────────────────────┐
│                    FASE 1 (Inteligência & Cache)            │
├─────────────────────────────────────────────────────────────┤
│  1. Carrega usuários do Google Sheets                       │
│  2. Extrai tickers ÚNICOS de todos os usuários              │
│  3. Para cada ticker (1x apenas):                           │
│     ├─ Carrega/Gera Tese Estratégica (Contexto Business)    │
│     ├─ Busca notícias (Event Registry API)                  │
│     ├─ Analisa com IA (GPT-4o-mini + Contexto)              │
│     │  └─ Atribui Relevância Score (0-10)                   │
│     └─ Gera resumo executivo baseado na tese                │
│  4. Armazena tudo em cache e persiste novos contextos       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    FASE 2 (Distribuição)                    │
├─────────────────────────────────────────────────────────────┤
│  Para cada usuário:                                         │
│     ├─ Pega notícias filtradas pelo Score de Relevância     │
│     ├─ Pega resumos do cache (0 chamadas API)               │
│     └─ Envia email personalizado                            │
└─────────────────────────────────────────────────────────────┘
```

### 🧠 Diferenciais Técnicos
- **Deduplicação:** Processa cada ação apenas uma vez, independente do número de usuários.
- **Contexto de Negócio:** A IA estuda o modelo de negócio da empresa (KPIs, riscos) antes de julgar as notícias.
- **Filtro de Ruído:** Usa um `relevancia_score` inteligente em vez de apenas sentimento.
- **Persistência Automática:** Novos contextos gerados são salvos automaticamente no repositório para economizar tokens no futuro.

---

## ⚡ Como Usar

### 1️⃣ Rodar Agora (Local)

```bash
# Instalar dependências (primeira vez)
pip install -r requirements.txt

# Executar
python main.py
```

---

### 2️⃣ Rodar Automático (GitHub Actions)

**Configure Secrets no GitHub** (Settings → Secrets → Actions):
`OPENAI_API_KEY`, `EVENT_REGISTRY_API_KEY`, `REMETENTE_EMAIL`, `REMETENTE_SENHA`, `SHEET_ID`, `GOOGLE_CREDENTIALS`.

✅ **Pronto!** Rodará automaticamente todo dia às **9h da manhã (Brasília)**.

---

## 📁 Estrutura

```
TradingCore/
├── main.py                      # 🚀 Script principal (2 fases otimizadas)
├── .github/workflows/           # ⏰ Automações
│   ├── daily-analysis.yml       # Análise diária (9h Brasília)
│   └── update-contexts.yml      # Atualização mensal das teses
└── src/
    ├── contexts/                # 📂 Teses estratégicas (.txt)
    ├── context_manager.py       # 🧠 Gestão de contexto business
    ├── ai_analyzer.py           # 🤖 Análise IA com Score de Relevância
    ├── news_fetcher.py          # 🔍 Busca de notícias
    ├── email_sender.py          # 📧 Geração de emails HTML
    ├── sheets_client.py         # 📊 Integração Google Sheets
    └── utils.py                 # 🛠️ Utilitários
```

---

## 🔧 Configuração

### Google Sheets - Usuários
Planilha ID: `1rhQCLpOboojr9CNYXyisEQ-U8OnQAtqiU3kDq3nT-_o`
**Colunas:** `Qual seu nome completo?`, `Qual seu e-mail?`, `Ticker 1`.

---

## 📅 Horários e Cron
- **Diário (9h Brasília):** Envio das análises e aprendizado de novos tickers.
- **Mensal (Dia 1):** Reciclagem completa das teses estratégicas para manter a IA atualizada.

---

## 💰 Custos Estimados
- **OpenAI (GPT-4o-mini):** ~$0.10-0.30/mês.
- **Infra (GitHub/Sheets/Gmail):** **Grátis**.

*A persistência de contextos e a deduplicação de tickers garantem o menor custo operacional possível.*

---

**✨ Sistema criado por Eduardo Fleischmann**
