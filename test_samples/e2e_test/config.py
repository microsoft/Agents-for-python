from os import environ
from microsoft.agents.hosting.core import AuthTypes, AgentAuthConfiguration


class DefaultConfig(AgentAuthConfiguration):
    """Agent Configuration"""

    def __init__(self) -> None:
        self.AUTH_TYPE = AuthTypes.client_secret
        self.TENANT_ID = "" or environ.get("TENANT_ID")
        self.CLIENT_ID = "" or environ.get("CLIENT_ID")
        self.CLIENT_SECRET = "" or environ.get("CLIENT_SECRET")
        self.AZURE_OPENAI_API_KEY = "" or environ.get("AZURE_OPENAI_API_KEY")
        self.AZURE_OPENAI_ENDPOINT = "" or environ.get("AZURE_OPENAI_ENDPOINT")
        self.AZURE_OPENAI_API_VERSION = "" or environ.get(
            "AZURE_OPENAI_API_VERSION", "2024-06-01"
        )
        self.PORT = 3978
