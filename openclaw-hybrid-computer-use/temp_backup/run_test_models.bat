@echo off
chcp 65001 >nul
echo ========================================
echo 🧪 测试录制功能数据模型
echo ========================================
echo.

set "PYTHON=C:\Users\openclaw-windows-2\AppData\Local\Programs\Python\Python312\python.exe"

echo 使用 Python: %PYTHON%
echo.

"%PYTHON%" test_models_only.py

echo.
pause
