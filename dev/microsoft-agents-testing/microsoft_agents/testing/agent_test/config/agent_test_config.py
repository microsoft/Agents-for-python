from dataclasses import dataclass

from microsoft_agents.activity import Activity

from microsoft_agents.testing.utils import ActivityTemplate

@dataclass
class AgentTestConfig:

    service_url: str | None = None
    scenario_config: AgentScenarioConfig | None = None
    activity_template: ActivityTemplate | None = None
    
    kwargs: dict | None = None

class AgentTestsConfigBuilder:

    def __init__(self):
        pass

    def service_url(self, url: str) -> AgentTestsConfigBuilder:
        return self

    def build(self) -> AgentTestConfig:
        return AgentTestConfig()