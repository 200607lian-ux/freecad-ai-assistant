import os
from openai import OpenAI

# 从环境变量获取配置
api_key = os.getenv("DASHSCOPE_API_KEY")
workspace_id = os.getenv("DASHSCOPE_WORKSPACE_ID", "")

print(f"API Key 存在: {'是' if api_key else '否'}")
print(f"API Key 长度: {len(api_key) if api_key else 0}")
print(f"Workspace ID: {workspace_id if workspace_id else '未设置'}")

if not api_key:
    print("\n[FAIL] 请设置环境变量 DASHSCOPE_API_KEY")
    exit(1)

# 构建 base_url（如果设置了 Workspace ID）
if workspace_id:
    base_url = f"https://{workspace_id}.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
else:
    # 使用默认的 DashScope endpoint
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

print(f"Base URL: {base_url}")

client = OpenAI(
    api_key=api_key,
    base_url=base_url,
)

try:
    completion = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[{'role': 'user', 'content': '你是谁？'}]
    )
    print(f"\n[OK] 连接成功！")
    print(f"模型响应: {completion.choices[0].message.content[:100]}...")
except Exception as e:
    print(f"\n[FAIL] 连接失败: {e}")
