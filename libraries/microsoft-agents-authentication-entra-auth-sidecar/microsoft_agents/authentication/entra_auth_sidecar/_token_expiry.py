# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt

# Conservative lifetime applied when the token is opaque or carries no readable JWT ``exp``.
FALLBACK_LIFETIME = timedelta(minutes=5)


class SidecarTokenExpiry:
    """Helpers for interpreting the lifetime of sidecar-issued tokens."""

    @staticmethod
    def resolve(token: str) -> datetime:
        """
        Resolve the absolute (UTC) expiry of a sidecar-issued token.

        Prefers the token's own JWT ``exp`` claim; falls back to
        :data:`FALLBACK_LIFETIME` from now when the token is opaque or carries no
        readable expiry.

        :param token: The raw access token returned by the sidecar.
        :return: The absolute UTC expiry of the token.
        """
        now = datetime.now(timezone.utc)
        if token:
            try:
                claims = jwt.decode(token, options={"verify_signature": False})
                exp = claims.get("exp")
                if exp is not None:
                    return datetime.fromtimestamp(int(exp), tz=timezone.utc)
            except (jwt.PyJWTError, ValueError, TypeError, OverflowError, OSError):
                # Opaque/non-JWT token, or an out-of-range/invalid ``exp`` - fall
                # back below.
                pass

        return now + FALLBACK_LIFETIME
