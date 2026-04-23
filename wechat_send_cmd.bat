@echo off
chcp 65001 >nul
echo ========================================
echo WeChat Send Message
echo ========================================
echo.

if "%~2"=="" (
    echo Usage: wechat_send_cmd.bat "contact" "message"
    echo Example: wechat_send_cmd.bat "张三" "晚上好！"
    pause
    exit /b 1
)

echo Contact: %~1
echo Message: %~2
echo.

set /p confirm="Confirm? (y/n): "
if /i not "%confirm%"=="y" (
    echo Cancelled
    pause
    exit /b 0
)

echo.
echo Sending...
py "%~dp0wechat_send.py" "%~1" "%~2"

echo.
pause
