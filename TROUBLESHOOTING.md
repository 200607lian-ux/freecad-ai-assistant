# FreeCAD AI 助手常见问题排查指南

## 1. 连接类问题

### 1.1 FreeCAD 未连接
**报错信息**：
```
[FAIL] 导出失败: FreeCAD 未连接
```
或前端显示：`等待 FreeCAD 连接...`

**问题原因**：
- FreeCAD 软件未启动
- FreeCAD 中未运行 RPC Server 宏
- RPC Server 端口（默认 9877）被占用
- 网络防火墙阻止了连接

**解决方法**：
1. 启动 FreeCAD 软件
2. 在 FreeCAD 中执行宏：`freecad_socket_server.FCMacro` 或 `freecad_rpc_server.FCMacro`
3. 检查控制台输出确认服务器已启动（应显示 `RPC Server started on port 9877`）
4. 重启后端服务：`python launcher.py`

---

### 1.2 WebSocket 连接断开
**报错信息**：
```
连接已断开，正在尝试自动恢复...
```

**问题原因**：
- 后端服务崩溃或重启
- 网络不稳定
- 浏览器长时间无操作导致连接超时

**解决方法**：
1. 刷新页面（F5 或 Ctrl+F5）
2. 检查后端控制台是否有错误日志
3. 重启后端服务
4. 检查网络连接

---

## 2. 导出类问题

### 2.1 导出超时（TimeoutError）
**报错信息**：
```
[FAIL] 导出失败: 导出错误: TimeoutError
asyncio.exceptions.CancelledError
```

**问题原因**：
- 模型过于复杂，导出耗时超过超时限制
- FreeCAD 正在执行其他操作，导出被阻塞
- STEP/IGES 等格式导出本身较慢

**解决方法**：
1. **延长超时时间**：在 `backend/main_freecad_ai.py` 中修改 `handle_export` 函数的超时参数
   - 文档查询超时：从 10 秒改为 30 秒
   - 导出执行超时：从 60 秒改为 120 秒或更长
2. **简化模型**：减少对象数量或降低网格精度
3. **先导出 STL**：STL 导出速度更快，可先验证模型是否正确
4. **重启 FreeCAD**：有时 FreeCAD 内部状态异常会导致导出变慢

---

### 2.2 导出失败：没有活动文档
**报错信息**：
```
[FAIL] 导出失败: 没有活动文档
```
或前端显示：`暂无模型`

**问题原因**：
- FreeCAD 中没有任何打开的文档
- 活动文档中没有对象
- AI 生成的代码未成功创建对象

**解决方法**：
1. 在 FreeCAD 中确认是否有文档打开（标题栏显示文档名）
2. 检查 FreeCAD 的 3D 视图中是否有可见对象
3. 重新发送创建指令，观察 AI 执行结果
4. 检查后端日志中的代码执行输出

---

### 2.3 导出失败：GUI dispatch timed out
**报错信息**：
```
[FAIL] 代码执行失败: GUI dispatch timed out after 90s
Error executing Python code: {'success': False, 'error': 'GUI dispatch timed out after 90s'}
```

**问题原因**：
- AI 生成的代码过于复杂，执行时间超过 FreeCAD GUI 线程的超时限制（90 秒）
- 代码中包含大量布尔运算或复杂几何操作
- FreeCAD 内部计算卡住

**解决方法**：
1. **延长后端超时**：将 `main_freecad_ai.py` 中的 `timeout=60` 改为 `timeout=120` 或更长
2. **简化 AI 指令**：避免一次性创建过于复杂的模型，分步骤创建
3. **使用异步执行**：修改代码使用 `freecad.execute_code_async()` 代替 `execute_code()`
4. **优化 AI 提示词**：在 `ai_agent_freecad.py` 中提示 AI 生成更高效的代码

---

### 2.4 STL 导出成功但前端不显示
**报错信息**：
```
[OK] 已导出 STL: xxx.stl
导出完成: 5702384 bytes
```
但前端 3D 区域仍显示 `暂无模型`

**问题原因**：
- `export_document` 返回的结果格式与预期不符
- 后端发送 `stl_exported` 消息失败
- 前端未正确处理 `stl_exported` 消息
- WebSocket 消息丢失

**解决方法**：
1. 检查后端日志是否有 `[DEBUG] stl_exported 消息已发送`
2. 打开浏览器开发者工具（F12）→ Network → WS，查看 WebSocket 消息
3. 检查 `frontend/index.html` 中的 `handleMessage` 函数是否正确处理 `stl_exported` 类型
4. 确认 `loadSTLFromBase64` 函数是否被调用

---

## 3. AI 代码执行类问题

### 3.1 代码执行超时
**报错信息**：
```
[FAIL] 代码执行超时
```

**问题原因**：
- AI 生成的代码执行时间超过 60 秒（默认）
- 代码中包含复杂的几何运算（如大量布尔操作）
- FreeCAD 内部计算阻塞

**解决方法**：
1. 在 `backend/main_freecad_ai.py` 中将 `timeout=60` 改为 `timeout=120`
2. 让 AI 生成更简单的代码，分步骤创建复杂模型
3. 检查 FreeCAD 是否卡住，必要时重启 FreeCAD

---

### 3.2 代码执行失败：FreeCAD 闪退
**报错信息**：
```
[FAIL] 代码执行失败: Connection refused / 连接被拒绝
```
或 FreeCAD 直接崩溃关闭

**问题原因**：
- AI 生成的代码直接修改了 `.Shape` 属性（对于某些对象类型这是危险的）
- 代码删除了被其他对象引用的对象
- 代码创建了无效的几何形状

**解决方法**：
1. 检查 `ai_agent_freecad.py` 中的系统提示词是否包含安全规则
2. 确保提示词中有：
   - `严禁直接给 PartDesign::Body、App::Part 等类型赋值 .Shape`
   - `修改前必须先判断对象类型 obj.TypeId`
   - `优先修改参数，绝不直接替换 .Shape`
3. 在后端日志中查看生成的具体代码，手动排查问题
4. 重启 FreeCAD 和后端服务

---

### 3.3 AI 生成的代码不正确
**问题现象**：
- AI 返回了代码，但执行后没有创建预期的对象
- 对象位置、尺寸、颜色不符合描述

**问题原因**：
- AI 模型理解错误（尤其是复杂的空间描述）
- 系统提示词中的示例不够清晰
- 用户描述过于模糊

**解决方法**：
1. **更精确地描述**：
   - ❌ "创建一个显示器" → ✅ "创建一个宽 480mm、高 300mm、厚 20mm 的灰色屏幕，加上圆柱形支架和圆形底座"
2. **分步骤创建**：先创建主体，再添加细节
3. **检查系统提示词**：在 `ai_agent_freecad.py` 中更新示例和规则
4. **添加视图方向规则**：确保提示词包含屏幕朝向等要求

---

## 4. 前端展示类问题

### 4.1 3D 模型不显示 / 显示空白
**问题现象**：
- 前端 3D 区域空白或显示 `暂无模型`
- 加载动画一直转圈

**问题原因**：
- 没有模型数据（未导出成功）
- Three.js 初始化失败
- 浏览器不支持 WebGL
- STL 数据解析失败

**解决方法**：
1. 检查浏览器控制台（F12 → Console）是否有错误
2. 确认 WebSocket 已连接且收到 `stl_exported` 消息
3. 检查 `threejs_viewer.js` 中的 `loadSTLFromBase64` 是否被调用
4. 尝试刷新页面（Ctrl+F5）清除缓存
5. 更换浏览器（推荐 Chrome 或 Edge）

---

### 4.2 坐标轴仍显示
**问题现象**：
- 已删除坐标轴代码，但刷新后仍能看到红绿蓝三色轴

**问题原因**：
- 浏览器缓存了旧的 JS 文件
- 坐标轴代码在多个文件中存在（`threejs_viewer.js` 和 `index.html`）

**解决方法**：
1. **强制刷新**：Ctrl+F5 或 Ctrl+Shift+R
2. **检查所有文件**：
   - `frontend/threejs_viewer.js` 中的 `AxesHelper` 是否已注释
   - `frontend/index.html` 中的 `AxesHelper` 是否已注释
3. 清除浏览器缓存后重新加载

---

### 4.3 模型方向不对
**问题现象**：
- 生成的显示器屏幕朝上或朝侧面，不是正面朝前

**问题原因**：
- AI 生成的代码没有调整 `Placement.Rotation`
- FreeCAD 默认坐标系与 Three.js 不同（Z 向上 vs Y 向上）
- 系统提示词中缺少视图方向规则

**解决方法**：
1. 在 `ai_agent_freecad.py` 的系统提示词中添加：
   ```
   生成显示器、屏幕等具有正面朝向的物体时，必须确保屏幕正面朝向用户
   使用 Placement.Rotation 调整朝向，使屏幕正面朝向 -Y 方向
   ```
2. 在 `threejs_viewer.js` 中检查 `geometry.rotateX(-Math.PI / 2)` 是否正确应用
3. 手动调整相机位置：`camera.lookAt(0, 0, 0)` 和 `controls.update()`

---

## 5. 性能类问题

### 5.1 STL 加载速度慢
**问题现象**：
- 点击刷新后，3D 模型需要几秒甚至十几秒才显示

**问题原因**：
- 模型顶点数过多（百万级）
- Base64 解码和 STL 解析在阻塞主线程
- 前端一次性处理大量数据

**解决方法**：
1. **异步加载**：使用 `requestIdleCallback` 或 `setTimeout` 延迟解析
2. **简化模型**：在 FreeCAD 中降低网格精度（Mesh → Decimation）
3. **显示加载状态**：确保加载动画在解析前显示
4. **优化解码**：使用 `Uint8Array` 批量处理而不是逐字节

---

### 5.2 后端响应慢
**问题现象**：
- 发送指令后，AI 思考状态持续很久
- 整体流程（思考→执行→导出→展示）超过 2 分钟

**问题原因**：
- AI 模型推理慢（网络延迟）
- 代码执行复杂
- 截图/导出操作耗时

**解决方法**：
1. 检查网络连接（阿里云 API）
2. 简化指令，分步骤执行
3. 关闭截图功能（如果不需要）
4. 使用本地缓存的 AI 响应（重复指令）

---

## 6. 配置类问题

### 6.1 DASHSCOPE_API_KEY 未设置
**报错信息**：
```
AI 功能未启用：未设置 DASHSCOPE_API_KEY 环境变量
```

**问题原因**：
- 没有设置阿里云百炼的 API Key
- 环境变量未正确加载

**解决方法**：
1. 在系统环境变量中添加 `DASHSCOPE_API_KEY=your_key_here`
2. 或在 `.env` 文件中添加
3. 重启后端服务使环境变量生效

---

### 6.2 端口被占用
**报错信息**：
```
[WARN] 端口 8001 已被占用
```

**问题原因**：
- 之前的后端进程未正常退出
- 其他程序占用了 8001 端口

**解决方法**：
1. `launcher.py` 会自动检测并释放端口（终止占用进程）
2. 手动终止：任务管理器 → 找到 Python 进程 → 结束任务
3. 或修改 `launcher.py` 中的 `DEFAULT_PORT` 为其他端口（如 8002）

---

## 快速排查清单

遇到问题时，按以下顺序检查：

1. [ ] FreeCAD 是否已启动？
2. [ ] FreeCAD 中是否运行了 RPC Server 宏？
3. [ ] 后端服务是否正常运行？（看控制台日志）
4. [ ] WebSocket 是否已连接？（看前端状态栏）
5. [ ] 发送指令后，后端是否有 AI 思考→执行→导出的日志？
6. [ ] 浏览器控制台是否有错误？（F12 → Console）
7. [ ] 网络面板是否有 WebSocket 消息？（F12 → Network → WS）
8. [ ] 强制刷新页面（Ctrl+F5）后问题是否解决？

---

## 联系支持

如果以上方法都无法解决问题：
1. 记录完整的错误日志（后端控制台 + 浏览器控制台）
2. 记录复现步骤（从启动到报错的完整操作）
3. 记录环境信息（FreeCAD 版本、Python 版本、操作系统）
