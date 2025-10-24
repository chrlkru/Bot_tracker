FROM python:3.11-slim

WORKDIR /app

# Копируем зависимости сначала для кэширования
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаем папку для логов
RUN mkdir -p logs

# Запускаем бота
CMD ["python", "bot.py"]