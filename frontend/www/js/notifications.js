// Локальные уведомления (напоминания о тренировке и воде).
//
// В APK используется плагин @capacitor/local-notifications (реальные пуши на
// устройстве по расписанию, работают даже когда приложение закрыто).
// В обычном браузере — мягкий фолбэк через Web Notification (только пока
// вкладка открыта). Управляется тумблером «Уведомления» в профиле.

const AFCNotifications = (function () {
  let PROFILE = null;

  function plugin() {
    const cap = window.Capacitor;
    if (cap && cap.Plugins && cap.Plugins.LocalNotifications) {
      return cap.Plugins.LocalNotifications;
    }
    return null;
  }

  function isNative() {
    return !!(window.Capacitor && window.Capacitor.isNativePlatform && window.Capacitor.isNativePlatform());
  }

  // Запросить разрешение. true — можно слать уведомления.
  async function requestPermission() {
    const ln = plugin();
    if (ln) {
      try {
        const res = await ln.requestPermissions();
        return res && res.display === "granted";
      } catch (e) { return false; }
    }
    // браузерный фолбэк
    if ("Notification" in window) {
      if (Notification.permission === "granted") return true;
      if (Notification.permission !== "denied") {
        const p = await Notification.requestPermission();
        return p === "granted";
      }
    }
    return false;
  }

  // Запланировать напоминания: тренировка в дни из профиля (18:00) + вода (13:00).
  async function schedule() {
    const ln = plugin();
    if (!ln) return; // браузер: расписания нет, только мгновенные уведомления
    try {
      await cancelAll();
      const notifs = window.AFCNotifSchedule.buildNotifications(PROFILE);
      if (notifs.length) await ln.schedule({ notifications: notifs });
    } catch (e) { /* не критично */ }
  }

  // Отправить тестовое уведомление, чтобы проверить работу прямо сейчас.
  // В APK — через ~5 секунд, в браузере — мгновенно. Возвращает true при успехе.
  async function test() {
    const ok = await requestPermission();
    if (!ok) return false;
    const ln = plugin();
    if (ln) {
      try {
        await ln.schedule({
          notifications: [{
            id: 999,
            title: "Проверка уведомлений ✅",
            body: "Если ты это видишь — уведомления работают! Придёт через 5 секунд.",
            schedule: { at: new Date(Date.now() + 5000) },
          }],
        });
        return true;
      } catch (e) { return false; }
    }
    // браузерный фолбэк — показать сразу (только пока вкладка открыта)
    if ("Notification" in window) {
      new Notification("Проверка уведомлений ✅", {
        body: "Если ты это видишь — уведомления работают!",
      });
      return true;
    }
    return false;
  }

  async function cancelAll() {
    const ln = plugin();
    if (!ln) return;
    try {
      const pending = await ln.getPending();
      if (pending && pending.notifications && pending.notifications.length) {
        await ln.cancel({ notifications: pending.notifications.map((n) => ({ id: n.id })) });
      }
    } catch (e) {}
  }

  // Включить уведомления (запрос разрешения + расписание). Возвращает true при успехе.
  async function enable() {
    const ok = await requestPermission();
    if (!ok) return false;
    await schedule();
    return true;
  }

  async function disable() {
    await cancelAll();
  }

  // Вызывается из app.js после загрузки профиля.
  function init(profile) {
    PROFILE = profile;

    // тумблер уже мог быть включён ранее — восстановим расписание
    if (window.AFCSettings && AFCSettings.get("notifications")) {
      enable().then((ok) => {
        if (!ok && window.AFCSettings) {
          AFCSettings.set("notifications", false);
          const el = document.querySelector('[data-setting="notifications"]');
          if (el) el.classList.remove("on");
        }
      });
    }

    // реакция на переключение тумблера
    if (window.AFCSettings) {
      AFCSettings.onChange("notifications", async (on) => {
        if (on) {
          const ok = await enable();
          if (!ok) {
            AFCSettings.set("notifications", false);
            const el = document.querySelector('[data-setting="notifications"]');
            if (el) el.classList.remove("on");
            if (typeof addToast === "function") {
              addToast(isNative()
                ? "Разреши уведомления в настройках телефона"
                : "Уведомления работают в приложении (APK)");
            }
          } else if (typeof addToast === "function") {
            addToast("Напоминания включены");
          }
        } else {
          await disable();
        }
      });
    }
  }

  return { init, enable, disable, test, isNative };
})();
