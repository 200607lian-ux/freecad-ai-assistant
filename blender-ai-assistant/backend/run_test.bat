@echo off
echo ========================================
echo Blender 客户端通信模块测试
echo 毕业设计项目 - 测试脚本
echo ========================================
echo.

REM 检查 Python 环境
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo 请确保：
echo   1. Blender 已启动
echo   2. Blender MCP 插件已启用
echo   3. 在 Blender 中点击了「启动 MCP 服务器」
echo   4. MCP 服务器端口为 9876
echo.

echo 选择测试模式：
echo   1. 快速测试 (--quick)
echo   2. 完整测试 (--full)
echo.

set /p choice="请输入选项 (1-2, 默认 1): "

if "%choice%"=="2" (
    echo.
    echo 正在运行完整测试套件...
    echo.
    python test_client.py --full
) else (
    echo.
    echo 正在运行快速测试...
    echo.
    python test_client.py --quick
)

echo.
echo 测试完成。
echo 按任意键退出...
pause >nul