@echo off
cd /d "%~dp0.."
call scripts\make_vfs.bat
echo === parameters only from config.xml ===
python main.py --config scripts/config.xml
pause