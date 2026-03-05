# AgentPass 客户端 SDK

用于 AgentPass 协议的 Python 客户端库 - 让 Agent 能与支持机器对机器登录的网站通信。

## 安装

```bash
pip install requests
```

或从源代码安装：

```bash
python setup.py install
```

## 快速开始

```python
from agentpass_client import AgentPassClient

# 使用 API Key 创建客户端
client = AgentPassClient(api_key="sk-your-api-key-here")

# 定义任务
task = {
    "action": "analyze",
    "params": {
        "url": "https://example.com"
    }
}

# 向网站发送请求
response = client.request_site("https://myservice.com", task)

if response:
    print("成功:", response)
else:
    print("请求失败")
```

## 特性

- **协议发现**: 自动探测网站是否支持 AgentPass
- **握手包构造**: 生成标准 AgentPass 请求数据包
- **无状态通信**: 无需会话管理
- **批量请求**: 支持发送多个任务
- **错误处理**: 优雅的防错机制和明确的错误信息

## API 参考

### AgentPassClient 类

```python
client = AgentPassClient(api_key, provider="openai")
```

#### 方法

**discover(url: str) -> Optional[Dict]**
- 检查网站是否支持 AgentPass 协议
- 返回协议配置字典，如不支持则返回 None

**request_site(url: str, task: Dict, identity: Optional[str]) -> Optional[Dict]**
- 使用 AgentPass 协议向网站发送请求
- 自动进行协议发现
- 构造并发送握手数据包
- 返回网站的响应

**request_batch(url: str, tasks: list) -> list**
- 向同一网站发送多个任务
- 返回响应列表（顺序与任务一致）

### 快速函数

```python
from agentpass_client import quick_request

response = quick_request(
    api_key="sk-xxx",
    url="https://service.com",
    task={"action": "analyze", "params": {}}
)
```

## 请求格式

客户端自动构造 AgentPass 握手数据包：

```json
{
  "auth_type": "BYOK",
  "identity": "agentpass-client",
  "credentials": {
    "provider": "openai",
    "api_key": "sk-xxxx..."
  },
  "task": {
    "action": "analyze",
    "params": { "url": "..." }
  },
  "ext": {}
}
```

## 示例：批量处理

```python
from agentpass_client import AgentPassClient

client = AgentPassClient(api_key="sk-your-key")

tasks = [
    {"action": "analyze", "params": {"url": "http://example1.com"}},
    {"action": "analyze", "params": {"url": "http://example2.com"}},
    {"action": "summarize", "params": {"text": "需要总结的文本"}}
]

results = client.request_batch("https://processing-service.com", tasks)

for i, result in enumerate(results):
    print(f"任务 {i}: {result}")
```

## 完整示例

```python
from agentpass_client import AgentPassClient
import json

# 初始化客户端
client = AgentPassClient(
    api_key="sk-1234567890abcdef",
    provider="openai"
)

# 示例 1: 发现协议
print("检查服务支持...")
config = client.discover("https://myservice.com")

if config:
    print(f"✓ 支持 AgentPass")
    print(f"  版本: {config['version']}")
    print(f"  端点: {config['endpoint']}")
else:
    print("✗ 服务不支持 AgentPass")
    exit(1)

# 示例 2: 发送单个请求
task = {
    "action": "analyze",
    "params": {
        "url": "https://example.com",
        "depth": "detailed"
    }
}

print("\n发送分析请求...")
response = client.request_site(
    "https://myservice.com",
    task,
    identity="my-agent-v1"
)

if response:
    print("✓ 请求成功")
    print(json.dumps(response, indent=2))
else:
    print("✗ 请求失败")

# 示例 3: 批量请求
tasks = [
    {"action": "analyze", "params": {"url": "https://site1.com"}},
    {"action": "analyze", "params": {"url": "https://site2.com"}},
    {"action": "summarize", "params": {"text": "样本文本"}}
]

print("\n发送批量请求...")
results = client.request_batch("https://myservice.com", tasks)

for i, result in enumerate(results):
    status = "✓" if result else "✗"
    print(f"  任务 {i+1}: {status}")
```

## 安全注意事项

- API Key 永不存储到磁盘
- 通信应使用 HTTPS
- 服务器端中间件在每个请求后从内存清除密钥
- 遵循 BYOK（自带密钥）原则

## 错误处理

```python
from agentpass_client import AgentPassClient

client = AgentPassClient(api_key="sk-xxx")

try:
    # 协议发现
    config = client.discover("https://service.com")
    if not config:
        print("错误: 服务不支持 AgentPass")
        exit(1)
    
    # 发送请求
    task = {"action": "process", "params": {"data": "test"}}
    response = client.request_site("https://service.com", task)
    
    if response and response.get('status') == 'success':
        print("成功:", response.get('result'))
    else:
        print("错误:", response.get('error') if response else "无响应")
        
except Exception as e:
    print(f"异常: {e}")
```

## 常见问题

### Q: 发现失败时应该怎么做？

```python
config = client.discover("example.com")
if not config:
    # 检查 URL 格式
    # 检查网络连接
    # 检查服务是否在线
    print("无法连接到服务")
```

### Q: 如何处理超时？

```python
# 使用快速函数时的超时处理
import socket
try:
    response = client.request_site("https://slow-service.com", task)
except socket.timeout:
    print("请求超时，请稍后重试")
```

### Q: 如何批量处理大量任务？

```python
# 分批处理以避免内存溢出
batch_size = 10
all_tasks = [...]  # 任务列表

for i in range(0, len(all_tasks), batch_size):
    batch = all_tasks[i:i+batch_size]
    results = client.request_batch(url, batch)
    process_results(results)
```

## 环境变量配置

```bash
# 保存 API Key 到环境变量（不要硬编码）
export AGENTPASS_API_KEY="sk-your-key"
export AGENTPASS_SERVICE_URL="https://service.com"
```

```python
import os
from agentpass_client import AgentPassClient

api_key = os.getenv('AGENTPASS_API_KEY')
service_url = os.getenv('AGENTPASS_SERVICE_URL')

if not api_key:
    raise ValueError("AGENTPASS_API_KEY 环境变量未设置")

client = AgentPassClient(api_key=api_key)
response = client.request_site(service_url, task)
```

## 与服务器端中间件集成

### 端到端流程

```python
# 1. Agent 端：发现并发送请求
from agentpass_client import AgentPassClient

client = AgentPassClient(api_key="sk-agent-key")
response = client.request_site(
    "https://processor.service.com",
    {"action": "analyze", "params": {"url": "data"}}
)

# 2. 服务器端会:
#    - 验证 auth_type 为 BYOK
#    - 提取 API Key 到内存
#    - 使用 Key 调用大模型
#    - 返回结果
#    - 从内存清除 Key

print("处理结果:", response)
```

## 类型注解

```python
from typing import Dict, Any, Optional, List

def discover(url: str) -> Optional[Dict[str, Any]]:
    """发现协议"""
    pass

def request_site(
    url: str,
    task: Dict[str, Any],
    identity: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """发送单个请求"""
    pass

def request_batch(
    url: str,
    tasks: List[Dict[str, Any]]
) -> List[Optional[Dict[str, Any]]]:
    """批量发送请求"""
    pass
```

## 许可证

MIT

## 相关资源

- [AgentPass 主文档](../README.md)
- [协议规范](../PROTOCOL.md)
- [完整 API 文档](../API.md)
- [部署指南](../DEPLOYMENT.md)
- [服务器中间件](../agentpass-middleware/)
