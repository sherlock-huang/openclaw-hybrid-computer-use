@echo off
chcp 65001 >nul
echo ==========================================
echo 微信发送消息
echo ==========================================
echo.

:: 检查 py 命令
where py >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 找不到 py 命令
    echo 请确保 Python 已安装并添加到 PATH
    pause
    exit /b 1
)

:: 运行脚本
py "%~dp0wechat_run.py" %*

pause
