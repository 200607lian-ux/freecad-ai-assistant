"""
main_freecad.py - FastAPI 后端主程序 (FreeCAD 版本)
作用：提供 WebSocket 接口，处理前端请求，连接 FreeCAD
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import asyncio
import os
from pathlib import Path

from freecad_client import FreeCADClient
from ai_agent_freecad import AIAgent

# 创建应用
app = FastAPI(title="FreeCAD AI 助手")

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
freecad = None
ai_agent = None

@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    global freecad, ai_agent
    
    print("\n" + "="*50)
    print("FreeCAD AI 助手后端启动")
    print("="*50)
    
    # 连接 FreeCAD
    print("\n[1/2] 连接 FreeCAD MCP 服务器...")
    freecad = FreeCADClient()
    if freecad.connect():
        print("✓ FreeCAD 连接成功")
    else:
        print("✗ FreeCAD 连接失败（某些功能将不可用）")
    
    # 初始化 AI
    print("\n[2/2] 初始化 AI 代码生成引擎...")
    ai_agent = AIAgent(use_ai=True)
    
    # 检查 AI 状态
    if ai_agent.client:
        print("✓ AI 模式：使用 DeepSeek-V4-Flash 模型")
        print("  提供商：阿里云百炼")
        print("  能力：智能理解自然语言，生成 FreeCAD 建模代码")
    else:
        print("⚠️  AI 模式：规则引擎（降级模式）")
        print("  原因：未找到 DASHSCOPE_API_KEY 环境变量")
        print("  能力：基础几何体创建和简单操作")
    
    print("\n" + "-"*50)
    print("服务地址: http://localhost:8001")
    print("WebSocket: ws://localhost:8001/ws")
    print("健康检查: http://localhost:8001/health")
    print("="*50 + "\n")
    print("💡 提示：")
    print("  - 前端可通过 WebSocket 发送自然语言指令")
    print("  - 支持 CAD 建模描述，如「创建一个红色的立方体」")
    print("  - AI 会自动生成并执行 FreeCAD Python 代码")
    print("  - 支持导出 STEP、IGES、STL 等多种格式")
    print("="*50 + "\n")

# ===================================
# 静态文件服务（前端页面）
# ===================================

frontend_dir = Path(__file__).parent.parent / "frontend"

if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")
    print(f"✓ 静态文件服务已启用: {frontend_dir}")

@app.get("/")
async def root():
    """返回前端页面"""
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "FreeCAD AI 助手运行中", "status": "ok", "frontend": "not_found"}

@app.get("/health")
async def health():
    """健康检查端点"""
    ai_status = "ai_enabled" if (ai_agent and ai_agent.client) else "rule_engine"
    
    return {
        "status": "ok",
        "cad_software": "FreeCAD",
        "freecad_connected": freecad is not None and freecad.connected,
        "ai_mode": ai_status,
        "ai_model": "deepseek-v4-flash" if ai_status == "ai_enabled" else None,
        "supported_formats": ["step", "stp", "iges", "igs", "stl", "obj", "brep"],
        "capabilities": {
            "natural_language": ai_status == "ai_enabled",
            "complex_modeling": ai_status == "ai_enabled",
            "basic_operations": True,
            "cad_export": True
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
            "cad_software": "FreeCAD",
            "features": [
                "自然语言理解",
                "FreeCAD CAD 建模指令",
                "智能代码生成",
                "材质和颜色设置",
                "布尔运算",
                "STEP/IGES 导出"
            ],
            "examples": [
                "创建一个红色的立方体",
                "在位置(20,0,0)创建一个蓝色球体",
                "创建球体和立方体的并集",
                "创建一个绿色的圆柱体，半径5，高度10"
            ]
        }
    else:
        return {
            "enabled": False,
            "mode": "rule_engine",
            "model": None,
            "cad_software": "FreeCAD",
            "features": [
                "基础几何体创建",
                "简单移动操作",
                "删除对象"
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
                
                # 使用标准响应模式
                await handle_standard_chat(websocket, user_input, freecad, ai_agent)
                
            elif message.get("type") == "get_scene":
                try:
                    if freecad and freecad.connected:
                        loop = asyncio.get_event_loop()
                        scene = await asyncio.wait_for(
                            loop.run_in_executor(None, freecad.get_scene_info),
                            timeout=10
                        )
                    else:
                        scene = None
                    await websocket.send_json({"type": "scene_info", "content": scene})
                except Exception as e:
                    print(f"获取场景信息失败: {e}")
                    await websocket.send_json({"type": "error", "content": f"获取场景信息失败: {str(e)}"})
            
            elif message.get("type") == "export_stl":
                # 导出 STL 文件（用于 3D 预览）
                print("\n📦 导出 STL 文件...")
                await websocket.send_json({"type": "status", "content": "正在导出 STL..."})
                
                if freecad and freecad.connected:
                    try:
                        loop = asyncio.get_event_loop()
                        stl_data = await asyncio.wait_for(
                            loop.run_in_executor(None, freecad.export_stl, False),
                            timeout=30
                        )
                        
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
                                "content": "STL 导出失败，请确保文档中有对象"
                            })
                    except asyncio.TimeoutError:
                        await websocket.send_json({"type": "error", "content": "STL 导出超时"})
                    except Exception as e:
                        await websocket.send_json({"type": "error", "content": f"STL 导出错误: {str(e)}"})
                else:
                    await websocket.send_json({
                        "type": "error",
                        "content": "FreeCAD 未连接"
                    })
            
            elif message.get("type") == "export_model":
                # 导出模型（多格式支持）
                format_type = message.get("format", "step").lower()
                selection_only = message.get("selection_only", False)
                
                print(f"\n📦 导出 {format_type.upper()} 文件...")
                await websocket.send_json({
                    "type": "status", 
                    "content": f"正在导出 {format_type.upper()}..."
                })
                
                if freecad and freecad.connected:
                    try:
                        loop = asyncio.get_event_loop()
                        model_data = await asyncio.wait_for(
                            loop.run_in_executor(None, lambda: freecad.export_model(
                                format_type=format_type,
                                selection_only=selection_only
                            )),
                            timeout=30
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
                                "content": f"{format_type.upper()} 导出失败，请确保文档中有对象"
                            })
                    except asyncio.TimeoutError:
                        await websocket.send_json({"type": "error", "content": f"{format_type.upper()} 导出超时"})
                    except Exception as e:
                        await websocket.send_json({"type": "error", "content": f"导出错误: {str(e)}"})
                else:
                    await websocket.send_json({
                        "type": "error",
                        "content": "FreeCAD 未连接"
                    })
                    
    except WebSocketDisconnect:
        print("✗ 前端断开连接")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        await websocket.send_json({"type": "error", "content": str(e)})

async def handle_standard_chat(websocket: WebSocket, user_input: str, freecad_client, ai_agent):
    """处理标准对话（单步模式）"""
    try:
        # 发送状态
        await websocket.send_json({"type": "status", "content": "AI 思考中..."})
        
        # 使用 AIAgent 生成响应
        ai_response = await ai_agent.generate_response(
            user_message=user_input,
            conversation_history=[],
            blender_client=freecad_client  # 参数名保持兼容
        )
        
        # 从 AI 响应中提取代码
        response_type = ai_response.get("type", "")
        code_to_execute = ai_response.get("code", "")
        response_message = ai_response.get("message", "")
        
        # 根据响应类型处理
        if response_type == "code" and code_to_execute:
            # 发送代码
            await websocket.send_json({"type": "code", "content": code_to_execute})
            
            # 执行代码（在线程池中执行，避免阻塞事件循环）
            await websocket.send_json({"type": "status", "content": "FreeCAD 执行中..."})
            
            if freecad_client and freecad_client.connected and code_to_execute:
                try:
                    # 使用线程池执行同步 Socket 操作
                    loop = asyncio.get_event_loop()
                    result = await asyncio.wait_for(
                        loop.run_in_executor(None, freecad_client.execute_code, code_to_execute),
                        timeout=30
                    )
                    print(f"执行结果: {result}")
                except asyncio.TimeoutError:
                    print("✗ FreeCAD 代码执行超时")
                    await websocket.send_json({"type": "error", "content": "FreeCAD 执行超时"})
                    return
                except Exception as e:
                    print(f"✗ FreeCAD 执行错误: {e}")
                    await websocket.send_json({"type": "error", "content": f"FreeCAD 执行错误: {str(e)}"})
                    return
            
            # 自动导出 STL（如果是建模操作）
            if freecad_client and freecad_client.connected:
                await websocket.send_json({"type": "status", "content": "正在生成 3D 预览..."})
                
                try:
                    loop = asyncio.get_event_loop()
                    stl_data = await asyncio.wait_for(
                        loop.run_in_executor(None, freecad_client.export_stl, False),
                        timeout=30
                    )
                    if stl_data:
                        await websocket.send_json({
                            "type": "stl_exported",
                            "content": stl_data,
                            "message": "3D 模型已加载",
                            "auto": True
                        })
                        print("✓ STL 已自动导出并发送")
                except asyncio.TimeoutError:
                    print("✗ STL 导出超时")
                    await websocket.send_json({"type": "error", "content": "STL 导出超时"})
                except Exception as e:
                    print(f"✗ STL 导出错误: {e}")
            
            # 发送完成消息
            await websocket.send_json({
                "type": "response",
                "content": response_message,
                "code": code_to_execute,
                "explanation": ai_response.get("explanation", "")
            })
        elif response_type == "chat":
            # 聊天响应
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
            # 其他类型响应
            await websocket.send_json({
                "type": "response",
                "content": response_message or "操作完成",
                "code": code_to_execute
            })
    
    except Exception as e:
        print(f"处理失败: {e}")
        import traceback
        traceback.print_exc()
        await websocket.send_json({
            "type": "error",
            "content": f"处理失败: {str(e)}"
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
