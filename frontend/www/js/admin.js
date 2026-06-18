// Админ-панель. Вход по секрету → отдельный админ-JWT (role=admin).
//
// Токен админа хранится ОТДЕЛЬНО от пользовательского (afc_admin_token), чтобы
// не пересекаться с обычной сессией в том же браузере. Поэтому здесь свой
// request-хелпер, а не apiGet/apiPost из api.js (те шлют пользовательский токен).
// Глобальные API_BASE и errorText берём из api.js (подключён раньше).

const ADMIN_TOKEN_KEY = "afc_admin_token";
const getAdminToken = () => localStorage.getItem(ADMIN_TOKEN_KEY) || "";
const setAdminToken = (t) => localStorage.setItem(ADMIN_TOKEN_KEY, t);
const clearAdminToken = () => localStorage.removeItem(ADMIN_TOKEN_KEY);

// Безопасный вывод текста в HTML.
function esc(s) {
  const d = document.createElement("div");
  d.textContent = s == null ? "" : String(s);
  return d.innerHTML;
}

async function adminRequest(method, path, body) {
  try {
    const opts = { method, headers: {} };
    const t = getAdminToken();
    if (t) opts.headers["Authorization"] = "Bearer " + t;
    if (body !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    const resp = await fetch(API_BASE + path, opts);
    let data = null;
    try { data = await resp.json(); } catch (e) { data = null; }
    // Токен админа протух/невалиден — назад на экран входа.
    if (resp.status === 401 && !path.endsWith("/login")) {
      clearAdminToken();
      showLogin("Сессия истекла. Войдите снова.");
    }
    return { ok: resp.ok, status: resp.status, data };
  } catch (e) {
    return { ok: false, status: 0, data: { detail: "Сервер недоступен. Запущен ли бэкенд?" } };
  }
}
const adminGet = (p) => adminRequest("GET", p);
const adminPost = (p, b) => adminRequest("POST", p, b || {});
const adminDelete = (p) => adminRequest("DELETE", p);

// ---------- Переключение экранов «вход / панель» ----------
const $login = () => document.getElementById("admin-login");
const $panel = () => document.querySelector(".admin-wrap");

function showLogin(message) {
  $panel().hidden = true;
  $login().hidden = false;
  const err = document.getElementById("admin-login-error");
  if (message) { err.textContent = message; err.hidden = false; }
  else { err.hidden = true; }
  const inp = document.getElementById("admin-secret");
  if (inp) { inp.value = ""; inp.focus(); }
}

function showPanel() {
  $login().hidden = true;
  $panel().hidden = false;
  loadUsers();
}

// ---------- Вход ----------
async function doLogin(e) {
  e.preventDefault();
  const secret = document.getElementById("admin-secret").value.trim();
  const err = document.getElementById("admin-login-error");
  if (!secret) { err.textContent = "Введите секрет."; err.hidden = false; return; }
  const res = await adminPost("/api/admin/login", { secret });
  if (!res.ok || !res.data || !res.data.token) {
    err.textContent = errorText(res.data, "Неверный секрет.");
    err.hidden = false;
    return;
  }
  setAdminToken(res.data.token);
  showPanel();
}

function logout() {
  clearAdminToken();
  showLogin();
}

// ---------- Вкладки ----------
function switchTab(name) {
  document.querySelectorAll("#admin-tabs .chip").forEach((c) =>
    c.classList.toggle("active", c.dataset.tab === name));
  document.querySelectorAll(".admin-section").forEach((s) =>
    s.hidden = s.dataset.tab !== name);
  if (name === "analytics") loadStats();
  if (name === "logs") loadLogs();
}

// ---------- Пользователи ----------
const GOAL_OPTS = ["Похудение", "Набор массы", "Баланс формы"];
const LEVEL_OPTS = ["Начальный", "Средний", "Продвинутый"];
const PLACE_OPTS = ["Дома", "В зале", "На улице"];
const SEX_OPTS = [["male", "Мужской"], ["female", "Женский"]];

async function loadUsers() {
  const q = (document.getElementById("user-search").value || "").trim();
  const tbody = document.getElementById("users-tbody");
  tbody.innerHTML = `<tr><td colspan="6" class="page-sub">Загрузка…</td></tr>`;
  const res = await adminGet(`/api/admin/users?limit=100&q=${encodeURIComponent(q)}`);
  if (!res.ok) {
    tbody.innerHTML = `<tr><td colspan="6" class="page-sub">${esc(errorText(res.data, "Ошибка загрузки"))}</td></tr>`;
    return;
  }
  const { items, total } = res.data;
  if (!items.length) {
    tbody.innerHTML = `<tr><td colspan="6" class="page-sub">Ничего не найдено</td></tr>`;
  } else {
    tbody.innerHTML = items.map((u) => `
      <tr>
        <td>${u.id}</td>
        <td>${esc(u.email)}</td>
        <td>${esc(u.full_name || "—")}</td>
        <td>${esc(u.goal || "—")}</td>
        <td>${u.onboarded ? '<span class="pill">да</span>' : "—"}</td>
        <td class="admin-actions">
          <button class="btn btn-ghost" data-open="${u.id}">Открыть</button>
        </td>
      </tr>`).join("");
    tbody.querySelectorAll("[data-open]").forEach((b) =>
      b.addEventListener("click", () => openUser(+b.dataset.open)));
  }
  document.getElementById("users-count").textContent = `Всего: ${total}`;
}

async function openUser(id) {
  const box = document.getElementById("user-detail");
  box.hidden = false;
  box.innerHTML = `<div class="page-sub">Загрузка…</div>`;
  box.scrollIntoView({ behavior: "smooth", block: "nearest" });
  const res = await adminGet(`/api/admin/users/${id}`);
  if (!res.ok) {
    box.innerHTML = `<div class="page-sub">${esc(errorText(res.data, "Ошибка"))}</div>`;
    return;
  }
  renderUserDetail(box, res.data);
}

function field(label, name, value, type = "text") {
  return `<label class="page-sub" style="display:block;">${label}
    <input class="input" data-f="${name}" type="${type}" value="${esc(value ?? "")}" style="margin-top:4px;">
  </label>`;
}
function selectField(label, name, value, opts) {
  const options = opts.map((o) => {
    const [val, text] = Array.isArray(o) ? o : [o, o];
    const sel = String(val) === String(value ?? "") ? " selected" : "";
    return `<option value="${esc(val)}"${sel}>${esc(text)}</option>`;
  }).join("");
  return `<label class="page-sub" style="display:block;">${label}
    <select class="input" data-f="${name}" style="margin-top:4px;"><option value="">—</option>${options}</select>
  </label>`;
}

function renderUserDetail(box, u) {
  const plans = (u.plans || []).map((p) => `
    <div class="data-row">
      <span>План: <b>${esc(p.kind)}</b> <span class="page-sub">(${esc(p.updated_at)})</span></span>
      <span class="admin-actions">
        <button class="btn btn-ghost" data-regen="${esc(p.kind)}">Перегенерировать</button>
        <button class="btn btn-ghost danger" data-delplan="${esc(p.kind)}">Удалить</button>
      </span>
    </div>`).join("") || `<div class="page-sub">Планов нет</div>`;

  const checkins = (u.checkins || []).slice(0, 7).map((c) =>
    `<span class="pill" title="питание/тренировка/всё">${esc(c.day)}: ${c.ate_well}/${c.trained}/${c.all_done}</span>`
  ).join(" ") || `<span class="page-sub">Чек-инов нет</span>`;

  box.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap;">
      <h3 style="margin:0;">#${u.id} · ${esc(u.email)}</h3>
      <button class="btn btn-ghost" data-close>Закрыть</button>
    </div>

    <h4>Профиль</h4>
    <div class="edit-grid">
      ${field("Имя", "full_name", u.full_name)}
      ${selectField("Пол", "sex", u.sex, SEX_OPTS)}
      ${field("Возраст", "age", u.age, "number")}
      ${field("Рост, см", "height_cm", u.height_cm, "number")}
      ${field("Вес, кг", "weight_kg", u.weight_kg, "number")}
      ${field("Цель веса, кг", "goal_weight_kg", u.goal_weight_kg, "number")}
      ${selectField("Цель", "goal", u.goal, GOAL_OPTS)}
      ${selectField("Уровень", "level", u.level, LEVEL_OPTS)}
      ${selectField("Место", "place", u.place, PLACE_OPTS)}
      ${field("Дни тренировок", "training_days", u.training_days)}
    </div>
    <div class="admin-actions" style="margin-top:14px;">
      <button class="btn" data-save>Сохранить</button>
      <button class="btn btn-ghost danger" data-deluser>Удалить пользователя</button>
    </div>
    <div class="page-sub" data-msg style="margin-top:8px;"></div>

    <h4 style="margin-top:20px;">Контент</h4>
    ${plans}
    <h4 style="margin-top:16px;">Активность (7 дней)</h4>
    <div>${checkins}</div>
  `;

  const msg = box.querySelector("[data-msg]");
  const setMsg = (t, ok) => { msg.textContent = t; msg.style.color = ok ? "var(--good,#3ec98a)" : "var(--hard,#e3596a)"; };

  box.querySelector("[data-close]").addEventListener("click", () => { box.hidden = true; });

  box.querySelector("[data-save]").addEventListener("click", async () => {
    const payload = {};
    box.querySelectorAll("[data-f]").forEach((el) => {
      let v = el.value;
      if (el.type === "number") v = v === "" ? null : Number(v);
      else v = v === "" ? null : v;
      payload[el.dataset.f] = v;
    });
    if (!payload.full_name || payload.full_name.trim().length < 2) {
      setMsg("Имя должно быть не короче 2 символов.", false);
      return;
    }
    const res = await adminPost(`/api/admin/users/${u.id}`, payload);
    if (!res.ok) { setMsg(errorText(res.data, "Не удалось сохранить"), false); return; }
    setMsg("Сохранено.", true);
    loadUsers();
  });

  box.querySelector("[data-deluser]").addEventListener("click", async () => {
    if (!confirm(`Удалить пользователя #${u.id} и все его данные? Это необратимо.`)) return;
    const res = await adminDelete(`/api/admin/users/${u.id}`);
    if (!res.ok) { setMsg(errorText(res.data, "Не удалось удалить"), false); return; }
    box.hidden = true;
    loadUsers();
  });

  box.querySelectorAll("[data-regen]").forEach((b) =>
    b.addEventListener("click", async () => {
      b.disabled = true; b.textContent = "Генерация…";
      const res = await adminPost(`/api/admin/users/${u.id}/plans/${b.dataset.regen}/regenerate`);
      if (!res.ok) { setMsg(errorText(res.data, "Ошибка генерации"), false); b.disabled = false; b.textContent = "Перегенерировать"; return; }
      openUser(u.id);
    }));

  box.querySelectorAll("[data-delplan]").forEach((b) =>
    b.addEventListener("click", async () => {
      if (!confirm(`Удалить план «${b.dataset.delplan}»?`)) return;
      const res = await adminDelete(`/api/admin/users/${u.id}/plans/${b.dataset.delplan}`);
      if (!res.ok) { setMsg(errorText(res.data, "Не удалось удалить план"), false); return; }
      openUser(u.id);
    }));
}

// ---------- Аналитика ----------
async function loadStats() {
  const tiles = document.getElementById("stats-tiles");
  tiles.innerHTML = `<div class="page-sub">Загрузка…</div>`;
  const res = await adminGet("/api/admin/stats");
  if (!res.ok) { tiles.innerHTML = `<div class="page-sub">${esc(errorText(res.data, "Ошибка"))}</div>`; return; }
  const s = res.data;
  const tile = (label, val) => `<div class="panel" style="text-align:center;">
    <div style="font-size:28px; font-weight:700;">${val}</div>
    <div class="page-sub">${label}</div></div>`;
  tiles.innerHTML = [
    tile("Пользователей", s.users_total),
    tile("Прошли онбординг", s.users_onboarded),
    tile("Активны (7 дн.)", s.active_users_7d),
    tile("Планы (тренировки)", s.plans?.workout || 0),
    tile("Планы (питание)", s.plans?.nutrition || 0),
    tile("Чек-инов всего", s.checkins_total),
  ].join("");

  const bars = document.getElementById("reg-bars");
  const regs = s.registrations_by_day || [];
  const max = Math.max(1, ...regs.map((r) => r.count));
  bars.innerHTML = regs.map((r) => {
    const h = Math.round((r.count / max) * 100);
    const d = r.day.slice(5); // MM-DD
    return `<div class="b" style="height:${Math.max(3, h)}%;" title="${esc(r.day)}: ${r.count}"><span>${esc(d)}</span></div>`;
  }).join("") || `<div class="page-sub">Нет данных</div>`;
}

// ---------- Логи ----------
async function loadLogs() {
  const pre = document.getElementById("logs-pre");
  pre.textContent = "Загрузка…";
  const res = await adminGet("/api/admin/logs?lines=400");
  if (!res.ok) { pre.textContent = errorText(res.data, "Ошибка загрузки логов"); return; }
  pre.textContent = res.data.text || "(лог пуст)";
  pre.scrollTop = pre.scrollHeight;
}

// ---------- Инициализация ----------
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("admin-login-form").addEventListener("submit", doLogin);
  document.getElementById("btn-admin-logout").addEventListener("click", logout);
  document.getElementById("btn-user-search").addEventListener("click", loadUsers);
  document.getElementById("user-search").addEventListener("keydown", (e) => {
    if (e.key === "Enter") loadUsers();
  });
  document.getElementById("btn-logs-refresh").addEventListener("click", loadLogs);
  document.querySelectorAll("#admin-tabs .chip").forEach((c) =>
    c.addEventListener("click", () => switchTab(c.dataset.tab)));

  if (getAdminToken()) showPanel();
  else showLogin();
});
