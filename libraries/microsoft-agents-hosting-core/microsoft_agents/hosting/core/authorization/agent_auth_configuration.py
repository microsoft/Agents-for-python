# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Optional

from microsoft_agents.hosting.core.authorization.auth_types import AuthTypes


class AgentAuthConfiguration:
    """
    Configuration for Agent authentication.

    TENANT_ID: The tenant ID for the Azure AD.
    CLIENT_ID: The client ID for the Azure AD application.
    AUTH_TYPE: The type of authentication to use (microsoft_agents.hosting.core.authorization.auth_types.AuthTypes).
    CLIENT_SECRET: The client secret for the Azure AD application (if using client secret authentication).
    CERT_PEM_FILE: The path to the PEM file for certificate authentication (if using certificate authentication).
    CERT_KEY_FILE: The path to the key file for certificate authentication (if using certificate authentication).
    CONNECTION_NAME: The name of the connection
    SCOPES: The scopes to request
    AUTHORITY: The authority URL for the Azure AD (if different from the default).f
    ALT_BLUEPRINT_ID: An optional alternative blueprint ID used when constructing a connector client.
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
    ALT_BLUEPRINT_ID: Optional[str]

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
        self.ALT_BLUEPRINT_ID = kwargs.get("ALT_BLUEPRINT_NAME", None)

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
