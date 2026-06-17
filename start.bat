@echo off
echo ==========================================
echo FreeCAD AI Assistant Launcher
echo ==========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Python not found
    pause
    exit /b 1
)

:: 使用 launcher.py 启动（自动处理端口占用）
cd /d "%~dp0"
python launcher.py

pause
