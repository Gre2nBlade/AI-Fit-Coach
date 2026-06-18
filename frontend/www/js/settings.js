// Настройки приложения (тумблеры в профиле). Хранятся в localStorage,
// привязка к DOM по атрибуту data-setting. Другие модули читают значения
// через AFCSettings.get(key) и подписываются через AFCSettings.onChange(key, cb).

const AFCSettings = (function () {
  const KEY = "afc_settings";
  const DEFAULTS = {
    theme_light: false,     // светлая тема
    notifications: false,   // локальные напоминания (см. notifications.js)
    ai_tips: true,          // контекстные подсказки под ответами ИИ
    timer_sound: true,      // звук таймера в тренировке
  };
  const listeners = {};

  function load() {
    try {
      const raw = localStorage.getItem(KEY);
      if (raw) return Object.assign({}, DEFAULTS, JSON.parse(raw));
    } catch (e) {}
    return Object.assign({}, DEFAULTS);
  }

  let state = load();

  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {}
  }

  function get(key) { return !!state[key]; }

  function set(key, value) {
    value = !!value;
    if (state[key] === value) return;
    state[key] = value;
    save();
    (listeners[key] || []).forEach((cb) => cb(value));
  }

  function onChange(key, cb) {
    (listeners[key] = listeners[key] || []).push(cb);
  }

  // Синхронизировать тему с сохранённым тумблером при старте.
  function syncTheme() {
    const light = (window.AFCTheme && window.AFCTheme.get() === "light");
    state.theme_light = light;
  }

  // Привязать тумблеры в DOM: проставить класс .on и навесить клик.
  function bindToggles() {
    syncTheme();
    document.querySelectorAll("[data-setting]").forEach((el) => {
      const key = el.dataset.setting;
      el.classList.toggle("on", get(key));
      el.addEventListener("click", () => {
        const next = !el.classList.contains("on");
        el.classList.toggle("on", next);
        if (key === "theme_light" && window.AFCTheme) {
          window.AFCTheme.set(next ? "light" : "dark");
        }
        set(key, next);
      });
    });
  }

  return { get, set, onChange, bindToggles };
})();
