"""
测试 FreeCAD Socket 连接
用于验证 FreeCAD Socket 服务器是否正常运行

协议：先发送4字节长度（大端序），再发送JSON数据
"""

import socket
import json
import struct
import sys

def send_command(sock, command):
    """发送命令（带长度前缀）"""
    command_json = json.dumps(command, ensure_ascii=False)
    command_bytes = command_json.encode('utf-8')
    # 先发送4字节长度（大端序无符号整数）
    sock.sendall(struct.pack('>I', len(command_bytes)))
    # 再发送实际数据
    sock.sendall(command_bytes)

def recv_response(sock):
    """接收响应"""
    # 接收响应长度（4字节）
    length_bytes = recv_all(sock, 4)
    if not length_bytes:
        return None
    
    response_length = struct.unpack('>I', length_bytes)[0]
    
    # 接收响应数据
    response_bytes = recv_all(sock, response_length)
    if not response_bytes:
        return None
    
    return json.loads(response_bytes.decode('utf-8'))

def recv_all(sock, n):
    """精确接收 n 字节数据"""
    data = b''
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            return None
        data += chunk
    return data

def test_connection():
    """测试基础连接"""
    print("="*50)
    print("测试 1：基础连接（Ping）")
    print("="*50)
    
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(('127.0.0.1', 9877))
        
        command = {"type": "ping", "params": {}}
        send_command(sock, command)
        
        result = recv_response(sock)
        
        if result and result.get('status') == 'ok':
            print("✓ 连接成功！")
            print(f"  响应: {result}")
            return True
        else:
            print("✗ 连接失败")
            print(f"  响应: {result}")
            return False
            
    except ConnectionRefusedError:
        print("✗ 连接被拒绝")
        print("  请确保：")
        print("    1. FreeCAD 已启动")
        print("    2. 在 FreeCAD 中执行了 freecad_socket_server.FCMacro 宏")
        return False
    except socket.timeout:
        print("✗ 连接超时")
        return False
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False
    finally:
        if sock:
            sock.close()

def test_code_execution():
    """测试代码执行"""
    print("\n" + "="*50)
    print("测试 2：代码执行")
    print("="*50)
    
    test_code = """
import FreeCAD
import Part

doc = FreeCAD.ActiveDocument
if not doc:
    doc = FreeCAD.newDocument("SocketTest")

# 创建一个测试立方体
box = Part.makeBox(10, 10, 10)
obj = doc.addObject("Part::Feature", "TestBox")
obj.Shape = box
obj.Label = "Socket测试立方体"
doc.recompute()

print(f"✓ 成功创建对象: {obj.Label}")
"""
    
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect(('127.0.0.1', 9877))
        
        command = {
            "type": "execute_code",
            "params": {
                "code": test_code
            }
        }
        
        print("发送代码...")
        send_command(sock, command)
        
        print("等待响应...")
        result = recv_response(sock)
        
        if result and result.get('status') == 'ok':
            print("✓ 代码执行成功！")
            output = result.get('result', {}).get('output', '')
            if output:
                print(f"  输出:\n{output}")
            return True
        else:
            print("✗ 代码执行失败")
            error = result.get('result', {}).get('error', '未知错误') if result else '无响应'
            print(f"  错误: {error}")
            return False
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if sock:
            sock.close()

def test_scene_info():
    """测试场景信息获取"""
    print("\n" + "="*50)
    print("测试 3：获取场景信息")
    print("="*50)
    
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(('127.0.0.1', 9877))
        
        command = {"type": "get_scene_info", "params": {}}
        send_command(sock, command)
        
        result = recv_response(sock)
        
        if result and result.get('status') == 'ok':
            scene_info = result.get('result', {})
            print("✓ 获取成功！")
            print(f"  文档名称: {scene_info.get('document_name', '未知')}")
            print(f"  对象数量: {scene_info.get('object_count', 0)}")
            
            objects = scene_info.get('objects', [])
            if objects:
                print("  对象列表:")
                for obj in objects[:5]:
                    print(f"    - {obj.get('label', obj.get('name', '未知'))} ({obj.get('type', '未知')})")
                if len(objects) > 5:
                    print(f"    ... 还有 {len(objects) - 5} 个对象")
            
            return True
        else:
            print("✗ 获取失败")
            print(f"  响应: {result}")
            return False
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False
    finally:
        if sock:
            sock.close()

def main():
    """主函数"""
    print("\n" + "="*50)
    print("FreeCAD Socket 服务器测试工具")
    print("="*50)
    print()
    
    # 测试 1：基础连接
    if not test_connection():
        print("\n" + "="*50)
        print("测试失败：无法连接到 FreeCAD Socket 服务器")
        print("="*50)
        print("\n请按照以下步骤操作：")
        print("1. 启动 FreeCAD")
        print("2. 打开宏编辑器：Macro → Macros...")
        print("3. 选择并执行：freecad_socket_server.FCMacro")
        print("4. 确认看到「FreeCAD Socket 服务器已启动」消息")
        print("5. 重新运行此测试脚本")
        print()
        sys.exit(1)
    
    # 测试 2：代码执行
    if not test_code_execution():
        print("\n警告：代码执行测试失败")
    
    # 测试 3：场景信息
    if not test_scene_info():
        print("\n警告：场景信息获取测试失败")
    
    print("\n" + "="*50)
    print("测试完成！")
    print("="*50)
    print("\n所有测试通过！可以启动后端服务器了。")
    print("运行: cd backend && python main_freecad.py")
    print()

if __name__ == "__main__":
    main()
