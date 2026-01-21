const APP_SCRIPT_URL = "https://script.google.com/macros/s/AKfycby0BqLxkUkmu7QNtEl162XfHmsWPfsFdA9VJ3d73iXhgoRvwSiWDcOLUC-wVPb6uZyDaQ/exec";

const TOKEN_KEY = "tc_token";
const EMAIL_KEY = "tc_email";

const signupForm = document.getElementById("signup-form");
const loginForm = document.getElementById("login-form");
const portfolioForm = document.getElementById("portfolio-form");
const logoutButton = document.getElementById("logout-button");
const dashboard = document.getElementById("dashboard");
const authMessage = document.getElementById("auth-message");

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

const normalizeTickers = (raw) =>
  raw
    .split(",")
    .map((item) => item.trim().toUpperCase())
    .filter(Boolean)
    .join(", ");

const isValidTickers = (value) =>
  /^(?:[A-Z]{4}\d{1,2})(?:,\s*[A-Z]{4}\d{1,2})*$/.test(value);

const postToScript = async (payload) => {
  const response = await fetch(APP_SCRIPT_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
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
    setMessage("Erro ao conectar com o servidor.", "error");
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
    setMessage("Erro ao conectar com o servidor.", "error");
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

  const formData = new FormData(portfolioForm);
  const rawTickers = formData.get("tickers")?.toString() || "";
  const tickers = normalizeTickers(rawTickers);

  if (!tickers || !isValidTickers(tickers)) {
    setMessage("Informe tickers validos da B3 (ex: PETR4, VALE3).", "error");
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

    portfolioForm.reset();
    setMessage("Carteira salva com sucesso.", "success");
  } catch (error) {
    setMessage("Erro ao conectar com o servidor.", "error");
  } finally {
    setLoading(submitButton, false);
  }
});

logoutButton?.addEventListener("click", () => {
  clearSession();
  setMessage("Voce saiu da area logada.", "success");
});

const boot = () => {
  const session = getSession();
  if (session.token && session.email) {
    dashboard.classList.remove("hidden");
  }
};

boot();
