@echo off
chcp 65001 >nul
echo ==========================================
echo FreeCAD AI 助手 - 启动脚本
echo ==========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请安装 Python 3.8+
    pause
    exit /b 1
)

REM 检查依赖
echo [1/3] 检查依赖...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [信息] 安装依赖...
    pip install fastapi uvicorn websockets openai pillow -i https://pypi.tuna.tsinghua.edu.cn/simple
)

REM 检查环境变量
echo [2/3] 检查环境变量...
if "%DASHSCOPE_API_KEY%"=="" (
    echo [警告] 未设置 DASHSCOPE_API_KEY 环境变量
    echo [警告] AI 功能将以规则引擎模式运行
    echo [提示] 设置方法: set DASHSCOPE_API_KEY=your_api_key
    echo.
) else (
    echo [OK] DASHSCOPE_API_KEY 已设置
)

REM 启动后端
echo [3/3] 启动后端服务...
echo.
echo 服务地址: http://localhost:8001
echo 按 Ctrl+C 停止服务
echo.

cd /d "%~dp0\backend"
python main_freecad_ai.py

pause
