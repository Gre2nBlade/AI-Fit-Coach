// Обёртка над fetch() к FastAPI.
// Каждый запрос передаёт Telegram initData в заголовке X-Telegram-Init-Data —
// сервер проверяет HMAC-подпись (api/dependencies.py).

// База API. При локальной отдаче статики через FastAPI можно оставить пустым ("").
const API_BASE = "";

function getInitData() {
  // Telegram.WebApp.initData — подписанная строка с данными пользователя.
  if (window.Telegram && window.Telegram.WebApp) {
    return window.Telegram.WebApp.initData || "";
  }
  return "";
}

async function apiGet(path) {
  const resp = await fetch(API_BASE + path, {
    method: "GET",
    headers: { "X-Telegram-Init-Data": getInitData() },
  });
  return resp.json();
}

async function apiPost(path, body) {
  const resp = await fetch(API_BASE + path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Telegram-Init-Data": getInitData(),
    },
    body: JSON.stringify(body || {}),
  });
  return resp.json();
}
