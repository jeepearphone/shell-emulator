@echo off
cd /d "%~dp0.."
echo === 1. no parameters ===
python main.py
echo === 2. only --vfs ===
python main.py --vfs vfs_cli
echo === 3. all parameters from command line ===
python main.py --vfs vfs_cli --script scripts/start_ok.txt
pause