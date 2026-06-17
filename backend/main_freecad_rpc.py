"""
main_freecad_rpc.py - FastAPI 后端主程序 (FreeCAD RPC 版本)
直接连接 freecad-mcp 的 RPC 服务器，绕过 MCP 协议

使用方法:
1. 在 FreeCAD 中启动 RPC Server（通过 FreeCADMCP addon）
2. 运行: python main_freecad_rpc.py
3. 访问: http://localhost:8001
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import asyncio
import os
from pathlib import Path
import sys

# 添加 backend 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from freecad_rpc_client import FreeCADRPCClient

# 创建应用
app = FastAPI(title="FreeCAD AI 助手 - RPC 直连版")

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

@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    global freecad
    
    print("\n" + "="*50)
    print("FreeCAD AI 助手后端启动 (RPC 直连版)")
    print("="*50)
    
    # 连接 FreeCAD RPC
    print("\n[1/1] 连接 FreeCAD RPC 服务器...")
    freecad = FreeCADRPCClient(host="localhost", port=9875)
    if freecad.connect():
        print("[OK] FreeCAD 连接成功")
        
        # 获取文档列表
        docs = freecad.list_documents()
        print(f"   文档列表: {docs}")
    else:
        print("[FAIL] FreeCAD 连接失败（某些功能将不可用）")
        print("   请确保:")
        print("     1. FreeCAD 已启动")
        print("     2. 在 FreeCAD 中执行了 'Start RPC Server'")
    
    print("\n" + "-"*50)
    print("服务地址: http://localhost:8001")
    print("WebSocket: ws://localhost:8001/ws")
    print("健康检查: http://localhost:8001/health")
    print("="*50 + "\n")

# ===================================
# 静态文件服务（前端页面）
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
    return {"message": "FreeCAD AI 助手运行中", "status": "ok", "frontend": "not_found"}

@app.get("/health")
async def health():
    """健康检查端点"""
    freecad_connected = freecad is not None and freecad.connected
    
    return {
        "status": "ok",
        "cad_software": "FreeCAD",
        "freecad_connected": freecad_connected,
        "connection_type": "RPC (XML-RPC)",
        "capabilities": {
            "create_object": freecad_connected,
            "edit_object": freecad_connected,
            "delete_object": freecad_connected,
            "execute_code": freecad_connected,
            "get_screenshot": freecad_connected,
            "fem_analysis": freecad_connected
        }
    }

# ===================================
# REST API 端点
# ===================================

@app.get("/api/documents")
async def get_documents():
    """获取文档列表"""
    if freecad and freecad.connected:
        docs = freecad.list_documents()
        return {"documents": docs}
    return {"error": "FreeCAD 未连接"}

@app.post("/api/documents")
async def create_document(name: str = "New_Document"):
    """创建新文档"""
    if freecad and freecad.connected:
        result = freecad.create_document(name)
        return result
    return {"error": "FreeCAD 未连接"}

@app.get("/api/documents/{doc_name}/objects")
async def get_objects(doc_name: str):
    """获取文档中的对象"""
    if freecad and freecad.connected:
        objects = freecad.get_objects(doc_name)
        return {"objects": objects}
    return {"error": "FreeCAD 未连接"}

@app.post("/api/documents/{doc_name}/objects")
async def create_object(doc_name: str, obj_type: str, obj_name: str, 
                       properties: dict = None):
    """创建对象"""
    if freecad and freecad.connected:
        result = freecad.create_object(doc_name, obj_type, obj_name, properties)
        return result
    return {"error": "FreeCAD 未连接"}

@app.post("/api/execute")
async def execute_code(code: str):
    """执行 Python 代码"""
    if freecad and freecad.connected:
        result = freecad.execute_code(code)
        return result
    return {"error": "FreeCAD 未连接"}

@app.get("/api/screenshot")
async def get_screenshot(view_name: str = "Isometric"):
    """获取截图"""
    if freecad and freecad.connected:
        image = freecad.get_screenshot(view_name)
        if image:
            # 返回 base64 编码的图片
            import io
            import base64
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode()
            return {"image": img_str}
        return {"error": "截图失败"}
    return {"error": "FreeCAD 未连接"}

# ===================================
# WebSocket 通信端点
# ===================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 通信端点"""
    await websocket.accept()
    print("[OK] 前端已连接")
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            msg_type = message.get("type", "")
            
            if msg_type == "chat":
                # 处理聊天消息
                user_input = message.get("content", "")
                print(f"\n用户: {user_input}")
                
                # 简单响应（可以集成 AI）
                await websocket.send_json({
                    "type": "response",
                    "content": f"收到消息: {user_input}"
                })
                
            elif msg_type == "create_object":
                # 创建对象
                if freecad and freecad.connected:
                    doc_name = message.get("doc_name", "Unnamed")
                    obj_type = message.get("obj_type", "Part::Box")
                    obj_name = message.get("obj_name", "NewObject")
                    properties = message.get("properties", {})
                    
                    await websocket.send_json({"type": "status", "content": "创建对象中..."})
                    
                    result = freecad.create_object(doc_name, obj_type, obj_name, properties)
                    
                    if result.get("success"):
                        await websocket.send_json({
                            "type": "object_created",
                            "content": f"对象 {obj_name} 创建成功"
                        })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "content": f"创建失败: {result.get('error', '未知错误')}"
                        })
                else:
                    await websocket.send_json({"type": "error", "content": "FreeCAD 未连接"})
                    
            elif msg_type == "execute_code":
                # 执行代码
                if freecad and freecad.connected:
                    code = message.get("code", "")
                    
                    await websocket.send_json({"type": "status", "content": "执行代码中..."})
                    
                    result = freecad.execute_code(code)
                    
                    if result.get("success"):
                        await websocket.send_json({
                            "type": "code_executed",
                            "content": result.get("message", "代码执行成功")
                        })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "content": f"执行失败: {result.get('error', '未知错误')}"
                        })
                else:
                    await websocket.send_json({"type": "error", "content": "FreeCAD 未连接"})
                    
            elif msg_type == "get_scene":
                # 获取场景信息
                if freecad and freecad.connected:
                    docs = freecad.list_documents()
                    scene_info = {
                        "documents": docs,
                        "objects": {}
                    }
                    for doc in docs:
                        scene_info["objects"][doc] = freecad.get_objects(doc)
                    
                    await websocket.send_json({
                        "type": "scene_info",
                        "content": scene_info
                    })
                else:
                    await websocket.send_json({"type": "error", "content": "FreeCAD 未连接"})
                    
            elif msg_type == "get_screenshot":
                # 获取截图
                if freecad and freecad.connected:
                    view_name = message.get("view_name", "Isometric")
                    image = freecad.get_screenshot(view_name)
                    
                    if image:
                        import io
                        import base64
                        buffer = io.BytesIO()
                        image.save(buffer, format="PNG")
                        img_str = base64.b64encode(buffer.getvalue()).decode()
                        
                        await websocket.send_json({
                            "type": "screenshot",
                            "content": img_str
                        })
                    else:
                        await websocket.send_json({"type": "error", "content": "截图失败"})
                else:
                    await websocket.send_json({"type": "error", "content": "FreeCAD 未连接"})
                    
    except WebSocketDisconnect:
        print("[OK] 前端断开连接")
    except Exception as e:
        print(f"[FAIL] 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
