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

// DOM Elements - Mobile menu
const mobileMenuBtn = document.getElementById("mobile-menu-btn");
const mobileNav = document.getElementById("mobile-nav");

// DOM Elements - Forms
const signupForm = document.getElementById("signup-form");
const loginForm = document.getElementById("login-form");

// DOM Elements - Dashboard Header
const headerUserAvatar = document.getElementById("header-user-avatar");
const logoutButton = document.getElementById("logout-button");
const navDashboard = document.getElementById("nav-dashboard");

// DOM Elements - Dashboard Sections
const sectionCarteira = document.getElementById("section-carteira");
const sectionPerfil = document.getElementById("section-perfil");

// DOM Elements - Dashboard Content
const welcomeName = document.getElementById("welcome-name");
const tickerInput = document.getElementById("ticker-input");
const tickerSuggestions = document.getElementById("ticker-suggestions");
const addTickerButton = document.getElementById("add-ticker");
const tickerList = document.getElementById("ticker-list");
const emptyTickers = document.getElementById("empty-tickers");
const tickerCount = document.getElementById("ticker-count");

// DOM Elements - Profile
const profileAvatar = document.getElementById("profile-avatar");
const profileName = document.getElementById("profile-name");
const profileEmail = document.getElementById("profile-email");

// State
const tickerCatalog = new Map();
const userTickers = new Set();
let currentSuggestionIndex = -1;

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
// VIEW MANAGEMENT
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
  
  // Update header
  if (headerUserAvatar) headerUserAvatar.textContent = displayName.charAt(0).toUpperCase();
  
  // Update welcome
  if (welcomeName) welcomeName.textContent = displayName;
  
  // Update profile section
  if (profileAvatar) profileAvatar.textContent = displayName.charAt(0).toUpperCase();
  if (profileName) profileName.textContent = session.name || displayName;
  if (profileEmail) profileEmail.textContent = session.email || "-";
  
  // Load tickers from session
  userTickers.clear();
  session.tickers.forEach((t) => {
    if (t && t.trim()) userTickers.add(t.trim().toUpperCase());
  });
  renderUserTickers();
  
  // Show carteira section by default
  showSection("carteira");
};

const showSection = (sectionName) => {
  // Hide all sections
  if (sectionCarteira) sectionCarteira.classList.add("hidden");
  if (sectionPerfil) sectionPerfil.classList.add("hidden");
  
  // Show target section
  if (sectionName === "carteira" && sectionCarteira) {
    sectionCarteira.classList.remove("hidden");
  } else if (sectionName === "perfil" && sectionPerfil) {
    sectionPerfil.classList.remove("hidden");
  }
  
  // Update nav active state
  document.querySelectorAll(".nav-dashboard-item").forEach((item) => {
    item.classList.toggle("active", item.dataset.section === sectionName);
  });
};

// ========================================
// TICKER AUTOCOMPLETE
// ========================================
const showSuggestions = (searchTerm) => {
  if (!tickerSuggestions || !searchTerm) {
    hideSuggestions();
    return;
  }

  const term = searchTerm.toUpperCase();
  const matches = [];
  
  tickerCatalog.forEach((name, code) => {
    if (code.includes(term) || name.toUpperCase().includes(term)) {
      matches.push({ code, name });
    }
  });

  // Limit to 10 results
  const limited = matches.slice(0, 10);

  if (limited.length === 0) {
    hideSuggestions();
    return;
  }

  tickerSuggestions.innerHTML = limited
    .map(
      (item, index) => `
      <div class="ticker-suggestion ${index === currentSuggestionIndex ? "selected" : ""}" data-code="${item.code}">
        <span class="ticker-suggestion-code">${item.code}</span>
        <span class="ticker-suggestion-name">${item.name}</span>
      </div>
    `
    )
    .join("");

  tickerSuggestions.classList.remove("hidden");

  // Add click handlers
  tickerSuggestions.querySelectorAll(".ticker-suggestion").forEach((el) => {
    el.addEventListener("click", () => {
      selectSuggestion(el.dataset.code);
    });
  });
};

const hideSuggestions = () => {
  if (tickerSuggestions) {
    tickerSuggestions.classList.add("hidden");
    tickerSuggestions.innerHTML = "";
  }
  currentSuggestionIndex = -1;
};

const selectSuggestion = (code) => {
  if (tickerInput) {
    tickerInput.value = code;
  }
  hideSuggestions();
  addTicker();
};

const navigateSuggestions = (direction) => {
  const suggestions = tickerSuggestions?.querySelectorAll(".ticker-suggestion");
  if (!suggestions || suggestions.length === 0) return;

  // Remove previous selection
  suggestions.forEach((s) => s.classList.remove("selected"));

  if (direction === "down") {
    currentSuggestionIndex = Math.min(currentSuggestionIndex + 1, suggestions.length - 1);
  } else {
    currentSuggestionIndex = Math.max(currentSuggestionIndex - 1, 0);
  }

  suggestions[currentSuggestionIndex]?.classList.add("selected");
};

// ========================================
// TICKER MANAGEMENT
// ========================================
const normalizeTicker = (value) => value.trim().toUpperCase();

const updateTickerCount = () => {
  if (tickerCount) {
    const count = userTickers.size;
    tickerCount.textContent = `${count} ${count === 1 ? "ativo" : "ativos"}`;
  }
};

const renderUserTickers = () => {
  if (!tickerList) return;

  // Clear existing ticker items
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
          <button class="ticker-item-remove" type="button" aria-label="Remover ${ticker}">✕</button>
        `;

        item.querySelector(".ticker-item-remove").addEventListener("click", () => removeTicker(ticker));
        tickerList.appendChild(item);
      });
  }

  updateTickerCount();
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
    hideSuggestions();
    return;
  }

  // Add to local state
  userTickers.add(raw);
  tickerInput.value = "";
  hideSuggestions();

  // Update local storage
  localStorage.setItem(TICKERS_KEY, JSON.stringify(Array.from(userTickers)));

  // Save to server
  await savePortfolioToServer();

  renderUserTickers();
  showToast(`${raw} adicionado à sua carteira!`, "success");
};

const removeTicker = async (ticker) => {
  userTickers.delete(ticker);

  // Update local storage
  localStorage.setItem(TICKERS_KEY, JSON.stringify(Array.from(userTickers)));

  // Save to server
  await savePortfolioToServer();

  renderUserTickers();
  showToast(`${ticker} removido da carteira.`, "info");
};

const savePortfolioToServer = async () => {
  const session = getSession();
  if (!session.token || !session.email) return;

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
  }
};

const loadTickers = async () => {
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

// Função para buscar dados do usuário da planilha
const fetchUserDataFromSheet = async (email) => {
  try {
    // Tenta buscar via getPortfolio
    const session = getSession();
    if (!session.token) return null;
    
    const result = await postToScript({
      action: "getPortfolio",
      token: session.token,
      email: email,
    });

    if (result.ok && result.data) {
      return result.data;
    }
  } catch (error) {
    console.log("getPortfolio não disponível, usando dados do login");
  }
  return null;
};

// ========================================
// EVENT HANDLERS
// ========================================

// Mobile menu
mobileMenuBtn?.addEventListener("click", () => {
  mobileMenuBtn.classList.toggle("active");
  mobileNav?.classList.toggle("hidden");
});

// Close mobile menu on link click
mobileNav?.querySelectorAll("a").forEach((link) => {
  link.addEventListener("click", () => {
    mobileMenuBtn?.classList.remove("active");
    mobileNav?.classList.add("hidden");
  });
});

// Dashboard navigation
navDashboard?.addEventListener("click", (e) => {
  const item = e.target.closest(".nav-dashboard-item");
  if (item) {
    showSection(item.dataset.section);
  }
});

// Signup form
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
    showToast("🎉 Conta criada com sucesso!", "success", 5000);
  } catch (error) {
    showToast(error.message || "Erro ao conectar com o servidor.", "error");
  } finally {
    setLoading(submitButton, false);
  }
});

// Login form
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

    // Pega dados da resposta do login
    const name = result.data.name || "";
    const tickersFromLogin = result.data.tickers || "";
    
    // Parse tickers
    let tickerArray = [];
    if (tickersFromLogin) {
      tickerArray = tickersFromLogin
        .split(",")
        .map((t) => t.trim().toUpperCase())
        .filter((t) => t);
    }

    console.log("Login - Nome:", name, "Tickers:", tickerArray);

    // Salva sessão com os tickers do login
    setSession(result.data.token, email, name, tickerArray);
    loginForm.reset();
    
    showToast("✓ Login realizado!", "success");

    // Tenta buscar dados atualizados do servidor
    const freshData = await fetchUserDataFromSheet(email);
    if (freshData) {
      console.log("Dados do servidor:", freshData);
      if (freshData.name) {
        localStorage.setItem(NAME_KEY, freshData.name);
      }
      if (freshData.tickers) {
        const freshTickers = freshData.tickers
          .split(",")
          .map((t) => t.trim().toUpperCase())
          .filter((t) => t);
        console.log("Tickers do servidor:", freshTickers);
        localStorage.setItem(TICKERS_KEY, JSON.stringify(freshTickers));
      }
    }

    // Mostra dashboard
    showDashboard();
  } catch (error) {
    showToast(error.message || "Erro ao conectar com o servidor.", "error");
  } finally {
    setLoading(submitButton, false);
  }
});

// Logout
logoutButton?.addEventListener("click", () => {
  clearSession();
  showLandingPage();
  showToast("Você saiu da sua conta.", "info");
});

// Ticker input - autocomplete
tickerInput?.addEventListener("input", (e) => {
  const value = e.target.value.trim();
  if (value.length >= 1) {
    showSuggestions(value);
  } else {
    hideSuggestions();
  }
});

tickerInput?.addEventListener("keydown", (event) => {
  const suggestions = tickerSuggestions?.querySelectorAll(".ticker-suggestion");
  
  if (event.key === "ArrowDown" && suggestions?.length > 0) {
    event.preventDefault();
    navigateSuggestions("down");
  } else if (event.key === "ArrowUp" && suggestions?.length > 0) {
    event.preventDefault();
    navigateSuggestions("up");
  } else if (event.key === "Enter") {
    event.preventDefault();
    if (currentSuggestionIndex >= 0 && suggestions?.[currentSuggestionIndex]) {
      selectSuggestion(suggestions[currentSuggestionIndex].dataset.code);
    } else {
      addTicker();
    }
  } else if (event.key === "Escape") {
    hideSuggestions();
  }
});

tickerInput?.addEventListener("blur", () => {
  // Delay to allow click on suggestions
  setTimeout(hideSuggestions, 200);
});

// Add ticker button
addTickerButton?.addEventListener("click", addTicker);

// Close suggestions on outside click
document.addEventListener("click", (e) => {
  if (!e.target.closest(".ticker-autocomplete")) {
    hideSuggestions();
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
    // Tenta buscar dados atualizados do servidor
    const session = getSession();
    const freshData = await fetchUserDataFromSheet(session.email);
    
    if (freshData) {
      console.log("Boot - Dados do servidor:", freshData);
      if (freshData.name) {
        localStorage.setItem(NAME_KEY, freshData.name);
      }
      if (freshData.tickers) {
        const freshTickers = freshData.tickers
          .split(",")
          .map((t) => t.trim().toUpperCase())
          .filter((t) => t);
        console.log("Boot - Tickers:", freshTickers);
        localStorage.setItem(TICKERS_KEY, JSON.stringify(freshTickers));
      }
    }

    showDashboard();
  } else {
    showLandingPage();
  }
};

boot();
