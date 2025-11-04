# Используем легкий образ Python
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get clean

# Создаем пользователя для безопасности
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /home/app

# Копируем зависимости
COPY --chown=app:app requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir --user -r requirements.txt

# Копируем код приложения
COPY --chown=app:app . .

# Запускаем бота
CMD ["python", "hello_world.py"]