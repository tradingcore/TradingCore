const FIREBASE_CONFIG = window.FIREBASE_CONFIG || {};
if (!FIREBASE_CONFIG.apiKey || FIREBASE_CONFIG.apiKey === "REPLACE_ME") {
  console.error("Configure o FIREBASE_CONFIG em index.html.");
}

firebase.initializeApp(FIREBASE_CONFIG);
const auth = firebase.auth();
const db = firebase.firestore();

// ========================================
// FERIADOS ANBIMA (2024-2030)
// ========================================
const FERIADOS = {
  "2024": ["01-01", "02-12", "02-13", "03-29", "04-21", "05-01", "05-30", "09-07", "10-12", "11-02", "11-15", "11-20", "12-25"],
  "2025": ["01-01", "03-03", "03-04", "04-18", "04-21", "05-01", "06-19", "09-07", "10-12", "11-02", "11-15", "11-20", "12-25"],
  "2026": ["01-01", "02-16", "02-17", "04-03", "04-21", "05-01", "06-04", "09-07", "10-12", "11-02", "11-15", "11-20", "12-25"],
  "2027": ["01-01", "02-08", "02-09", "03-26", "04-21", "05-01", "05-27", "09-07", "10-12", "11-02", "11-15", "11-20", "12-25"],
  "2028": ["01-01", "02-28", "02-29", "04-14", "04-21", "05-01", "06-15", "09-07", "10-12", "11-02", "11-15", "11-20", "12-25"],
  "2029": ["01-01", "02-12", "02-13", "03-30", "04-21", "05-01", "05-31", "09-07", "10-12", "11-02", "11-15", "11-20", "12-25"],
  "2030": ["01-01", "03-04", "03-05", "04-19", "04-21", "05-01", "06-20", "09-07", "10-12", "11-02", "11-15", "11-20", "12-25"]
};

const FERIADOS_NOMES = {
  "01-01": "Confraternização Universal",
  "02-08": "Carnaval", "02-09": "Carnaval", "02-12": "Carnaval", "02-13": "Carnaval",
  "02-16": "Carnaval", "02-17": "Carnaval", "02-28": "Carnaval", "02-29": "Carnaval",
  "03-03": "Carnaval", "03-04": "Carnaval", "03-05": "Carnaval",
  "03-26": "Paixão de Cristo", "03-29": "Paixão de Cristo", "03-30": "Paixão de Cristo",
  "04-03": "Paixão de Cristo", "04-14": "Paixão de Cristo", "04-18": "Paixão de Cristo", "04-19": "Paixão de Cristo",
  "04-21": "Tiradentes",
  "05-01": "Dia do Trabalho",
  "05-27": "Corpus Christi", "05-30": "Corpus Christi", "05-31": "Corpus Christi",
  "06-04": "Corpus Christi", "06-15": "Corpus Christi", "06-19": "Corpus Christi", "06-20": "Corpus Christi",
  "09-07": "Independência",
  "10-12": "N. Sra. Aparecida",
  "11-02": "Finados",
  "11-15": "Proclamação da República",
  "11-20": "Consciência Negra",
  "12-25": "Natal"
};

const TOKEN_KEY = "tc_token";
const EMAIL_KEY = "tc_email";
const NAME_KEY = "tc_name";
const TICKERS_KEY = "tc_tickers";
const PHONE_KEY = "tc_phone";
const ADDRESS_KEY = "tc_address";
const BIRTHDATE_KEY = "tc_birthdate";

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
const sectionNoticias = document.getElementById("section-noticias");

// DOM Elements - News Section
const newsContainer = document.getElementById("news-container");
const emptyNews = document.getElementById("empty-news");
const newsLoading = document.getElementById("news-loading");
const newsDateBadge = document.getElementById("news-date");
const newsDateInput = document.getElementById("news-date-input");
const loadNewsBtn = document.getElementById("load-news-btn");

// DOM Elements - Destaque
const destaqueContainer = document.getElementById("destaque-container");
const destaqueTicker = document.getElementById("destaque-ticker");
const destaqueTitulo = document.getElementById("destaque-titulo");
const destaqueResumo = document.getElementById("destaque-resumo");
const destaqueSentimento = document.getElementById("destaque-sentimento");

// DOM Elements - Calendar
const calendarContainer = document.getElementById("calendar-container");
const calendarToggle = document.getElementById("calendar-toggle");
const calendarArrow = document.getElementById("calendar-arrow");
const calendarMonthYear = document.getElementById("calendar-month-year");
const calendarDays = document.getElementById("calendar-days");
const calendarPrev = document.getElementById("calendar-prev");
const calendarNext = document.getElementById("calendar-next");

// Calendar State
let currentCalendarMonth = new Date().getMonth();
let currentCalendarYear = new Date().getFullYear();
let availableNewsDates = new Map(); // Map<dateStr, sentimentAvg>
let calendarExpanded = false;

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
const profileDisplayName = document.getElementById("profile-display-name");
const profileDisplayEmail = document.getElementById("profile-display-email");
const profileForm = document.getElementById("profile-form");
const profileName = document.getElementById("profile-name");
const profileEmail = document.getElementById("profile-email");
const profilePhone = document.getElementById("profile-phone");
const profileAddress = document.getElementById("profile-address");
const profileBirthdate = document.getElementById("profile-birthdate");
const saveProfileBtn = document.getElementById("save-profile-btn");

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
const setSession = (token, email, userData = {}) => {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(EMAIL_KEY, email);
  if (userData.name) localStorage.setItem(NAME_KEY, userData.name);
  if (userData.tickers !== undefined) localStorage.setItem(TICKERS_KEY, JSON.stringify(userData.tickers || []));
  if (userData.phone !== undefined) localStorage.setItem(PHONE_KEY, userData.phone);
  if (userData.address !== undefined) localStorage.setItem(ADDRESS_KEY, userData.address);
  if (userData.birthdate !== undefined) localStorage.setItem(BIRTHDATE_KEY, userData.birthdate);
};

const clearSession = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(EMAIL_KEY);
  localStorage.removeItem(NAME_KEY);
  localStorage.removeItem(TICKERS_KEY);
  localStorage.removeItem(PHONE_KEY);
  localStorage.removeItem(ADDRESS_KEY);
  localStorage.removeItem(BIRTHDATE_KEY);
  userTickers.clear();
};

const getSession = () => ({
  token: localStorage.getItem(TOKEN_KEY),
  email: localStorage.getItem(EMAIL_KEY),
  name: localStorage.getItem(NAME_KEY),
  tickers: JSON.parse(localStorage.getItem(TICKERS_KEY) || "[]"),
  phone: localStorage.getItem(PHONE_KEY) || "",
  address: localStorage.getItem(ADDRESS_KEY) || "",
  birthdate: localStorage.getItem(BIRTHDATE_KEY) || "",
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
  
  // Update profile header
  if (profileAvatar) profileAvatar.textContent = displayName.charAt(0).toUpperCase();
  if (profileDisplayName) profileDisplayName.textContent = displayName;
  if (profileDisplayEmail) profileDisplayEmail.textContent = session.email || "-";
  
  // Fill profile form
  if (profileName) profileName.value = session.name || "";
  if (profileEmail) profileEmail.value = session.email || "";
  if (profilePhone) profilePhone.value = session.phone || "";
  if (profileAddress) profileAddress.value = session.address || "";
  if (profileBirthdate) profileBirthdate.value = session.birthdate || "";
  
  // Load tickers from session
  userTickers.clear();
  session.tickers.forEach((t) => {
    if (t && t.trim()) userTickers.add(t.trim().toUpperCase());
  });
  renderUserTickers();
  
  // Atualizar ticker tape com ativos do usuário
  loadTickerTape();
  
  // Show carteira section by default
  showSection("carteira");
};

const showSection = (sectionName) => {
  // Hide all sections
  if (sectionCarteira) sectionCarteira.classList.add("hidden");
  if (sectionPerfil) sectionPerfil.classList.add("hidden");
  if (sectionNoticias) sectionNoticias.classList.add("hidden");
  
  // Show target section
  if (sectionName === "carteira" && sectionCarteira) {
    sectionCarteira.classList.remove("hidden");
  } else if (sectionName === "perfil" && sectionPerfil) {
    sectionPerfil.classList.remove("hidden");
  } else if (sectionName === "noticias" && sectionNoticias) {
    sectionNoticias.classList.remove("hidden");
    // Atualizar status do mercado e carregar notícias
    updateMarketStatus();
    loadTodayNews();
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
  loadTickerTape(); // Atualizar ticker tape com novo ativo
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
  const user = auth.currentUser;
  if (!user) return;

  const tickers = Array.from(userTickers);

  try {
    await getUserDocRef(user.uid).set(
      {
        tickers,
        updatedAt: firebase.firestore.FieldValue.serverTimestamp(),
      },
      { merge: true }
    );
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
// FIREBASE HELPERS
// ========================================
const ensureFirebaseReady = () => {
  if (!FIREBASE_CONFIG.apiKey || FIREBASE_CONFIG.apiKey === "REPLACE_ME") {
    showToast("Configure o Firebase em index.html.", "error");
    return false;
  }
  return true;
};

const getUserDocRef = (uid) => db.collection("users").doc(uid);

const normalizeTickers = (value) => {
  if (Array.isArray(value)) {
    return value.map((t) => String(t).trim().toUpperCase()).filter((t) => t);
  }
  if (typeof value === "string") {
    return value
      .split(",")
      .map((t) => t.trim().toUpperCase())
      .filter((t) => t);
  }
  return [];
};

const fetchUserDataFromFirestore = async (uid) => {
  try {
    const snap = await getUserDocRef(uid).get();
    if (!snap.exists) return null;
    return snap.data();
  } catch (error) {
    console.error("Erro ao buscar perfil:", error);
    return null;
  }
};

const saveUserDataToStorage = (data) => {
  if (!data) return;

  if (data.name) localStorage.setItem(NAME_KEY, data.name);
  if (data.phone !== undefined) localStorage.setItem(PHONE_KEY, data.phone);
  if (data.address !== undefined) localStorage.setItem(ADDRESS_KEY, data.address);
  if (data.birthdate !== undefined) localStorage.setItem(BIRTHDATE_KEY, data.birthdate);

  if (data.tickers !== undefined) {
    const tickerArray = normalizeTickers(data.tickers);
    localStorage.setItem(TICKERS_KEY, JSON.stringify(tickerArray));
  }
};

const getAuthErrorMessage = (error) => {
  const code = error?.code || "";
  if (code.includes("auth/email-already-in-use")) {
    return "E-mail já cadastrado.";
  }
  if (code.includes("auth/invalid-email")) {
    return "E-mail inválido.";
  }
  if (code.includes("auth/weak-password")) {
    return "A senha precisa ter pelo menos 6 caracteres.";
  }
  if (code.includes("auth/invalid-credential") || code.includes("auth/wrong-password")) {
    return "Email ou senha incorretos.";
  }
  if (code.includes("auth/user-not-found")) {
    return "Usuário não encontrado.";
  }
  return error?.message || "Erro ao autenticar.";
};

const updateProfileOnServer = async (name, phone, address) => {
  const user = auth.currentUser;
  if (!user) return false;

  try {
    await getUserDocRef(user.uid).set(
      {
        name,
        phone,
        address,
        updatedAt: firebase.firestore.FieldValue.serverTimestamp(),
      },
      { merge: true }
    );
    return true;
  } catch (error) {
    console.error("Erro ao atualizar perfil:", error);
    return false;
  }
};

// ========================================
// TICKER TAPE (Cotações em tempo real)
// ========================================
const MARKET_TICKERS = [
  { symbol: "^BVSP", name: "IBOV", type: "index" },
  { symbol: "USDBRL=X", name: "Dólar", type: "currency" },
  { symbol: "EURBRL=X", name: "Euro", type: "currency" },
  { symbol: "GC=F", name: "Ouro", type: "commodity" },
  { symbol: "BTC-USD", name: "Bitcoin", type: "crypto" }
];

const loadTickerTape = async () => {
  const tickerTapeContent = document.getElementById("ticker-tape-content");
  if (!tickerTapeContent) return;

  try {
    // Buscar cotações de mercado
    const marketQuotes = await fetchMarketQuotes();
    
    // Buscar cotações da carteira do usuário (se logado)
    const userQuotes = await fetchUserPortfolioQuotes();
    
    // Combinar: primeiro mercado, depois carteira do usuário
    const allQuotes = [...marketQuotes, ...userQuotes];
    
    if (allQuotes && allQuotes.length > 0) {
      // Duplicar para efeito de loop contínuo
      const itemsHtml = [...allQuotes, ...allQuotes].map(q => createTickerItem(q)).join("");
      tickerTapeContent.innerHTML = itemsHtml;
    }
  } catch (error) {
    console.error("Erro ao carregar cotações:", error);
    tickerTapeContent.innerHTML = `<span class="ticker-tape-loading">Cotações indisponíveis</span>`;
  }
};

const fetchMarketQuotes = async () => {
  // Carregar dados do Firestore primeiro
  await loadMarketDataFromFirestore();
  
  const results = [];
  
  for (const ticker of MARKET_TICKERS) {
    const cachedData = getMarketQuote(ticker.symbol);
    
    if (cachedData) {
      console.log(`✓ ${ticker.name}:`, cachedData);
    } else {
      console.warn(`⚠ Sem dados para ${ticker.symbol}`);
    }
    
    results.push({
      symbol: ticker.name,
      price: cachedData?.price ?? null,
      change: cachedData?.change ?? 0,
      changePercent: cachedData?.changePercent ?? 0,
      type: ticker.type,
      hasData: !!cachedData
    });
  }
  
  return results;
};

const fetchUserPortfolioQuotes = async () => {
  const session = getSession();
  const tickers = session.tickers || [];
  
  if (tickers.length === 0) return [];
  
  // Garantir que o cache foi carregado
  await loadMarketDataFromFirestore();
  
  const results = [];
  
  for (const ticker of tickers) {
    const cachedData = getB3Quote(ticker);
    
    if (cachedData) {
      console.log(`✓ ${ticker}:`, cachedData);
      results.push({
        symbol: ticker,
        price: cachedData.price,
        change: cachedData.change || 0,
        changePercent: cachedData.changePercent || 0,
        type: "stock"
      });
    } else {
      console.warn(`⚠ Sem dados B3 para ${ticker}`);
      results.push({
        symbol: ticker,
        price: null,
        change: 0,
        changePercent: 0,
        type: "stock"
      });
    }
  }
  
  return results;
};

// Cache local para evitar múltiplas requisições ao Firestore
let marketQuotesCache = null;
let b3QuotesCache = null;
let cacheTimestamp = 0;
const CACHE_TTL = 60000; // 1 minuto

const loadMarketDataFromFirestore = async () => {
  const now = Date.now();
  
  // Se cache ainda é válido, retorna
  if (marketQuotesCache && (now - cacheTimestamp) < CACHE_TTL) {
    return;
  }
  
  try {
    // Buscar cotações de mercado
    const quotesDoc = await db.collection("market_data").doc("quotes").get();
    if (quotesDoc.exists) {
      marketQuotesCache = quotesDoc.data();
      console.log("📊 Cotações de mercado carregadas:", Object.keys(marketQuotesCache));
    } else {
      console.warn("⚠ Documento market_data/quotes não existe");
      marketQuotesCache = {};
    }
    
    // Buscar cotações B3
    const b3Doc = await db.collection("market_data").doc("b3_quotes").get();
    if (b3Doc.exists) {
      b3QuotesCache = b3Doc.data();
      console.log("💹 Cotações B3 carregadas:", Object.keys(b3QuotesCache));
    } else {
      console.warn("⚠ Documento market_data/b3_quotes não existe");
      b3QuotesCache = {};
    }
    
    cacheTimestamp = now;
  } catch (e) {
    console.error("❌ Erro ao carregar cotações do Firestore:", e);
    marketQuotesCache = {};
    b3QuotesCache = {};
  }
};

const getMarketQuote = (symbol) => {
  if (!marketQuotesCache) return null;
  return marketQuotesCache[symbol] || null;
};

const getB3Quote = (ticker) => {
  if (!b3QuotesCache) return null;
  return b3QuotesCache[ticker] || null;
};

const createTickerItem = (quote) => {
  const changeClass = quote.changePercent > 0 ? "up" : quote.changePercent < 0 ? "down" : "neutral";
  const changeSign = quote.changePercent > 0 ? "+" : "";
  
  // Formatação especial para cada tipo
  let priceStr;
  if (quote.price === null || quote.price === undefined) {
    priceStr = "...";
  } else if (quote.type === "index") {
    priceStr = Number(quote.price).toLocaleString("pt-BR", { maximumFractionDigits: 0 });
  } else if (quote.type === "crypto") {
    priceStr = `$${Number(quote.price).toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
  } else if (quote.type === "commodity") {
    priceStr = `$${Number(quote.price).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  } else if (quote.type === "stock") {
    priceStr = `R$ ${Number(quote.price).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  } else {
    // currency (Dólar, Euro)
    priceStr = `R$ ${Number(quote.price).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 4 })}`;
  }
  
  // Destacar visualmente os tickers do usuário
  const isUserStock = quote.type === "stock";
  const symbolClass = isUserStock ? "ticker-tape-symbol ticker-tape-symbol--user" : "ticker-tape-symbol";
  
  // Se tem dados válidos, mostrar variação
  const hasValidData = quote.price !== null && quote.price !== undefined;
  const changeHtml = hasValidData 
    ? `<span class="ticker-tape-change ticker-tape-change--${changeClass}">${changeSign}${Number(quote.changePercent).toFixed(2)}%</span>` 
    : "";
  
  return `
    <span class="ticker-tape-item${isUserStock ? " ticker-tape-item--user" : ""}">
      <span class="${symbolClass}">${quote.symbol}</span>
      <span class="ticker-tape-price">${priceStr}</span>
      ${changeHtml}
    </span>
    <span class="ticker-tape-separator">|</span>
  `;
};

// ========================================
// MARKET STATUS & HOLIDAYS
// ========================================
const ehFeriado = (date) => {
  const year = date.getFullYear().toString();
  const monthDay = `${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
  
  return FERIADOS[year]?.includes(monthDay) || false;
};

const ehFimDeSemana = (date) => {
  const day = date.getDay();
  return day === 0 || day === 6; // Domingo ou Sábado
};

const ehDiaUtil = (date) => {
  return !ehFimDeSemana(date) && !ehFeriado(date);
};

const getProximoFeriado = () => {
  const hoje = new Date();
  const anoAtual = hoje.getFullYear();
  
  // Verificar próximos 2 anos
  for (let ano = anoAtual; ano <= anoAtual + 1; ano++) {
    const feriados = FERIADOS[ano.toString()] || [];
    
    for (const mesDia of feriados) {
      const [mes, dia] = mesDia.split("-");
      const dataFeriado = new Date(ano, parseInt(mes) - 1, parseInt(dia));
      
      if (dataFeriado > hoje) {
        const nome = FERIADOS_NOMES[mesDia] || "Feriado";
        const diasRestantes = Math.ceil((dataFeriado - hoje) / (1000 * 60 * 60 * 24));
        
        return {
          data: dataFeriado,
          nome,
          diasRestantes,
          formatado: `${dia}/${mes} (${nome})`
        };
      }
    }
  }
  
  return null;
};

const getMarketStatus = () => {
  const agora = new Date();
  const hora = agora.getHours();
  const minuto = agora.getMinutes();
  const horaDecimal = hora + minuto / 60;
  
  // Verificar se é dia útil
  if (!ehDiaUtil(agora)) {
    if (ehFeriado(agora)) {
      const mesDia = `${String(agora.getMonth() + 1).padStart(2, "0")}-${String(agora.getDate()).padStart(2, "0")}`;
      const nome = FERIADOS_NOMES[mesDia] || "Feriado";
      return { open: false, status: "holiday", message: `Fechado - ${nome}` };
    }
    return { open: false, status: "closed", message: "Fechado - Fim de semana" };
  }
  
  // Horário do pregão B3: 10:00 - 17:55 (horário normal)
  if (horaDecimal >= 10 && horaDecimal < 17.92) {
    return { open: true, status: "open", message: "Mercado aberto" };
  }
  
  // Pré-abertura: 9:45 - 10:00
  if (horaDecimal >= 9.75 && horaDecimal < 10) {
    return { open: false, status: "preopen", message: "Pré-abertura" };
  }
  
  // After-market: 17:55 - 18:00
  if (horaDecimal >= 17.92 && horaDecimal < 18) {
    return { open: false, status: "aftermarket", message: "After-market" };
  }
  
  return { open: false, status: "closed", message: "Mercado fechado" };
};

const updateMarketStatus = () => {
  const indicator = document.getElementById("market-status-indicator");
  const statusText = document.getElementById("market-status-text");
  const holidayInfo = document.getElementById("holiday-info");
  
  // Status atual do mercado
  const status = getMarketStatus();
  
  if (indicator) {
    indicator.className = "market-status-indicator";
    if (status.status === "open") {
      indicator.classList.add("market-open");
    } else if (status.status === "holiday") {
      indicator.classList.add("market-holiday");
    } else {
      indicator.classList.add("market-closed");
    }
  }
  
  if (statusText) {
    statusText.textContent = status.message;
  }
  
  // Próximo feriado
  const proximoFeriado = getProximoFeriado();
  if (holidayInfo && proximoFeriado) {
    const diasTexto = proximoFeriado.diasRestantes === 1 
      ? "amanhã" 
      : `em ${proximoFeriado.diasRestantes} dias`;
    holidayInfo.textContent = `${proximoFeriado.formatado} - ${diasTexto}`;
  }
};

// ========================================
// NEWS FUNCTIONS
// ========================================
const formatDateBR = (dateStr) => {
  const [year, month, day] = dateStr.split("-");
  return `${day}/${month}/${year}`;
};

const getTodayDateStr = () => {
  const today = new Date();
  // Usar data local (não UTC) para corresponder ao backend
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, "0");
  const day = String(today.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

const loadTodayNews = async () => {
  const today = getTodayDateStr();
  
  // Carregar datas disponíveis para o calendário
  await loadAvailableNewsDates();
  
  // Carregar notícias de hoje
  loadNewsForDate(today);
};

const loadNewsForDate = async (dateStr) => {
  const user = auth.currentUser;
  if (!user) return;

  // Show loading
  if (newsLoading) newsLoading.classList.remove("hidden");
  if (emptyNews) emptyNews.classList.add("hidden");
  clearNewsContent();

  // Update date badge
  if (newsDateBadge) newsDateBadge.textContent = formatDateBR(dateStr);

  try {
    const newsRef = db.collection("users").doc(user.uid).collection("news").doc(dateStr);
    const doc = await newsRef.get();

    if (newsLoading) newsLoading.classList.add("hidden");

    if (!doc.exists) {
      if (emptyNews) emptyNews.classList.remove("hidden");
      return;
    }

    const data = doc.data();
    renderNews(data);
  } catch (error) {
    console.error("Erro ao carregar notícias:", error);
    if (newsLoading) newsLoading.classList.add("hidden");
    if (emptyNews) emptyNews.classList.remove("hidden");
    showToast("Erro ao carregar notícias. Tente novamente.", "error");
  }
};

const clearNewsContent = () => {
  if (!newsContainer) return;
  
  // Remove all news cards, keep empty state
  const newsCards = newsContainer.querySelectorAll(".news-ticker-card");
  newsCards.forEach((card) => card.remove());
  
  // Clear periodo
  const periodoValor = document.getElementById("news-periodo-valor");
  if (periodoValor) periodoValor.textContent = "--";
  
  // Hide destaque
  if (destaqueContainer) destaqueContainer.classList.add("hidden");
};

const renderNews = async (data) => {
  if (!newsContainer) return;

  const { resumos, consolidadas, precos, periodo_noticias, destaque } = data;
  
  // Check if there's any content
  const hasResumos = resumos && Object.keys(resumos).length > 0;
  const hasConsolidadas = consolidadas && Object.keys(consolidadas).length > 0;
  
  if (!hasResumos && !hasConsolidadas) {
    if (emptyNews) emptyNews.classList.remove("hidden");
    return;
  }

  if (emptyNews) emptyNews.classList.add("hidden");

  // Renderizar destaque do dia
  if (destaque && destaque.ticker) {
    renderDestaque(destaque);
  }

  // Mostrar período das notícias no header
  const periodoValor = document.getElementById("news-periodo-valor");
  if (periodoValor && periodo_noticias && periodo_noticias.de && periodo_noticias.ate) {
    periodoValor.textContent = `${formatDateRef(periodo_noticias.de)} → ${formatDateRef(periodo_noticias.ate)}`;
  }

  // Buscar histórico de sentimento para cada ticker
  const sentimentoHistorico = await getSentimentHistory();

  // Get all tickers (union of resumos and consolidadas)
  const tickers = new Set([
    ...Object.keys(resumos || {}),
    ...Object.keys(consolidadas || {})
  ]);

  // Render each ticker
  Array.from(tickers).sort().forEach((ticker) => {
    const resumo = resumos?.[ticker] || "";
    const consolidado = consolidadas?.[ticker] || {};
    const preco = precos?.[ticker] || {};
    const historico = sentimentoHistorico[ticker] || [];
    
    const card = createNewsCard(ticker, resumo, consolidado, preco, historico);
    newsContainer.appendChild(card);
  });
};

const getSentimentHistory = async () => {
  const user = auth.currentUser;
  if (!user) return {};

  try {
    // Buscar os últimos 7 dias de notícias
    const newsRef = db.collection("users").doc(user.uid).collection("news")
      .orderBy("data", "desc")
      .limit(7);
    
    const snapshot = await newsRef.get();
    
    // Organizar por ticker
    const porTicker = {};
    
    snapshot.forEach((doc) => {
      const data = doc.data();
      const dateStr = doc.id;
      const sentimentoHist = data.sentimento_historico || {};
      
      // Para cada ticker nesse dia
      Object.entries(sentimentoHist).forEach(([ticker, sentimento]) => {
        if (!porTicker[ticker]) {
          porTicker[ticker] = [];
        }
        porTicker[ticker].push({
          data: dateStr,
          sentimento: sentimento
        });
      });
    });
    
    // Ordenar por data (mais antigo primeiro)
    Object.keys(porTicker).forEach((ticker) => {
      porTicker[ticker].sort((a, b) => a.data.localeCompare(b.data));
    });
    
    return porTicker;
  } catch (error) {
    console.error("Erro ao buscar histórico de sentimento:", error);
    return {};
  }
};

const renderDestaque = (destaque) => {
  if (!destaqueContainer) return;
  
  const { ticker, titulo, resumo, sentimento } = destaque;
  
  // Mostrar container
  destaqueContainer.classList.remove("hidden");
  
  if (destaqueTicker) {
    destaqueTicker.textContent = ticker || "--";
  }
  
  if (destaqueTitulo) {
    destaqueTitulo.textContent = titulo || "--";
  }
  
  if (destaqueResumo) {
    destaqueResumo.textContent = resumo || "--";
  }
  
  if (destaqueSentimento) {
    const sent = sentimento || 0;
    let icon, text, className;
    
    if (sent > 0.3) {
      icon = "🟢";
      text = "Positivo";
      className = "destaque-sentimento--positivo";
    } else if (sent < -0.3) {
      icon = "🔴";
      text = "Negativo";
      className = "destaque-sentimento--negativo";
    } else {
      icon = "🟡";
      text = "Neutro";
      className = "destaque-sentimento--neutro";
    }
    
    destaqueSentimento.className = `destaque-sentimento ${className}`;
    destaqueSentimento.innerHTML = `${icon} ${text}`;
  }
};

// ========================================
// CALENDAR FUNCTIONS
// ========================================
const MONTH_NAMES = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
];

const loadAvailableNewsDates = async () => {
  const user = auth.currentUser;
  if (!user) return;

  try {
    // Buscar todos os documentos de notícias do usuário
    const newsRef = db.collection("users").doc(user.uid).collection("news");
    const snapshot = await newsRef.get();
    
    availableNewsDates.clear();
    
    snapshot.forEach((doc) => {
      const data = doc.data();
      const dateStr = doc.id; // formato YYYY-MM-DD
      
      // Calcular sentimento médio do dia
      let sentimentoMedio = 0;
      const sentimentoHist = data.sentimento_historico;
      
      if (sentimentoHist && Object.keys(sentimentoHist).length > 0) {
        const valores = Object.values(sentimentoHist);
        sentimentoMedio = valores.reduce((a, b) => a + b, 0) / valores.length;
      } else if (data.destaque && data.destaque.sentimento !== undefined) {
        sentimentoMedio = data.destaque.sentimento;
      }
      
      availableNewsDates.set(dateStr, sentimentoMedio);
    });
    
    renderCalendar();
  } catch (error) {
    console.error("Erro ao carregar datas disponíveis:", error);
  }
};

const renderCalendar = () => {
  if (!calendarDays || !calendarMonthYear) return;
  
  // Atualizar título
  calendarMonthYear.textContent = `${MONTH_NAMES[currentCalendarMonth]} ${currentCalendarYear}`;
  
  // Limpar dias
  calendarDays.innerHTML = "";
  
  // Primeiro dia do mês
  const firstDay = new Date(currentCalendarYear, currentCalendarMonth, 1);
  const startingDay = firstDay.getDay(); // 0 = Domingo
  
  // Último dia do mês
  const lastDay = new Date(currentCalendarYear, currentCalendarMonth + 1, 0);
  const totalDays = lastDay.getDate();
  
  // Dias vazios antes do primeiro dia
  for (let i = 0; i < startingDay; i++) {
    const emptyDay = document.createElement("div");
    emptyDay.className = "calendar-day calendar-day--empty";
    calendarDays.appendChild(emptyDay);
  }
  
  // Dias do mês
  const today = new Date();
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
  
  for (let day = 1; day <= totalDays; day++) {
    const dateStr = `${currentCalendarYear}-${String(currentCalendarMonth + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    
    const dayElement = document.createElement("div");
    dayElement.className = "calendar-day";
    dayElement.textContent = day;
    
    // Verificar se é hoje
    if (dateStr === todayStr) {
      dayElement.classList.add("calendar-day--today");
    }
    
    // Verificar se tem notícias nesse dia
    if (availableNewsDates.has(dateStr)) {
      dayElement.classList.add("calendar-day--has-news");
      
      // Colorir dia inteiro baseado no sentimento
      const sentimento = availableNewsDates.get(dateStr);
      
      if (sentimento > 0.2) {
        dayElement.classList.add("calendar-day--positive");
      } else if (sentimento < -0.2) {
        dayElement.classList.add("calendar-day--negative");
      } else {
        dayElement.classList.add("calendar-day--neutral");
      }
      
      // Adicionar evento de clique
      dayElement.addEventListener("click", () => {
        // Marcar dia selecionado
        document.querySelectorAll(".calendar-day--selected").forEach(el => el.classList.remove("calendar-day--selected"));
        dayElement.classList.add("calendar-day--selected");
        
        // Carregar notícias desse dia
        loadNewsForDate(dateStr);
        
        // Fechar calendário após seleção em mobile
        if (window.innerWidth <= 768) {
          toggleCalendar();
        }
      });
    } else {
      dayElement.classList.add("calendar-day--disabled");
    }
    
    calendarDays.appendChild(dayElement);
  }
};

// Toggle calendário
const toggleCalendar = () => {
  calendarExpanded = !calendarExpanded;
  
  if (calendarContainer) {
    calendarContainer.classList.toggle("hidden", !calendarExpanded);
  }
  
  if (calendarToggle) {
    calendarToggle.classList.toggle("active", calendarExpanded);
  }
};

const prevMonth = () => {
  currentCalendarMonth--;
  if (currentCalendarMonth < 0) {
    currentCalendarMonth = 11;
    currentCalendarYear--;
  }
  renderCalendar();
};

const nextMonth = () => {
  currentCalendarMonth++;
  if (currentCalendarMonth > 11) {
    currentCalendarMonth = 0;
    currentCalendarYear++;
  }
  renderCalendar();
};

const formatDateRef = (dateStr) => {
  if (!dateStr) return "";
  const [year, month, day] = dateStr.split("-");
  return `${day}/${month}`;
};

const createNewsCard = (ticker, resumo, consolidado, preco, sentimentoHistorico) => {
  const card = document.createElement("div");
  card.className = "news-ticker-card";

  // Header with ticker and price
  let precoHtml = "";
  if (preco.sucesso) {
    const variacao = preco.variacao_percentual || 0;
    const variacaoClass = variacao > 0 ? "variacao-positiva" : variacao < 0 ? "variacao-negativa" : "variacao-neutra";
    const variacaoSinal = variacao > 0 ? "+" : "";
    
    // Data de referência única (simplificado)
    const dataRef = preco.data_referencia ? formatDateRef(preco.data_referencia) : "";
    const dataRefHtml = dataRef ? `<span class="preco-data">(ref. ${dataRef})</span>` : "";
    
    precoHtml = `
      <div class="news-ticker-preco">
        <span class="preco-valor">R$ ${preco.preco_fechamento?.toFixed(2) || "0.00"}</span>
        <span class="${variacaoClass}">${variacaoSinal}${variacao.toFixed(2)}%</span>
        ${dataRefHtml}
      </div>
    `;
  }
  
  // Gráfico de sentimento (se houver histórico)
  let graficoHtml = "";
  if (sentimentoHistorico && sentimentoHistorico.length > 1) {
    graficoHtml = createSentimentChart(ticker, sentimentoHistorico);
  }

  // Executive summary
  let resumoHtml = "";
  if (resumo) {
    resumoHtml = `
      <div class="news-resumo">
        <h4>📋 Resumo Executivo</h4>
        <p>${resumo}</p>
      </div>
    `;
  }

  // Consolidated analysis
  let consolidadoHtml = "";
  if (consolidado.positivo || consolidado.negativo) {
    let positivoHtml = "";
    let negativoHtml = "";
    
    if (consolidado.positivo) {
      positivoHtml = `
        <div class="news-bloco news-bloco--positivo">
          <h5>🟢 Pontos Positivos</h5>
          <p>${consolidado.positivo}</p>
        </div>
      `;
    }
    
    if (consolidado.negativo) {
      negativoHtml = `
        <div class="news-bloco news-bloco--negativo">
          <h5>🔴 Pontos de Atenção</h5>
          <p>${consolidado.negativo}</p>
        </div>
      `;
    }
    
    consolidadoHtml = `
      <div class="news-consolidado">
        ${positivoHtml}
        ${negativoHtml}
      </div>
    `;
  }

  card.innerHTML = `
    <div class="news-ticker-header">
      <h3 class="news-ticker-code">${ticker}</h3>
      ${precoHtml}
    </div>
    ${graficoHtml}
    ${resumoHtml}
    ${consolidadoHtml}
  `;

  return card;
};

const createSentimentChart = (ticker, historico) => {
  if (!historico || historico.length < 2) return "";
  
  // Pegar últimos 7 dias
  const dados = historico.slice(-7);
  
  // Calcular tendência
  const primeiro = dados[0].sentimento;
  const ultimo = dados[dados.length - 1].sentimento;
  const tendencia = ultimo - primeiro;
  
  let tendenciaIcon, tendenciaText, tendenciaClass;
  if (tendencia > 0.1) {
    tendenciaIcon = "📈";
    tendenciaText = "Melhorando";
    tendenciaClass = "tendencia--positiva";
  } else if (tendencia < -0.1) {
    tendenciaIcon = "📉";
    tendenciaText = "Piorando";
    tendenciaClass = "tendencia--negativa";
  } else {
    tendenciaIcon = "➡️";
    tendenciaText = "Estável";
    tendenciaClass = "tendencia--neutra";
  }
  
  // Criar pontos do gráfico
  const maxSent = 1;
  const minSent = -1;
  const range = maxSent - minSent;
  
  const pontos = dados.map((d, i) => {
    const x = (i / (dados.length - 1)) * 100;
    const y = 100 - ((d.sentimento - minSent) / range) * 100;
    return `${x},${y}`;
  }).join(" ");
  
  // Criar labels de data
  const labels = dados.map(d => formatDateRef(d.data)).join("");
  
  return `
    <div class="sentiment-chart-container">
      <div class="sentiment-chart-header">
        <span class="sentiment-chart-title">📊 Sentimento (${dados.length} dias)</span>
        <span class="sentiment-tendencia ${tendenciaClass}">
          ${tendenciaIcon} ${tendenciaText}
        </span>
      </div>
      <div class="sentiment-chart">
        <svg viewBox="0 0 100 60" preserveAspectRatio="none" class="sentiment-chart-svg">
          <!-- Linha de zero -->
          <line x1="0" y1="30" x2="100" y2="30" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/>
          <!-- Área do gráfico -->
          <polyline 
            points="${pontos}"
            fill="none"
            stroke="url(#gradient-${ticker})"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <!-- Pontos -->
          ${dados.map((d, i) => {
            const x = (i / (dados.length - 1)) * 100;
            const y = 100 - ((d.sentimento - minSent) / range) * 100;
            const color = d.sentimento > 0.2 ? "#22c55e" : d.sentimento < -0.2 ? "#ef4444" : "#fbbf24";
            return `<circle cx="${x}" cy="${y}" r="3" fill="${color}"/>`;
          }).join("")}
          <defs>
            <linearGradient id="gradient-${ticker}" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stop-color="#5b7cfa"/>
              <stop offset="100%" stop-color="#22c55e"/>
            </linearGradient>
          </defs>
        </svg>
        <div class="sentiment-chart-labels">
          ${dados.map(d => `<span>${formatDateRef(d.data)}</span>`).join("")}
        </div>
      </div>
    </div>
  `;
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
  if (!ensureFirebaseReady()) return;

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
    const credential = await auth.createUserWithEmailAndPassword(email, password);
    const user = credential.user;

    await getUserDocRef(user.uid).set(
      {
        name,
        email,
        phone,
        address,
        birthdate,
        tickers: [],
        createdAt: firebase.firestore.FieldValue.serverTimestamp(),
      },
      { merge: true }
    );

    setSession(user.uid, email, {
      name,
      tickers: [],
      phone,
      address,
      birthdate,
    });
    signupForm.reset();
    showDashboard();
    showToast("🎉 Conta criada com sucesso!", "success", 5000);
  } catch (error) {
    showToast(getAuthErrorMessage(error), "error");
  } finally {
    setLoading(submitButton, false);
  }
});

// Login form
loginForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!ensureFirebaseReady()) return;

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
    const credential = await auth.signInWithEmailAndPassword(email, password);
    const user = credential.user;

    const profile = await fetchUserDataFromFirestore(user.uid);
    const tickers = normalizeTickers(profile?.tickers);

    setSession(user.uid, user.email || email, {
      name: profile?.name || "",
      tickers,
      phone: profile?.phone || "",
      address: profile?.address || "",
      birthdate: profile?.birthdate || "",
    });

    loginForm.reset();
    showToast("✓ Login realizado!", "success");
    showDashboard();
  } catch (error) {
    showToast(getAuthErrorMessage(error), "error");
  } finally {
    setLoading(submitButton, false);
  }
});

// Logout
logoutButton?.addEventListener("click", async () => {
  try {
    await auth.signOut();
  } catch (error) {
    console.error("Erro ao sair:", error);
  } finally {
    clearSession();
    showLandingPage();
    showToast("Você saiu da sua conta.", "info");
  }
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

// Calendar toggle
calendarToggle?.addEventListener("click", toggleCalendar);

// Calendar navigation
calendarPrev?.addEventListener("click", prevMonth);
calendarNext?.addEventListener("click", nextMonth);

// Profile form
profileForm?.addEventListener("submit", async (event) => {
  event.preventDefault();

  const name = profileName?.value?.trim() || "";
  const phone = profilePhone?.value?.trim() || "";
  const address = profileAddress?.value?.trim() || "";

  if (!name) {
    showToast("O nome é obrigatório.", "error");
    return;
  }

  if (saveProfileBtn) setLoading(saveProfileBtn, true);

  try {
    const success = await updateProfileOnServer(name, phone, address);

    if (success) {
      // Atualiza storage local
      localStorage.setItem(NAME_KEY, name);
      localStorage.setItem(PHONE_KEY, phone);
      localStorage.setItem(ADDRESS_KEY, address);

      // Atualiza displays
      const displayName = name || getSession().email?.split("@")[0] || "Usuário";
      if (headerUserAvatar) headerUserAvatar.textContent = displayName.charAt(0).toUpperCase();
      if (welcomeName) welcomeName.textContent = displayName;
      if (profileAvatar) profileAvatar.textContent = displayName.charAt(0).toUpperCase();
      if (profileDisplayName) profileDisplayName.textContent = displayName;

      showToast("Perfil atualizado com sucesso!", "success");
    } else {
      showToast("Erro ao salvar. Tente novamente.", "error");
    }
  } catch (error) {
    showToast("Erro ao conectar com o servidor.", "error");
  } finally {
    if (saveProfileBtn) setLoading(saveProfileBtn, false);
  }
});

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
  // Carregar ticker tape imediatamente
  loadTickerTape();
  
  // Atualizar ticker tape a cada 5 minutos
  setInterval(loadTickerTape, 5 * 60 * 1000);
  
  await loadTickers();

  auth.onAuthStateChanged(async (user) => {
    if (user) {
      let profile = await fetchUserDataFromFirestore(user.uid);

      if (!profile) {
        profile = {
          name: "",
          email: user.email || "",
          phone: "",
          address: "",
          birthdate: "",
          tickers: [],
        };
        await getUserDocRef(user.uid).set(
          {
            ...profile,
            createdAt: firebase.firestore.FieldValue.serverTimestamp(),
          },
          { merge: true }
        );
      }

      const tickers = normalizeTickers(profile.tickers);
      setSession(user.uid, user.email || "", {
        name: profile.name || "",
        tickers,
        phone: profile.phone || "",
        address: profile.address || "",
        birthdate: profile.birthdate || "",
      });

      showDashboard();
    } else {
      clearSession();
      showLandingPage();
    }
  });
};

boot();
