from microsoft.agents.authorization.msal import AuthTypes, MsalAuthConfiguration


class DefaultConfig(MsalAuthConfiguration):
    """Bot Configuration"""

    AUTH_TYPE = AuthTypes.client_secret
    TENANT_ID = ""
    CLIENT_ID = ""
    CLIENT_SECRET = ""
    PORT = 3999
