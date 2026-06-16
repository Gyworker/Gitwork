@echo off
chcp 65001 > nul
echo ========================================
echo  推送修复到GitHub
echo ========================================
cd /d D:\GITwork
"D:\Program Files\Git\cmd\git.exe" push -u origin main
pause
