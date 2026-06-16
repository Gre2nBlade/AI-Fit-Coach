// Обёртка над fetch() к FastAPI-бэкенду.
// JWT хранится в localStorage и подставляется в Authorization: Bearer <token>.

// ВАЖНО: в APK (Capacitor) приложение грузится с capacitor://localhost,
// поэтому API_BASE должен указывать на реальный адрес бэкенда.
// Для локальной разработки в браузере — http://localhost:8000.
const API_BASE = "http://localhost:8000";

const TOKEN_KEY = "afc_token";

function getToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function authHeaders() {
  const t = getToken();
  return t ? { Authorization: "Bearer " + t } : {};
}

async function apiGet(path) {
  try {
    const resp = await fetch(API_BASE + path, {
      method: "GET",
      headers: { ...authHeaders() },
    });
    return resp.json();
  } catch (e) {
    return { detail: "Сервер недоступен. Запущен ли бэкенд?" };
  }
}

async function apiPost(path, body) {
  try {
    const resp = await fetch(API_BASE + path, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(body || {}),
    });
    return resp.json();
  } catch (e) {
    return { detail: "Сервер недоступен. Запущен ли бэкенд?" };
  }
}
