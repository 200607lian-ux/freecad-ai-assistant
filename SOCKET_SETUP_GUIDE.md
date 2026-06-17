# FreeCAD AI 助手 - Socket 独立版本使用指南

## 概述

这是一个完全独立的 FreeCAD AI 建模助手，通过 TCP Socket 与 FreeCAD 通信，无需依赖 Kiro MCP 或其他复杂配置。

## 架构

```
前端 (浏览器)
    ↓ WebSocket
后端 (Python FastAPI)
    ↓ TCP Socket (端口 9877)
FreeCAD (Socket 服务器宏)
```

## 安装步骤

### 第一步：启动 FreeCAD Socket 服务器

1. 打开 FreeCAD
2. 打开宏编辑器：`Macro` → `Macros...`
3. 选择宏文件：`freecad_socket_server.FCMacro`
4. 点击 `Execute` 执行宏
5. 看到提示"FreeCAD Socket 服务器已启动，监听端口: 9877"

**注意**：每次启动 FreeCAD 后都需要执行此宏

### 第二步：启动后端服务器

**方法 1：使用批处理文件（推荐）**
```bash
# 双击运行
START_SERVER.bat
```

**方法 2：手动启动**
```bash
cd backend
pip install -r requirements.txt
python main_freecad.py
```

### 第三步：访问前端界面

打开浏览器，访问：
```
http://localhost:8001
```

## 使用示例

### 基础操作

1. **创建基础几何体**
   - "创建一个立方体"
   - "创建一个球体"
   - "创建一个圆柱体"

2. **创建带颜色的对象**
   - "创建一个红色的立方体"
   - "创建一个蓝色球体"
   - "创建一个绿色圆柱体"

3. **复杂建模**（使用 AI）
   - "创建一个M6螺帽50mm螺杆"
   - "创建一个桌子"
   - "创建一个带孔的立方体"

### AI 功能（需要 API Key）

如果你有阿里云百炼的 API Key，可以启用完整的 AI 功能：

```bash
# Windows
set DASHSCOPE_API_KEY=your_api_key_here
python main_freecad.py

# Linux/Mac
export DASHSCOPE_API_KEY=your_api_key_here
python main_freecad.py
```

启用 AI 后，系统可以理解更复杂的自然语言描述。

## 测试连接

### 测试 FreeCAD Socket 连接

在 Python 中运行：

```python
import socket
import json

# 连接到 FreeCAD
sock = socket.socket()
sock.connect(('127.0.0.1', 9877))

# 发送 ping 命令
command = {"type": "ping", "params": {}}
sock.sendall(json.dumps(command).encode())

# 接收响应
response = sock.recv(1024)
print(json.loads(response))  # 应该返回 {"status": "ok", "message": "pong"}

sock.close()
```

### 测试代码执行

```python
import socket
import json

sock = socket.socket()
sock.connect(('127.0.0.1', 9877))

command = {
    "type": "execute_code",
    "params": {
        "code": """
import FreeCAD
import Part

doc = FreeCAD.ActiveDocument
if not doc:
    doc = FreeCAD.newDocument("Test")

box = Part.makeBox(10, 10, 10)
obj = doc.addObject("Part::Feature", "Box")
obj.Shape = box
doc.recompute()
print("创建成功")
"""
    }
}

sock.sendall(json.dumps(command).encode())
response = sock.recv(1024*1024)
print(json.loads(response))

sock.close()
```

## 故障排除

### 问题 1：连接被拒绝

**症状**：
```
✗ 连接被拒绝，请确保 FreeCAD Socket 服务器正在运行
```

**解决方案**：
1. 确认 FreeCAD 已启动
2. 确认在 FreeCAD 中执行了 `freecad_socket_server.FCMacro` 宏
3. 检查宏是否显示"服务器已启动"消息

### 问题 2：AI 生成错误代码

**症状**：
```
生成的 Blender Python 代码：import bpy...
```

**原因**：AI 可能误生成了 Blender 代码而不是 FreeCAD 代码

**解决方案**：
1. 更新 `ai_agent_freecad.py` 文件
2. 确认系统提示词正确指定了 FreeCAD
3. 重启后端服务器

### 问题 3：前端立即断开

**症状**：
```
INFO:     connection open
INFO:     Shutting down
INFO:     connection closed
```

**原因**：后端在处理请求时崩溃

**解决方案**：
1. 检查后端控制台的完整错误日志
2. 确认 `freecad_client.py` 使用的是 Socket 版本而不是 MCP 版本
3. 确认所有依赖已安装

### 问题 4：代码执行超时

**症状**：
```
✗ Socket 超时（30秒）
```

**解决方案**：
1. 检查 FreeCAD 是否响应
2. 尝试在 FreeCAD Python 控制台手动运行代码
3. 检查代码是否有死循环或长时间运行的操作

## API 端点

### HTTP 端点

- `GET /` - 前端页面
- `GET /health` - 健康检查
- `GET /api/ai/status` - AI 状态

### WebSocket 端点

- `ws://localhost:8001/ws` - WebSocket 通信

#### WebSocket 消息格式

**聊天消息**：
```json
{
  "type": "chat",
  "content": "创建一个立方体"
}
```

**获取场景信息**：
```json
{
  "type": "get_scene"
}
```

**导出 STL**：
```json
{
  "type": "export_stl"
}
```

**导出模型**：
```json
{
  "type": "export_model",
  "format": "step",
  "selection_only": false
}
```

## 支持的导出格式

- `step` / `stp` - STEP 格式（CAD 标准）
- `iges` / `igs` - IGES 格式（CAD 交换）
- `stl` - STL 格式（3D 打印）
- `obj` - Wavefront OBJ 格式
- `brep` - OpenCASCADE BREP 格式

## 项目结构

```
freecad-ai-assistant/
├── backend/
│   ├── ai_agent_freecad.py       # AI 代理（代码生成）
│   ├── freecad_client.py         # Socket 客户端
│   ├── main_freecad.py           # FastAPI 后端
│   └── requirements.txt          # Python 依赖
├── frontend/
│   ├── index.html               # 前端界面
│   ├── app.js                   # 前端逻辑
│   └── style.css                # 样式
├── freecad_socket_server.FCMacro  # FreeCAD 宏
├── START_SERVER.bat              # 启动脚本
└── SOCKET_SETUP_GUIDE.md         # 本文档
```

## 技术栈

- **前端**：原生 JavaScript + Three.js（3D预览）
- **后端**：Python FastAPI + WebSocket
- **通信**：TCP Socket（JSON 协议）
- **CAD**：FreeCAD + Part Workbench
- **AI**：阿里云百炼 DeepSeek-V4-Flash（可选）

## 开发计划

- [x] Socket 通信层
- [x] 基础几何体创建
- [x] AI 代码生成
- [x] 颜色设置
- [x] 导出功能（STEP/STL）
- [ ] 布尔运算
- [ ] 草图功能
- [ ] 零件装配
- [ ] 参数化建模

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
