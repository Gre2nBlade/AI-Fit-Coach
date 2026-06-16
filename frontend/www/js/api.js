// Обёртка над fetch() к FastAPI-бэкенду.
// JWT хранится в localStorage и подставляется в Authorization: Bearer <token>.

// API_BASE настраивается в одном месте — js/config.js (window.AFC_API_BASE).
// В браузере по умолчанию http://localhost:8000.
// В APK (Capacitor) приложение грузится с https://localhost, поэтому там
// нужно указать реальный адрес бэкенда в config.js.
const API_BASE = (window.AFC_API_BASE || "http://localhost:8000").replace(/\/$/, "");

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
function isAuthed() {
  return !!getToken();
}

function authHeaders() {
  const t = getToken();
  return t ? { Authorization: "Bearer " + t } : {};
}

// Возвращает { ok, status, data }. Сетевые сбои не бросают исключение.
async function apiRequest(method, path, body) {
  try {
    const opts = { method, headers: { ...authHeaders() } };
    if (body !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    const resp = await fetch(API_BASE + path, opts);
    let data = null;
    try { data = await resp.json(); } catch (e) { data = null; }
    // 401 — токен протух/неверный: чистим и отправляем на вход
    if (resp.status === 401 && !path.startsWith("/api/auth/")) {
      clearToken();
    }
    return { ok: resp.ok, status: resp.status, data };
  } catch (e) {
    return { ok: false, status: 0, data: { detail: "Сервер недоступен. Запущен ли бэкенд?" } };
  }
}

const apiGet = (path) => apiRequest("GET", path);
const apiPost = (path, body) => apiRequest("POST", path, body || {});

// Текст ошибки из ответа FastAPI (detail может быть строкой или списком).
function errorText(data, fallback) {
  if (!data || data.detail == null) return fallback || "Что-то пошло не так.";
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) return data.detail.map((e) => e.msg).join(", ");
  return fallback || "Что-то пошло не так.";
}
