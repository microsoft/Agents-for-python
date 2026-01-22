from __future__ import annotations

from typing import Callable, cast
from collections.abc import AsyncIterator

import pytest

from microsoft_agents.hosting.core import (
    AgentApplication,
    Authorization,
    ChannelServiceAdapter,
    Connections,
    Storage,
)

from .agent_client import AgentClient
from .agent_environment import AgentEnvironment
from .agent_scenario import AgentScenario, ExternalAgentScenario

class AgentTestConfig:
    
    pass

class AgentTestsConfigBuilder:

    def __init__(self):
        pass

    def service_url(self, url: str) -> AgentTestsConfigBuilder:
        return self

    def build(self) -> AgentTestConfig:
        return AgentTestConfig()

def _create_fixtures(scenario: AgentScenario) -> list[Callable]:
    """Create pytest fixtures for the given agent scenario."""

    fixtures = []

    @pytest.fixture
    async def agent_client(self) -> AsyncIterator[AgentClient]:
        async with scenario.run() as client:
            yield client

    if hasattr(scenario, "agent_environment"): # not super clean...

        agent_environmnent: AgentEnvironment = scenario.agent_environment

        @pytest.fixture
        def agent_environment(self, agent_client) -> AgentEnvironment:
            return agent_environmnent

        @pytest.fixture
        def agent_application(self, agent_environment) -> AgentApplication:
            return agent_environmnent.agent_application
        
        @pytest.fixture
        def authorization(self, agent_environment) -> Authorization:
            return agent_environmnent.authorization
        
        @pytest.fixture
        def storage(self, agent_environment) -> Storage:
            return agent_environmnent.storage
        
        @pytest.fixture
        def adapter(self, agent_environment) -> ChannelServiceAdapter:
            return agent_environmnent.adapter
        
        @pytest.fixture
        def connection_manager(self, agent_environment) -> Connections:
            return agent_environmnent.connections
        
        fixtures.extend([
            agent_environment,
            agent_application,
            authorization,
            storage,
            adapter,
            connection_manager
        ])
    
    return fixtures

    
def agent_test(
    arg: str | AgentScenario,
    config: AgentTestConfig | None = None
) -> Callable[[type], type]:
    """Class decorator to set up pytest fixtures that allow for the testing of agents
    based on the provided scenario.

    If a non-external scenario is provided, a new instance of the scenario will be created
    for each test case. A test case must use the `agent_client` fixture or one of the other
    fixtures provided by this decorator in order to interact with the agent.

    :param arg: Either a string representing the path to an external agent scenario
                or an AgentScenario instance to run.
    :param config: Optional configuration for the agent test.

    :return: A class decorator that adds the necessary pytest fixtures to the test class.
    """
    
    config = config or AgentTestConfig()

    fixtures = []

    scenario: AgentScenario
    if isinstance(arg, str):
        scenario = ExternalAgentScenario(arg, config)
    else:
        scenario = cast(AgentScenario, arg)

    fixtures = _create_fixtures(scenario)
    
    def decorator(cls: type) -> type:

        for fixture in fixtures:
            if getattr(cls, fixture.__name__, None) is not None:
                raise ValueError(f"The class {cls.__name__} already has an attribute named {fixture.__name__}, cannot decorate.")
            setattr(cls, fixture.__name__, fixture)
        
        return cls
    
    return decorator