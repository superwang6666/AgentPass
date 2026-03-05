# AgentPass Middleware

Express middleware for the AgentPass protocol - a minimal machine-to-machine login standard.

## Installation

```bash
npm install agentpass-middleware express
```

## Quick Start

```javascript
const express = require('express');
const agentPass = require('agentpass-middleware');

const app = express();

// Apply AgentPass middleware
app.use('/api/agent', agentPass.gate());

// Handle agent requests
app.post('/api/agent/entry', (req, res) => {
  // Extract API key from agent context
  const apiKey = req.agentContext.api_key;
  const provider = req.agentContext.provider;
  const task = req.agentContext.task;
  
  // Use the key to call your large model or service
  console.log('Agent task:', task);
  
  res.json({
    status: 'success',
    message: 'Task received'
  });
});

app.listen(3000, () => {
  console.log('Agent Pass server running on port 3000');
});
```

## How It Works

1. **Request Interception**: The middleware intercepts POST requests to `/api/agent/entry`
2. **Validation**: Validates that `auth_type` is `BYOK`
3. **Key Injection**: Extracts and injects the `credentials.api_key` into `req.agentContext`
4. **Stateless Processing**: After the response is sent, the API key is automatically destroyed from memory
5. **Auto Cleanup**: Uses `res.on('finish')` to ensure credentials are never persisted

## Request Format

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

## Response Context

After the middleware processes the request, the following properties are available in `req.agentContext`:

- `api_key`: The agent's API key
- `provider`: The provider name (e.g., "openai")
- `identity`: The agent's identity/name
- `task`: The task payload

## Security Features

- No database storage of API keys
- In-memory credentials only
- Automatic cleanup on response finish
- Strict auth_type validation
- Simple, auditable code

## License

MIT
