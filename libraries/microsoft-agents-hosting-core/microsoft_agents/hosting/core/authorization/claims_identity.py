# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from typing import Optional

from .authentication_constants import AuthenticationConstants


class ClaimsIdentity:
    def __init__(
        self,
        claims: dict[str, str],
        is_authenticated: bool,
        authentication_type: str = None,
    ):
        self.claims = claims
        self.is_authenticated = is_authenticated
        self.authentication_type = authentication_type

    def get_claim_value(self, claim_type: str) -> Optional[str]:
        return self.claims.get(claim_type)

    def get_app_id(self) -> Optional[str]:
        """
        Gets the AppId from the current ClaimsIdentity.

        :return: The AppId if found, otherwise None.
        """

        return self.claims.get(
            AuthenticationConstants.AUDIENCE_CLAIM, None
        ) or self.claims.get(AuthenticationConstants.APP_ID_CLAIM, None)

    def get_outgoing_app_id(self) -> Optional[str]:
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
        return f"app://{self.get_outgoing_app_id()}"
