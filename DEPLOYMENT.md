# 部署和配置指南

## 目录
- [快速部署](#快速部署)
- [对网站主的部署指南](#对网站主的部署指南)
- [对 Agent 的部署指南](#对-agent-的部署指南)
- [生产环境配置](#生产环境配置)
- [安全检查清单](#安全检查清单)
- [故障排查](#故障排查)

---

## 快速部署

### 网站主（5 分钟）

```bash
# 1. 安装
npm install agentpass-middleware express

# 2. 创建 app.js
cat > app.js << 'EOF'
const express = require('express');
const agentPass = require('agentpass-middleware');

const app = express();

app.get('/.well-known/ai-agent.json', (req, res) => {
  res.json({
    version: "1.0.0",
    endpoint: "/api/agent/entry",
    methods: ["BYOK"]
  });
});

app.use('/api/agent', agentPass.gate());

app.post('/api/agent/entry', (req, res) => {
  const { api_key } = req.agentContext;
  // 使用 api_key 调用大模型...
  res.json({ status: 'success' });
});

app.listen(3000);
EOF

# 3. 运行
node app.js
```

### Agent（5 分钟）

```bash
# 1. 安装
pip install requests

# 2. 创建 script.py
cat > script.py << 'EOF'
from agentpass_client import AgentPassClient

client = AgentPassClient(api_key='sk-your-key')
response = client.request_site(
    'https://myservice.com',
    {'action': 'analyze', 'params': {}}
)
print(response)
EOF

# 3. 运行
python script.py
```

---

## 对网站主的部署指南

### 第一步：验证 Node.js 环境

```bash
# 检查 Node.js 版本（需要 12+）
node --version

# 检查 npm 版本
npm --version
```

### 第二步：安装依赖

```bash
# 创建项目目录
mkdir my-agentpass-service
cd my-agentpass-service

# 初始化 npm 项目
npm init -y

# 安装 agentpass-middleware
npm install agentpass-middleware express
```

### 第三步：创建应用

**完整示例** (`server.js`):

```javascript
const express = require('express');
const agentPass = require('agentpass-middleware');

const app = express();
const PORT = process.env.PORT || 3000;

// 步骤 1: 声明协议支持
app.get('/.well-known/ai-agent.json', (req, res) => {
  res.json({
    version: "1.0.0",
    endpoint: "/api/agent/entry",
    methods: ["BYOK"],
    metadata: {
      name: "My AgentPass Service",
      contact: "support@example.com"
    }
  });
});

// 步骤 2: 应用中间件
app.use('/api/agent', agentPass.gate());

// 步骤 3: 处理请求
app.post('/api/agent/entry', async (req, res) => {
  try {
    const { api_key, provider, identity, task } = req.agentContext;
    
    console.log(`[${new Date().toISOString()}] Agent request:`, {
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
    console.error('Processing error:', error.message);
    res.status(500).json({
      status: 'error',
      message: 'Internal server error'
    });
  }
});

// 业务逻辑（使用 Agent 的 API Key）
async function processTask(apiKey, task) {
  // 这里使用 apiKey 调用大模型
  // 示例：调用 OpenAI API
  
  return {
    action: task.action,
    result: `Processed: ${JSON.stringify(task.params)}`
  };
}

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
  console.log(`Discovery: http://localhost:${PORT}/.well-known/ai-agent.json`);
});
```

### 第四步：运行应用

```bash
# 开发环境
node server.js

# 生产环境（使用 PM2）
npm install -g pm2
pm2 start server.js --name "agentpass-service"
pm2 save
```

### 第五步：验证部署

```bash
# 检查发现文档
curl http://localhost:3000/.well-known/ai-agent.json

# 测试握手（用实际的 API Key 替换）
curl -X POST http://localhost:3000/api/agent/entry \
  -H "Content-Type: application/json" \
  -d '{
    "auth_type": "BYOK",
    "identity": "test-agent",
    "credentials": {
      "provider": "openai",
      "api_key": "sk-test-key"
    },
    "task": {
      "action": "test",
      "params": {}
    },
    "ext": {}
  }'
```

---

## 对 Agent 的部署指南

### 第一步：验证 Python 环境

```bash
# 检查 Python 版本（需要 3.7+）
python --version

# 检查 pip
pip --version
```

### 第二步：安装 SDK

```bash
# 方式 1: 从源代码安装
git clone https://github.com/agentpass/agentpass-client.git
cd agentpass-client
pip install -e .

# 方式 2: 从 PyPI（未来）
pip install agentpass-client
```

### 第三步：创建 Agent 脚本

**基础示例** (`agent.py`):

```python
from agentpass_client import AgentPassClient

# 初始化客户端
client = AgentPassClient(
    api_key="your-api-key-here",
    provider="openai"
)

# 定义任务
task = {
    "action": "analyze",
    "params": {
        "url": "https://example.com",
        "depth": "detailed"
    }
}

# 发送请求
response = client.request_site(
    "https://myservice.com",
    task,
    identity="my-agent"
)

# 处理响应
if response:
    print("Success!")
    print(response)
else:
    print("Failed to get response")
```

**高级示例** (`advanced_agent.py`):

```python
from agentpass_client import AgentPassClient
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MyAgent:
    def __init__(self, api_key, service_url):
        self.client = AgentPassClient(api_key=api_key)
        self.service_url = service_url
        
        # 验证服务支持
        if not self.client.discover(service_url):
            raise Exception(f"Service {service_url} doesn't support AgentPass")
        
        logger.info(f"Connected to {service_url}")
    
    def process_batch(self, urls):
        """处理多个 URL"""
        tasks = [
            {
                "action": "analyze",
                "params": {"url": url}
            }
            for url in urls
        ]
        
        results = self.client.request_batch(self.service_url, tasks)
        
        success_count = sum(1 for r in results if r is not None)
        logger.info(f"Processed {success_count}/{len(urls)} URLs")
        
        return results

# 使用
if __name__ == "__main__":
    agent = MyAgent(
        api_key="sk-your-key",
        service_url="https://myservice.com"
    )
    
    urls = [
        "https://example1.com",
        "https://example2.com",
        "https://example3.com"
    ]
    
    results = agent.process_batch(urls)
    
    for i, result in enumerate(results):
        print(f"URL {i+1}: {result}")
```

### 第四步：测试连接

```bash
# 运行 Python 脚本
python agent.py

# 或使用 example_client.py
python example_client.py
```

---

## 生产环境配置

### 网站主配置

**使用 PM2 管理进程** (`ecosystem.config.js`):

```javascript
module.exports = {
  apps: [{
    name: "agentpass-service",
    script: "./server.js",
    instances: 4,
    exec_mode: "cluster",
    env: {
      NODE_ENV: "production",
      PORT: 3000
    },
    error_file: "./logs/err.log",
    out_file: "./logs/out.log",
    log_file: "./logs/combined.log",
    time_format: "YYYY-MM-DD HH:mm:ss Z",
    merge_logs: true
  }]
};
```

启动：
```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

**使用 Docker**:

```dockerfile
FROM node:16-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install --production

COPY server.js .

EXPOSE 3000

CMD ["node", "server.js"]
```

构建和运行：
```bash
docker build -t agentpass-service .
docker run -p 3000:3000 agentpass-service
```

**反向代理配置（Nginx）**:

```nginx
server {
    listen 443 ssl http2;
    server_name api.example.com;
    
    ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 增加超时时间
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### Agent 配置

**环境变量管理** (`.env`):

```
AGENTPASS_API_KEY=sk-your-key-here
AGENTPASS_SERVICE_URL=https://api.example.com
AGENTPASS_PROVIDER=openai
HTTP_TIMEOUT=30
RETRIES=3
```

**加载环境变量**:

```python
import os
from dotenv import load_dotenv
from agentpass_client import AgentPassClient

load_dotenv()

client = AgentPassClient(
    api_key=os.getenv('AGENTPASS_API_KEY'),
    provider=os.getenv('AGENTPASS_PROVIDER', 'openai')
)
```

---

## 安全检查清单

### 中间件安全

- [ ] API Key 仅存在于内存（不写入数据库）
- [ ] API Key 不写入日志文件
- [ ] 响应完成后自动清除凭证
- [ ] 使用 HTTPS（生产环境必须）
- [ ] 验证请求格式和 Content-Type
- [ ] 验证 auth_type 为 BYOK
- [ ] 设置请求大小限制

**配置示例**:

```javascript
const express = require('express');
const agentPass = require('agentpass-middleware');

const app = express();

// 限制请求大小
app.use(express.json({ limit: '1mb' }));

// 强制 HTTPS（生产环境）
app.use((req, res, next) => {
  if (process.env.NODE_ENV === 'production' && !req.secure) {
    return res.redirect(`https://${req.headers.host}${req.url}`);
  }
  next();
});

// 设置安全头
app.use((req, res, next) => {
  res.set('X-Content-Type-Options', 'nosniff');
  res.set('X-Frame-Options', 'DENY');
  res.set('X-XSS-Protection', '1; mode=block');
  next();
});

app.use('/api/agent', agentPass.gate());
```

### 客户端安全

- [ ] 不在代码中硬编码 API Key
- [ ] 使用环境变量或安全的密钥管理系统
- [ ] 验证 SSL/TLS 证书
- [ ] 设置请求超时
- [ ] 实施重试和熔断机制

**安全代码示例**:

```python
import os
from agentpass_client import AgentPassClient
import certifi

# 从环境变量获取 API Key
api_key = os.environ.get('AGENTPASS_API_KEY')
if not api_key:
    raise Exception("AGENTPASS_API_KEY not set")

# 初始化客户端
client = AgentPassClient(api_key=api_key)

# 使用 SSL 验证
response = client.request_site(
    'https://api.example.com',
    task,
    identity='secure-agent'
)
```

---

## 故障排查

### 常见问题

#### 问题 1: 发现失败

```
Discovery failed: Connection refused
```

**解决方案**:
1. 检查服务是否运行
2. 检查 URL 格式和协议
3. 检查网络连接

```bash
# 测试连接
curl https://api.example.com/.well-known/ai-agent.json
```

#### 问题 2: 握手失败

```
Invalid JSON in request body
```

**解决方案**:
1. 验证请求体是有效的 JSON
2. 检查 Content-Type 头

```bash
# 测试 JSON 格式
curl -X POST https://api.example.com/api/agent/entry \
  -H "Content-Type: application/json" \
  -d @request.json
```

#### 问题 3: 权限错误

```
Invalid auth_type. Only BYOK is supported.
```

**解决方案**:
1. 检查 auth_type 字段是否为 "BYOK"
2. 检查 credentials 是否包含 api_key

#### 问题 4: 超时

```
Request failed: Connection timeout
```

**解决方案**:
1. 增加超时时间
2. 检查服务响应时间
3. 检查网络延迟

### 调试模式

**服务器端调试**:

```javascript
// 添加详细日志
app.post('/api/agent/entry', (req, res) => {
  console.log('[DEBUG] Request body:', JSON.stringify(req.agentContext));
  console.log('[DEBUG] Context keys:', Object.keys(req.agentContext || {}));
  // ... 处理 ...
});
```

**客户端调试**:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('agentpass_client')

# 启用详细输出
response = client.request_site(url, task)
```

### 性能监控

**中间件性能**:

```javascript
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    console.log(`${req.method} ${req.path} - ${duration}ms`);
  });
  next();
});
```

**客户端性能**:

```python
import time

start = time.time()
response = client.request_site(url, task)
duration = time.time() - start

print(f"Request took {duration:.2f}s")
```

---

## 更新和维护

### 检查更新

```bash
# Node.js 中间件
npm outdated agentpass-middleware
npm update agentpass-middleware

# Python 客户端  
pip install --upgrade agentpass-client
```

### 版本兼容性

| 组件 | 版本 | 说明 |
|------|------|------|
| Node.js | 12+ | 建议 16+ |
| Express | 4.17+ | 最小依赖 |
| Python | 3.7+ | 建议 3.9+ |
| requests | 2.28+ | HTTP 库 |

---

## 技术支持

- 问题报告: https://github.com/agentpass/issues
- 文档: https://github.com/agentpass/wiki
- 社区: https://github.com/agentpass/discussions
