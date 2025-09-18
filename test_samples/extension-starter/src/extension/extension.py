from microsoft_agents.hosting.core import (
    AgentApplication,
)

from src.extension.my_connector_client import MyConnectorClient

class ExtensionAgent:

    def __init__(self, app: AgentApplication):
        self.app = app

    @staticmethod
    def get_rest_client(self, context: TurnContext) -> MyConnectorClient:
        connector_client = context.turn_state.get("connector_client")
        return MyConnectorClient(connector_client)