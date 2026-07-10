# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import jwt

from datetime import datetime, timedelta, timezone

from microsoft_agents.authentication.entra_auth_sidecar._token_expiry import (
    SidecarTokenExpiry,
    FALLBACK_LIFETIME,
)


class TestSidecarTokenExpiry:
    def test_reads_jwt_exp(self):
        exp = datetime.now(timezone.utc) + timedelta(hours=1)
        token = jwt.encode({"exp": int(exp.timestamp())}, "x" * 32, algorithm="HS256")
        resolved = SidecarTokenExpiry.resolve(token)
        assert abs((resolved - exp).total_seconds()) < 2

    def test_opaque_token_uses_fallback(self):
        before = datetime.now(timezone.utc)
        resolved = SidecarTokenExpiry.resolve("opaque-token")
        expected = before + FALLBACK_LIFETIME
        assert abs((resolved - expected).total_seconds()) < 5

    def test_empty_token_uses_fallback(self):
        before = datetime.now(timezone.utc)
        resolved = SidecarTokenExpiry.resolve("")
        expected = before + FALLBACK_LIFETIME
        assert abs((resolved - expected).total_seconds()) < 5

    def test_jwt_without_exp_uses_fallback(self):
        token = jwt.encode({"sub": "x"}, "x" * 32, algorithm="HS256")
        before = datetime.now(timezone.utc)
        resolved = SidecarTokenExpiry.resolve(token)
        expected = before + FALLBACK_LIFETIME
        assert abs((resolved - expected).total_seconds()) < 5

    def test_exp_zero_is_treated_as_expired_not_fallback(self):
        # ``exp: 0`` is a real (epoch) expiry - it must resolve to the epoch (an
        # already-expired token), never be mistaken for "no exp" and granted a
        # fresh fallback lease.
        token = jwt.encode({"exp": 0}, "x" * 32, algorithm="HS256")
        resolved = SidecarTokenExpiry.resolve(token)
        assert resolved == datetime.fromtimestamp(0, tz=timezone.utc)

    def test_out_of_range_exp_uses_fallback(self):
        # A wildly out-of-range ``exp`` must not crash token acquisition.
        token = jwt.encode({"exp": 10**30}, "x" * 32, algorithm="HS256")
        before = datetime.now(timezone.utc)
        resolved = SidecarTokenExpiry.resolve(token)
        expected = before + FALLBACK_LIFETIME
        assert abs((resolved - expected).total_seconds()) < 5
