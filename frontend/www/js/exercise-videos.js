// Видео к упражнениям. Если ИИ прислал у упражнения поле `video` (URL) —
// используем его. Иначе ищем по названию в маппинге ниже (Darebee / YouTube),
// а для неизвестных упражнений отдаём ссылку-поиск на YouTube — так кнопка
// «Видео» работает для ЛЮБОГО упражнения, которое сгенерит ИИ.

const AFCVideos = (function () {
  // Общий плейлист с техникой (запасной вариант / «смотреть все»).
  const PLAYLIST =
    "https://www.youtube.com/playlist?list=PLmEioiKeQ7fgFOyZUiv8oMnmwxWq2ZCTX";

  // Маппинг по нормализованному названию (нижний регистр, без лишних слов).
  // Точечные ссылки на проверенные ролики/страницы Darebee и YouTube.
  const MAP = {
    "отжимания": "https://www.youtube.com/results?search_query=отжимания+техника",
    "отжимания от пола": "https://www.youtube.com/results?search_query=отжимания+от+пола+техника",
    "отжимания узким хватом": "https://www.youtube.com/results?search_query=отжимания+узким+хватом",
    "приседания": "https://www.youtube.com/results?search_query=приседания+техника",
    "выпады": "https://www.youtube.com/results?search_query=выпады+техника",
    "подтягивания": "https://www.youtube.com/results?search_query=подтягивания+техника",
    "планка": "https://darebee.com/exercises/plank-exercise.html",
    "берпи": "https://darebee.com/exercises/burpees-exercise.html",
    "ягодичный мостик": "https://www.youtube.com/results?search_query=ягодичный+мостик+техника",
    "тяга гантели в наклоне": "https://www.youtube.com/results?search_query=тяга+гантели+в+наклоне",
    "жим гантелей лёжа": "https://www.youtube.com/results?search_query=жим+гантелей+лёжа",
    "жим штанги лёжа": "https://www.youtube.com/results?search_query=жим+штанги+лёжа+техника",
    "разводка гантелей": "https://www.youtube.com/results?search_query=разводка+гантелей+техника",
    "гиперэкстензия": "https://www.youtube.com/results?search_query=гиперэкстензия+техника",
    "подъём гантелей на бицепс": "https://www.youtube.com/results?search_query=подъём+гантелей+на+бицепс",
    "французский жим": "https://www.youtube.com/results?search_query=французский+жим+техника",
    "молотки": "https://www.youtube.com/results?search_query=молотки+упражнение+бицепс",
    "разгибания на трицепс": "https://www.youtube.com/results?search_query=разгибания+на+трицепс",
    "подъём на носки": "https://www.youtube.com/results?search_query=подъём+на+носки+икры",
  };

  function norm(name) {
    return (name || "").trim().toLowerCase().replace(/ё/g, "ё").replace(/\s+/g, " ");
  }

  // Вернуть URL видео для упражнения.
  function urlFor(ex) {
    if (ex && ex.video) return ex.video;
    const key = norm(ex && ex.name);
    if (MAP[key]) return MAP[key];
    if (key) return "https://www.youtube.com/results?search_query=" + encodeURIComponent(key + " техника упражнения");
    return PLAYLIST;
  }

  return { urlFor, PLAYLIST };
})();
