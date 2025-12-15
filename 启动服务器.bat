@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   快速启动 BHV 接收服务器
echo ========================================
echo.

cd /d "%~dp0"

if not exist "bhv_server.py" (
    echo ❌ 错误：找不到 bhv_server.py
    pause
    exit /b 1
)

echo 正在启动服务器...
echo.
echo 提示：
echo - 记下显示的 IP 地址
echo - 如果是第一次运行，需要修改 Tweak.x 中的服务器地址
echo - 按 Ctrl+C 停止服务器
echo.
echo ----------------------------------------
echo.

python bhv_server.py

pause
