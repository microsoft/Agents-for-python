from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from .agent_client import AgentClient
from ._hosted_agent_scenario import _HostedAgentScenario
from .agent_scenario import AgentScenarioConfig

class ExternalAgentScenario(_HostedAgentScenario):
    """Agent test scenario for an external hosted agent."""

    def __init__(self, endpoint: str, config: AgentScenarioConfig | None = None) -> None:
        """Initialize the external agent scenario with the given endpoint and configuration.
        
        :param endpoint: The endpoint of the external hosted agent.
        :param config: The configuration for the agent scenario.
        """
        if not endpoint:
            raise ValueError("endpoint must be provided.")
        super().__init__(config)
        self._endpoint = endpoint

    @asynccontextmanager
    async def client(self) -> AsyncIterator[AgentClient]:
        """Get an asynchronous context manager for the external agent client.
        
        :yield: An asynchronous iterator that yields an AgentClient.
        """
        async with self._create_client(self._endpoint) as client:
            yield client