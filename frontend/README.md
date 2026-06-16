# Frontend — AI Fit Coach

Чистый веб-app (HTML/CSS/JS) в `www/`. Упаковывается в APK (Android) и позже
в iOS через **Capacitor**. Дизайна нет — только кнопки.

## Локальный запуск (браузер)

`www/` — статика, открывается как обычный сайт. Удобно отдавать любым статик-сервером:

```bash
cd www
python -m http.server 5173
# открыть http://localhost:5173
```

Бэкенд должен крутиться на `http://localhost:8000` (см. `API_BASE` в `www/js/api.js`).

## Сборка APK (Android)

Нужны Node.js и Android Studio (SDK).

```bash
npm install
npx cap add android        # один раз — создаёт android/ проект
npx cap sync               # копирует www/ в нативный проект
npx cap open android       # откроет Android Studio → Build > Build APK
```

> ⚠️ В APK приложение грузится с `https://localhost`, поэтому `API_BASE` в
> `www/js/api.js` нужно поменять с `http://localhost:8000` на реальный адрес
> бэкенда (домен/IP с HTTPS), иначе запросы не пройдут.

## iOS (позже)

```bash
npx cap add ios
npx cap open ios           # Xcode (нужен macOS)
```

## Структура

```
www/                 статика, попадает в APK
├── index.html       экран входа/регистрации + дашборд
├── css/style.css
├── js/api.js        fetch + JWT в localStorage
├── js/auth.js       register/login/logout
└── js/app.js        обработчики кнопок
capacitor.config.json
package.json
```
