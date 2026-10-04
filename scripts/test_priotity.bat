@echo off
cd /d "%~dp0.."
echo === config.xml says vfs_from_config, CLI says vfs_cli: CLI must win ===
python main.py --config scripts/config.xml --vfs vfs_cli
pause