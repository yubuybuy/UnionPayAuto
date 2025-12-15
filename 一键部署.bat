@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   云闪付 Tweak - 快速部署脚本
echo ========================================
echo.

cd /d "%~dp0"

REM 检查必要文件
if not exist "Tweak.x" (
    echo ❌ 错误：找不到 Tweak.x
    pause
    exit /b 1
)

if not exist "bhv_server.py" (
    echo ❌ 错误：找不到 bhv_server.py
    pause
    exit /b 1
)

echo 步骤 1/4: 启动 BHV 接收服务器
echo ----------------------------------------
echo 正在启动服务器获取 IP 地址...
echo.

REM 启动服务器并获取IP（后台运行）
start /min cmd /c "python bhv_server.py > server_ip.tmp"

REM 等待服务器启动
timeout /t 3 /nobreak >nul

echo 请查看弹出的服务器窗口，找到类似这样的信息：
echo   本地地址: http://192.168.1.100:8888
echo.
set /p SERVER_IP="请输入你的电脑 IP 地址（例如 192.168.1.100）: "

if "%SERVER_IP%"=="" (
    echo ❌ 错误：IP 地址不能为空
    pause
    exit /b 1
)

echo.
echo 步骤 2/4: 更新 Tweak.x 配置
echo ----------------------------------------

REM 使用 PowerShell 替换 IP 地址
powershell -Command "(Get-Content 'Tweak.x') -replace 'http://192\.168\.1\.100:8888/bhv', 'http://%SERVER_IP%:8888/bhv' | Set-Content 'Tweak.x'"

echo ✅ 已更新服务器地址为: http://%SERVER_IP%:8888/bhv
echo.

echo 步骤 3/4: 初始化 Git 仓库
echo ----------------------------------------

if exist ".git" (
    echo Git 仓库已存在
) else (
    git init
    echo ✅ Git 仓库初始化完成
)

git add .
git status
echo.

echo 步骤 4/4: 准备推送到 GitHub
echo ----------------------------------------
echo.
echo 请按照以下步骤操作：
echo.
echo 1. 访问 https://github.com/new 创建新仓库
echo 2. 仓库名建议：UnionPayAuto
echo 3. 创建完成后，复制仓库地址（例如：https://github.com/你的用户名/UnionPayAuto.git）
echo.
set /p REPO_URL="请输入你的 GitHub 仓库地址: "

if "%REPO_URL%"=="" (
    echo ❌ 错误：仓库地址不能为空
    pause
    exit /b 1
)

REM 检查是否已有 remote
git remote | findstr "origin" >nul
if %errorlevel%==0 (
    echo 移除旧的 remote...
    git remote remove origin
)

git remote add origin %REPO_URL%
git branch -M main
git commit -m "Initial commit - UnionPay Auto Tweak with BHV capture"

echo.
echo 准备推送到 GitHub...
echo.
git push -u origin main

if %errorlevel%==0 (
    echo.
    echo ========================================
    echo   ✅ 推送成功！
    echo ========================================
    echo.
    echo 下一步：
    echo 1. 访问你的 GitHub 仓库
    echo 2. 点击 "Actions" 标签
    echo 3. 等待编译完成（约 2-3 分钟）
    echo 4. 下载 "UnionPayAuto-DEB" artifact
    echo.
    echo 快捷打开（如果安装了 gh）：
    echo   gh repo view --web
    echo.
) else (
    echo.
    echo ========================================
    echo   ⚠️ 推送失败
    echo ========================================
    echo.
    echo 可能的原因：
    echo 1. 仓库地址错误
    echo 2. 没有配置 Git 凭据
    echo 3. 网络问题
    echo.
    echo 请手动推送：
    echo   git push -u origin main
    echo.
)

pause
