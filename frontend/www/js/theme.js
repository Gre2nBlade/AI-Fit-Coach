// Тема оформления: тёмная (по умолчанию) и светлая.
// Значение хранится в localStorage и применяется к <html data-theme="...">.
// Чтобы не было «вспышки» тёмного фона на светлой теме, применяем как можно
// раньше — этот файл подключается в <head> до отрисовки.
(function () {
  var KEY = "afc_theme";
  var saved = null;
  try { saved = localStorage.getItem(KEY); } catch (e) {}
  if (saved === "light") {
    document.documentElement.setAttribute("data-theme", "light");
  }

  window.AFCTheme = {
    get: function () {
      return document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark";
    },
    set: function (theme) {
      if (theme === "light") {
        document.documentElement.setAttribute("data-theme", "light");
      } else {
        document.documentElement.removeAttribute("data-theme");
      }
      try { localStorage.setItem(KEY, theme); } catch (e) {}
    },
    toggle: function () {
      var next = this.get() === "light" ? "dark" : "light";
      this.set(next);
      return next;
    },
  };
})();
