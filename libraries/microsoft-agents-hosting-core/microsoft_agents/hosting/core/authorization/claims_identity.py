# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import warnings

from typing import Any

from .authentication_constants import AuthenticationConstants


class ClaimsIdentity:
    """Represents an identity with associated claims and authentication information.

    For context, this class merges the functionality of ClaimsIdentity and AgentClaims from .NET
    """

    claims: dict[str, Any]
    authentication_type: str | None
    security_token: str | None  # deprecated, will be removed in future versions

    def __init__(
        self,
        claims: dict[str, Any] | None = None,
        is_authenticated: bool | None = None,
        authentication_type: str | None = None,
        security_token: str | None = None,
    ):
        """Creates a new instance of the ClaimsIdentity class.

        :param claims: A dictionary of claims associated with the identity.
        :param is_authenticated: A boolean indicating whether the identity is authenticated. (Deprecated)
        :param authentication_type: A string representing the type of authentication used.
        :param security_token: The security token associated with the identity.
        """
        if claims is None:
            claims = {}
        self.claims = claims
        if is_authenticated is not None:
            warnings.warn(
                "The 'is_authenticated' parameter is deprecated and will be removed in future versions.",
                DeprecationWarning,
                stacklevel=2,
            )

        self.authentication_type = authentication_type
        self.security_token = security_token
        self._is_authenticated = is_authenticated

    def get_claim_value(self, claim_type: str) -> Any:
        """Gets the value of a specific claim type from the claims dictionary.

        :param claim_type: The type of claim to retrieve.
        :return: The value of the claim if found, otherwise None.
        """
        return self.claims.get(claim_type)

    @property
    def allow_anonymous(self) -> bool:
        """Returns True if the identity allows anonymous access, otherwise False."""
        return (
            not self.authentication_type
            or self.authentication_type.lower() == "anonymous"
        ) and not self.claims

    @property
    def is_authenticated(self) -> bool:
        """Returns True if the identity is authenticated, otherwise False."""
        warnings.warn(
            "The 'is_authenticated' property is deprecated and will be removed in future versions.",
            DeprecationWarning,
            stacklevel=2,
        )
        return bool(self.claims)

    @is_authenticated.setter
    def is_authenticated(self, value: bool) -> None:
        """(Deprecated). This is now a no-op."""
        warnings.warn(
            "The 'is_authenticated' property is deprecated and will be removed in future versions.",
            DeprecationWarning,
            stacklevel=2,
        )

    def get_app_id(self) -> str | None:
        """
        Gets the AppId from the current ClaimsIdentity.

        :return: The AppId if found, otherwise None.
        """

        return self.claims.get(
            AuthenticationConstants.AUDIENCE_CLAIM, None
        ) or self.claims.get(AuthenticationConstants.APP_ID_CLAIM, None)

    def get_outgoing_app_id(self) -> str | None:
        """
        Gets the outgoing AppId from current claims.

        :return: The value of the appId claim if found, otherwise None.
        """

        token_version = self.claims.get(AuthenticationConstants.VERSION_CLAIM, None)
        app_id = None

        if not token_version or token_version == "1.0":
            app_id = self.claims.get(AuthenticationConstants.APP_ID_CLAIM, None)
        elif token_version == "2.0":
            app_id = self.claims.get(AuthenticationConstants.AUTHORIZED_PARTY, None)

        return app_id

    def is_agent_claim(self) -> bool:
        """
        Checks if the current claims represents an agent claim (not coming from ABS/SMBA).

        :return: True if the list of claims is an agent claim, otherwise False.
        """

        version = self.claims.get(AuthenticationConstants.VERSION_CLAIM, None)
        if not version:
            return False

        audience = self.claims.get(AuthenticationConstants.AUDIENCE_CLAIM, None)
        if (
            not audience
            or audience.lower()
            == AuthenticationConstants.AGENTS_SDK_TOKEN_ISSUER.lower()
        ):
            return False

        app_id = self.get_outgoing_app_id()
        if not app_id:
            return False

        return app_id != audience

    def get_token_audience(self) -> str:
        """
        Gets the token audience from current claims.

        :return: The token audience.
        """
        return (
            f"app://{self.get_outgoing_app_id()}"
            if self.is_agent_claim()
            else AuthenticationConstants.AGENTS_SDK_SCOPE
        )

    def get_token_scope(self) -> list[str]:
        """
        Gets the token scope from current claims.

        :return: The token scope.
        """
        return [
            (
                f"{self.get_outgoing_app_id()}/.default"
                if self.is_agent_claim()
                else AuthenticationConstants.AGENTS_SDK_SCOPE + "/.default"
            )
        ]
