# AgentPass 中间件

Express 中间件实现 AgentPass 协议 - 最小化的机器对机器登录标准。

## 安装

```bash
npm install agentpass-middleware express
```

## 快速开始

```javascript
const express = require('express');
const agentPass = require('agentpass-middleware');

const app = express();

// 应用 AgentPass 中间件
app.use('/api/agent', agentPass.gate());

// 处理 Agent 请求
app.post('/api/agent/entry', (req, res) => {
  // 从 Agent 上下文提取 API Key
  const apiKey = req.agentContext.api_key;
  const provider = req.agentContext.provider;
  const task = req.agentContext.task;
  
  // 使用密钥调用大模型或服务
  console.log('Agent 任务:', task);
  
  res.json({
    status: 'success',
    message: '任务已接收'
  });
});

app.listen(3000, () => {
  console.log('AgentPass 服务器运行在端口 3000');
});
```

## 工作原理

1. **请求拦截**: 中间件拦截发往 `/api/agent/entry` 的 POST 请求
2. **验证**: 验证 `auth_type` 是否为 `BYOK`
3. **密钥注入**: 提取 `credentials.api_key` 并注入到 `req.agentContext`
4. **无状态处理**: 响应发送后，API Key 自动从内存销毁
5. **自动清理**: 使用 `res.on('finish')` 确保凭证永不持久化

## 请求格式

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

## 响应上下文

中间件处理请求后，以下属性在 `req.agentContext` 中可用：

- `api_key`: Agent 的 API Key
- `provider`: 提供商名称（如 "openai"）
- `identity`: Agent 的标识/名称
- `task`: 任务数据包

## 安全特性

- API Key 不存储到数据库
- 仅在内存中保存凭证
- 响应完成时自动清理
- 严格的 auth_type 验证
- 代码简洁易审计

## 完整示例

```javascript
const express = require('express');
const agentPass = require('agentpass-middleware');

const app = express();

// 发布发现文档
app.get('/.well-known/ai-agent.json', (req, res) => {
  res.json({
    version: "1.0.0",
    endpoint: "/api/agent/entry",
    methods: ["BYOK"],
    metadata: {
      name: "我的 AgentPass 服务",
      description: "示例服务"
    }
  });
});

// 应用中间件
app.use('/api/agent', agentPass.gate());

// 处理请求
app.post('/api/agent/entry', async (req, res) => {
  try {
    const { api_key, provider, identity, task } = req.agentContext;
    
    console.log(`[${new Date().toISOString()}] Agent 请求:`, {
      identity,
      action: task.action,
      provider
    });
    
    // 使用 API Key 调用 LLM
    const result = await processTask(api_key, task);
    
    res.json({
      status: 'success',
      result: result,
      processed_at: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('处理错误:', error.message);
    res.status(500).json({
      status: 'error',
      message: '内部服务器错误'
    });
  }
});

// 业务逻辑（使用 Agent 的 API Key）
async function processTask(apiKey, task) {
  // 这里使用 apiKey 调用大模型
  // 示例：调用 OpenAI API
  
  return {
    action: task.action,
    result: `已处理: ${JSON.stringify(task.params)}`
  };
}

app.listen(3000);
```

## API 参考

### `gate()`

创建并返回 AgentPass 中间件函数。

**使用示例**:

```javascript
const agentPass = require('agentpass-middleware');

app.use('/api/agent', agentPass.gate());
```

### `createHeaders(key)`

为 API 请求生成标准 HTTP 头。

**参数**:
- `key` (string): 从 `req.agentContext.api_key` 获得的 API Key

**返回**:
```javascript
{
  'Authorization': `Bearer ${key}`,
  'Content-Type': 'application/json'
}
```

**使用示例**:

```javascript
const headers = agentPass.createHeaders(req.agentContext.api_key);

fetch('https://api.openai.com/v1/chat/completions', {
  method: 'POST',
  headers: headers,
  body: JSON.stringify({...})
});
```

## 集成步骤

### 第一步：安装依赖

```bash
npm init -y
npm install express agentpass-middleware
```

### 第二步：创建服务器

```javascript
// server.js
const express = require('express');
const agentPass = require('agentpass-middleware');

const app = express();

// 步骤 1: 声明协议支持
app.get('/.well-known/ai-agent.json', (req, res) => {
  res.json({
    version: "1.0.0",
    endpoint: "/api/agent/entry",
    methods: ["BYOK"]
  });
});

// 步骤 2: 应用中间件
app.use('/api/agent', agentPass.gate());

// 步骤 3: 业务逻辑
app.post('/api/agent/entry', (req, res) => {
  const { api_key } = req.agentContext;
  // 使用 api_key...
  res.json({ status: 'success' });
});

app.listen(3000);
```

### 第三步：运行服务

```bash
node server.js
# 访问 http://localhost:3000/.well-known/ai-agent.json
```

## 错误处理

### 验证失败

```javascript
// 400 Bad Request - auth_type 无效
{
  "error": "Invalid auth_type",
  "message": "Only BYOK is supported"
}
```

### 缺少必需字段

```javascript
// 400 Bad Request - 缺少凭证
{
  "error": "Missing credentials.api_key"
}
```

### JSON 解析错误

```javascript
// 400 Bad Request - JSON 格式错误
{
  "error": "Invalid JSON in request body"
}
```

## 请求流程

```
Agent 请求
    ↓
中间件 (gate())
    ├─ 解析 JSON
    ├─ 验证 auth_type
    ├─ 验证必需字段
    ├─ 提取 API Key → req.agentContext
    ↓
业务逻辑处理
    ├─ 读取 req.agentContext.api_key
    ├─ 调用大模型
    ├─ 生成响应
    ↓
响应发送
    ├─ res.json(result)
    ├─ res.on('finish') 触发
    ├─ 清除 req.agentContext
    ↓
Agent 接收结果
```

## 生产环境配置

### 使用 PM2

```bash
npm install -g pm2

pm2 start server.js --name "agentpass"
pm2 save
pm2 startup
```

### 使用 Docker

```dockerfile
FROM node:16-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY server.js .
EXPOSE 3000
CMD ["node", "server.js"]
```

```bash
docker build -t agentpass-service .
docker run -p 3000:3000 agentpass-service
```

## 安全建议

- ✅ 使用 HTTPS（生产环境必须）
- ✅ 限制请求大小
- ✅ 设置请求超时
- ✅ 不记录 API Key
- ✅ 验证 Content-Type
- ✅ 设置速率限制

## 常见问题

### Q: API Key 会被记录吗？

**A:** 不会。中间件仅在内存中保存 Key，请求完成后立即清除。

### Q: 如何使用 Agent 提供的 Key 调用 LLM？

**A:** 使用 `createHeaders()` 函数生成授权头：

```javascript
const headers = agentPass.createHeaders(req.agentContext.api_key);
```

### Q: 是否支持其他认证方式？

**A:** 当前版本仅支持 BYOK。扩展支持可通过修改验证逻辑实现。

## 许可证

MIT

## 相关资源

- [客户端 SDK](../agentpass-client/)
- [协议规范](../PROTOCOL.md)
- [完整 API 文档](../API.md)
- [部署指南](../DEPLOYMENT.md)
- [主文档](../README.md)
