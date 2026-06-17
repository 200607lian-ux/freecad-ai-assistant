"""
AI 代码生成模块
处理自然语言指令并生成相应的 Blender Python 代码
使用阿里云百炼 DeepSeek-V4-Flash 模型
"""

import re
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json
from openai import OpenAI

class ActionType(Enum):
    """动作类型枚举"""
    CREATE_OBJECT = "create_object"
    MODIFY_OBJECT = "modify_object"
    SET_MATERIAL = "set_material"
    EXECUTE_CODE = "execute_code"
    GET_INFO = "get_info"
    CHAT_RESPONSE = "chat_response"

@dataclass
class Intent:
    """用户意图"""
    action: ActionType
    parameters: Dict[str, Any]
    confidence: float
    raw_text: str

class AIAgent:
    """AI 代理 - 处理自然语言并生成代码"""
    
    def __init__(self, use_ai: bool = True):
        """
        初始化 AI 代理
        
        Args:
            use_ai: 是否使用真实 AI 模型（需要 API Key）
        """
        # 预定义的 Blender 对象类型
        self.object_types = {
            "cube": "立方体",
            "sphere": "球体",
            "cylinder": "圆柱体",
            "cone": "圆锥体",
            "plane": "平面",
            "torus": "圆环",
            "monkey": "猴子",
            "grid": "网格",
            "circle": "圆形",
            "uv_sphere": "UV球体"
        }
        
        # 预定义的操作
        self.operations = {
            "move": "移动",
            "rotate": "旋转",
            "scale": "缩放",
            "delete": "删除",
            "duplicate": "复制",
            "hide": "隐藏",
            "show": "显示",
            "select": "选择"
        }
        
        # 预定义的颜色映射
        self.color_map = {
            "red": (1.0, 0.0, 0.0, 1.0),
            "green": (0.0, 1.0, 0.0, 1.0),
            "blue": (0.0, 0.0, 1.0, 1.0),
            "yellow": (1.0, 1.0, 0.0, 1.0),
            "purple": (0.5, 0.0, 0.5, 1.0),
            "orange": (1.0, 0.5, 0.0, 1.0),
            "white": (1.0, 1.0, 1.0, 1.0),
            "black": (0.0, 0.0, 0.0, 1.0),
            "gray": (0.5, 0.5, 0.5, 1.0),
            "红色": (1.0, 0.0, 0.0, 1.0),
            "绿色": (0.0, 1.0, 0.0, 1.0),
            "蓝色": (0.0, 0.0, 1.0, 1.0),
            "黄色": (1.0, 1.0, 0.0, 1.0),
            "紫色": (0.5, 0.0, 0.5, 1.0),
            "橙色": (1.0, 0.5, 0.0, 1.0),
            "白色": (1.0, 1.0, 1.0, 1.0),
            "黑色": (0.0, 0.0, 0.0, 1.0),
            "灰色": (0.5, 0.5, 0.5, 1.0)
        }
        
        # 初始化 AI 客户端
        self.use_ai = use_ai
        self.client = None
        
        if use_ai:
            api_key = os.getenv("DASHSCOPE_API_KEY")
            if api_key:
                try:
                    self.client = OpenAI(
                        api_key=api_key,
                        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                    )
                    print("✓ AI 代理使用 DeepSeek-V4-Flash 模型")
                except Exception as e:
                    print(f"⚠️  AI 客户端初始化失败: {e}")
                    print("   将使用规则引擎模式")
                    self.client = None
            else:
                print("⚠️  未找到 DASHSCOPE_API_KEY 环境变量")
                print("   将使用规则引擎模式")
        else:
            print("ℹ️  AI 代理使用规则引擎模式")
        
        # 系统提示词
        self.system_prompt = """你是一个专业的 FreeCAD Python 代码生成助手。你的任务是根据用户的自然语言描述，生成准确、可执行的 FreeCAD Python 代码。

重要规则：
1. **只输出 Python 代码**，不要有任何解释、注释或其他文字
2. 代码必须以 `import FreeCAD` 和 `import Part` 开头
3. 代码必须可以直接在 FreeCAD Python 控制台中执行
4. 确保文档存在（使用 FreeCAD.ActiveDocument 或创建新文档）
5. 为创建的对象设置有意义的中文名称
6. 在代码末尾使用 print() 输出操作结果
7. 始终调用 doc.recompute() 刷新视图

常用 FreeCAD 操作模板：

创建基础几何体：
- 立方体: Part.makeBox(10, 10, 10)
- 球体: Part.makeSphere(5)
- 圆柱: Part.makeCylinder(5, 10)
- 圆锥: Part.makeCone(5, 0, 10)
- 圆环: Part.makeTorus(10, 2)

创建对象的完整流程：
import FreeCAD
import Part

doc = FreeCAD.ActiveDocument
if not doc:
    doc = FreeCAD.newDocument("MyDoc")

# 创建形状
box = Part.makeBox(10, 10, 10)

# 添加到文档
obj = doc.addObject("Part::Feature", "Box")
obj.Shape = box

# 设置位置
obj.Placement.Base = FreeCAD.Vector(x, y, z)

# 设置颜色
obj.ViewObject.ShapeColor = (r, g, b)

# 刷新
doc.recompute()

移动对象：
obj.Placement.Base = FreeCAD.Vector(x, y, z)

旋转对象（角度）：
import math
obj.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), angle_deg)

缩放对象：
obj.Shape = obj.Shape.scaled(scale_factor)

设置颜色：
obj.ViewObject.ShapeColor = (r, g, b)

删除对象：
doc.removeObject(obj.Name)

删除所有对象：
for obj in doc.Objects:
    doc.removeObject(obj.Name)

布尔运算：
- 并集: fusion = box1.fuse(box2)
- 差集: cut = box1.cut(box2)
- 交集: common = box1.common(box2)

示例输入输出：

用户: 创建一个红色的立方体
输出:
import FreeCAD
import Part

doc = FreeCAD.ActiveDocument
if not doc:
    doc = FreeCAD.newDocument("MyDoc")

box = Part.makeBox(10, 10, 10)
obj = doc.addObject("Part::Feature", "Box")
obj.Shape = box
obj.ViewObject.ShapeColor = (1.0, 0.0, 0.0)
obj.Label = "红色立方体"
doc.recompute()
print("已创建红色立方体")

用户: 在位置(20, 0, 0)创建一个蓝色圆柱体
输出:
import FreeCAD
import Part

doc = FreeCAD.ActiveDocument
if not doc:
    doc = FreeCAD.newDocument("MyDoc")

cylinder = Part.makeCylinder(5, 10)
obj = doc.addObject("Part::Feature", "Cylinder")
obj.Shape = cylinder
obj.Placement.Base = FreeCAD.Vector(20, 0, 0)
obj.ViewObject.ShapeColor = (0.0, 0.0, 1.0)
obj.Label = "蓝色圆柱体"
doc.recompute()
print("已创建蓝色圆柱体")

用户: 创建一个球体和立方体的并集
输出:
import FreeCAD
import Part

doc = FreeCAD.ActiveDocument
if not doc:
    doc = FreeCAD.newDocument("MyDoc")

sphere = Part.makeSphere(8)
box = Part.makeBox(10, 10, 10)
box.translate(FreeCAD.Vector(-5, -5, -5))
fusion = sphere.fuse(box)

obj = doc.addObject("Part::Feature", "Fusion")
obj.Shape = fusion
obj.Label = "球体立方体并集"
doc.recompute()
print("已创建球体和立方体的并集")

用户: 删除所有对象
输出:
import FreeCAD

doc = FreeCAD.ActiveDocument
if doc:
    for obj in doc.Objects:
        doc.removeObject(obj.Name)
    doc.recompute()
    print("已删除所有对象")
else:
    print("没有活动文档")

现在请根据用户的描述生成对应的 FreeCAD Python 代码。记住：只输出代码，不要有任何其他内容！"""
    
    async def generate_response(self, 
                               user_message: str, 
                               conversation_history: List[Dict[str, Any]] = None,
                               blender_client: Any = None) -> Dict[str, Any]:
        """
        生成 AI 响应
        
        Args:
            user_message: 用户消息
            conversation_history: 对话历史
            blender_client: Blender 客户端实例
            
        Returns:
            AI 响应
        """
        # 检查是否是信息查询（规则引擎处理）
        if any(keyword in user_message for keyword in ["场景", "对象列表", "信息", "查看", "有哪些"]):
            intent = self._analyze_intent(user_message)
            if intent.action == ActionType.GET_INFO:
                return await self._generate_info_response(intent, blender_client)
        
        # 检查是否是帮助请求（规则引擎处理）
        if any(keyword in user_message for keyword in ["帮助", "help", "怎么用", "说明"]):
            intent = self._analyze_intent(user_message)
            return self._generate_chat_response(intent)
        
        # 优先尝试使用 AI 生成代码
        if self.client:
            try:
                ai_response = self._generate_with_ai(user_message)
                if ai_response:
                    return ai_response
            except Exception as e:
                print(f"⚠️  AI 生成失败，使用规则引擎: {e}")
        
        # AI 失败，降级到规则引擎
        intent = self._analyze_intent(user_message)
        
        if intent.action == ActionType.CHAT_RESPONSE:
            return self._generate_chat_response(intent)
        else:
            return self._generate_code_response(intent)
    
    def _generate_with_ai(self, user_message: str) -> Optional[Dict[str, Any]]:
        """
        使用 AI 模型生成代码
        
        Args:
            user_message: 用户消息
            
        Returns:
            AI 响应或 None（如果失败）
        """
        try:
            completion = self.client.chat.completions.create(
                model="deepseek-v4-flash",
                messages=[
                    {'role': 'system', 'content': self.system_prompt},
                    {'role': 'user', 'content': user_message}
                ],
                temperature=0.3,  # 降低温度以获得更确定的代码
                max_tokens=1500
            )
            
            # 提取生成的代码
            generated_content = completion.choices[0].message.content
            code = self._clean_code(generated_content)
            
            # 验证代码
            if not code or "import bpy" not in code:
                print(f"⚠️  AI 生成的代码格式不正确")
                return None
            
            # 生成简短的解释
            explanation = self._extract_explanation(user_message, code)
            
            return {
                "type": "code",
                "message": f"✓ AI 生成: {explanation}",
                "code": code,
                "explanation": explanation,
                "intent": "ai_generated"
            }
            
        except Exception as e:
            print(f"AI 生成错误: {e}")
            return None
    
    def _clean_code(self, code: str) -> str:
        """
        清理代码格式
        
        Args:
            code: 原始代码
            
        Returns:
            清理后的代码
        """
        # 去除 markdown 代码块标记
        code = code.strip()
        
        if code.startswith("```python"):
            code = code[9:]
        elif code.startswith("```"):
            code = code[3:]
        
        if code.endswith("```"):
            code = code[:-3]
        
        code = code.strip()
        
        # 如果代码没有 import bpy，添加它
        if "import bpy" not in code:
            code = "import bpy\n\n" + code
        
        return code
    
    def _extract_explanation(self, user_message: str, code: str) -> str:
        """
        从用户消息和代码中提取简短解释
        
        Args:
            user_message: 用户消息
            code: 生成的代码
            
        Returns:
            简短解释
        """
        # 简单的启发式方法
        if "创建" in user_message or "添加" in user_message or "新建" in user_message:
            for obj_type_zh in self.object_types.values():
                if obj_type_zh in user_message:
                    return f"创建{obj_type_zh}"
            return "创建对象"
        elif "移动" in user_message:
            return "移动对象"
        elif "旋转" in user_message:
            return "旋转对象"
        elif "缩放" in user_message or "放大" in user_message or "缩小" in user_message:
            return "缩放对象"
        elif "删除" in user_message or "清空" in user_message:
            return "删除对象"
        elif "颜色" in user_message or "材质" in user_message:
            return "设置材质"
        else:
            return "执行操作"
    
    def _analyze_intent(self, text: str) -> Intent:
        """
        分析用户意图
        
        Args:
            text: 用户输入的文本
            
        Returns:
            识别的意图
        """
        text_lower = text.lower()
        
        # 检查删除意图（优先级高）
        if any(keyword in text for keyword in ["删除", "清空", "清除", "移除"]):
            # 检查是否删除所有对象
            if any(keyword in text for keyword in ["所有", "全部", "一切"]):
                return Intent(
                    action=ActionType.MODIFY_OBJECT,
                    parameters={"operation": "delete_all"},
                    confidence=0.95,
                    raw_text=text
                )
            else:
                return Intent(
                    action=ActionType.MODIFY_OBJECT,
                    parameters={"operation": "delete"},
                    confidence=0.9,
                    raw_text=text
                )
        
        # 检查创建对象意图
        for obj_type_en, obj_type_zh in self.object_types.items():
            if f"创建{obj_type_zh}" in text or f"添加{obj_type_zh}" in text or f"新建{obj_type_zh}" in text:
                # 尝试提取颜色
                color_rgba = None
                for color_name, rgba in self.color_map.items():
                    if color_name in text:
                        color_rgba = rgba
                        break
                
                params = {"object_type": obj_type_en}
                if color_rgba:
                    params["color"] = color_rgba
                
                return Intent(
                    action=ActionType.CREATE_OBJECT,
                    parameters=params,
                    confidence=0.9,
                    raw_text=text
                )
        
        # 简单模式：检查是否只是提到了几何体名称（如"球体"）
        if not any(word in text for word in ["帮助", "什么", "怎么", "为什么", "吗"]):
            for obj_type_en, obj_type_zh in self.object_types.items():
                if obj_type_zh in text:
                    # 尝试提取颜色
                    color_rgba = None
                    for color_name, rgba in self.color_map.items():
                        if color_name in text:
                            color_rgba = rgba
                            break
                    
                    params = {"object_type": obj_type_en}
                    if color_rgba:
                        params["color"] = color_rgba
                    
                    return Intent(
                        action=ActionType.CREATE_OBJECT,
                        parameters=params,
                        confidence=0.8,
                        raw_text=text
                    )
        
        # 检查移动/旋转/缩放意图
        for op_en, op_zh in self.operations.items():
            if op_zh in text:
                # 尝试提取对象名称和参数
                params = {"operation": op_en}
                
                # 提取位置/旋转/缩放参数
                if op_en in ["move", "rotate", "scale"]:
                    # 尝试提取坐标
                    coords = self._extract_coordinates(text)
                    if coords:
                        params.update(coords)
                
                return Intent(
                    action=ActionType.MODIFY_OBJECT,
                    parameters=params,
                    confidence=0.8,
                    raw_text=text
                )
        
        # 检查颜色/材质意图
        color_match = re.search(r'(设置|改成|变为|变成)(.*?)(颜色|材质)', text)
        if color_match:
            color_name = color_match.group(2).strip()
            color_rgba = self.color_map.get(color_name.lower())
            
            if color_rgba:
                return Intent(
                    action=ActionType.SET_MATERIAL,
                    parameters={"color": color_rgba},
                    confidence=0.7,
                    raw_text=text
                )
        
        # 检查代码执行意图
        if "代码" in text or "python" in text_lower or "脚本" in text:
            # 尝试提取代码块
            code_match = re.search(r'```python\n(.*?)\n```', text, re.DOTALL)
            if code_match:
                return Intent(
                    action=ActionType.EXECUTE_CODE,
                    parameters={"code": code_match.group(1)},
                    confidence=0.9,
                    raw_text=text
                )
        
        # 检查信息查询意图
        info_keywords = ["场景", "对象", "信息", "查看", "列表", "有哪些"]
        if any(keyword in text for keyword in info_keywords):
            return Intent(
                action=ActionType.GET_INFO,
                parameters={"info_type": "scene"},
                confidence=0.7,
                raw_text=text
            )
        
        # 默认返回聊天响应
        return Intent(
            action=ActionType.CHAT_RESPONSE,
            parameters={"message": text},
            confidence=0.5,
            raw_text=text
        )
    
    def _extract_coordinates(self, text: str) -> Dict[str, float]:
        """从文本中提取坐标"""
        # 匹配数字模式
        coord_patterns = [
            r'x[:\s]*([-\d\.]+)',
            r'y[:\s]*([-\d\.]+)',
            r'z[:\s]*([-\d\.]+)',
            r'位置[:\s]*([-\d\.]+)[,\s]*([-\d\.]+)[,\s]*([-\d\.]+)',
            r'坐标[:\s]*([-\d\.]+)[,\s]*([-\d\.]+)[,\s]*([-\d\.]+)'
        ]
        
        for pattern in coord_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if 'x' in pattern:
                    # 单独提取 x, y, z
                    x_match = re.search(r'x[:\s]*([-\d\.]+)', text, re.IGNORECASE)
                    y_match = re.search(r'y[:\s]*([-\d\.]+)', text, re.IGNORECASE)
                    z_match = re.search(r'z[:\s]*([-\d\.]+)', text, re.IGNORECASE)
                    
                    if x_match and y_match and z_match:
                        return {
                            "location": [
                                float(x_match.group(1)),
                                float(y_match.group(1)),
                                float(z_match.group(1))
                            ]
                        }
                else:
                    # 一次提取三个坐标
                    return {
                        "location": [
                            float(match.group(1)),
                            float(match.group(2)),
                            float(match.group(3))
                        ]
                    }
        
        return {}
    
    def _generate_chat_response(self, intent: Intent) -> Dict[str, Any]:
        """生成聊天响应"""
        response_text = f"我理解了你的意图：{intent.raw_text}\n\n"
        
        if "帮助" in intent.raw_text or "?" in intent.raw_text:
            response_text += self._get_help_text()
        else:
            response_text += "我可以帮你：\n"
            response_text += "1. 创建 3D 对象（立方体、球体、圆柱体等）\n"
            response_text += "2. 修改对象（移动、旋转、缩放）\n"
            response_text += "3. 设置对象材质和颜色\n"
            response_text += "4. 执行 Python 代码\n"
            response_text += "5. 查看场景信息\n\n"
            response_text += "请告诉我你想要做什么？"
        
        return {
            "type": "chat",
            "message": response_text,
            "code": None,
            "intent": intent.action.value
        }
    
    def _generate_code_response(self, intent: Intent) -> Dict[str, Any]:
        """生成代码响应"""
        code = ""
        explanation = ""
        
        if intent.action == ActionType.CREATE_OBJECT:
            obj_type = intent.parameters.get("object_type", "cube")
            color = intent.parameters.get("color")
            code = self._generate_create_object_code(obj_type, color)
            
            obj_name = self.object_types.get(obj_type, obj_type)
            if color:
                color_name = self._get_color_name(color)
                explanation = f"创建了一个{color_name}{obj_name}"
            else:
                explanation = f"创建了一个{obj_name}"
            
        elif intent.action == ActionType.MODIFY_OBJECT:
            operation = intent.parameters.get("operation", "move")
            location = intent.parameters.get("location", [0, 0, 0])
            code = self._generate_modify_object_code(operation, location)
            
            if operation == "delete_all":
                explanation = "删除所有物体"
            elif operation == "delete":
                explanation = "删除选中的对象"
            else:
                explanation = f"{self.operations.get(operation, operation)}对象"
            
        elif intent.action == ActionType.SET_MATERIAL:
            color = intent.parameters.get("color", (1.0, 1.0, 1.0, 1.0))
            code = self._generate_set_material_code(color)
            color_name = self._get_color_name(color)
            explanation = f"设置对象材质颜色为{color_name}"
            
        elif intent.action == ActionType.EXECUTE_CODE:
            code = intent.parameters.get("code", "")
            explanation = "执行自定义 Python 代码"
        
        return {
            "type": "code",
            "message": f"✓ {explanation}",
            "code": code,
            "explanation": explanation,
            "intent": intent.action.value
        }
    
    def _get_color_name(self, color_rgba: tuple) -> str:
        """根据 RGBA 值获取颜色名称"""
        for name, rgba in self.color_map.items():
            if rgba == color_rgba:
                # 优先返回中文名称
                if len(name) > 1 and '\u4e00' <= name[0] <= '\u9fff':
                    return name
        
        # 如果没找到，返回 RGB 值描述
        return f"RGB({color_rgba[0]:.1f}, {color_rgba[1]:.1f}, {color_rgba[2]:.1f})"
    
    async def _generate_info_response(self, intent: Intent, blender_client: Any) -> Dict[str, Any]:
        """生成信息响应"""
        if not blender_client:
            return {
                "type": "chat",
                "message": "无法获取场景信息，Blender 客户端未连接",
                "code": None,
                "intent": intent.action.value
            }
        
        try:
            # 注意：blender_client.get_scene_info() 是同步方法
            # 使用 await 会使错误，改为直接调用
            scene_info = blender_client.get_scene_info()
            response_text = "当前场景信息：\n"
            response_text += f"- 对象数量：{scene_info.get('object_count', 0)}\n"
            response_text += f"- 活动对象：{scene_info.get('active_object', '无')}\n"
            
            objects = scene_info.get('objects', [])
            if objects:
                response_text += "- 对象列表：\n"
                for obj in objects[:10]:  # 显示前10个对象
                    response_text += f"  • {obj.get('name', '未知')} ({obj.get('type', '未知')})\n"
                if len(objects) > 10:
                    response_text += f"  ... 还有 {len(objects) - 10} 个对象\n"
            
            return {
                "type": "info",
                "message": response_text,
                "data": scene_info,
                "intent": intent.action.value
            }
            
        except Exception as e:
            return {
                "type": "error",
                "message": f"获取场景信息失败：{str(e)}",
                "intent": intent.action.value
            }
    
    def _generate_create_object_code(self, object_type: str, color: tuple = None) -> str:
        """生成创建对象代码"""
        obj_name_zh = self.object_types.get(object_type, object_type)
        
        # 基础创建代码
        if object_type == "uv_sphere" or object_type == "sphere":
            create_op = "bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))"
        elif object_type == "cube":
            create_op = "bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))"
        elif object_type == "cylinder":
            create_op = "bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 0))"
        elif object_type == "cone":
            create_op = "bpy.ops.mesh.primitive_cone_add(radius1=1, depth=2, location=(0, 0, 0))"
        elif object_type == "plane":
            create_op = "bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))"
        elif object_type == "torus":
            create_op = "bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.25, location=(0, 0, 0))"
        else:
            create_op = f"bpy.ops.mesh.primitive_{object_type}_add(location=(0, 0, 0))"
        
        # 如果有颜色，添加材质设置
        if color:
            color_name = self._get_color_name(color)
            return f"""import bpy

# 创建{obj_name_zh}
{create_op}

# 获取创建的对象
obj = bpy.context.active_object
obj.name = "{color_name}{obj_name_zh}"

# 设置材质颜色
mat = bpy.data.materials.new(name="{color_name}材质")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs['Base Color'].default_value = {color}

# 应用材质
if obj.data.materials:
    obj.data.materials[0] = mat
else:
    obj.data.materials.append(mat)

print(f"✓ 已创建{{obj.name}}")
"""
        else:
            return f"""import bpy

# 创建{obj_name_zh}
{create_op}

# 获取创建的对象
obj = bpy.context.active_object
obj.name = "{obj_name_zh}"

print(f"✓ 已创建{{obj.name}}")
"""
    
    def _generate_modify_object_code(self, operation: str, location: List[float] = None) -> str:
        """生成修改对象代码"""
        if operation == "delete_all":
            return """import bpy

# 删除所有对象
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
print("✓ 已删除所有物体")
"""
        elif operation == "delete":
            return """import bpy

# 删除选中的对象
if bpy.context.selected_objects:
    for obj in bpy.context.selected_objects:
        print(f"✓ 删除对象: {obj.name}")
        bpy.data.objects.remove(obj, do_unlink=True)
else:
    print("⚠️ 没有选中的对象")
"""
        elif operation == "move":
            if not location:
                location = [0, 0, 0]
            return f"""import bpy

# 移动活动对象
if bpy.context.active_object:
    obj = bpy.context.active_object
    obj.location = ({location[0]}, {location[1]}, {location[2]})
    print(f"✓ 已将对象 {{obj.name}} 移动到位置 {{obj.location}}")
else:
    print("⚠️ 没有活动对象")
"""
        elif operation == "rotate":
            if not location:
                location = [0, 0, 0]
            return f"""import bpy
import math

# 旋转活动对象
if bpy.context.active_object:
    obj = bpy.context.active_object
    # 将角度转换为弧度
    obj.rotation_euler = (
        math.radians({location[0]}),
        math.radians({location[1]}),
        math.radians({location[2]})
    )
    print(f"✓ 已将对象 {{obj.name}} 旋转到 {{[math.degrees(x) for x in obj.rotation_euler]}} 度")
else:
    print("⚠️ 没有活动对象")
"""
        elif operation == "scale":
            if not location:
                location = [1, 1, 1]
            return f"""import bpy

# 缩放活动对象
if bpy.context.active_object:
    obj = bpy.context.active_object
    obj.scale = ({location[0]}, {location[1]}, {location[2]})
    print(f"✓ 已将对象 {{obj.name}} 缩放到 {{obj.scale}}")
else:
    print("⚠️ 没有活动对象")
"""
        else:
            return f"""import bpy

# {operation} 操作
print("⚠️ 该操作尚未实现")
"""
    
    def _generate_set_material_code(self, color: tuple) -> str:
        """生成设置材质代码"""
        return f"""import bpy

# 为活动对象设置材质
if bpy.context.active_object:
    obj = bpy.context.active_object
    
    # 创建新材质
    mat = bpy.data.materials.new(name="新材质")
    mat.use_nodes = True
    
    # 设置基础颜色
    if mat.node_tree:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs['Base Color'].default_value = {color}
    
    # 应用材质到对象
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    
    print(f"已为对象 {{obj.name}} 设置材质颜色 {{bsdf.inputs['Base Color'].default_value}}")
else:
    print("没有活动对象")
"""
    
    def _get_help_text(self) -> str:
        """获取帮助文本"""
        return """Blender AI 助手帮助：

可用命令：
1. 创建对象
   - "创建立方体"
   - "添加球体"
   - "新建圆柱体"

2. 修改对象
   - "移动对象到 x:1 y:2 z:3"
   - "旋转对象"
   - "放大对象"

3. 设置材质
   - "设置为红色"
   - "改成蓝色材质"

4. 执行代码
   - ```python
     # 你的代码
     ```

5. 查询信息
   - "查看场景"
   - "有哪些对象"

6. 获取帮助
   - "帮助"
   - "我能做什么"

示例：
- "创建一个红色的立方体在位置 (0, 1, 2)"
- "旋转当前对象 45度"
- "查看场景中的对象列表"
"""