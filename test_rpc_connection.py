"""
FreeCAD RPC 连接测试
测试 freecad-mcp 的 RPC 服务器连接
"""

import sys
sys.path.insert(0, 'd:/lixiangdownload/freecad-ai-assistant/backend')

from freecad_rpc_client import FreeCADRPCClient


def test_connection():
    """测试基础连接"""
    print("=" * 50)
    print("测试 1: 基础连接 (Ping)")
    print("=" * 50)
    
    client = FreeCADRPCClient(host="localhost", port=9875)
    
    if client.connect():
        print("[OK] 连接成功!")
        print(f"  地址: localhost:9875")
        
        # 测试文档列表
        print("\n" + "=" * 50)
        print("测试 2: 获取文档列表")
        print("=" * 50)
        docs = client.list_documents()
        print(f"[OK] 文档列表: {docs}")
        
        # 测试创建文档
        if not docs:
            print("\n" + "=" * 50)
            print("测试 3: 创建文档")
            print("=" * 50)
            result = client.create_document("TestDoc")
            print(f"结果: {result}")
            docs = client.list_documents()
        
        doc_name = docs[0] if docs else "TestDoc"
        
        # 测试创建对象
        print("\n" + "=" * 50)
        print("测试 4: 创建对象 (立方体)")
        print("=" * 50)
        result = client.create_box(
            doc_name=doc_name,
            obj_name="TestBox",
            length=10, width=10, height=10,
            color=[1.0, 0.0, 0.0]  # 红色
        )
        print(f"结果: {result}")
        
        # 测试获取对象
        print("\n" + "=" * 50)
        print("测试 5: 获取对象列表")
        print("=" * 50)
        objects = client.get_objects(doc_name)
        print(f"对象数量: {len(objects)}")
        for obj in objects:
            print(f"  - {obj.get('name', 'unknown')}: {obj.get('type', 'unknown')}")
        
        # 测试执行代码
        print("\n" + "=" * 50)
        print("测试 6: 执行 Python 代码")
        print("=" * 50)
        code = """
import FreeCAD
print("FreeCAD 版本:", FreeCAD.Version())
print("文档:", FreeCAD.ActiveDocument.Name if FreeCAD.ActiveDocument else "None")
"""
        result = client.execute_code(code)
        if result.get("success"):
            print(f"[OK] 代码执行成功")
            print(f"  输出: {result.get('message', '')[:200]}")
        
        # 断开连接
        client.disconnect()
        
        print("\n" + "=" * 50)
        print("所有测试完成!")
        print("=" * 50)
        return True
        
    else:
        print("\n[FAIL] 连接失败")
        print("\n请确保:")
        print("  1. FreeCAD 已启动")
        print("  2. 安装了 FreeCADMCP addon")
        print("  3. 在 FreeCAD 中执行了 'Start RPC Server'")
        print("  4. RPC 服务器监听在端口 9875")
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
