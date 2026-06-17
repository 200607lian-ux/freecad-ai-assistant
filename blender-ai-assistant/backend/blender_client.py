"""
Blender MCP 通信模块
毕业设计项目：通过自然语言对话控制 Blender 3D 建模
作者：[你的名字]
日期：2024年1月

作用：负责与 Blender MCP 插件通信，发送命令并接收结果。
核心功能：连接 Blender，发送 Python 代码执行，获取建模结果。
"""

import socket
import json
import base64
import tempfile
import os
import time
from typing import Dict, Any, Optional, Union

class BlenderClient:
    """
    Blender 通信客户端
    
    负责与 Blender MCP 插件建立 TCP 连接，发送命令并接收结果。
    这是毕业设计项目的核心通信模块。
    """
    
    def __init__(self, host='localhost', port=9876):
        """
        初始化 Blender 客户端
        
        Args:
            host: Blender MCP 服务器主机地址（默认 localhost）
            port: Blender MCP 服务器端口（默认 9876）
        """
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.last_error = None
        self.timeout = 30  # 默认超时时间（秒）
        
    def connect(self) -> bool:
        """
        连接到 Blender MCP 插件
        
        Returns:
            bool: 连接是否成功
            
        注意：需要确保：
        1. Blender 已启动
        2. Blender MCP 插件已启用
        3. 在 Blender 中点击了「启动 MCP 服务器」
        """
        try:
            print(f"正在连接 Blender MCP 服务器 ({self.host}:{self.port})...")
            
            # 创建 TCP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)  # 连接超时10秒
            
            # 连接服务器
            self.socket.connect((self.host, self.port))
            self.connected = True
            
            # 设置接收超时
            self.socket.settimeout(self.timeout)
            
            print(f"✓ 已连接到 Blender (端口 {self.port})")
            print("连接状态：就绪")
            
            return True
            
        except socket.timeout:
            self.last_error = "连接超时：请检查 Blender 是否启动且 MCP 插件是否运行"
            print(f"✗ {self.last_error}")
            return False
            
        except ConnectionRefusedError:
            self.last_error = "连接被拒绝：请确保 Blender MCP 服务器正在运行"
            print(f"✗ {self.last_error}")
            return False
            
        except Exception as e:
            self.last_error = f"连接失败: {e}"
            print(f"✗ {self.last_error}")
            print("\n请确保：")
            print("  1. Blender 已启动")
            print("  2. Blender MCP 插件已启用")
            print("  3. 在 Blender 中点击了「启动 MCP 服务器」")
            print("  4. MCP 服务器端口配置正确（默认 9876）")
            return False
    
    def send_command(self, cmd_type: str, params: Dict[str, Any] = None, retry_count: int = 2) -> Optional[Dict[str, Any]]:
        """
        发送命令到 Blender MCP 服务器（带重试机制）
        
        Args:
            cmd_type: 命令类型（如 "execute_code", "get_scene_info"）
            params: 命令参数
            retry_count: 失败后重试次数
            
        Returns:
            Optional[Dict]: 服务器响应结果，失败返回 None
        """
        # 检查连接
        if not self.socket or not self.connected:
            if not self.connect():
                print("✗ 无法连接到服务器")
                return None
        
        command = {
            "type": cmd_type,
            "params": params or {},
            "timestamp": time.time()
        }
        
        attempt = 0
        while attempt <= retry_count:
            try:
                # 发送命令（原始插件不发送换行符）
                command_json = json.dumps(command, ensure_ascii=False)
                print(f"发送命令 JSON (尝试 {attempt + 1}/{retry_count + 1}): {command_json[:100]}...")  # 只显示前100字符
                
                # 注意：原始插件使用 client.sendall() 而不是 client.send()
                self.socket.sendall(command_json.encode('utf-8'))
                
                print(f"✓ 命令已发送: {cmd_type}")
                if params:
                    print(f"  参数: {params}")
                
                # 接收响应（增加超时时间，因为 Blender 可能需要在主线程执行）
                print("等待服务器响应...")
                response_data = self._receive_response(timeout=60.0)  # 增加到60秒
                
                if not response_data:
                    print("✗ 未收到响应数据")
                    self.last_error = "未收到响应数据"
                    
                    # 如果是最后一次尝试，返回失败
                    if attempt >= retry_count:
                        return None
                    
                    # 否则重连后重试
                    print("尝试重新连接...")
                    self.socket = None
                    self.connected = False
                    if not self.connect():
                        return None
                    attempt += 1
                    continue
                
                # 尝试解析响应
                try:
                    response_str = response_data.decode('utf-8', errors='ignore')
                    print(f"收到响应数据 ({len(response_str)} 字符): {response_str[:200]}...")
                    
                    response = json.loads(response_str)
                    
                    if response.get("status") == "error":
                        error_msg = response.get("message", "未知错误")
                        print(f"✗ Blender 错误: {error_msg}")
                        self.last_error = error_msg
                        return None
                    
                    print(f"✓ 命令执行成功: {cmd_type}")
                    return response.get("result", {})
                    
                except json.JSONDecodeError as e:
                    print(f"✗ 响应不是有效的 JSON")
                    print(f"  响应数据: {response_str[:500]}")
                    print(f"  解析错误: {e}")
                    self.last_error = f"响应解析失败: {e}"
                    return None
                
            except socket.timeout:
                self.last_error = "命令执行超时 (60秒)"
                print(f"✗ {self.last_error}")
                
                if attempt >= retry_count:
                    return None
                
                print("尝试重新连接...")
                self.socket = None
                self.connected = False
                if not self.connect():
                    return None
                attempt += 1
                continue
                
            except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError) as e:
                self.last_error = f"连接中断: {e}"
                print(f"✗ {self.last_error}")
                self.socket = None
                self.connected = False
                
                if attempt >= retry_count:
                    return None
                
                print(f"尝试重新连接 (尝试 {attempt + 1}/{retry_count + 1})...")
                time.sleep(1)  # 等待1秒后重连
                if not self.connect():
                    return None
                attempt += 1
                continue
                
            except Exception as e:
                self.last_error = f"命令执行失败: {e}"
                print(f"✗ {self.last_error}")
                import traceback
                traceback.print_exc()
                
                if attempt >= retry_count:
                    return None
                
                attempt += 1
                continue
        
        return None
    
    def _receive_response(self, timeout=30.0) -> Optional[bytes]:
        """
        接收完整的响应数据
        
        根据调试结果，服务器返回完整的 JSON 数据，没有换行符。
        使用简单可靠的接收方式。
        
        Args:
            timeout: 接收超时时间（秒）
            
        Returns:
            Optional[bytes]: 完整的响应数据，失败返回 None
        """
        if not self.socket:
            return None
        
        self.socket.settimeout(timeout)
        chunks = []
        
        try:
            start_time = time.time()
            
            while True:
                # 检查超时
                if time.time() - start_time > timeout:
                    print(f"✗ 接收超时 ({timeout} 秒)")
                    if chunks:
                        print(f"  已接收部分数据: {len(chunks)} 字节")
                    return None
                
                try:
                    # 接收数据
                    chunk = self.socket.recv(4096)
                    if chunk:
                        chunks.append(chunk)
                        
                        # 尝试解析 JSON
                        combined_data = b''.join(chunks)
                        try:
                            response = json.loads(combined_data.decode('utf-8', errors='ignore'))
                            # 解析成功，返回完整数据
                            print(f"✓ 收到完整响应 ({len(combined_data)} 字节)")
                            return combined_data
                        except json.JSONDecodeError:
                            # JSON 不完整，继续接收
                            continue
                    else:
                        # 没有数据了（连接关闭）
                        if chunks:
                            # 尝试使用已有的数据
                            combined_data = b''.join(chunks)
                            print(f"连接关闭，使用已接收数据 ({len(combined_data)} 字节)")
                            return combined_data
                        else:
                            print("✗ 连接被服务器关闭")
                            return None
                            
                except socket.timeout:
                    # 套接字超时，但继续尝试直到总超时
                    continue
                    
                except Exception as e:
                    print(f"✗ 接收数据时出错: {e}")
                    if chunks:
                        combined_data = b''.join(chunks)
                        print(f"使用已接收数据 ({len(combined_data)} 字节)")
                        return combined_data
                    return None
        
        except Exception as e:
            print(f"✗ 接收响应失败: {e}")
            if chunks:
                combined_data = b''.join(chunks)
                print(f"使用部分数据 ({len(combined_data)} 字节)")
                return combined_data
            return None
    
    def execute_code(self, code: str) -> Optional[str]:
        """
        执行 Blender Python 代码（核心功能）
        
        Args:
            code: 要执行的 Python 代码
            
        Returns:
            Optional[str]: 执行结果，失败返回 None
        """
        if not code or not code.strip():
            print("✗ 代码为空")
            return None
        
        result = self.send_command("execute_code", {"code": code})
        
        if result:
            execution_result = result.get("result", "")
            print(f"执行结果: {execution_result}")
            return execution_result
        
        return None
    
    def get_scene_info(self) -> Optional[Dict[str, Any]]:
        """
        获取当前场景信息
        
        Returns:
            Optional[Dict]: 场景信息，包含对象列表等
        """
        result = self.send_command("get_scene_info")
        
        if result:
            print(f"场景信息获取成功")
            print(f"对象数量: {result.get('object_count', 0)}")
            return result
        
        return None
    
    def get_screenshot(self, max_size: int = 800) -> Optional[str]:
        """
        获取 Blender 视口截图（Base64 编码）
        
        Args:
            max_size: 图片最大尺寸（像素）
            
        Returns:
            Optional[str]: Base64 编码的图片数据，失败返回 None
        """
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            result = self.send_command("get_viewport_screenshot", {
                "max_size": max_size,
                "filepath": tmp_path,
                "format": "png"
            })
            
            if result and os.path.exists(tmp_path):
                # 读取图片并转换为 Base64
                with open(tmp_path, 'rb') as f:
                    image_data = f.read()
                
                # 清理临时文件
                os.remove(tmp_path)
                
                if image_data:
                    base64_image = base64.b64encode(image_data).decode('utf-8')
                    print(f"✓ 截图成功，大小: {len(base64_image)} 字符")
                    return base64_image
                    
        except Exception as e:
            print(f"✗ 截图失败: {e}")
        
        # 清理临时文件（如果失败）
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except:
                pass
        
        return None
    
    def export_stl(self, filepath: Optional[str] = None, selection_only: bool = False) -> Optional[str]:
        """
        导出场景为 STL 文件（Base64 编码）
        
        Args:
            filepath: STL 文件路径（如果为 None，使用临时文件）
            selection_only: 是否只导出选中的对象
            
        Returns:
            Optional[str]: Base64 编码的 STL 数据，失败返回 None
        """
        return self.export_model('stl', filepath, selection_only)
    
    def export_model(self, format_type: str = 'stl', filepath: Optional[str] = None, selection_only: bool = False) -> Optional[str]:
        """
        导出场景为指定格式的模型文件（Base64 编码）
        
        支持的格式：
        - stl: STL 格式（3D 打印常用）
        - obj: Wavefront OBJ 格式（通用）
        - fbx: FBX 格式（游戏和动画）
        - gltf: glTF 2.0 格式（Web3D 标准）
        - glb: glTF 二进制格式
        - ply: Stanford PLY 格式
        - x3d: X3D 格式（Web3D）
        - dae: Collada DAE 格式
        - abc: Alembic 格式（影视）
        
        Args:
            format_type: 导出格式（stl, obj, fbx, gltf, glb, ply, x3d, dae, abc）
            filepath: 文件路径（如果为 None，使用临时文件）
            selection_only: 是否只导出选中的对象
            
        Returns:
            Optional[str]: Base64 编码的模型数据，失败返回 None
        """
        format_type = format_type.lower()
        
        # 支持的格式及其文件扩展名
        format_extensions = {
            'stl': '.stl',
            'obj': '.obj',
            'fbx': '.fbx',
            'gltf': '.gltf',
            'glb': '.glb',
            'ply': '.ply',
            'x3d': '.x3d',
            'dae': '.dae',
            'abc': '.abc'
        }
        
        if format_type not in format_extensions:
            print(f"✗ 不支持的格式: {format_type}")
            print(f"  支持的格式: {', '.join(format_extensions.keys())}")
            return None
        
        # 如果没有指定路径，使用临时文件
        if filepath is None:
            with tempfile.NamedTemporaryFile(suffix=format_extensions[format_type], delete=False) as tmp:
                filepath = tmp.name
        
        print(f"正在导出 {format_type.upper()} 到: {filepath}")
        
        try:
            # 根据格式类型生成导出代码
            export_code = self._generate_export_code(format_type, filepath, selection_only)
            
            result = self.execute_code(export_code)
            print(f"导出结果: {result}")
            
            # 检查文件是否生成
            if os.path.exists(filepath):
                # 读取文件并编码为 Base64
                with open(filepath, 'rb') as f:
                    file_data = f.read()
                
                # 清理临时文件
                try:
                    os.remove(filepath)
                except:
                    pass
                
                if file_data:
                    base64_data = base64.b64encode(file_data).decode('utf-8')
                    print(f"✓ {format_type.upper()} 导出成功，大小: {len(file_data)} 字节 ({len(base64_data)} 字符 Base64)")
                    return base64_data
            else:
                print(f"✗ {format_type.upper()} 导出失败: 文件不存在或为空")
                return None
                
        except Exception as e:
            print(f"✗ {format_type.upper()} 导出错误: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            # 清理临时文件
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass
    
    def _generate_export_code(self, format_type: str, filepath: str, selection_only: bool) -> str:
        """
        生成不同格式的导出代码
        
        Args:
            format_type: 导出格式
            filepath: 文件路径
            selection_only: 是否只导出选中对象
            
        Returns:
            str: Blender Python 导出代码
        """
        # 基础检查代码
        base_code = f"""
import bpy
import os

# 导出 {format_type.upper()}
filepath = r"{filepath}"

# 确保目录存在
dir_path = os.path.dirname(filepath)
if dir_path:
    os.makedirs(dir_path, exist_ok=True)

# 检查是否有对象可导出
if len(bpy.data.objects) == 0:
    print("ERROR: 场景中没有对象可导出")
    raise Exception("场景中没有对象可导出")
"""
        
        # 根据格式生成导出操作
        if format_type == 'stl':
            export_op = f"""# 导出 STL
try:
    bpy.ops.wm.stl_export(
        filepath=filepath,
        export_selected_objects={selection_only},
        global_scale=1.0,
        apply_modifiers=True,
        ascii_format=False
    )
except Exception as e:
    print(f"STL 导出失败: {{e}}")
    raise
"""
        
        elif format_type == 'obj':
            export_op = f"""# 导出 OBJ
try:
    bpy.ops.wm.obj_export(
        filepath=filepath,
        export_selected_objects={selection_only},
        apply_modifiers=True,
        export_materials=True,
        export_uv=True,
        export_normals=True,
        global_scale=1.0
    )
except Exception as e:
    print(f"OBJ 导出失败: {{e}}")
    raise
"""
        
        elif format_type == 'fbx':
            export_op = f"""# 导出 FBX
try:
    bpy.ops.export_scene.fbx(
        filepath=filepath,
        use_selection={selection_only},
        apply_scale_options='FBX_SCALE_ALL',
        apply_unit_scale=True,
        bake_space_transform=True,
        object_types={{'MESH', 'ARMATURE', 'EMPTY', 'LIGHT', 'CAMERA'}},
        use_mesh_modifiers=True,
        mesh_smooth_type='FACE',
        add_leaf_bones=False
    )
except Exception as e:
    print(f"FBX 导出失败: {{e}}")
    raise
"""
        
        elif format_type == 'gltf':
            export_op = f"""# 导出 glTF
try:
    bpy.ops.export_scene.gltf(
        filepath=filepath,
        export_format='GLTF_SEPARATE',
        use_selection={selection_only},
        export_apply=True
    )
except Exception as e:
    print(f"glTF 导出失败: {{e}}")
    raise
"""
        
        elif format_type == 'glb':
            export_op = f"""# 导出 GLB（glTF 二进制）
try:
    bpy.ops.export_scene.gltf(
        filepath=filepath,
        export_format='GLB',
        use_selection={selection_only},
        export_apply=True
    )
except Exception as e:
    print(f"GLB 导出失败: {{e}}")
    raise
"""
        
        elif format_type == 'ply':
            export_op = f"""# 导出 PLY
try:
    bpy.ops.wm.ply_export(
        filepath=filepath,
        export_selected_objects={selection_only},
        apply_modifiers=True,
        export_normals=True,
        export_uv=True,
        export_colors='SRGB',
        global_scale=1.0
    )
except Exception as e:
    print(f"PLY 导出失败: {{e}}")
    raise
"""
        
        elif format_type == 'x3d':
            export_op = f"""# 导出 X3D
try:
    bpy.ops.export_scene.x3d(
        filepath=filepath,
        use_selection={selection_only},
        use_mesh_modifiers=True,
        use_triangulate=False,
        use_normals=True,
        use_compress=False
    )
except Exception as e:
    print(f"X3D 导出失败: {{e}}")
    raise
"""
        
        elif format_type == 'dae':
            export_op = f"""# 导出 Collada DAE
try:
    bpy.ops.wm.collada_export(
        filepath=filepath,
        selected={selection_only},
        apply_modifiers=True
    )
except Exception as e:
    print(f"Collada 导出失败: {{e}}")
    raise
"""
        
        elif format_type == 'abc':
            export_op = f"""# 导出 Alembic
try:
    bpy.ops.wm.alembic_export(
        filepath=filepath,
        selected={selection_only},
        apply_subdiv=True
    )
except Exception as e:
    print(f"Alembic 导出失败: {{e}}")
    raise
"""
        
        else:
            export_op = f"""print("✗ 不支持的格式: {format_type}")"""
        
        # 结果检查代码
        check_code = """
if os.path.exists(filepath):
    file_size = os.path.getsize(filepath)
    print(f"✓ 导出成功: {filepath}")
    print(f"  文件大小: {file_size} 字节")
else:
    print("✗ 导出失败: 文件未生成")
"""
        
        return base_code + export_op + check_code
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取连接状态信息
        
        Returns:
            Dict: 状态信息
        """
        return {
            "connected": self.connected,
            "host": self.host,
            "port": self.port,
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
            # 发送一个简单的 ping 命令
            result = self.send_command("ping", {"message": "health_check"})
            return result is not None
        except:
            return False
    
    def close(self):
        """关闭连接"""
        if self.socket:
            try:
                # 注意：原始 MCP 插件没有 close_connection 命令
                # 直接关闭 socket 即可
                self.socket.close()
                print("连接已关闭")
            except Exception as e:
                print(f"关闭连接时出错: {e}")
            finally:
                self.socket = None
                self.connected = False
    
    def __del__(self):
        """析构函数：确保连接关闭"""
        self.close()


class BlenderModeling(BlenderClient):
    """
    建模快捷操作类
    
    提供常用的建模操作的快捷方法，让 AI 生成代码更简单。
    这是可选类，主要用于简化常见操作。
    """
    
    def __init__(self, host='localhost', port=9876):
        """初始化建模快捷操作"""
        super().__init__(host, port)
        print("建模快捷操作初始化完成")
    
    def create_cube(self, size=1.0, x=0.0, y=0.0, z=0.0, name="Cube") -> bool:
        """
        创建立方体
        
        Args:
            size: 立方体大小
            x, y, z: 位置坐标
            name: 对象名称
            
        Returns:
            bool: 是否成功
        """
        code = f'''
import bpy

# 创建立方体
bpy.ops.mesh.primitive_cube_add(
    size={size},
    location=({x}, {y}, {z})
)

# 重命名
if bpy.context.active_object:
    bpy.context.active_object.name = "{name}"
    print(f"✓ 创建立方体: {{bpy.context.active_object.name}}")
else:
    print("✗ 创建立方体失败")
'''
        result = self.execute_code(code)
        return result is not None and "✓ 创建立方体:" in result
    
    def create_sphere(self, radius=1.0, x=0.0, y=0.0, z=0.0, name="Sphere") -> bool:
        """
        创建球体
        
        Args:
            radius: 球体半径
            x, y, z: 位置坐标
            name: 对象名称
            
        Returns:
            bool: 是否成功
        """
        code = f'''
import bpy

# 创建球体
bpy.ops.mesh.primitive_uv_sphere_add(
    radius={radius},
    location=({x}, {y}, {z})
)

# 重命名
if bpy.context.active_object:
    bpy.context.active_object.name = "{name}"
    print(f"✓ 创建球体: {{bpy.context.active_object.name}}")
else:
    print("✗ 创建球体失败")
'''
        result = self.execute_code(code)
        return result is not None and "✓ 创建球体:" in result
    
    def create_cylinder(self, radius=0.5, depth=2.0, x=0.0, y=0.0, z=0.0, name="Cylinder") -> bool:
        """
        创建圆柱体
        
        Args:
            radius: 半径
            depth: 高度
            x, y, z: 位置坐标
            name: 对象名称
            
        Returns:
            bool: 是否成功
        """
        code = f'''
import bpy

# 创建圆柱体
bpy.ops.mesh.primitive_cylinder_add(
    radius={radius},
    depth={depth},
    location=({x}, {y}, {z})
)

# 重命名
if bpy.context.active_object:
    bpy.context.active_object.name = "{name}"
    print(f"✓ 创建圆柱体: {{bpy.context.active_object.name}}")
else:
    print("✗ 创建圆柱体失败")
'''
        result = self.execute_code(code)
        return result is not None and "✓ 创建圆柱体:" in result
    
    def move_object(self, object_name: str, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> bool:
        """
        移动对象
        
        Args:
            object_name: 对象名称
            x, y, z: 移动距离
            
        Returns:
            bool: 是否成功
        """
        code = f'''
import bpy

# 查找对象
obj = bpy.data.objects.get("{object_name}")
if obj:
    # 移动对象
    obj.location.x += {x}
    obj.location.y += {y}
    obj.location.z += {z}
    print(f"✓ 移动对象 {{obj.name}} 到位置 {{obj.location}}")
    return True
else:
    print(f"✗ 未找到对象: {object_name}")
    return False
'''
        result = self.execute_code(code)
        return result is not None and "✓ 移动对象" in result
    
    def rotate_object(self, object_name: str, x_deg: float = 0.0, y_deg: float = 0.0, z_deg: float = 0.0) -> bool:
        """
        旋转对象
        
        Args:
            object_name: 对象名称
            x_deg, y_deg, z_deg: 旋转角度（度）
            
        Returns:
            bool: 是否成功
        """
        import math
        
        # 转换为弧度
        x_rad = math.radians(x_deg)
        y_rad = math.radians(y_deg)
        z_rad = math.radians(z_deg)
        
        code = f'''
import bpy
import math

# 查找对象
obj = bpy.data.objects.get("{object_name}")
if obj:
    # 旋转对象
    obj.rotation_euler.x += {x_rad}
    obj.rotation_euler.y += {y_rad}
    obj.rotation_euler.z += {z_rad}
    
    # 转换为度显示
    x_deg = math.degrees(obj.rotation_euler.x)
    y_deg = math.degrees(obj.rotation_euler.y)
    z_deg = math.degrees(obj.rotation_euler.z)
    
    print(f"✓ 旋转对象 {{obj.name}} 到角度 ({{x_deg:.1f}}, {{y_deg:.1f}}, {{z_deg:.1f}}) 度")
    return True
else:
    print(f"✗ 未找到对象: {object_name}")
    return False
'''
        result = self.execute_code(code)
        return result is not None and "✓ 旋转对象" in result
    
    def delete_all(self) -> bool:
        """
        删除所有对象
        
        Returns:
            bool: 是否成功
        """
        code = '''
import bpy

# 选择所有对象
bpy.ops.object.select_all(action='SELECT')

# 删除所有对象
deleted_count = len(bpy.context.selected_objects)
bpy.ops.object.delete(use_global=False)

print(f"✓ 删除了 {deleted_count} 个对象")
'''
        result = self.execute_code(code)
        return result is not None and "✓ 删除了" in result
    
    def set_material_color(self, object_name: str, r: float = 1.0, g: float = 1.0, b: float = 1.0) -> bool:
        """
        设置对象材质颜色
        
        Args:
            object_name: 对象名称
            r, g, b: RGB 颜色值 (0.0-1.0)
            
        Returns:
            bool: 是否成功
        """
        code = f'''
import bpy

# 查找对象
obj = bpy.data.objects.get("{object_name}")
if obj:
    # 创建或获取材质
    mat_name = f"Material_{object_name}"
    material = bpy.data.materials.get(mat_name)
    
    if not material:
        material = bpy.data.materials.new(name=mat_name)
        material.use_nodes = True
    
    # 设置颜色
    if material.node_tree:
        bsdf = material.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs['Base Color'].default_value = ({r}, {g}, {b}, 1.0)
    
    # 应用材质
    if obj.data.materials:
        obj.data.materials[0] = material
    else:
        obj.data.materials.append(material)
    
    print(f"✓ 为对象 {{obj.name}} 设置颜色 ({r}, {g}, {b})")
    return True
else:
    print(f"✗ 未找到对象: {object_name}")
    return False
'''


# 使用示例
if __name__ == "__main__":
    print("=" * 50)
    print("Blender MCP 客户端测试")
    print("=" * 50)
    
    # 创建客户端实例
    client = BlenderClient(host='localhost', port=9876)
    
    # 测试连接
    if client.connect():
        print("\n✓ 连接测试成功")
        
        # 获取状态
        status = client.get_status()
        print(f"状态: {status}")
        
        # 测试场景信息获取
        scene_info = client.get_scene_info()
        if scene_info:
            print(f"场景对象数量: {scene_info.get('object_count', 0)}")
        else:
            print("场景信息获取失败")
        
        # 测试代码执行
        test_code = '''
import bpy
print("Blender Python API 测试成功")
print(f"当前场景: {bpy.context.scene.name}")
print(f"对象数量: {len(bpy.data.objects)}")
'''
        result = client.execute_code(test_code)
        if result:
            print(f"代码执行结果:\n{result}")
        else:
            print("代码执行失败")
        
        # 关闭连接
        client.close()
    else:
        print("\n✗ 连接测试失败")
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)