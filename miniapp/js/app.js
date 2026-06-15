// Логика MiniApp: вешаем кнопки на вызовы API и выводим JSON в <pre>.

// Сообщаем Telegram, что приложение готово.
if (window.Telegram && window.Telegram.WebApp) {
  window.Telegram.WebApp.ready();
  window.Telegram.WebApp.expand();
}

function show(elId, data) {
  document.getElementById(elId).textContent = JSON.stringify(data, null, 2);
}

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
