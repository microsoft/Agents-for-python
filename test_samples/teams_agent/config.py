from os import environ
from msagents.hosting.core import AuthTypes, AgentAuthConfiguration


class DefaultConfig(AgentAuthConfiguration):
    """Teams Agent Configuration"""

    def __init__(self) -> None:
        self.AUTH_TYPE = AuthTypes.client_secret
        self.TENANT_ID = "" or environ.get(
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID"
        )
        self.CLIENT_ID = "" or environ.get(
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID"
        )
        self.CLIENT_SECRET = "" or environ.get(
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET"
        )
        self.CONNECTION_NAME = "" or environ.get(
            "AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__GRAPH__SETTINGS__AZUREBOTOAUTHCONNECTIONNAME"
        )
        self.AGENT_TYPE = environ.get(
            "AGENT_TYPE", "TeamsHandler"
        )  # Default to TeamsHandler
        self.PORT = 3978
