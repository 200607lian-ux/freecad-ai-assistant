@echo off
chcp 65001 >nul 2>&1
echo ==========================================
echo FreeCAD AI Assistant - Smart Launcher
echo ==========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Python not found
    pause
    exit /b 1
)

:: 查找并终止占用 8001 端口的 Python 进程
echo [1/3] Checking port 8001...

:: 使用 PowerShell 查找占用端口的进程并终止
powershell -Command "
    $conn = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue
    if ($conn) {
        $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host \"[WARN] Port 8001 is occupied by: $($proc.ProcessName) (PID: $($proc.Id))\"
            Write-Host \"        Stopping process...\"
            Stop-Process -Id $proc.Id -Force
            Write-Host \"[OK] Process stopped\"
            Start-Sleep -Seconds 2
        }
    } else {
        Write-Host \"[OK] Port 8001 is available\"
    }
"

:: 检查端口是否仍然被占用
echo.
echo [2/3] Verifying port availability...
python -c "
import socket
import sys

for port in [8001, 8002, 8003, 8004, 8005]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', port))
        s.close()
        print(f'[OK] Using port: {port}')
        with open('.port.tmp', 'w') as f:
            f.write(str(port))
        break
    except:
        continue
else:
    print('[FAIL] No available port found')
    sys.exit(1)
"

if errorlevel 1 (
    echo [FAIL] No available port
    pause
    exit /b 1
)

:: 读取端口
set /p PORT=<.port.tmp
del .port.tmp 2>nul

echo.
echo [3/3] Starting server...
echo ==========================================
echo Server: http://localhost:%PORT%
echo WebSocket: ws://localhost:%PORT%/ws
echo ==========================================
echo.

:: 设置环境变量并启动
set FREECAD_AI_PORT=%PORT%
cd /d "%~dp0"
python backend\main_freecad_ai.py

pause
