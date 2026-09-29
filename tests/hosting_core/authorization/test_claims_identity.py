# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.hosting.core.authorization import ClaimsIdentity


class TestClaimsIdentityConstructor:
    def test_default_identity_is_anonymous(self):
        identity = ClaimsIdentity()

        assert identity.claims == {}
        assert identity.authentication_type is None
        assert identity.security_token is None
        assert identity.allow_anonymous is True

    def test_default_claims_are_not_shared(self):
        first = ClaimsIdentity()
        second = ClaimsIdentity()

        first.claims["aud"] = "app-id"

        assert second.claims == {}

    def test_constructor_preserves_values(self):
        claims = {"aud": "app-id"}

        identity = ClaimsIdentity(
            claims=claims,
            authentication_type="Bearer",
            security_token="token",
        )

        assert identity.claims is claims
        assert identity.authentication_type == "Bearer"
        assert identity.security_token == "token"


class TestClaimsIdentityAnonymousAccess:
    @pytest.mark.parametrize(
        ("claims", "authentication_type", "expected"),
        [
            (None, None, True),
            ({}, None, True),
            ({"aud": "app-id"}, None, False),
            ({}, "Anonymous", True),
            ({}, "Bearer", False),
        ],
    )
    def test_allow_anonymous(
        self,
        claims,
        authentication_type,
        expected,
    ):
        identity = ClaimsIdentity(
            claims=claims,
            authentication_type=authentication_type,
        )

        assert identity.allow_anonymous is expected


def test_get_claim_value_returns_matching_claim():
    identity = ClaimsIdentity(claims={"aud": "app-id"})

    assert identity.get_claim_value("aud") == "app-id"
    assert identity.get_claim_value("missing") is None
