# AgentPass API 文档

## 目录
- [中间件 API](#中间件-api)
- [客户端 API](#客户端-api)
- [常见用法](#常见用法)
- [错误处理](#错误处理)

## 中间件 API

### agentpass-middleware

#### `gate()`

创建一个 Express 中间件，用于处理 AgentPass 请求。

**返回值**: `Function` - Express 中间件函数

**示例**:
```javascript
const agentPass = require('agentpass-middleware');
const express = require('express');

const app = express();
app.use('/api/agent', agentPass.gate());
```

**流程**:
1. 拦截发往 `/api/agent/entry` 的 POST 请求
2. 验证请求格式和 `auth_type`
3. 提取 API Key 放入 `req.agentContext`
4. 继续到下一个中间件或路由处理
5. 响应完成后自动清除凭证

**访问凭证**:
```javascript
app.post('/api/agent/entry', (req, res) => {
  // req.agentContext 中包含:
  const {
    api_key,      // 字符串，Agent 提供的 API Key
    provider,      // 字符串，'openai' 等
    identity,      // 字符串，Agent 标识
    task           // 对象，业务任务
  } = req.agentContext;
  
  res.json({ status: 'success' });
});
```

#### `createHeaders(key)`

为 API 请求生成标准的 HTTP 头。

**参数**:
- `key` (string): 从 `req.agentContext.api_key` 获取的 API Key

**返回值**: `Object` - HTTP 头对象

**示例**:
```javascript
const agentPass = require('agentpass-middleware');

const headers = agentPass.createHeaders('sk-1234567890');
// 返回:
// {
//   'Authorization': 'Bearer sk-1234567890',
//   'Content-Type': 'application/json'
// }

// 在调用大模型 API 时使用
const response = await fetch('https://api.openai.com/v1/chat/completions', {
  method: 'POST',
  headers: headers,
  body: JSON.stringify({ model: 'gpt-4', messages: [...] })
});
```

### 中间件的属性

#### `req.agentContext`

由中间件添加到每个请求对象上，包含以下属性：

| 属性 | 类型 | 说明 |
|------|------|------|
| `api_key` | string | Agent 提供的 API Key |
| `provider` | string | 提供商名称（如 'openai'） |
| `identity` | string | Agent 的标识 |
| `task` | object | 任务指令包（包含 action 和 params） |

**生命周期**:
- 请求到达时创建
- 中间件验证后填充
- 响应发送后自动销毁（通过 `res.on('finish')` 事件）

---

## 客户端 API

### AgentPassClient 类

Python 客户端用于 Agent 向支持 AgentPass 的服务发送请求。

#### 初始化

```python
from agentpass_client import AgentPassClient

client = AgentPassClient(api_key, provider='openai')
```

**参数**:
- `api_key` (string, 必需): Agent 的 API Key
- `provider` (string, 可选): 提供商名称，默认 'openai'

**示例**:
```python
client = AgentPassClient(
    api_key='sk-1234567890abcdef',
    provider='openai'
)
```

#### `discover(url)`

探测一个网站是否支持 AgentPass 协议。

**参数**:
- `url` (string): 目标网站 URL（可省略协议）

**返回值**: `dict` 或 `None`
- 成功: 包含协议配置的字典
- 失败或不支持: `None`

**示例**:
```python
config = client.discover('example.com')

if config:
    print(f"Version: {config['version']}")
    print(f"Endpoint: {config['endpoint']}")
    print(f"Methods: {config['methods']}")
else:
    print("Service does not support AgentPass")
```

**返回示例**:
```python
{
    'version': '1.0.0',
    'endpoint': '/api/agent/entry',
    'methods': ['BYOK'],
    'metadata': {
        'name': 'Service Name',
        'description': 'Service Description'
    }
}
```

#### `request_site(url, task, identity=None)`

向支持 AgentPass 的网站发送请求。

**参数**:
- `url` (string): 目标网站 URL
- `task` (dict): 任务定义，包含 `action` 和 `params`
- `identity` (string, 可选): Agent 标识，默认为 'agentpass-client'

**返回值**: `dict` 或 `None`
- 成功: 服务器响应数据
- 失败: `None`

**示例**:
```python
task = {
    'action': 'analyze',
    'params': {
        'url': 'https://example.com',
        'depth': 'detailed'
    }
}

response = client.request_site(
    'https://myservice.com',
    task,
    identity='my-agent-v1'
)

if response:
    print(f"Status: {response['status']}")
    print(f"Result: {response['result']}")
else:
    print("Request failed")
```

**内部流程**:
1. 调用 `discover()` 检查协议支持
2. 构造标准握手包（handshake packet）
3. 发送 POST 请求到 endpoint
4. 返回解析后的响应

#### `request_batch(url, tasks)`

批量向网站发送多个请求。

**参数**:
- `url` (string): 目标网站 URL
- `tasks` (list): 任务列表，每项都是一个任务定义

**返回值**: `list` - 响应列表，与任务列表顺序对应

**示例**:
```python
tasks = [
    {'action': 'analyze', 'params': {'url': 'https://site1.com'}},
    {'action': 'analyze', 'params': {'url': 'https://site2.com'}},
    {'action': 'summarize', 'params': {'text': 'Some text'}}
]

results = client.request_batch('https://processor.com', tasks)

for i, result in enumerate(results):
    if result:
        print(f"Task {i+1}: ✓ Success")
    else:
        print(f"Task {i+1}: ✗ Failed")
```

### 快速函数

#### `quick_request(api_key, url, task, provider='openai')`

一行代码发送单个请求（无需创建客户端实例）。

**参数**:
- `api_key` (string): API Key
- `url` (string): 目标 URL
- `task` (dict): 任务定义
- `provider` (string, 可选): 提供商，默认 'openai'

**返回值**: `dict` 或 `None` - 响应或失败

**示例**:
```python
from agentpass_client import quick_request

response = quick_request(
    api_key='sk-my-key',
    url='https://api.example.com',
    task={'action': 'test', 'params': {}},
    provider='openai'
)
```

---

## 常见用法

### 场景 1: 网站主集成中间件

```javascript
const express = require('express');
const agentPass = require('agentpass-middleware');

const app = express();

// 第 1 步: 应用中间件
app.use('/api/agent', agentPass.gate());

// 第 2 步: 发布发现文档
app.get('/.well-known/ai-agent.json', (req, res) => {
  res.json({
    version: "1.0.0",
    endpoint: "/api/agent/entry",
    methods: ["BYOK"]
  });
});

// 第 3 步: 处理 Agent 请求
app.post('/api/agent/entry', async (req, res) => {
  const { api_key, provider, task } = req.agentContext;
  
  try {
    // 使用 Agent 的 API Key 调用大模型
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: agentPass.createHeaders(api_key),
      body: JSON.stringify({
        model: 'gpt-4',
        messages: [{ role: 'user', content: JSON.stringify(task.params) }]
      })
    });
    
    const result = await response.json();
    res.json({ status: 'success', result });
  } catch (err) {
    res.status(500).json({ status: 'error', message: err.message });
  }
});

app.listen(3000);
```

### 场景 2: Agent 自动发现并请求

```python
from agentpass_client import AgentPassClient

client = AgentPassClient(api_key='sk-xxxx')

# 自动发现
if not client.discover('https://processor.service.com'):
    print("Service not found or doesn't support AgentPass")
    exit(1)

# 发送请求
task = {
    'action': 'process',
    'params': {'input': 'data to process'}
}

response = client.request_site('https://processor.service.com', task)
print(response)
```

### 场景 3: 错误处理和重试

```python
from agentpass_client import AgentPassClient
import time

client = AgentPassClient(api_key='sk-xxxx')

def request_with_retry(url, task, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = client.request_site(url, task)
            if response:
                return response
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避
    
    return None

result = request_with_retry('https://service.com', task)
```

---

## 错误处理

### 客户端错误

| 错误 | 说明 | 处理方法 |
|------|------|--------|
| 发现失败 | `discover()` 返回 `None` | 检查 URL 格式，确保网站在线 |
| 连接超时 | 请求超时 | 增加超时时间，检查网络连接 |
| JSON 解析错误 | 响应不是有效 JSON | 检查服务器端错误日志 |
| 认证失败 | `auth_type` 不支持 | 确保服务支持 BYOK，检查 API Key 有效性 |

### 服务器错误

| 状态码 | 说明 | 原因 |
|-------|------|------|
| 200 | 成功 | 请求已成功处理 |
| 400 | 错误的请求 | JSON 格式错误、缺少必需字段或 auth_type 无效 |
| 401 | 认证失败 | API Key 无效或过期 |
| 403 | 禁止访问 | 权限不足或 IP 被限制 |
| 500 | 服务器错误 | 服务器内部错误 |

### 错误响应示例

```json
{
  "status": "error",
  "error": "Invalid auth_type",
  "message": "Only BYOK is supported"
}
```

### 错误处理最佳实践

**在中间件中**:
```javascript
app.post('/api/agent/entry', (req, res) => {
  try {
    const { api_key, task } = req.agentContext;
    // 处理业务...
  } catch (err) {
    console.error('Error (not logging key):', err.message);
    res.status(500).json({
      status: 'error',
      message: 'Internal server error'
    });
  }
});
```

**在客户端**:
```python
try:
    response = client.request_site(url, task)
    if not response:
        raise Exception("No response from server")
    
    if response.get('status') == 'error':
        print(f"Server error: {response.get('error')}")
    else:
        print(f"Success: {response.get('result')}")
        
except Exception as e:
    print(f"Request failed: {e}")
```

---

## 类型定义

### Python 类型提示

```python
from typing import Dict, Any, Optional, List

def discover(url: str) -> Optional[Dict[str, Any]]:
    """返回协议配置或 None"""
    pass

def request_site(
    url: str,
    task: Dict[str, Any],
    identity: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """发送请求，返回响应或 None"""
    pass

def request_batch(
    url: str,
    tasks: List[Dict[str, Any]]
) -> List[Optional[Dict[str, Any]]]:
    """批量请求，返回响应列表"""
    pass
```

### JavaScript 类型

```javascript
// 中间件
function gate(): Function

function createHeaders(key: string): Object

// 请求上下文
interface AgentContext {
  api_key: string
  provider: string
  identity: string
  task: { action: string, params: object }
}
```

---

## 相关文档

- [完整协议规范](PROTOCOL.md)
- [项目 README](README.md)
- [服务器示例](agentpass-middleware/example.js)
- [客户端示例](agentpass-client/example_client.py)
