@echo off
cd /d "%~dp0.." || exit /b 1
call scripts\make_vfs.bat
echo === 1. minimal VFS (one file) ===
python main.py --vfs vfs_samples/minimal --script scripts/start_vfs.txt
echo === 2. VFS with several files ===
python main.py --vfs vfs_samples/files --script scripts/start_vfs.txt
echo === 3. VFS with nested folders (4 levels) ===
python main.py --vfs vfs_samples/deep --script scripts/start_vfs.txt
echo === 4. error: VFS path does not exist ===
python main.py --vfs vfs_samples/no_such --script scripts/start_vfs.txt
echo === 5. error: VFS path is a file, not a directory ===
python main.py --vfs scripts/config.xml --script scripts/start_vfs.txt
pause