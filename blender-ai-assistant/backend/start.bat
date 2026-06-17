@echo off
echo ========================================
echo Blender AI Assistant 后端服务启动
echo ========================================
echo.

REM 检查 Python 环境
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 检查虚拟环境
if exist ".venv\" (
    echo 激活虚拟环境...
    call .venv\Scripts\activate
) else (
    echo 创建虚拟环境...
    python -m venv .venv
    echo 激活虚拟环境...
    call .venv\Scripts\activate
    
    echo 安装依赖包...
    pip install --upgrade pip
    pip install -r requirements.txt
)

echo.
echo 检查依赖...
pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo 安装依赖失败...
    pip install -r requirements.txt
)

echo.
echo 启动后端服务...
echo 服务地址: http://localhost:8000
echo WebSocket: ws://localhost:8000/ws
echo.

REM 启动 FastAPI 服务
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

REM 如果服务退出
echo.
echo 服务已停止。
pause