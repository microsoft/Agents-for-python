# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from aiohttp import ClientSession

from .agent_client import AgentClient
from .client_config import ClientConfig
from .fluent import ActivityTemplate
from .transport import (
    Transcript,
    AiohttpSender,
)
from .utils import generate_token_from_config


class AiohttpClientFactory:
    """Factory for creating clients within an aiohttp scenario."""
    
    def __init__(
        self,
        agent_url: str,
        response_endpoint: str,
        sdk_config: dict,
        default_template: ActivityTemplate,
        default_config: ClientConfig,
        transcript: Transcript,
    ):
        self._agent_url = agent_url
        self._response_endpoint = response_endpoint
        self._sdk_config = sdk_config
        self._default_template = default_template
        self._default_config = default_config
        self._transcript = transcript
        self._sessions: list[ClientSession] = []  # track for cleanup
    
    async def create_client(self, config: ClientConfig | None = None) -> AgentClient:
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
            **{"from.id": config.user_id, "from.name": config.user_name},
        )
        
        # Create sender and client
        sender = AiohttpSender(session)
        return AgentClient(sender, self._transcript, template=template)
    
    async def cleanup(self):
        """Close all created sessions."""
        for session in self._sessions:
            await session.close()
        self._sessions.clear()
