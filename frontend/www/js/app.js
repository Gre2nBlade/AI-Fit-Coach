// Логика приложения: грузит профиль с бэкенда, наполняет дашборд расчётами,
// ИИ-чат через API, логаут, загрузка аватарки.

let PROFILE = null;

/* ---------- Гард: без токена — на вход ---------- */
if (!isAuthed()) {
  window.location.replace("index.html");
}

/* ---------- Навигация по вью ---------- */
const navItems = document.querySelectorAll(".nav-item[data-view]");
const views = document.querySelectorAll(".view");

function showView(name) {
  views.forEach((v) => v.classList.toggle("active", v.dataset.view === name));
  navItems.forEach((n) => n.classList.toggle("active", n.dataset.view === name));
  window.scrollTo(0, 0);
}
navItems.forEach((btn) => btn.addEventListener("click", () => showView(btn.dataset.view)));
document.querySelectorAll("[data-goto]").forEach((btn) =>
  btn.addEventListener("click", () => showView(btn.dataset.goto))
);
document.querySelectorAll("[data-goto-onb]").forEach((btn) =>
  btn.addEventListener("click", () => { window.location.href = "onboarding.html"; })
);

/* ---------- Логаут ---------- */
document.getElementById("btn-logout").addEventListener("click", () => {
  clearToken();
  window.location.href = "index.html";
});

/* ---------- Загрузка профиля ---------- */
async function loadProfile() {
  const res = await apiGet("/api/user/me");
  if (res.status === 401) { window.location.replace("index.html"); return; }
  if (!res.ok || !res.data) return;
  // онбординг не пройден — отправим туда
  if (!res.data.onboarded) { window.location.replace("onboarding.html"); return; }
  PROFILE = res.data;
  fillProfile(PROFILE);
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el != null) el.textContent = text;
}

function fillProfile(p) {
  const name = p.full_name || "Спортсмен";
  const initial = name.charAt(0).toUpperCase();

  setText("hello-name", name);
  setText("side-name", name);
  setText("side-goal", "Цель: " + (p.goal || "—"));
  setText("profile-name", name);
  setText("profile-goal", p.goal || "—");

  // аватарки (текст-инициал или фото)
  applyAvatar(p.avatar, initial);

  // данные профиля
  const dataEl = document.getElementById("profile-data");
  if (dataEl) {
    dataEl.innerHTML = [
      ["Имя", p.full_name], ["Возраст", p.age], ["Пол", p.sex],
      ["Рост", p.height_cm], ["Вес", p.weight_kg], ["Цель (вес)", p.goal_weight_kg],
      ["Уровень", p.level], ["Место", p.place], ["Дни", p.training_days],
    ].map(([k, v]) => `<div class="data-row"><span>${k}</span><span class="v">${v || "—"}</span></div>`).join("");
  }

  // мини-блок в профиле
  const minis = document.querySelectorAll(".profile-mini .big");
  if (minis.length === 3) {
    minis[0].textContent = p.age || "—";
    minis[1].textContent = p.height_cm || "—";
    minis[2].textContent = p.weight_kg || "—";
  }

  // метрики (с бэка или локально)
  const m = p.metrics || computeMetrics(p);
  if (m) fillMetrics(m);
}

function fillMetrics(m) {
  setText("m-calories", m.calories + " ккал");
  setText("m-bmi", m.bmi);
  setText("m-water", m.water_l + " л");

  // подпись к ИМТ
  let cat = "Норма";
  if (m.bmi < 18.5) cat = "Недовес";
  else if (m.bmi >= 25 && m.bmi < 30) cat = "Избыточный";
  else if (m.bmi >= 30) cat = "Ожирение";
  setText("m-bmi-lbl", "ИМТ · " + cat);

  // КБЖУ-граммы в питании
  setText("g-protein", m.protein_g + "г");
  setText("g-carbs", m.carbs_g + "г");
  setText("g-fat", m.fat_g + "г");
}

function applyAvatar(dataUrl, initial) {
  document.querySelectorAll(".avatar").forEach((a) => {
    if (a.id === "avatar-input") return;
    if (dataUrl) {
      a.style.backgroundImage = `url(${dataUrl})`;
      a.textContent = "";
    } else {
      a.style.backgroundImage = "";
      a.textContent = initial;
    }
  });
}

/* ---------- Аватарка: загрузка ---------- */
const avatarBox = document.getElementById("profile-avatar");
const avatarInput = document.getElementById("avatar-input");
if (avatarBox && avatarInput) {
  avatarBox.addEventListener("click", () => avatarInput.click());
  avatarInput.addEventListener("change", () => {
    const file = avatarInput.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async () => {
      const dataUrl = reader.result;
      const initial = (PROFILE?.full_name || "С").charAt(0).toUpperCase();
      applyAvatar(dataUrl, initial);
      const res = await apiPost("/api/user/profile", { avatar: dataUrl });
      if (res.ok && PROFILE) PROFILE.avatar = dataUrl;
    };
    reader.readAsDataURL(file);
  });
}

/* ---------- Переключатели настроек ---------- */
document.querySelectorAll("[data-toggle]").forEach((t) =>
  t.addEventListener("click", () => t.classList.toggle("on"))
);

/* ---------- Вкладки-чипы (визуальное переключение) ---------- */
document.querySelectorAll(".tabs").forEach((tabs) => {
  tabs.addEventListener("click", (e) => {
    const chip = e.target.closest(".chip");
    if (!chip) return;
    tabs.querySelectorAll(".chip").forEach((c) => c.classList.remove("active"));
    chip.classList.add("active");
  });
});

/* ---------- Чат ИИ-тренер ---------- */
const chatBody = document.getElementById("chat-body");
const chatText = document.getElementById("chat-text");

function addMessage(text, mine) {
  const msg = document.createElement("div");
  msg.className = "msg" + (mine ? " me" : "");
  const initial = (PROFILE?.full_name || "Я").charAt(0).toUpperCase();
  const bubble = `<div class="bubble">${escapeHtml(text)}</div>`;
  msg.innerHTML = mine ? `<div class="avatar sm">${initial}</div>${bubble}` : bubble;
  chatBody.appendChild(msg);
  chatBody.scrollTop = chatBody.scrollHeight;
  return msg;
}

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

let chatBusy = false;
async function sendChat(text) {
  text = (text || "").trim();
  if (!text || chatBusy) return;
  chatBusy = true;
  addMessage(text, true);
  chatText.value = "";

  const thinking = addMessage("…думаю", false);
  const res = await apiPost("/api/ai/ask", { question: text });
  thinking.remove();

  if (res.ok && res.data && res.data.answer) {
    addMessage(res.data.answer, false);
  } else {
    addMessage(errorText(res.data, "Не удалось получить ответ ИИ."), false);
  }
  chatBusy = false;
}

if (chatText) {
  document.getElementById("chat-send").addEventListener("click", () => sendChat(chatText.value));
  chatText.addEventListener("keydown", (e) => { if (e.key === "Enter") sendChat(chatText.value); });
  document.querySelectorAll("#chat-suggests .chip").forEach((chip) =>
    chip.addEventListener("click", () => sendChat(chip.textContent))
  );
}

loadProfile();
