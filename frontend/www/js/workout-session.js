// Интерактивная тренировка: подход → отдых (таймер) → следующий подход,
// галочки выполнения, в конце — «Засчитать тренировку» (пишет результат на бэк
// и проставляет отметку дня). Звук таймера зависит от тумблера «Таймер и сигналы».
//
// API модуля:  AFCWorkout.start(group, onFinish)
//   group    — { title, exercises:[{name, sets, reps, rest, video}] }
//   onFinish — колбэк после успешного засчитывания (необязательный).

const AFCWorkout = (function () {
  let overlay = null;
  let S = null; // состояние текущей сессии

  function parseRestSeconds(rest) {
    if (rest == null) return 60;
    const str = String(rest).toLowerCase();
    const num = parseFloat(str.replace(",", "."));
    if (isNaN(num)) return 60;
    if (str.includes("мин")) return Math.round(num * 60);
    return Math.round(num); // секунды по умолчанию
  }

  function beep() {
    if (!(window.AFCSettings && AFCSettings.get("timer_sound"))) return;
    try {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) return;
      const ctx = new Ctx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain); gain.connect(ctx.destination);
      osc.type = "sine";
      osc.frequency.value = 880;
      gain.gain.setValueAtTime(0.001, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.4, ctx.currentTime + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4);
      osc.start();
      osc.stop(ctx.currentTime + 0.42);
      osc.onended = () => ctx.close();
    } catch (e) {}
  }

  function esc(s) {
    const d = document.createElement("div");
    d.textContent = s == null ? "" : s;
    return d.innerHTML;
  }

  function buildOverlay() {
    overlay = document.createElement("div");
    overlay.className = "ws-overlay";
    overlay.innerHTML =
      `<div class="ws-card">
         <button class="ws-close" id="ws-close" title="Завершить">&times;</button>
         <div class="ws-head">
           <div class="ws-title" id="ws-ex-title">—</div>
           <div class="ws-sub" id="ws-ex-sub">—</div>
         </div>
         <div class="ws-stage" id="ws-stage"></div>
         <div class="ws-list" id="ws-list"></div>
       </div>`;
    document.body.appendChild(overlay);
    document.getElementById("ws-close").addEventListener("click", () => {
      if (confirm("Завершить тренировку без засчитывания?")) close();
    });
  }

  function close() {
    stopTimer();
    if (overlay) { overlay.remove(); overlay = null; }
    S = null;
  }

  let timerId = null;
  function stopTimer() {
    if (timerId) { clearInterval(timerId); timerId = null; }
  }

  function renderList() {
    const list = document.getElementById("ws-list");
    if (!list) return;
    list.innerHTML = S.exercises.map((ex, i) => {
      const doneSets = S.progress[i];
      const total = ex.sets || 1;
      const done = doneSets >= total;
      const cur = i === S.exIdx;
      return `<div class="ws-li${cur ? " cur" : ""}${done ? " done" : ""}">
        <span class="ws-check">${done ? "✓" : (i + 1)}</span>
        <span class="ws-li-nm">${esc(ex.name)}</span>
        <span class="ws-li-meta">${doneSets}/${total}</span>
        <a class="ws-video" href="${AFCVideos.urlFor(ex)}" target="_blank" rel="noopener" title="Видео">▶</a>
      </div>`;
    }).join("");
  }

  function currentExercise() { return S.exercises[S.exIdx]; }

  // Показать активный подход.
  function showSet() {
    stopTimer();
    const ex = currentExercise();
    const total = ex.sets || 1;
    const setNo = S.progress[S.exIdx] + 1;
    document.getElementById("ws-ex-title").textContent = ex.name || "Упражнение";
    document.getElementById("ws-ex-sub").textContent =
      `Упражнение ${S.exIdx + 1} из ${S.exercises.length}`;

    const stage = document.getElementById("ws-stage");
    stage.innerHTML =
      `<div class="ws-set">Подход ${setNo} из ${total}</div>
       <div class="ws-reps">${esc(ex.reps != null ? ex.reps : "—")} повторений</div>
       <a class="ws-video-btn" href="${AFCVideos.urlFor(ex)}" target="_blank" rel="noopener">
         <span class="micon">play_circle</span> Как делать (видео)
       </a>
       <button class="btn ws-done" id="ws-set-done">Подход выполнен</button>`;
    document.getElementById("ws-set-done").addEventListener("click", onSetDone);
    renderList();
  }

  function onSetDone() {
    S.progress[S.exIdx] += 1;
    const ex = currentExercise();
    const total = ex.sets || 1;

    // последний подход последнего упражнения?
    const isLastEx = S.exIdx >= S.exercises.length - 1;
    const exDone = S.progress[S.exIdx] >= total;
    if (exDone && isLastEx) { finishScreen(); return; }

    if (exDone) S.exIdx += 1; // к следующему упражнению
    restScreen();
  }

  function restScreen() {
    const ex = currentExercise();
    let left = parseRestSeconds(ex.rest);
    const stage = document.getElementById("ws-stage");
    stage.innerHTML =
      `<div class="ws-rest-lbl">Отдых</div>
       <div class="ws-rest" id="ws-rest">${left}</div>
       <div class="ws-sub">Следующий подход: ${esc(ex.name)}</div>
       <button class="btn btn-ghost ws-skip" id="ws-skip">Пропустить отдых</button>`;
    renderList();
    document.getElementById("ws-skip").addEventListener("click", () => { stopTimer(); showSet(); });

    stopTimer();
    timerId = setInterval(() => {
      left -= 1;
      const el = document.getElementById("ws-rest");
      if (el) el.textContent = left;
      if (left <= 3 && left > 0) beep();
      if (left <= 0) { stopTimer(); beep(); showSet(); }
    }, 1000);
  }

  function finishScreen() {
    stopTimer();
    document.getElementById("ws-ex-title").textContent = "Тренировка завершена";
    document.getElementById("ws-ex-sub").textContent = S.title || "";
    const stage = document.getElementById("ws-stage");
    const totalSets = S.exercises.reduce((a, e) => a + (e.sets || 1), 0);
    stage.innerHTML =
      `<div class="ws-finish-ico"><span class="micon">military_tech</span></div>
       <div class="ws-set">Отлично! ${totalSets} подходов выполнено</div>
       <div class="ws-sub">Засчитать тренировку в прогресс?</div>
       <button class="btn ws-done" id="ws-count">Засчитать</button>
       <button class="btn btn-ghost ws-skip" id="ws-skip2">Закрыть без засчёта</button>`;
    renderList();
    document.getElementById("ws-skip2").addEventListener("click", close);
    document.getElementById("ws-count").addEventListener("click", async () => {
      const btn = document.getElementById("ws-count");
      btn.disabled = true; btn.textContent = "Сохраняю…";
      const note = `${S.title}: ${totalSets} подходов`;
      const res = await apiPost("/api/workout/complete", { note });
      const cb = S.onFinish;
      close();
      if (res.ok && typeof cb === "function") cb(res.data);
    });
  }

  function start(group, onFinish) {
    const exercises = (group && group.exercises) || [];
    if (!exercises.length) { alert("В этой тренировке нет упражнений."); return; }
    S = {
      title: group.title || group.group || "Тренировка",
      exercises,
      progress: exercises.map(() => 0),
      exIdx: 0,
      onFinish,
    };
    if (!overlay) buildOverlay();
    showSet();
  }

  return { start, close };
})();
