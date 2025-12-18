# 📊 TradingCore

Sistema que envia emails diários com análise de notícias sobre suas ações.

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

✅ **Pronto!** Rodará automaticamente todo dia às 6h da manhã.

---

## 📁 Estrutura

```
TradingCore/
├── main.py                      # 🚀 Roda o sistema
├── requirements.txt             # 📦 Dependências
├── .env                         # 🔑 Suas senhas
├── config/                      # ⚙️ Configurações
│   ├── credentials.json         # Google Cloud
│   └── rodar.sh                 # Script para rodar
└── src/                         # 💻 Código
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
cron: '0 9 * * *'  # 9:00 UTC = 6:00 Brasília
```

**Exemplos:**
- `'0 12 * * *'` = 9h da manhã (Brasília)
- `'0 */6 * * *'` = A cada 6 horas
- `'0 9 * * 1-5'` = Dias úteis às 6h

---

## 💰 Custos

- GitHub Actions: **Grátis** (repo público)
- OpenAI: ~$0.20/mês (2 usuários)
- Event Registry: **Grátis** 
- Gmail: **Grátis**

**Total: ~$0.20/mês** 💰

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
