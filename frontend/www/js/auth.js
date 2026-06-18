// Экран входа / регистрации. После успеха — редирект по состоянию профиля.

let mode = "login"; // login | register

const titleEl = document.getElementById("auth-title");
const nameField = document.getElementById("name-field");
const submitBtn = document.getElementById("a-submit");
const switchBtn = document.getElementById("a-switch");
const msgEl = document.getElementById("auth-msg");

// Уже авторизован → не показываем экран входа
if (isAuthed()) {
  routeAfterAuth();
}

function setMode(m) {
  mode = m;
  if (m === "register") {
    titleEl.textContent = "Создать аккаунт";
    nameField.hidden = false;
    submitBtn.textContent = "Зарегистрироваться";
    switchBtn.textContent = "Уже есть аккаунт? Войти";
  } else {
    titleEl.textContent = "Вход в аккаунт";
    nameField.hidden = true;
    submitBtn.textContent = "Войти";
    switchBtn.textContent = "Нет аккаунта? Регистрация";
  }
  setMsg("");
}

function setMsg(text, isError) {
  msgEl.textContent = text;
  msgEl.style.color = isError ? "#e3596a" : "#41d18f";
}

switchBtn.addEventListener("click", () => setMode(mode === "login" ? "register" : "login"));

submitBtn.addEventListener("click", submit);
document.getElementById("a-password").addEventListener("keydown", (e) => {
  if (e.key === "Enter") submit();
});

async function submit() {
  const email = document.getElementById("a-email").value.trim();
  const password = document.getElementById("a-password").value;
  const name = document.getElementById("a-name").value.trim();

  if (!email || !password) {
    setMsg("Введите email и пароль.", true);
    return;
  }

  // Вход в админ-панель: email = admin, пароль = секрет (ADMIN_SECRET на бэке).
  if (email.toLowerCase() === "admin") {
    submitBtn.disabled = true;
    const res = await apiPost("/api/admin/login", { secret: password });
    submitBtn.disabled = false;
    if (res.ok && res.data && res.data.token) {
      localStorage.setItem("afc_admin_token", res.data.token);
      window.location.href = "admin.html";
    } else {
      setMsg(errorText(res.data, "Неверный секрет."), true);
    }
    return;
  }
  if (mode === "register" && name && name.length < 2) {
    setMsg("Имя должно быть не короче 2 символов.", true);
    return;
  }
  if (mode === "register" && password.length < 6) {
    setMsg("Пароль слишком короткий: минимум 6 символов.", true);
    return;
  }

  submitBtn.disabled = true;
  const path = mode === "register" ? "/api/auth/register" : "/api/auth/login";
  const body = mode === "register"
    ? { email, password, full_name: name || null }
    : { email, password };

  const res = await apiPost(path, body);
  submitBtn.disabled = false;

  if (res.ok && res.data && res.data.token) {
    setToken(res.data.token);
    setMsg("Готово!", false);
    routeAfterAuth();
  } else {
    setMsg(errorText(res.data, "Не удалось войти."), true);
  }
}

// Куда отправить после входа: не прошёл онбординг → onboarding, иначе → app.
async function routeAfterAuth() {
  const res = await apiGet("/api/user/me");
  if (res.ok && res.data) {
    window.location.href = res.data.onboarded ? "app.html" : "onboarding.html";
  } else if (res.status === 401) {
    clearToken();
    // остаёмся на странице входа
  } else {
    // сервер недоступен — пусть попробует онбординг локально
    window.location.href = "onboarding.html";
  }
}
