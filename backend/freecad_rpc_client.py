"""
FreeCAD RPC 直连客户端
绕过 MCP 协议，直接通过 XML-RPC 连接 freecad-mcp 的 RPC 服务器

使用方法：
1. 在 FreeCAD 中启动 RPC Server（通过 FreeCADMCP addon）
2. 默认端口: 9875
3. 使用此类直接调用 FreeCAD 功能

作者: FreeCAD AI 助手项目
"""

import xmlrpc.client
import logging
import threading
from typing import Any, Optional, Dict, List
import base64
import io
from PIL import Image

logger = logging.getLogger("FreeCADRPCClient")


class _TimeoutTransport(xmlrpc.client.Transport):
    """XML-RPC transport with configurable timeout"""
    def __init__(self, timeout: float = 30, **kwargs):
        super().__init__(**kwargs)
        self._timeout = timeout

    def make_connection(self, host):
        conn = super().make_connection(host)
        conn.timeout = self._timeout
        return conn


class FreeCADRPCClient:
    """
    FreeCAD RPC 直连客户端
    
    直接连接 freecad-mcp 的 RPC 服务器，无需 MCP 中间层
    """
    
    def __init__(self, host: str = "localhost", port: int = 9875, timeout: float = 150):
        """
        初始化 RPC 客户端
        
        Args:
            host: RPC 服务器主机地址（默认 localhost）
            port: RPC 服务器端口（默认 9875）
            timeout: 连接超时时间（秒）
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self._local = threading.local()
        self.connected = False
        
        print(f"FreeCAD RPC 客户端初始化")
        print(f"目标地址: {host}:{port}")
        print(f"提示: 请确保 FreeCAD 中已启动 RPC Server")
    
    def _get_server(self):
        """获取当前线程的 ServerProxy（线程安全）"""
        if not hasattr(self._local, 'server') or self._local.server is None:
            self._local.server = xmlrpc.client.ServerProxy(
                f"http://{self.host}:{self.port}",
                allow_none=True,
                transport=_TimeoutTransport(timeout=self.timeout),
            )
        return self._local.server
    
    def _close_server(self):
        """关闭当前线程的 ServerProxy"""
        if hasattr(self._local, 'server') and self._local.server is not None:
            try:
                server = self._local.server
                transport = getattr(server, "_ServerProxy__transport", None)
                close = getattr(transport, "close", None)
                if callable(close):
                    close()
            except Exception:
                pass
            self._local.server = None
    
    def _is_connection_error(self, error: Exception) -> bool:
        """判断异常是否为 FreeCAD RPC 连接类错误"""
        err_str = str(error).lower()
        return (
            isinstance(error, ConnectionRefusedError) or
            "actively refused" in err_str or
            "connection refused" in err_str or
            "10061" in err_str or
            "target machine" in err_str or
            "由于目标计算机积极拒绝" in err_str
        )
    
    def connect(self) -> bool:
        """
        连接到 FreeCAD RPC 服务器
        
        Returns:
            bool: 连接是否成功
        """
        try:
            # 先清理当前线程可能已损坏的旧连接
            self._close_server()
            # 测试连接（每个线程独立）
            result = self._get_server().ping()
            if result:
                self.connected = True
                print(f"[OK] 已连接到 FreeCAD RPC 服务器")
                print(f"   地址: {self.host}:{self.port}")
                return True
            else:
                print("[FAIL] RPC 服务器响应异常")
                return False
                
        except ConnectionRefusedError:
            print("[FAIL] 连接被拒绝")
            print("   请确保:")
            print("     1. FreeCAD 已启动")
            print("     2. 在 FreeCAD 中执行了 'Start RPC Server'")
            print("     3. RPC 服务器正在监听端口 9875")
            return False
        except Exception as e:
            print(f"[FAIL] 连接失败: {e}")
            return False
    
    def disconnect(self) -> None:
        """断开连接"""
        self._close_server()
        self.connected = False
        print("FreeCAD RPC 客户端已断开")
    
    # ==================== 文档操作 ====================
    
    def create_document(self, name: str = "New_Document") -> Dict[str, Any]:
        """创建新文档"""
        if not self._check_connection():
            return {"success": False, "error": "未连接"}
        
        try:
            result = self._get_server().create_document(name)
            print(f"[OK] 创建文档: {name}")
            return result
        except Exception as e:
            print(f"[FAIL] 创建文档失败: {e}")
            return {"success": False, "error": str(e)}
    
    def list_documents(self) -> List[str]:
        """获取所有文档列表（返回内部名称 Name）"""
        if not self._check_connection():
            return []
        
        try:
            return self._get_server().list_documents()
        except Exception as e:
            print(f"[FAIL] 获取文档列表失败: {e}")
            return []
    
    def get_document_labels(self) -> List[Dict[str, str]]:
        """获取所有文档的 Label 列表（用户可见名称）
        
        Returns:
            列表，每个元素包含 {"name": 内部名称, "label": 显示名称}
        """
        if not self._check_connection():
            return []
        
        try:
            # 通过 execute_code 获取文档 Label 信息
            code = """
import FreeCAD
result = []
for name in FreeCAD.listDocuments().keys():
    doc = FreeCAD.getDocument(name)
    result.append({"name": name, "label": doc.Label})
print(result)
"""
            exec_result = self._get_server().execute_code(code)
            if exec_result.get("success"):
                # 从输出中解析结果
                output = exec_result.get("message", "")
                # 提取 print 输出的列表字符串
                if "Output:" in output:
                    list_str = output.split("Output:")[-1].strip()
                    # 尝试解析为 Python 列表
                    import ast
                    try:
                        return ast.literal_eval(list_str)
                    except:
                        pass
            
            # 如果上面的方法失败，回退到只返回 Name 列表
            docs = self.list_documents()
            return [{"name": d, "label": d} for d in docs]
            
        except Exception as e:
            print(f"[FAIL] 获取文档标签失败: {e}")
            # 回退到只返回 Name 列表
            docs = self.list_documents()
            return [{"name": d, "label": d} for d in docs]
    
    def reload_document(self, doc_name: str) -> Dict[str, Any]:
        """重新加载文档"""
        if not self._check_connection():
            return {"success": False, "error": "未连接"}
        
        try:
            return self._get_server().reload_document(doc_name)
        except Exception as e:
            print(f"[FAIL] 重新加载文档失败: {e}")
            return {"success": False, "error": str(e)}
    
    # ==================== 对象操作 ====================
    
    def create_object(self, doc_name: str, obj_type: str, obj_name: str, 
                     obj_properties: Dict[str, Any] = None,
                     analysis_name: str = None) -> Dict[str, Any]:
        """
        创建对象
        
        Args:
            doc_name: 文档名称
            obj_type: 对象类型 (如 "Part::Box", "Part::Cylinder", "Draft::Circle")
            obj_name: 对象名称
            obj_properties: 对象属性字典
            analysis_name: FEM 分析名称（可选）
        
        Returns:
            操作结果
        """
        if not self._check_connection():
            return {"success": False, "error": "未连接"}
        
        obj_data = {
            "Name": obj_name,
            "Type": obj_type,
        }
        
        if analysis_name:
            obj_data["Analysis"] = analysis_name
        
        if obj_properties:
            obj_data["Properties"] = obj_properties
        
        try:
            result = self._get_server().create_object(doc_name, obj_data)
            if result.get("success"):
                print(f"[OK] 创建对象: {obj_name} ({obj_type})")
            else:
                print(f"[FAIL] 创建对象失败: {result.get('error', '未知错误')}")
            return result
        except Exception as e:
            print(f"[FAIL] 创建对象失败: {e}")
            return {"success": False, "error": str(e)}
    
    def edit_object(self, doc_name: str, obj_name: str, 
                   properties: Dict[str, Any]) -> Dict[str, Any]:
        """编辑对象属性"""
        if not self._check_connection():
            return {"success": False, "error": "未连接"}
        
        try:
            obj_data = {"Properties": properties}
            result = self._get_server().edit_object(doc_name, obj_name, obj_data)
            if result.get("success"):
                print(f"[OK] 编辑对象: {obj_name}")
            return result
        except Exception as e:
            print(f"[FAIL] 编辑对象失败: {e}")
            return {"success": False, "error": str(e)}
    
    def delete_object(self, doc_name: str, obj_name: str) -> Dict[str, Any]:
        """删除对象"""
        if not self._check_connection():
            return {"success": False, "error": "未连接"}
        
        try:
            result = self._get_server().delete_object(doc_name, obj_name)
            if result.get("success"):
                print(f"[OK] 删除对象: {obj_name}")
            return result
        except Exception as e:
            print(f"[FAIL] 删除对象失败: {e}")
            return {"success": False, "error": str(e)}
    
    def get_objects(self, doc_name: str) -> List[Dict[str, Any]]:
        """获取文档中的所有对象"""
        if not self._check_connection():
            return []
        
        try:
            return self._get_server().get_objects(doc_name)
        except Exception as e:
            print(f"[FAIL] 获取对象列表失败: {e}")
            return []
    
    def get_object(self, doc_name: str, obj_name: str) -> Optional[Dict[str, Any]]:
        """获取单个对象信息"""
        if not self._check_connection():
            return None
        
        try:
            return self._get_server().get_object(doc_name, obj_name)
        except Exception as e:
            print(f"[FAIL] 获取对象失败: {e}")
            return None
    
    # ==================== 代码执行 ====================
    
    def execute_code(self, code: str) -> Dict[str, Any]:
        """
        在 FreeCAD 中执行 Python 代码（同步，在 GUI 线程执行）
        
        Args:
            code: Python 代码字符串
        
        Returns:
            执行结果，包含输出和成功状态
        """
        if not self._check_connection():
            return {"success": False, "error": "未连接"}
        
        def _do_execute():
            result = self._get_server().execute_code(code)
            if result.get("success"):
                output = result.get("message", "")
                print(f"[OK] 代码执行成功")
                if "Output:" in output:
                    print(f"  输出: {output.split('Output:')[-1].strip()[:200]}")
            else:
                print(f"[FAIL] 代码执行失败: {result.get('error', '未知错误')}")
            return result
        
        try:
            return _do_execute()
        except Exception as e:
            if self._is_connection_error(e):
                print(f"[WARN] FreeCAD RPC 连接断开，尝试重连...")
                self.connected = False
                if self.connect():
                    try:
                        return _do_execute()
                    except Exception as e2:
                        err_msg = f"FreeCAD 重连后仍无法执行: {e2}"
                        print(f"[FAIL] {err_msg}")
                        return {"success": False, "error": err_msg}
                else:
                    err_msg = "FreeCAD RPC 连接已断开，请检查 FreeCAD 是否仍在运行并已启动 RPC Server"
                    print(f"[FAIL] {err_msg}")
                    return {"success": False, "error": err_msg}
            print(f"[FAIL] 代码执行失败: {e}")
            return {"success": False, "error": str(e)}
    
    def execute_code_async(self, code: str) -> Dict[str, Any]:
        """
        在后台线程异步执行 Python 代码
        
        适用于长时间运行的计算，不阻塞 GUI
        """
        if not self._check_connection():
            return {"success": False, "error": "未连接"}
        
        try:
            result = self._get_server().execute_code_async(code)
            print(f"[OK] 后台代码执行已启动")
            return result
        except Exception as e:
            print(f"[FAIL] 后台代码执行失败: {e}")
            return {"success": False, "error": str(e)}
    
    # ==================== 视图和截图 ====================
    
    def get_screenshot(self, view_name: str = "Isometric", 
                      width: int = None, height: int = None,
                      focus_object: str = None) -> Optional[Image.Image]:
        """
        获取 FreeCAD 视图的截图
        
        Args:
            view_name: 视图名称 (Isometric, Front, Top, Right, Back, Left, Bottom)
            width: 截图宽度
            height: 截图高度
            focus_object: 聚焦对象名称
        
        Returns:
            PIL Image 对象，失败返回 None
        """
        if not self._check_connection():
            return None
        
        try:
            image_data = self._get_server().get_active_screenshot(view_name, width, height, focus_object)
            if image_data:
                image_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_bytes))
                print(f"[OK] 截图获取成功: {image.size}")
                return image
            else:
                print("[FAIL] 截图获取失败")
                return None
        except Exception as e:
            print(f"[FAIL] 截图获取失败: {e}")
            return None
    
    def save_screenshot(self, filepath: str, view_name: str = "Isometric",
                       width: int = None, height: int = None,
                       focus_object: str = None) -> bool:
        """保存截图到文件"""
        image = self.get_screenshot(view_name, width, height, focus_object)
        if image:
            try:
                image.save(filepath)
                print(f"[OK] 截图已保存: {filepath}")
                return True
            except Exception as e:
                print(f"[FAIL] 保存截图失败: {e}")
                return False
        return False
    
    # ==================== 零件库 ====================
    
    def get_parts_list(self) -> List[str]:
        """获取零件库列表"""
        if not self._check_connection():
            return []
        
        try:
            return self._get_server().get_parts_list()
        except Exception as e:
            print(f"[FAIL] 获取零件库列表失败: {e}")
            return []
    
    def insert_part_from_library(self, relative_path: str) -> Dict[str, Any]:
        """从零件库插入零件"""
        if not self._check_connection():
            return {"success": False, "error": "未连接"}
        
        try:
            result = self._get_server().insert_part_from_library(relative_path)
            if result.get("success"):
                print(f"[OK] 插入零件: {relative_path}")
            return result
        except Exception as e:
            print(f"[FAIL] 插入零件失败: {e}")
            return {"success": False, "error": str(e)}
    
    # ==================== FEM 分析 ====================
    
    def run_fem_analysis(self, doc_name: str, analysis_name: str, 
                        timeout: int = 600) -> Dict[str, Any]:
        """运行 FEM 分析"""
        if not self._check_connection():
            return {"success": False, "error": "未连接"}
        
        try:
            print(f"开始 FEM 分析 (可能需要几分钟)...")
            result = self._get_server().run_fem_analysis(doc_name, analysis_name, timeout)
            if result.get("success"):
                print(f"[OK] FEM 分析完成")
            return result
        except Exception as e:
            print(f"[FAIL] FEM 分析失败: {e}")
            return {"success": False, "error": str(e)}
    
    # ==================== 便捷方法 ====================
    
    def create_box(self, doc_name: str, obj_name: str = "Box",
                   length: float = 10, width: float = 10, height: float = 10,
                   x: float = 0, y: float = 0, z: float = 0,
                   color: List[float] = None) -> Dict[str, Any]:
        """便捷方法：创建立方体"""
        properties = {
            "Length": length,
            "Width": width,
            "Height": height,
            "Placement": {
                "Base": {"x": x, "y": y, "z": z}
            }
        }
        
        if color:
            properties["ViewObject"] = {"ShapeColor": color + [1.0] if len(color) == 3 else color}
        
        return self.create_object(doc_name, "Part::Box", obj_name, properties)
    
    def create_cylinder(self, doc_name: str, obj_name: str = "Cylinder",
                        radius: float = 5, height: float = 10,
                        x: float = 0, y: float = 0, z: float = 0,
                        color: List[float] = None) -> Dict[str, Any]:
        """便捷方法：创建圆柱体"""
        properties = {
            "Radius": radius,
            "Height": height,
            "Placement": {
                "Base": {"x": x, "y": y, "z": z}
            }
        }
        
        if color:
            properties["ViewObject"] = {"ShapeColor": color + [1.0] if len(color) == 3 else color}
        
        return self.create_object(doc_name, "Part::Cylinder", obj_name, properties)
    
    def create_sphere(self, doc_name: str, obj_name: str = "Sphere",
                     radius: float = 5,
                     x: float = 0, y: float = 0, z: float = 0,
                     color: List[float] = None) -> Dict[str, Any]:
        """便捷方法：创建球体"""
        properties = {
            "Radius": radius,
            "Placement": {
                "Base": {"x": x, "y": y, "z": z}
            }
        }
        
        if color:
            properties["ViewObject"] = {"ShapeColor": color + [1.0] if len(color) == 3 else color}
        
        return self.create_object(doc_name, "Part::Sphere", obj_name, properties)
    
    def set_object_color(self, doc_name: str, obj_name: str, 
                        r: float, g: float, b: float, a: float = 1.0) -> Dict[str, Any]:
        """设置对象颜色"""
        properties = {
            "ViewObject": {
                "ShapeColor": [r, g, b, a]
            }
        }
        return self.edit_object(doc_name, obj_name, properties)
    
    def move_object(self, doc_name: str, obj_name: str, 
                   x: float, y: float, z: float) -> Dict[str, Any]:
        """移动对象"""
        properties = {
            "Placement": {
                "Base": {"x": x, "y": y, "z": z}
            }
        }
        return self.edit_object(doc_name, obj_name, properties)
    
    def rotate_object(self, doc_name: str, obj_name: str,
                     axis_x: float = 0, axis_y: float = 0, axis_z: float = 1,
                     angle: float = 45) -> Dict[str, Any]:
        """旋转对象"""
        properties = {
            "Placement": {
                "Rotation": {
                    "Axis": {"x": axis_x, "y": axis_y, "z": axis_z},
                    "Angle": angle
                }
            }
        }
        return self.edit_object(doc_name, obj_name, properties)
    
    def export_document(self, doc_name: str, filepath: str, format: str = "step") -> Dict[str, Any]:
        """
        导出文档到指定格式
        
        Args:
            doc_name: 文档名称
            filepath: 导出文件路径
            format: 导出格式 (step, stl, obj, iges, brep, csv)
        
        Returns:
            Dict: 导出结果
        """
        if not self._check_connection():
            return {"success": False, "error": "未连接"}
        
        try:
            # 使用 FreeCAD 的导出功能
            code = f'''
import FreeCAD
import Part
import Mesh
import MeshPart
import os

# 获取文档
doc = FreeCAD.getDocument("{doc_name}")
if not doc:
    print(f"错误: 找不到文档 {doc_name}")
    exit()

export_path = {repr(filepath)}
export_format = "{format}".lower()

# 创建临时合并对象（用于导出）
# 获取所有 Part 对象
part_objects = [obj for obj in doc.Objects if hasattr(obj, 'Shape')]

if not part_objects:
    print("错误: 文档中没有可导出的 Part 对象")
    exit()

# 导出逻辑
if export_format == "step":
    import Import
    Import.export(part_objects, export_path)
    print(f"[OK] 已导出 STEP: {{export_path}}")
    
elif export_format == "stl":
    # 合并所有形状并导出为 STL
    shapes = [obj.Shape for obj in part_objects]
    if shapes:
        compound = Part.makeCompound(shapes)
        mesh = MeshPart.meshFromShape(Shape=compound)
        mesh.write(export_path)
        print(f"[OK] 已导出 STL: {{export_path}}")
    
elif export_format == "obj":
    # 导出为 OBJ（通过 Mesh）
    shapes = [obj.Shape for obj in part_objects]
    if shapes:
        compound = Part.makeCompound(shapes)
        mesh = MeshPart.meshFromShape(Shape=compound)
        mesh.write(export_path)
        print(f"[OK] 已导出 OBJ: {{export_path}}")
    
elif export_format == "iges":
    import Import
    Import.export(part_objects, export_path)
    print(f"[OK] 已导出 IGES: {{export_path}}")
    
elif export_format == "brep":
    # 导出为 BREP 格式
    shapes = [obj.Shape for obj in part_objects]
    if shapes:
        compound = Part.makeCompound(shapes)
        compound.exportBrep(export_path)
        print(f"[OK] 已导出 BREP: {{export_path}}")

elif export_format == "csv":
    # 导出对象信息为 CSV
    import csv
    with open(export_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'Label', 'Type', 'Position_X', 'Position_Y', 'Position_Z'])
        for obj in doc.Objects:
            pos = obj.Placement.Base if hasattr(obj, 'Placement') else FreeCAD.Vector(0,0,0)
            writer.writerow([
                obj.Name,
                obj.Label,
                obj.TypeId,
                round(pos.x, 3),
                round(pos.y, 3),
                round(pos.z, 3)
            ])
    print(f"[OK] 已导出 CSV: {{export_path}}")

else:
    print(f"错误: 不支持的格式: {{export_format}}")
    exit()

print(f"导出完成: {{os.path.getsize(export_path)}} bytes")
'''
            result = self.execute_code(code)
            return result
            
        except Exception as e:
            print(f"[FAIL] 导出失败: {e}")
            return {"success": False, "error": str(e)}
    
    # ==================== 内部方法 ====================
    
    def _check_connection(self) -> bool:
        """检查连接状态"""
        if not self.connected:
            print("[FAIL] 未连接到 FreeCAD RPC 服务器")
            print("   请先调用 connect() 方法")
            return False
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """获取连接状态"""
        return {
            "connected": self.connected,
            "host": self.host,
            "port": self.port,
            "type": "FreeCAD RPC (XML-RPC)"
        }
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            if self.connected:
                return self._get_server().ping()
            return False
        except:
            return False


# ==================== 使用示例 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("FreeCAD RPC 直连客户端测试")
    print("=" * 60)
    
    # 创建客户端
    client = FreeCADRPCClient(host="localhost", port=9875)
    
    # 连接
    if client.connect():
        print("\n[OK] 连接成功")
        
        # 获取文档列表
        print("\n--- 文档列表 ---")
        docs = client.list_documents()
        print(f"文档: {docs}")
        
        # 如果没有文档，创建一个
        if not docs:
            print("\n--- 创建文档 ---")
            result = client.create_document("TestDoc")
            print(f"结果: {result}")
            docs = client.list_documents()
        
        doc_name = docs[0] if docs else "TestDoc"
        
        # 创建立方体
        print("\n--- 创建立方体 ---")
        result = client.create_box(
            doc_name=doc_name,
            obj_name="MyBox",
            length=20, width=20, height=20,
            x=0, y=0, z=0,
            color=[1.0, 0.0, 0.0]  # 红色
        )
        print(f"结果: {result}")
        
        # 创建圆柱体
        print("\n--- 创建圆柱体 ---")
        result = client.create_cylinder(
            doc_name=doc_name,
            obj_name="MyCylinder",
            radius=5, height=15,
            x=30, y=0, z=0,
            color=[0.0, 0.0, 1.0]  # 蓝色
        )
        print(f"结果: {result}")
        
        # 获取对象列表
        print("\n--- 对象列表 ---")
        objects = client.get_objects(doc_name)
        for obj in objects:
            print(f"  - {obj.get('name', 'unknown')} ({obj.get('type', 'unknown')})")
        
        # 执行自定义代码
        print("\n--- 执行自定义代码 ---")
        code = """
import FreeCAD
import Part

doc = FreeCAD.ActiveDocument
if doc:
    print(f"当前文档: {doc.Name}")
    print(f"对象数量: {len(doc.Objects)}")
    for obj in doc.Objects:
        print(f"  - {obj.Label} ({obj.TypeId})")
else:
    print("没有活动文档")
"""
        result = client.execute_code(code)
        print(f"结果: {result}")
        
        # 获取截图
        print("\n--- 获取截图 ---")
        image = client.get_screenshot(view_name="Isometric")
        if image:
            image.save("freecad_screenshot.png")
            print("[OK] 截图已保存到 freecad_screenshot.png")
        
        # 断开连接
        print("\n--- 断开连接 ---")
        client.disconnect()
        
    else:
        print("\n[FAIL] 连接失败")
        print("\n请确保:")
        print("  1. FreeCAD 已启动")
        print("  2. 安装了 FreeCADMCP addon")
        print("  3. 在 FreeCAD 中执行了 'Start RPC Server'")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
