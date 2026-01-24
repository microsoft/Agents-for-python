# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Optional
import jwt

from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class TokenResponse(AgentsModel):
    """A response that includes a user token.

    :param connection_name: The connection name
    :type connection_name: str
    :param token: The user token
    :type token: str
    :param expiration: Expiration for the token, in ISO 8601 format (e.g.
     "2007-04-05T14:30Z")
    :type expiration: str
    :param channel_id: The channelId of the TokenResponse
    :type channel_id: str
    """

    connection_name: NonEmptyString = None
    token: NonEmptyString = None
    expiration: NonEmptyString = None
    channel_id: NonEmptyString = None

    def __bool__(self):
        return bool(self.token)

    def is_exchangeable(self) -> bool:
        """
        Checks if a token is exchangeable (has api:// audience).

        :param token: The token to check.
        :type token: str
        :return: True if the token is exchangeable, False otherwise.
        """
        try:
            # Decode without verification to check the audience
            payload = jwt.decode(self.token, options={"verify_signature": False})

            idtyp = payload.get("idtyp")
            if idtyp == "user":
                return False

            aud = payload.get("aud")
            app_id = self._get_app_id_from_token_payload(payload)
            return isinstance(aud, str) and app_id in aud
        except Exception:
            return False

    @staticmethod
    def _get_app_id_from_token_payload(token_payload: dict) -> Optional[str]:
        """
        Extracts the appId from the token's claims.

        :return: The appId if found, otherwise None.
        """
        try:
            token_version = token_payload.get("ver", None)
            app_id = None

            if not token_version or token_version == "1.0":
                app_id = token_payload.get("appid", None)
            elif token_version == "2.0":
                app_id = token_payload.get("azp", None)

            return app_id
        except Exception:
            return None
