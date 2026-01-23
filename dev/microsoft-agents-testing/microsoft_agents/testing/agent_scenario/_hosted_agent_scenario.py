from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from aiohttp import ClientSession

from microsoft_agents.testing.utils import generate_token_from_config
from microsoft_agents.testing.agent_client import (
    AgentClient,
    ResponseServer,
    SenderClient
)
from .agent_scenario import AgentScenario, AgentScenarioConfig

class _HostedAgentScenario(AgentScenario):
    """Base class for an agent test scenario with a hosted agent."""

    def __init__(self, config: AgentScenarioConfig | None = None) -> None:
        """Initialize the hosted agent scenario with the given configuration."""
        super().__init__(config)

    @asynccontextmanager
    async def _create_client(self, agent_endpoint: str) -> AsyncIterator[AgentClient]:
        """Create an asynchronous context manager for the agent client.
        
        :param agent_endpoint: The endpoint of the hosted agent.
        :yield: An asynchronous iterator that yields an AgentClient.
        """

        response_server = ResponseServer(self._config.response_server_port)
        async with response_server.listen() as collector:

            headers = {
                "Content-Type": "application/json",
            }

            try:
                token = generate_token_from_config(self._sdk_config)
                headers["Authorization"] = f"Bearer {token}"
            except Exception as e:
                pass

            async with ClientSession(base_url=agent_endpoint, headers=headers) as session:

                activity_template = self._config.activity_template.with_updates(
                    service_url=response_server.service_endpoint,
                )

                client = AgentClient(
                    SenderClient(session),
                    collector,
                    activity_template=activity_template,
                )

                yield client