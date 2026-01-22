from dataclasses import dataclass

from microsoft_agents.testing.utils import ActivityTemplate

@dataclass
class AgentScenarioConfig:

    activity_template: ActivityTemplate
