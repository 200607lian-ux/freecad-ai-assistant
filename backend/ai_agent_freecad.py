"""
AI 代码生成模块 - FreeCAD 版本
处理自然语言指令并生成相应的 FreeCAD Python 代码
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
        # 预定义的 FreeCAD 对象类型
        self.object_types = {
            "cube": "立方体",
            "sphere": "球体",
            "cylinder": "圆柱体",
            "cone": "圆锥体",
            "torus": "圆环"
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
                    print("[OK] AI 代理使用 DeepSeek-V4-Flash 模型")
                except Exception as e:
                    print(f"[WARN]  AI 客户端初始化失败: {e}")
                    print("   将使用规则引擎模式")
                    self.client = None
            else:
                print("[WARN]  未找到 DASHSCOPE_API_KEY 环境变量")
                print("   将使用规则引擎模式")
        else:
            print("[INFO]  AI 代理使用规则引擎模式")
        
        # 系统提示词
        self.system_prompt = """你是一个专业的 FreeCAD Python 代码生成助手。你的任务是根据用户的自然语言描述，生成准确、可执行的 FreeCAD Python 代码。

重要规则：
1. **只输出 Python 代码**，不要有任何解释、注释或其他文字
2. 代码必须以 `import FreeCAD` 和 `import Part` 开头
3. 代码必须可以直接在 FreeCAD Python 控制台中执行
4. 如果用户指定了文档名称，使用 `FreeCAD.getDocument(doc_name)` 获取文档；否则使用 `FreeCAD.ActiveDocument`
5. 如果文档不存在，创建新文档
6. 为创建的对象设置有意义的中文名称
7. 在代码末尾使用 print() 输出操作结果
8. 始终调用 doc.recompute() 刷新视图
9. **如果用户要求修改、调整或重新创建对象，先删除文档中的旧对象，然后创建新的对象**
10. **修改对象时的安全规则（必须遵守，防止 FreeCAD 闪退）**：
    - **修改前必须先判断对象类型 `obj.TypeId`**
    - **优先修改参数，绝不直接替换 `.Shape`**：
      - `Part::Box` → 修改 `Length` / `Width` / `Height`
      - `Part::Cylinder` → 修改 `Radius` / `Height`
      - `Part::Sphere` → 修改 `Radius`
      - `Part::Cone` → 修改 `Radius1` / `Radius2` / `Height`
      - `Part::Torus` → 修改 `Radius1` / `Radius2`
      - `PartDesign::Pad` / `PartDesign::Extrusion` → 修改 `Length`
      - `PartDesign::Body` → 找到内部的 Sketch 约束或 Datum 尺寸并修改
    - **严禁直接给以下类型赋值 `.Shape`**：`PartDesign::Body`、`App::Part`、`Part::Compound`、`Part::Boolean`、装配容器，这些对象的 Shape 是只读或计算属性，直接赋值会导致 FreeCAD 崩溃
    - **如果对象类型复杂、不确定、或修改参数无法满足需求，删除旧对象并按新需求重新创建**（保持其他对象不变）
    - **对于由多个 Part::Feature 对象组成的组合模型**（如柜子由底板、顶板、侧板、隔板组成），通过 Label 识别每个部件，**用 `obj.Shape = Part.makeBox(...)` 重新创建每个部件的新形状**（Part::Feature 的 Shape 可以安全替换，因为它没有参数化约束），然后调整 Placement 位置，不要整体替换某个部件的 Shape
    - **如果对象被其他对象引用或参与布尔运算**，优先修改参数；若必须删除重建，需确保不影响依赖它的对象
    - **所有修改操作完成后调用 `doc.recompute()`**
    - **关键修改步骤用 try-except 包裹**，失败时打印明确错误而不是让 FreeCAD 崩溃
11. **修改柜子、书架、书柜等组合家具时的特殊规则**：
    - **优先通过 Label 识别组成部件**：底板、顶板、左侧板、右侧板、侧板、隔板、层板、背板、以及英文 Label 如 Shelf、Side、Top、Bottom、Back、Left、Right
    - 如果找到多个组成部件，**用 `obj.Shape = Part.makeBox(...)` 重新创建每个部件的新形状**（Part::Feature 的 Shape 可以安全替换），然后调整 Placement 位置，而不是查找一个不存在的整体“柜体”对象
    - 调整高度时：侧板高度改为新高度；顶板 z 位置改为 `新高度 - 顶板厚度`；中间隔板/层板 z 位置改为 `新高度 / 2 - 隔板厚度 / 2`
    - 只有在找不到任何组成部件、且确实只有一个整体柜体对象时，才允许整体修改或删除重建
    - **严禁在没找到明确柜体对象时删除所有对象**
    - **严禁直接给 Part::Feature 赋值 .Shape 来修改尺寸**，这是导致 FreeCAD 闪退的常见原因。Part::Feature 的 Shape 是只读/计算属性，应该通过修改 Length/Width/Height 等参数来改变尺寸。但对于组合模型的独立部件（如底板、侧板等），可以安全地给每个部件的 Part::Feature 重新赋值 Shape，因为它们是独立的 Part::Feature 对象，没有参数化约束
    - **如果对象类型是 `Part::Feature` 但不确定是否安全修改 `.Shape`**，先检查 `obj.Shape.isNull()` 或 `obj.Shape.isValid()`，无效形状不要赋值
12. **视图方向规则**：
    - **生成电脑显示器、电视机、屏幕、面板等具有正面朝向的物体时，必须确保屏幕正面朝向用户（即朝前，面向 -Y 方向或根据视图调整）**
    - 使用  创建屏幕时，默认长宽平面在 XY 平面，通过  调整朝向，使屏幕正面朝向观察者
    - 对于显示器类物体，底座在底部，屏幕竖直放置，屏幕正面朝向 -Y 方向（FreeCAD 默认前视图方向）
    - 在代码末尾添加  和  确保视图正确

重要：FreeCAD 文档有两个名称：
- `Name`：内部名称（如 "DocC", "StoolModel", "Unnamed"）
- `Label`：用户可见的显示名称（如 "1", "2", "3", "StoolModel1"）
- `FreeCAD.listDocuments()` 返回的是内部 Name 列表
- 如果用户说"文档3"，需要通过 Label 查找对应的文档 Name

查找文档的正确方法（通过 Label）：
```python
# 通过 Label 查找文档
doc_name = None
for name in FreeCAD.listDocuments().keys():
    if FreeCAD.getDocument(name).Label == "3":
        doc_name = name
        break

if doc_name:
    doc = FreeCAD.getDocument(doc_name)
else:
    doc = FreeCAD.newDocument("MyDoc")
```

查找文档的方法（通过 Name）：
```python
# 通过 Name 查找文档（Name 是 FreeCAD.listDocuments() 返回的名称）
doc_name = "Part1"
if doc_name in FreeCAD.listDocuments():
    doc = FreeCAD.getDocument(doc_name)
else:
    doc = FreeCAD.newDocument(doc_name)
```

常用 FreeCAD 操作模板：

创建基础几何体：
- 立方体: Part.makeBox(10, 10, 10)
- 球体: Part.makeSphere(5)
- 圆柱: Part.makeCylinder(5, 10)
- 圆锥: Part.makeCone(5, 0, 10)
- 圆环: Part.makeTorus(10, 2)

创建对象的完整流程（使用指定文档 - 通过 Label）：
import FreeCAD
import Part

# 通过 Label 查找文档
doc_name = None
for name in FreeCAD.listDocuments().keys():
    if FreeCAD.getDocument(name).Label == "3":
        doc_name = name
        break

if doc_name:
    doc = FreeCAD.getDocument(doc_name)
else:
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

创建对象的完整流程（使用活动文档）：
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

用户: 创建一把高凳子，坐面100x100，厚度5，腿高50，腿半径3
输出:
import FreeCAD
import Part

doc = FreeCAD.ActiveDocument
if not doc:
    doc = FreeCAD.newDocument("StoolDoc")

# 清除旧对象（如果存在）
for obj in doc.Objects:
    doc.removeObject(obj.Name)

# 参数定义
seat_size = 100      # 坐面尺寸
seat_thickness = 5   # 坐面厚度
leg_height = 50      # 腿高度（从地面到坐面底部）
leg_radius = 3       # 腿半径

# 创建坐面（居中放置，底部在 z=leg_height）
seat = Part.makeBox(seat_size, seat_size, seat_thickness)
seat_obj = doc.addObject("Part::Feature", "Seat")
seat_obj.Shape = seat
# 坐面居中：中心在原点，所以左下角在 (-50, -50, leg_height)
seat_obj.Placement.Base = FreeCAD.Vector(-seat_size/2, -seat_size/2, leg_height)
seat_obj.Label = "坐面"

# 创建四条腿（位于坐面四个角正下方）
# 腿中心位于坐面角的正下方（偏移 leg_radius 使腿外侧与坐面角对齐）
offset = seat_size/2 - leg_radius
leg_positions = [
    (-offset, -offset),  # 左后
    (offset, -offset),   # 右后
    (-offset, offset),   # 左前
    (offset, offset)     # 右前
]

for i, (x, y) in enumerate(leg_positions):
    leg = Part.makeCylinder(leg_radius, leg_height)
    leg_obj = doc.addObject("Part::Feature", f"Leg{i+1}")
    leg_obj.Shape = leg
    leg_obj.Placement.Base = FreeCAD.Vector(x, y, 0)
    leg_obj.Label = f"腿{i+1}"

doc.recompute()
print(f"已创建高凳子，坐面高度: {leg_height}mm")

用户: 创建一把椅子，坐面宽50深50厚3，靠背高30，腿高40
输出:
import FreeCAD
import Part

doc = FreeCAD.ActiveDocument
if not doc:
    doc = FreeCAD.newDocument("ChairDoc")

# 清除旧对象
for obj in doc.Objects:
    doc.removeObject(obj.Name)

# 参数定义
seat_w = 50          # 坐面宽度
seat_d = 50          # 坐面深度
seat_t = 3           # 坐面厚度
leg_h = 40           # 腿高度
back_h = 30          # 靠背高度（从坐面顶部向上延伸的高度）
back_t = 3           # 靠背厚度
leg_r = 2.5          # 腿半径

# 创建坐面（居中，底部在 z=leg_h）
seat = Part.makeBox(seat_w, seat_d, seat_t)
seat_obj = doc.addObject("Part::Feature", "Seat")
seat_obj.Shape = seat
seat_obj.Placement.Base = FreeCAD.Vector(-seat_w/2, -seat_d/2, leg_h)
seat_obj.Label = "坐面"

# 创建靠背（位于坐面后侧/后方，向上延伸）
# 靠背底部与坐面顶部平齐，向上延伸 back_h 高度
back = Part.makeBox(seat_w, back_t, back_h)
back_obj = doc.addObject("Part::Feature", "Back")
back_obj.Shape = back
# 靠背位于坐面后侧：Y = seat_d/2 - back_t（坐面后边缘）
back_obj.Placement.Base = FreeCAD.Vector(-seat_w/2, seat_d/2 - back_t, leg_h + seat_t)
back_obj.Label = "靠背"

# 创建四条腿（位于坐面四角）
offset_x = seat_w/2 - leg_r
offset_y = seat_d/2 - leg_r
leg_positions = [
    (-offset_x, -offset_y),
    (offset_x, -offset_y),
    (-offset_x, offset_y),
    (offset_x, offset_y)
]

for i, (x, y) in enumerate(leg_positions):
    leg = Part.makeCylinder(leg_r, leg_h)
    leg_obj = doc.addObject("Part::Feature", f"Leg{i+1}")
    leg_obj.Shape = leg
    leg_obj.Placement.Base = FreeCAD.Vector(x, y, 0)
    leg_obj.Label = f"腿{i+1}"

doc.recompute()
print(f"已创建椅子，坐面高度: {leg_h}mm，靠背高度: {leg_h + seat_t + back_h}mm")

用户: 把靠背高度改为80，不要移动位置，不要重新创建其他部分
输出:
import FreeCAD
import Part

doc = FreeCAD.ActiveDocument
if not doc:
    print("错误：没有活动文档")
    exit()

# 找到靠背对象（通过Label或Name）
back_obj = None
for obj in doc.Objects:
    if obj.Label == "靠背" or obj.Name == "Back":
        back_obj = obj
        break

if not back_obj:
    print("错误：未找到靠背对象")
    exit()

# 获取靠背当前位置和尺寸
old_placement = back_obj.Placement
old_base = old_placement.Base

# 从当前形状获取宽度、厚度（保持原样）
# 创建新的靠背形状，高度改为80
new_back_h = 80
# 需要从原对象推断宽度，这里假设坐面宽50
seat_w = 50
back_t = 3

# 创建新靠背（保持底部位置不变，只增加高度）
new_back = Part.makeBox(seat_w, back_t, new_back_h)
back_obj.Shape = new_back
# 保持底部位置不变（只修改Z坐标）
back_obj.Placement.Base = FreeCAD.Vector(old_base.x, old_base.y, old_base.z)

doc.recompute()
print(f"已调整靠背高度为: {new_back_h}mm")

用户: 创建一把凳子，坐面直径60的圆形，厚度4，三条腿高45
输出:
import FreeCAD
import Part

doc = FreeCAD.ActiveDocument
if not doc:
    doc = FreeCAD.newDocument("StoolDoc")

for obj in doc.Objects:
    doc.removeObject(obj.Name)

seat_d = 60          # 坐面直径
seat_r = seat_d / 2  # 坐面半径
seat_t = 4           # 坐面厚度
leg_h = 45           # 腿高度
leg_r = 3            # 腿半径

# 创建圆形坐面（圆柱）
seat = Part.makeCylinder(seat_r, seat_t)
seat_obj = doc.addObject("Part::Feature", "Seat")
seat_obj.Shape = seat
seat_obj.Placement.Base = FreeCAD.Vector(0, 0, leg_h)
seat_obj.Label = "圆形坐面"

# 创建三条腿（均匀分布）
import math
for i in range(3):
    angle = i * 2 * math.pi / 3
    x = (seat_r - leg_r) * math.cos(angle)
    y = (seat_r - leg_r) * math.sin(angle)
    
    leg = Part.makeCylinder(leg_r, leg_h)
    leg_obj = doc.addObject("Part::Feature", f"Leg{i+1}")
    leg_obj.Shape = leg
    leg_obj.Placement.Base = FreeCAD.Vector(x, y, 0)
    leg_obj.Label = f"腿{i+1}"

doc.recompute()
print(f"已创建圆形凳子，腿高: {leg_h}mm")

用户: 你创建的凳子腿没有在凳子面的四个角上。请调整建模
输出:
import FreeCAD
import Part

# 通过 Label 查找文档
doc_name = None
for name in FreeCAD.listDocuments().keys():
    if FreeCAD.getDocument(name).Label == "1":
        doc_name = name
        break

if doc_name:
    doc = FreeCAD.getDocument(doc_name)
else:
    doc = FreeCAD.ActiveDocument

# 先删除所有旧对象
for obj in doc.Objects:
    doc.removeObject(obj.Name)

# 参数定义
seat_size = 100      # 坐面尺寸
seat_thickness = 5   # 坐面厚度
leg_height = 50      # 腿高度
leg_radius = 3       # 腿半径

# 创建坐面（居中，底部在 z=leg_height）
seat = Part.makeBox(seat_size, seat_size, seat_thickness)
seat_obj = doc.addObject("Part::Feature", "Seat")
seat_obj.Shape = seat
seat_obj.Placement.Base = FreeCAD.Vector(-seat_size/2, -seat_size/2, leg_height)
seat_obj.Label = "坐面"

# 创建四条腿（位于坐面四个角正下方）
offset = seat_size/2 - leg_radius
leg_positions = [
    (-offset, -offset),  # 左后
    (offset, -offset),   # 右后
    (-offset, offset),   # 左前
    (offset, offset)     # 右前
]

for i, (x, y) in enumerate(leg_positions):
    leg = Part.makeCylinder(leg_radius, leg_height)
    leg_obj = doc.addObject("Part::Feature", f"Leg{i+1}")
    leg_obj.Shape = leg
    leg_obj.Placement.Base = FreeCAD.Vector(x, y, 0)
    leg_obj.Label = f"腿{i+1}"

doc.recompute()
print(f"已重新创建凳子，腿位于坐面四角，坐面高度: {leg_height}mm")

用户: 在文档"Part1"中创建一个蓝色的圆柱体
输出:
import FreeCAD
import Part

doc_name = "Part1"
if doc_name in FreeCAD.listDocuments():
    doc = FreeCAD.getDocument(doc_name)
else:
    doc = FreeCAD.newDocument(doc_name)

cylinder = Part.makeCylinder(5, 10)
obj = doc.addObject("Part::Feature", "Cylinder")
obj.Shape = cylinder
obj.ViewObject.ShapeColor = (0.0, 0.0, 1.0)
obj.Label = "蓝色圆柱体"
doc.recompute()
print(f"已在文档 {doc_name} 中创建蓝色圆柱体")

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

用户: 列出所有文档
输出:
import FreeCAD

docs = FreeCAD.listDocuments()
for name, doc in docs.items():
    print(f"文档: {doc.Label} (内部名称: {name})")

用户: 切换到文档"Assembly"
输出:
import FreeCAD

# 通过 Label 查找文档
doc_name = None
for name in FreeCAD.listDocuments().keys():
    if FreeCAD.getDocument(name).Label == "Assembly":
        doc_name = name
        break

if doc_name:
    FreeCAD.setActiveDocument(doc_name)
    print(f"已切换到文档: Assembly")
else:
    print(f"文档 Assembly 不存在")

用户: 把柜子的高度从660mm调整为880mm，保持上下两层均分
输出:
import FreeCAD

doc = FreeCAD.ActiveDocument
if not doc:
    print("错误：没有活动文档")
    exit()

# 通过 Label 查找柜子的五个部件
def find_part(label):
    for obj in doc.Objects:
        if obj.Label == label:
            return obj
    return None

bottom = find_part("底板")
top = find_part("顶板")
left = find_part("左侧板")
right = find_part("右侧板")
shelf = find_part("隔板")

parts = {"底板": bottom, "顶板": top, "左侧板": left, "右侧板": right, "隔板": shelf}
missing = [k for k, v in parts.items() if v is None]
if missing:
    print(f"错误：缺少部件: {', '.join(missing)}")
    exit()

for name, obj in parts.items():
    if obj.TypeId != "Part::Box":
        print(f"错误：{name} 不是 Part::Box")
        exit()

old_height = left.Height
new_height = 880.0

# 侧板高度改为新总高
left.Height = new_height
right.Height = new_height

# 顶板移回顶部
top.Placement.Base = FreeCAD.Vector(top.Placement.Base.x, top.Placement.Base.y, new_height - top.Height)

# 隔板移到新中间位置
shelf.Placement.Base = FreeCAD.Vector(shelf.Placement.Base.x, shelf.Placement.Base.y, new_height / 2 - shelf.Height / 2)

doc.recompute()
print(f"柜子高度已从 {old_height}mm 调整为 {new_height}mm，上下两层均分")

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
                print(f"[WARN]  AI 生成失败，使用规则引擎: {e}")
        
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
            if not code or "import FreeCAD" not in code:
                print(f"[WARN]  AI 生成的代码格式不正确")
                return None
            
            # 生成简短的解释
            explanation = self._extract_explanation(user_message, code)
            
            return {
                "type": "code",
                "message": f"[OK] AI 生成: {explanation}",
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
        
        # 如果代码没有 import FreeCAD，添加它
        if "import FreeCAD" not in code:
            code = "import FreeCAD\nimport Part\n\n" + code
        
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
            "message": f"[OK] {explanation}",
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
        """生成创建对象代码 - FreeCAD版本"""
        obj_name_zh = self.object_types.get(object_type, object_type)
        
        # 基础创建代码 - FreeCAD Part API
        if object_type == "sphere":
            shape_creation = "Part.makeSphere(10)"
        elif object_type == "cube":
            shape_creation = "Part.makeBox(10, 10, 10)"
        elif object_type == "cylinder":
            shape_creation = "Part.makeCylinder(5, 10)"
        elif object_type == "cone":
            shape_creation = "Part.makeCone(5, 0, 10)"
        elif object_type == "torus":
            shape_creation = "Part.makeTorus(10, 2)"
        else:
            shape_creation = "Part.makeBox(10, 10, 10)"  # 默认立方体
        
        # 如果有颜色，添加材质设置
        if color:
            color_name = self._get_color_name(color)
            # FreeCAD颜色是RGB，不需要A通道
            color_rgb = color[:3]
            return f"""import FreeCAD
import Part

doc = FreeCAD.ActiveDocument
if not doc:
    doc = FreeCAD.newDocument("MyDoc")

# 创建{obj_name_zh}
shape = {shape_creation}
obj = doc.addObject("Part::Feature", "{obj_name_zh}")
obj.Shape = shape
obj.Label = "{color_name}{obj_name_zh}"

# 设置颜色
obj.ViewObject.ShapeColor = {color_rgb}

doc.recompute()
print(f"已创建{{obj.Label}}")
"""
        else:
            return f"""import FreeCAD
import Part

doc = FreeCAD.ActiveDocument
if not doc:
    doc = FreeCAD.newDocument("MyDoc")

# 创建{obj_name_zh}
shape = {shape_creation}
obj = doc.addObject("Part::Feature", "{obj_name_zh}")
obj.Shape = shape
obj.Label = "{obj_name_zh}"

doc.recompute()
print(f"已创建{{obj.Label}}")
"""
    
    def _generate_modify_object_code(self, operation: str, location: List[float] = None) -> str:
        """生成修改对象代码 - FreeCAD版本"""
        if operation == "delete_all":
            return """import FreeCAD

# 删除所有对象
doc = FreeCAD.ActiveDocument
if doc:
    for obj in doc.Objects:
        doc.removeObject(obj.Name)
    doc.recompute()
    print("已删除所有对象")
else:
    print("没有活动文档")
"""
        elif operation == "delete":
            return """import FreeCAD

# 删除选中的对象
doc = FreeCAD.ActiveDocument
if doc and doc.Objects:
    # 删除第一个对象（模拟删除选中）
    if len(doc.Objects) > 0:
        obj_name = doc.Objects[-1].Name
        doc.removeObject(obj_name)
        doc.recompute()
        print(f"已删除对象: {obj_name}")
    else:
        print("文档中没有对象")
else:
    print("没有活动文档")
"""
        elif operation == "move":
            if not location:
                location = [0, 0, 0]
            return f"""import FreeCAD

# 移动对象
doc = FreeCAD.ActiveDocument
if doc and len(doc.Objects) > 0:
    obj = doc.Objects[-1]  # 最后一个对象
    obj.Placement.Base = FreeCAD.Vector({location[0]}, {location[1]}, {location[2]})
    doc.recompute()
    print(f"已将对象 {{obj.Label}} 移动到 {{obj.Placement.Base}}")
else:
    print("没有对象可移动")
"""
        elif operation == "rotate":
            if not location:
                location = [0, 0, 45]  # 默认绕Z轴旋转45度
            return f"""import FreeCAD

# 旋转对象
doc = FreeCAD.ActiveDocument
if doc and len(doc.Objects) > 0:
    obj = doc.Objects[-1]
    # 绕Z轴旋转（角度）
    obj.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), {location[2]})
    doc.recompute()
    print(f"已旋转对象 {{obj.Label}}")
else:
    print("没有对象可旋转")
"""
        elif operation == "scale":
            if not location:
                location = [2, 2, 2]
            scale_factor = location[0]  # 使用第一个值作为缩放因子
            return f"""import FreeCAD

# 缩放对象
doc = FreeCAD.ActiveDocument
if doc and len(doc.Objects) > 0:
    obj = doc.Objects[-1]
    if hasattr(obj, 'Shape'):
        scaled_shape = obj.Shape.scaled({scale_factor})
        obj.Shape = scaled_shape
        doc.recompute()
        print(f"已缩放对象 {{obj.Label}} 倍数: {scale_factor}")
    else:
        print("对象没有 Shape 属性")
else:
    print("没有对象可缩放")
"""
        else:
            return f"""import FreeCAD

# {operation} 操作
print("该操作尚未实现")
"""
    
    def _generate_set_material_code(self, color: tuple) -> str:
        """生成设置材质代码 - FreeCAD版本"""
        color_rgb = color[:3]  # FreeCAD 只需要 RGB
        return f"""import FreeCAD

# 为对象设置颜色
doc = FreeCAD.ActiveDocument
if doc and len(doc.Objects) > 0:
    obj = doc.Objects[-1]  # 最后一个对象
    obj.ViewObject.ShapeColor = {color_rgb}
    doc.recompute()
    print(f"已为对象 {{obj.Label}} 设置颜色 {{obj.ViewObject.ShapeColor}}")
else:
    print("没有对象可设置颜色")
"""
    
    def _get_help_text(self) -> str:
        """获取帮助文本"""
        return """FreeCAD AI 助手帮助：

可用命令：
1. 创建对象
   - "创建立方体"
   - "添加球体"
   - "新建圆柱体"
   - "创建圆锥"
   - "创建圆环"

2. 修改对象
   - "移动对象到 x:1 y:2 z:3"
   - "旋转对象"
   - "放大对象"

3. 设置颜色
   - "设置为红色"
   - "改成蓝色"

4. 删除对象
   - "删除对象"
   - "删除所有对象"

5. 查询信息
   - "查看场景"
   - "有哪些对象"

6. 获取帮助
   - "帮助"
   - "我能做什么"

示例：
- "创建一个红色的立方体"
- "在位置 (20, 0, 0) 创建一个蓝色球体"
- "在已有的文档\"3\"中创建一把椅子"
- "查看场景中的对象列表"
"""


# 使用示例
if __name__ == "__main__":
    print("=" * 60)
    print("AI 代理测试")
    print("=" * 60)
    
    # 创建 AI 代理
    ai = AIAgent(use_ai=True)
    
    # 测试意图分析
    test_inputs = [
        "创建一个红色的立方体",
        "在位置(20, 0, 0)创建一个蓝色球体",
        "删除所有对象",
        "查看场景"
    ]
    
    for user_input in test_inputs:
        print(f"\n用户: {user_input}")
        intent = ai._analyze_intent(user_input)
        print(f"意图: {intent.action.value}")
        print(f"参数: {intent.parameters}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
