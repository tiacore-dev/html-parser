#!/bin/sh
set -eu

rm -f /tmp/.X99-lock
Xvfb :99 -screen 0 1920x1080x24 &

exec "$@"
