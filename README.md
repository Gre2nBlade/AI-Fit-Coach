# AI Fit Coach 🏋️

Telegram-бот для персонального фитнес-коучинга с AI + MiniApp-дашборд.

> ⚠️ **Черновой каркас (ветка `dev`).** Дизайна нет, бизнес-логика — заглушки.
> Цель этого коммита: рабочая структура слоёв, по которой дальше наращивается мясо.

## Стек

| Слой            | Технология                                   |
|-----------------|----------------------------------------------|
| Telegram-бот    | python-telegram-bot 22.x (async)             |
| REST API        | FastAPI + uvicorn                            |
| AI              | OpenRouter через httpx (async)               |
| ORM             | SQLAlchemy 2.0 + aiosqlite                   |
| Миграции        | Alembic (подключается позже)                 |
| Конфиг          | pydantic-settings (.env)                     |
| Планировщик     | APScheduler 3.x                              |
| Кэш             | dict + TTL в памяти (→ Redis потом)          |
| MiniApp         | чистый HTML/CSS/JS + Telegram WebApp SDK     |
| Деплой          | Docker + docker-compose                      |

## Архитектура (сверху вниз)

```
Клиенты:   Telegram App            Браузер в Telegram (MiniApp)
              │                              │
Точки      bot/handlers/  ←── один процесс ──→  api/routers/
входа:     (python-telegram-bot)  asyncio.gather  (FastAPI)
              │                              │
              └──────────────┬───────────────┘
Сервисы:              services/  (бизнес-логика, без Telegram/HTTP)
                              │
Репозитории:        db/repositories/  (единственное место с SQL)
                              │
БД:                  SQLAlchemy 2.0 async + SQLite
```

**Принцип:** и хендлеры бота, и роутеры API вызывают одни и те же сервисы —
никакой дублированной логики.

## Структура

```
bot/        Telegram-слой (точка входа main.py, конфиг, handlers/)
api/        FastAPI для MiniApp (app, dependencies, routers/)
services/   Бизнес-логика (ai, user, workout, nutrition, scheduler)
db/         base, engine, models, repositories/
cache/      memory_cache.py (интерфейс совместим с будущим Redis)
miniapp/    index.html + css/js (голые кнопки, без дизайна)
```

## Запуск (локально)

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # вписать BOT_TOKEN и OPENROUTER_API_KEY
python -m bot.main          # запускает бота + FastAPI вместе
```

API поднимется на `http://localhost:8000` (Swagger: `/docs`).

## Запуск (Docker)

```bash
cp .env.example .env
docker compose up --build
```

## Что уже есть / чего ещё нет

- ✅ Структура слоёв, точки входа, заглушки сервисов/репозиториев
- ✅ HMAC-проверка `initData` в `api/dependencies.py`
- ✅ MiniApp с кнопками, дёргающими API
- ⬜ Реальная бизнес-логика (промпты, генерация планов, расчёт КБЖУ)
- ⬜ Alembic-миграции, дизайн MiniApp, тесты
```
