from os import environ
from microsoft.agents.authentication.msal import AuthTypes, MsalAuthConfiguration


class DefaultConfig(MsalAuthConfiguration):
    """Agent Configuration"""

    def __init__(self) -> None:
        self.AUTH_TYPE = AuthTypes.client_secret
        self.TENANT_ID = "" or environ.get("TENANT_ID")
        self.CLIENT_ID = "" or environ.get("CLIENT_ID")
        self.CLIENT_SECRET = "" or environ.get("CLIENT_SECRET")
        self.CONNECTION_NAME = "" or environ.get("CONNECTION_NAME")
        self.PORT = 3978
