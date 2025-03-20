from typing import Protocol, Optional

from microsoft.agents.authentication import AgentAuthConfiguration

from .auth_types import AuthTypes


class MsalAuthConfiguration(AgentAuthConfiguration, Protocol):
    """
    Configuration for MSAL authentication.
    """

    AUTH_TYPE: AuthTypes
    CLIENT_SECRET: Optional[str]
    CERT_PEM_FILE: Optional[str]
    CERT_KEY_FILE: Optional[str]
    CONNECTION_NAME: Optional[str]
    SCOPES: Optional[list[str]]
    AUTHORITY: Optional[str]
