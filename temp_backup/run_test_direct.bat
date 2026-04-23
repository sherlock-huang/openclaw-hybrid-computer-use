@echo off
chcp 65001 >nul
echo ========================================
echo 🧪 直接指定 Python 路径运行测试
echo ========================================
echo.

REM 直接使用已知的 Python 路径
set "PYTHON=C:\Users\openclaw-windows-2\AppData\Local\Microsoft\WindowsApps\python.exe"

echo Python 路径: %PYTHON%
echo.

if not exist "%PYTHON%" (
    echo ❌ Python 不存在于该路径
echo 请手动修改此脚本中的 PYTHON 变量为你的 Python 路径
    pause
    exit /b 1
)

echo [1/3] 检查 Python...
"%PYTHON%" --version
echo ✅ Python 正常
echo.

echo [2/3] 安装依赖...
"%PYTHON%" -m pip install -q pytest numpy pynput pillow opencv-python-headless 2>nul
echo ✅ 依赖安装完成
echo.

echo [3/3] 运行快速测试...
"%PYTHON%" quick_test.py
echo.

pause
