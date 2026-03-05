"""
AgentPass Client SDK
Agent-side implementation for machine-to-machine login
"""

import requests
import json
import logging
from typing import Dict, Any, Optional

# Configure logger
logger = logging.getLogger(__name__)


class AgentPassClient:
    """
    AgentPass Client for Agent to communicate with websites supporting AgentPass protocol
    """

    def __init__(self, api_key: str, provider: str = "openai"):
        """
        Initialize AgentPass client

        Args:
            api_key: The API key to use for requests
            provider: The provider name (e.g., "openai", "anthropic")
        """
        self.api_key = api_key
        self.provider = provider
        self.identity = "agentpass-client"

    def discover(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Discover if a website supports AgentPass protocol

        Args:
            url: Base URL of the website

        Returns:
            Protocol configuration dict if supported, None otherwise
        """
        try:
            # Ensure URL has protocol
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            # Remove trailing slash for clean path construction
            url = url.rstrip('/')

            # Try to fetch the discovery document
            discovery_url = f"{url}/.well-known/ai-agent.json"
            response = requests.get(discovery_url, timeout=5)

            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            logger.debug(f"Discovery failed for {url}: {e}")
            return None

    def request_site(self, url: str, task: Dict[str, Any], 
                    identity: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Send a request to a website using AgentPass protocol

        Args:
            url: Base URL of the website
            task: Task payload with 'action' and 'params'
            identity: Optional identity override

        Returns:
            Response from the website or None if failed
        """
        try:
            # Use provided identity or default
            agent_identity = identity or self.identity

            # Ensure URL has protocol
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            # Remove trailing slash
            url = url.rstrip('/')

            # Step 1: Discover protocol support
            config = self.discover(url)
            if not config:
                logger.debug(f"Website {url} does not support AgentPass protocol")
                return None

            # Step 2: Build handshake packet
            handshake = {
                "auth_type": "BYOK",
                "identity": agent_identity,
                "credentials": {
                    "provider": self.provider,
                    "api_key": self.api_key
                },
                "task": task,
                "ext": {}
            }

            # Step 3: Get the endpoint from config
            endpoint = config.get('endpoint', '/api/agent/entry')

            # Step 4: Send POST request with handshake
            request_url = f"{url}{endpoint}"
            response = requests.post(
                request_url,
                json=handshake,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.debug(f"Request to {request_url} failed with status {response.status_code}")
                return None

        except Exception as e:
            logger.debug(f"Request failed: {e}")
            return None

    def request_batch(self, url: str, tasks: list) -> list:
        """
        Send multiple requests in batch

        Args:
            url: Base URL of the website
            tasks: List of task payloads

        Returns:
            List of responses
        """
        results = []
        for task in tasks:
            result = self.request_site(url, task)
            results.append(result)
        return results


# Convenience function for quick one-off requests
def quick_request(api_key: str, url: str, task: Dict[str, Any], 
                 provider: str = "openai") -> Optional[Dict[str, Any]]:
    """
    Quick helper to make a single AgentPass request

    Args:
        api_key: The API key to use
        url: Target website URL
        task: Task payload
        provider: Provider name

    Returns:
        Response from the website
    """
    client = AgentPassClient(api_key, provider)
    return client.request_site(url, task)
