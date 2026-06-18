// Онбординг: пошаговый сбор профиля, валидация, расчёты, сохранение на бэкенд.

const profile = {
  full_name: "", age: "", sex: "",
  height_cm: "", weight_kg: "", goal_weight_kg: "",
  goal: "", level: "", place: "", days: [],
};

const steps = Array.from(document.querySelectorAll(".onb-step"));
const segs = Array.from(document.querySelectorAll("#step-rail .seg"));
let current = 0;
// Режим редактирования: пользователь уже прошёл онбординг и зашёл править данные
// из профиля. В этом режиме на первом шаге показываем кнопку «Назад» (отмена).
let IS_EDIT = false;

// Если пользователь уже авторизован и есть профиль — предзаполним поля.
(async function prefill() {
  if (!isAuthed()) return;
  const res = await apiGet("/api/user/me");
  if (res.ok && res.data) {
    const p = res.data;
    if (p.onboarded) {
      IS_EDIT = true;
      const cancel = document.getElementById("btn-cancel-edit");
      if (cancel) cancel.hidden = false;
    }
    setVal("f-name", p.full_name); setVal("f-age", p.age); setVal("f-sex", p.sex);
    setVal("f-height", p.height_cm); setVal("f-weight", p.weight_kg);
    setVal("f-goalweight", p.goal_weight_kg);
    setVal("f-level", p.level); setVal("f-place", p.place);
    if (p.goal) {
      const card = document.querySelector(`.goal-card[data-goal="${p.goal}"]`);
      if (card) { card.classList.add("active"); profile.goal = p.goal; }
    }
    if (p.training_days) {
      p.training_days.split(",").forEach((d) => {
        const btn = document.querySelector(`.day[data-day="${d.trim()}"]`);
        if (btn) { btn.classList.add("active"); profile.days.push(d.trim()); }
      });
    }
  }
})();

function setVal(id, v) {
  const el = document.getElementById(id);
  if (el && v != null && v !== "") el.value = v;
}

function render() {
  steps.forEach((s, i) => s.classList.toggle("active", i === current));
  segs.forEach((seg, i) => seg.classList.toggle("active", i <= current));
  if (current === steps.length - 1) buildSummary();
}

function stepErr(text) {
  const step = steps[current];
  const el = step.querySelector(".step-err");
  if (el) { el.textContent = text || ""; el.style.color = "#e3596a"; }
}

function collect() {
  const v = (id) => (document.getElementById(id)?.value || "").trim();
  if (current === 0) {
    profile.full_name = v("f-name"); profile.age = v("f-age"); profile.sex = v("f-sex");
  } else if (current === 1) {
    profile.height_cm = v("f-height"); profile.weight_kg = v("f-weight"); profile.goal_weight_kg = v("f-goalweight");
  } else if (current === 3) {
    profile.level = v("f-level"); profile.place = v("f-place");
  }
}

function validateStep() {
  if (current === 0) {
    if (profile.full_name.trim().length < 2) return "Имя должно быть не короче 2 символов.";
    if (!profile.age || profile.age < 10 || profile.age > 100) return "Укажите корректный возраст.";
    if (!profile.sex) return "Выберите пол.";
  } else if (current === 1) {
    if (!profile.height_cm) return "Укажите рост.";
    if (!profile.weight_kg) return "Укажите вес.";
    if (!profile.goal_weight_kg) return "Укажите желаемый вес.";
  } else if (current === 2) {
    if (!profile.goal) return "Выберите цель.";
  } else if (current === 3) {
    if (!profile.level) return "Выберите уровень подготовки.";
    if (!profile.place) return "Выберите место тренировок.";
    if (profile.days.length === 0) return "Отметьте хотя бы один день тренировок.";
  }
  return null;
}

document.querySelectorAll("[data-next]").forEach((btn) =>
  btn.addEventListener("click", () => {
    collect();
    const err = validateStep();
    if (err) { stepErr(err); return; }
    stepErr("");
    if (current < steps.length - 1) { current += 1; render(); }
  })
);

document.querySelectorAll("[data-back]").forEach((btn) =>
  btn.addEventListener("click", () => { if (current > 0) { current -= 1; render(); } })
);

// «Назад» на первом шаге в режиме редактирования — вернуться в приложение без сохранения.
document.querySelectorAll("[data-cancel]").forEach((btn) =>
  btn.addEventListener("click", () => { window.location.href = "app.html"; })
);

document.getElementById("goal-grid").addEventListener("click", (e) => {
  const card = e.target.closest(".goal-card");
  if (!card) return;
  document.querySelectorAll(".goal-card").forEach((c) => c.classList.remove("active"));
  card.classList.add("active");
  profile.goal = card.dataset.goal;
});

document.getElementById("days-row").addEventListener("click", (e) => {
  const day = e.target.closest(".day");
  if (!day) return;
  day.classList.toggle("active");
  const d = day.dataset.day;
  profile.days = day.classList.contains("active")
    ? [...profile.days, d]
    : profile.days.filter((x) => x !== d);
});

function buildSummary() {
  const rows = [
    ["Имя", profile.full_name], ["Возраст", profile.age], ["Пол", profile.sex],
    ["Рост", profile.height_cm], ["Вес", profile.weight_kg], ["Цель", profile.goal_weight_kg],
    ["Уровень", profile.level], ["Место", profile.place],
    ["Дни", profile.days.join(", ") || "—"],
  ];
  document.getElementById("summary-card").innerHTML = rows
    .map(([k, val]) => `<div class="row"><span class="k">${k}</span><span class="v">${val || "—"}</span></div>`)
    .join("");

  const m = computeMetrics(profile);
  const mc = document.getElementById("metrics-card");
  if (m) {
    mc.innerHTML = [
      ["Калории/день", m.calories + " ккал"],
      ["Белки", m.protein_g + " г"],
      ["Жиры", m.fat_g + " г"],
      ["Углеводы", m.carbs_g + " г"],
      ["ИМТ", m.bmi],
      ["Вода", m.water_l + " л"],
    ].map(([k, val]) => `<div class="row"><span class="k">${k}</span><span class="v">${val}</span></div>`).join("");
  } else {
    mc.innerHTML = '<div class="row"><span class="k">Недостаточно данных для расчёта</span></div>';
  }
}

document.getElementById("btn-start").addEventListener("click", async () => {
  const btn = document.getElementById("btn-start");
  const msg = document.getElementById("save-msg");
  const payload = {
    full_name: profile.full_name,
    age: Number(profile.age),
    sex: profile.sex,
    height_cm: Number(profile.height_cm),
    weight_kg: Number(profile.weight_kg),
    goal_weight_kg: Number(profile.goal_weight_kg),
    goal: profile.goal,
    level: profile.level,
    place: profile.place,
    training_days: profile.days.join(","),
  };

  // Не авторизован → сохраним локально и попросим войти
  if (!isAuthed()) {
    localStorage.setItem("afc_profile", JSON.stringify(profile));
    window.location.href = "index.html";
    return;
  }

  btn.disabled = true;
  msg.style.color = "#8d86a3";
  msg.textContent = "Сохраняем...";
  const res = await apiPost("/api/user/profile", payload);
  btn.disabled = false;

  if (res.ok) {
    window.location.href = "app.html";
  } else {
    msg.style.color = "#e3596a";
    msg.textContent = errorText(res.data, "Не удалось сохранить профиль.");
  }
});

render();
