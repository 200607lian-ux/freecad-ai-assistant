# FreeCAD AI 建模助手

一个基于 AI 的 FreeCAD 自然语言建模助手，支持通过自然语言描述创建 3D 模型。

## 🌟 特性

- 🤖 **AI 驱动**：使用阿里云百炼 DeepSeek-V4-Flash 模型理解自然语言
- 🎨 **直观操作**：通过自然语言描述创建复杂 3D 模型
- 🔧 **独立部署**：通过 TCP Socket 通信，无需复杂配置
- 📦 **多格式导出**：支持 STEP、IGES、STL、OBJ 等多种格式
- 🌐 **Web 界面**：现代化的浏览器界面，实时 3D 预览

## 📋 系统要求

- FreeCAD 0.19 或更高版本
- Python 3.8 或更高版本
- 现代浏览器（Chrome、Firefox、Edge 等）

## 🚀 快速开始

### 方案选择

本项目提供两种部署方案：

1. **Socket 独立方案**（推荐）- 通过 TCP Socket 通信，简单易用
2. **Kiro MCP 方案** - 通过 Kiro 的 MCP 集成，功能更强大

### Socket 独立方案（推荐）

#### 第一步：启动 FreeCAD Socket 服务器

1. 打开 FreeCAD
2. 打开宏编辑器：`Macro` → `Macros...`
3. 选择宏文件：`freecad_socket_server.FCMacro`
4. 点击 `Execute` 执行宏
5. 看到提示"FreeCAD Socket 服务器已启动"

#### 第二步：测试连接（可选）

```bash
python test_socket.py
```

如果测试通过，继续下一步。

#### 第三步：启动后端服务器

双击运行：
```
START_SERVER.bat
```

或手动启动：
```bash
cd backend
pip install -r requirements.txt
python main_freecad.py
```

#### 第四步：访问 Web 界面

打开浏览器访问：
```
http://localhost:8001
```

## 💡 使用示例

### 基础操作

```
创建一个立方体
创建一个红色球体
在位置(20,0,0)创建一个蓝色圆柱体
```

### 复杂建模（需要 AI）

```
创建一个M6螺帽50mm螺杆
创建一个带孔的立方体
创建一个桌子
```

### 启用 AI 功能

设置环境变量：

**Windows:**
```bash
set DASHSCOPE_API_KEY=your_api_key_here
python main_freecad.py
```

**Linux/Mac:**
```bash
export DASHSCOPE_API_KEY=your_api_key_here
python main_freecad.py
```

## 📖 详细文档

- [Socket 独立方案指南](SOCKET_SETUP_GUIDE.md) - 推荐新用户使用
- [Kiro MCP 方案指南](KIRO_SETUP_GUIDE.md) - 高级用户
- [项目状态](PROJECT_STATUS.md) - 开发进度和计划

## 🏗️ 项目结构

```
freecad-ai-assistant/
├── backend/                          # 后端服务
│   ├── ai_agent_freecad.py          # AI 代码生成引擎
│   ├── freecad_client.py            # FreeCAD Socket 客户端
│   ├── main_freecad.py              # FastAPI 服务器
│   └── requirements.txt             # Python 依赖
├── frontend/                         # 前端界面
│   ├── index.html                   # 主页面
│   ├── app.js                       # 前端逻辑
│   └── style.css                    # 样式
├── freecad_socket_server.FCMacro    # FreeCAD Socket 服务器宏
├── START_SERVER.bat                 # 快速启动脚本
├── test_socket.py                   # Socket 连接测试工具
└── README.md                        # 本文档
```

## 🔧 故障排除

### 问题：连接被拒绝

**原因**：FreeCAD Socket 服务器未运行

**解决方案**：
1. 确认 FreeCAD 已启动
2. 在 FreeCAD 中执行 `freecad_socket_server.FCMacro` 宏
3. 确认看到"服务器已启动"消息

### 问题：AI 生成错误代码

**原因**：AI 误生成了 Blender 代码

**解决方案**：
1. 确认使用最新版本的 `ai_agent_freecad.py`
2. 重启后端服务器
3. 如果问题持续，请在 GitHub 提交 Issue

### 问题：前端立即断开

**原因**：后端处理请求时崩溃

**解决方案**：
1. 查看后端控制台的完整错误日志
2. 运行 `test_socket.py` 验证 Socket 连接
3. 确认所有依赖已正确安装

## 🛠️ 技术栈

- **前端**：HTML5 + JavaScript + Three.js
- **后端**：Python FastAPI + WebSocket
- **通信**：TCP Socket (JSON)
- **CAD 引擎**：FreeCAD + Part Workbench
- **AI 模型**：阿里云百炼 DeepSeek-V4-Flash

## 📚 API 文档

### WebSocket 消息格式

**聊天消息**：
```json
{
  "type": "chat",
  "content": "创建一个立方体"
}
```

**导出模型**：
```json
{
  "type": "export_model",
  "format": "step"
}
```

详见 [SOCKET_SETUP_GUIDE.md](SOCKET_SETUP_GUIDE.md)

## 🗺️ 开发计划

- [x] Socket 通信层
- [x] 基础几何体创建
- [x] AI 代码生成
- [x] 颜色设置
- [x] 导出功能（STEP/STL/IGES）
- [ ] 布尔运算支持
- [ ] 草图功能
- [ ] 零件装配
- [ ] 参数化建模
- [ ] 模型库集成

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

本项目基于 Blender AI 建模助手改编而来，感谢原项目的贡献者。

---

**快速链接**

- [立即开始](SOCKET_SETUP_GUIDE.md)
- [测试连接](test_socket.py)
- [启动服务器](START_SERVER.bat)
