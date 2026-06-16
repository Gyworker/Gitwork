@echo off
chcp 65001 > nul
echo ========================================
echo  推送到GitHub
echo ========================================
echo.

cd /d D:\GITwork

echo 配置远程仓库...
"D:\Program Files\Git\cmd\git.exe" remote set-url origin https://github.com/Gyworker/Gitwork.git

echo.
echo 开始推送...
echo.

"D:\Program Files\Git\cmd\git.exe" push -u origin main

echo.
echo ========================================
echo  推送完成！
echo.
echo 请访问 https://github.com/Gyworker/Gitwork/actions
echo 查看CI检查结果
echo ========================================
pause
