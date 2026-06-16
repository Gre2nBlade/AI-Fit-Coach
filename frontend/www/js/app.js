// Точка входа фронта: вешаем обработчики и выбираем стартовый экран.

function show(elId, data) {
  document.getElementById(elId).textContent = JSON.stringify(data, null, 2);
}

// auth
document.getElementById("btn-login").addEventListener("click", doLogin);
document.getElementById("btn-register").addEventListener("click", doRegister);
document.getElementById("btn-logout").addEventListener("click", doLogout);

// dashboard
document.getElementById("btn-me").addEventListener("click", async () => {
  show("out-me", await apiGet("/api/user/me"));
});
document.getElementById("btn-plans").addEventListener("click", async () => {
  show("out-workout", await apiGet("/api/workout/plans"));
});
document.getElementById("btn-generate").addEventListener("click", async () => {
  show("out-workout", await apiPost("/api/workout/generate"));
});
document.getElementById("btn-diary").addEventListener("click", async () => {
  show("out-nutrition", await apiGet("/api/nutrition/diary"));
});

// стартовый экран зависит от наличия токена
if (getToken()) {
  showDashboard();
} else {
  showAuth();
}
