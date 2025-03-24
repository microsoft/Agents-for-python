from microsoft.agents.authentication.msal import AuthTypes, MsalAuthConfiguration


class DefaultConfig(MsalAuthConfiguration):
    """Agent Configuration"""

    AUTH_TYPE = AuthTypes.client_secret
    TENANT_ID = ""
    CLIENT_ID = ""
    CLIENT_SECRET = ""
    PORT = 3978
