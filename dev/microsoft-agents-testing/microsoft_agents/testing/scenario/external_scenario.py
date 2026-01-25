from __future__ import annotations
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from aiohttp import ClientSession

from microsoft_agents.testing.utils import generate_token_from_config
from microsoft_agents.testing.client import AgentClient
from microsoft_agents.testing.client.client_config import ClientConfig
from microsoft_agents.testing.client.transport.aiohttp_sender import AiohttpActivitySender
from microsoft_agents.testing.client.receiver.aiohttp_server import AiohttpResponseServer

from .aiohttp import AiohttpClientFactory
from .base import Scenario, ScenarioConfig

from microsoft_agents.testing.client import (
    AiohttpSender,
    AiohttpCallbackServer,
    Transcript,
    AgentClient,
)


class ExternalScenario(Scenario):
    """Scenario for testing an externally-hosted agent."""
    
    def __init__(self, endpoint: str, config: ScenarioConfig | None = None) -> None:
        super().__init__(config)
        if not endpoint:
            raise ValueError("endpoint must be provided.")
        self._endpoint = endpoint

    @asynccontextmanager
    async def run(self) -> AsyncIterator[AiohttpClientFactory]:
        """Start callback server and yield a client factory."""
        from dotenv import dotenv_values
        from microsoft_agents.activity import load_configuration_from_env
        
        env_vars = dotenv_values(self._config.env_file_path)
        sdk_config = load_configuration_from_env(env_vars)
        
        callback_server = AiohttpCallbackServer(self._config.response_server_port)

        async with callback_server.listen() as transcript:

            sender = AiohttpActivitySender(
                endpoint=self._endpoint,
                transcript=transcript,
            )

            factory = AiohttpClientFactory(
                agent_endpoint=self._endpoint,
                response_endpoint=response_server.service_endpoint,
                sdk_config=sdk_config,
                default_template=self._config.default_activity_template,
                default_config=self._config.default_client_config,
                response_receiver=receiver,
            )
            
            try:
                yield factory
            finally:
                await factory.cleanup()