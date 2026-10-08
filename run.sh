#!/bin/sh
# Запуск эмулятора: ./run.sh [--vfs PATH] [--script PATH] [--config PATH]
# Запуск тестов:    ./run.sh test
cd "$(dirname "$0")" || exit 1
if [ "$1" = "test" ]; then
    python3 -m unittest discover -s tests -t . -v
else
    python3 src/main.py "$@"
fi