# ===== Этап 1: билд Python-зависимостей =====
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --prefix=/install --no-cache-dir -r requirements.txt

# ===== Этап 2: runtime =====
FROM python:3.12-slim

WORKDIR /app

# Установка системных зависимостей + Firefox + geckodriver
RUN apt-get update && apt-get install -y --no-install-recommends \
    firefox-esr \
    wget \
    curl \
    unzip \
    xvfb \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libnss3 \
    libasound2 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxss1 \
    libxtst6 \
    libxi6 \
    fonts-liberation \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Установка geckodriver (последняя стабильная)
RUN GECKO_VERSION="v0.36.0" && \
    wget -q "https://github.com/mozilla/geckodriver/releases/download/$GECKO_VERSION/geckodriver-$GECKO_VERSION-linux64.tar.gz" && \
    tar -xzf "geckodriver-$GECKO_VERSION-linux64.tar.gz" && \
    rm "geckodriver-$GECKO_VERSION-linux64.tar.gz" && \
    mv geckodriver /usr/local/bin/ && chmod +x /usr/local/bin/geckodriver

# Копируем зависимости из builder'а
COPY --from=builder /install /usr/local

# Копируем исходный код
COPY . .

# Очистка мусора перед стартом + запуск
CMD sh -c "rm -rf /tmp/* ~/.mozilla ~/.cache && Xvfb :99 -screen 0 1920x1080x24 & gunicorn -c gunicorn.conf.py run:app"
