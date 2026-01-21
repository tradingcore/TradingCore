const APP_SCRIPT_URL =
  "https://script.google.com/macros/s/AKfycby0BqLxkUkmu7QNtEl162XfHmsWPfsFdA9VJ3d73iXhgoRvwSiWDcOLUC-wVPb6uZyDaQ/exec";

const TOKEN_KEY = "tc_token";
const EMAIL_KEY = "tc_email";
const NAME_KEY = "tc_name";
const TICKERS_KEY = "tc_tickers";

// DOM Elements - Views
const landingPage = document.getElementById("landing-page");
const appDashboard = document.getElementById("app-dashboard");
const toastContainer = document.getElementById("toast-container");

// DOM Elements - Forms
const signupForm = document.getElementById("signup-form");
const loginForm = document.getElementById("login-form");
const portfolioForm = document.getElementById("portfolio-form");

// DOM Elements - Dashboard Header
const headerUserEmail = document.getElementById("header-user-email");
const headerUserAvatar = document.getElementById("header-user-avatar");
const logoutButton = document.getElementById("logout-button");

// DOM Elements - Dashboard Content
const welcomeName = document.getElementById("welcome-name");
const tickerInput = document.getElementById("ticker-input");
const tickerOptions = document.getElementById("ticker-options");
const addTickerButton = document.getElementById("add-ticker");
const tickerList = document.getElementById("ticker-list");
const emptyTickers = document.getElementById("empty-tickers");
const tickerCount = document.getElementById("ticker-count");
const tickersHidden = document.getElementById("tickers-hidden");

// State
const tickerCatalog = new Map();
const userTickers = new Set();

// ========================================
// TOAST NOTIFICATIONS
// ========================================
const showToast = (message, type = "info", duration = 4000) => {
  if (!toastContainer) return;
  
  const toast = document.createElement("div");
  toast.className = `toast toast--${type}`;

  const icons = {
    success: "✓",
    error: "✕",
    info: "ℹ",
  };

  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || icons.info}</span>
    <span>${message}</span>
  `;

  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = "slideOut 0.3s ease forwards";
    setTimeout(() => toast.remove(), 300);
  }, duration);
};

// ========================================
// LOADING STATE
// ========================================
const setLoading = (button, isLoading) => {
  if (!button) return;
  button.disabled = isLoading;
  button.dataset.originalText = button.dataset.originalText || button.textContent;
  button.textContent = isLoading ? "Aguarde..." : button.dataset.originalText;
};

// ========================================
// SESSION MANAGEMENT
// ========================================
const setSession = (token, email, name = "", tickers = []) => {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(EMAIL_KEY, email);
  if (name) localStorage.setItem(NAME_KEY, name);
  localStorage.setItem(TICKERS_KEY, JSON.stringify(tickers));
};

const clearSession = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(EMAIL_KEY);
  localStorage.removeItem(NAME_KEY);
  localStorage.removeItem(TICKERS_KEY);
  userTickers.clear();
};

const getSession = () => ({
  token: localStorage.getItem(TOKEN_KEY),
  email: localStorage.getItem(EMAIL_KEY),
  name: localStorage.getItem(NAME_KEY),
  tickers: JSON.parse(localStorage.getItem(TICKERS_KEY) || "[]"),
});

const isLoggedIn = () => {
  const session = getSession();
  return !!(session.token && session.email);
};

// ========================================
// UTILITY FUNCTIONS
// ========================================
const truncateEmail = (email) => {
  if (!email) return "";
  const parts = email.split("@");
  if (parts[0].length <= 8) return email;
  return parts[0].substring(0, 8) + "...";
};

// ========================================
// VIEW MANAGEMENT (Landing vs Dashboard)
// ========================================
const showLandingPage = () => {
  if (landingPage) landingPage.classList.remove("hidden");
  if (appDashboard) appDashboard.classList.add("hidden");
};

const showDashboard = () => {
  if (landingPage) landingPage.classList.add("hidden");
  if (appDashboard) appDashboard.classList.remove("hidden");
  
  const session = getSession();
  const displayName = session.name || session.email?.split("@")[0] || "Usuário";
  
  // Update header - truncate email
  if (headerUserEmail) headerUserEmail.textContent = truncateEmail(session.email);
  if (headerUserAvatar) headerUserAvatar.textContent = displayName.charAt(0).toUpperCase();
  
  // Update welcome
  if (welcomeName) welcomeName.textContent = displayName;
  
  // Load tickers from session into state
  userTickers.clear();
  session.tickers.forEach((t) => {
    if (t && t.trim()) userTickers.add(t.trim().toUpperCase());
  });
  renderUserTickers();
};

// ========================================
// TICKER MANAGEMENT
// ========================================
const normalizeTicker = (value) => value.trim().toUpperCase();

const updateHiddenTickers = () => {
  if (tickersHidden) {
    tickersHidden.value = Array.from(userTickers).join(", ");
  }
};

const updateTickerCount = () => {
  if (tickerCount) {
    const count = userTickers.size;
    tickerCount.textContent = `${count} ${count === 1 ? "ativo" : "ativos"}`;
  }
};

const renderUserTickers = () => {
  if (!tickerList) return;

  // Clear existing ticker items (keep empty state element)
  const tickerItems = tickerList.querySelectorAll(".ticker-item");
  tickerItems.forEach((item) => item.remove());

  if (userTickers.size === 0) {
    if (emptyTickers) emptyTickers.classList.remove("hidden");
  } else {
    if (emptyTickers) emptyTickers.classList.add("hidden");

    Array.from(userTickers)
      .sort()
      .forEach((ticker) => {
        const name = tickerCatalog.get(ticker) || "";
        const item = document.createElement("div");
        item.className = "ticker-item";
        item.innerHTML = `
          <span class="ticker-item-code">${ticker}</span>
          ${name ? `<span class="ticker-item-name">${name}</span>` : ""}
          <button class="ticker-item-remove" type="button" aria-label="Remover ${ticker}" data-ticker="${ticker}">
            ✕
          </button>
        `;

        const removeBtn = item.querySelector(".ticker-item-remove");
        removeBtn.addEventListener("click", () => removeTicker(ticker));

        tickerList.appendChild(item);
      });
  }

  updateTickerCount();
  updateHiddenTickers();
};

const addTicker = async () => {
  if (!tickerInput) return;

  const raw = normalizeTicker(tickerInput.value || "");
  if (!raw) {
    showToast("Digite um ticker para adicionar.", "error");
    return;
  }

  if (!tickerCatalog.has(raw)) {
    showToast("Ticker não encontrado na lista da B3.", "error");
    return;
  }

  if (userTickers.has(raw)) {
    showToast("Este ticker já está na sua carteira.", "info");
    tickerInput.value = "";
    return;
  }

  // Add to local state
  userTickers.add(raw);
  tickerInput.value = "";

  // Update local storage
  localStorage.setItem(TICKERS_KEY, JSON.stringify(Array.from(userTickers)));

  // Save to server (sends ALL current tickers, not just the new one)
  await savePortfolioToServer();

  renderUserTickers();
  showToast(`${raw} adicionado à sua carteira!`, "success");
};

const removeTicker = async (ticker) => {
  // Remove from local state
  userTickers.delete(ticker);

  // Update local storage
  localStorage.setItem(TICKERS_KEY, JSON.stringify(Array.from(userTickers)));

  // Save to server (sends ALL current tickers)
  await savePortfolioToServer();

  renderUserTickers();
  showToast(`${ticker} removido da carteira.`, "info");
};

const savePortfolioToServer = async () => {
  const session = getSession();
  if (!session.token || !session.email) return;

  // Send ALL current tickers to server
  const tickers = Array.from(userTickers).join(", ");

  try {
    await postToScript({
      action: "savePortfolio",
      token: session.token,
      email: session.email,
      tickers,
    });
  } catch (error) {
    console.error("Erro ao salvar carteira:", error);
    showToast("Erro ao salvar carteira no servidor.", "error");
  }
};

const loadTickers = async () => {
  if (!tickerOptions) return;

  try {
    const response = await fetch("docs/acoes-listadas-b3.csv");
    const text = await response.text();
    const lines = text.trim().split(/\r?\n/);

    lines.slice(1).forEach((line) => {
      if (!line) return;

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

      if (!ticker || ticker === "Ticker") return;

      tickerCatalog.set(ticker, name);
      const option = document.createElement("option");
      option.value = ticker;
      if (name) option.label = `${ticker} - ${name}`;
      tickerOptions.appendChild(option);
    });
  } catch (error) {
    console.error("Erro ao carregar tickers:", error);
  }
};

// ========================================
// API COMMUNICATION
// ========================================
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
    throw new Error(`Resposta inválida do servidor (status ${response.status}).`);
  }

  if (!response.ok) {
    throw new Error(data.error || `Erro HTTP ${response.status}.`);
  }

  return data;
};

const requireScriptUrl = () => {
  if (APP_SCRIPT_URL.includes("REPLACE_ME")) {
    showToast("Configure a URL do Apps Script em app.js.", "error");
    return false;
  }
  return true;
};

const loadUserPortfolioFromServer = async () => {
  const session = getSession();
  if (!session.token || !session.email) return null;

  try {
    const result = await postToScript({
      action: "getPortfolio",
      token: session.token,
      email: session.email,
    });

    if (result.ok && result.data) {
      return result.data;
    }
  } catch (error) {
    console.error("Erro ao carregar carteira do servidor:", error);
  }
  
  return null;
};

// ========================================
// EVENT HANDLERS
// ========================================
signupForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!requireScriptUrl()) return;

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
    showToast("Preencha todos os campos do cadastro.", "error");
    setLoading(submitButton, false);
    return;
  }

  if (password.length < 8) {
    showToast("A senha precisa ter pelo menos 8 caracteres.", "error");
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
      showToast(result.error || "Não foi possível criar a conta.", "error");
      return;
    }

    setSession(result.data.token, email, name, []);
    signupForm.reset();
    showDashboard();
    showToast("🎉 Conta criada com sucesso! Bem-vindo ao TradingCore!", "success", 5000);
  } catch (error) {
    showToast(error.message || "Erro ao conectar com o servidor.", "error");
  } finally {
    setLoading(submitButton, false);
  }
});

loginForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!requireScriptUrl()) return;

  const submitButton = loginForm.querySelector("button[type='submit']");
  setLoading(submitButton, true);

  const formData = new FormData(loginForm);
  const email = formData.get("email")?.trim().toLowerCase();
  const password = formData.get("password");

  if (!email || !password) {
    showToast("Informe seu email e senha.", "error");
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
      showToast(result.error || "Email ou senha incorretos.", "error");
      return;
    }

    // Get name and tickers from login response
    const name = result.data.name || "";
    const tickersStr = result.data.tickers || "";
    const tickerArray = tickersStr
      ? tickersStr.split(",").map((t) => t.trim().toUpperCase()).filter((t) => t)
      : [];

    console.log("Login response - tickers:", tickersStr, "parsed:", tickerArray);

    setSession(result.data.token, email, name, tickerArray);
    loginForm.reset();
    
    showToast("✓ Login realizado com sucesso!", "success");

    // Try to load fresh data from server (getPortfolio action)
    const portfolioData = await loadUserPortfolioFromServer();
    console.log("Portfolio data from server:", portfolioData);
    
    if (portfolioData) {
      if (portfolioData.name) {
        localStorage.setItem(NAME_KEY, portfolioData.name);
      }
      if (portfolioData.tickers) {
        const freshTickers = portfolioData.tickers
          .split(",")
          .map((t) => t.trim().toUpperCase())
          .filter((t) => t);
        console.log("Fresh tickers from getPortfolio:", freshTickers);
        localStorage.setItem(TICKERS_KEY, JSON.stringify(freshTickers));
      }
    }

    // Show dashboard with loaded data
    showDashboard();
  } catch (error) {
    showToast(error.message || "Erro ao conectar com o servidor.", "error");
  } finally {
    setLoading(submitButton, false);
  }
});

logoutButton?.addEventListener("click", () => {
  clearSession();
  showLandingPage();
  showToast("Você saiu da sua conta.", "info");
});

addTickerButton?.addEventListener("click", addTicker);

tickerInput?.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    addTicker();
  }
});

// ========================================
// INITIALIZATION
// ========================================
const boot = async () => {
  // Load ticker catalog first
  await loadTickers();

  // Check if user is logged in
  if (isLoggedIn()) {
    // Try to load fresh data from server first
    const portfolioData = await loadUserPortfolioFromServer();
    console.log("Boot - Portfolio data:", portfolioData);
    
    if (portfolioData) {
      if (portfolioData.name) {
        localStorage.setItem(NAME_KEY, portfolioData.name);
      }
      if (portfolioData.tickers) {
        const freshTickers = portfolioData.tickers
          .split(",")
          .map((t) => t.trim().toUpperCase())
          .filter((t) => t);
        console.log("Boot - Fresh tickers:", freshTickers);
        localStorage.setItem(TICKERS_KEY, JSON.stringify(freshTickers));
      }
    }

    // Show dashboard with loaded data
    showDashboard();
  } else {
    showLandingPage();
  }
};

boot();
