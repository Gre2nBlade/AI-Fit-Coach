# AI Fit Coach

Персональный фитнес-коуч с AI: веб-приложение + бэкенд. Сайт упаковывается в
мобильное приложение (APK для Android, позже iOS) через **Capacitor**.

> ⚠️ **Черновой каркас (ветка `dev`).** Дизайна нет, бизнес-логика — заглушки.
> Цель: рабочая структура слоёв, по которой дальше наращивается функционал.

## Стек

| Слой           | Технология                                  |
|----------------|---------------------------------------------|
| Бэкенд API     | FastAPI + uvicorn                           |
| Аутентификация | email + пароль, JWT (python-jose, passlib)  |
| AI             | OpenRouter через httpx (async)              |
| ORM            | SQLAlchemy 2.0 + aiosqlite                  |
| Миграции       | Alembic (подключается позже)                |
| Конфиг         | pydantic-settings (.env)                    |
| Планировщик    | APScheduler 3.x                             |
| Кэш            | dict + TTL в памяти (→ Redis потом)         |
| Фронтенд       | чистый HTML/CSS/JS                          |
| Мобилка        | Capacitor (APK Android, потом iOS)          |
| Деплой бэка    | Docker + docker-compose                     |

## Структура

```
backend/                 FastAPI-бэкенд
├── main.py              точка входа (uvicorn)
├── config.py            pydantic-settings (.env)
├── Dockerfile
├── requirements.txt
├── api/
│   ├── app.py           сборка FastAPI, CORS, lifespan (init_db + scheduler)
│   ├── dependencies.py  get_current_user_id — проверка JWT (Bearer)
│   └── routers/         auth, user, workout, nutrition
├── services/            бизнес-логика (без HTTP)
│   ├── auth_service.py  хеш паролей + JWT
│   ├── ai_service.py    промпты + OpenRouter
│   ├── user_service.py
│   ├── workout_service.py
│   ├── nutrition_service.py
│   └── scheduler.py
├── db/
│   ├── base.py · engine.py · models.py
│   └── repositories/    user_repo, workout_repo, nutrition_repo  (единственное место с SQL)
└── cache/memory_cache.py

frontend/                Веб-app → Capacitor
├── www/                 статика (попадает в APK): index.html, css/, js/
├── capacitor.config.json
├── package.json
└── README.md            как собрать APK

.env.example · docker-compose.yml
```

**Принцип слоёв:** роутеры → сервисы → репозитории → БД. SQL живёт только в
`db/repositories/`. Смена SQLite→PostgreSQL — одна строка `DATABASE_URL` в `.env`.

## Запуск бэкенда (локально)

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
cp .env.example .env        # вписать OPENROUTER_API_KEY и JWT_SECRET
python -m backend.main      # FastAPI на http://localhost:8000 (Swagger: /docs)
```

## Запуск бэкенда (Docker)

```bash
cp .env.example .env
docker compose up --build
```

## Запуск с публичным доступом (туннель)

Чтобы приложение в APK работало **с любого Wi-Fi и мобильного интернета**, а не
только из домашней сети, бэкенд выставляется наружу через **Cloudflare Tunnel**
(`cloudflared`) — даёт публичный `https`-адрес и работает в РФ.

Подготовка (один раз):

```bash
# установить cloudflared:
winget install --id Cloudflare.cloudflared
# (или https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/)
# для быстрого туннеля регистрация НЕ нужна.
```

Запуск бэкенда + туннеля одной командой:

```bash
# быстрый туннель (адрес случайный, меняется при каждом запуске):
bash scripts/serve-public.sh

# именованный туннель со своим доменом в Cloudflare (адрес постоянный):
#   разово: cloudflared tunnel login && cloudflared tunnel create afc
#           cloudflared tunnel route dns afc afc.example.com
CF_TUNNEL=afc bash scripts/serve-public.sh
```

Затем вписать публичный адрес (вида `https://...trycloudflare.com` или свой домен)
в `frontend/www/js/config.js` (`window.AFC_API_BASE`) **без `/` в конце** и
пересобрать фронт:

```bash
cd frontend && npx cap sync android
```

Проверка: открой `<публичный-адрес>/health` — должно вернуться `{"status":"ok"}`.
С именованным туннелем (свой домен) адрес вписывается один раз; быстрый туннель
выдаёт новый адрес после каждого перезапуска.

## Фронтенд и сборка APK

См. [`frontend/README.md`](frontend/README.md). Кратко:

```bash
cd frontend
npm install
npx cap add android
npx cap sync
npx cap open android        # Android Studio → Build APK
```

## Поток аутентификации

1. Фронт шлёт `POST /api/auth/register` или `/api/auth/login` (email + пароль).
2. Бэкенд проверяет/создаёт пользователя, возвращает **JWT**.
3. Фронт хранит токен в `localStorage`, шлёт его в `Authorization: Bearer <token>`.
4. `get_current_user_id` декодирует токен → `user_id` → роутер → сервис → репозиторий.

## Что есть / чего ещё нет

- ✅ Структура слоёв, JWT-авторизация, точки входа, заглушки сервисов
- ✅ Веб-app с кнопками + конфиг Capacitor под APK
- ⬜ Реальная бизнес-логика (промпты, генерация планов, расчёт КБЖУ)
- ⬜ Alembic-миграции, дизайн, тесты, нативная сборка APK
