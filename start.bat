@echo off
chcp 65001 >nul
echo ===============================================
echo    云闪付自动领券工具
echo ===============================================
echo.

:menu
echo 请选择运行模式：
echo.
echo 1. 首次使用 - 从HAR文件提取配置
echo 2. 单账号模式
echo 3. 多账号并发模式
echo 4. 多账号顺序模式
echo 5. 多账号智能模式（推荐）
echo 6. 查看运行日志
echo 7. 安装依赖
echo 0. 退出
echo.

set /p choice=请输入选项（0-7）:

if "%choice%"=="1" goto extract
if "%choice%"=="2" goto single
if "%choice%"=="3" goto concurrent
if "%choice%"=="4" goto sequential
if "%choice%"=="5" goto smart
if "%choice%"=="6" goto logs
if "%choice%"=="7" goto install
if "%choice%"=="0" goto end
goto menu

:extract
echo.
echo ===============================================
echo 提取HAR文件配置
echo ===============================================
echo.
set /p har_file=请输入HAR文件路径（或拖拽文件到此窗口）:
python har_parser.py "%har_file%"
echo.
echo 配置已提取到 extracted_config.py
echo 请将内容复制到 config.py 后运行脚本
echo.
pause
goto menu

:install
echo.
echo ===============================================
echo 安装依赖
echo ===============================================
echo.
python -m pip install -r requirements.txt
echo.
echo 依赖安装完成！
echo.
pause
goto menu

:single
echo.
echo ===============================================
echo 启动单账号模式
echo ===============================================
echo.
python unionpay_auto.py
pause
goto menu

:concurrent
echo.
echo ===============================================
echo 启动多账号并发模式
echo ===============================================
echo.
set /p workers=请输入并发数（默认3）:
if "%workers%"=="" set workers=3
python multi_account_runner.py --mode concurrent --workers %workers%
pause
goto menu

:sequential
echo.
echo ===============================================
echo 启动多账号顺序模式
echo ===============================================
echo.
set /p delay=请输入间隔秒数（默认2）:
if "%delay%"=="" set delay=2
python multi_account_runner.py --mode sequential --delay %delay%
pause
goto menu

:smart
echo.
echo ===============================================
echo 启动多账号智能模式（推荐）
echo ===============================================
echo.
python multi_account_runner.py --mode smart
pause
goto menu

:logs
echo.
echo ===============================================
echo 查看运行日志
echo ===============================================
echo.
echo 1. 单账号日志 (unionpay_auto.log)
echo 2. 多账号日志 (multi_account.log)
echo 3. 返回主菜单
echo.
set /p log_choice=请选择（1-3）:

if "%log_choice%"=="1" type unionpay_auto.log | more
if "%log_choice%"=="2" type multi_account.log | more
if "%log_choice%"=="3" goto menu

pause
goto menu

:end
echo.
echo 感谢使用！再见！
timeout /t 2 >nul
exit

