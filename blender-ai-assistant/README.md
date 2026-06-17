# Blender AI 建模助手

> 🎨 通过自然语言对话创建 3D 模型的智能建模系统

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Blender](https://img.shields.io/badge/Blender-3.0+-orange.svg)](https://www.blender.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## ✨ 项目简介

Blender AI 建模助手是一个基于**大语言模型**的智能 3D 建模系统，让用户通过**简单的文字描述**就能创建 3D 模型，无需学习复杂的建模软件操作。

**核心特色：**
- 🤖 **自然语言交互** - 用对话方式控制 Blender 建模
- 🔄 **实时 3D 预览** - Web 端即时查看建模效果
- 💾 **多格式导出** - 支持 STL、OBJ、FBX、GLB 等 9 种格式
- ⚡ **智能代码生成** - AI 自动将指令转换为 Python 代码

---

## 🖼️ 系统截图

### 主界面
- 左侧：3D 模型实时预览（Three.js）
- 右侧：AI 对话建模界面

### 功能演示
```
用户: "创建一个红色的球体"
AI: ✓ 已创建红色球体
    [显示生成的 Python 代码]
    [3D 预览自动更新]

用户: "在位置(3, 0, 0)创建一个蓝色立方体"
AI: ✓ 已创建蓝色立方体
    [Blender 中实时显示两个对象]
```

---

## 🚀 快速开始

### 环境要求

```
Python 3.9+
Blender 3.0+
现代浏览器（Chrome/Firefox/Edge）
```

### 安装步骤

#### 1. 安装 Python 依赖

```bash
cd backend
pip install -r requirements.txt
```

#### 2. 配置 AI 密钥

```bash
# Windows PowerShell
$env:DASHSCOPE_API_KEY = "your-api-key-here"

# Linux/macOS
export DASHSCOPE_API_KEY=your-api-key-here
```

> 💡 获取 API Key: 访问 [阿里云百炼](https://bailian.console.aliyun.com/)

#### 3. 启动 Blender MCP 服务

1. 打开 Blender
2. 编辑 → 偏好设置 → 插件
3. 启用 "MCP Server" 插件
4. 点击 "启动 MCP 服务器" (端口 9876)

#### 4. 启动后端服务

```bash
cd backend
python main.py
```

#### 5. 访问 Web 界面

打开浏览器访问：
```
http://localhost:8000
```

---

## 📖 使用说明

### 基础建模指令

```python
# 创建几何体
"创建一个红色的立方体"
"在位置(2, 0, 0)创建一个蓝色球体"
"创建一个绿色的圆柱体，高度为3"

# 操作对象
"把当前对象移动到(5, 5, 5)"
"将球体旋转45度"
"放大立方体2倍"

# 场景管理
"删除所有物体"
"查看场景信息"
```

### 导出模型

1. 点击左上角的 💾 导出按钮
2. 选择格式（STL、OBJ、FBX 等）
3. 文件自动下载

### 3D 视图控制

- 🖱️ **左键拖动** - 旋转模型
- 🔍 **滚轮** - 缩放
- 🖱️ **右键拖动** - 平移
- 🎯 **重置按钮** - 恢复默认视角

---

## 🏗️ 系统架构

```
┌─────────────────┐
│   Web 前端      │ ← Three.js 3D 渲染
│  (HTML/JS/CSS)  │
└────────┬────────┘
         │ WebSocket
┌────────┴────────┐
│  FastAPI 后端   │ ← AI 代码生成
│  (Python)       │    (DeepSeek)
└────────┬────────┘
         │ TCP Socket
┌────────┴────────┐
│  Blender 引擎   │ ← 3D 建模
│  (MCP Server)   │
└─────────────────┘
```

---

## 🛠️ 技术栈

### 前端
- **框架**: 原生 JavaScript + HTML5 + CSS3
- **3D 渲染**: Three.js (r128)
- **通信**: WebSocket

### 后端
- **Web 框架**: FastAPI
- **AI 模型**: DeepSeek-V4-Flash
- **异步处理**: asyncio + uvicorn

### Blender
- **通信协议**: MCP (Model Context Protocol)
- **接口**: Blender Python API (bpy)

---

## 📁 项目结构

```
blender-ai-assistant/
├── frontend/                 # 前端代码
│   ├── index.html           # 主页面
│   ├── app.js               # 核心逻辑（1200+ 行）
│   └── style.css            # 样式文件
├── backend/                  # 后端代码
│   ├── main.py              # FastAPI 主服务
│   ├── ai_agent.py          # AI 代理（基础版）
│   ├── ai_agent_enhanced.py # AI 代理（增强版）
│   ├── blender_client.py    # Blender 通信客户端
│   └── requirements.txt     # Python 依赖
├── docs/                     # API 文档
└── PROJECT_DOCUMENTATION.md  # 完整项目文档
```

---

## 🎯 核心功能

### 1. 自然语言建模
- ✅ AI 理解自然语言指令
- ✅ 自动生成 Blender Python 代码
- ✅ 实时执行并反馈结果

### 2. 实时 3D 预览
- ✅ 基于 Three.js 的 3D 查看器
- ✅ 支持旋转、缩放、平移交互
- ✅ 自动刷新场景信息

### 3. 多格式导出
| 格式 | 用途 | 状态 |
|------|------|------|
| STL | 3D 打印 | ✅ |
| OBJ | 通用交换 | ✅ |
| FBX | 游戏/动画 | ✅ |
| glTF/GLB | Web3D | ✅ |
| PLY | 点云 | ✅ |
| X3D | Web3D | ✅ |
| Collada | 影视 | ✅ |
| Alembic | 特效 | ✅ |

### 4. 智能错误处理
- ✅ 空场景检测
- ✅ 导出超时保护（30秒）
- ✅ 用户主动取消
- ✅ 友好的错误提示

---

## 📚 详细文档

- 📖 [完整项目文档](PROJECT_DOCUMENTATION.md) - 系统设计、技术细节、开发历程
- 📘 [Blender MCP API](docs/blender-mcp-api.md) - Blender 通信协议文档

---

## 🔧 常见问题

### Q: AI 生成的代码执行失败?
**A:** 尝试简化指令，分步执行复杂操作。

### Q: 某些格式导出失败？
**A:** 优先使用 STL、OBJ、FBX 这些通用格式，某些格式需要特定 Blender 版本支持。

### Q: 3D 预览显示不正常？
**A:** 检查浏览器是否支持 WebGL，尝试硬刷新（Ctrl + Shift + R）。

### Q: WebSocket 连接失败？
**A:** 确保后端服务已启动，检查端口 8000 是否被占用。

---

## 🚧 未来计划

- [ ] 材质库和预设
- [ ] 场景保存/加载
- [ ] 图像生成 3D 模型
- [ ] 多人协作建模
- [ ] 移动端适配
- [ ] 云端 SaaS 部署

---

## 📝 开发历程

**v1.0** (当前版本)
- ✅ 完整的 Web 界面
- ✅ AI 智能代码生成
- ✅ 9 种格式导出
- ✅ 实时 3D 预览
- ✅ 健壮的错误处理

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License

---

## 👤 作者

**项目作者：** [你的名字]  
**课程：** [课程名称]  
**学期：** 2023-2024 学年第一学期

---

## 🙏 致谢

- [Blender](https://www.blender.org/) - 开源 3D 创作软件
- [Three.js](https://threejs.org/) - JavaScript 3D 库
- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Python Web 框架
- [DeepSeek](https://www.deepseek.com/) - 高性能 AI 模型

---

*最后更新：2024年1月*
