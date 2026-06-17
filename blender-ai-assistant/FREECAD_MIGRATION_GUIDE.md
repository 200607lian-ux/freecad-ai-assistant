# FreeCAD 迁移开发指南

> **目标**：将 Blender AI 建模助手迁移到 FreeCAD，实现 STEP 格式建模和导出
> 
> **原项目**：基于 Blender + MCP + DeepSeek AI 的 Web 3D 建模系统  
> **新需求**：使用 FreeCAD MCP 插件替代 Blender，支持 STEP 格式

---

## 📋 目录

1. [现有架构概述](#现有架构概述)
2. [核心组件说明](#核心组件说明)
3. [迁移关键点](#迁移关键点)
4. [FreeCAD MCP 工具](#freecad-mcp-工具)
5. [开发步骤](#开发步骤)
6. [API 对照表](#api-对照表)

---

## 现有架构概述

### 三层架构

```
┌─────────────────────────────────────────────────────────────┐
│  前端层 (frontend/)                                          │
│  - index.html: 主界面（聊天 + 3D 预览 + 导出面板）           │
│  - app.js: WebSocket 通信 + Three.js 3D 预览器               │
│  - style.css: 橙白配色 UI                                    │
└─────────────────────────────────────────────────────────────┘
                    ↕ WebSocket (ws://localhost:8000/ws)
┌─────────────────────────────────────────────────────────────┐
│  后端层 (backend/)                                           │
│  - main.py: FastAPI 服务器 + WebSocket 路由                 │
│  - ai_agent.py: DeepSeek API 调用 + 代码生成                │
│  - blender_client.py: TCP Socket 连接 Blender MCP           │
└─────────────────────────────────────────────────────────────┘
                    ↕ TCP Socket (localhost:9876)
┌─────────────────────────────────────────────────────────────┐
│  建模引擎层 (Blender/FreeCAD)                                │
│  - MCP Server: 接收 JSON 命令，执行 Python 代码             │
│  - Python API: bpy (Blender) → FreeCAD API                  │
│  - 导出引擎: STL/OBJ/FBX/glTF → STEP/STL/IGES/等            │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **前端** | HTML/CSS/JS | 原生开发，无框架依赖 |
| | Three.js r128 | 3D 模型渲染（STL 加载） |
| | WebSocket | 实时双向通信 |
| **后端** | FastAPI | 异步 Web 框架 |
| | Python 3.9+ | 后端语言 |
| | OpenAI SDK | 调用 DeepSeek API |
| **AI** | DeepSeek-V4-Flash | 阿里云百炼平台 |
| | API Key | 环境变量 DASHSCOPE_API_KEY |
| **建模** | Blender 3.0+ | 原系统 → 改为 FreeCAD |
| | MCP Protocol | 命令通信协议 |

---

## 核心组件说明

### 1. 前端 (frontend/app.js)

**关键功能：**

```javascript
// WebSocket 连接管理
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => handleMessage(JSON.parse(event.data));

// Three.js 3D 预览器初始化
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer();
const controls = new THREE.OrbitControls(camera, renderer.domElement);

// STL 加载和显示
function loadSTLFromBase64(base64Data) {
    const loader = new THREE.STLLoader();
    const geometry = loader.parse(binaryData);
    geometry.rotateX(-Math.PI / 2);  // Blender Z-up → Three.js Y-up
    const mesh = new THREE.Mesh(geometry, material);
    scene.add(mesh);
}

// 导出功能（9种格式）
function exportModel(format) {
    ws.send(JSON.stringify({
        type: 'export_model',
        format: format,  // stl/obj/fbx/gltf/glb/ply/x3d/dae/abc
        selection_only: false
    }));
}
```

**迁移要点：**
- ✅ **保留**：WebSocket 通信、UI 布局、导出面板
- 🔄 **修改**：STL 加载器可能需要支持 STEP 格式（需要 STEP.js 或其他库）
- ➕ **新增**：STEP 格式的 3D 预览支持

---

### 2. 后端 (backend/main.py)

**FastAPI 核心代码：**

```python
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from ai_agent import AIAgent
from blender_client import BlenderClient

app = FastAPI()
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")

# 全局客户端实例
blender_client = BlenderClient(host='127.0.0.1', port=9876)
ai_agent = AIAgent(api_key=os.getenv('DASHSCOPE_API_KEY'))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # 连接 Blender
    blender_client.connect()
    
    while True:
        data = await websocket.receive_json()
        
        if data['type'] == 'chat':
            # AI 生成代码
            code = ai_agent.generate_code(data['content'])
            
            # 执行代码
            result = blender_client.execute_code(code)
            
            # 自动导出 STL 预览
            stl_data = blender_client.export_stl()
            await websocket.send_json({
                'type': 'stl_exported',
                'content': base64.b64encode(stl_data).decode('utf-8')
            })
        
        elif data['type'] == 'export_model':
            # 导出指定格式
            file_data = blender_client.export_format(data['format'])
            await websocket.send_json({
                'type': 'file_download',
                'content': base64.b64encode(file_data).decode('utf-8'),
                'filename': f'model.{data["format"]}'
            })
```

**迁移要点：**
- ✅ **保留**：FastAPI 框架、WebSocket 路由、文件服务
- 🔄 **修改**：`blender_client` → `freecad_client`
- 🔄 **修改**：导出格式列表（增加 STEP、IGES，可能移除 FBX/glTF）

---

### 3. AI 代理 (backend/ai_agent.py)

**DeepSeek API 调用：**

```python
from openai import OpenAI

class AIAgent:
    def __init__(self, api_key):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        self.model = "deepseek-v4-flash"
    
    def generate_code(self, user_input):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": user_input}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        return self.extract_code(response.choices[0].message.content)
    
    def get_system_prompt(self):
        return """
你是 Blender Python API 专家。

要求：
1. 只输出纯 Python 代码，不要任何解释
2. 只使用 bpy 模块
3. 代码必须完整可执行
4. 使用 try-except 处理错误

示例：
用户: "创建红色立方体"
你:
```python
import bpy
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
obj = bpy.context.active_object
mat = bpy.data.materials.new(name="Red")
mat.diffuse_color = (1, 0, 0, 1)
obj.data.materials.append(mat)
```
"""
```

**迁移要点：**
- ✅ **保留**：OpenAI SDK、API 调用结构、DeepSeek 模型
- 🔄 **修改**：System Prompt 从 "Blender Python 专家" → "FreeCAD Python 专家"
- 🔄 **修改**：示例代码从 `bpy` → FreeCAD API (`FreeCAD.ActiveDocument`)
- ✅ **保留**：环境变量 `DASHSCOPE_API_KEY`

---

### 4. Blender 客户端 (backend/blender_client.py)

**MCP 通信代码：**

```python
import socket
import json

class BlenderClient:
    def __init__(self, host='127.0.0.1', port=9876):
        self.host = host
        self.port = port
        self.socket = None
    
    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
    
    def send_command(self, cmd_type, params):
        command = {
            "type": cmd_type,
            "params": params
        }
        self.socket.sendall(json.dumps(command).encode('utf-8'))
        response = self._receive_response()
        return response
    
    def execute_code(self, code):
        return self.send_command("execute_code", {"code": code})
    
    def export_stl(self):
        response = self.send_command("export", {
            "format": "stl",
            "filepath": "/tmp/preview.stl"
        })
        with open("/tmp/preview.stl", "rb") as f:
            return f.read()
```

**迁移要点：**
- ✅ **保留**：Socket 连接逻辑、JSON 命令格式
- 🔄 **修改**：类名 `BlenderClient` → `FreeCADClient`
- 🔄 **修改**：命令参数适配 FreeCAD MCP 工具

---

## 迁移关键点

### 关键变更矩阵

| 组件 | 原实现 (Blender) | 新实现 (FreeCAD) | 难度 |
|------|------------------|------------------|------|
| **建模 API** | `bpy.ops.mesh.primitive_*` | `Part.makeBox()`, `Part.makeCylinder()` | 🟡 中 |
| **代码执行** | MCP `execute_code` | FreeCAD MCP `execute_code` | 🟢 低 |
| **导出格式** | STL/OBJ/FBX/glTF/GLB | **STEP**/IGES/STL/OBJ | 🟢 低 |
| **3D 预览** | STL → Three.js | STEP → ? (需调研) | 🔴 高 |
| **AI Prompt** | Blender Python 专家 | FreeCAD Python 专家 | 🟡 中 |

### 必须解决的问题

#### 1. STEP 格式 3D 预览

**问题**：Three.js 原生不支持 STEP 格式

**解决方案选项：**


**选项 A**：后端转换 STEP → STL  
```python
# FreeCAD 可以导出多种格式
def export_for_preview(self):
    # 先导出 STEP（给用户下载）
    step_data = self.export_step()
    
    # 再导出 STL（给 Three.js 预览）
    stl_data = self.export_stl()
    return step_data, stl_data
```

**选项 B**：使用 STEP.js 库（如果存在）  
- 调研是否有 JavaScript STEP 解析库
- 可能性能较差

**推荐**：选项 A，双格式导出

#### 2. FreeCAD Python API 差异

**Blender API 示例：**
```python
import bpy
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
obj = bpy.context.active_object
```

**FreeCAD API 对应：**
```python
import FreeCAD
import Part

doc = FreeCAD.ActiveDocument
box = Part.makeBox(10, 10, 10)
obj = doc.addObject("Part::Feature", "Box")
obj.Shape = box
doc.recompute()
```

**AI Prompt 需要更新**：提供 FreeCAD 的 Few-shot Examples

---

## FreeCAD MCP 工具

### 可用工具列表

根据 Kiro 配置，FreeCAD MCP 提供以下工具：

| 工具名 | 功能 | 对应 Blender 功能 |
|--------|------|-------------------|
| `mcp_freecad_create_document` | 创建文档 | 自动创建场景 |
| `mcp_freecad_create_object` | 创建对象 | `bpy.ops.mesh.primitive_*` |
| `mcp_freecad_edit_object` | 编辑对象属性 | 修改对象参数 |
| `mcp_freecad_delete_object` | 删除对象 | `bpy.ops.object.delete()` |
| `mcp_freecad_execute_code` | **执行 Python 代码** | **核心功能** |
| `mcp_freecad_get_view` | 获取视图截图 | 可选功能 |
| `mcp_freecad_get_objects` | 列出所有对象 | 场景信息 |
| `mcp_freecad_get_object` | 获取对象详情 | 对象查询 |
| `mcp_freecad_list_documents` | 列出文档 | 场景管理 |

### 核心工具：execute_code

**这是最重要的工具，等同于 Blender MCP 的 execute_code**

```python
# 调用方式（在 freecad_client.py 中）
def execute_code(self, code):
    """
    执行任意 FreeCAD Python 代码
    
    Args:
        code: FreeCAD Python 代码字符串
    
    Returns:
        执行结果
    """
    # 使用 FreeCAD MCP 工具
    result = mcp_freecad_execute_code(code=code)
    return result
```

**示例代码：**

```python
# 创建立方体
code = """
import FreeCAD
import Part

doc = FreeCAD.ActiveDocument
if not doc:
    doc = FreeCAD.newDocument("MyDoc")

box = Part.makeBox(10, 10, 10)
obj = doc.addObject("Part::Feature", "Box")
obj.Shape = box
obj.ViewObject.ShapeColor = (1.0, 0.0, 0.0)  # 红色
doc.recompute()
"""
```

---

## 开发步骤

### Phase 1: 后端适配（1-2天）

**步骤 1.1**：创建 `freecad_client.py`

```python
class FreeCADClient:
    """
    FreeCAD MCP 客户端
    复制 blender_client.py 的结构，修改为调用 FreeCAD MCP 工具
    """
    
    def __init__(self):
        # FreeCAD MCP 通过 Kiro Powers 调用，不需要 Socket
        pass
    
    def execute_code(self, code):
        """调用 mcp_freecad_execute_code"""
        # 实际实现中，通过 Kiro 的 MCP 工具调用
        return mcp_freecad_execute_code(code=code)
    
    def export_step(self, filepath="/tmp/model.step"):
        """导出 STEP 格式"""
        code = f"""
import FreeCAD
import Import

doc = FreeCAD.ActiveDocument
if doc and doc.Objects:
    Import.export(doc.Objects, "{filepath}")
"""
        self.execute_code(code)
        with open(filepath, 'rb') as f:
            return f.read()
    
    def export_stl(self, filepath="/tmp/preview.stl"):
        """导出 STL 用于预览"""
        code = f"""
import FreeCAD
import Mesh

doc = FreeCAD.ActiveDocument
if doc and doc.Objects:
    # 合并所有对象
    shapes = [obj.Shape for obj in doc.Objects if hasattr(obj, 'Shape')]
    if shapes:
        import Part
        compound = Part.makeCompound(shapes)
        Mesh.export([doc.Objects[0]], "{filepath}")
"""
        self.execute_code(code)
        with open(filepath, 'rb') as f:
            return f.read()
```

**步骤 1.2**：修改 `main.py`

```python
# 修改导入
from freecad_client import FreeCADClient

# 修改初始化
freecad_client = FreeCADClient()

# 修改导出格式列表
SUPPORTED_FORMATS = ['step', 'stp', 'iges', 'igs', 'stl', 'obj', 'brep']
```

**步骤 1.3**：修改 `ai_agent.py` 的 System Prompt

```python
def get_system_prompt(self):
    return """
你是 FreeCAD Python API 专家。

要求：
1. 只输出纯 Python 代码，不要任何解释
2. 使用 FreeCAD、Part、Sketcher 等模块
3. 代码必须完整可执行
4. 使用 try-except 处理错误
5. 确保文档存在（FreeCAD.ActiveDocument）

FreeCAD API 基础：
- 创建文档: FreeCAD.newDocument("Doc")
- 获取文档: FreeCAD.ActiveDocument
- 创建对象: doc.addObject("Part::Feature", "Name")
- 设置形状: obj.Shape = Part.makeBox(10, 10, 10)
- 刷新视图: doc.recompute()

示例：
用户: "创建一个红色立方体"
你:
```python
import FreeCAD
import Part

doc = FreeCAD.ActiveDocument
if not doc:
    doc = FreeCAD.newDocument("MyDoc")

box = Part.makeBox(10, 10, 10)
obj = doc.addObject("Part::Feature", "Box")
obj.Shape = box
obj.ViewObject.ShapeColor = (1.0, 0.0, 0.0)
doc.recompute()
```

用户: "创建一个蓝色圆柱体"
你:
```python
import FreeCAD
import Part

doc = FreeCAD.ActiveDocument
cylinder = Part.makeCylinder(5, 10)
obj = doc.addObject("Part::Feature", "Cylinder")
obj.Shape = cylinder
obj.ViewObject.ShapeColor = (0.0, 0.0, 1.0)
obj.Placement.Base = FreeCAD.Vector(20, 0, 0)
doc.recompute()
```
"""
```

---

### Phase 2: 前端适配（1天）

**步骤 2.1**：修改导出格式列表

```javascript
// frontend/app.js
const exportFormats = [
    { value: 'step', label: 'STEP (通用CAD格式)', icon: '🔧' },
    { value: 'iges', label: 'IGES (CAD交换格式)', icon: '🔄' },
    { value: 'stl', label: 'STL (3D打印)', icon: '🖨️' },
    { value: 'obj', label: 'OBJ (通用3D)', icon: '📦' },
    { value: 'brep', label: 'BREP (边界表示)', icon: '📐' }
];
```

**步骤 2.2**：保留 Three.js STL 预览

```javascript
// 不需要修改，后端会自动导出 STL 用于预览
function loadSTLFromBase64(base64Data) {
    // 保持不变
}
```

**步骤 2.3**：更新 UI 文案

```javascript
// 修改标题
document.title = "FreeCAD AI 建模助手";

// 修改快捷按钮示例
const quickButtons = [
    { text: "🟥 创建立方体", prompt: "创建一个红色立方体" },
    { text: "🔵 创建圆柱", prompt: "创建一个蓝色圆柱体" },
    { text: "🗑️ 清空文档", prompt: "删除所有对象" }
];
```

---

### Phase 3: 测试验证（1天）

**测试清单：**

- [ ] FreeCAD MCP 连接正常
- [ ] AI 生成 FreeCAD 代码正确
- [ ] 代码执行成功
- [ ] STL 预览正常显示
- [ ] STEP 格式导出成功
- [ ] 其他格式导出正常
- [ ] 错误处理正常
- [ ] WebSocket 断线重连

**测试用例：**

```
1. 基础几何体
   "创建一个红色立方体，边长为10"
   "在位置(20, 0, 0)创建一个蓝色圆柱体"

2. 复杂形状
   "创建一个球体和立方体的并集"
   "创建一个环形体"

3. 导出功能
   - 导出 STEP 格式
   - 导出 STL 格式
   - 导出 IGES 格式

4. 错误处理
   "导出一个空场景"（应该提示错误）
   断开 FreeCAD 连接（应该提示重连）
```

---

## API 对照表

### Blender vs FreeCAD 常用操作

| 操作 | Blender API | FreeCAD API |
|------|-------------|-------------|
| **创建立方体** | `bpy.ops.mesh.primitive_cube_add()` | `Part.makeBox(10, 10, 10)` |
| **创建球体** | `bpy.ops.mesh.primitive_uv_sphere_add()` | `Part.makeSphere(5)` |
| **创建圆柱** | `bpy.ops.mesh.primitive_cylinder_add()` | `Part.makeCylinder(5, 10)` |
| **获取活动对象** | `bpy.context.active_object` | `FreeCADGui.Selection.getSelection()[0]` |
| **设置位置** | `obj.location = (x, y, z)` | `obj.Placement.Base = Vector(x, y, z)` |
| **设置颜色** | `mat.diffuse_color = (r, g, b, 1)` | `obj.ViewObject.ShapeColor = (r, g, b)` |
| **删除对象** | `bpy.ops.object.delete()` | `doc.removeObject(obj.Name)` |
| **导出 STL** | `bpy.ops.export_mesh.stl()` | `Mesh.export([obj], filepath)` |
| **导出 STEP** | ❌ 不支持 | ✅ `Import.export([obj], filepath)` |

### 导出格式对照

| 格式 | Blender 支持 | FreeCAD 支持 | 用途 |
|------|--------------|--------------|------|
| **STEP** | ❌ | ✅ | **CAD 标准格式** |
| **IGES** | ❌ | ✅ | CAD 交换格式 |
| **STL** | ✅ | ✅ | 3D 打印 |
| **OBJ** | ✅ | ✅ | 通用 3D |
| **FBX** | ✅ | ❌ | 游戏/动画 |
| **glTF** | ✅ | ❌ | Web3D |
| **BREP** | ❌ | ✅ | FreeCAD 原生格式 |

---

## 快速启动检查清单

### 环境准备

- [ ] Python 3.9+ 已安装
- [ ] FreeCAD 已安装并配置 MCP 插件
- [ ] 已安装后端依赖: `pip install -r backend/requirements.txt`
- [ ] 已设置 API Key: `$env:DASHSCOPE_API_KEY = "your-key"`
- [ ] FreeCAD MCP 服务已启动（端口 9876 或其他）

### 文件修改清单


**必须修改：**
- [ ] `backend/freecad_client.py` - 新建，替代 blender_client.py
- [ ] `backend/main.py` - 导入 FreeCADClient，修改导出格式
- [ ] `backend/ai_agent.py` - 更新 System Prompt 为 FreeCAD 专家

**可选修改：**
- [ ] `frontend/index.html` - 修改标题为 "FreeCAD AI 建模助手"
- [ ] `frontend/app.js` - 更新导出格式列表和快捷按钮
- [ ] `frontend/style.css` - 可选：修改配色方案

**保持不变：**
- ✅ `frontend/app.js` - WebSocket 通信逻辑
- ✅ `frontend/app.js` - Three.js 3D 预览器
- ✅ `backend/main.py` - FastAPI 框架结构
- ✅ `backend/ai_agent.py` - OpenAI SDK 调用逻辑

---

## 核心代码模板

### freecad_client.py 完整模板

```python
"""
FreeCAD MCP 客户端
用于与 FreeCAD 通信，执行建模代码和导出模型
"""

class FreeCADClient:
    def __init__(self):
        self.connected = False
    
    def connect(self):
        """检查 FreeCAD 连接"""
        try:
            # 通过 Kiro MCP 调用测试连接
            result = self.execute_code("import FreeCAD; print('Connected')")
            self.connected = True
            return True
        except Exception as e:
            print(f"FreeCAD 连接失败: {e}")
            self.connected = False
            return False
    
    def execute_code(self, code: str) -> dict:
        """
        执行 FreeCAD Python 代码
        
        Args:
            code: FreeCAD Python 代码字符串
        
        Returns:
            {'status': 'ok'/'error', 'result': '...', 'message': '...'}
        """
        try:
            # 调用 Kiro 的 FreeCAD MCP 工具
            # 实际实现中需要通过 Kiro Powers API 调用
            result = mcp_freecad_execute_code(code=code)
            return {
                'status': 'ok',
                'result': result,
                'message': '代码执行成功'
            }
        except Exception as e:
            return {
                'status': 'error',
                'result': None,
                'message': str(e)
            }
    
    def get_scene_info(self) -> dict:
        """获取场景信息"""
        code = """
import FreeCAD
doc = FreeCAD.ActiveDocument
if doc:
    print(f"对象数量: {len(doc.Objects)}")
    for obj in doc.Objects:
        print(f"- {obj.Label} ({obj.TypeId})")
else:
    print("没有活动文档")
"""
        return self.execute_code(code)
    
    def export_step(self, selection_only=False) -> bytes:
        """
        导出 STEP 格式
        
        Args:
            selection_only: 是否仅导出选中对象
        
        Returns:
            STEP 文件的二进制数据
        """
        filepath = "/tmp/export.step"
        
        code = f"""
import FreeCAD
import Import

doc = FreeCAD.ActiveDocument
if not doc or not doc.Objects:
    raise Exception("场景中没有对象可导出")

{"objects = FreeCADGui.Selection.getSelection()" if selection_only else "objects = doc.Objects"}
if not objects:
    raise Exception("没有选中的对象")

Import.export(objects, "{filepath}")
print(f"STEP 导出成功: {filepath}")
"""
        
        result = self.execute_code(code)
        if result['status'] == 'ok':
            with open(filepath, 'rb') as f:
                return f.read()
        else:
            raise Exception(result['message'])
    
    def export_stl(self, selection_only=False) -> bytes:
        """导出 STL 格式用于 3D 预览"""
        filepath = "/tmp/preview.stl"
        
        code = f"""
import FreeCAD
import Mesh

doc = FreeCAD.ActiveDocument
if not doc or not doc.Objects:
    raise Exception("场景中没有对象")

{"objects = FreeCADGui.Selection.getSelection()" if selection_only else "objects = doc.Objects"}
if not objects:
    raise Exception("没有对象可导出")

# 导出 STL
Mesh.export(objects, "{filepath}")
print(f"STL 导出成功: {filepath}")
"""
        
        result = self.execute_code(code)
        if result['status'] == 'ok':
            with open(filepath, 'rb') as f:
                return f.read()
        else:
            raise Exception(result['message'])
    
    def export_format(self, format_name: str, selection_only=False) -> bytes:
        """
        导出指定格式
        
        Args:
            format_name: 格式名称 (step/iges/stl/obj/brep)
            selection_only: 是否仅导出选中对象
        
        Returns:
            文件的二进制数据
        """
        format_map = {
            'step': self.export_step,
            'stp': self.export_step,
            'iges': self.export_iges,
            'igs': self.export_iges,
            'stl': self.export_stl,
            'obj': self.export_obj,
            'brep': self.export_brep
        }
        
        if format_name.lower() not in format_map:
            raise Exception(f"不支持的格式: {format_name}")
        
        return format_map[format_name.lower()](selection_only)
    
    def export_iges(self, selection_only=False) -> bytes:
        """导出 IGES 格式"""
        # 类似 export_step，修改文件扩展名
        pass
    
    def export_obj(self, selection_only=False) -> bytes:
        """导出 OBJ 格式"""
        # 实现 OBJ 导出逻辑
        pass
    
    def export_brep(self, selection_only=False) -> bytes:
        """导出 BREP 格式（FreeCAD 原生格式）"""
        # 实现 BREP 导出逻辑
        pass
```

---

## 常见问题预判

### Q1: FreeCAD MCP 如何连接？

**A**: FreeCAD MCP 通过 Kiro 的 Powers 系统集成，不需要手动 Socket 连接。

**步骤：**
1. 确保 Kiro 配置中已添加 FreeCAD MCP 服务器
2. 在代码中直接调用 `mcp_freecad_*` 工具
3. Kiro 会自动处理与 FreeCAD 的通信

### Q2: STEP 格式如何在浏览器预览？

**A**: 推荐双格式策略

```python
# 自动导出时
async def auto_export_preview(websocket):
    # 导出 STL 用于预览（Three.js 支持）
    stl_data = freecad_client.export_stl()
    await websocket.send_json({
        'type': 'stl_exported',
        'content': base64.b64encode(stl_data).decode('utf-8'),
        'auto': True
    })

# 用户主动导出时
async def user_export(websocket, format_name):
    # 导出用户请求的格式（包括 STEP）
    file_data = freecad_client.export_format(format_name)
    await websocket.send_json({
        'type': 'file_download',
        'content': base64.b64encode(file_data).decode('utf-8'),
        'filename': f'model.{format_name}'
    })
```

### Q3: AI 生成的代码不正确怎么办？

**A**: 优化 Few-shot Examples

在 System Prompt 中添加更多 FreeCAD 示例：

```python
示例 1: 创建立方体
用户: "创建一个边长为10的红色立方体"
你:
```python
import FreeCAD
import Part
doc = FreeCAD.ActiveDocument or FreeCAD.newDocument()
box = Part.makeBox(10, 10, 10)
obj = doc.addObject("Part::Feature", "Box")
obj.Shape = box
obj.ViewObject.ShapeColor = (1.0, 0.0, 0.0)
doc.recompute()
```

示例 2: 创建圆柱体
用户: "在位置(20, 0, 0)创建一个蓝色圆柱体，半径5，高度10"
你:
```python
import FreeCAD
import Part
doc = FreeCAD.ActiveDocument or FreeCAD.newDocument()
cylinder = Part.makeCylinder(5, 10)
obj = doc.addObject("Part::Feature", "Cylinder")
obj.Shape = cylinder
obj.ViewObject.ShapeColor = (0.0, 0.0, 1.0)
obj.Placement.Base = FreeCAD.Vector(20, 0, 0)
doc.recompute()
```
```

---

## 总结

### 迁移工作量估算

| 任务 | 工作量 | 优先级 |
|------|--------|--------|
| 创建 `freecad_client.py` | 4小时 | 🔴 高 |
| 修改 `ai_agent.py` Prompt | 2小时 | 🔴 高 |
| 修改 `main.py` 导出逻辑 | 2小时 | 🔴 高 |
| 更新前端 UI 文案 | 1小时 | 🟡 中 |
| 测试和调试 | 4小时 | 🔴 高 |
| **总计** | **~2天** | - |

### 核心保留内容

✅ **完全保留（不需要修改）：**
- FastAPI 框架和 WebSocket 通信
- Three.js 3D 预览器（STL 加载）
- OpenAI SDK 和 DeepSeek API 调用
- 前端 UI 布局和交互逻辑
- 环境变量配置方式

🔄 **需要修改的部分：**
- Blender 客户端 → FreeCAD 客户端
- AI System Prompt（Blender API → FreeCAD API）
- 导出格式列表（增加 STEP、IGES）
- UI 文案（Blender → FreeCAD）

### 给下一位 AI 的建议

1. **先看这份文档**：理解现有架构和技术栈
2. **保留前端**：Three.js 预览器已经很完善，只需修改导出格式
3. **保留 AI 调用**：DeepSeek API 已验证好用，只需更新 Prompt
4. **重点在后端**：核心工作是实现 `freecad_client.py`
5. **参考原代码**：`blender_client.py` 是很好的模板
6. **测试驱动**：先实现基础功能，再添加复杂特性

---

**文档版本**: 1.0  
**创建日期**: 2024年1月  
**适用项目**: Blender AI Assistant → FreeCAD AI Assistant 迁移

---

**附录：关键文件清单**

```
必读文件:
├── PROJECT_DOCUMENTATION.md     # 原项目完整文档
├── FREECAD_MIGRATION_GUIDE.md   # 本迁移指南（当前文件）
├── backend/blender_client.py    # 参考这个实现 freecad_client.py
├── backend/ai_agent.py          # AI 代理，需修改 Prompt
└── frontend/app.js              # WebSocket 和 Three.js，了解交互流程

待创建文件:
└── backend/freecad_client.py    # 核心新文件

待修改文件:
├── backend/main.py              # 导入和初始化部分
├── backend/ai_agent.py          # System Prompt 部分
└── frontend/app.js              # 导出格式列表（可选）
```
