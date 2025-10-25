from typing import TypeVar, Any
import pytest

from .environment import Environment
from .sample import Sample
from .client import AgentClient, AIAgentClient
from .response_server import ResponseServer
    
class IntegrationFixtures:
    """Provides integration test fixtures."""

    _environment: Environment
    _sample: Sample
    _response_server: ResponseServer

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
        ...
    
    @pytest.fixture
    def ai_agent_client(self) -> AIAgentClient:
        ...

    @pytest.fixture
    def response_server(self) -> ResponseServer:
        return self._response_server