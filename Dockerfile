# Используем официальный образ Python в качестве базового
FROM python:3.12-slim

# Указываем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    unzip \
    gnupg \
    chromium \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Прямое скачивание пакета Chrome
RUN wget -q https://www.slimjet.com/chrome/download-chrome.php?file=files%2Fchrome64_114.0.5735.90.deb -O google-chrome-stable_114.0.5735.90-1_amd64.deb && \
    apt-get update && \
    apt-get install -y ./google-chrome-stable_114.0.5735.90-1_amd64.deb && \
    rm google-chrome-stable_114.0.5735.90-1_amd64.deb && \
    apt-mark hold google-chrome-stable


# Устанавливаем ChromeDriver версии 114
RUN CHROME_DRIVER_VERSION=114.0.5735.90 && \
    wget -q https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip && \
    rm chromedriver_linux64.zip && \
    mv chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver

# Устанавливаем Python-зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Указываем переменную окружения для headless режима
ENV DISPLAY=:99

