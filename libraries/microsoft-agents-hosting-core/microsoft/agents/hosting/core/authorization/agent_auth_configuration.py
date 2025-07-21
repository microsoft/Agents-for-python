from typing import Optional

from microsoft.agents.hosting.core.authorization.auth_types import AuthTypes


class AgentAuthConfiguration:
    """
    Configuration for Agent authentication.
    """

    TENANT_ID: Optional[str]
    CLIENT_ID: Optional[str]
    AUTH_TYPE: AuthTypes
    CLIENT_SECRET: Optional[str]
    CERT_PEM_FILE: Optional[str]
    CERT_KEY_FILE: Optional[str]
    CONNECTION_NAME: Optional[str]
    SCOPES: Optional[list[str]]
    AUTHORITY: Optional[str]

    def __init__(
        self,
        auth_type: AuthTypes = None,
        client_id: str = None,
        tenant_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        cert_pem_file: Optional[str] = None,
        cert_key_file: Optional[str] = None,
        connection_name: Optional[str] = None,
        authority: Optional[str] = None,
        scopes: Optional[list[str]] = None,
        **kwargs: Optional[dict[str, str]],
    ):
        self.AUTH_TYPE = auth_type or kwargs.get("AUTHTYPE", AuthTypes.client_secret)
        self.CLIENT_ID = client_id or kwargs.get("CLIENTID", None)
        self.AUTHORITY = authority or kwargs.get("AUTHORITY", None)
        self.TENANT_ID = tenant_id or kwargs.get("TENANTID", None)
        self.CLIENT_SECRET = client_secret or kwargs.get("CLIENTSECRET", None)
        self.CERT_PEM_FILE = cert_pem_file or kwargs.get("CERTPEMFILE", None)
        self.CERT_KEY_FILE = cert_key_file or kwargs.get("CERTKEYFILE", None)
        self.CONNECTION_NAME = connection_name or kwargs.get("CONNECTIONNAME", None)
        self.SCOPES = scopes or kwargs.get("SCOPES", None)

    @property
    def ISSUERS(self) -> list[str]:
        """
        Gets the list of issuers.
        """
        return [
            "https://api.botframework.com",
            f"https://sts.windows.net/{self.TENANT_ID}/",
            f"https://login.microsoftonline.com/{self.TENANT_ID}/v2.0",
        ]
