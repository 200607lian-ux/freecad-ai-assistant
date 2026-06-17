# Blender MCP API 文档

## 概述

Blender MCP (Model Context Protocol) 服务器提供了一套 RESTful API，允许外部程序通过 HTTP 协议与 Blender 3D 软件进行交互。本文档描述了 API 的端点、请求/响应格式和示例。

## 基础信息

- **基础 URL**: `http://localhost:5001`
- **协议**: HTTP/HTTPS
- **默认端口**: 5001
- **数据格式**: JSON

## API 端点

### 1. 根端点

获取服务器基本信息。

**请求**:
```
GET /
```

**响应**:
```json
{
  "status": "running",
  "version": "1.0.0",
  "service": "blender-mcp-server",
  "blender_version": "3.6.0",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 2. 执行 Python 代码

在 Blender 中执行 Python 代码。

**请求**:
```
POST /execute
Content-Type: application/json
```

**请求体**:
```json
{
  "type": "execute_python",
  "code": "import bpy\nprint('Hello from Blender!')"
}
```

**响应**:
```json
{
  "success": true,
  "result": "Hello from Blender!",
  "execution_time": 0.123,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 3. 执行 Blender 命令

执行特定的 Blender 命令。

**请求**:
```
POST /command
Content-Type: application/json
```

**请求体**:
```json
{
  "type": "execute_command",
  "command": "create_object",
  "args": {
    "type": "cube",
    "location": [0, 0, 0],
    "size": 2.0
  }
}
```

**响应**:
```json
{
  "success": true,
  "result": {
    "object_name": "Cube",
    "object_type": "MESH",
    "location": [0, 0, 0]
  },
  "execution_time": 0.456,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 4. 获取场景信息

获取当前场景的详细信息。

**请求**:
```
GET /scene
```

**响应**:
```json
{
  "success": true,
  "object_count": 5,
  "active_object": "Cube",
  "objects": [
    {
      "name": "Cube",
      "type": "MESH",
      "location": [0, 0, 0],
      "rotation": [0, 0, 0],
      "scale": [1, 1, 1]
    },
    {
      "name": "Light",
      "type": "LIGHT",
      "location": [4, 1, 6],
      "rotation": [0.785, 0, 0],
      "scale": [1, 1, 1]
    }
  ],
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 5. 健康检查

检查服务器健康状况。

**请求**:
```
GET /health
```

**响应**:
```json
{
  "status": "healthy",
  "blender_connected": true,
  "memory_usage_mb": 256.5,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 命令参考

### 创建对象

创建新的 3D 对象。

```json
{
  "type": "execute_command",
  "command": "create_object",
  "args": {
    "type": "cube|sphere|cylinder|cone|plane|torus|monkey",
    "location": [x, y, z],
    "size": number,
    "name": "optional_name"
  }
}
```

### 修改对象

修改现有对象。

```json
{
  "type": "execute_command",
  "command": "modify_object",
  "args": {
    "object": "object_name",
    "operation": "move|rotate|scale|delete|duplicate|hide|show",
    "location": [x, y, z],
    "rotation": [x, y, z],
    "scale": [x, y, z]
  }
}
```

### 设置材质

设置对象的材质属性。

```json
{
  "type": "execute_command",
  "command": "set_material",
  "args": {
    "object": "object_name",
    "material": {
      "color": [r, g, b, a],
      "roughness": 0.5,
      "metallic": 0.0,
      "emission_strength": 0.0
    }
  }
}
```

### 选择对象

选择场景中的对象。

```json
{
  "type": "execute_command",
  "command": "select_object",
  "args": {
    "object": "object_name",
    "mode": "single|add|remove"
  }
}
```

### 渲染场景

渲染当前场景。

```json
{
  "type": "execute_command",
  "command": "render_scene",
  "args": {
    "output_path": "/path/to/output.png",
    "resolution_x": 1920,
    "resolution_y": 1080,
    "samples": 128
  }
}
```

## 错误处理

所有 API 端点都可能返回错误响应。

**错误响应格式**:
```json
{
  "success": false,
  "error": "错误描述",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 常见错误代码

.
    - `1001`: Blender 未连接
    - `1002`: 无效的命令类型
    - `1003`: 参数验证失败
    - `1004`: Python 执行错误
    - `1005`: 对象不存在
    - `1006`: 文件操作失败
    - `2001`: 服务器内部错误

## Python 代码示例

### 基本示例

```python
import bpy
import math

# 创建立方体
bpy.ops.mesh.primitive_cube_add(
    size=2.0,
    location=(0, 0, 0)
)

# 修改立方体
cube = bpy.context.active_object
cube.location.x = 3.0
cube.rotation_euler = (0, 0, math.radians(45))

# 创建材质
material = bpy.data.materials.new(name="Red_Material")
material.use_nodes = True
bsdf = material.node_tree.nodes.get("Principled BSDF")
bsdf.inputs['Base Color'].default_value = (1.0, 0.0, 0.0, 1.0)

# 应用材质
cube.data.materials.append(material)
```

### 高级示例

```python
import bpy
import numpy as np

# 创建多个对象
for i in range(5):
    for j in range(5):
        # 创建立方体
        bpy.ops.mesh.primitive_cube_add(
            size=0.5,
            location=(i * 2, j * 2, 0)
        )
        
        # 设置随机颜色
        cube = bpy.context.active_object
        mat = bpy.data.materials.new(name=f"Material_{i}_{j}")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs['Base Color'].default_value = (
            np.random.random(),
            np.random.random(),
            np.random.random(),
            1.0
        )
        cube.data.materials.append(mat)

# 选择所有对象
bpy.ops.object.select_all(action='SELECT')

# 应用缩放变换
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
```

## WebSocket 支持

MCP 服务器还支持 WebSocket 连接，用于实时通信。

**WebSocket 端点**: `ws://localhost:5001/ws`

### WebSocket 消息格式

**客户端发送**:
```json
{
  "type": "execute",
  "id": "request_123",
  "command": "python_code",
  "data": {
    "code": "import bpy\nprint('Hello')"
  }
}
```

**服务器响应**:
```json
{
  "type": "response",
  "id": "request_123",
  "success": true,
  "result": "Hello",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 安全注意事项

1. **本地访问**: MCP 服务器默认仅监听 localhost，避免远程访问风险
2. **代码执行**: Python 代码在 Blender 环境中执行，具有完全的系统访问权限
3. **输入验证**: 所有输入都应进行验证，避免恶意代码执行
4. **资源限制**: 考虑实现执行时间和内存使用限制
5. **认证**: 生产环境应考虑添加 API 密钥或令牌认证

## 部署指南

### 开发环境

1. 安装 Blender 3.0+
2. 安装 Python 依赖: `pip install -r requirements.txt`
3. 启动 MCP 服务器: `python mcp_server.py`

### 生产环境

1. 使用 systemd 或 supervisor 管理服务
2. 配置防火墙限制访问
3. 启用 HTTPS 加密
4. 设置日志轮转和监控
5. 定期更新 Blender 和 Python 依赖

## 故障排除

### 常见问题

1. **Blender 未启动**: 确保 Blender 正在运行且 MCP 插件已启用
2. **端口冲突**: 检查端口 5001 是否被其他程序占用
3. **Python 错误**: 查看服务器日志获取详细错误信息
4. **内存不足**: 大型场景可能需要更多内存

### 日志查看

- 服务器日志: `blender_mcp.log`
- Blender 控制台: 查看 Blender 的输出窗口
- 系统日志: `journalctl -u blender-mcp`

## 版本历史

- **v1.0.0** (2024-01-01): 初始版本，基础 API 支持
- **v1.1.0** (2024-02-01): 添加 WebSocket 支持
- **v1.2.0** (2024-03-01): 添加材质和渲染功能

## 相关资源

- [Blender Python API 文档](https://docs.blender.org/api/current/)
- [MCP 协议规范](https://spec.modelcontextprotocol.io/)
- [示例代码仓库](https://github.com/example/blender-mcp)

---

*最后更新: 2024-01-01*