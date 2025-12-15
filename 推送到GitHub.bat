@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   推送到 GitHub
echo ========================================
echo.

cd /d "%~dp0"

REM 检查是否已配置服务器地址
findstr /C:"192.168.1.100" Tweak.x >nul
if %errorlevel%==0 (
    echo ⚠️  警告：检测到默认 IP 地址 192.168.1.100
    echo.
    echo 建议先运行以下命令配置正确的 IP：
    echo   python 自动配置.py
    echo.
    set /p CONTINUE="是否继续推送？(y/n) [n]: "
    if not "%CONTINUE%"=="y" (
        echo 已取消
        pause
        exit /b 0
    )
)

echo.
echo 检查 Git 状态...
git status

echo.
echo ----------------------------------------
echo.

if not exist ".git" (
    echo 初始化 Git 仓库...
    git init
    git branch -M main
)

echo 添加文件...
git add .

echo.
set /p COMMIT_MSG="请输入提交信息 [Update tweak]: "
if "%COMMIT_MSG%"=="" set COMMIT_MSG=Update tweak

git commit -m "%COMMIT_MSG%"

echo.
echo 检查 remote...
git remote -v

git remote | findstr "origin" >nul
if %errorlevel%==0 (
    echo Remote origin 已存在
    echo.
    set /p PUSH_NOW="是否立即推送？(y/n) [y]: "
    if "%PUSH_NOW%"=="" set PUSH_NOW=y

    if "%PUSH_NOW%"=="y" (
        echo.
        echo 推送到 GitHub...
        git push

        if %errorlevel%==0 (
            echo.
            echo ✅ 推送成功！
            echo.
            echo 访问 GitHub Actions 查看编译进度：
            echo   gh repo view --web
            echo.
        ) else (
            echo.
            echo ❌ 推送失败
            echo.
        )
    )
) else (
    echo.
    echo 未配置 remote origin
    echo.
    echo 请先创建 GitHub 仓库，然后运行：
    echo   一键部署.bat
    echo.
    echo 或手动添加 remote：
    echo   git remote add origin https://github.com/你的用户名/UnionPayAuto.git
    echo   git push -u origin main
    echo.
)

pause
