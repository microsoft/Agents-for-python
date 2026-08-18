# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Shared helpers for building signed RS256 JWTs in tests.

Generates an in-memory RSA keypair per call so tests can sign tokens with the
private key and have JwtTokenValidator "fetch" the matching public key via a
monkeypatched JWKS client, without any real network access.
"""

from __future__ import annotations

import json
import time
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey


def generate_rsa_keypair() -> tuple[RSAPrivateKey, RSAPublicKey]:
    """Generates a fresh RSA keypair for signing/verifying test tokens."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key, private_key.public_key()


def make_signed_jwt(
    private_key: RSAPrivateKey,
    claims: dict[str, Any],
    kid: str = "test-kid",
    expires_in: float = 3600.0,
) -> str:
    """Encodes ``claims`` as an RS256 JWT signed with ``private_key``.

    ``exp`` is filled in from ``expires_in`` (seconds from now) unless the
    caller already supplied one.
    """
    payload = dict(claims)
    payload.setdefault("exp", int(time.time() + expires_in))
    return jwt.encode(payload, private_key, algorithm="RS256", headers={"kid": kid})


def make_signed_jwt_with_raw_claims(
    private_key: RSAPrivateKey,
    claims: dict[str, Any],
    kid: str = "test-kid",
    expires_in: float = 3600.0,
) -> str:
    """Like :func:`make_signed_jwt`, but signs via the lower-level JWS API so
    claim values are serialized as-is (no PyJWT claims-shape validation).

    PyJWT's ``jwt.encode`` (the higher-level JWT API) rejects a non-string
    ``iss`` at encode time (``TypeError: Issuer (iss) must be a string.``),
    which makes it impossible to build regression tokens for malformed
    ``iss`` shapes (list/dict) via ``make_signed_jwt``. This helper drops
    down to ``jwt.api_jws`` (JWS: a signed, opaque payload) to produce a
    structurally valid, signed token carrying any JSON-serializable claims,
    exactly mirroring what a non-conformant or malicious token producer
    could hand to a real deployment.
    """
    payload = dict(claims)
    payload.setdefault("exp", int(time.time() + expires_in))
    payload_bytes = json.dumps(payload).encode("utf-8")
    return jwt.api_jws.encode(
        payload_bytes, private_key, algorithm="RS256", headers={"kid": kid}
    )
