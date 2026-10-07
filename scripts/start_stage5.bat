@echo off
cd /d "%~dp0.." || exit /b 1
call scripts\make_vfs.bat
echo === all commands of stage 5: rm ===
python main.py --vfs vfs_samples/deep --script scripts/start_stage5.txt
echo === folder on disk AFTER rm: all files must still be here ===
dir /s /b vfs_samples\deep
pause