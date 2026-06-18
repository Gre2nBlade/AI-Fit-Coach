// Чистая логика расписания локальных уведомлений (без обращения к window/Capacitor),
// чтобы её можно было покрыть юнит-тестами (node --test) и переиспользовать в браузере.
//
// Экспортируется как CommonJS-модуль (для тестов) и как window.AFCNotifSchedule (в браузере).
(function (root) {
  // День недели из профиля → номер в Capacitor (1=вс … 7=сб).
  const DOW = { "ВС": 1, "ПН": 2, "ВТ": 3, "СР": 4, "ЧТ": 5, "ПТ": 6, "СБ": 7 };
  const WORKOUT_HOUR = 18; // напоминание о тренировке
  const WATER_HOUR = 13;   // напоминание про воду
  const WATER_ID = 200;

  // Построить массив уведомлений из профиля: тренировки в дни из профиля + вода ежедневно.
  function buildNotifications(profile) {
    const notifs = [];
    const days = (profile && profile.training_days)
      ? String(profile.training_days).split(/[,\s]+/).filter(Boolean)
      : [];

    days.forEach((d, i) => {
      const weekday = DOW[d.toUpperCase()];
      if (!weekday) return;
      notifs.push({
        id: 100 + i,
        title: "AI Fit Coach",
        body: "Время тренировки! Открой приложение и начни занятие 💪",
        schedule: { on: { weekday, hour: WORKOUT_HOUR, minute: 0 }, repeats: true },
      });
    });

    // ежедневное напоминание про воду
    notifs.push({
      id: WATER_ID,
      title: "Не забудь про воду 💧",
      body: "Сделай пару глотков — поддержи норму воды на сегодня.",
      schedule: { on: { hour: WATER_HOUR, minute: 0 }, repeats: true },
    });

    return notifs;
  }

  const api = { DOW, WORKOUT_HOUR, WATER_HOUR, WATER_ID, buildNotifications };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  } else {
    root.AFCNotifSchedule = api;
  }
})(typeof window !== "undefined" ? window : globalThis);
