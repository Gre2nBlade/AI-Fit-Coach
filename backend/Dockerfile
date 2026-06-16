FROM python:3.12-slim

WORKDIR /app

# Зависимости отдельным слоем для кэширования
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем пакет backend как backend/ внутрь /app, чтобы работали импорты backend.*
COPY backend ./backend

RUN mkdir -p /app/data

EXPOSE 8000

CMD ["python", "-m", "backend.main"]
