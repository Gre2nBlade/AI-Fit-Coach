// Регистрация / вход / выход. Управляет переключением экранов.

function showDashboard() {
  document.getElementById("auth-screen").hidden = true;
  document.getElementById("dash-screen").hidden = false;
}

function showAuth() {
  document.getElementById("auth-screen").hidden = false;
  document.getElementById("dash-screen").hidden = true;
}

function setAuthMessage(text, isError) {
  const el = document.getElementById("out-auth");
  el.textContent = text;
  el.style.color = isError ? "#c00" : "#080";
}

// FastAPI кладёт текст ошибки в res.detail (строка или список) — достаём читаемо.
function errorText(res) {
  if (!res || res.detail == null) return "Что-то пошло не так.";
  if (typeof res.detail === "string") return res.detail;
  return res.detail.map((e) => e.msg).join(", ");
}

async function doRegister() {
  const body = {
    email: document.getElementById("inp-email").value,
    password: document.getElementById("inp-password").value,
    full_name: document.getElementById("inp-name").value || null,
  };
  const res = await apiPost("/api/auth/register", body);
  if (res.token) {
    setToken(res.token);
    setAuthMessage("Регистрация прошла успешно.", false);
    showDashboard();
  } else {
    setAuthMessage(errorText(res), true);
  }
}

async function doLogin() {
  const body = {
    email: document.getElementById("inp-email").value,
    password: document.getElementById("inp-password").value,
  };
  const res = await apiPost("/api/auth/login", body);
  if (res.token) {
    setToken(res.token);
    setAuthMessage("Вход выполнен.", false);
    showDashboard();
  } else {
    setAuthMessage(errorText(res), true);
  }
}

function doLogout() {
  clearToken();
  showAuth();
}
