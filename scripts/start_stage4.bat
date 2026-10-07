@echo off
cd /d "%~dp0.." || exit /b 1
call scripts\make_vfs.bat
set EMU_DIR=/home/user/docs
echo === all commands of stage 4: ls, cd, pwd, cat ===
python main.py --vfs vfs_samples/deep --script scripts/start_stage4.txt
pause