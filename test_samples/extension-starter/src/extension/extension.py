from microsoft_agents.hosting.core import (
    AgentApplication,
)

class ExtensionAgent:

    def __init__(self, app: AgentApplication):
        self.app = app

    def