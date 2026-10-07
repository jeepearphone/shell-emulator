@echo off
cd /d "%~dp0.."
call scripts\make_vfs.bat
echo === config.xml says vfs_from_config, CLI says vfs_samples/files: CLI must win ===
python main.py --config scripts/config.xml --vfs vfs_samples/files
pause