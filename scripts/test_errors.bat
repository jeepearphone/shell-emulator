@echo off
cd /d "%~dp0.."
echo === 1. config file does not exist ===
python main.py --config scripts/no_such.xml
echo === 2. broken XML ===
python main.py --config scripts/config_bad.xml
echo === 3. startup script does not exist ===
python main.py --script scripts/no_such.txt
echo === 4. script with erroneous lines ===
python main.py --script scripts/start_errors.txt
pause