from typing import TypeVar, Any, AsyncGenerator, Callable
import pytest

from .environment import Environment
from .sample import Sample
from .client import AgentClient, ResponseClient
    
class IntegrationFixtures:
    """Provides integration test fixtures."""

    _environment: Environment
    _sample: Sample
    _agent_client: AgentClient
    _response_client: ResponseClient

    @pytest.fixture
    def environment(self) -> Environment:
        """Provides the test environment instance."""
        return self._environment
    
    @pytest.fixture
    def sample(self) -> Sample:
        """Provides the sample instance."""
        return self._sample
    
    @pytest.fixture
    def agent_client(self) -> AgentClient:
        return self._agent_client

    @pytest.fixture
    async def response_client(self) -> AsyncGenerator[ResponseClient, None]:
        """Provides the response client instance."""
        async with ResponseClient() as response_client:
            yield response_client

    @pytest.fixture
    def create_response_client(self) -> Callable[None, ResponseClient]:
        return lambda: ResponseClient()