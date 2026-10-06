@echo off
cd /d "%~dp0.." || exit /b 1
if exist vfs_samples rmdir /s /q vfs_samples

mkdir vfs_samples\minimal
echo hello> vfs_samples\minimal\readme.txt

mkdir vfs_samples\files
echo first file> vfs_samples\files\a.txt
echo second file> vfs_samples\files\b.txt
echo name,value> vfs_samples\files\data.csv

mkdir vfs_samples\deep\etc
mkdir vfs_samples\deep\home\user\docs
echo root readme> vfs_samples\deep\readme.txt
echo mode=test> vfs_samples\deep\etc\config.txt
echo my notes> vfs_samples\deep\home\user\notes.txt
echo report text> vfs_samples\deep\home\user\docs\report.txt
echo todo list> vfs_samples\deep\home\user\docs\todo.txt

echo VFS samples created in vfs_samples