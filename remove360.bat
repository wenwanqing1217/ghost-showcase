@echo off
chcp 65001 >nul 2>&1
title 360 彻底清理工具
echo ========================================
echo      360 安全卫士 彻底清理工具
echo ========================================
echo.
echo  本脚本将执行以下操作：
echo  1. 停止所有360进程
echo  2. 删除360服务
echo  3. 删除360文件夹
echo  4. 清理注册表启动项
echo  5. 删除计划任务
echo.
echo  请确保已以管理员身份运行此脚本！
echo ========================================
echo.
pause

echo [1/5] 正在停止360进程...
taskkill /F /IM 360Tray.exe 2>nul
taskkill /F /IM 360Safe.exe 2>nul
taskkill /F /IM 360AppLoader.exe 2>nul
taskkill /F /IM MultiTip.exe 2>nul
taskkill /F /IM DFSSearchService.exe 2>nul
taskkill /F /IM 360DeskAna.exe 2>nul
taskkill /F /IM 360DeskAna64.exe 2>nul
taskkill /F /IM LiveUpdate360.exe 2>nul
taskkill /F /IM SodaDownloader.exe 2>nul
taskkill /F /IM DumpUper.exe 2>nul
timeout /t 2 /nobreak >nul

echo [2/5] 正在删除360服务...
for %%s in (360netmon 360Box64 360Camera 360AntiHacker 360Hvm 360AntiHijack 360AntiSteal 360FsFlt 360Sensor 360boost 360Tray) do (
    sc stop %%s 2>nul
    sc delete %%s 2>nul
)
sc delete 360netmon 2>nul
sc delete 360Box64 2>nul
sc delete 360Camera 2>nul
sc delete 360AntiHacker 2>nul
sc delete 360Hvm 2>nul
sc delete 360AntiHijack 2>nul
sc delete 360AntiSteal 2>nul
sc delete 360FsFlt 2>nul
sc delete 360Sensor 2>nul
sc delete 360boost 2>nul

echo [3/5] 正在删除360文件夹...
takeown /F "C:\Program Files (x86)\360" /R /D Y 2>nul
icacls "C:\Program Files (x86)\360" /grant Administrators:F /T 2>nul
rd /s /q "C:\Program Files (x86)\360" 2>nul
rd /s /q "C:\Program Files\360" 2>nul
rd /s /q "C:\ProgramData\360Safe" 2>nul

echo [4/5] 正在清理注册表...
reg delete "HKLM\SOFTWARE\360Safe" /f 2>nul
reg delete "HKLM\SOFTWARE\360" /f 2>nul
reg delete "HKCU\SOFTWARE\360Safe" /f 2>nul
reg delete "HKCU\SOFTWARE\360" /f 2>nul
reg delete "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "360Safe" /f 2>nul
reg delete "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "360Tray" /f 2>nul
reg delete "HKLM\SOFTWARE\WOW6432Node\360Safe" /f 2>nul
reg delete "HKLM\SOFTWARE\WOW6432Node\360" /f 2>nul

echo [5/5] 正在清理计划任务和启动文件夹...
schtasks /Delete /TN "360*" /F 2>nul
del /f /q "%ProgramData%\Microsoft\Windows\Start Menu\Programs\Startup\360*" 2>nul
del /f /q "%AppData%\Microsoft\Windows\Start Menu\Programs\Startup\360*" 2>nul

echo.
echo ========================================
echo  清理完成！
echo ========================================
echo.
echo  建议操作：
echo  1. 重启计算机以确保所有残留被清除
echo  2. 重启后检查 C:\Program Files (x86)\ 下是否还有360文件夹
echo  3. 如有残留，重启进入安全模式再次删除
echo.
pause
