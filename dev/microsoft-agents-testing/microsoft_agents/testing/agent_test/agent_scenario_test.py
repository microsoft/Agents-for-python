import pytest

from .agent_test import AgentTest
from .agent_test_config import AgentTestConfig

from .components import AgentScenario

class AgentScenarioTest(AgentTest):
    
    def __init__(self, config: AgentTestConfig, scenario: AgentScenario):
        super().__init__(config)
        self._scenario = scenario

    async def run(self):
        
        async with self._scenario.run() as agent_endpoint:

            async with self._create_test_client(agent_endpoint) as test_client:
                yield test_client