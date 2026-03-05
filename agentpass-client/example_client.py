"""
Example Client using AgentPass SDK
This shows how an AI agent can use the AgentPass client to communicate
with services that support the AgentPass protocol
"""

from agentpass_client import AgentPassClient, quick_request

def main():
    print("=" * 60)
    print("AgentPass Client Example")
    print("=" * 60)
    
    # Example 1: Using the high-level client
    print("\n[Example 1] Using AgentPassClient")
    print("-" * 60)
    
    client = AgentPassClient(
        api_key="sk-test-key-1234567890abcdef",
        provider="openai"
    )
    
    # First, discover if the service supports AgentPass
    url = "http://localhost:3000"
    print(f"Discovering AgentPass support at {url}...")
    
    config = client.discover(url)
    if config:
        print("✓ Service supports AgentPass!")
        print(f"  Version: {config.get('version')}")
        print(f"  Endpoint: {config.get('endpoint')}")
        print(f"  Methods: {config.get('methods')}")
    else:
        print("✗ Service does not support AgentPass")
        return
    
    # Create a task
    task = {
        "action": "analyze",
        "params": {
            "url": "https://example.com",
            "depth": "detailed"
        }
    }
    
    print("\nSending request with task:")
    print(f"  Action: {task['action']}")
    print(f"  Params: {task['params']}")
    
    # Send the request
    response = client.request_site(url, task, identity="my-ai-agent")
    
    if response:
        print("✓ Request successful!")
        print(f"  Response: {response}")
    else:
        print("✗ Request failed")
    
    # Example 2: Using the quick function
    print("\n[Example 2] Using quick_request function")
    print("-" * 60)
    
    task2 = {
        "action": "summarize",
        "params": {
            "text": "Here is some text to summarize...",
            "length": "brief"
        }
    }
    
    response2 = quick_request(
        api_key="sk-test-key-another-key",
        url="http://localhost:3000",
        task=task2,
        provider="openai"
    )
    
    if response2:
        print("✓ Quick request successful!")
        print(f"  Response: {response2}")
    else:
        print("✗ Quick request failed")
    
    # Example 3: Batch requests
    print("\n[Example 3] Batch requests")
    print("-" * 60)
    
    tasks = [
        {
            "action": "analyze",
            "params": {"url": "https://example1.com"}
        },
        {
            "action": "analyze",
            "params": {"url": "https://example2.com"}
        },
        {
            "action": "summarize",
            "params": {"text": "Sample text"}
        }
    ]
    
    print(f"Sending {len(tasks)} tasks in batch...")
    results = client.request_batch(url, tasks)
    
    for i, result in enumerate(results):
        if result:
            print(f"  Task {i+1}: ✓ {result.get('message', 'Success')}")
        else:
            print(f"  Task {i+1}: ✗ Failed")


if __name__ == "__main__":
    main()
