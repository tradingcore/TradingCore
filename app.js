const FIREBASE_CONFIG = window.FIREBASE_CONFIG || {};
if (!FIREBASE_CONFIG.apiKey || FIREBASE_CONFIG.apiKey === "REPLACE_ME") {
  console.error("Configure o FIREBASE_CONFIG em index.html.");
}

firebase.initializeApp(FIREBASE_CONFIG);
const auth = firebase.auth();
const db = firebase.firestore();

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
