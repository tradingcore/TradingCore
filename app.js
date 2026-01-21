const APP_SCRIPT_URL =
  "https://script.google.com/macros/s/AKfycby0BqLxkUkmu7QNtEl162XfHmsWPfsFdA9VJ3d73iXhgoRvwSiWDcOLUC-wVPb6uZyDaQ/exec";

const TOKEN_KEY = "tc_token";
const EMAIL_KEY = "tc_email";

const signupForm = document.getElementById("signup-form");
const loginForm = document.getElementById("login-form");
const portfolioForm = document.getElementById("portfolio-form");
const logoutButton = document.getElementById("logout-button");
const dashboard = document.getElementById("dashboard");
const authMessage = document.getElementById("auth-message");
const tickerInput = document.getElementById("ticker-input");
const tickerOptions = document.getElementById("ticker-options");
const addTickerButton = document.getElementById("add-ticker");
const tickerChips = document.getElementById("ticker-chips");
const tickersHidden = document.getElementById("tickers-hidden");

const tickerCatalog = new Map();
const selectedTickers = new Set();

const setMessage = (text, type = "") => {
  if (!authMessage) {
    return;
  }
  authMessage.textContent = text;
  authMessage.classList.remove("success", "error");
  if (type) {
    authMessage.classList.add(type);
  }
};

const setLoading = (button, isLoading) => {
  if (!button) {
    return;
  }
  button.disabled = isLoading;
  button.dataset.originalText = button.dataset.originalText || button.textContent;
  button.textContent = isLoading ? "Aguarde..." : button.dataset.originalText;
};

const normalizeTicker = (value) => value.trim().toUpperCase();

const postToScript = async (payload) => {
  const response = await fetch(APP_SCRIPT_URL, {
    method: "POST",
    headers: { "Content-Type": "text/plain;charset=utf-8" },
    body: JSON.stringify(payload),
  });

  const text = await response.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch (error) {
    throw new Error(`Resposta invalida do Apps Script (status ${response.status}).`);
  }

  if (!response.ok) {
    throw new Error(data.error || `Erro HTTP ${response.status}.`);
  }

  return data;
};

const setSession = (token, email) => {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(EMAIL_KEY, email);
  dashboard.classList.remove("hidden");
};

const clearSession = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(EMAIL_KEY);
  dashboard.classList.add("hidden");
};

const getSession = () => ({
  token: localStorage.getItem(TOKEN_KEY),
  email: localStorage.getItem(EMAIL_KEY),
});

const requireScriptUrl = () => {
  if (APP_SCRIPT_URL.includes("REPLACE_ME")) {
    setMessage("Configure a URL do Apps Script em app.js.", "error");
    return false;
  }
  return true;
};

const updateHiddenTickers = () => {
  if (tickersHidden) {
    tickersHidden.value = Array.from(selectedTickers).join(", ");
  }
};

const renderTickerChips = () => {
  if (!tickerChips) {
    return;
  }
  tickerChips.innerHTML = "";
  Array.from(selectedTickers)
    .sort()
    .forEach((ticker) => {
      const chip = document.createElement("span");
      chip.className = "ticker-chip";
      const name = tickerCatalog.get(ticker);
      chip.textContent = name ? `${ticker} - ${name}` : ticker;

      const removeButton = document.createElement("button");
      removeButton.type = "button";
      removeButton.setAttribute("aria-label", `Remover ${ticker}`);
      removeButton.textContent = "×";
      removeButton.addEventListener("click", () => {
        selectedTickers.delete(ticker);
        updateHiddenTickers();
        renderTickerChips();
      });

      chip.appendChild(removeButton);
      tickerChips.appendChild(chip);
    });
};

const addTicker = () => {
  if (!tickerInput) {
    return;
  }
  const raw = normalizeTicker(tickerInput.value || "");
  if (!raw) {
    setMessage("Selecione um ticker para adicionar.", "error");
    return;
  }
  if (!tickerCatalog.has(raw)) {
    setMessage("Ticker nao encontrado na lista da B3.", "error");
    return;
  }
  selectedTickers.add(raw);
  updateHiddenTickers();
  renderTickerChips();
  tickerInput.value = "";
  setMessage("", "");
};

const loadTickers = async () => {
  if (!tickerOptions) {
    return;
  }
  try {
    const response = await fetch("docs/acoes-listadas-b3.csv");
    const text = await response.text();
    const lines = text.trim().split(/\r?\n/);
    lines.slice(1).forEach((line) => {
      if (!line) {
        return;
      }
      let ticker = "";
      let name = "";
      const match = line.match(/^"([^"]+)","([^"]+)"/);
      if (match) {
        ticker = match[1];
        name = match[2];
      } else {
        const parts = line.split(",");
        ticker = parts[0]?.replace(/"/g, "") || "";
        name = parts[1]?.replace(/"/g, "") || "";
      }
      if (!ticker || ticker === "Ticker") {
        return;
      }
      tickerCatalog.set(ticker, name);
      const option = document.createElement("option");
      option.value = ticker;
      if (name) {
        option.label = `${ticker} - ${name}`;
      }
      tickerOptions.appendChild(option);
    });
  } catch (error) {
    setMessage("Nao foi possivel carregar a lista da B3.", "error");
  }
};

signupForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!requireScriptUrl()) {
    return;
  }

  const submitButton = signupForm.querySelector("button[type='submit']");
  setLoading(submitButton, true);

  const formData = new FormData(signupForm);
  const name = formData.get("name")?.trim();
  const email = formData.get("email")?.trim().toLowerCase();
  const phone = formData.get("phone")?.trim();
  const address = formData.get("address")?.trim();
  const birthdate = formData.get("birthdate");
  const password = formData.get("password");

  if (!name || !email || !phone || !address || !birthdate || !password) {
    setMessage("Preencha todos os campos do cadastro.", "error");
    setLoading(submitButton, false);
    return;
  }

  if (password.length < 8) {
    setMessage("A senha precisa ter pelo menos 8 caracteres.", "error");
    setLoading(submitButton, false);
    return;
  }

  try {
    const result = await postToScript({
      action: "signup",
      name,
      email,
      phone,
      address,
      birthdate,
      password,
    });

    if (!result.ok) {
      setMessage(result.error || "Nao foi possivel criar a conta.", "error");
      return;
    }

    setSession(result.data.token, email);
    setMessage("Conta criada com sucesso. Sua area logada esta liberada.", "success");
    signupForm.reset();
  } catch (error) {
    setMessage(error.message || "Erro ao conectar com o servidor.", "error");
  } finally {
    setLoading(submitButton, false);
  }
});

loginForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!requireScriptUrl()) {
    return;
  }

  const submitButton = loginForm.querySelector("button[type='submit']");
  setLoading(submitButton, true);

  const formData = new FormData(loginForm);
  const email = formData.get("email")?.trim().toLowerCase();
  const password = formData.get("password");

  if (!email || !password) {
    setMessage("Informe seu email e senha.", "error");
    setLoading(submitButton, false);
    return;
  }

  try {
    const result = await postToScript({
      action: "login",
      email,
      password,
    });

    if (!result.ok) {
      setMessage(result.error || "Credenciais invalidas.", "error");
      return;
    }

    setSession(result.data.token, email);
    setMessage("Login realizado com sucesso.", "success");
    loginForm.reset();
  } catch (error) {
    setMessage(error.message || "Erro ao conectar com o servidor.", "error");
  } finally {
    setLoading(submitButton, false);
  }
});

portfolioForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!requireScriptUrl()) {
    return;
  }

  const submitButton = portfolioForm.querySelector("button[type='submit']");
  setLoading(submitButton, true);

  const tickers = Array.from(selectedTickers).join(", ");
  if (!tickers) {
    setMessage("Adicione ao menos um ticker da B3.", "error");
    setLoading(submitButton, false);
    return;
  }

  const session = getSession();
  if (!session.token || !session.email) {
    setMessage("Sua sessao expirou. Faca login novamente.", "error");
    setLoading(submitButton, false);
    return;
  }

  try {
    const result = await postToScript({
      action: "savePortfolio",
      token: session.token,
      email: session.email,
      tickers,
    });

    if (!result.ok) {
      setMessage(result.error || "Nao foi possivel salvar a carteira.", "error");
      return;
    }

    selectedTickers.clear();
    updateHiddenTickers();
    renderTickerChips();
    setMessage("Carteira salva com sucesso.", "success");
  } catch (error) {
    setMessage(error.message || "Erro ao conectar com o servidor.", "error");
  } finally {
    setLoading(submitButton, false);
  }
});

logoutButton?.addEventListener("click", () => {
  clearSession();
  setMessage("Voce saiu da area logada.", "success");
});

addTickerButton?.addEventListener("click", addTicker);

tickerInput?.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    addTicker();
  }
});

const boot = () => {
  const session = getSession();
  if (session.token && session.email) {
    dashboard.classList.remove("hidden");
  }
  updateHiddenTickers();
  renderTickerChips();
  loadTickers();
};

boot();
