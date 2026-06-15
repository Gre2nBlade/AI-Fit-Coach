FROM python:3.12-slim

WORKDIR /app

# Зависимости отдельным слоем для кэширования
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Каталог под SQLite-файл
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["python", "-m", "bot.main"]
