#!/bin/bash

# Удалим старый лок, если остался
rm -f /tmp/.X99-lock

# Запускаем виртуальный X-сервер в фоне
Xvfb :99 -screen 0 1920x1080x24 &

# Экспортируем DISPLAY переменную
export DISPLAY=:99

# Запускаем приложение
exec python schedule_run.py
