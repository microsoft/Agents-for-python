# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass, field

from microsoft_agents.activity.config import Configuration, xpath
from microsoft_agents.hosting.core import (
    AgentAuthConfiguration,
    AuthTypes,
    ConnectionSettingsBase,
)


@dataclass(frozen=True)
class MsalConnectionSettings(ConnectionSettingsBase):
    """MSAL-specific settings, bound independently of inbound JWT policy."""

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
                    xpath("auth_type"), default=AuthTypes.client_secret
                ),
                "client_secret": config.get_strn(xpath("client_secret")),
                "cert_pfx_file": config.get_strn(xpath("cert_pfx_file")),
                "send_x5c": config.get_bool(xpath("send_x5c"), default=False),
                "connection_name": config.get_strn(xpath("connection_name")),
                "federated_client_id": config.get_strn(xpath("federated_client_id")),
                "federated_token_file": config.get_strn(xpath("federated_token_file")),
                "idpm_resource": config.get_strn(xpath("idpm_resource")),
                "azure_region": config.get_strn(
                    xpath("azure_region"), xpath("regional_authority")
                ),
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
