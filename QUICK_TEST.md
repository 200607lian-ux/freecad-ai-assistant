# 快速测试 - 在 FreeCAD 中创建立方体

## 方法 1：使用 Python 控制台（最快）

### 步骤 1：打开 FreeCAD Python 控制台

1. 打开 FreeCAD
2. 点击菜单：`View` → `Panels` → `Python console`
3. 在底部会出现 Python 控制台

### 步骤 2：复制并执行代码

在 Python 控制台中输入（或复制粘贴）以下代码：

```python
import FreeCAD
import Part

doc = FreeCAD.ActiveDocument
if not doc:
    doc = FreeCAD.newDocument("CubeDoc")

box = Part.makeBox(10, 10, 10)
obj = doc.addObject("Part::Feature", "Cube")
obj.Shape = box
obj.Label = "立方体"
obj.ViewObject.ShapeColor = (0.8, 0.8, 0.8)
doc.recompute()

print("✓ 成功创建了立方体！")
```

### 步骤 3：查看结果

立方体会立即出现在 3D 视图中！

---

## 方法 2：使用宏（推荐）

### 步骤 1：创建宏文件

1. 打开 FreeCAD
2. 点击菜单：`Macro` → `New macro...`
3. 输入名称：`CreateCube`
4. 点击创建

### 步骤 2：粘贴代码

将以下代码复制到宏编辑器：

```python
import FreeCAD
import Part

doc = FreeCAD.ActiveDocument
if not doc:
    doc = FreeCAD.newDocument("CubeDoc")

box = Part.makeBox(10, 10, 10)
obj = doc.addObject("Part::Feature", "Cube")
obj.Shape = box
obj.Label = "立方体"
obj.ViewObject.ShapeColor = (0.8, 0.8, 0.8)
doc.recompute()

print("✓ 成功创建了立方体！")
```

### 步骤 3：执行宏

1. 点击 `Execute` 按钮（或按 Ctrl+Return）
2. 立方体会出现在 3D 视图中

---

## 方法 3：使用 AI 助手系统（完整流程）

### 前提条件

确保以下步骤已完成：

1. ✅ FreeCAD 已启动
2. ✅ Socket 服务器宏已运行（`freecad_socket_server.FCMacro`）
3. ✅ 后端服务器已启动（`START_SERVER.bat`）

### 使用步骤

1. 打开浏览器：`http://localhost:8001`
2. 在聊天框输入：`创建一个立方体`
3. 按下回车或点击发送
4. 系统会：
   - 生成 FreeCAD 代码
   - 通过 Socket 发送到 FreeCAD
   - 执行代码
   - 显示 3D 预览

---

## 自定义立方体

### 改变大小

将代码中的 `10, 10, 10` 改为其他尺寸：

```python
# 创建 20x15x10 的立方体
box = Part.makeBox(20, 15, 10)
```

### 改变颜色

修改 RGB 值（范围 0.0 到 1.0）：

```python
# 红色
obj.ViewObject.ShapeColor = (1.0, 0.0, 0.0)

# 绿色
obj.ViewObject.ShapeColor = (0.0, 1.0, 0.0)

# 蓝色
obj.ViewObject.ShapeColor = (0.0, 0.0, 1.0)

# 黄色
obj.ViewObject.ShapeColor = (1.0, 1.0, 0.0)
```

### 改变位置

添加位置设置：

```python
# 将立方体放在 (5, 10, 0) 位置
obj.Placement.Base = FreeCAD.Vector(5, 10, 0)
```

### 完整示例

```python
import FreeCAD
import Part

doc = FreeCAD.ActiveDocument
if not doc:
    doc = FreeCAD.newDocument("CustomCube")

# 创建 20x15x10 的蓝色立方体
box = Part.makeBox(20, 15, 10)
obj = doc.addObject("Part::Feature", "CustomCube")
obj.Shape = box
obj.Label = "自定义立方体"
obj.ViewObject.ShapeColor = (0.0, 0.0, 1.0)  # 蓝色

# 设置位置
obj.Placement.Base = FreeCAD.Vector(5, 10, 0)

doc.recompute()

print("✓ 成功创建了自定义立方体！")
print(f"  大小: 20 x 15 x 10")
print(f"  颜色: 蓝色")
print(f"  位置: (5, 10, 0)")
```

---

## 导出模型

### 导出为 STEP 格式

```python
import FreeCAD

doc = FreeCAD.ActiveDocument

# 导出为 STEP 文件
filepath = "C:/Users/YourName/Desktop/cube.step"
FreeCAD.ActiveDocument.exportStep(filepath)

print(f"✓ 已导出到: {filepath}")
```

### 导出为 STL 格式

```python
import FreeCAD
import Mesh

doc = FreeCAD.ActiveDocument

# 导出为 STL 文件（用于 3D 打印）
filepath = "C:/Users/YourName/Desktop/cube.stl"
Mesh.export(doc.Objects, filepath)

print(f"✓ 已导出到: {filepath}")
```

---

## 常见问题

### Q: 代码没有运行？

A: 检查以下几点：
1. FreeCAD 是否已启动
2. Python 控制台是否打开
3. 代码是否完整（缩进正确）
4. 是否有拼写错误

### Q: 看不到立方体？

A: 尝试：
1. 按 `V` 键调整视图
2. 按 `Home` 键重置视图
3. 在左侧树视图中选中立方体
4. 右键 → `Toggle visibility`

### Q: 如何删除立方体？

A: 
```python
# 在 Python 控制台执行
doc.removeObject("Cube")
doc.recompute()
```

或在树视图中右键 → `Delete`

### Q: 如何修改已创建的立方体？

A:
```python
# 获取立方体对象
cube = doc.getObject("Cube")

# 修改颜色
cube.ViewObject.ShapeColor = (1.0, 0.0, 0.0)  # 变为红色

# 修改位置
cube.Placement.Base = FreeCAD.Vector(10, 10, 10)

# 刷新
doc.recompute()
```

---

## 下一步

现在你已经学会了如何在 FreeCAD 中创建基础对象！

接下来可以尝试：
- 创建其他形状（球体、圆柱、圆锥等）
- 使用布尔运算（并集、差集、交集）
- 创建复杂模型（零件、装配体）
- 使用 AI 助手生成代码

查看更多示例：
- [Socket 设置指南](SOCKET_SETUP_GUIDE.md)
- [AI 助手文档](SOCKET_SETUP_GUIDE.md)
