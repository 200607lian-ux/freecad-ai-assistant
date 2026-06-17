"""
FreeCAD Socket 通信模块
独立版本 - 通过 TCP Socket 与 FreeCAD 通信
作者：FreeCAD AI 助手项目
日期：2024年1月

作用：负责与 FreeCAD Socket 服务器通信，执行建模命令并导出 STEP 格式。
核心功能：连接 FreeCAD，发送 Python 代码执行，获取建模结果。

使用前提：
1. 在 FreeCAD 中运行宏: freecad_socket_server.FCMacro
2. 确保服务器监听在 127.0.0.1:9877
"""

import base64
import tempfile
import os
import time
import json
from typing import Dict, Any, Optional

class FreeCADClient:
    """
    FreeCAD 通信客户端
    
    通过 Kiro 的 MCP 工具与 FreeCAD 通信，执行建模代码并导出模型。
    替代原 Blender 客户端，支持 STEP、IGES 等 CAD 格式。
    """
    
    def __init__(self):
        """初始化 FreeCAD 客户端"""
        self.connected = False
        self.last_error = None
        self.timeout = 30
        self.host = '127.0.0.1'
        self.port = 9877
        
        print("FreeCAD Socket 客户端初始化完成")
        print(f"目标地址: {self.host}:{self.port}")
        print("提示：请确保在 FreeCAD 中运行 freecad_socket_server.FCMacro")
    
    def connect(self) -> bool:
        """
        测试 FreeCAD Socket 连接
        
        Returns:
            bool: 连接是否正常
        """
        try:
            print(f"正在测试 FreeCAD Socket 连接...")
            
            # 发送 ping 命令测试
            command = {"type": "ping", "params": {}}
            response = self._send_command(command)
            
            if response and response.get("status") == "ok":
                self.connected = True
                print(f"✓ 已连接到 FreeCAD Socket 服务器")
                print(f"   地址: {self.host}:{self.port}")
                
                # 获取 FreeCAD 版本信息
                test_code = "import FreeCAD; print(f'FreeCAD {FreeCAD.Version()}')"
                result = self.execute_code(test_code)
                if result:
                    print(f"   版本: {result.strip()}")
                
                return True
            else:
                self.last_error = "连接测试失败"
                print(f"✗ {self.last_error}")
                return False
                
        except Exception as e:
            self.last_error = f"连接失败: {e}"
            print(f"✗ {self.last_error}")
            print("\n请确保：")
            print("  1. FreeCAD 已启动")
            print("  2. 在 FreeCAD 中执行宏: freecad_socket_server.FCMacro")
            print("  3. 服务器正在监听 127.0.0.1:9877")
            return False
    
    def execute_code(self, code: str) -> Optional[str]:
        """
        执行 FreeCAD Python 代码（核心功能）- Socket 版本
        
        Args:
            code: 要执行的 FreeCAD Python 代码
            
        Returns:
            Optional[str]: 执行结果，失败返回 None
        """
        if not code or not code.strip():
            print("✗ 代码为空")
            return None
        
        try:
            print(f"执行 FreeCAD 代码 ({len(code)} 字符)...")
            
            # 通过 Socket 发送命令
            command = {
                "type": "execute_code",
                "params": {
                    "code": code
                }
            }
            
            response = self._send_command(command)
            
            if response and response.get("status") == "ok":
                result = response.get("result", {})
                output = result.get("output", "")
                print(f"✓ 执行成功")
                if output:
                    print(f"输出: {output[:200]}...")
                return output or "执行成功"
            else:
                error = response.get("result", {}).get("error", "未知错误") if response else "连接失败"
                print(f"✗ 执行失败: {error}")
                self.last_error = error
                return None
                
        except Exception as e:
            error_msg = f"代码执行失败: {e}"
            print(f"✗ {error_msg}")
            self.last_error = error_msg
            return None
    
    def _send_command(self, command: dict) -> Optional[dict]:
        """
        通过 Socket 发送命令到 FreeCAD
        
        协议：先发送4字节长度（大端序），再发送JSON数据
        
        Args:
            command: 命令字典
            
        Returns:
            Optional[dict]: 响应字典，失败返回 None
        """
        import socket
        import struct
        
        sock = None
        try:
            # 创建 Socket 连接
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect(('127.0.0.1', 9877))
            
            # 发送命令（带长度前缀）
            command_json = json.dumps(command, ensure_ascii=False)
            command_bytes = command_json.encode('utf-8')
            # 先发送4字节长度（大端序无符号整数）
            sock.sendall(struct.pack('>I', len(command_bytes)))
            # 再发送实际数据
            sock.sendall(command_bytes)
            
            # 接收响应长度（4字节）
            length_bytes = self._recv_all(sock, 4)
            if not length_bytes:
                print("✗ 接收响应长度失败")
                return None
            
            response_length = struct.unpack('>I', length_bytes)[0]
            
            # 接收响应数据
            response_bytes = self._recv_all(sock, response_length)
            if not response_bytes:
                print("✗ 接收响应数据失败")
                return None
            
            response = json.loads(response_bytes.decode('utf-8'))
            return response
            
        except socket.timeout:
            print(f"✗ Socket 超时（{self.timeout}秒）")
            return None
        except ConnectionRefusedError:
            print("✗ 连接被拒绝，请确保 FreeCAD Socket 服务器正在运行")
            print("   在 FreeCAD 中执行宏: freecad_socket_server.FCMacro")
            return None
        except Exception as e:
            print(f"✗ Socket 通信失败: {e}")
            return None
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass
    
    def _recv_all(self, sock, n):
        """精确接收 n 字节数据"""
        data = b''
        while len(data) < n:
            chunk = sock.recv(n - len(data))
            if not chunk:
                return None
            data += chunk
        return data
    
    def get_scene_info(self) -> Optional[Dict[str, Any]]:
        """
        获取当前文档信息
        
        Returns:
            Optional[Dict]: 文档信息，包含对象列表等
        """
        code = """
import FreeCAD

doc = FreeCAD.ActiveDocument
if doc:
    print(f"文档名称: {doc.Name}")
    print(f"对象数量: {len(doc.Objects)}")
    print("\\n对象列表:")
    for obj in doc.Objects:
        print(f"  - {obj.Label} ({obj.TypeId})")
else:
    print("没有活动文档")
"""
        
        result = self.execute_code(code)
        
        if result:
            # 解析结果
            object_count = 0
            if "对象数量:" in result:
                try:
                    count_line = [line for line in result.split('\n') if "对象数量:" in line][0]
                    object_count = int(count_line.split(":")[-1].strip())
                except:
                    pass
            
            print(f"场景信息获取成功")
            print(f"对象数量: {object_count}")
            
            return {
                "object_count": object_count,
                "result": result,
                "active_document": "FreeCAD Document"
            }
        
        return None
    
    def export_step(self, filepath: Optional[str] = None, selection_only: bool = False) -> Optional[str]:
        """
        导出场景为 STEP 文件（Base64 编码）
        
        Args:
            filepath: STEP 文件路径（如果为 None，使用临时文件）
            selection_only: 是否只导出选中的对象
            
        Returns:
            Optional[str]: Base64 编码的 STEP 数据，失败返回 None
        """
        if filepath is None:
            filepath = os.path.join(tempfile.gettempdir(), f"freecad_export_{int(time.time())}.step")
        
        print(f"正在导出 STEP 到: {filepath}")
        
        # 规范化路径（Windows 路径处理）
        filepath = filepath.replace('\\', '/')
        
        export_code = f"""
import FreeCAD
import Import

doc = FreeCAD.ActiveDocument
if not doc or not doc.Objects:
    print("ERROR: 文档中没有对象可导出")
    raise Exception("文档中没有对象可导出")

# 导出所有对象为 STEP
filepath = r"{filepath}"
Import.export(doc.Objects, filepath)

import os
if os.path.exists(filepath):
    file_size = os.path.getsize(filepath)
    print(f"✓ STEP 导出成功: {{filepath}}")
    print(f"  文件大小: {{file_size}} 字节")
else:
    print("✗ STEP 导出失败")
"""
        
        result = self.execute_code(export_code)
        
        if result and "✓ STEP 导出成功" in result:
            try:
                # 读取文件并编码
                with open(filepath, 'rb') as f:
                    file_data = f.read()
                
                # 清理临时文件
                try:
                    os.remove(filepath)
                except:
                    pass
                
                base64_data = base64.b64encode(file_data).decode('utf-8')
                print(f"✓ STEP 导出成功，大小: {len(file_data)} 字节 ({len(base64_data)} 字符 Base64)")
                return base64_data
                
            except Exception as e:
                print(f"✗ 读取 STEP 文件失败: {e}")
                return None
        else:
            print(f"✗ STEP 导出失败")
            return None
    
    def export_stl(self, filepath: Optional[str] = None, selection_only: bool = False) -> Optional[str]:
        """
        导出场景为 STL 文件（Base64 编码）
        用于 3D 预览（Three.js 支持）
        
        Args:
            filepath: STL 文件路径（如果为 None，使用临时文件）
            selection_only: 是否只导出选中的对象
            
        Returns:
            Optional[str]: Base64 编码的 STL 数据，失败返回 None
        """
        if filepath is None:
            filepath = os.path.join(tempfile.gettempdir(), f"freecad_preview_{int(time.time())}.stl")
        
        print(f"正在导出 STL 预览到: {filepath}")
        
        # 规范化路径
        filepath = filepath.replace('\\', '/')
        
        export_code = f"""
import FreeCAD
import Mesh
import os

doc = FreeCAD.ActiveDocument
if not doc or not doc.Objects:
    print("ERROR: 文档中没有对象可导出")
    raise Exception("文档中没有对象可导出")

# 获取所有对象的形状
shapes = []
for obj in doc.Objects:
    if hasattr(obj, 'Shape') and obj.Shape:
        shapes.append(obj.Shape)

if not shapes:
    print("ERROR: 没有有效的形状对象")
    raise Exception("没有有效的形状对象")

# 合并所有形状
import Part
if len(shapes) > 1:
    compound = Part.makeCompound(shapes)
else:
    compound = shapes[0]

# 导出为 STL
filepath = r"{filepath}"
Mesh.export([doc.Objects[0]], filepath)

if os.path.exists(filepath):
    file_size = os.path.getsize(filepath)
    print(f"✓ STL 导出成功: {{filepath}}")
    print(f"  文件大小: {{file_size}} 字节")
else:
    print("✗ STL 导出失败")
"""
        
        result = self.execute_code(export_code)
        
        if result and "✓ STL 导出成功" in result:
            try:
                # 读取文件并编码
                with open(filepath, 'rb') as f:
                    file_data = f.read()
                
                # 清理临时文件
                try:
                    os.remove(filepath)
                except:
                    pass
                
                base64_data = base64.b64encode(file_data).decode('utf-8')
                print(f"✓ STL 导出成功，大小: {len(file_data)} 字节")
                return base64_data
                
            except Exception as e:
                print(f"✗ 读取 STL 文件失败: {e}")
                return None
        else:
            print(f"✗ STL 导出失败")
            return None
    
    def export_model(self, format_type: str = 'step', filepath: Optional[str] = None, 
                    selection_only: bool = False) -> Optional[str]:
        """
        导出场景为指定格式的模型文件（Base64 编码）
        
        支持的格式：
        - step/stp: STEP 格式（CAD 标准）
        - iges/igs: IGES 格式（CAD 交换）
        - stl: STL 格式（3D 打印）
        - obj: Wavefront OBJ 格式
        - brep: OpenCASCADE BREP 格式
        
        Args:
            format_type: 导出格式
            filepath: 文件路径（如果为 None，使用临时文件）
            selection_only: 是否只导出选中的对象
            
        Returns:
            Optional[str]: Base64 编码的模型数据，失败返回 None
        """
        format_type = format_type.lower()
        
        # 格式映射
        format_map = {
            'step': self.export_step,
            'stp': self.export_step,
            'iges': self._export_iges,
            'igs': self._export_iges,
            'stl': self.export_stl,
            'obj': self._export_obj,
            'brep': self._export_brep
        }
        
        if format_type not in format_map:
            print(f"✗ 不支持的格式: {format_type}")
            print(f"  支持的格式: {', '.join(format_map.keys())}")
            return None
        
        return format_map[format_type](filepath, selection_only)
    
    def _export_iges(self, filepath: Optional[str] = None, selection_only: bool = False) -> Optional[str]:
        """导出 IGES 格式"""
        if filepath is None:
            filepath = os.path.join(tempfile.gettempdir(), f"freecad_export_{int(time.time())}.iges")
        
        filepath = filepath.replace('\\', '/')
        
        export_code = f"""
import FreeCAD
import Import

doc = FreeCAD.ActiveDocument
if not doc or not doc.Objects:
    raise Exception("文档中没有对象")

filepath = r"{filepath}"
Import.export(doc.Objects, filepath)
print(f"✓ IGES 导出成功: {{filepath}}")
"""
        
        result = self.execute_code(export_code)
        
        if result and "✓ IGES 导出成功" in result:
            try:
                with open(filepath, 'rb') as f:
                    file_data = f.read()
                os.remove(filepath)
                return base64.b64encode(file_data).decode('utf-8')
            except Exception as e:
                print(f"✗ 读取 IGES 文件失败: {e}")
                return None
        return None
    
    def _export_obj(self, filepath: Optional[str] = None, selection_only: bool = False) -> Optional[str]:
        """导出 OBJ 格式"""
        if filepath is None:
            filepath = os.path.join(tempfile.gettempdir(), f"freecad_export_{int(time.time())}.obj")
        
        filepath = filepath.replace('\\', '/')
        
        export_code = f"""
import FreeCAD
import Mesh

doc = FreeCAD.ActiveDocument
if not doc or not doc.Objects:
    raise Exception("文档中没有对象")

filepath = r"{filepath}"
Mesh.export(doc.Objects, filepath)
print(f"✓ OBJ 导出成功: {{filepath}}")
"""
        
        result = self.execute_code(export_code)
        
        if result and "✓ OBJ 导出成功" in result:
            try:
                with open(filepath, 'rb') as f:
                    file_data = f.read()
                os.remove(filepath)
                return base64.b64encode(file_data).decode('utf-8')
            except Exception as e:
                print(f"✗ 读取 OBJ 文件失败: {e}")
                return None
        return None
    
    def _export_brep(self, filepath: Optional[str] = None, selection_only: bool = False) -> Optional[str]:
        """导出 BREP 格式"""
        if filepath is None:
            filepath = os.path.join(tempfile.gettempdir(), f"freecad_export_{int(time.time())}.brep")
        
        filepath = filepath.replace('\\', '/')
        
        export_code = f"""
import FreeCAD
import Part

doc = FreeCAD.ActiveDocument
if not doc or not doc.Objects:
    raise Exception("文档中没有对象")

# 获取所有形状
shapes = [obj.Shape for obj in doc.Objects if hasattr(obj, 'Shape')]
if shapes:
    compound = Part.makeCompound(shapes)
    filepath = r"{filepath}"
    compound.exportBrep(filepath)
    print(f"✓ BREP 导出成功: {{filepath}}")
else:
    raise Exception("没有有效的形状")
"""
        
        result = self.execute_code(export_code)
        
        if result and "✓ BREP 导出成功" in result:
            try:
                with open(filepath, 'rb') as f:
                    file_data = f.read()
                os.remove(filepath)
                return base64.b64encode(file_data).decode('utf-8')
            except Exception as e:
                print(f"✗ 读取 BREP 文件失败: {e}")
                return None
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取连接状态信息
        
        Returns:
            Dict: 状态信息
        """
        return {
            "connected": self.connected,
            "type": "FreeCAD MCP",
            "last_error": self.last_error,
            "timestamp": time.time()
        }
    
    def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            bool: 连接是否健康
        """
        try:
            result = self.execute_code("import FreeCAD; print('OK')")
            return result is not None and "OK" in result
        except:
            return False
    
    def close(self):
        """关闭连接"""
        print("FreeCAD 客户端关闭")
        self.connected = False


# 使用示例
if __name__ == "__main__":
    print("=" * 50)
    print("FreeCAD MCP 客户端测试")
    print("=" * 50)
    
    # 创建客户端实例
    client = FreeCADClient()
    
    # 测试连接
    if client.connect():
        print("\n✓ 连接测试成功")
        
        # 获取状态
        status = client.get_status()
        print(f"状态: {status}")
        
        # 测试场景信息获取
        scene_info = client.get_scene_info()
        if scene_info:
            print(f"文档对象数量: {scene_info.get('object_count', 0)}")
        
        # 测试代码执行
        test_code = """
import FreeCAD
import Part

doc = FreeCAD.ActiveDocument
if not doc:
    doc = FreeCAD.newDocument("TestDoc")

# 创建一个立方体
box = Part.makeBox(10, 10, 10)
obj = doc.addObject("Part::Feature", "Box")
obj.Shape = box
doc.recompute()

print(f"✓ 测试成功，创建了对象: {obj.Label}")
"""
        result = client.execute_code(test_code)
        print(f"代码执行结果:\n{result}")
        
        # 关闭连接
        client.close()
    else:
        print("\n✗ 连接测试失败")
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
