# 项目文件清理指南

> 用于期末汇报前清理多余的开发文档和测试文件

---

## 📋 保留的核心文件

### 主文档（必须保留）
- ✅ `README.md` - 项目主文档（已更新）
- ✅ `PROJECT_DOCUMENTATION.md` - 完整项目文档（新创建）
- ✅ `requirements.txt` - 根目录的依赖文件

### 核心代码（必须保留）
```
frontend/
├── index.html
├── app.js
└── style.css

backend/
├── main.py
├── ai_agent.py
├── ai_agent_enhanced.py
├── blender_client.py
└── requirements.txt

docs/
└── blender-mcp-api.md
```

---

## 🗑️ 建议删除的文件

### 根目录 - 临时和重复文档（共 22 个）

```bash
# 删除这些文件：
6.3.md                              # 临时笔记
AUTO_3D_PREVIEW.md                  # 开发过程文档
CHANGELOG_EXPORT.md                 # 变更日志
CONNECTION_TROUBLESHOOTING.md       # 故障排查（已整合到主文档）
COORDINATE_FIX_SUMMARY.md           # 修复总结
demo_export.py                      # 测试脚本
DOWNLOAD_FIX_GUIDE.md               # 修复指南
EXPORT_FEATURE_SUMMARY.md           # 功能总结
EXPORT_FORMATS_GUIDE.md             # 格式指南（已整合）
FUTURE_DEVELOPMENT.md               # 未来开发（已整合）
MULTI_FORMAT_EXPORT_README.md       # 导出说明（已整合）
ORBITCONTROLS_FIX.md                # 修复文档
QUICK_START_EXPORT.md               # 快速开始（已整合）
QUICK_START_GUIDE.md                # 快速开始（已整合）
RESTART_GUIDE.md                    # 重启指南
TEST_EXPORT_FEATURE.md              # 测试文档
test_new_export_ui.html             # 测试页面
THREEJS_FIX_SUMMARY.md              # 修复总结
TROUBLESHOOTING_3D_VIEWER.md        # 故障排查
UI_IMPROVEMENT_EXPORT.md            # UI 改进
UI_REDESIGN_SUMMARY.md              # 重新设计总结
USAGE_GUIDE.md                      # 使用指南（已整合）
导出功能文档索引.md                  # 中文文档索引
新导出界面使用说明.md                # 中文使用说明
新功能说明.md                        # 中文功能说明
```

### backend/ - 测试文件（共 19 个）

```bash
# 删除这些文件：
backend/diagnose_connection.py         # 诊断脚本
backend/final_test.py                  # 测试脚本
backend/hello_qwen.py                  # 测试脚本
backend/run_test.bat                   # 测试批处理
backend/run_test.sh                    # 测试脚本
backend/start_server_test.py           # 测试脚本
backend/start_with_ai.bat              # 启动脚本（可选）
backend/start_with_ai.ps1              # 启动脚本（可选）
backend/start.bat                      # 启动脚本（可选）
backend/test_ai_generation.py          # 测试脚本
backend/test_client.py                 # 测试脚本
backend/test_cube_orientation.py       # 测试脚本
backend/test_fastapi.py                # 测试脚本
backend/test_main_ai.py                # 测试脚本
backend/test_material.py               # 测试脚本
backend/test_mock_server.py            # 测试脚本
backend/test_output.stl                # 测试输出
backend/test_stl_export.py             # 测试脚本
backend/test_web_server_offline.py     # 测试脚本
backend/test_web_server.py             # 测试脚本
backend/test_websocket.py              # 测试脚本
backend/verify_web_module.py           # 验证脚本
backend/websocket_example.py           # 示例脚本

# 删除这些文档：
backend/AI_INTEGRATION_README.md       # AI 集成说明（已整合）
backend/MAIN_AI_UPDATE.md              # 更新说明
backend/MATERIAL_FIX_GUIDE.md          # 修复指南
backend/QUICK_START_AI.md              # 快速开始（已整合）
backend/STL_EXPORT_GUIDE.md            # 导出指南（已整合）
backend/TEST_README.md                 # 测试说明
backend/UPDATE_SUMMARY.md              # 更新总结
backend/WEB_SERVER_TEST.md             # Web 服务器测试
```

### 其他目录

```bash
# 删除整个目录：
unused_tests/                          # 废弃的测试文件夹
references/                            # 参考代码（如果不需要）
```

---

## 🔧 一键清理脚本

### Windows PowerShell

```powershell
# 保存为 cleanup.ps1
# 运行前请仔细检查列表！

# 删除根目录临时文件
Remove-Item "6.3.md" -ErrorAction SilentlyContinue
Remove-Item "AUTO_3D_PREVIEW.md" -ErrorAction SilentlyContinue
Remove-Item "CHANGELOG_EXPORT.md" -ErrorAction SilentlyContinue
Remove-Item "CONNECTION_TROUBLESHOOTING.md" -ErrorAction SilentlyContinue
Remove-Item "COORDINATE_FIX_SUMMARY.md" -ErrorAction SilentlyContinue
Remove-Item "demo_export.py" -ErrorAction SilentlyContinue
Remove-Item "DOWNLOAD_FIX_GUIDE.md" -ErrorAction SilentlyContinue
Remove-Item "EXPORT_FEATURE_SUMMARY.md" -ErrorAction SilentlyContinue
Remove-Item "EXPORT_FORMATS_GUIDE.md" -ErrorAction SilentlyContinue
Remove-Item "FUTURE_DEVELOPMENT.md" -ErrorAction SilentlyContinue
Remove-Item "MULTI_FORMAT_EXPORT_README.md" -ErrorAction SilentlyContinue
Remove-Item "ORBITCONTROLS_FIX.md" -ErrorAction SilentlyContinue
Remove-Item "QUICK_START_EXPORT.md" -ErrorAction SilentlyContinue
Remove-Item "QUICK_START_GUIDE.md" -ErrorAction SilentlyContinue
Remove-Item "RESTART_GUIDE.md" -ErrorAction SilentlyContinue
Remove-Item "TEST_EXPORT_FEATURE.md" -ErrorAction SilentlyContinue
Remove-Item "test_new_export_ui.html" -ErrorAction SilentlyContinue
Remove-Item "THREEJS_FIX_SUMMARY.md" -ErrorAction SilentlyContinue
Remove-Item "TROUBLESHOOTING_3D_VIEWER.md" -ErrorAction SilentlyContinue
Remove-Item "UI_IMPROVEMENT_EXPORT.md" -ErrorAction SilentlyContinue
Remove-Item "UI_REDESIGN_SUMMARY.md" -ErrorAction SilentlyContinue
Remove-Item "USAGE_GUIDE.md" -ErrorAction SilentlyContinue
Remove-Item "导出功能文档索引.md" -ErrorAction SilentlyContinue
Remove-Item "新导出界面使用说明.md" -ErrorAction SilentlyContinue
Remove-Item "新功能说明.md" -ErrorAction SilentlyContinue

# 删除 backend 测试文件
Remove-Item "backend/diagnose_connection.py" -ErrorAction SilentlyContinue
Remove-Item "backend/final_test.py" -ErrorAction SilentlyContinue
Remove-Item "backend/hello_qwen.py" -ErrorAction SilentlyContinue
Remove-Item "backend/test_*.py" -ErrorAction SilentlyContinue
Remove-Item "backend/test_output.stl" -ErrorAction SilentlyContinue
Remove-Item "backend/*test*.py" -ErrorAction SilentlyContinue
Remove-Item "backend/websocket_example.py" -ErrorAction SilentlyContinue
Remove-Item "backend/verify_web_module.py" -ErrorAction SilentlyContinue

# 删除 backend 临时文档
Remove-Item "backend/AI_INTEGRATION_README.md" -ErrorAction SilentlyContinue
Remove-Item "backend/MAIN_AI_UPDATE.md" -ErrorAction SilentlyContinue
Remove-Item "backend/MATERIAL_FIX_GUIDE.md" -ErrorAction SilentlyContinue
Remove-Item "backend/QUICK_START_AI.md" -ErrorAction SilentlyContinue
Remove-Item "backend/STL_EXPORT_GUIDE.md" -ErrorAction SilentlyContinue
Remove-Item "backend/TEST_README.md" -ErrorAction SilentlyContinue
Remove-Item "backend/UPDATE_SUMMARY.md" -ErrorAction SilentlyContinue
Remove-Item "backend/WEB_SERVER_TEST.md" -ErrorAction SilentlyContinue

# 删除废弃目录
Remove-Item "unused_tests" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "references" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "✓ 清理完成！" -ForegroundColor Green
```

### Linux/macOS Bash

```bash
#!/bin/bash
# 保存为 cleanup.sh
# 运行前请仔细检查列表！
# chmod +x cleanup.sh && ./cleanup.sh

# 删除根目录临时文件
rm -f 6.3.md
rm -f AUTO_3D_PREVIEW.md
rm -f CHANGELOG_EXPORT.md
rm -f CONNECTION_TROUBLESHOOTING.md
rm -f COORDINATE_FIX_SUMMARY.md
rm -f demo_export.py
rm -f DOWNLOAD_FIX_GUIDE.md
rm -f EXPORT_FEATURE_SUMMARY.md
rm -f EXPORT_FORMATS_GUIDE.md
rm -f FUTURE_DEVELOPMENT.md
rm -f MULTI_FORMAT_EXPORT_README.md
rm -f ORBITCONTROLS_FIX.md
rm -f QUICK_START_EXPORT.md
rm -f QUICK_START_GUIDE.md
rm -f RESTART_GUIDE.md
rm -f TEST_EXPORT_FEATURE.md
rm -f test_new_export_ui.html
rm -f THREEJS_FIX_SUMMARY.md
rm -f TROUBLESHOOTING_3D_VIEWER.md
rm -f UI_IMPROVEMENT_EXPORT.md
rm -f UI_REDESIGN_SUMMARY.md
rm -f USAGE_GUIDE.md
rm -f 导出功能文档索引.md
rm -f 新导出界面使用说明.md
rm -f 新功能说明.md

# 删除 backend 测试文件
rm -f backend/diagnose_connection.py
rm -f backend/final_test.py
rm -f backend/hello_qwen.py
rm -f backend/test_*.py
rm -f backend/test_output.stl
rm -f backend/websocket_example.py
rm -f backend/verify_web_module.py

# 删除 backend 临时文档
rm -f backend/AI_INTEGRATION_README.md
rm -f backend/MAIN_AI_UPDATE.md
rm -f backend/MATERIAL_FIX_GUIDE.md
rm -f backend/QUICK_START_AI.md
rm -f backend/STL_EXPORT_GUIDE.md
rm -f backend/TEST_README.md
rm -f backend/UPDATE_SUMMARY.md
rm -f backend/WEB_SERVER_TEST.md

# 删除废弃目录
rm -rf unused_tests
rm -rf references

echo "✓ 清理完成！"
```

---

## ⚠️ 重要提示

1. **备份**：清理前请先备份整个项目！
2. **检查**：仔细检查文件列表，确认不需要后再删除
3. **保留启动脚本**：如果需要 `start_with_ai.bat` 等启动脚本，请不要删除
4. **保留 references**：如果参考代码对你有用，可以保留

---

## 📊 清理后的项目结构

```
blender-ai-assistant/
├── .gitignore                       # Git 配置
├── README.md                        # 项目主文档 ⭐
├── PROJECT_DOCUMENTATION.md         # 完整文档 ⭐
├── requirements.txt                 # Python 依赖
├── frontend/                        # 前端代码 ⭐
│   ├── index.html
│   ├── app.js
│   └── style.css
├── backend/                         # 后端代码 ⭐
│   ├── main.py
│   ├── ai_agent.py
│   ├── ai_agent_enhanced.py
│   ├── blender_client.py
│   ├── requirements.txt
│   ├── run_test.bat               # (可选)
│   ├── start_with_ai.bat          # (可选)
│   └── start.bat                  # (可选)
└── docs/                            # API 文档 ⭐
    └── blender-mcp-api.md
```

**清理后文件统计：**
- 保留核心文件：~15 个
- 删除临时文件：~40+ 个
- 项目更加清爽整洁！

---

## ✅ 检查清单

清理完成后，请确认：

- [ ] README.md 存在且内容完整
- [ ] PROJECT_DOCUMENTATION.md 存在
- [ ] frontend/ 目录包含所有前端文件
- [ ] backend/ 目录包含所有后端核心文件
- [ ] requirements.txt 存在于根目录和 backend/
- [ ] docs/blender-mcp-api.md 存在
- [ ] 所有测试文件已删除
- [ ] 所有临时文档已删除
- [ ] 项目仍可正常运行

---

## 🧪 测试运行

清理后请测试系统是否正常：

```bash
# 1. 启动后端
cd backend
python main.py

# 2. 访问前端
# 打开浏览器: http://localhost:8000

# 3. 测试基本功能
# - 输入指令："创建一个红色的球体"
# - 检查 3D 预览是否正常
# - 尝试导出 STL 格式
```

---

**祝你期末汇报顺利！🎉**
