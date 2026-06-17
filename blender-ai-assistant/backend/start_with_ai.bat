@echo off
REM Blender AI 助手启动脚本（启用 AI）
REM 自动设置环境变量并启动服务器

title Blender AI 助手服务器

echo ========================================
echo   Blender AI 助手服务器启动
echo ========================================
echo.

REM 刷新环境变量
echo [1/3] 刷新环境变量...
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v DASHSCOPE_API_KEY 2^>nul') do set DASHSCOPE_API_KEY=%%b

if defined DASHSCOPE_API_KEY (
    echo   ^|____ DASHSCOPE_API_KEY: %DASHSCOPE_API_KEY:~0,20%...
    echo   ^|____ AI 模式: 已启用
) else (
    echo   ^|____ DASHSCOPE_API_KEY: 未设置
    echo   ^|____ AI 模式: 规则引擎（降级）
    echo.
    echo   提示：要启用完整 AI 功能，请设置环境变量
    echo   运行：setx DASHSCOPE_API_KEY "sk-your-key"
)
echo.

REM 检查 Python
echo [2/3] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo   ^|____ Python 未安装或不在 PATH 中
    echo   ^|____ 请安装 Python 3.10+
    pause
    exit /b 1
)
python --version
echo.

REM 启动服务器
echo [3/3] 启动服务器...
echo ========================================
echo.
python main.py

REM 如果服务器退出
echo.
echo ========================================
echo 服务器已停止
echo ========================================
pause
