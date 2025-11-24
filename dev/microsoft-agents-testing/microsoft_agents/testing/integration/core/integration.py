# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

import os
from typing import (
    Optional,
    TypeVar,
    Any,
    AsyncGenerator,
)

import aiohttp.web
from dotenv import load_dotenv

from microsoft_agents.testing.utils import get_host_and_port
from .environment import Environment
from .client import AgentClient, ResponseClient
from .sample import Sample

T = TypeVar("T", bound=type)
AppT = TypeVar("AppT", bound=aiohttp.web.Application)  # for future extension w/ Union


class Integration:
    """Provides integration test fixtures."""

    _sample_cls: Optional[type[Sample]] = None
    _environment_cls: Optional[type[Environment]] = None

    _config: dict[str, Any] = {}

    _service_url: Optional[str] = "http://localhost:9378"
    _agent_url: Optional[str] = "http://localhost:3978"
    _config_path: Optional[str] = "./src/tests/.env"
    _cid: Optional[str] = None
    _client_id: Optional[str] = None
    _tenant_id: Optional[str] = None
    _client_secret: Optional[str] = None

    _environment: Environment
    _sample: Sample
    _agent_client: AgentClient
    _response_client: ResponseClient

    @property
    def service_url(self) -> str:
        return self._service_url or self._config.get("service_url", "")

    @property
    def agent_url(self) -> str:
        return self._agent_url or self._config.get("agent_url", "")
    
    def setup_method(self):
        if not self._config:
            self._config = {}

            load_dotenv(self._config_path)
            self._config.update(
                {
                    "client_id": os.getenv(
                        "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID", ""
                    ),
                    "tenant_id": os.getenv(
                        "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID", ""
                    ),
                    "client_secret": os.getenv(
                        "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET", ""
                    ),
                }
            )

    @pytest.fixture
    async def environment(self):
        """Provides the test environment instance."""
        if self._environment_cls:
            assert self._sample_cls
            environment = self._environment_cls()
            await environment.init_env(await self._sample_cls.get_config())
            yield environment
        else:
            yield None

    @pytest.fixture
    async def sample(self, environment):
        """Provides the sample instance."""
        if environment:
            assert self._sample_cls
            sample = self._sample_cls(environment)
            await sample.init_app()
            host, port = get_host_and_port(self.agent_url)
            app_runner = environment.create_runner(host, port)
            async with app_runner:
                yield sample
        else:
            yield None

    def create_agent_client(self) -> AgentClient:

        agent_client = AgentClient(
            agent_url=self.agent_url,
            cid=self._cid or self._config.get("cid", ""),
            client_id=self._client_id or self._config.get("client_id", ""),
            tenant_id=self._tenant_id or self._config.get("tenant_id", ""),
            client_secret=self._client_secret or self._config.get("client_secret", ""),
            service_url=self.service_url,
        )
        return agent_client

    @pytest.fixture
    async def agent_client(
        self, sample, environment
    ) -> AsyncGenerator[AgentClient, None]:
        agent_client = self.create_agent_client()
        yield agent_client
        await agent_client.close()

    async def _create_response_client(self) -> ResponseClient:
        host, port = get_host_and_port(self.service_url)
        assert host and port
        return ResponseClient(host=host, port=port)

    @pytest.fixture
    async def response_client(self) -> AsyncGenerator[ResponseClient, None]:
        """Provides the response client instance."""
        async with await self._create_response_client() as response_client:
            yield response_client
