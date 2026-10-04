@echo off
cd /d "%~dp0.."
echo === parameters only from config.xml ===
python main.py --config scripts/config.xml
pause