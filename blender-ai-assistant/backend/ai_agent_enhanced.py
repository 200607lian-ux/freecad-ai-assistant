"""
增强版 AI Agent - 支持多步思考和执行
实现类似 Cursor 的分步推理功能
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from openai import OpenAI

@dataclass
class ThinkingStep:
    """思考步骤"""
    step_number: int
    thought: str  # 思考内容
    action: str  # 计划的动作
    code: Optional[str] = None  # 生成的代码
    result: Optional[str] = None  # 执行结果

class EnhancedAIAgent:
    """增强版 AI 代理 - 支持多步推理"""
    
    def __init__(self, use_ai: bool = True):
        """初始化 AI 代理"""
        self.use_ai = use_ai
        self.client = None
        
        if use_ai:
            api_key = os.getenv("DASHSCOPE_API_KEY")
            if api_key:
                try:
                    self.client = OpenAI(
                        api_key=api_key,
                        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                    )
                    print("✓ 增强版 AI Agent 已启用（支持多步推理）")
                except Exception as e:
                    print(f"⚠️  AI 客户端初始化失败: {e}")
                    self.client = None
            else:
                print("⚠️  未找到 DASHSCOPE_API_KEY")
        
        # 系统提示词 - 引导 AI 进行分步思考
        self.system_prompt = """你是一个专业的 Blender Python 代码生成助手，擅长将复杂任务拆解为清晰的步骤。

## 工作模式

对于复杂任务，你需要：
1. **分析任务**：理解用户意图，识别子任务
2. **制定计划**：将任务拆解为 2-5 个步骤
3. **逐步执行**：每次只生成一个步骤的代码

## 响应格式

你的响应必须是 JSON 格式：

**简单任务（单步）**：
```json
{
  "type": "single_step",
  "thought": "这是一个简单的创建球体任务",
  "code": "import bpy\\nbpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0,0,0))\\nprint('已创建球体')"
}
```

**复杂任务（多步）**：
```json
{
  "type": "multi_step",
  "thought": "这个任务需要3个步骤：设置材质、布光、配置渲染器",
  "total_steps": 3,
  "current_step": 1,
  "step_description": "步骤1: 设置红色金属材质",
  "code": "import bpy\\n# 材质代码...",
  "next_steps": ["步骤2: 添加三点布光", "步骤3: 切换为Cycles渲染器"]
}
```

## 任务类型判断

**简单任务**（单步）：
- 创建单个对象："创建一个球体"
- 删除对象："删除所有物体"
- 简单移动："把立方体移动到(1,2,3)"

**复杂任务**（多步）：
- 涉及多个操作："创建球体，设置红色，添加灯光"
- 材质+灯光+渲染设置
- 场景布置："创建一个产品展示场景"

## Blender 代码规范

- 所有代码必须以 `import bpy` 开头
- 使用 print() 输出执行结果
- 代码必须能直接在 Blender Python 控制台运行
- 错误处理：检查对象是否存在

## 坐标轴约定（重要）

Blender 使用 Z 轴向上坐标系，但大多数 3D 查看器（如 Three.js）使用 Y 轴向上。
创建几何体时，请确保：
1. 默认创建在 XY 平面上（z=0）
2. 尺寸使用正确的轴：x=宽度，y=深度，z=高度

示例：
```python
# 创建立方体，x=2, y=4, z=6（Blender 中 z 是向上）
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
cube = bpy.context.object
cube.scale = (1, 2, 3)  # 缩放会改变尺寸
# 或者直接设置尺寸
cube.dimensions = (2, 4, 6)
```

## 材质设置（重要）

设置材质时必须按照以下模板，确保颜色正确显示：

```python
import bpy

# 1. 获取对象
obj = bpy.context.view_layer.objects.active
if not obj or obj.type != 'MESH':
    # 查找场景中的第一个 MESH 对象
    for o in bpy.context.scene.objects:
        if o.type == 'MESH':
            obj = o
            bpy.context.view_layer.objects.active = obj
            break

if obj and obj.type == 'MESH':
    # 2. 创建材质
    mat_name = "材质名称"
    mat = bpy.data.materials.get(mat_name)
    if mat is None:
        mat = bpy.data.materials.new(name=mat_name)
    
    # 3. 启用节点并清除旧节点
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    # 4. 创建 Principled BSDF
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    
    # 5. 设置材质属性（重要：确保正确设置）
    bsdf.inputs['Base Color'].default_value = (r, g, b, 1.0)  # 基础色
    bsdf.inputs['Metallic'].default_value = 0.9  # 金属度
    bsdf.inputs['Roughness'].default_value = 0.1  # 粗糙度
    
    # 6. 创建输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # 7. 连接节点
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    # 8. 应用材质
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    
    # 9. 设置对象颜色（Solid 模式显示）
    obj.color = (r, g, b, 1.0)
    
    print(f"✓ 已设置材质")
```

## 示例

用户: "创建一个蓝色的球体"
→ 简单任务，单步完成

用户: "创建一个红色金属立方体，粗糙度0.1，金属度0.9，添加三点布光，切换为Cycles渲染器，采样128"
→ 复杂任务，拆解为：
  步骤1: 创建立方体并设置红色金属材质
  步骤2: 添加三点布光（主光、补光、背光）
  步骤3: 切换渲染器为Cycles，设置采样数

记住：
- 复杂任务必须拆解
- 每次只返回一个步骤的代码
- 保持思考过程清晰
- JSON 格式必须正确
- 材质设置必须清除旧节点并正确连接
"""
    
    async def generate_response_stream(
        self, 
        user_message: str,
        scene_info: Optional[Dict] = None,
        conversation_history: List[Dict] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式生成响应 - 支持多步思考和执行
        
        Yields:
            字典，包含 type 和相应的数据
            - type: "thinking" - 思考过程
            - type: "code" - 生成的代码
            - type: "execution_result" - 执行结果
            - type: "completed" - 完成
        """
        if not self.client:
            # 降级到简单模式
            yield {
                "type": "code",
                "code": "# AI 未启用，请配置 DASHSCOPE_API_KEY",
                "explanation": "AI 功能未启用"
            }
            return
        
        try:
            # 构建消息
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # 添加场景信息（如果有）
            if scene_info:
                scene_context = f"\n\n当前场景信息：\n{json.dumps(scene_info, ensure_ascii=False, indent=2)}"
                messages.append({"role": "system", "content": scene_context})
            
            # 添加对话历史
            if conversation_history:
                messages.extend(conversation_history[-4:])  # 只保留最近4轮
            
            # 添加用户消息
            messages.append({"role": "user", "content": user_message})
            
            # 第一次调用：分析任务
            yield {"type": "thinking", "content": "正在分析任务..."}
            
            response = self.client.chat.completions.create(
                model="deepseek-v4-flash",
                messages=messages,
                temperature=0.3,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            # 解析 JSON 响应
            try:
                response_data = self._parse_json_response(content)
            except Exception as e:
                # 如果不是 JSON 格式，尝试提取代码
                print(f"⚠️  响应不是 JSON 格式，尝试提取代码: {e}")
                code = self._extract_code(content)
                yield {
                    "type": "code",
                    "code": code,
                    "explanation": "生成代码",
                    "is_final": True
                }
                yield {"type": "completed"}
                return
            
            # 处理单步任务
            if response_data.get("type") == "single_step":
                thought = response_data.get("thought", "")
                code = response_data.get("code", "")
                
                if thought:
                    yield {"type": "thinking", "content": thought}
                
                yield {
                    "type": "code",
                    "code": code,
                    "explanation": thought,
                    "is_final": True
                }
                yield {"type": "completed"}
                return
            
            # 处理多步任务
            elif response_data.get("type") == "multi_step":
                total_steps = response_data.get("total_steps", 1)
                current_step = response_data.get("current_step", 1)
                thought = response_data.get("thought", "")
                step_desc = response_data.get("step_description", f"步骤 {current_step}")
                code = response_data.get("code", "")
                next_steps = response_data.get("next_steps", [])
                
                # 显示总体思考
                if thought:
                    yield {"type": "thinking", "content": f"📋 任务规划：{thought}"}
                
                # 显示所有步骤计划
                if next_steps:
                    plan = f"共 {total_steps} 个步骤：\n"
                    plan += f"✓ {step_desc}\n"
                    for i, next_step in enumerate(next_steps, start=current_step + 1):
                        plan += f"  {i}. {next_step}\n"
                    yield {"type": "plan", "content": plan}
                
                # 执行第一步
                yield {
                    "type": "step_start",
                    "step": current_step,
                    "total": total_steps,
                    "description": step_desc
                }
                
                yield {
                    "type": "code",
                    "code": code,
                    "step": current_step,
                    "explanation": step_desc,
                    "is_final": current_step >= total_steps
                }
                
                # 如果还有后续步骤，继续生成
                if current_step < total_steps:
                    # 将当前步骤加入历史
                    messages.append({"role": "assistant", "content": content})
                    
                    # 请求下一步
                    for step_num in range(current_step + 1, total_steps + 1):
                        yield {"type": "thinking", "content": f"准备执行步骤 {step_num}..."}
                        
                        messages.append({
                            "role": "user", 
                            "content": f"请继续步骤 {step_num}，生成相应的代码"
                        })
                        
                        next_response = self.client.chat.completions.create(
                            model="deepseek-v4-flash",
                            messages=messages,
                            temperature=0.3,
                            max_tokens=2000
                        )
                        
                        next_content = next_response.choices[0].message.content.strip()
                        next_data = self._parse_json_response(next_content)
                        
                        step_desc = next_data.get("step_description", f"步骤 {step_num}")
                        code = next_data.get("code", "")
                        
                        yield {
                            "type": "step_start",
                            "step": step_num,
                            "total": total_steps,
                            "description": step_desc
                        }
                        
                        yield {
                            "type": "code",
                            "code": code,
                            "step": step_num,
                            "explanation": step_desc,
                            "is_final": step_num >= total_steps
                        }
                        
                        # 保存到历史
                        messages.append({"role": "assistant", "content": next_content})
                
                yield {"type": "completed"}
            
            else:
                # 未知类型，尝试提取代码
                code = self._extract_code(content)
                yield {
                    "type": "code",
                    "code": code,
                    "explanation": "生成代码",
                    "is_final": True
                }
                yield {"type": "completed"}
        
        except Exception as e:
            print(f"❌ AI 生成错误: {e}")
            import traceback
            traceback.print_exc()
            yield {
                "type": "error",
                "message": f"生成失败: {str(e)}"
            }
    
    def _parse_json_response(self, content: str) -> Dict:
        """解析 JSON 响应"""
        # 尝试提取 JSON
        content = content.strip()
        
        # 移除 markdown 代码块标记
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()
        
        # 解析 JSON
        return json.loads(content)
    
    def _extract_code(self, content: str) -> str:
        """从响应中提取代码"""
        # 移除 markdown 代码块标记
        content = content.strip()
        
        if "```python" in content:
            start = content.find("```python") + 9
            end = content.find("```", start)
            if end > start:
                return content[start:end].strip()
        
        if "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            if end > start:
                return content[start:end].strip()
        
        # 如果找不到代码块，检查是否整个内容都是代码
        if "import bpy" in content:
            return content
        
        # 返回占位符
        return "# 未能提取代码\nprint('请手动检查响应')"
    
    def _clean_code(self, code: str) -> str:
        """清理代码"""
        code = code.strip()
        
        # 确保有 import bpy
        if "import bpy" not in code:
            code = "import bpy\n\n" + code
        
        return code
