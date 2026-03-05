# AgentPass Client SDK

Python client library for the AgentPass protocol - enabling agents to communicate with websites supporting machine-to-machine login.

## Installation

```bash
pip install requests
```

Or from source:

```bash
python setup.py install
```

## Quick Start

```python
from agentpass_client import AgentPassClient

# Create a client with your API key
client = AgentPassClient(api_key="sk-your-api-key-here")

# Define a task
task = {
    "action": "analyze",
    "params": {
        "url": "https://example.com"
    }
}

# Send request to a website
response = client.request_site("https://myservice.com", task)

if response:
    print("Success:", response)
else:
    print("Failed to get response")
```

## Features

- **Protocol Discovery**: Automatically discovers if a website supports AgentPass
- **Handshake Construction**: Builds standard AgentPass request packets
- **Stateless Communication**: No session management required
- **Batch Requests**: Support for sending multiple tasks
- **Error Handling**: Graceful failure handling with informative messages

## API Reference

### AgentPassClient

```python
client = AgentPassClient(api_key, provider="openai")
```

#### Methods

**discover(url: str) -> Optional[Dict]**
- Checks if a website supports AgentPass protocol
- Returns the protocol configuration if supported

**request_site(url: str, task: Dict, identity: Optional[str]) -> Optional[Dict]**
- Sends a request to a website using AgentPass protocol
- Automatically discovers protocol support
- Constructs and sends the handshake packet
- Returns the response from the website

**request_batch(url: str, tasks: list) -> list**
- Sends multiple tasks to the same website
- Returns a list of responses

### Quick Function

```python
from agentpass_client import quick_request

response = quick_request(
    api_key="sk-xxx",
    url="https://service.com",
    task={"action": "analyze", "params": {}}
)
```

## Request Format

The client automatically constructs the AgentPass handshake packet:

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

## Example: Batch Processing

```python
from agentpass_client import AgentPassClient

client = AgentPassClient(api_key="sk-your-key")

tasks = [
    {"action": "analyze", "params": {"url": "http://example1.com"}},
    {"action": "analyze", "params": {"url": "http://example2.com"}},
    {"action": "summarize", "params": {"text": "Some text to summarize"}}
]

results = client.request_batch("https://processing-service.com", tasks)

for i, result in enumerate(results):
    print(f"Task {i}: {result}")
```

## Security Notes

- API keys are never stored on disk
- Communication should use HTTPS
- The server-side middleware ensures keys are cleared from memory after each request
- Follow BYOK (Bring Your Own Key) principle

## License

MIT
