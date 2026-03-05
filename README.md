# AgentPass - AI 代理免密通行协议

## 项目概述

AgentPass 是一个最简化的"机器对机器"登录标准，让网站主通过一行代码即可接待 Agent，并让 Agent 实现 BYOK (自带 API Key) 访问服务。

### 核心特性

- **零配置**: 仅需一行代码即可集成
- **无密码**: 使用自带密钥 (BYOK) 模式
- **无存储**: 密钥仅在内存中，用完即丢
- **极简**: 核心代码不超过 200 行
- **无依赖**: 无需复杂的数据库

## 技术规范

### 发现协议 (Discovery)

网站在根目录放置 `/.well-known/ai-agent.json`:

```json
{
  "version": "1.0.0",
  "endpoint": "/api/agent/entry",
  "methods": ["BYOK"],
  "metadata": {}
}
```

### 握手数据包 (Request Packet)

Agent 发送的 POST 请求体：

```json
{
  "auth_type": "BYOK",
  "identity": "agent-name-or-id",
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

### 运行逻辑 (Stateless Execution)

1. 中间件提取 `credentials.api_key` 并放入当前 Request 上下文
2. 业务逻辑直接使用该 Key 调用大模型
3. 请求处理结束，Key 立即从内存销毁

## 项目结构

```
AgentPass/
├── agentpass-middleware/      # Node.js/Express 中间件
│   ├── package.json
│   ├── index.js               # 核心中间件实现
│   ├── example.js             # 服务器示例
│   └── README.md
├── agentpass-client/          # Python 客户端 SDK
│   ├── setup.py
│   ├── agentpass_client.py    # 核心客户端实现
│   ├── example_client.py      # 客户端示例
│   └── README.md
├── PROTOCOL.md                # 协议规范详解
└── LICENSE
```

## 快速开始

### 对于网站主（服务端）

使用 Node.js/Express:

```javascript
const express = require('express');
const agentPass = require('agentpass-middleware');

const app = express();

// 一行代码：应用 AgentPass 中间件
app.use('/api/agent', agentPass.gate());

// 业务逻辑
app.post('/api/agent/entry', (req, res) => {
  const apiKey = req.agentContext.api_key;
  // 使用 apiKey 调用大模型...
  res.json({ status: 'success' });
});

app.listen(3000);
```

同时需要在 `/.well-known/ai-agent.json` 声明支持：

```json
{
  "version": "1.0.0",
  "endpoint": "/api/agent/entry",
  "methods": ["BYOK"]
}
```

### 对于 Agent（客户端）

使用 Python:

```python
from agentpass_client import AgentPassClient

client = AgentPassClient(api_key="sk-your-key")

# Agent 自动发现服务支持哪些协议
task = {
    "action": "analyze",
    "params": {"url": "https://example.com"}
}

response = client.request_site("https://myservice.com", task)
```

## 使用示例

### 示例 1: 服务器端集成

```bash
cd agentpass-middleware
npm install
node example.js
# 访问 http://localhost:3000/.well-known/ai-agent.json
# 访问 http://localhost:3000/health
```

### 示例 2: 客户端请求

```bash
cd agentpass-client
pip install -e .
python example_client.py
```

## 扩展性

### 身份升级
在 `auth_type` 中扩展 `Digital-Signature`:

```json
{
  "auth_type": "Digital-Signature",
  "signature": "..." 
}
```

### 支付升级
在 `ext` 中扩展 `payment_hash`:

```json
{
  "ext": {
    "payment_hash": "0x..."
  }
}
```

### 多模型升级
在 `credentials` 中扩展自定义 `base_url`:

```json
{
  "credentials": {
    "provider": "openai",
    "api_key": "sk-...",
    "base_url": "https://private-api.example.com"
  }
}
```

## 安全特性

- ✅ API 密钥不写入数据库
- ✅ 内存中临时存储
- ✅ 请求完成后自动清除
- ✅ 无 Session 管理
- ✅ 无需认证系统

## 核心代码指标

| 组件 | 文件 | 代码行数 | 依赖 |
|------|------|--------|------|
| 中间件本体 | index.js | ~90 | Express |
| 客户端本体 | agentpass_client.py | ~120 | requests |
| 总计 | - | ~210 | 最小化 |

## 架构图

```
Agent
  │
  ├─ 1. GET /.well-known/ai-agent.json (获取配置)
  │
  ├─ 2. POST /api/agent/entry (发送握手包)
  │      {
  │        "auth_type": "BYOK",
  │        "credentials": { "api_key": "sk-xxx" },
  │        "task": { ... }
  │      }
  │
Server (AgentPass Middleware)
  │
  ├─ 验证 auth_type
  │
  ├─ 提取 api_key -> req.agentContext.api_key
  │
  ├─ 业务逻辑处理 (使用 api_key 调用 LLM)
  │
  └─ 响应完成 -> 清除内存中的 api_key
```

## 比较表

| 特性 | AgentPass | 传统 OAuth | JWT |
|------|-----------|-----------|-----|
| 配置复杂度 | 1 行代码 | 多个配置步骤 | 多个配置步骤 |
| 密钥存储 | 内存 | 服务器 DB | 客户端 |
| 密钥生命周期 | 请求级 | 会话级 | Token 有效期 |
| 初始化时间 | <10ms | 100-500ms | <50ms |
| 数据库依赖 | ✗ | ✓ | 可选 |

## 文件说明

### agentpass-middleware/

**index.js**: 核心中间件
- `gate()`: 返回 Express 中间件函数
- `createHeaders()`: 生成 HTTP 头

**example.js**: 完整的服务器示例
- 发布发现文档
- 处理 Agent 请求
- 演示密钥使用

### agentpass-client/

**agentpass_client.py**: Python 客户端类
- `AgentPassClient`: 主要类
  - `discover()`: 协议发现
  - `request_site()`: 发送请求
  - `request_batch()`: 批量请求
- `quick_request()`: 快速请求函数

**example_client.py**: 客户端使用示例
- 演示发现过程
- 演示单个请求
- 演示批量请求

## License

MIT

## 联系方式

如有问题或建议，欢迎提交 Issue 或 Pull Request。
