from __future__ import annotations
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dotenv import dotenv_values

from microsoft_agents.testing.client import (
    AgentClient,
    AiohttpCallbackServer,
)


from .aiohttp_client_factory import AiohttpClientFactory
from .scenario import Scenario, ScenarioConfig


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
        from microsoft_agents.activity import load_configuration_from_env
        
        env_vars = dotenv_values(self._config.env_file_path)
        sdk_config = load_configuration_from_env(env_vars)
        
        callback_server = AiohttpCallbackServer(self._config.response_server_port)

        async with callback_server.listen() as transcript:

            factory = AiohttpClientFactory(
                agent_url=self._endpoint,
                response_endpoint=callback_server.service_endpoint,
                sdk_config=sdk_config,
                default_template=self._config.default_activity_template,
                default_config=self._config.default_client_config,
                transcript=transcript,
            )
            
            try:
                yield factory
            finally:
                await factory.cleanup()