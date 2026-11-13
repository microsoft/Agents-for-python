# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass, field

from microsoft_agents.activity.config import Configuration, _legpath as legpath
from microsoft_agents.hosting.core import (
    AgentAuthConfiguration,
    AuthTypes,
    ConnectionSettingsBase,
)


@dataclass(frozen=True)
class MsalConnectionSettings(ConnectionSettingsBase):
    """Credentials and options MSAL uses to request access tokens.

    Create this object with keyword arguments, or call ``from_config`` with a
    dictionary containing one connection's settings::

        >>> from microsoft_agents.authentication.msal import MsalConnectionSettings
        >>> settings = MsalConnectionSettings.from_config({
        ...     "CLIENT_ID": "your-client-id",
        ...     "TENANT_ID": "your-tenant-id",
        ...     "CLIENT_SECRET": "<your-client-secret>",
        ...     "SCOPES": "https://graph.microsoft.com/.default",
        ... })
        >>> settings.client_id
        'your-client-id'
        >>> settings.scopes
        ['https://graph.microsoft.com/.default']

    ``CLIENT_ID``, ``ClientId``, and ``client_id`` all populate ``client_id``.
    You can also pass a connection entry containing a ``settings`` dictionary.
    Do not pass the entire application configuration: select the connection
    first, or let ``MsalConnectionManager`` do that for you.

    The default authentication type is ``AuthTypes.client_secret``; provide
    ``client_secret`` when using that type to acquire tokens. Other types have
    their own required fields: certificate authentication requires
    ``cert_pfx_file``, federated credentials require ``federated_client_id``,
    and workload identity requires ``federated_token_file``.
    These three requirements are checked when the settings object is created.

    ``regional_authority`` can be used if ``azure_region`` is not supplied.
    Unrecognized settings are available through ``extras``.
    """

    auth_type: str = AuthTypes.client_secret
    client_secret: str | None = field(default=None, repr=False)
    cert_pfx_file: str | None = None
    send_x5c: bool = False
    connection_name: str | None = None
    federated_client_id: str | None = None
    federated_token_file: str | None = None
    idpm_resource: str | None = None
    azure_region: str | None = None

    def __post_init__(self):
        if self.auth_type == AuthTypes.certificate and not self.cert_pfx_file:
            raise ValueError(
                "CERT_PFX_FILE is required for certificate authentication."
            )
        if (
            self.auth_type == AuthTypes.federated_credentials
            and not self.federated_client_id
        ):
            raise ValueError(
                "FEDERATED_CLIENT_ID is required for federated_credentials authentication."
            )
        if (
            self.auth_type == AuthTypes.workload_identity
            and not self.federated_token_file
        ):
            raise ValueError(
                "FEDERATED_TOKEN_FILE is required for workload_identity authentication."
            )

    @classmethod
    def _get_init_kwargs(cls, config: Configuration) -> dict:
        base = super()._get_init_kwargs(config)
        base.update(
            {
                "auth_type": config.get_str(
                    legpath("auth_type"), default=AuthTypes.client_secret
                ),
                "client_secret": config.get_strn(legpath("client_secret")),
                "cert_pfx_file": config.get_strn(legpath("cert_pfx_file")),
                "send_x5c": config.get_bool(legpath("send_x5c"), default=False),
                "connection_name": config.get_strn(legpath("connection_name")),
                "federated_client_id": config.get_strn(legpath("federated_client_id")),
                "federated_token_file": config.get_strn(
                    legpath("federated_token_file")
                ),
                "idpm_resource": config.get_strn(legpath("idpm_resource")),
                "azure_region": config.get_strn(legpath("azure_region"))
                or config.get_strn(legpath("regional_authority")),
            }
        )
        return base

    def _to_agent_auth_config(self) -> AgentAuthConfiguration:
        fields = dict(
            auth_type=self.auth_type,
            client_id=self.client_id,
            tenant_id=self.tenant_id,
            authority=self.authority,
            client_secret=self.client_secret,
            cert_pfx_file=self.cert_pfx_file,
            send_x5c=self.send_x5c,
            connection_name=self.connection_name,
            federated_client_id=self.federated_client_id,
            federated_token_file=self.federated_token_file,
            ALT_BLUEPRINT_NAME=self.alternate_blueprint_connection_name,
            idpm_resource=self.idpm_resource,
            azure_region=self.azure_region,
            scopes=self.scopes,
        )
        return AgentAuthConfiguration(**{**self.extras, **fields})
