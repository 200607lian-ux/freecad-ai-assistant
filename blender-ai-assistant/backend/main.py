"""
main.py - FastAPI 后端主程序
作用：提供 WebSocket 接口，处理前端请求
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import asyncio
import os
from pathlib import Path

from blender_client import BlenderClient
from ai_agent import AIAgent  # 使用现有的 AIAgent

# 创建应用
app = FastAPI(title="Blender AI 助手")

# 允许跨域（让前端能访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
blender = None
ai_agent = None

@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    global blender, ai_agent
    
    print("\n" + "="*50)
    print("Blender AI 助手后端启动")
    print("="*50)
    
    # 连接 Blender
    print("\n[1/2] 连接 Blender MCP 服务器...")
    blender = BlenderClient()
    if blender.connect():
        print("✓ Blender 连接成功")
    else:
        print("✗ Blender 连接失败（某些功能将不可用）")
    
    # 初始化 AI（启用真实 AI）
    print("\n[2/2] 初始化 AI 代码生成引擎...")
    
    # 尝试导入增强版 AI Agent
    try:
        from ai_agent_enhanced import EnhancedAIAgent
        ai_agent = EnhancedAIAgent(use_ai=True)
        print("✓ 使用增强版 AI Agent（支持多步推理）")
    except ImportError:
        ai_agent = AIAgent(use_ai=True)  # 使用原版
        print("✓ 使用标准 AI Agent")
    
    # 检查 AI 状态
    if ai_agent.client:
        print("✓ AI 模式：使用 DeepSeek-V4-Flash 模型")
        print("  提供商：阿里云百炼")
        print("  能力：智能理解自然语言，生成复杂建模代码")
    else:
        print("⚠️  AI 模式：规则引擎（降级模式）")
        print("  原因：未找到 DASHSCOPE_API_KEY 环境变量")
        print("  能力：基础几何体创建和简单操作")
        print("  建议：设置 API Key 以启用完整 AI 功能")
    
    print("\n" + "-"*50)
    print("服务地址: http://localhost:8000")
    print("WebSocket: ws://localhost:8000/ws")
    print("健康检查: http://localhost:8000/health")
    print("="*50 + "\n")
    print("💡 提示：")
    print("  - 前端可通过 WebSocket 发送自然语言指令")
    print("  - 支持复杂的建模描述，如「创建一个红色的球体」")
    print("  - AI 会自动生成并执行 Blender Python 代码")
    print("="*50 + "\n")

# ===================================
# 静态文件服务（前端页面）
# ===================================

# 获取前端目录的绝对路径
frontend_dir = Path(__file__).parent.parent / "frontend"

# 挂载静态文件目录
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")
    print(f"✓ 静态文件服务已启用: {frontend_dir}")

@app.get("/")
async def root():
    """返回前端页面"""
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Blender AI 助手运行中", "status": "ok", "frontend": "not_found"}

@app.get("/health")
async def health():
    """健康检查端点 - 返回系统状态"""
    ai_status = "ai_enabled" if (ai_agent and ai_agent.client) else "rule_engine"
    
    return {
        "status": "ok",
        "blender_connected": blender is not None and blender.socket is not None,
        "ai_mode": ai_status,
        "ai_model": "deepseek-v4-flash" if ai_status == "ai_enabled" else None,
        "capabilities": {
            "natural_language": ai_status == "ai_enabled",
            "complex_modeling": ai_status == "ai_enabled",
            "basic_operations": True
        }
    }

@app.get("/api/ai/status")
async def ai_status():
    """获取 AI 状态详情"""
    if ai_agent and ai_agent.client:
        return {
            "enabled": True,
            "mode": "ai",
            "model": "deepseek-v4-flash",
            "provider": "阿里云百炼",
            "api_endpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "features": [
                "自然语言理解",
                "复杂建模指令",
                "智能代码生成",
                "材质和颜色设置",
                "多对象组合操作"
            ],
            "examples": [
                "创建一个红色的立方体",
                "在位置(2,0,0)创建一个蓝色球体",
                "把当前对象移动到(5,5,5)",
                "创建一个绿色的圆柱体，高度为3"
            ]
        }
    else:
        return {
            "enabled": False,
            "mode": "rule_engine",
            "model": None,
            "provider": None,
            "features": [
                "基础几何体创建",
                "简单移动操作",
                "删除对象"
            ],
            "examples": [
                "创建立方体",
                "创建球体",
                "删除所有"
            ],
            "recommendation": "设置 DASHSCOPE_API_KEY 环境变量以启用完整 AI 功能"
        }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 通信端点"""
    await websocket.accept()
    print("✓ 前端已连接")
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "chat":
                user_input = message.get("content", "")
                print(f"\n📝 用户: {user_input}")
                
                # 检查是否使用流式模式（如果有 enhanced agent）
                if hasattr(ai_agent, 'generate_response_stream'):
                    # 使用流式响应（多步推理）
                    await handle_stream_chat(websocket, user_input, blender, ai_agent)
                else:
                    # 使用传统响应（单步）
                    await handle_standard_chat(websocket, user_input, blender, ai_agent)
                
            elif message.get("type") == "load_base_model":
                # 加载基础模型
                print("\n📁 加载基础模型...")
                await websocket.send_json({"type": "status", "content": "正在加载基础模型..."})
                
                if blender and blender.socket:
                    # 打开 .blend 文件
                    blend_file = "D:\\lixiangdownload\\chairset1.blend"
                    load_code = f'''
import bpy
import os

# 加载基础模型
blend_file = r"{blend_file}"

if os.path.exists(blend_file):
    # 关闭当前文件（可选）
    # bpy.ops.wm.close()
    
    # 打开基础模型文件
    bpy.ops.wm.open_mainfile(filepath=blend_file)
    print(f"✓ 已加载基础模型: {{blend_file}}")
    print(f"场景对象数: {{len(bpy.data.objects)}}")
else:
    print(f"✗ 基础模型文件不存在: {{blend_file}}")
'''
                    result = blender.execute_code(load_code)
                    
                    # 等待一下，让 Blender 完成加载
                    await asyncio.sleep(2)
                    
                    # 获取场景信息
                    scene_info = blender.get_scene_info()
                    if scene_info:
                        await websocket.send_json({"type": "scene_info", "content": scene_info})
                        
                        # 获取截图
                        screenshot = blender.get_screenshot()
                        if screenshot:
                            await websocket.send_json({"type": "screenshot", "content": screenshot})
                        
                        # 自动导出 STL
                        await websocket.send_json({
                            "type": "status",
                            "content": "正在生成 3D 预览..."
                        })
                        
                        stl_data = blender.export_stl(selection_only=False)
                        if stl_data:
                            await websocket.send_json({
                                "type": "stl_exported",
                                "content": stl_data,
                                "message": "✓ 基础模型已加载",
                                "auto": True
                            })
                            print("✓ 基础模型已加载并导出")
                    
                    await websocket.send_json({
                        "type": "response",
                        "content": "✓ 基础模型加载成功"
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "content": "Blender 未连接"
                    })
            
            elif message.get("type") == "get_scene":
                scene = blender.get_scene_info() if blender else None
                await websocket.send_json({"type": "scene_info", "content": scene})
                
                screenshot = blender.get_screenshot() if blender else None
                if screenshot:
                    await websocket.send_json({"type": "screenshot", "content": screenshot})
            
            elif message.get("type") == "export_stl":
                # 导出 STL 文件
                print("\n📦 导出 STL 文件...")
                await websocket.send_json({"type": "status", "content": "正在导出 STL..."})
                
                if blender and blender.socket:
                    stl_data = blender.export_stl(selection_only=False)
                    
                    if stl_data:
                        await websocket.send_json({
                            "type": "stl_exported",
                            "content": stl_data,
                            "message": "STL 文件导出成功"
                        })
                        print("✓ STL 已发送到前端")
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "content": "STL 导出失败，请确保场景中有对象"
                        })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "content": "Blender 未连接"
                    })
            
            elif message.get("type") == "export_model":
                # 导出模型（多格式支持）
                format_type = message.get("format", "stl").lower()
                selection_only = message.get("selection_only", False)
                
                print(f"\n📦 导出 {format_type.upper()} 文件...")
                await websocket.send_json({
                    "type": "status", 
                    "content": f"正在导出 {format_type.upper()}..."
                })
                
                if blender and blender.socket:
                    model_data = blender.export_model(
                        format_type=format_type,
                        selection_only=selection_only
                    )
                    
                    if model_data:
                        await websocket.send_json({
                            "type": "model_exported",
                            "content": model_data,
                            "format": format_type,
                            "message": f"{format_type.upper()} 文件导出成功"
                        })
                        print(f"✓ {format_type.upper()} 已发送到前端")
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "content": f"{format_type.upper()} 导出失败，请确保场景中有对象"
                        })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "content": "Blender 未连接"
                    })
                    
    except WebSocketDisconnect:
        print("✗ 前端断开连接")
    except Exception as e:
        print(f"错误: {e}")
        await websocket.send_json({"type": "error", "content": str(e)})

async def handle_stream_chat(websocket: WebSocket, user_input: str, blender_client, ai_agent):
    """处理流式对话（多步推理模式）"""
    try:
        # 获取场景信息
        scene_info = blender_client.get_scene_info() if blender_client else None
        
        # 流式生成响应
        async for event in ai_agent.generate_response_stream(user_input, scene_info):
            event_type = event.get("type")
            
            if event_type == "thinking":
                # 发送思考过程
                await websocket.send_json({
                    "type": "thinking",
                    "content": event.get("content", "")
                })
            
            elif event_type == "plan":
                # 发送执行计划
                await websocket.send_json({
                    "type": "plan",
                    "content": event.get("content", "")
                })
            
            elif event_type == "step_start":
                # 发送步骤开始
                await websocket.send_json({
                    "type": "step_start",
                    "step": event.get("step"),
                    "total": event.get("total"),
                    "description": event.get("description", "")
                })
            
            elif event_type == "code":
                # 发送代码
                code = event.get("code", "")
                step = event.get("step", 1)
                explanation = event.get("explanation", "")
                is_final = event.get("is_final", True)
                
                await websocket.send_json({
                    "type": "code",
                    "content": code,
                    "step": step,
                    "explanation": explanation
                })
                
                # 执行代码
                if code and blender_client and blender_client.socket:
                    await websocket.send_json({
                        "type": "status",
                        "content": f"执行步骤 {step}..."
                    })
                    
                    result = blender_client.execute_code(code)
                    print(f"步骤 {step} 执行结果: {result}")
                    
                    # 发送执行结果
                    await websocket.send_json({
                        "type": "execution_result",
                        "content": result or "执行完成",
                        "step": step
                    })
                    
                    # 如果是最后一步，获取截图并导出 STL
                    if is_final:
                        # 获取截图
                        screenshot = blender_client.get_screenshot()
                        if screenshot:
                            await websocket.send_json({
                                "type": "screenshot",
                                "content": screenshot
                            })
                        
                        # 自动导出 STL
                        await websocket.send_json({
                            "type": "status",
                            "content": "正在生成 3D 预览..."
                        })
                        
                        stl_data = blender_client.export_stl(selection_only=False)
                        if stl_data:
                            await websocket.send_json({
                                "type": "stl_exported",
                                "content": stl_data,
                                "message": "3D 模型已加载",
                                "auto": True
                            })
                            print("✓ STL 已自动导出并发送")
            
            elif event_type == "completed":
                # 任务完成
                await websocket.send_json({
                    "type": "response",
                    "content": "✓ 所有步骤执行完成"
                })
            
            elif event_type == "error":
                # 错误
                await websocket.send_json({
                    "type": "error",
                    "content": event.get("message", "未知错误")
                })
    
    except Exception as e:
        print(f"流式处理错误: {e}")
        import traceback
        traceback.print_exc()
        await websocket.send_json({
            "type": "error",
            "content": f"处理失败: {str(e)}"
        })

async def handle_standard_chat(websocket: WebSocket, user_input: str, blender_client, ai_agent):
    """处理标准对话（单步模式）"""
    # 发送状态
    await websocket.send_json({"type": "status", "content": "AI 思考中..."})
    
    # 使用 AIAgent 生成响应
    ai_response = await ai_agent.generate_response(
        user_message=user_input,
        conversation_history=[],
        blender_client=blender_client
    )
    
    # 从 AI 响应中提取代码
    response_type = ai_response.get("type", "")
    code_to_execute = ai_response.get("code", "")
    response_message = ai_response.get("message", "")
    
    # 根据响应类型处理
    if response_type == "code" and code_to_execute:
        # 发送代码
        await websocket.send_json({"type": "code", "content": code_to_execute})
        
        # 执行代码
        await websocket.send_json({"type": "status", "content": "Blender 执行中..."})
        
        if blender_client and blender_client.socket and code_to_execute:
            result = blender_client.execute_code(code_to_execute)
            print(f"执行结果: {result}")
        
        # 获取截图
        screenshot = blender_client.get_screenshot() if blender_client else None
        if screenshot:
            await websocket.send_json({"type": "screenshot", "content": screenshot})
        
        # 自动导出 STL（如果是建模操作）
        if blender_client and blender_client.socket:
            await websocket.send_json({"type": "status", "content": "正在生成 3D 预览..."})
            
            stl_data = blender_client.export_stl(selection_only=False)
            if stl_data:
                await websocket.send_json({
                    "type": "stl_exported",
                    "content": stl_data,
                    "message": "3D 模型已加载",
                    "auto": True
                })
                print("✓ STL 已自动导出并发送")
        
        # 发送完成消息
        await websocket.send_json({
            "type": "response",
            "content": response_message,
            "code": code_to_execute,
            "explanation": ai_response.get("explanation", "")
        })
    elif response_type == "chat":
        # 聊天响应，不需要执行代码
        await websocket.send_json({
            "type": "response",
            "content": response_message
        })
    elif response_type == "info":
        # 信息响应
        await websocket.send_json({
            "type": "response",
            "content": response_message,
            "data": ai_response.get("data", {})
        })
    else:
        # 其他类型的响应
        await websocket.send_json({
            "type": "response",
            "content": response_message or "操作完成",
            "code": code_to_execute
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)