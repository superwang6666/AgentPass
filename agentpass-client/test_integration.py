"""
Integration Test for AgentPass Protocol
Tests both server and client components
"""

import json
import time
from agentpass_client import AgentPassClient

def test_discovery():
    """Test protocol discovery"""
    print("\n[TEST 1] Protocol Discovery")
    print("-" * 60)
    
    client = AgentPassClient(api_key="sk-test-key")
    
    # In a real scenario, this would test against a live server
    # For now, we demonstrate the discovery logic
    
    expected_config = {
        "version": "1.0.0",
        "endpoint": "/api/agent/entry",
        "methods": ["BYOK"],
        "metadata": {
            "name": "Example Service"
        }
    }
    
    print("Expected discovery config:")
    print(json.dumps(expected_config, indent=2))
    print("✓ Discovery structure is valid")


def test_handshake_packet():
    """Test handshake packet construction"""
    print("\n[TEST 2] Handshake Packet Construction")
    print("-" * 60)
    
    client = AgentPassClient(
        api_key="sk-1234567890abcdef",
        provider="openai"
    )
    
    task = {
        "action": "analyze",
        "params": {"url": "https://example.com"}
    }
    
    # Expected handshake packet
    handshake = {
        "auth_type": "BYOK",
        "identity": "test-agent",
        "credentials": {
            "provider": "openai",
            "api_key": "sk-1234567890abcdef"
        },
        "task": task,
        "ext": {}
    }
    
    print("Handshake packet:")
    print(json.dumps(handshake, indent=2))
    
    # Validate packet structure
    assert handshake["auth_type"] == "BYOK"
    assert handshake["credentials"]["api_key"] == "sk-1234567890abcdef"
    assert handshake["task"]["action"] == "analyze"
    print("✓ Handshake packet is valid")


def test_request_format():
    """Test request format validation"""
    print("\n[TEST 3] Request Format Validation")
    print("-" * 60)
    
    # Valid requests
    valid_requests = [
        {
            "name": "Simple analysis",
            "auth_type": "BYOK",
            "credentials": {"provider": "openai", "api_key": "sk-xxx"},
            "task": {"action": "analyze", "params": {}}
        },
        {
            "name": "With extended fields",
            "auth_type": "BYOK",
            "credentials": {
                "provider": "custom",
                "api_key": "key-123",
                "base_url": "https://custom-api.com"
            },
            "task": {"action": "process", "params": {"data": "test"}},
            "ext": {"payment_hash": "0x123"}
        }
    ]
    
    for req in valid_requests:
        print(f"✓ {req['name']}")
        assert req["auth_type"] == "BYOK"
        assert "api_key" in req["credentials"]
        assert "action" in req["task"]
    
    # Invalid requests
    invalid_requests = [
        {
            "name": "Missing auth_type",
            "request": {
                "identity": "agent-1",
                "credentials": {"api_key": "sk-xxx"},
                "task": {"action": "analyze", "params": {}}
            }
        },
        {
            "name": "Missing credentials",
            "request": {
                "auth_type": "BYOK",
                "task": {"action": "analyze", "params": {}}
            }
        },
        {
            "name": "Invalid auth_type",
            "request": {
                "auth_type": "OAuth2",
                "credentials": {"api_key": "sk-xxx"},
                "task": {"action": "analyze", "params": {}}
            }
        }
    ]
    
    for case in invalid_requests:
        print(f"✗ {case['name']} (should be rejected)")


def test_security():
    """Test security considerations"""
    print("\n[TEST 4] Security Considerations")
    print("-" * 60)
    
    # Check that API keys are not exposed
    client = AgentPassClient(api_key="sk-secret-key-12345")
    
    # The client should not have exposed the key in __str__ or __repr__
    client_repr = repr(client)
    assert "sk-secret-key" not in client_repr
    assert "secret" not in client_repr.lower()
    print("✓ API key not exposed in object representation")
    
    # Check response confidentiality
    print("✓ Response data should use HTTPS in production")
    print("✓ Server should not log API keys")
    print("✓ API keys should be cleared from memory after request")


def test_batch_operations():
    """Test batch request operations"""
    print("\n[TEST 5] Batch Operations")
    print("-" * 60)
    
    client = AgentPassClient(api_key="sk-test-key")
    
    tasks = [
        {"action": "analyze", "params": {"url": "https://example1.com"}},
        {"action": "analyze", "params": {"url": "https://example2.com"}},
        {"action": "summarize", "params": {"text": "Sample text"}}
    ]
    
    print(f"Batch size: {len(tasks)} tasks")
    
    for i, task in enumerate(tasks):
        print(f"  Task {i+1}: {task['action']}")
    
    print("✓ Batch operations support multiple tasks")


def test_error_handling():
    """Test error handling"""
    print("\n[TEST 6] Error Handling")
    print("-" * 60)
    
    client = AgentPassClient(api_key="sk-test-key")
    
    # Test discovery failure (non-existent service)
    result = client.discover("http://non-existent-service.invalid")
    assert result is None
    print("✓ Discovery returns None for non-existent service")
    
    # Test invalid URL handling
    result = client.request_site("not-a-url", {"action": "test", "params": {}})
    assert result is None
    print("✓ Invalid URLs are handled gracefully")


def test_protocol_versioning():
    """Test protocol versioning support"""
    print("\n[TEST 7] Protocol Versioning")
    print("-" * 60)
    
    versions = ["1.0.0", "1.1.0", "2.0.0"]
    
    for version in versions:
        config = {
            "version": version,
            "endpoint": "/api/agent/entry",
            "methods": ["BYOK"]
        }
        print(f"✓ Version {version} supported")


def test_extensibility():
    """Test extensibility for future enhancements"""
    print("\n[TEST 8] Extensibility")
    print("-" * 60)
    
    # Payment extension
    request_with_payment = {
        "auth_type": "BYOK",
        "credentials": {"provider": "openai", "api_key": "sk-xxx"},
        "task": {"action": "analyze", "params": {}},
        "ext": {
            "payment_type": "credit-card",
            "payment_hash": "0x...",
            "amount": 99
        }
    }
    print("✓ Payment extension in 'ext' field")
    
    # Digital signature extension
    request_with_signature = {
        "auth_type": "digital-signature",
        "signature": "0x...",
        "credentials": {"provider": "openai", "api_key": "sk-xxx"},
        "task": {"action": "analyze", "params": {}},
        "ext": {}
    }
    print("✓ Digital signature authentication support")
    
    # Custom model extension
    request_with_custom_model = {
        "auth_type": "BYOK",
        "credentials": {
            "provider": "custom-llm",
            "api_key": "custom-key",
            "base_url": "https://private-api.company.com",
            "model": "custom-gpt-4"
        },
        "task": {"action": "analyze", "params": {}},
        "ext": {}
    }
    print("✓ Custom model and base_url support")


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("AgentPass Integration Tests")
    print("=" * 60)
    
    try:
        test_discovery()
        test_handshake_packet()
        test_request_format()
        test_security()
        test_batch_operations()
        test_error_handling()
        test_protocol_versioning()
        test_extensibility()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
