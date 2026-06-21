# FreeCAD AI 助手 — 技术实现与问题排查深度解析

> 本文档面向开发者与部署运维人员，系统梳理项目架构、核心技术实现路径，以及生产环境中高频出现的问题与根治方案。

---

## 一、项目结构

```
freecad-ai-assistant/
│
├── frontend/                          # 前端展示层
│   ├── index.html                     # 主页面：聊天面板 + 3D 预览面板
│   ├── threejs_viewer.js              # Three.js 3D 渲染核心（STL 加载、场景控制）
│   ├── style.css                      # 样式表（暗色主题、响应式布局）
│   └── test_*.html                    # 功能测试页（坐标系、Three.js 独立测试）
│
├── backend/                           # 后端服务层
│   ├── main_freecad_ai.py             # FastAPI 主服务：WebSocket 路由、消息分发、导出调度
│   ├── ai_agent_freecad.py            # AI 代理：DeepSeek 调用、系统提示词工程、意图解析
│   ├── freecad_rpc_client.py          # FreeCAD RPC 客户端（XML-RPC 通信、代码执行、截图、导出）
│   ├── freecad_client.py              # Socket 备用客户端（TCP 直连，降级方案）
│   └── requirements.txt               # Python 依赖清单
│
├── freecad_socket_server.FCMacro      # FreeCAD 宏：Socket 服务器端（监听 9877 端口）
├── freecad_rpc_server.FCMacro         # FreeCAD 宏：RPC 服务器端（XML-RPC 服务）
│
├── launcher.py                        # 启动器：端口检测、进程清理、服务启动
├── start.bat / start_ai.bat           # Windows 快捷启动脚本
│
├── README.md                          # 项目快速开始指南
├── PROJECT_OVERVIEW.md                # 项目全景介绍（架构、流程、扩展）
└── TROUBLESHOOTING.md                 # 故障排查速查手册
```

---

## 二、技术实现流程图与核心步骤

### 2.1 整体数据流架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              用户交互层（前端）                               │
│  ┌──────────────┐    WebSocket    ┌──────────────────────────────────────┐  │
│  │  聊天输入框   │ ◄──────────────►│  Three.js 3D 预览区（模型展示）      │  │
│  │  快捷按钮    │   实时双向通信    │  - STLLoader 解析                    │  │
│  │  状态栏     │                  │  - OrbitControls 轨道控制             │  │
│  └──────────────┘                  │  - 自动居中 / 上移 / 坐标系转换       │  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              业务逻辑层（后端）                               │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────────┐  │
│  │  FastAPI WebSocket │───►│   AI Agent 模块   │───►│  FreeCAD RPC Client  │  │
│  │  - 消息路由分发    │    │  - 意图解析       │    │  - execute_code()    │  │
│  │  - 状态广播       │    │  - 系统提示词工程  │    │  - export_document() │  │
│  │  - 超时管控       │    │  - DeepSeek API   │    │  - get_screenshot()  │  │
│  └──────────────────┘    └──────────────────┘    └──────────────────────┘  │
│           │                                               │                 │
│           │  异步线程池（run_in_executor）                 │                 │
│           ▼                                               ▼                 │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                         导出调度器（handle_export）                   │  │
│  │  - 文档非空检测  →  格式映射  →  临时文件生成  →  Base64 编码  →  推送 │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ XML-RPC / Socket（端口 9877）
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CAD 内核层（FreeCAD）                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  FreeCAD GUI 线程（Python 控制台执行）                               │  │
│  │  - Part 模块：几何体创建（Box、Cylinder、Sphere...）                  │  │
│  │  - Import 模块：STEP / IGES / BREP 导出                             │  │
│  │  - Mesh 模块：STL / OBJ 导出                                        │  │
│  │  - 视图渲染：等轴测 / 前视图 / 俯视图截图                              │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 核心五步技术实现（按项目制作顺序）

#### Step 1 — 搭建基础通信链路（FreeCAD ↔ 后端）

**技术要点**：
- **通信协议选型**：XML-RPC（主用）/ Socket（备用）
- **FreeCAD 宏开发**：`freecad_rpc_server.FCMacro` 在 FreeCAD 内部启动 XML-RPC 服务器，监听 127.0.0.1:9877
- **Python 客户端封装**：`freecad_rpc_client.py` 封装 `execute_code()`、`export_document()`、`get_screenshot()` 等原子操作
- **连接健康检查**：`health_check()` + `ping()` 确保链路可用

**关键代码片段**：
```python
# backend/freecad_rpc_client.py
class FreeCADRPCClient:
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 9877
        self.connected = False
    
    def connect(self) -> bool:
        result = self._get_server().ping()
        if result:
            self.connected = True
            print(f"[OK] 已连接到 FreeCAD RPC 服务器")
        return self.connected
    
    def execute_code(self, code: str) -> Dict[str, Any]:
        # 在 FreeCAD GUI 线程同步执行 Python 代码
        result = self._get_server().execute_code(code)
        return result
```

**制作顺序意义**：这是整个项目的地基。没有稳定的通信链路，后续 AI 生成代码无法执行，3D 预览也无数据源。

---

#### Step 2 — 构建 WebSocket 实时通信框架（前端 ↔ 后端）

**技术要点**：
- **FastAPI WebSocket**：`@app.websocket("/ws")` 建立持久连接，支持全双工通信
- **消息类型系统**：定义 `chat`/`status`/`response`/`code`/`stl_exported`/`export`/`error`/`scene_info` 等消息类型
- **状态广播机制**：后端主动推送「AI 思考中...」「FreeCAD 执行中...」等状态，前端实时更新 UI
- **自动重连**：前端断开 5 秒后自动尝试重连，最多 5 次

**关键代码片段**：
```python
# backend/main_freecad_ai.py
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    conversation_history = []
    
    while True:
        data = await websocket.receive_text()
        message = json.loads(data)
        msg_type = message.get("type", "")
        
        if msg_type == "chat":
            await handle_ai_chat(websocket, user_input, conversation_history)
        elif msg_type == "export":
            await handle_export(websocket, message)
        elif msg_type == "export_stl":
            await handle_export(websocket, {"format": "stl", "preview": True})
```

**制作顺序意义**：建立前后端实时通道，为后续 AI 对话和 3D 预览推送提供基础设施。

---

#### Step 3 — 集成 AI 大模型实现自然语言到代码的转换（AI Agent）

**技术要点**：
- **模型选型**：阿里云百炼 DeepSeek-V4-Flash（通过 DashScope OpenAI 兼容接口调用）
- **系统提示词工程**：560+ 行中文提示词，包含 12 条硬规则（安全约束、API 规范、视图方向）
- **少样本学习（Few-shot）**：13 个完整输入/输出示例覆盖常见场景
- **温度参数**：`temperature=0.3`（低随机性，确保代码生成确定性）

**关键代码片段**：
```python
# backend/ai_agent_freecad.py
completion = self.client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[
        {'role': 'system', 'content': self.system_prompt},  # 560+ 行规则
        {'role': 'user', 'content': user_message}
    ],
    temperature=0.3,
    max_tokens=1500
)
```

**制作顺序意义**：在通信链路稳定后，引入 AI 作为「翻译器」，将用户自然语言转化为 FreeCAD 可执行的 Python 代码，这是项目的核心价值所在。

---

#### Step 4 — 异步代码执行与导出调度（后端执行引擎）

**技术要点**：
- **线程隔离**：`asyncio.run_in_executor()` 将同步 RPC 调用放入线程池，避免阻塞 WebSocket 主循环
- **双层超时**：后端 `asyncio.wait_for(timeout=120s)` + FreeCAD 内部 GUI dispatch 超时 90s
- **智能导出调度**：代码执行成功后自动触发 STL 导出，读取临时文件 → Base64 编码 → WebSocket 推送
- **空文档防护**：导出前检测 `FreeCAD.ActiveDocument.Objects` 数量，为空则立即返回错误

**关键代码片段**：
```python
# backend/main_freecad_ai.py
# 1. 异步执行 AI 生成的代码
loop = asyncio.get_event_loop()
result = await asyncio.wait_for(
    loop.run_in_executor(None, freecad.execute_code, code_to_execute),
    timeout=120
)

# 2. 执行成功后自动导出 STL
if result.get("success"):
    export_result = await asyncio.wait_for(
        loop.run_in_executor(
            None,
            lambda: freecad.export_document(doc_name, export_path, "stl")
        ),
        timeout=120
    )
    
    # 读取文件并推送到前端
    with open(export_path, 'rb') as f:
        file_data = f.read()
    file_b64 = base64.b64encode(file_data).decode()
    
    await websocket.send_json({
        "type": "stl_exported",
        "content": file_b64
    })
```

**制作顺序意义**：将 AI 生成的代码「落地执行」，并把执行结果（3D 模型数据）回传给前端，完成闭环。

---

#### Step 5 — 浏览器端 3D 实时渲染与交互（Three.js 前端）

**技术要点**：
- **坐标系转换**：FreeCAD Z-up → Three.js Y-up，通过 `geometry.rotateX(-Math.PI / 2)` 实现
- **异步加载优化**：`requestIdleCallback` 延迟 STL 解析，优先渲染加载动画，提升感知速度
- **自动布局**：计算 bounding box 后居中，并沿 Y 轴上移 15% 模型高度，避免贴底
- **交互控制**：OrbitControls 支持旋转/缩放/平移，线框模式切换，视角重置

**关键代码片段**：
```javascript
// frontend/threejs_viewer.js
function loadSTLFromBase64(base64Data) {
    setModelLoading(true);
    
    const loadTask = () => {
        // 1. 解码 Base64
        const binaryString = atob(base64Data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < len; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        
        // 2. 解析 STL
        const loader = new THREE.STLLoader();
        let geometry = loader.parse(bytes.buffer);
        
        // 3. 坐标系转换（Z-up → Y-up）
        geometry.rotateX(-Math.PI / 2);
        
        // 4. 创建材质和网格
        const material = new THREE.MeshPhongMaterial({
            color: 0xff8c42,
            specular: 0x444444,
            shininess: 100
        });
        const mesh = new THREE.Mesh(geometry, material);
        
        // 5. 居中并上移
        const center = new THREE.Vector3();
        geometry.boundingBox.getCenter(center);
        mesh.position.sub(center);
        mesh.position.y += maxDim * 0.15;
        
        // 6. 添加到场景
        scene.add(mesh);
        setModelLoading(false);
    };
    
    // 异步执行，让 UI 先渲染加载动画
    requestIdleCallback(loadTask, { timeout: 100 });
}
```

**制作顺序意义**：作为项目的「门面」，3D 预览是用户直接感知价值的环节。放在最后制作，是因为需要前面所有步骤（通信、AI、执行、导出）都就绪后，才有数据源可供展示。

---

## 三、问题与解决（生产环境高频踩坑）

---

### 问题一：导出超时（TimeoutError）— STEP/复杂模型导出失败

#### 问题现象

后端日志出现：
```
[FAIL] 导出失败: 导出错误: TimeoutError
asyncio.exceptions.CancelledError

Traceback (most recent call last):
  File "...main_freecad_ai.py", line 761, in handle_export
    active_doc_result = await asyncio.wait_for(...)
    ...
  File "...asyncio\timeouts.py", line 116, in __aexit__
    raise TimeoutError from exc_val
```

前端表现：导出按钮显示「导出中...」后无响应，或提示 `[FAIL] 导出失败: 导出错误`。

#### 深层原因分析

1. **FreeCAD GUI 线程单线程瓶颈**：所有 `execute_code()` 调用均在 FreeCAD GUI 主线程执行，复杂 STEP 导出涉及拓扑遍历、B-Rep 计算，耗时随面片数指数增长
2. **双层超时冲突**：后端 `asyncio.wait_for(timeout=60s)` 与 FreeCAD 内部 `GUI dispatch timeout=90s` 不匹配，后端先超时但 FreeCAD 仍在执行，导致状态不一致
3. **文档查询阶段即超时**：`handle_export` 中先执行 `freecad.execute_code()` 查询活动文档，此步骤本身就可能因 FreeCAD 繁忙而超时

#### 分步落地解决方法

**步骤 1 — 延长后端超时时间**

修改 `backend/main_freecad_ai.py` 中 `handle_export` 函数：

```python
# 原代码（超时 10 秒）
active_doc_result = await asyncio.wait_for(
    loop.run_in_executor(None, lambda: freecad.execute_code("...")),
    timeout=10
)

# 修改为 30 秒
active_doc_result = await asyncio.wait_for(
    loop.run_in_executor(None, lambda: freecad.execute_code("...")),
    timeout=30
)

# 导出执行阶段（原 60 秒 → 120 秒）
result = await asyncio.wait_for(
    loop.run_in_executor(None, lambda: freecad.export_document(...)),
    timeout=120
)
```

**步骤 2 — 延长 AI 代码执行超时**

修改 `handle_ai_chat` 中的代码执行超时：

```python
# 原 60 秒 → 120 秒
result = await asyncio.wait_for(
    loop.run_in_executor(None, freecad.execute_code, code_to_execute),
    timeout=120
)
```

**步骤 3 — 简化模型降低导出负载**

在 `ai_agent_freecad.py` 系统提示词中添加：
```
13. **性能优化规则**：
    - 导出 STEP 前，对复杂模型使用 `doc.removeObject()` 删除隐藏/辅助对象
    - 避免创建百万级面片的细分曲面，优先使用参数化实体
    - 布尔运算后调用 `doc.recompute()` 清理中间拓扑
```

**步骤 4 — 验证命令**

```bash
# 重启后端使配置生效
python launcher.py

# 测试导出
# 1. 创建简单立方体 → 导出 STEP（应成功）
# 2. 创建复杂显示器 → 导出 STEP（观察耗时）
```

---

### 问题二：STL 导出成功但前端 3D 预览不显示

#### 问题现象

后端日志显示：
```
[OK] 已导出 STL: C:\Users\...\Temp\freecad_preview_xxx.stl
导出完成: 5702384 bytes
[DEBUG] stl_exported 消息已发送
```

但前端 3D 区域仍显示「暂无模型」，或保持「正在加载 3D 模型...」转圈。

#### 深层原因分析

1. **返回类型误判**：`freecad.export_document()` 返回的是 `Dict[str, Any]`（执行结果），而非文件路径字符串。原代码错误地检查 `export_result.get("success")`，但实际返回的是 FreeCAD 执行输出，成功标记在输出文本中而非字典键
2. **文件路径未正确传递**：`export_document` 内部通过 `execute_code()` 执行导出脚本，临时文件路径作为 Python 变量嵌入代码，但路径中的反斜杠在 Python 字符串中未正确处理
3. **前端消息处理遗漏**：`handleMessage` 中 `stl_exported` 分支存在重复定义（`object_created` case 被重复添加），导致消息路由异常

#### 分步落地解决方法

**步骤 1 — 修复导出成功判断逻辑**

修改 `backend/main_freecad_ai.py` 中 AI 执行成功后的自动导出段：

```python
# 原代码（错误：直接判断 dict.get("success")）
if export_result and export_result.get("success"):

# 修改为：兼容字符串和字典，检查输出内容
export_success = False
if isinstance(export_result, dict):
    if export_result.get("success"):
        export_success = True
    else:
        msg = export_result.get("message", "")
        if "[OK] 已导出 STL" in msg or "导出完成" in msg:
            export_success = True
elif isinstance(export_result, str):
    if "[OK] 已导出 STL" in export_result or "导出完成" in export_result:
        export_success = True

if export_success and os.path.exists(export_path):
    with open(export_path, 'rb') as f:
        file_data = f.read()
    file_b64 = base64.b64encode(file_data).decode()
    
    await websocket.send_json({
        "type": "stl_exported",
        "content": file_b64
    })
```

**步骤 2 — 修复前端消息处理**

修改 `frontend/index.html` 中的 `handleMessage`：

```javascript
// 删除重复的 object_created case，确保每个 case 只出现一次
case 'stl_exported':
    if (msg.content) {
        loadSTLFromBase64(msg.content);
    }
    break;

case 'error':
    setModelLoading(false);  // 关键：停止加载动画
    addMessage('error', msg.content);
    break;
```

**步骤 3 — 添加调试日志定位**

在后端添加：
```python
print(f"[DEBUG] export_result type: {type(export_result)}, value: {export_result}")
print(f"[DEBUG] STL 文件大小: {len(file_data)} bytes, base64: {len(file_b64)} chars")
print(f"[DEBUG] stl_exported 消息已发送")
```

在前端 `loadSTLFromBase64` 首行添加：
```javascript
console.log('[DEBUG] loadSTLFromBase64 called, data length:', base64Data.length);
```

**步骤 4 — 验证命令**

```bash
# 1. 启动后端
python launcher.py

# 2. 浏览器 F12 → Console，过滤 "[DEBUG]"
# 3. 发送指令："创建一个红色立方体"
# 4. 观察 Console 是否出现：
#    [DEBUG] loadSTLFromBase64 called, data length: xxxxxx
# 5. 若未出现，检查 Network → WS 是否有 stl_exported 消息
```

---

### 问题三：AI 代码执行导致 FreeCAD 崩溃（GUI 闪退）

#### 问题现象

后端日志显示：
```
[FAIL] 代码执行失败: GUI dispatch timed out after 90s
Error executing Python code: {'success': False, 'error': 'GUI dispatch timed out after 90s'}
```

或 FreeCAD 直接无响应后自动关闭，Windows 事件查看器显示 `FreeCAD.exe` 崩溃。

#### 深层原因分析

1. **危险 Shape 赋值**：AI 生成的代码直接对 `PartDesign::Body`、`App::Part`、`Part::Compound` 等容器类型赋值 `.Shape`，这些对象的 Shape 是只读/计算属性，强制赋值触发 FreeCAD 内部断言失败，导致 C++ 层崩溃
2. **参数化对象直接重建**：对 `Part::Box` 等参数化对象直接 `obj.Shape = Part.makeBox(...)`，破坏了参数驱动链，引发依赖对象级联失效
3. **提示词规则遗漏**：早期系统提示词未明确禁止 `.Shape` 赋值，AI 从训练数据中学到了「直接替换 Shape」的直觉写法

#### 分步落地解决方法

**步骤 1 — 强化系统提示词安全规则**

修改 `backend/ai_agent_freecad.py` 中 `self.system_prompt`：

```python
# 在规则 10 中补充（已存在则确认完整性）：
10. **修改对象时的安全规则（必须遵守，防止 FreeCAD 闪退）**：
    - **修改前必须先判断对象类型 `obj.TypeId`**
    - **优先修改参数，绝不直接替换 `.Shape`**：
      - `Part::Box` → 修改 `Length` / `Width` / `Height`
      - `Part::Cylinder` → 修改 `Radius` / `Height`
      - `Part::Sphere` → 修改 `Radius`
    - **严禁直接给以下类型赋值 `.Shape`**：
      `PartDesign::Body`、`App::Part`、`Part::Compound`、
      `Part::Boolean`、装配容器
      这些对象的 Shape 是只读或计算属性，直接赋值会导致 FreeCAD 崩溃
    - **如果对象类型复杂、不确定、或修改参数无法满足需求，
      删除旧对象并按新需求重新创建**（保持其他对象不变）
    - **关键修改步骤用 try-except 包裹**，失败时打印明确错误
```

**步骤 2 — 后端添加代码执行前校验（可选加固）**

在 `main_freecad_ai.py` 中，AI 生成代码后、执行前，添加正则检查：

```python
import re

# 危险模式检测
dangerous_patterns = [
    r'\.Shape\s*=\s*Part\.make',  # 直接 Shape 赋值
    r'\.Shape\s*=\s*[^\n]+makeCompound',  # Compound Shape 赋值
]

for pattern in dangerous_patterns:
    if re.search(pattern, code_to_execute):
        print(f"[WARN] 检测到危险代码模式: {pattern}")
        # 可选：拦截并提示 AI 重新生成
```

**步骤 3 — 崩溃后快速恢复**

1. **重启 FreeCAD**：关闭崩溃进程，重新启动软件
2. **重新运行 RPC Server 宏**：`freecad_rpc_server.FCMacro`
3. **后端自动重连**：`freecad_rpc_client.py` 已内置重连逻辑，连接断开后会自动尝试一次重连
4. **前端刷新**：F5 刷新页面，重新建立 WebSocket 连接

**步骤 4 — 验证命令**

```bash
# 1. 重启 FreeCAD 和 RPC Server
# 2. 重启后端：python launcher.py
# 3. 发送测试指令："创建一个红色立方体"
# 4. 观察后端日志应出现：
#    [OK] 代码执行成功
#    输出: [OK] 已创建...
# 5. 若再次崩溃，检查 FreeCAD 安装目录下的 `crash.log` 或 Windows 事件查看器
```

---

## 四、附录

### 4.1 关键配置速查表

| 配置项 | 文件路径 | 默认值 | 建议值 | 说明 |
|--------|---------|--------|--------|------|
| AI 代码执行超时 | `main_freecad_ai.py` | 60s | 120s | 复杂模型需要更多时间 |
| 导出执行超时 | `main_freecad_ai.py` | 60s | 120s | STEP 导出较慢 |
| 文档查询超时 | `main_freecad_ai.py` | 10s | 30s | FreeCAD 繁忙时响应慢 |
| 截图超时 | `main_freecad_ai.py` | 30s | 30s | 一般无需调整 |
| WebSocket 端口 | `launcher.py` | 8001 | 8001 | 被占用时自动切换 |
| FreeCAD RPC 端口 | `freecad_rpc_client.py` | 9877 | 9877 | 需与宏配置一致 |
| AI 温度 | `ai_agent_freecad.py` | 0.3 | 0.3 | 低随机性确保代码稳定 |
| AI 最大 Token | `ai_agent_freecad.py` | 1500 | 1500 | 复杂模型可能需要 2000 |

### 4.2 日志排查关键词

| 关键词 | 含义 | 处理建议 |
|--------|------|---------|
| `[OK]` | 操作成功 | 正常，无需处理 |
| `[WARN]` | 警告，可恢复 | 关注但不阻断，如截图失败、STL 导出失败 |
| `[FAIL]` | 操作失败 | 检查具体错误信息，针对性修复 |
| `[ERROR]` | 系统错误 | 查看堆栈跟踪，可能需重启服务 |
| `[DEBUG]` | 调试信息 | 开发阶段开启，生产可关闭 |
| `TimeoutError` | 超时 | 延长超时时间或简化操作 |
| `GUI dispatch timed out` | FreeCAD 内部超时 | 简化模型或分批执行 |
| `Connection refused` | 连接被拒绝 | 检查 FreeCAD 是否启动、RPC Server 是否运行 |
| `CancelledError` | 异步取消 | 通常是超时导致的连锁反应 |

### 4.3 版本兼容性

| 组件 | 版本 | 说明 |
|------|------|------|
| Python | 3.13 | 开发测试版本 |
| FreeCAD | 0.20+ | 支持 Python 3 控制台 |
| Three.js | r128 | 稳定版本，支持 STLLoader |
| FastAPI | 0.100+ | 支持 WebSocket |
| Uvicorn | 0.23+ | ASGI 服务器 |
| DashScope | 最新 | 阿里云百炼 SDK |

---

> 文档版本：v1.0 | 最后更新：2026-06-18 | 维护者：FreeCAD AI 助手开发团队
