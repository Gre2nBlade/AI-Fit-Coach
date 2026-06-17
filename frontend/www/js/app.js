// Логика приложения: грузит профиль с бэкенда, наполняет дашборд расчётами,
// ИИ-чат через API, логаут, загрузка аватарки.

let PROFILE = null;

/* ---------- Гард: без токена — на вход ---------- */
if (!isAuthed()) {
  window.location.replace("index.html");
}

/* ---------- Навигация по вью (сайдбар + нижняя панель вкладок) ---------- */
const navItems = document.querySelectorAll(".nav-item[data-view], .tab-item[data-view]");
const views = document.querySelectorAll(".view");

function showView(name) {
  views.forEach((v) => v.classList.toggle("active", v.dataset.view === name));
  navItems.forEach((n) => n.classList.toggle("active", n.dataset.view === name));
  window.scrollTo(0, 0);
  // вкладки, которым нужны данные с бэка
  if (name === "workout") ensureWorkoutPlan();
  else if (name === "nutrition") ensureNutritionPlan();
  else if (name === "progress") ensureProgress();
}
navItems.forEach((btn) => btn.addEventListener("click", () => showView(btn.dataset.view)));
document.querySelectorAll("[data-goto]").forEach((btn) =>
  btn.addEventListener("click", () => showView(btn.dataset.goto))
);
document.querySelectorAll("[data-goto-onb]").forEach((btn) =>
  btn.addEventListener("click", () => { window.location.href = "onboarding.html"; })
);

/* ---------- Логаут (сайдбар + кнопка в профиле для мобильного) ---------- */
function doLogout() {
  clearToken();
  window.location.href = "index.html";
}
document.getElementById("btn-logout").addEventListener("click", doLogout);
document.getElementById("btn-logout-2")?.addEventListener("click", doLogout);

/* ---------- Загрузка профиля ---------- */
async function loadProfile() {
  const res = await apiGet("/api/user/me");
  if (res.status === 401) { window.location.replace("index.html"); return; }
  if (!res.ok || !res.data) return;
  // онбординг не пройден — отправим туда
  if (!res.data.onboarded) { window.location.replace("onboarding.html"); return; }
  PROFILE = res.data;
  fillProfile(PROFILE);
  // подтянуть план тренировок для главной (тренировка дня)
  ensureWorkoutPlan();
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

function addMessage(text, mine, image) {
  const msg = document.createElement("div");
  msg.className = "msg" + (mine ? " me" : "");
  const initial = (PROFILE?.full_name || "Я").charAt(0).toUpperCase();
  const photo = image ? `<img class="chat-photo" src="${image}" alt="фото">` : "";
  const bubble = `<div class="bubble">${photo}${escapeHtml(text)}</div>`;
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

/* фото-вложение в чат */
let CHAT_IMAGE = null; // data URL прикреплённого фото
const chatImageInput = document.getElementById("chat-image-input");
const chatImagePreview = document.getElementById("chat-image-preview");
const chatImageThumb = document.getElementById("chat-image-thumb");

function clearChatImage() {
  CHAT_IMAGE = null;
  if (chatImageInput) chatImageInput.value = "";
  if (chatImagePreview) chatImagePreview.hidden = true;
  if (chatImageThumb) chatImageThumb.src = "";
}

if (chatImageInput) {
  document.getElementById("chat-attach")?.addEventListener("click", () => chatImageInput.click());
  document.getElementById("chat-image-remove")?.addEventListener("click", clearChatImage);
  chatImageInput.addEventListener("change", () => {
    const file = chatImageInput.files[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      addMessage("Можно прикрепить только фото (изображение).", false);
      chatImageInput.value = "";
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      CHAT_IMAGE = reader.result;
      if (chatImageThumb) chatImageThumb.src = CHAT_IMAGE;
      if (chatImagePreview) chatImagePreview.hidden = false;
    };
    reader.readAsDataURL(file);
  });
}

let chatBusy = false;
async function sendChat(text) {
  text = (text || "").trim();
  const image = CHAT_IMAGE;
  if ((!text && !image) || chatBusy) return;
  chatBusy = true;

  addMessage(text || "Оцени, что на фото", true, image);
  chatText.value = "";
  clearChatImage();

  const thinking = addMessage("…думаю", false);
  const res = await apiPost("/api/ai/ask", { question: text, image });
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

/* ============================================================
   ИИ-планы: тренировки и питание (с кэшем и кнопкой «Обновить»)
   ============================================================ */
let WORKOUT_PLAN = null;
let NUTRITION_PLAN = null;
let activeGroupIdx = 0;

const DIFF = {
  easy: { cls: "easy", label: "Легко" },
  medium: { cls: "medium", label: "Среднее" },
  hard: { cls: "hard", label: "Тяжёлое" },
};

function exerciseRows(exercises, withDiff) {
  return (exercises || []).map((ex, i) => {
    const meta = `${ex.sets ?? "—"}x${ex.reps ?? "—"}${ex.rest ? " · Отдых " + ex.rest : ""}`;
    const d = DIFF[(ex.difficulty || "").toLowerCase()];
    const diffHtml = withDiff && d ? `<div class="diff ${d.cls}">${d.label}</div>` : "";
    return `<div class="ex-row"><div class="num">${i + 1}</div>` +
      `<div class="info"><div class="nm">${escapeHtml(ex.name || "Упражнение")}</div>` +
      `<div class="meta">${escapeHtml(meta)}</div></div>${diffHtml}</div>`;
  }).join("");
}

function renderWorkoutGroup(idx) {
  if (!WORKOUT_PLAN || !WORKOUT_PLAN.groups) return;
  activeGroupIdx = idx;
  const g = WORKOUT_PLAN.groups[idx];
  const tabs = document.getElementById("workout-tabs");
  if (tabs) {
    tabs.querySelectorAll(".chip").forEach((c, i) => c.classList.toggle("active", i === idx));
  }
  const content = document.getElementById("workout-content");
  if (!content || !g) return;
  const count = (g.exercises || []).length;
  content.innerHTML =
    `<div class="panel">
       <h3 style="font-size:24px;">${escapeHtml(g.title || g.group || "Тренировка")}</h3>
       <div class="page-sub" style="font-size:14px;margin:6px 0 18px;">${g.minutes || "—"} минут · ${g.calories || "—"} калорий · ${count} упражнений</div>
       <div class="ex-list">${exerciseRows(g.exercises, true)}</div>
     </div>
     <div class="stack">
       <div class="panel"><h3>Статистика</h3>
         <div class="grid-3">
           <div class="stat-num"><div class="big">${g.minutes || "—"}</div><div class="lbl">Минут</div></div>
           <div class="stat-num"><div class="big">${g.calories || "—"}</div><div class="lbl">Калорий</div></div>
           <div class="stat-num"><div class="big">${count}</div><div class="lbl">Упр</div></div>
         </div>
       </div>
       <div class="panel"><h3>Совет от ИИ</h3>
         <p class="page-sub" style="font-size:15px;margin:0;">Соблюдай технику и отдых между подходами. Когда выполняешь все повторения легко — повышай нагрузку.</p>
       </div>
     </div>`;
}

function renderWorkoutPlan() {
  const tabs = document.getElementById("workout-tabs");
  if (tabs && WORKOUT_PLAN && WORKOUT_PLAN.groups) {
    tabs.innerHTML = WORKOUT_PLAN.groups.map((g, i) =>
      `<button class="chip${i === 0 ? " active" : ""}" data-gi="${i}">${escapeHtml(g.group || g.title)}</button>`
    ).join("");
    tabs.querySelectorAll(".chip").forEach((c) =>
      c.addEventListener("click", () => renderWorkoutGroup(Number(c.dataset.gi)))
    );
  }
  renderWorkoutGroup(0);
  fillHomeWorkout();
}

function fillHomeWorkout() {
  if (!WORKOUT_PLAN || !WORKOUT_PLAN.groups || !WORKOUT_PLAN.groups[0]) return;
  const g = WORKOUT_PLAN.groups[0];
  const count = (g.exercises || []).length;
  setText("home-workout-title", g.title || g.group || "Тренировка дня");
  setText("home-workout-meta", `${g.minutes || "—"} минут · ${g.calories || "—"} калорий · ${count} упражнений`);
  const list = document.getElementById("home-workout-list");
  if (list) list.innerHTML = exerciseRows(g.exercises, false);
}

async function ensureWorkoutPlan(force) {
  if (WORKOUT_PLAN && !force) return;
  const path = force ? "/api/workout/regenerate" : "/api/workout/plan";
  const setLoading = (msg) => {
    const c = document.getElementById("workout-content");
    if (c) c.innerHTML = `<div class="panel"><div class="page-sub">${msg}</div></div>`;
  };
  if (force) setLoading("Генерирую новую программу… это займёт несколько секунд");
  const res = force ? await apiPost(path) : await apiGet(path);
  if (res.ok && res.data && res.data.groups) {
    WORKOUT_PLAN = res.data;
    renderWorkoutPlan();
  } else {
    setLoading(errorText(res.data, "Не удалось получить программу от ИИ."));
  }
}

const MEAL_ICONS = { завтрак: "breakfast_dining", обед: "rice_bowl", перекус: "local_drink", ужин: "restaurant" };

function renderNutritionPlan() {
  const box = document.getElementById("nutrition-meals");
  if (!box || !NUTRITION_PLAN || !NUTRITION_PLAN.meals) return;
  box.innerHTML = NUTRITION_PLAN.meals.map((m) => {
    const icon = MEAL_ICONS[(m.meal || "").toLowerCase()] || "restaurant";
    return `<div class="meal"><div class="ico"><span class="micon">${icon}</span></div>` +
      `<div class="info"><div class="nm">${escapeHtml(m.meal || "Приём пищи")}</div>` +
      `<div class="desc">${escapeHtml(m.dish || "")}</div></div>` +
      `<div class="kcal">${m.kcal != null ? m.kcal + " ккал" : ""}</div></div>`;
  }).join("");
}

async function ensureNutritionPlan(force) {
  if (NUTRITION_PLAN && !force) return;
  const box = document.getElementById("nutrition-meals");
  if (force && box) box.innerHTML = `<div class="page-sub">Генерирую план питания…</div>`;
  const res = force ? await apiPost("/api/nutrition/regenerate") : await apiGet("/api/nutrition/plan");
  if (res.ok && res.data && res.data.meals) {
    NUTRITION_PLAN = res.data;
    renderNutritionPlan();
  } else if (box) {
    box.innerHTML = `<div class="page-sub">${errorText(res.data, "Не удалось получить план питания.")}</div>`;
  }
}

document.getElementById("btn-regen-workout")?.addEventListener("click", () => ensureWorkoutPlan(true));
document.getElementById("btn-regen-nutrition")?.addEventListener("click", () => ensureNutritionPlan(true));

/* ============================================================
   Реальный прогресс: ежедневный чек-ин + графики
   ============================================================ */
let PROGRESS_LOADED = false;

function renderProgress(s) {
  // столбики недели
  const bars = document.getElementById("progress-bars");
  if (bars && s.week_bars) {
    bars.innerHTML = s.week_bars.map((b) => {
      const h = b.trained ? 85 : 18;
      const cls = b.trained ? "bar" : "bar empty";
      return `<div class="bar-col"><div class="${cls}" style="height:${h}%"></div><div class="lbl">${b.label}</div></div>`;
    }).join("");
  }
  setText("st-workouts", s.workouts_month ?? 0);
  setText("st-completion", (s.completion_pct ?? 0) + "%");
  setText("st-streak", s.streak ?? 0);
  setText("progress-streak", "Серия: " + (s.streak ?? 0));

  // тумблеры чек-ина
  const t = s.today || {};
  document.querySelectorAll("[data-checkin]").forEach((el) => {
    el.classList.toggle("on", !!t[el.dataset.checkin]);
  });
}

async function ensureProgress(force) {
  if (PROGRESS_LOADED && !force) return;
  const res = await apiGet("/api/progress/summary");
  if (res.ok && res.data) {
    PROGRESS_LOADED = true;
    renderProgress(res.data);
  }
}

// клики по тумблерам чек-ина → сохранить день
document.querySelectorAll("[data-checkin]").forEach((el) => {
  el.addEventListener("click", async () => {
    el.classList.toggle("on");
    const payload = {};
    document.querySelectorAll("[data-checkin]").forEach((t) => {
      payload[t.dataset.checkin] = t.classList.contains("on");
    });
    const res = await apiPost("/api/progress/checkin", payload);
    if (res.ok) ensureProgress(true);  // обновить графики/серии
  });
});

loadProfile();
