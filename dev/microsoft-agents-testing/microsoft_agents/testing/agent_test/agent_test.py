import pytest

from contextlib import asynccontextmanager
from typing import Callable
from abc import ABC, abstractmethod

from .agent_test_config import AgentTestConfig

from .components import (
    ResponseClient,
    SenderClient,
    TestClient,
)

class AgentTest:
    
    def __init__(self, config: AgentTestConfig):
        self._config = config
        self._scenario: AgentScenario | None = None


    async def _create_test_client(self, agent_endpoint: str):
        test_client = TestClient(agent_endpoint, self._config)

        yield test_client.connect()

        test_client.close()

    @asynccontextmanager
    async def run(self):

        if self._scenario is None: # external case
            async with self._create_test_client(agent_endpoint) as test_client:
                yield test_client
        else: # scenario case
            async with self._scenario.run() as agent_endpoint:
                async with self._run_external(agent_endpoint) as test_client:
                    yield test_client
    
    def decorate(self, cls: type):

        if not isinstance(cls, type):
            raise ValueError("The decorate method can only be used to decorate classes.")
        
        if self._scenario is not None:
            for fixture in self._fixtures():
                if getattr(cls, fixture.__name__, None) is not None:
                    raise ValueError(f"The class {cls.__name__} already has an attribute named {fixture.__name__}, cannot decorate.")
                setattr(cls, fixture.__name__, fixture)
            return cls
        
    @classmethod
    def scenario(cls, scenario: AgentScenario):

        ins = cls(AgentTestConfig(), scenario)

        return ins.decorate
    
    @classmethod
    def external(cls, agent_endpoint: str, config: AgentTestConfig | None = None):

        ins = cls(config, agent_endpoint)

        return ins.decorate

    ###
    ### Fixtures
    ####

    @pytest.fixture
    async def test_client(self) -> TestClient:
        async with self.run() as client:
            yield client
    
    def _fixtures(self):
        scenario_fixtures = self._scenario.get_fixtures() if self._scenario is not None else []
        return [
            self.test_client,
        ] + scenario_fixtures