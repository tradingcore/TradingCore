# Apps Script (Backend simples)

Use este guia para configurar um Web App do Google Apps Script que grava o cadastro e
a carteira na planilha do Google Sheets.

## 1) Crie a planilha
Crie uma planilha com a aba principal (ex: `Form_Responses`). A primeira linha deve
ter estes cabecalhos, nessa ordem:

1. Carimbo de data/hora
2. Qual seu nome completo?
3. Qual seu e-mail?
4. Ticker
5. Telefone com WhatsApp
6. Endereco
7. Data de nascimento
8. Senha hash
9. Sal
10. Status da conta

## 2) Crie o Apps Script
No Google Sheets: Extensoes -> Apps Script. Substitua o conteudo pelo script abaixo.

```javascript
const CONFIG = {
  SPREADSHEET_ID: "COLE_AQUI_O_ID_DA_PLANILHA",
  SHEET_NAME: "Form_Responses",
  TOKEN_TTL_MS: 1000 * 60 * 60 * 24 * 7,
};

const HEADERS = [
  "Carimbo de data/hora",
  "Qual seu nome completo?",
  "Qual seu e-mail?",
  "Ticker",
  "Telefone com WhatsApp",
  "Endereco",
  "Data de nascimento",
  "Senha hash",
  "Sal",
  "Status da conta",
];

function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents || "{}");
    if (!payload.action) {
      return jsonOutput({ ok: false, error: "Acao nao informada." });
    }

    switch (payload.action) {
      case "signup":
        return handleSignup(payload);
      case "login":
        return handleLogin(payload);
      case "savePortfolio":
        return handleSavePortfolio(payload);
      case "getPortfolio":
        return handleGetPortfolio(payload);
      case "updateProfile":
        return handleUpdateProfile(payload);
      default:
        return jsonOutput({ ok: false, error: "Acao invalida." });
    }
  } catch (error) {
    return jsonOutput({ ok: false, error: "Erro no servidor: " + error.message });
  }
}

function handleSignup(data) {
  const { name, email, phone, address, birthdate, password } = data;
  if (!name || !email || !phone || !address || !birthdate || !password) {
    return jsonOutput({ ok: false, error: "Campos obrigatorios faltando." });
  }

  const sheet = getSheet();
  const headerMap = getHeaderMap(sheet);

  const existingRow = findRowByEmail(sheet, headerMap, email);
  if (existingRow) {
    return jsonOutput({ ok: false, error: "E-mail ja cadastrado." });
  }

  const salt = Utilities.getUuid();
  const hash = hashPassword(password, salt);

  const row = buildRow(headerMap, {
    "Carimbo de data/hora": new Date(),
    "Qual seu nome completo?": name,
    "Qual seu e-mail?": email,
    "Telefone com WhatsApp": phone,
    Endereco: address,
    "Data de nascimento": birthdate,
    "Senha hash": hash,
    Sal: salt,
    Ticker: "",
    "Status da conta": "Ativo",
  });

  sheet.appendRow(row);
  const token = createToken(email);
  return jsonOutput({ 
    ok: true, 
    data: { 
      token,
      name: name,
      tickers: ""
    } 
  });
}

function handleLogin(data) {
  const { email, password } = data;
  if (!email || !password) {
    return jsonOutput({ ok: false, error: "Credenciais incompletas." });
  }

  const sheet = getSheet();
  const headerMap = getHeaderMap(sheet);
  const rowIndex = findRowByEmail(sheet, headerMap, email);
  if (!rowIndex) {
    return jsonOutput({ ok: false, error: "E-mail nao encontrado." });
  }

  const hash = sheet.getRange(rowIndex, headerMap["Senha hash"]).getValue();
  const salt = sheet.getRange(rowIndex, headerMap["Sal"]).getValue();
  const expected = hashPassword(password, salt);
  if (expected !== hash) {
    return jsonOutput({ ok: false, error: "Senha invalida." });
  }

  const name = sheet.getRange(rowIndex, headerMap["Qual seu nome completo?"]).getValue();
  const tickers = sheet.getRange(rowIndex, headerMap["Ticker"]).getValue();
  const phone = sheet.getRange(rowIndex, headerMap["Telefone com WhatsApp"]).getValue();
  const address = sheet.getRange(rowIndex, headerMap["Endereco"]).getValue();
  const birthdate = sheet.getRange(rowIndex, headerMap["Data de nascimento"]).getValue();

  const token = createToken(email);
  return jsonOutput({ 
    ok: true, 
    data: { 
      token,
      name: name || "",
      tickers: tickers || "",
      phone: phone || "",
      address: address || "",
      birthdate: birthdate || ""
    } 
  });
}

function handleSavePortfolio(data) {
  const { token, email, tickers } = data;
  if (!token || !email) {
    return jsonOutput({ ok: false, error: "Dados incompletos." });
  }

  if (!validateToken(token, email)) {
    return jsonOutput({ ok: false, error: "Sessao expirada." });
  }

  const sheet = getSheet();
  const headerMap = getHeaderMap(sheet);
  const rowIndex = findRowByEmail(sheet, headerMap, email);
  if (!rowIndex) {
    return jsonOutput({ ok: false, error: "Conta nao encontrada." });
  }

  sheet.getRange(rowIndex, headerMap["Ticker"]).setValue(tickers || "");
  sheet.getRange(rowIndex, headerMap["Status da conta"]).setValue("Ativo");
  return jsonOutput({ ok: true });
}

function handleGetPortfolio(data) {
  const { token, email } = data;
  if (!token || !email) {
    return jsonOutput({ ok: false, error: "Dados incompletos." });
  }

  if (!validateToken(token, email)) {
    return jsonOutput({ ok: false, error: "Sessao expirada." });
  }

  const sheet = getSheet();
  const headerMap = getHeaderMap(sheet);
  const rowIndex = findRowByEmail(sheet, headerMap, email);
  if (!rowIndex) {
    return jsonOutput({ ok: false, error: "Conta nao encontrada." });
  }

  const name = sheet.getRange(rowIndex, headerMap["Qual seu nome completo?"]).getValue();
  const tickers = sheet.getRange(rowIndex, headerMap["Ticker"]).getValue();
  const phone = sheet.getRange(rowIndex, headerMap["Telefone com WhatsApp"]).getValue();
  const address = sheet.getRange(rowIndex, headerMap["Endereco"]).getValue();
  const birthdate = sheet.getRange(rowIndex, headerMap["Data de nascimento"]).getValue();

  return jsonOutput({ 
    ok: true, 
    data: { 
      name: name || "",
      tickers: tickers || "",
      phone: phone || "",
      address: address || "",
      birthdate: birthdate || ""
    } 
  });
}

function handleUpdateProfile(data) {
  const { token, email, name, phone, address } = data;
  if (!token || !email) {
    return jsonOutput({ ok: false, error: "Dados incompletos." });
  }

  if (!validateToken(token, email)) {
    return jsonOutput({ ok: false, error: "Sessao expirada." });
  }

  const sheet = getSheet();
  const headerMap = getHeaderMap(sheet);
  const rowIndex = findRowByEmail(sheet, headerMap, email);
  if (!rowIndex) {
    return jsonOutput({ ok: false, error: "Conta nao encontrada." });
  }

  if (name !== undefined) {
    sheet.getRange(rowIndex, headerMap["Qual seu nome completo?"]).setValue(name);
  }
  if (phone !== undefined) {
    sheet.getRange(rowIndex, headerMap["Telefone com WhatsApp"]).setValue(phone);
  }
  if (address !== undefined) {
    sheet.getRange(rowIndex, headerMap["Endereco"]).setValue(address);
  }

  return jsonOutput({ ok: true });
}

function getSheet() {
  const spreadsheet = SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID);
  const sheet = spreadsheet.getSheetByName(CONFIG.SHEET_NAME);
  if (!sheet) {
    throw new Error("Aba nao encontrada.");
  }
  ensureHeaders(sheet);
  return sheet;
}

function ensureHeaders(sheet) {
  const current = sheet.getRange(1, 1, 1, HEADERS.length).getValues()[0];
  const needsUpdate = current.some((value, index) => value !== HEADERS[index]);
  if (needsUpdate) {
    sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);
  }
}

function getHeaderMap(sheet) {
  const values = sheet.getRange(1, 1, 1, HEADERS.length).getValues()[0];
  const map = {};
  values.forEach((value, index) => {
    map[value] = index + 1;
  });
  return map;
}

function buildRow(headerMap, data) {
  return HEADERS.map((header) => data[header] || "");
}

function findRowByEmail(sheet, headerMap, email) {
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) {
    return null;
  }
  const emails = sheet
    .getRange(2, headerMap["Qual seu e-mail?"], lastRow - 1, 1)
    .getValues();
  for (let i = 0; i < emails.length; i++) {
    if (String(emails[i][0]).toLowerCase() === String(email).toLowerCase()) {
      return i + 2;
    }
  }
  return null;
}

function hashPassword(password, salt) {
  const digest = Utilities.computeDigest(
    Utilities.DigestAlgorithm.SHA_256,
    salt + password
  );
  return digest
    .map((byte) => ("0" + (byte & 0xff).toString(16)).slice(-2))
    .join("");
}

function createToken(email) {
  const token = Utilities.getUuid();
  const payload = {
    email,
    exp: Date.now() + CONFIG.TOKEN_TTL_MS,
  };
  PropertiesService.getScriptProperties().setProperty(
    "token_" + token,
    JSON.stringify(payload)
  );
  return token;
}

function validateToken(token, email) {
  const payload = PropertiesService.getScriptProperties().getProperty(
    "token_" + token
  );
  if (!payload) {
    return false;
  }
  const data = JSON.parse(payload);
  if (data.exp < Date.now()) {
    return false;
  }
  return data.email === email;
}

function jsonOutput(payload) {
  return ContentService.createTextOutput(JSON.stringify(payload)).setMimeType(
    ContentService.MimeType.JSON
  );
}
```

## 3) Deploy como Web App
1. Clique em "Implantar" -> "Nova implantacao".
2. Tipo: "Web app".
3. Executar como: "Eu".
4. Quem tem acesso: "Qualquer pessoa".
5. Copie a URL do Web App.

**IMPORTANTE**: Sempre que atualizar o codigo, faca uma NOVA implantacao para que as mudancas tenham efeito!

## 4) Atualize o frontend
No arquivo app.js, substitua REPLACE_ME pela URL do Web App.

## Endpoints disponiveis

| Action | Descricao | Parametros |
|--------|-----------|------------|
| signup | Criar conta | name, email, phone, address, birthdate, password |
| login | Fazer login | email, password |
| savePortfolio | Salvar tickers | token, email, tickers |
| getPortfolio | Buscar dados do usuario | token, email |
| updateProfile | Atualizar perfil | token, email, name?, phone?, address? |

## Observacoes
- Este backend e simples e atende ao MVP.
- Senhas sao armazenadas como hash+sal, nunca em texto puro.
- O login agora retorna name e tickers junto com o token.
- A action getPortfolio permite buscar os dados a qualquer momento.
- A action updateProfile permite editar nome, telefone e endereco.
