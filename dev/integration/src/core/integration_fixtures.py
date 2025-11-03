from typing import TypeVar, Any, AsyncGenerator, Callable, Optional
import pytest

from .environment import Environment
from .sample import Sample
from .client import AgentClient, ResponseClient
    
class IntegrationFixtures:
    """Provides integration test fixtures."""

    _sample_cls: Optional[type[Sample]] = None
    _environment_cls: Optional[type[Environment]] = None

    _environment: Environment
    _sample: Sample
    _agent_client: AgentClient
    _response_client: ResponseClient

    @pytest.fixture
    async def environment(self):
        """Provides the test environment instance."""
        assert self._environment_cls
        assert self._sample_cls
        environment = self._environment_cls()
        await environment.init_env(await self._sample_cls.get_config())
        yield environment
    
    @pytest.fixture
    async def sample(self, environment):
        """Provides the sample instance."""
        assert environment
        assert self._sample_cls
        sample = self._sample_cls(environment)
        await sample.init_app()
        yield sample
    
    @pytest.fixture
    def agent_client(self) -> AgentClient:
        return self._agent_client

    async def _create_response_client(self) -> ResponseClient:
        return ResponseClient()

    @pytest.fixture
    async def response_client(self) -> AsyncGenerator[ResponseClient, None]:
        """Provides the response client instance."""
        async with await self._create_response_client() as response_client:
            yield response_client