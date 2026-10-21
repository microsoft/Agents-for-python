# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from dataclasses import dataclass

from microsoft_agents.activity.config import (
    Configuration,
    _name_variants
)
from microsoft_agents.hosting.core.authorization import AuthTypes
from microsoft_agents.hosting.core.authorization.config import _ConnectionSettingsBase

@dataclass(frozen=True)
class MsalConnectionSettings(_ConnectionSettingsBase):
    """
    Connection settings for MSAL authentication.
    """

    auth_type: str = AuthTypes.client_secret
    client_secret: str | None = None
    cert_pfx_file: str | None = None
    send_x5c: bool = False
    connection_name: str | None = None
    federated_client_id: str | None = None
    federated_token_file: str | None = None
    idpm_resource: str | None = None
    azure_region: str | None = None

    def __post_init__(self) -> None:
        self._validate()

    @classmethod
    def _get_init_kwargs(cls, config: Configuration) -> dict:
        base = super()._get_init_kwargs(config)
        base.update({
            "auth_type": config.get_strn("auth_type", AuthTypes.client_secret),
            "client_secret": config.get_strn("client_secret"),
            "cert_pfx_file": config.get_strn("cert_pfx_file"),
            "send_x5c": config.get_booln("send_x5c"),
            "connection_name": config.get_strn("connection_name"),
            "federated_client_id": config.get_strn("federated_client_id"),
            "federated_token_file": config.get_strn("federated_token_file"),
            "idpm_resource": config.get_strn("idpm_resource"),
            "azure_region": config.get_strn(*_name_variants("azure_region", "regional_authority"))
        })
        return base

    def _validate(self) -> None:
        """
        Validates the configuration. Raises ValueError if any required fields are missing or invalid.
        """
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