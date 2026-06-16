# Frontend — AI Fit Coach

Веб-app (HTML/CSS/JS) в `www/`, упаковывается в APK (Android) / iOS через **Capacitor**.

## Флоу

```
index.html (вход/регистрация, JWT)
   └─ новый юзер → onboarding.html (4 шага + расчёты) → сохранение на бэкенд → app.html
   └─ вернувшийся → app.html
```

## Структура

```
www/
├── index.html        вход / регистрация (email + пароль)
├── onboarding.html   онбординг: 4 шага, валидация, «Назад», расчёт КБЖУ
├── app.html          приложение: сайдбар + 6 экранов
├── css/style.css     дизайн-система (тёмная тема, фиолетовый акцент)
├── js/config.js      ⚙️ АДРЕС БЭКЕНДА (менять тут)
├── js/api.js         fetch + JWT, единый apiGet/apiPost
├── js/auth.js        вход / регистрация / маршрутизация
├── js/calc.js        BMR / TDEE / BMI / КБЖУ (зеркало бэкенда)
├── js/onboarding.js  сбор профиля → POST /api/user/profile
└── js/app.js         профиль с бэка, метрики, ИИ-чат, аватарка, логаут
capacitor.config.json
package.json
```

Экраны `app.html`: Главная (метрики из профиля), Тренировки, Питание (КБЖУ
из расчёта), Прогресс, ИИ-Тренер (живой чат через `/api/ai/ask`), Профиль
(данные, загрузка фото, настройки).

## Локальный запуск (браузер)

1. Подними бэкенд (см. корневой README): `python -m backend.main` → `http://localhost:8000`.
   В `.env` обязательно задай `OPENROUTER_API_KEY`, иначе ИИ-чат вернёт ошибку.
2. Отдай статику:
   ```bash
   cd www
   python -m http.server 5173
   ```
   Открой `http://localhost:5173`.

`js/config.js` по умолчанию смотрит на `http://localhost:8000`.

## MVP на телефон (APK через Capacitor)

Нужны Node.js и Android Studio (с Android SDK).

**1. Адрес бэкенда.** Телефон не видит `localhost` компьютера. В `www/js/config.js`
укажи IP компьютера в общей Wi-Fi сети:
```js
window.AFC_API_BASE = "http://192.168.X.X:8000";   // твой IP (ipconfig / ifconfig)
```
Бэкенд уже слушает `0.0.0.0:8000`, так что будет доступен по сети.

**2. Сборка:**
```bash
cd frontend
npm install
npx cap add android        # один раз — создаёт android/
npx cap sync               # копирует www/ в нативный проект (повторять после правок)
npx cap open android       # Android Studio → Run (на телефоне) или Build > Build APK(s)
```
Готовый `app-debug.apk` лежит в `android/app/build/outputs/apk/debug/`.

> Для отладочного APK по `http://<IP>` Capacitor по умолчанию разрешает
> cleartext-трафик — отдельной настройки не требует. Для продакшна — вынести
> бэкенд на домен с HTTPS и поменять `AFC_API_BASE`.

## iOS (позже)

```bash
npx cap add ios
npx cap open ios           # Xcode (нужен macOS)
```
