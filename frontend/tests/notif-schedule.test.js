// Юнит-тесты логики расписания уведомлений. Запуск: `npm test` (node --test).
// Зависимостей нет — используется встроенный тест-раннер Node 18+.
const { test } = require("node:test");
const assert = require("node:assert/strict");

const {
  buildNotifications,
  WORKOUT_HOUR,
  WATER_HOUR,
  WATER_ID,
} = require("../www/js/notif-schedule.js");

const water = (notifs) => notifs.find((n) => n.id === WATER_ID);
const workouts = (notifs) => notifs.filter((n) => n.id !== WATER_ID);

test("напоминание про воду есть всегда — ежедневно в 13:00", () => {
  const w = water(buildNotifications({ training_days: "ПН, СР, ПТ" }));
  assert.ok(w, "должно быть уведомление про воду");
  assert.equal(w.schedule.on.hour, WATER_HOUR);
  assert.equal(WATER_HOUR, 13);
  assert.equal(w.schedule.on.weekday, undefined, "вода — без привязки ко дню недели");
  assert.equal(w.schedule.repeats, true);
});

test("без профиля и без дней тренировок — только вода", () => {
  assert.equal(buildNotifications(null).length, 1);
  assert.equal(buildNotifications({}).length, 1);
  assert.equal(buildNotifications({ training_days: "" }).length, 1);
});

test("дни тренировок → уведомления в 18:00 с верными номерами дней", () => {
  const notifs = buildNotifications({ training_days: "ПН, СР, ПТ" });
  const w = workouts(notifs);
  assert.equal(w.length, 3);
  // Capacitor: 1=вс … 7=сб → ПН=2, СР=4, ПТ=6
  assert.deepEqual(w.map((n) => n.schedule.on.weekday), [2, 4, 6]);
  for (const n of w) {
    assert.equal(n.schedule.on.hour, WORKOUT_HOUR);
    assert.equal(WORKOUT_HOUR, 18);
    assert.equal(n.schedule.repeats, true);
  }
});

test("у уведомлений уникальные id (вода не конфликтует с тренировками)", () => {
  const notifs = buildNotifications({ training_days: "ПН ВТ СР ЧТ ПТ СБ ВС" });
  const ids = notifs.map((n) => n.id);
  assert.equal(new Set(ids).size, ids.length);
  assert.ok(!workouts(notifs).some((n) => n.id === WATER_ID));
});

test("дни разбираются через запятую и пробелы, регистр игнорируется", () => {
  const a = workouts(buildNotifications({ training_days: "пн,ср" }));
  const b = workouts(buildNotifications({ training_days: "ПН СР" }));
  assert.deepEqual(a.map((n) => n.schedule.on.weekday), [2, 4]);
  assert.deepEqual(b.map((n) => n.schedule.on.weekday), [2, 4]);
});

test("невалидные дни пропускаются", () => {
  const notifs = buildNotifications({ training_days: "ПН, XX, ПТ" });
  assert.deepEqual(workouts(notifs).map((n) => n.schedule.on.weekday), [2, 6]);
});
