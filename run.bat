@echo off
rem Запуск эмулятора: run.bat [--vfs PATH] [--script PATH] [--config PATH]
rem Запуск тестов:    run.bat test
cd /d "%~dp0"
if "%1"=="test" (
    python -m unittest discover -s tests -t . -v
) else (
    python src\main.py %*
)