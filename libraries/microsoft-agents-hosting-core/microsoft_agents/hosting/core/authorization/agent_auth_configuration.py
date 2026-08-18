# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from typing import Any

from microsoft_agents.activity.config._coercion import coerce_bool

from microsoft_agents.hosting.core.authorization.auth_types import AuthTypes
from microsoft_agents.hosting.core.authorization._entra_issuers import (
    default_connection_issuers,
)

# Env-style configuration keys that ``__init__`` recognizes and binds into
# first-class fields (via the ``kwargs.get("...")`` aliases below). These are
# excluded from ``provider_settings`` so that core config — including sensitive
# values like ``CLIENTSECRET`` — is never duplicated into the provider bag.
_RECOGNIZED_CONFIG_KEYS = frozenset(
    {
        "AUTHTYPE",
        "CLIENTID",
        "AUTHORITY",
        "AUTHORITYENDPOINT",
        "TENANTID",
        "CLIENTSECRET",
        "CERTPFXFILE",
        "CONNECTIONNAME",
        "FEDERATEDCLIENTID",
        "FEDERATEDTOKENFILE",
        "SCOPES",
        "AZUREREGION",
        "REGIONALAUTHORITY",
        "IDPMRESOURCE",
        "ALT_BLUEPRINT_NAME",
        "ALTERNATEBLUEPRINTCONNECTIONNAME",
        "ANONYMOUS_ALLOWED",
        "ISSUERS",
        "VALIDATE_ISSUER",
    }
)


def _normalize_issuers(value: Any) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        values = value.replace(",", " ").split()
    elif isinstance(value, dict):
        values = value.values()
    else:
        values = value
    issuers = [str(item).strip() for item in values if item and str(item).strip()]
    return issuers or None


class AgentAuthConfiguration:
    """
    Configuration for Agent authentication.

    TENANT_ID: The tenant ID for the Azure AD.
    CLIENT_ID: The client ID for the Azure AD application.
    AUTH_TYPE: The type of authentication to use (microsoft_agents.hosting.core.authorization.auth_types.AuthTypes).
    CLIENT_SECRET: The client secret for the Azure AD application (if using client secret authentication).
    CERT_PFX_FILE: The path to the PFX certificate file (if using certificate authentication).
    CONNECTION_NAME: The name of the connection
    FEDERATED_CLIENT_ID: The client ID for federated credentials (if using federated credentials authentication).
    SCOPES: The scopes to request
    AUTHORITY: The authority URL for the Azure AD (if different from the default).
    ALT_BLUEPRINT_ID: An optional alternative blueprint ID used when constructing a connector client.
    AZURE_REGION: The Azure regional token service to use for token acquisition (ESTS-R).
        This feature is currently available to first-party applications only.
    IDPM_RESOURCE: The resource URL for Identity Proxy Manager (IDPM) token acquisition.
        Only meaningful when AUTH_TYPE is AuthTypes.identity_proxy_manager. When not set,
        it defaults to "api://AzureAdTokenExchange/.default".
    ISSUERS: An optional explicit list of accepted token issuers. When not provided,
        a cloud/tenant-scoped default is computed from TENANT_ID and AUTHORITY.
    VALIDATE_ISSUER: Explicit opt-in flag (default False) that enables issuer
        allow-list validation in JwtTokenValidator. Preserved as an opt-in for
        backward compatibility: existing deployments are unaffected unless
        they explicitly enable it. Note: tid-to-issuer binding is always
        enforced by JwtTokenValidator (per issue #626) whenever the verified
        token's issuer is a recognized Entra issuer with a GUID tenant,
        regardless of this flag.
    ANONYMOUS_ALLOWED: Whether anonymous access is allowed (default False).
    FEDERATED_TOKEN_FILE: The path to the federated token file (if using federated credentials authentication).
    """

    TENANT_ID: str | None
    AUTH_TYPE: AuthTypes
    CLIENT_ID: str | None
    CLIENT_SECRET: str | None
    CERT_PFX_FILE: str | None
    CONNECTION_NAME: str | None
    FEDERATED_CLIENT_ID: str | None
    SCOPES: list[str] | None
    AUTHORITY: str | None
    ALT_BLUEPRINT_ID: str | None
    AZURE_REGION: str | None
    IDPM_RESOURCE: str | None
    ANONYMOUS_ALLOWED: bool = False
    VALIDATE_ISSUER: bool = False
    FEDERATED_TOKEN_FILE: str | None

    # Provider-specific settings that aren't first-class fields (e.g. the Entra
    # sidecar's SERVICE_NAME, SIDECAR_BASE_URL). Preserved here as a single dict
    # rather than as dynamic attributes so the extra surface is explicit and
    # discoverable. Custom providers read these via ``provider_settings``.
    provider_settings: dict[str, Any]

    # Multi-connection support: Maintains a map of all configured connections
    # to enable JWT validation across connections. This allows tokens issued
    # for any configured connection to be validated, supporting multi-tenant
    # scenarios where connections share a security boundary.
    #
    # Note: This is an internal implementation detail. External code should
    # not directly access _connections.
    _connections: dict[str, AgentAuthConfiguration]

    def __init__(
        self,
        auth_type: AuthTypes | None = None,
        client_id: str | None = None,
        tenant_id: str | None = None,
        client_secret: str | None = None,
        cert_pfx_file: str | None = None,
        connection_name: str | None = None,
        federated_client_id: str | None = None,
        authority: str | None = None,
        scopes: list[str] | None = None,
        azure_region: str | None = None,
        idpm_resource: str | None = None,
        anonymous_allowed: bool | None = None,
        issuers: list[str] | None = None,
        validate_issuer: bool | None = None,
        federated_token_file: str | None = None,
        **kwargs: Any,
    ):

        self.AUTH_TYPE = auth_type or kwargs.get("AUTHTYPE", AuthTypes.client_secret)
        self.CLIENT_ID = client_id or kwargs.get("CLIENTID", None)
        # .NET binds the authority from the "AuthorityEndpoint" configuration key;
        # accept it as an alias for parity while keeping the existing "AUTHORITY" key.
        self.AUTHORITY = (
            authority
            or kwargs.get("AUTHORITY", None)
            or kwargs.get("AUTHORITYENDPOINT", None)
        )
        self.TENANT_ID = tenant_id or kwargs.get("TENANTID", None)
        self.CLIENT_SECRET = client_secret or kwargs.get("CLIENTSECRET", None)
        self.CERT_PFX_FILE = cert_pfx_file or kwargs.get("CERTPFXFILE", None)
        self.CONNECTION_NAME = connection_name or kwargs.get("CONNECTIONNAME", None)
        self.FEDERATED_CLIENT_ID = federated_client_id or kwargs.get(
            "FEDERATEDCLIENTID", None
        )
        self.FEDERATED_TOKEN_FILE = federated_token_file or kwargs.get(
            "FEDERATEDTOKENFILE", None
        )
        self.SCOPES = scopes or kwargs.get("SCOPES", None)
        # Azure regional token service. Falls back to the legacy "REGIONALAUTHORITY"
        # configuration key when "AZUREREGION" is not provided.
        self.AZURE_REGION = (
            azure_region
            or kwargs.get("AZUREREGION", None)
            or kwargs.get("REGIONALAUTHORITY", None)
        )
        # Resource URL for Identity Proxy Manager (IDPM) token acquisition.
        # Only meaningful when AUTH_TYPE is AuthTypes.identity_proxy_manager.
        self.IDPM_RESOURCE = idpm_resource or kwargs.get("IDPMRESOURCE", None)
        # .NET names this "AlternateBlueprintConnectionName"; accept that key as an
        # alias for the existing "ALT_BLUEPRINT_NAME" without removing the latter.
        self.ALT_BLUEPRINT_ID = kwargs.get("ALT_BLUEPRINT_NAME", None) or kwargs.get(
            "ALTERNATEBLUEPRINTCONNECTIONNAME", None
        )
        # Env values arrive as strings, so coerce explicitly: ``bool("false")``
        # would be ``True`` and silently enable anonymous auth when configured
        # off. Coercion is fail-safe (unrecognized -> False). An explicitly
        # provided ``anonymous_allowed`` (including ``False``) takes precedence
        # over the ``ANONYMOUS_ALLOWED`` kwarg; ``None`` means "not provided".
        self.ANONYMOUS_ALLOWED = coerce_bool(
            (
                anonymous_allowed
                if anonymous_allowed is not None
                else kwargs.get("ANONYMOUS_ALLOWED", False)
            ),
            default=False,
            name="ANONYMOUS_ALLOWED",
        )

        # Explicit, optional issuer allow-list. When not provided, ISSUERS falls
        # back to a cloud/tenant-scoped default (see the ISSUERS property below).
        self._configured_issuers = _normalize_issuers(
            issuers if issuers is not None else kwargs.get("ISSUERS", None)
        )
        # Explicit opt-in for issuer allow-list validation in JwtTokenValidator.
        # Off by default so existing deployments are unaffected unless they
        # explicitly enable it. Note: tid-to-issuer binding is always enforced
        # by JwtTokenValidator regardless of this flag (see VALIDATE_ISSUER
        # docstring above). Same fail-safe string coercion as ANONYMOUS_ALLOWED
        # applies here.
        self.VALIDATE_ISSUER = coerce_bool(
            (
                validate_issuer
                if validate_issuer is not None
                else kwargs.get("VALIDATE_ISSUER", False)
            ),
            default=False,
            name="VALIDATE_ISSUER",
        )

        # Preserve genuinely provider-specific settings that aren't first-class
        # fields (e.g. the Entra sidecar's SERVICE_NAME, SIDECAR_BASE_URL) so
        # custom providers can read them via ``provider_settings``. Recognized
        # core alias keys (bound into first-class fields above) are excluded so
        # core config — including ``CLIENTSECRET`` — is never copied into this bag.
        self.provider_settings = {
            key: value
            for key, value in kwargs.items()
            if not hasattr(self, key) and key not in _RECOGNIZED_CONFIG_KEYS
        }

        # JWT-patch: always at least include self for backward compat
        self._connections = {str(self.CONNECTION_NAME): self}

        self._validate()

    def _validate(self) -> None:
        """
        Validates the configuration. Raises ValueError if any required fields are missing or invalid.
        """
        if self.AUTH_TYPE == AuthTypes.certificate and not self.CERT_PFX_FILE:
            raise ValueError(
                "CERT_PFX_FILE is required for certificate authentication."
            )
        if (
            self.AUTH_TYPE == AuthTypes.federated_credentials
            and not self.FEDERATED_CLIENT_ID
        ):
            raise ValueError(
                "FEDERATED_CLIENT_ID is required for federated_credentials authentication."
            )
        if (
            self.AUTH_TYPE == AuthTypes.workload_identity
            and not self.FEDERATED_TOKEN_FILE
        ):
            raise ValueError(
                "FEDERATED_TOKEN_FILE is required for workload_identity authentication."
            )

    @property
    def ISSUERS(self) -> list[str]:
        """
        Gets the list of accepted issuers: the explicitly configured list when
        provided, otherwise a cloud/tenant-scoped default derived from the
        effective tenant (the tenant segment embedded in AUTHORITY's path when
        present, e.g. ``https://login.microsoftonline.com/common`` or
        ``.../{tenant-guid}``, otherwise TENANT_ID) and AUTHORITY (US
        Government authorities yield US Government issuer defaults).
        """
        if self._configured_issuers:
            return list(self._configured_issuers)
        return default_connection_issuers(self.TENANT_ID, self.AUTHORITY)

    # .NET-aligned, read-only property aliases. These mirror the property names on
    # the .NET ``ConnectionSettingsBase`` so provider code and cross-language readers
    # can use a consistent snake_case surface. They are thin views over the existing
    # UPPER_SNAKE attributes and do not change how configuration is stored.
    @property
    def client_id(self) -> str | None:
        """Alias for :attr:`CLIENT_ID` (.NET ``ClientId``)."""
        return self.CLIENT_ID

    @property
    def authority(self) -> str | None:
        """Alias for :attr:`AUTHORITY` (.NET ``AuthorityEndpoint``)."""
        return self.AUTHORITY

    @property
    def tenant_id(self) -> str | None:
        """Alias for :attr:`TENANT_ID` (.NET ``TenantId``)."""
        return self.TENANT_ID

    @property
    def scopes(self) -> list[str] | None:
        """Alias for :attr:`SCOPES` (.NET ``Scopes``)."""
        return self.SCOPES

    @property
    def alternate_blueprint_connection_name(self) -> str | None:
        """Alias for :attr:`ALT_BLUEPRINT_ID` (.NET ``AlternateBlueprintConnectionName``)."""
        return self.ALT_BLUEPRINT_ID

    def _jwt_patch_is_valid_aud(self, aud: Any) -> bool:
        """
        JWT-patch: Checks if the given audience is valid for any of the
        connections. A non-string ``aud`` (e.g. the JWT-spec-permitted array
        form, or a malformed numeric/object claim) is never valid: only a
        single string audience is accepted, so this returns ``False`` rather
        than raising, letting the caller reject it as an invalid audience.
        """
        if not isinstance(aud, str):
            return False
        for conn in self._connections.values():
            if not conn.CLIENT_ID:
                continue
            if aud.lower() == conn.CLIENT_ID.lower():
                return True
        return False

    def _jwt_patch_find_connection(self, aud: Any) -> "AgentAuthConfiguration | None":
        """
        JWT-patch: Finds the configured connection whose CLIENT_ID matches the
        given audience (case-insensitive), so JwtTokenValidator can route JWKS
        lookup and issuer validation to the correct connection's tenant/authority
        in multi-connection setups. Returns None when no connection matches,
        or when ``aud`` is not a string (e.g. an unverified array-form or
        malformed claim) -- callers fall back to default routing rather than
        failing.
        """
        if not aud or not isinstance(aud, str):
            return None
        for conn in self._connections.values():
            if conn.CLIENT_ID and aud.lower() == conn.CLIENT_ID.lower():
                return conn
        return None
