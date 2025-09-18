from microsoft_agents.hosting.core import (
    ConnectorClient
)

class MyConnectorClient(ConnectorClient):

    def __init__(self, base_url: str, **kwargs):
        super().__init__(base_url, **kwargs)