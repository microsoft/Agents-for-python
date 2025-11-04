import pytest
import asyncio

import os
from typing import (
    Optional,
    TypeVar,
    Union,
    Callable,
    Any,
    AsyncGenerator,
)

import aiohttp.web
from dotenv import load_dotenv

from .application_runner import ApplicationRunner
from .environment import Environment
from .client import AgentClient, ResponseClient
from .sample import Sample
from .utils import get_host_and_port

T = TypeVar("T", bound=type)
AppT = TypeVar("AppT", bound=aiohttp.web.Application)  # for future extension w/ Union


class IntegrationFixtures:
    """Provides integration test fixtures."""

    _sample_cls: Optional[type[Sample]] = None
    _environment_cls: Optional[type[Environment]] = None

    _config: dict[str, Any] = {}

    _service_url: Optional[str] = None
    _agent_url: Optional[str] = None
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
            async with environment.create_runner(host, port):
                await asyncio.sleep(1)  # Give time for the app to start
                yield sample
        else:
            yield None

    def create_agent_client(self) -> AgentClient:
        if not self._config:
            self._config = {}

            load_dotenv("./dev/integration/src/tests/.env")
            self._config.update(
                {
                    "client_id": os.getenv("CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID", ""),
                    "tenant_id": os.getenv("CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID", ""),
                    "client_secret": os.getenv("CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET", ""),
                }
            )

        agent_client = AgentClient(
            agent_url=self.agent_url,
            cid=self._cid or self._config.get("cid", ""),
            client_id=self._client_id or self._config.get("client_id", ""),
            tenant_id=self._tenant_id or self._config.get("tenant_id", ""),
            client_secret=self._client_secret or self._config.get("client_secret", ""),
        )
        return agent_client

    @pytest.fixture
    async def agent_client(self, sample, environment) -> AsyncGenerator[AgentClient, None]:
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


def integration(
    agent_url: Optional[str] = "http://localhost:3978/",
    sample: Optional[type[Sample]] = None,
    environment: Optional[type[Environment]] = None,
    app: Optional[AppT] = None,
    **kwargs
) -> Callable[[T], T]:
    """Factory function to create an Integration instance based on provided parameters.

    Essentially resolves to one of the static methods of Integration:
        `from_service_url`, `from_sample`, or `from_app`,
    based on the provided parameters.

    If a service URL is provided, it creates the Integration using that.
    If both sample and environment are provided, it creates the Integration using them.
    If an aiohttp application is provided, it creates the Integration using that.

    :param cls: The Integration class type.
    :param service_url: Optional service URL to connect to.
    :param sample: Optional Sample instance.
    :param environment: Optional Environment instance.
    :param host_agent: Flag to indicate if the agent should be hosted.
    :param app: Optional aiohttp application instance.
    :return: An instance of the Integration class.
    """

    def decorator(target_cls: T) -> T:

        if agent_url:
            target_cls._agent_url = agent_url
        if sample and environment:
            target_cls._sample_cls = sample
            target_cls._environment_cls = environment

        target_cls._config = kwargs

        return target_cls

    return decorator
