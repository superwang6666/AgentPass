# AgentPass 协议规范

## 1. 协议概述

AgentPass 是一个轻量级的"机器对机器"通信协议，旨在简化 AI Agent 与服务之间的身份验证和授权流程。

**设计原则**：
- 最小化：避免复杂配置
- 无状态：无需服务器端存储用户状态
- 安全性：在内存中处理加密凭证，不持久化存储
- 互操作性：易于实现多种编程语言版本

## 2. 发现协议

### 2.1 发现文档位置

服务必须在以下位置发布 AgentPass 支持声明：

```
GET /.well-known/ai-agent.json
```

### 2.2 发现文档格式

```json
{
  "version": "1.0.0",
  "endpoint": "/api/agent/entry",
  "methods": ["BYOK"],
  "metadata": {
    "name": "Service Name",
    "description": "Service Description",
    "contact": "contact@example.com"
  }
}
```

**字段说明**：

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| version | string | ✓ | 协议版本号 |
| endpoint | string | ✓ | Agent 访问入口 URL 路径 |
| methods | array | ✓ | 支持的认证方式数组 |
| metadata | object | ✗ | 额外元数据 |

**支持的 methods**：
- `BYOK`: Bring Your Own Key - 自带密钥模式

## 3. 握手协议

### 3.1 请求格式

Agent 向 endpoint 发起 POST 请求：

```http
POST /api/agent/entry HTTP/1.1
Host: example.com
Content-Type: application/json

{
  "auth_type": "BYOK",
  "identity": "my-agent-v1",
  "credentials": {
    "provider": "openai",
    "api_key": "sk-xxxxxxxxxxxxxxxx",
    "base_url": "https://api.openai.com/v1"
  },
  "task": {
    "action": "analyze",
    "params": {
      "url": "https://example.com",
      "depth": "detailed"
    }
  },
  "ext": {}
}
```

**字段说明**：

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| auth_type | string | ✓ | 认证类型，必须为 "BYOK" 或其他支持的方式 |
| identity | string | ✓ | Agent 标识，用于日志和追溯 |
| credentials | object | ✓ | 凭证对象 |
| credentials.provider | string | ✓ | 提供商名称 (如 "openai", "anthropic") |
| credentials.api_key | string | ✓ | 加密凭证内容 |
| credentials.base_url | string | ✗ | 自定义 API 地址 |
| task | object | ✓ | 任务指令包 |
| task.action | string | ✓ | 操作类型 |
| task.params | object | ✓ | 操作参数 |
| ext | object | ✗ | 扩展字段 |

### 3.2 响应格式

服务返回处理结果：

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "success",
  "message": "Task processed successfully",
  "result": {
    "action": "analyze",
    "output": "Analysis result..."
  },
  "processed_at": "2026-03-05T10:30:00Z"
}
```

### 3.3 错误响应

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "status": "error",
  "error": "Invalid auth_type",
  "message": "Only BYOK is supported"
}
```

**错误码**：

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求格式错误或验证失败 |
| 401 | 认证失败 |
| 403 | 访问被拒绝 |
| 500 | 服务器内部错误 |

## 4. 执行流程

### 4.1 服务器端流程

```
1. 接收 POST 请求
   ↓
2. 验证 Content-Type 为 application/json
   ↓
3. 解析 JSON 请求体
   ↓
4. 验证 auth_type 在支持列表中
   ↓
5. 验证必需字段存在
   ↓
6. 提取 credentials -> 放入请求上下文
   ↓
7. 执行业务逻辑（使用上下文中的凭证）
   ↓
8. 构造响应
   ↓
9. 清除凭证数据（从内存销毁）
   ↓
10. 发送响应
```

### 4.2 客户端流程

```
1. 发现：GET /.well-known/ai-agent.json
   ↓
2. 解析发现文档，获取 endpoint
   ↓
3. 构造握手包（包含自己的 API Key）
   ↓
4. POST 握手包到 endpoint
   ↓
5. 接收响应
   ↓
6. 处理结果
```

## 5. 安全考量

### 5.1 密钥管理

- **不持久化**: API Key 仅存在于内存中，请求完成后销毁
- **不日志化**: 禁止将 API Key 写入日志文件
- **环境隔离**: 在不同内存页面中处理凭证

### 5.2 传输安全

- 必须使用 HTTPS
- 建议实施 TLS 1.2 或更高版本
- 建议启用 HSTS 头

### 5.3 验证

- 验证请求来源 (可选 IP 白名单)
- 验证请求格式和字段完整性
- 限流防止滥用

### 5.4 日志记录

**允许记录**：
- 请求时间戳
- Agent identity
- 操作类型
- 响应状态

**禁止记录**：
- API Key 内容
- 完整凭证对象
- 请求体中的敏感数据

## 6. 扩展规范

### 6.1 认证方式扩展

未来可扩展的认证方式：

```json
{
  "auth_type": "digital-signature",
  "signature": "0x...",
  "public_key": "0x..."
}
```

### 6.2 支付扩展

在 `ext` 中添加支付信息：

```json
{
  "ext": {
    "payment_type": "credit-card",
    "payment_hash": "0x...",
    "amount": 99,
    "currency": "USD"
  }
}
```

### 6.3 多模型支持

在 `credentials` 中指定自定义端点：

```json
{
  "credentials": {
    "provider": "custom-llm",
    "api_key": "...",
    "base_url": "https://private-llm.company.com/api/v1",
    "model": "custom-gpt-4"
  }
}
```

## 7. 实现建议

### 7.1 中间件实现建议

```
1. 创建 Express 中间件
2. 在 POST /api/agent/entry 时拦截
3. 使用流式处理大请求体
4. 验证 JSON 格式
5. 在 res.on('finish') 时清除凭证
```

### 7.2 客户端实现建议

```
1. 首先执行发现
2. 缓存发现结果（可选，带 TTL）
3. 构造标准握手包
4. 实现重试逻辑
5. 处理错误响应
```

## 8. 版本兼容性

### 8.1 向后兼容性

- 1.0.x 版本为基础版本
- 新字段添加到 `ext` 中以保持兼容
- 必需字段不应被移除

### 8.2 版本迁移

服务应支持多个版本的发现文档：

```json
{
  "versions": {
    "1.0.0": "/api/agent/entry",
    "1.1.0": "/api/agent/v1/entry"
  }
}
```

## 9. 测试用例

### 9.1 基本测试

- [ ] GET /.well-known/ai-agent.json 返回有效 JSON
- [ ] POST 请求包含所需字段时返回 200
- [ ] 缺少必需字段时返回 400
- [ ] 响应后 API Key 被清除

### 9.2 安全测试

- [ ] API Key 不出现在日志中
- [ ] 请求完成后内存中不存在密钥
- [ ] 无效的 auth_type 被拒绝

## 10. 示例

### 示例 1: 简单的文本分析任务

**请求**:
```json
{
  "auth_type": "BYOK",
  "identity": "text-analyzer-agent",
  "credentials": {
    "provider": "openai",
    "api_key": "sk-..."
  },
  "task": {
    "action": "analyze-sentiment",
    "params": {
      "text": "这是一个很好的产品",
      "language": "zh"
    }
  },
  "ext": {}
}
```

**响应**:
```json
{
  "status": "success",
  "result": {
    "sentiment": "positive",
    "confidence": 0.95
  }
}
```

### 示例 2: 网络数据提取

**请求**:
```json
{
  "auth_type": "BYOK",
  "identity": "web-crawler-agent",
  "credentials": {
    "provider": "openai",
    "api_key": "sk-..."
  },
  "task": {
    "action": "extract-content",
    "params": {
      "url": "https://example.com",
      "fields": ["title", "summary", "keywords"]
    }
  },
  "ext": {}
}
```

## 11. 参考资源

- OAuth 2.0: https://tools.ietf.org/html/rfc6749
- JWT: https://tools.ietf.org/html/rfc7519
- .well-known: https://tools.ietf.org/html/rfc5785
