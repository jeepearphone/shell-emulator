@echo off
cd /d "%~dp0.."
call scripts\make_vfs.bat
echo === 1. no parameters ===
python main.py
echo === 2. only --vfs ===
python main.py --vfs vfs_samples/files
echo === 3. all parameters from command line ===
python main.py --vfs vfs_samples/files --script scripts/start_ok.txt
pause