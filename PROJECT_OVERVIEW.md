# FreeCAD AI 助手 - 项目介绍

## 项目概述

**FreeCAD AI 助手**是一个基于自然语言交互的 3D CAD 建模辅助系统。用户通过中文对话描述建模需求，AI 自动生成并执行 FreeCAD Python 代码，实时在浏览器中展示 3D 模型预览，并支持导出多种 CAD 格式文件。

---

## 核心功能

| 功能 | 说明 |
|------|------|
| **自然语言建模** | 用中文描述需求，AI 自动生成 FreeCAD 代码 |
| **实时 3D 预览** | 基于 Three.js 的浏览器端模型展示 |
| **多格式导出** | 支持 STEP、STL、OBJ、IGES、BREP、CSV |
| **对话式交互** | WebSocket 实时通信，状态即时反馈 |
| **智能安全约束** | AI 提示词内置规则，防止 FreeCAD 崩溃 |
| **自动端口管理** | 启动器自动检测并释放占用端口 |

---

## 技术栈

### 前端
- **HTML5 + CSS3 + JavaScript**（原生，无框架）
- **Three.js r128** - 3D 渲染引擎
- **STLLoader** - STL 模型加载
- **OrbitControls** - 相机轨道控制

### 后端
- **Python 3.13**
- **FastAPI** - Web 框架
- **WebSocket** - 实时双向通信
- **Uvicorn** - ASGI 服务器

### AI 引擎
- **阿里云百炼 DeepSeek-V4-Flash**
- **OpenAI 兼容接口**
- **DashScope API**

### CAD 集成
- **FreeCAD**（桌面软件）
- **XML-RPC / Socket** 通信
- **Python 宏执行**

---

## 系统架构

```
┌─────────────────┐     WebSocket      ┌─────────────────┐
│   前端 (浏览器)   │ ◄────────────────► │   后端 (Python)  │
│                 │                    │                 │
│ • HTML/CSS/JS   │                    │ • FastAPI       │
│ • Three.js 3D   │                    │ • AI 代理       │
│ • 聊天界面      │                    │ • FreeCAD 客户端 │
└─────────────────┘                    └────────┬────────┘
                                               │
                                               │ XML-RPC / Socket
                                               │
                                        ┌──────▼──────┐
                                        │   FreeCAD   │
                                        │  (桌面软件)  │
                                        │             │
                                        │ • Python 控制台│
                                        │ • 3D 建模内核 │
                                        │ • 导出器     │
                                        └─────────────┘
```

---

## 项目流程详解

### 完整交互流程

```
用户输入指令
    │
    ▼
┌─────────────────┐
│ 1. 前端发送消息  │  ──►  WebSocket: {"type": "chat", "content": "创建红色立方体"}
│    到后端       │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ 2. 后端 AI 思考  │  ──►  调用 DeepSeek-V4-Flash 生成 FreeCAD Python 代码
│                │
│ • 系统提示词包含 │      示例输出：
│   FreeCAD API   │      import FreeCAD
│   规则和安全约束 │      import Part
│                │      doc = FreeCAD.newDocument("MyDoc")
│ • 温度 0.3      │      box = doc.addObject("Part::Box", "Box")
│ • 最大 1500 tokens│    box.Length = 10
└─────────────────┘      ...
    │
    ▼
┌─────────────────┐
│ 3. 后端执行代码  │  ──►  通过 RPC 发送代码到 FreeCAD
│                │
│ • 超时 120 秒   │      FreeCAD 在 GUI 线程执行 Python 代码
│ • 线程池执行    │      创建几何对象、设置颜色、调整位置
│ • 异常捕获    │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ 4. 获取截图     │  ──►  从 FreeCAD 获取等轴测视图截图（PNG）
│   (可选)       │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ 5. 导出 STL     │  ──►  将 FreeCAD 模型导出为 STL 格式
│   用于 3D 预览  │
│                │      • 获取活动文档名称
│ • 检查文档非空  │      • 调用 export_document(doc_name, path, "stl")
│ • 导出到临时文件│      • 读取文件 → Base64 编码
│ • Base64 编码   │      • 发送 WebSocket 消息到前端
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ 6. 前端接收并   │  ──►  WebSocket: {"type": "stl_exported", "content": "base64..."}
│   展示 3D 模型  │
│                │
│ • 隐藏占位符    │      loadSTLFromBase64(base64Data)
│ • 解析 STL     │      ├── 解码 Base64
│ • 创建 Three.js │      ├── STLLoader.parse()
│   网格         │      ├── 旋转坐标系（Z→Y）
│ • 调整相机     │      ├── 居中并上移
│ • 渲染场景     │      └── 添加到场景
└─────────────────┘
    │
    ▼
用户看到 3D 模型
```

---

## 详细流程步骤

### 步骤 1：启动服务

```bash
# 方式一：使用启动器（推荐）
python launcher.py

# 方式二：直接启动
python -m backend.main_freecad_ai
```

**启动器功能**：
1. 检查端口 8001 是否可用
2. 如被占用，查找并终止占用进程
3. 设置环境变量 `FREECAD_AI_PORT`
4. 启动 Uvicorn 服务器
5. 打印服务地址：`http://localhost:8001`

---

### 步骤 2：启动 FreeCAD 并运行 RPC Server

1. 打开 FreeCAD 软件
2. 执行宏：`freecad_rpc_server.FCMacro`
3. 确认控制台输出：`RPC Server started on port 9877`

---

### 步骤 3：打开前端页面

1. 浏览器访问：`http://localhost:8001`
2. 或打开 `frontend/index.html`（本地文件模式）
3. 页面自动连接 WebSocket

**前端状态栏显示**：
- 🟢 WebSocket 已连接
- 🟢 FreeCAD 已连接
- 🟢 AI 已启用

---

### 步骤 4：发送建模指令

**用户输入示例**：
```
创建一个红色的立方体，边长 50mm
```

**前端发送**：
```json
{
  "type": "chat",
  "content": "创建一个红色的立方体，边长 50mm"
}
```

---

### 步骤 5：AI 生成代码

**后端处理**：
1. 调用 `ai_agent.generate_response()`
2. 拼接系统提示词 + 用户输入
3. 发送给 DeepSeek-V4-Flash
4. 解析返回的代码

**AI 生成的代码示例**：
```python
import FreeCAD
import Part

doc = FreeCAD.ActiveDocument
if not doc:
    doc = FreeCAD.newDocument("MyDoc")

# 删除旧对象
for obj in list(doc.Objects):
    doc.removeObject(obj.Name)

# 创建红色立方体
box = doc.addObject("Part::Box", "RedCube")
box.Length = 50
box.Width = 50
box.Height = 50
box.Label = "红色立方体"

# 设置颜色
box.ViewObject.ShapeColor = (1.0, 0.0, 0.0, 1.0)

doc.recompute()
print("已创建红色立方体，边长 50mm")
```

---

### 步骤 6：执行代码并导出

**后端执行流程**：

```
execute_code(code) ──► FreeCAD RPC ──► GUI 线程执行
                                              │
                                              ▼
                                    对象创建成功
                                              │
                                              ▼
                                    get_screenshot() ──► PNG 截图
                                              │
                                              ▼
                                    export_document("stl") ──► STL 文件
                                              │
                                              ▼
                                    读取文件 → Base64 → 发送前端
```

---

### 步骤 7：前端 3D 展示

**Three.js 渲染流程**：

```javascript
// 1. 接收消息
{"type": "stl_exported", "content": "base64encodeddata..."}

// 2. 解码 Base64
const binaryString = atob(base64Data);
const bytes = new Uint8Array(binaryString.length);
for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
}

// 3. 解析 STL
const loader = new THREE.STLLoader();
let geometry = loader.parse(bytes.buffer);

// 4. 坐标系转换（FreeCAD Z 向上 → Three.js Y 向上）
geometry.rotateX(-Math.PI / 2);

// 5. 创建材质和网格
const material = new THREE.MeshPhongMaterial({
    color: 0xff8c42,
    specular: 0x444444,
    shininess: 100
});
const mesh = new THREE.Mesh(geometry, material);

// 6. 居中并上移
const center = new THREE.Vector3();
geometry.boundingBox.getCenter(center);
mesh.position.sub(center);
mesh.position.y += maxDim * 0.15;

// 7. 添加到场景并渲染
scene.add(mesh);
```

---

## 文件结构

```
freecad-ai-assistant/
│
├── frontend/                 # 前端代码
│   ├── index.html             # 主页面（聊天 + 3D 预览）
│   ├── threejs_viewer.js      # Three.js 3D 渲染
│   ├── style.css              # 样式（内嵌在 index.html）
│   ├── app.js                 # 前端逻辑（内嵌在 index.html）
│   └── test_*.html            # 测试页面
│
├── backend/                   # 后端代码
│   ├── main_freecad_ai.py     # FastAPI 主服务 + WebSocket
│   ├── ai_agent_freecad.py    # AI 代码生成模块
│   ├── freecad_rpc_client.py  # FreeCAD RPC 客户端
│   ├── freecad_client.py      # Socket 客户端（备用）
│   └── requirements.txt       # Python 依赖
│
├── freecad_socket_server.FCMacro  # FreeCAD 宏（Socket 服务器）
├── freecad_rpc_server.FCMacro     # FreeCAD 宏（RPC 服务器）
│
├── launcher.py                # 启动器（端口管理 + 自动启动）
├── start.bat                  # Windows 启动脚本
├── start_ai.bat               # AI 模式启动脚本
│
├── README.md                  # 项目说明
├── TROUBLESHOOTING.md         # 故障排查指南
├── FREECAD_MIGRATION_GUIDE.md # FreeCAD 迁移指南
└── PROJECT_STATUS.md          # 项目状态
```

---

## 关键技术细节

### 1. 坐标系转换

| 系统 | 向上方向 | 坐标系 |
|------|---------|--------|
| FreeCAD | Z 轴 | 右手坐标系 |
| Three.js | Y 轴 | 右手坐标系 |

**转换代码**：
```javascript
geometry.rotateX(-Math.PI / 2);  // Z→Y 转换
```

### 2. AI 安全约束

系统提示词中的关键规则：
- 修改前判断 `obj.TypeId`
- 优先修改参数，不直接替换 `.Shape`
- 严禁给 `PartDesign::Body` 等类型赋值 `.Shape`
- 复杂对象删除重建而不是修改
- 所有修改后调用 `doc.recompute()`

### 3. 超时配置

| 操作 | 超时时间 | 位置 |
|------|---------|------|
| AI 代码执行 | 120 秒 | `main_freecad_ai.py` |
| 截图获取 | 30 秒 | `main_freecad_ai.py` |
| 文档查询 | 30 秒 | `main_freecad_ai.py` |
| 导出执行 | 120 秒 | `main_freecad_ai.py` |
| FreeCAD GUI 线程 | 90 秒 | FreeCAD 内部限制 |

### 4. 通信协议

**WebSocket 消息类型**：

| 类型 | 方向 | 说明 |
|------|------|------|
| `chat` | 前端→后端 | 用户发送指令 |
| `status` | 后端→前端 | 状态更新（思考中、执行中...） |
| `response` | 后端→前端 | AI 成功响应 |
| `code` | 后端→前端 | 生成的代码（已隐藏） |
| `screenshot` | 后端→前端 | 截图数据（已废弃） |
| `stl_exported` | 后端→前端 | STL Base64 数据 |
| `export` | 双向 | 导出请求/结果 |
| `error` | 后端→前端 | 错误信息 |
| `scene_info` | 双向 | 场景信息查询/更新 |

---

## 使用场景

### 场景 1：快速原型设计
用户："创建一个 100x50x30mm 的蓝色底座，上面放一个直径 20mm 的圆柱"
→ AI 生成代码 → 执行 → 3D 展示 → 导出 STEP 给工厂加工

### 场景 2：参数化修改
用户："把刚才的底座高度改成 40mm"
→ AI 识别现有对象 → 修改参数 → 重新导出 → 更新预览

### 场景 3：复杂装配
用户："生成一台电脑显示器，有底座、支架和屏幕"
→ AI 分部件创建 → 调整位置和朝向 → 组合展示

---

## 未来扩展方向

1. **语音输入**：集成语音识别，口述建模需求
2. **图片理解**：上传草图，AI 识别并生成 3D 模型
3. **版本管理**：保存建模历史，支持撤销/重做
4. **协作编辑**：多用户同时查看和修改模型
5. **云端渲染**：大型模型云端渲染，前端仅显示结果
6. **更多格式**：支持 3MF、AMF、PLY 等 3D 打印格式

---

## 项目团队与贡献

**核心开发者**：基于 FreeCAD + DeepSeek 的开源社区项目
**技术贡献**：AI 提示词工程、FreeCAD API 封装、Three.js 渲染优化
**设计目标**：降低 CAD 建模门槛，让非专业用户也能快速创建 3D 模型

---

## 许可证

本项目采用 MIT 许可证开源，欢迎贡献代码和提出改进建议。
