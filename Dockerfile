# Используем официальный Python-образ
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости и удаляем мусор
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    unzip \
    gnupg \
    firefox-esr \
    xvfb \
    libnss3 \
    libxss1 \
    libasound2 \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Устанавливаем GeckoDriver
RUN GECKODRIVER_VERSION="v0.33.0" && \
    wget -q "https://github.com/mozilla/geckodriver/releases/download/$GECKODRIVER_VERSION/geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz" && \
    tar -xzf "geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz" && \
    rm "geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz" && \
    mv geckodriver /usr/local/bin/ && \
    chmod +x /usr/local/bin/geckodriver

# Устанавливаем зависимости Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код проекта
COPY . .

# Запускаем приложение через Xvfb и gunicorn
CMD sh -c "Xvfb :99 -screen 0 1920x1080x24 & gunicorn -c gunicorn.conf.py run:app"
