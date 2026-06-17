"""
在 Kiro 环境中启动 FreeCAD AI 助手
这个脚本应该通过 Kiro 运行，以便访问 MCP 工具
"""

import sys
import os

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print("FreeCAD AI 助手 - Kiro 环境启动")
print("="*60)
print()

# 检查 MCP 工具是否可用
print("🔍 检查 MCP 工具...")
try:
    # 测试 FreeCAD MCP 工具
    result = mcp_freecad_execute_code(code="""
import FreeCAD
print("✓ FreeCAD MCP 工具可用")
print(f"FreeCAD 版本: {FreeCAD.Version()}")
""")
    print("✓ MCP 工具已加载")
    print()
except NameError:
    print("✗ 错误：MCP 工具不可用")
    print("   请确保此脚本在 Kiro 环境中运行")
    print()
    sys.exit(1)

# 导入并启动 FastAPI 应用
print("🚀 启动 FastAPI 服务器...")
print()

from main_freecad import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
