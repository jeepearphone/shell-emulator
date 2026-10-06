@echo off
cd /d "%~dp0.." || exit /b 1
call scripts\make_vfs.bat
echo === folder on disk BEFORE vfs-init ===
dir /s /b vfs_samples\deep
echo === all commands of stages 1-3, including vfs-init ===
python main.py --vfs vfs_samples/deep --script scripts/start_stage3.txt
echo === folder on disk AFTER vfs-init (nothing listed = empty) ===
dir /s /b vfs_samples\deep 2>nul
pause