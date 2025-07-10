#!/bin/bash
set -e

# Удаляем файл блокировки, если остался
rm -f /tmp/.X99-lock

# Запускаем виртуальный дисплей в фоне
Xvfb :99 -screen 0 1920x1080x24 &

# Запускаем Gunicorn
exec gunicorn -c gunicorn.conf.py run:app
