"""
启动器脚本 - 处理端口占用问题
自动检测并释放端口，然后启动主服务器
"""
import os
import sys
import socket
import subprocess
import time
import signal

# 添加 backend 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def find_process_using_port(port):
    """查找占用端口的进程 PID"""
    try:
        # 使用 PowerShell 获取端口占用信息（更可靠）
        ps_cmd = f"""
        $conn = Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue
        if ($conn) {{
            $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
            if ($proc) {{
                Write-Output "PID=$($proc.Id)"
                Write-Output "NAME=$($proc.ProcessName)"
            }}
        }}
        """
        result = subprocess.run(
            ['powershell', '-Command', ps_cmd],
            capture_output=True,
            text=True,
            shell=True
        )
        
        pid = None
        name = None
        for line in result.stdout.strip().split('\n'):
            if line.startswith('PID='):
                pid = int(line.split('=')[1])
            elif line.startswith('NAME='):
                name = line.split('=')[1]
        
        return pid, name
    except Exception as e:
        print(f"[WARN] 查找端口占用进程失败: {e}")
    return None, None

def kill_process_by_pid(pid):
    """终止指定 PID 的进程"""
    try:
        # 强制终止
        subprocess.run(
            ['taskkill', '/F', '/PID', str(pid)],
            capture_output=True,
            shell=True
        )
        print(f"[OK] 已终止进程 PID: {pid}")
        return True
    except Exception as e:
        print(f"[FAIL] 终止进程失败: {e}")
        return False

def is_port_available(port):
    """检查端口是否可用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.settimeout(1)
            result = s.connect_ex(('0.0.0.0', port))
            return result != 0  # 0 表示端口被占用
    except:
        return False

def wait_for_port_release(port, timeout=10):
    """等待端口释放"""
    for i in range(timeout):
        if is_port_available(port):
            return True
        time.sleep(1)
        print(f"  等待端口释放... {i+1}/{timeout}")
    return False

def find_available_port(start_port, max_attempts=10):
    """查找可用端口"""
    for port in range(start_port, start_port + max_attempts):
        if is_port_available(port):
            return port
    return None

def main():
    DEFAULT_PORT = 8001
    port = DEFAULT_PORT
    
    print("\n" + "="*60)
    print("FreeCAD AI 助手 - 启动器")
    print("="*60)
    
    print(f"\n[1/3] 检查端口 {port}...")
    
    if not is_port_available(port):
        print(f"[WARN] 端口 {port} 已被占用")
        
        # 查找占用进程
        pid, name = find_process_using_port(port)
        
        if pid:
            print(f"[2/3] 发现占用进程: {name} (PID: {pid})")
            print(f"        尝试释放端口...")
            
            if kill_process_by_pid(pid):
                # 等待端口释放
                if wait_for_port_release(port, timeout=10):
                    print(f"[OK] 端口 {port} 已释放")
                else:
                    print(f"[WARN] 端口仍被占用，尝试查找新端口...")
                    new_port = find_available_port(port + 1)
                    if new_port:
                        port = new_port
                        print(f"[OK] 使用新端口: {port}")
                    else:
                        print(f"[FAIL] 找不到可用端口")
                        sys.exit(1)
            else:
                # 无法终止，查找新端口
                new_port = find_available_port(port + 1)
                if new_port:
                    port = new_port
                    print(f"[OK] 使用新端口: {port}")
                else:
                    print(f"[FAIL] 找不到可用端口")
                    sys.exit(1)
        else:
            # 找不到进程，查找新端口
            print(f"[WARN] 找不到占用进程，尝试查找新端口...")
            new_port = find_available_port(port + 1)
            if new_port:
                port = new_port
                print(f"[OK] 使用新端口: {port}")
            else:
                print(f"[FAIL] 找不到可用端口")
                sys.exit(1)
    else:
        print(f"[OK] 端口 {port} 可用")
    
    print(f"\n[3/3] 启动服务器...")
    print(f"="*60)
    print(f"服务地址: http://localhost:{port}")
    print(f"WebSocket: ws://localhost:{port}/ws")
    print(f"="*60 + "\n")
    
    # 设置环境变量
    os.environ['FREECAD_AI_PORT'] = str(port)
    
    # 自动打开浏览器（在新线程中，避免阻塞）
    def open_browser():
        time.sleep(3)  # 等待服务器启动
        url = f"http://localhost:{port}"
        print(f"[INFO] 正在打开浏览器: {url}")
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception as e:
            print(f"[WARN] 无法自动打开浏览器: {e}")
            print(f"       请手动访问: {url}")
    
    import threading
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # 导入并启动主应用
    import uvicorn
    from backend.main_freecad_ai import app
    
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[OK] 服务器已停止")
        sys.exit(0)
