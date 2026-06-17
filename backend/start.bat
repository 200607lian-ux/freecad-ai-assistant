@echo off
echo ======================================
echo FreeCAD AI 助手 - 启动脚本
echo ======================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python 未安装或不在 PATH 中
    echo 请安装 Python 3.9 或更高版本
    pause
    exit /b 1
)

REM 检查 API Key
if not defined DASHSCOPE_API_KEY (
    echo [警告] 未设置 DASHSCOPE_API_KEY 环境变量
    echo AI 功能将使用规则引擎模式
    echo.
    echo 如需使用完整 AI 功能，请设置环境变量：
    echo set DASHSCOPE_API_KEY=your-api-key
    echo.
)

REM 安装依赖
echo [1/2] 检查依赖...
python -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

echo [2/2] 启动服务器...
echo.
echo ======================================
echo 服务已启动！
echo.
echo 前端地址: http://localhost:8001
echo WebSocket: ws://localhost:8001/ws
echo 健康检查: http://localhost:8001/health
echo ======================================
echo.
echo 按 Ctrl+C 停止服务
echo.

python main_freecad.py
pause
