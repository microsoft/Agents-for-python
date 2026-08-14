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
        assert identity.is_authenticated is False

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
        assert identity.is_authenticated is True

    def test_is_authenticated_parameter_is_deprecated(self):
        with pytest.warns(DeprecationWarning, match="is_authenticated"):
            identity = ClaimsIdentity(is_authenticated=True)

        assert identity.allow_anonymous is True


class TestClaimsIdentityAnonymousAccess:
    @pytest.mark.parametrize(
        ("claims", "is_authenticated", "authentication_type", "expected"),
        [
            (None, None, None, True),
            ({}, False, None, True),
            ({}, True, None, True),
            ({"aud": "app-id"}, None, None, False),
            ({}, None, "Bearer", False),
        ],
    )
    def test_allow_anonymous(
        self,
        claims,
        is_authenticated,
        authentication_type,
        expected,
    ):
        identity = ClaimsIdentity(
            claims=claims,
            is_authenticated=is_authenticated,
            authentication_type=authentication_type,
        )

        assert identity.allow_anonymous is expected

    @pytest.mark.parametrize("is_authenticated", [False, True])
    def test_deprecated_is_authenticated_does_not_affect_allow_anonymous(
        self, is_authenticated
    ):
        identity = ClaimsIdentity(
            claims={},
            is_authenticated=is_authenticated,
        )

        assert identity.allow_anonymous is True


class TestClaimsIdentityAuthenticationCompatibility:
    @pytest.mark.parametrize(
        ("claims", "expected"),
        [
            ({}, False),
            ({"aud": "app-id"}, True),
        ],
    )
    def test_is_authenticated_is_derived_from_claims(self, claims, expected):
        identity = ClaimsIdentity(claims=claims)

        assert identity.is_authenticated is expected

    def test_is_authenticated_setter_is_deprecated_no_op(self):
        identity = ClaimsIdentity(claims={"aud": "app-id"})

        with pytest.warns(DeprecationWarning, match="is_authenticated"):
            identity.is_authenticated = False

        with pytest.warns(DeprecationWarning, match="is_authenticated"):
            assert identity.is_authenticated is True


def test_get_claim_value_returns_matching_claim():
    identity = ClaimsIdentity(claims={"aud": "app-id"})

    assert identity.get_claim_value("aud") == "app-id"
    assert identity.get_claim_value("missing") is None
