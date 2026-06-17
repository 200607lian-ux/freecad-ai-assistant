"""
main_freecad_ai.py - FastAPI 后端主程序 (AI + RPC 直连版)
集成 AI 代码生成与 FreeCAD RPC 控制

使用方法:
1. 在 FreeCAD 中启动 RPC Server
2. 设置环境变量: DASHSCOPE_API_KEY=your_api_key
3. 运行: python main_freecad_ai.py
4. 访问: http://localhost:8001
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import asyncio
import os
import time
from pathlib import Path
import sys
import base64
import io
from PIL import Image

# 添加 backend 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from freecad_rpc_client import FreeCADRPCClient
from ai_agent_freecad import AIAgent

# 创建应用
app = FastAPI(title="FreeCAD AI 助手 - AI+RPC 版")

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
screenshot_lock = asyncio.Lock()
last_reconnect_attempt = 0
RECONNECT_INTERVAL = 5  # 重连尝试最小间隔（秒）

async def ensure_freecad_connection():
    """确保 FreeCAD 连接可用，断开时自动尝试重连"""
    global freecad, last_reconnect_attempt
    
    if freecad is None:
        freecad = FreeCADRPCClient(host="localhost", port=9875)
    
    if freecad.connected:
        return True
    
    now = time.time()
    if now - last_reconnect_attempt < RECONNECT_INTERVAL:
        return False
    
    last_reconnect_attempt = now
    
    try:
        loop = asyncio.get_event_loop()
        connected = await asyncio.wait_for(
            loop.run_in_executor(None, freecad.connect),
            timeout=5
        )
        if connected:
            print("[OK] FreeCAD 重新连接成功")
            docs = await asyncio.wait_for(
                loop.run_in_executor(None, freecad.list_documents),
                timeout=5
            )
            print(f"   文档列表: {docs}")
        return connected
    except asyncio.TimeoutError:
        print("[WARN] FreeCAD 重连超时")
        return False
    except Exception as e:
        print(f"[WARN] FreeCAD 重连失败: {e}")
        return False

# 获取端口（从环境变量或默认）
def get_server_port():
    import os
    return int(os.environ.get('FREECAD_AI_PORT', 8001))

@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    global freecad, ai_agent
    
    port = get_server_port()
    
    print("\n" + "="*60)
    print("FreeCAD AI 助手后端启动")
    print(f"端口: {port}")
    print("="*60)
    
    # 连接 FreeCAD RPC
    print("\n[1/2] 连接 FreeCAD RPC 服务器...")
    try:
        freecad = FreeCADRPCClient(host="localhost", port=9875)
        if freecad.connect():
            print("[OK] FreeCAD 连接成功")
            try:
                docs = freecad.list_documents()
                print(f"   文档列表: {docs}")
            except Exception as e:
                print(f"[WARN] 获取文档列表失败: {e}")
        else:
            print("[FAIL] FreeCAD 连接失败")
            print("   请确保 FreeCAD 中已启动 RPC Server")
    except Exception as e:
        print(f"[FAIL] FreeCAD 初始化失败: {e}")
        freecad = None
    
    # 初始化 AI
    print("\n[2/2] 初始化 AI 代码生成引擎...")
    ai_agent = AIAgent(use_ai=True)
    
    if ai_agent.client:
        print("[OK] AI 模式: 使用 DeepSeek-V4-Flash 模型")
        print("   提供商: 阿里云百炼")
    else:
        print("[WARN] AI 模式: 规则引擎（降级模式）")
        print("   原因: 未找到 DASHSCOPE_API_KEY 环境变量")
        print("   设置方法: set DASHSCOPE_API_KEY=your_api_key")
    
    print("\n" + "-"*60)
    print(f"服务地址: http://localhost:{port}")
    print(f"WebSocket: ws://localhost:{port}/ws")
    print(f"健康检查: http://localhost:{port}/health")
    print("="*60 + "\n")

# ===================================
# 静态文件服务
# ===================================

frontend_dir = Path(__file__).parent.parent / "frontend"

if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")
    print(f"[OK] 静态文件服务已启用: {frontend_dir}")

@app.get("/")
async def root():
    """返回前端页面"""
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "FreeCAD AI 助手运行中", "status": "ok"}

@app.get("/health")
async def health():
    """健康检查"""
    # 如果 FreeCAD 断开，尝试自动重连
    await ensure_freecad_connection()
    
    ai_status = "ai_enabled" if (ai_agent and ai_agent.client) else "rule_engine"
    
    return {
        "status": "ok",
        "cad_software": "FreeCAD",
        "freecad_connected": freecad is not None and freecad.connected,
        "ai_mode": ai_status,
        "ai_model": "deepseek-v4-flash" if ai_status == "ai_enabled" else None,
        "supported_operations": [
            "create_object", "edit_object", "delete_object",
            "execute_code", "get_screenshot", "fem_analysis"
        ]
    }

@app.get("/api/ai/status")
async def ai_status():
    """获取 AI 状态"""
    if ai_agent and ai_agent.client:
        return {
            "enabled": True,
            "mode": "ai",
            "model": "deepseek-v4-flash",
            "provider": "阿里云百炼",
            "features": [
                "自然语言理解",
                "FreeCAD CAD 建模指令",
                "智能代码生成",
                "材质和颜色设置",
                "布尔运算"
            ]
        }
    else:
        return {
            "enabled": False,
            "mode": "rule_engine",
            "features": ["基础几何体创建", "简单操作"],
            "recommendation": "设置 DASHSCOPE_API_KEY 环境变量以启用完整 AI 功能"
        }

# ===================================
# WebSocket 通信端点
# ===================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 通信端点 - 处理 AI 对话"""
    await websocket.accept()
    print("[OK] 前端已连接")
    
    # 前端连接时尝试恢复 FreeCAD 连接
    await ensure_freecad_connection()
    
    # 对话历史
    conversation_history = []
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            msg_type = message.get("type", "")
            
            if msg_type == "chat":
                # 处理 AI 聊天消息
                user_input = message.get("content", "")
                print(f"\n[用户] {user_input}")
                
                await handle_ai_chat(websocket, user_input, conversation_history)
                
            elif msg_type == "execute_code":
                # 直接执行代码
                await handle_execute_code(websocket, message)
                
            elif msg_type == "get_scene":
                # 获取场景信息
                await handle_get_scene(websocket)
                
            elif msg_type == "get_screenshot":
                # 获取截图
                await handle_get_screenshot(websocket, message)
                
            elif msg_type == "export":
                # 导出模型
                await handle_export(websocket, message)
                
            elif msg_type == "export_stl":
                # 导出 STL 用于 3D 预览
                await handle_export(websocket, {"format": "stl"})
                
            elif msg_type == "create_object":
                # 直接创建对象
                await handle_create_object(websocket, message)
                
    except WebSocketDisconnect:
        print("[OK] 前端断开连接")
    except asyncio.CancelledError:
        # 服务器关闭时正常取消，不打印堆栈
        pass
    except Exception as e:
        print(f"[ERROR] WebSocket 错误: {e}")
        import traceback
        traceback.print_exc()


async def handle_ai_chat(websocket: WebSocket, user_input: str, conversation_history: list):
    """处理 AI 聊天 - 生成代码并执行"""
    try:
        # 发送思考状态
        await websocket.send_json({"type": "status", "content": "AI 思考中..."})
        
        # 使用 AI 生成响应
        ai_response = await ai_agent.generate_response(
            user_message=user_input,
            conversation_history=conversation_history,
            blender_client=freecad  # 参数名保持兼容
        )
        
        # 保存对话历史
        conversation_history.append({"role": "user", "content": user_input})
        
        response_type = ai_response.get("type", "")
        code_to_execute = ai_response.get("code", "")
        response_message = ai_response.get("message", "")
        explanation = ai_response.get("explanation", "")
        
        if response_type == "code" and code_to_execute:
            # 发送生成的代码
            await websocket.send_json({"type": "code", "content": code_to_execute})
            
            # 执行代码前确保 FreeCAD 已连接
            if not await ensure_freecad_connection():
                await websocket.send_json({
                    "type": "error",
                    "content": "FreeCAD 未连接，请检查 FreeCAD 是否已启动 RPC Server"
                })
                return
            
            await websocket.send_json({"type": "status", "content": "FreeCAD 执行中..."})
            
            try:
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, freecad.execute_code, code_to_execute),
                    timeout=60
                )
                
                if result.get("success"):
                    print(f"[OK] 代码执行成功")
                    
                    # 获取截图
                    await websocket.send_json({"type": "status", "content": "生成预览..."})
                    
                    try:
                        image = await asyncio.wait_for(
                            loop.run_in_executor(None, freecad.get_screenshot, "Isometric"),
                            timeout=30
                        )
                        
                        if image:
                            # 转换为 base64
                            buffer = io.BytesIO()
                            image.save(buffer, format="PNG")
                            img_str = base64.b64encode(buffer.getvalue()).decode()
                            
                            await websocket.send_json({
                                "type": "screenshot",
                                "content": img_str,
                                "message": "3D 预览已更新"
                            })
                    except Exception as e:
                        print(f"[WARN] 截图失败: {e}")
                    
                    # 发送成功响应
                    await websocket.send_json({
                        "type": "response",
                        "content": response_message,
                        "code": code_to_execute,
                        "explanation": explanation,
                        "output": result.get("message", "")[:500]
                    })
                else:
                    error_msg = result.get("error", "未知错误")
                    print(f"[FAIL] 代码执行失败: {error_msg}")
                    await websocket.send_json({
                        "type": "error",
                        "content": f"执行失败: {error_msg}",
                        "code": code_to_execute
                    })
                    
            except asyncio.TimeoutError:
                print("[FAIL] 代码执行超时")
                await websocket.send_json({"type": "error", "content": "代码执行超时"})
            except Exception as e:
                print(f"[FAIL] 执行错误: {e}")
                await websocket.send_json({"type": "error", "content": f"执行错误: {str(e)}"})
                
        elif response_type == "chat":
            # 纯聊天响应
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
            await websocket.send_json({
                "type": "response",
                "content": response_message or "操作完成"
            })
        
        # 保存 AI 响应到历史
        conversation_history.append({
            "role": "assistant",
            "content": response_message,
            "code": code_to_execute
        })
        
    except Exception as e:
        print(f"[ERROR] AI 处理失败: {e}")
        import traceback
        traceback.print_exc()
        await websocket.send_json({
            "type": "error",
            "content": f"处理失败: {str(e)}"
        })


async def handle_execute_code(websocket: WebSocket, message: dict):
    """处理代码执行请求"""
    code = message.get("code", "")
    
    if not code:
        await websocket.send_json({"type": "error", "content": "代码为空"})
        return
    
    if freecad and freecad.connected:
        await websocket.send_json({"type": "status", "content": "执行代码中..."})
        
        try:
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, freecad.execute_code, code),
                timeout=60
            )
            
            if result.get("success"):
                await websocket.send_json({
                    "type": "code_executed",
                    "content": "代码执行成功",
                    "output": result.get("message", "")[:1000]
                })
            else:
                await websocket.send_json({
                    "type": "error",
                    "content": f"执行失败: {result.get('error', '未知错误')}"
                })
        except Exception as e:
            await websocket.send_json({"type": "error", "content": f"执行错误: {str(e)}"})
    else:
        await websocket.send_json({"type": "error", "content": "FreeCAD 未连接"})


async def handle_get_scene(websocket: WebSocket):
    """获取场景信息"""
    # 先检查连接是否仍然有效
    if freecad and freecad.connected:
        try:
            loop = asyncio.get_event_loop()
            is_alive = await asyncio.wait_for(
                loop.run_in_executor(None, freecad.health_check),
                timeout=3
            )
            if not is_alive:
                freecad.connected = False
        except Exception:
            freecad.connected = False
    
    # 如果连接断了，尝试重连
    if not (freecad and freecad.connected):
        connected = await ensure_freecad_connection()
        if not connected:
            try:
                await websocket.send_json({"type": "error", "content": "FreeCAD 未连接"})
            except:
                pass
            return
    
    if freecad and freecad.connected:
        try:
            loop = asyncio.get_event_loop()
            
            # 获取文档列表（使用 Label 显示）
            docs = await asyncio.wait_for(
                loop.run_in_executor(None, freecad.get_document_labels),
                timeout=10
            )
            
            print(f"[DEBUG] get_document_labels 返回: {docs}")
            
            scene_info = {"documents": {}, "doc_list": docs}
            
            # 使用内部名称获取对象，但用 Label 显示
            for doc_info in docs:
                try:
                    doc_name = doc_info.get("name", "")
                    doc_label = doc_info.get("label", doc_name)
                    
                    print(f"[DEBUG] 获取文档 {doc_name} (Label: {doc_label}) 的对象")
                    
                    objects = await asyncio.wait_for(
                        loop.run_in_executor(None, freecad.get_objects, doc_name),
                        timeout=10
                    )
                    scene_info["documents"][doc_label] = objects
                except Exception as e:
                    print(f"[ERROR] 获取文档 {doc_info} 的对象失败: {e}")
                    scene_info["documents"][doc_info.get("label", "unknown")] = []
            
            try:
                await websocket.send_json({
                    "type": "scene_info",
                    "content": scene_info
                })
            except Exception as e:
                print(f"[WARN] 发送场景信息失败，连接可能已关闭: {e}")
                
        except Exception as e:
            print(f"[ERROR] handle_get_scene 失败: {e}")
            import traceback
            traceback.print_exc()
            try:
                await websocket.send_json({"type": "error", "content": f"获取场景失败: {str(e)}"})
            except:
                pass
    else:
        try:
            await websocket.send_json({"type": "error", "content": "FreeCAD 未连接"})
        except:
            pass


async def handle_get_screenshot(websocket: WebSocket, message: dict):
    """获取截图（带全局锁，防止并发请求堆积）"""
    view_name = message.get("view_name", "Isometric")
    
    if not (freecad and freecad.connected):
        try:
            await websocket.send_json({"type": "error", "content": "FreeCAD 未连接"})
        except Exception:
            pass
        return
    
    # 全局锁保证同一时刻只执行一次截图，避免多次点击导致请求堆积
    async with screenshot_lock:
        try:
            await websocket.send_json({"type": "status", "content": "正在生成截图..."})
        except Exception:
            pass
        
        try:
            loop = asyncio.get_event_loop()
            image = await asyncio.wait_for(
                loop.run_in_executor(None, freecad.get_screenshot, view_name),
                timeout=30
            )
            
            if image:
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                img_str = base64.b64encode(buffer.getvalue()).decode()
                
                await websocket.send_json({
                    "type": "screenshot",
                    "content": img_str
                })
            else:
                await websocket.send_json({"type": "error", "content": "截图失败"})
        except asyncio.TimeoutError:
            try:
                await websocket.send_json({"type": "error", "content": "截图超时，请稍后重试"})
            except Exception:
                pass
        except Exception as e:
            try:
                await websocket.send_json({"type": "error", "content": f"截图错误: {str(e)}"})
            except Exception:
                pass


async def handle_create_object(websocket: WebSocket, message: dict):
    """处理创建对象请求"""
    doc_name = message.get("doc_name", "Unnamed")
    obj_type = message.get("obj_type", "Part::Box")
    obj_name = message.get("obj_name", "NewObject")
    properties = message.get("properties", {})
    
    if freecad and freecad.connected:
        await websocket.send_json({"type": "status", "content": "创建对象中..."})
        
        try:
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: freecad.create_object(
                    doc_name, obj_type, obj_name, properties
                )),
                timeout=30
            )
            
            if result.get("success"):
                await websocket.send_json({
                    "type": "object_created",
                    "content": f"对象 {obj_name} 创建成功"
                })
                
                # 自动获取截图
                await handle_get_screenshot(websocket, {"view_name": "Isometric"})
            else:
                await websocket.send_json({
                    "type": "error",
                    "content": f"创建失败: {result.get('error', '未知错误')}"
                })
        except Exception as e:
            await websocket.send_json({"type": "error", "content": f"创建错误: {str(e)}"})
    else:
        await websocket.send_json({"type": "error", "content": "FreeCAD 未连接"})


async def handle_export(websocket: WebSocket, message: dict):
    """处理导出请求"""
    export_format = message.get("format", "step").lower()
    
    # 支持的格式映射
    format_extensions = {
        "step": ".step",
        "stl": ".stl",
        "obj": ".obj",
        "iges": ".iges",
        "brep": ".brep",
        "csv": ".csv"
    }
    
    if export_format not in format_extensions:
        await websocket.send_json({
            "type": "export",
            "success": False,
            "error": f"不支持的格式: {export_format}"
        })
        return
    
    # 先检查连接是否仍然有效
    if freecad and freecad.connected:
        try:
            loop = asyncio.get_event_loop()
            is_alive = await asyncio.wait_for(
                loop.run_in_executor(None, freecad.health_check),
                timeout=3
            )
            if not is_alive:
                freecad.connected = False
        except Exception:
            freecad.connected = False
    
    # 如果连接断了，尝试重连
    if not (freecad and freecad.connected):
        connected = await ensure_freecad_connection()
        if not connected:
            await websocket.send_json({
                "type": "export",
                "success": False,
                "error": "FreeCAD 未连接"
            })
            return
    
    try:
        await websocket.send_json({
            "type": "status",
            "content": f"正在导出 {export_format.upper()} 格式..."
        })
        
        loop = asyncio.get_event_loop()
        
        # 获取活动文档名称
        docs = await asyncio.wait_for(
            loop.run_in_executor(None, freecad.list_documents),
            timeout=10
        )
        
        if not docs:
            await websocket.send_json({
                "type": "export",
                "success": False,
                "error": "没有活动文档"
            })
            return
        
        # 获取当前活动文档（而不是第一个文档）
        active_doc_result = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: freecad.execute_code("""
import FreeCAD
doc = FreeCAD.ActiveDocument
if doc:
    print(doc.Name)
else:
    print("")
""")
            ),
            timeout=10
        )
        
        doc_name = None
        if active_doc_result.get("success"):
            output = active_doc_result.get("message", "").strip()
            # 从输出中提取文档名（可能在 "Output:" 后面）
            if "Output:" in output:
                output = output.split("Output:")[-1].strip()
            if output in docs:
                doc_name = output
        
        if not doc_name:
            doc_name = docs[-1]  # 如果没有活动文档，使用最后一个文档（通常是最新打开的）
        
        ext = format_extensions[export_format]
        
        # 生成导出文件名
        import tempfile
        import time
        timestamp = int(time.time())
        export_path = os.path.join(tempfile.gettempdir(), f"freecad_export_{timestamp}{ext}")
        
        # 执行导出
        result = await asyncio.wait_for(
            loop.run_in_executor(
                None, 
                lambda: freecad.export_document(doc_name, export_path, export_format)
            ),
            timeout=60
        )
        
        if result.get("success"):
            # 读取导出的文件内容
            if export_format == "csv":
                # CSV 直接返回内容
                with open(export_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                await websocket.send_json({
                    "type": "export",
                    "success": True,
                    "format": export_format,
                    "filename": f"freecad_export_{timestamp}{ext}",
                    "content": content,
                    "mime_type": "text/csv"
                })
            else:
                # 二进制文件返回 base64
                with open(export_path, 'rb') as f:
                    file_data = f.read()
                
                file_b64 = base64.b64encode(file_data).decode()
                
                await websocket.send_json({
                    "type": "export",
                    "success": True,
                    "format": export_format,
                    "filename": f"freecad_export_{timestamp}{ext}",
                    "content": file_b64,
                    "is_base64": True,
                    "mime_type": get_mime_type(export_format)
                })
                
                # 如果是 STL 格式，额外发送 stl_exported 消息用于 3D 预览
                if export_format == "stl":
                    await websocket.send_json({
                        "type": "stl_exported",
                        "content": file_b64
                    })
            
            # 清理临时文件
            try:
                os.remove(export_path)
            except:
                pass
        else:
            await websocket.send_json({
                "type": "export",
                "success": False,
                "error": result.get("error", "导出失败")
            })
            
    except Exception as e:
        print(f"[ERROR] 导出失败: {e}")
        import traceback
        traceback.print_exc()
        # 确保即使异常也能清理临时文件
        try:
            if 'export_path' in locals() and export_path and os.path.exists(export_path):
                os.remove(export_path)
        except Exception:
            pass
        await websocket.send_json({
            "type": "export",
            "success": False,
            "error": f"导出错误: {str(e)}"
        })


def get_mime_type(format):
    """获取文件格式的 MIME 类型"""
    mime_types = {
        "step": "application/step",
        "stl": "application/vnd.ms-pki.stl",
        "obj": "text/plain",
        "iges": "application/iges",
        "brep": "application/octet-stream"
    }
    return mime_types.get(format, "application/octet-stream")


if __name__ == "__main__":
    import uvicorn
    
    # 从环境变量获取端口，如果没有则使用默认 8001
    port = int(os.environ.get('FREECAD_AI_PORT', 8001))
    
    uvicorn.run(app, host="0.0.0.0", port=port)
