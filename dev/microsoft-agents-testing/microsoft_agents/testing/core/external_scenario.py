# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dotenv import dotenv_values

from microsoft_agents.activity import load_configuration_from_env

from ._aiohttp_client_factory import _AiohttpClientFactory
from .scenario import Scenario, ScenarioConfig, ClientFactory
from .transport import AiohttpCallbackServer


class ExternalScenario(Scenario):
    """Scenario for testing an externally-hosted agent."""
    
    def __init__(self, endpoint: str, config: ScenarioConfig | None = None) -> None:
        super().__init__(config)
        if not endpoint:
            raise ValueError("endpoint must be provided.")
        self._endpoint = endpoint

    @asynccontextmanager
    async def run(self) -> AsyncIterator[ClientFactory]:
        """Start callback server and yield a client factory."""
        
        env_vars = dotenv_values(self._config.env_file_path)
        sdk_config = load_configuration_from_env(env_vars)
        
        callback_server = AiohttpCallbackServer(self._config.callback_server_port)

        async with callback_server.listen() as transcript:

            factory = _AiohttpClientFactory(
                agent_url=self._endpoint,
                response_endpoint=callback_server.service_endpoint,
                sdk_config=sdk_config,
                default_config=self._config.client_config,
                transcript=transcript,
            )
            
            try:
                yield factory
            finally:
                await factory.cleanup()