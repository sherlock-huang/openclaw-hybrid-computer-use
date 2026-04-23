@echo off
chcp 65001 >nul
echo ========================================
echo 🧪 运行所有测试
echo ========================================
echo.

REM 尝试多种方式找到 Python
set "PYTHON_CMD="

REM 方法1: 直接尝试 python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
    goto :python_found
)

REM 方法2: 尝试 python3
python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python3"
    goto :python_found
)

REM 方法3: 尝试 py
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py"
    goto :python_found
)

REM 方法4: 尝试常见路径
if exist "C:\Users\openclaw-windows-2\AppData\Local\Microsoft\WindowsApps\python.exe" (
    set "PYTHON_CMD=C:\Users\openclaw-windows-2\AppData\Local\Microsoft\WindowsApps\python.exe"
    goto :python_found
)

REM 方法5: 尝试 where 命令
for /f "tokens=*" %%a in ('where python 2^>nul') do (
    set "PYTHON_CMD=%%a"
    goto :python_found
)

echo ❌ 找不到 Python！
echo.
echo 💡 解决方法：
echo 1. 确保 Python 已安装
echo 2. 手动指定 Python 路径运行：
echo    C:\Users\openclaw-windows-2\AppData\Local\Microsoft\WindowsApps\python.exe quick_test.py
pause
exit /b 1

:python_found
echo [1/4] 检查 Python...
%PYTHON_CMD% --version
echo ✅ Python 路径: %PYTHON_CMD%
echo.

echo [2/4] 安装依赖...
%PYTHON_CMD% -m pip install -q pytest numpy pynput 2>nul
echo ✅ 依赖安装完成
echo.

echo [3/4] 运行快速测试...
%PYTHON_CMD% quick_test.py
if %errorlevel% neq 0 (
    echo ❌ 快速测试失败
    pause
    exit /b 1
)
echo.

echo [4/4] 运行单元测试...
%PYTHON_CMD% -m pytest tests/test_recorder.py -v --tb=short
if %errorlevel% neq 0 (
    echo ❌ 单元测试失败
    pause
    exit /b 1
)
echo.

echo ========================================
echo 🎉 所有测试通过!
echo ========================================
echo.
echo 💡 现在可以运行录制功能:
echo    %PYTHON_CMD% -m src record
pause
