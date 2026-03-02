# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Internal factory for creating aiohttp-based AgentClient instances.

This module provides the factory implementation used by scenarios to create
configured AgentClient instances with proper HTTP session management.
"""

from aiohttp import ClientSession

from .agent_client import AgentClient
from .config import ClientConfig
from .fluent import ActivityTemplate
from .transport import (
    Transcript,
    AiohttpSender,
)
from .utils import generate_token_from_config


class _AiohttpClientFactory:
    """Internal factory for creating AgentClient instances using aiohttp.
    
    This factory manages HTTP session lifecycle and handles authentication
    token generation. It is used internally by scenario implementations.
    
    Note:
        This is an internal class. Use Scenario.run() or Scenario.client()
        instead of instantiating this directly.
    """
    
    def __init__(
        self,
        agent_url: str,
        response_endpoint: str,
        sdk_config: dict,
        default_template: ActivityTemplate | None = None,
        default_config: ClientConfig | None = None,
        transcript: Transcript | None = None,
    ):
        self._agent_url = agent_url
        self._response_endpoint = response_endpoint
        self._sdk_config = sdk_config
        self._default_template = default_template or ActivityTemplate()
        self._default_config = default_config or ClientConfig()
        self._transcript = transcript
        self._sessions: list[ClientSession] = []  # track for cleanup
    
    async def __call__(self, config: ClientConfig | None = None) -> AgentClient:
        """Create a new client with the given configuration."""
        config = config or self._default_config
        
        # Build headers
        headers = {"Content-Type": "application/json", **config.headers}
        
        # Handle auth
        if config.auth_token:
            headers["Authorization"] = f"Bearer {config.auth_token}"
        elif "Authorization" not in headers:
            # Try to generate from SDK config
            try:
                token = generate_token_from_config(self._sdk_config)
                headers["Authorization"] = f"Bearer {token}"
            except Exception:
                pass  # No auth available
        
        # Create session
        session = ClientSession(base_url=self._agent_url, headers=headers)
        self._sessions.append(session)
        
        # Build activity template with user identity
        template = config.activity_template or self._default_template
        template = template.with_updates(
            service_url=self._response_endpoint,
        )
        
        # Create sender and client
        sender = AiohttpSender(session)
        return AgentClient(sender, self._transcript, template=template)
    
    async def cleanup(self):
        """Close all HTTP sessions created by this factory.

        Should be called when the scenario finishes to release resources.
        """
        for session in self._sessions:
            await session.close()
        self._sessions.clear()
