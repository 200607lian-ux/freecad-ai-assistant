"""
测试 AI + RPC 集成后端
验证完整流程：AI 生成代码 -> RPC 执行 -> 获取截图
"""

import sys
import asyncio
sys.path.insert(0, 'd:/lixiangdownload/freecad-ai-assistant/backend')

from freecad_rpc_client import FreeCADRPCClient
from ai_agent_freecad import AIAgent


async def test_ai_rpc_integration():
    """测试 AI 生成代码并通过 RPC 执行"""
    
    print("=" * 60)
    print("测试 AI + RPC 集成")
    print("=" * 60)
    
    # 1. 连接 FreeCAD
    print("\n[1/4] 连接 FreeCAD RPC...")
    client = FreeCADRPCClient(host="localhost", port=9875)
    if not client.connect():
        print("[FAIL] 无法连接 FreeCAD，请确保 RPC Server 已启动")
        return False
    print("[OK] FreeCAD 连接成功")
    
    # 2. 初始化 AI
    print("\n[2/4] 初始化 AI 代理...")
    ai = AIAgent(use_ai=True)
    if ai.client:
        print("[OK] AI 代理已初始化 (DeepSeek-V4-Flash)")
    else:
        print("[WARN] AI 代理使用规则引擎模式")
    
    # 3. 测试 AI 生成代码
    print("\n[3/4] 测试 AI 代码生成...")
    test_inputs = [
        "创建一个红色的立方体",
        "创建一个蓝色的圆柱体，半径5，高度10",
    ]
    
    for user_input in test_inputs:
        print(f"\n  用户输入: {user_input}")
        
        # 生成响应
        response = await ai.generate_response(
            user_message=user_input,
            conversation_history=[],
            blender_client=client
        )
        
        print(f"  响应类型: {response.get('type')}")
        print(f"  响应消息: {response.get('message')}")
        
        if response.get('type') == 'code' and response.get('code'):
            code = response['code']
            print(f"  生成代码:\n{code[:200]}...")
            
            # 4. 执行代码
            print(f"\n  [4/4] 执行代码...")
            result = client.execute_code(code)
            
            if result.get('success'):
                print(f"  [OK] 代码执行成功")
                print(f"  输出: {result.get('message', '')[:200]}")
            else:
                print(f"  [FAIL] 代码执行失败: {result.get('error')}")
    
    # 5. 获取截图
    print(f"\n[5/5] 获取截图...")
    image = client.get_screenshot("Isometric")
    if image:
        image.save("test_screenshot.png")
        print(f"[OK] 截图已保存到 test_screenshot.png")
    
    # 获取场景信息
    print(f"\n[6/5] 获取场景信息...")
    docs = client.list_documents()
    print(f"  文档: {docs}")
    for doc in docs:
        objects = client.get_objects(doc)
        print(f"  文档 '{doc}' 对象数量: {len(objects)}")
        for obj in objects[:5]:
            print(f"    - {obj.get('name', 'unknown')}: {obj.get('type', 'unknown')}")
    
    # 断开连接
    client.disconnect()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = asyncio.run(test_ai_rpc_integration())
    sys.exit(0 if success else 1)
