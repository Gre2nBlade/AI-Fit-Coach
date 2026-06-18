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
    "отжимания": "https://rutube.ru/video/c2e14affff0915096ac0eea29719f424/",
    "отжимания от пола": "https://rutube.ru/video/c2e14affff0915096ac0eea29719f424/",
    "отжимания узким хватом": "https://rutube.ru/video/a4c0c843f2d0e66e77df396ccadb1420/",
    "приседания": "https://rutube.ru/video/360fdaef89826ec4cd2eff4fb8ecd89f/",
    "выпады": "https://rutube.ru/video/ae88ef7e2a9fb1901000e8a1f90bd8ec/",
    "подтягивания": "https://rutube.ru/video/690e3232c3edd5eff117eb699dd63db2/",
    "планка": "https://rutube.ru/video/4d856b988d2da6caf41bdc1f55594f96/",
    "берпи": "https://rutube.ru/video/d79f9cfd071a1e92c619fc1f1ab52d94/",
    "ягодичный мостик": "https://rutube.ru/video/b65470162fffc6cc063824b205ad95c5/",
    "тяга гантели в наклоне": "https://rutube.ru/video/e5c5d927c3f1f9a39eaadbf476b130d6/",
    "жим гантелей лёжа": "https://rutube.ru/video/5a4493d4945c83450b3046d5172b4504/",
    "жим штанги лёжа": "https://rutube.ru/video/eaa78a57d31e5a6d2de17af63baaf9a3/",
    "разводка гантелей": "https://rutube.ru/video/277ccc492dfec0555d3a77b8898b21c5/",
    "гиперэкстензия": "https://rutube.ru/video/fdbe5f048d7fbcdbe56d2173c04bb8f0/",
    "подъём гантелей на бицепс": "https://rutube.ru/video/382c0c232caab00697866902a18d761f/",
    "французский жим": "https://rutube.ru/video/24c73eee5c0374dbf16a4f2540f449e9/",
    "молотки": "https://rutube.ru/video/f50640dd9d33d9ce09204c38c1bb2322/",
    "разгибания на трицепс": "https://rutube.ru/video/1586950a393b959c6fa7634987477675/",
    "подъём на носки": "https://rutube.ru/video/fda13aea5d12d2c3d83a6e3894db370c/",
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
