# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import uuid

import jwt as pyjwt
import pytest

from microsoft_agents.hosting.core import AgentAuthConfiguration
from microsoft_agents.hosting.core.authorization.jwt.jwt_token_validator import (
    JwtTokenValidator,
)

from tests._common.jwt_test_utils import (
    generate_rsa_keypair,
    make_signed_jwt,
    make_signed_jwt_with_raw_claims,
)


def _patch_signing_key(monkeypatch, validator, public_key, captured_uris=None):
    async def fake_get_signing_key(jwks_uri, header):
        if captured_uris is not None:
            captured_uris.append(jwks_uri)
        return public_key

    # Only mocked member: the JWKS client manager's network call.
    monkeypatch.setattr(
        validator._jwk_client_manager, "get_signing_key", fake_get_signing_key
    )


class TestJwtTokenValidatorAudienceAndSignature:
    @pytest.mark.asyncio
    async def test_validate_token_success_returns_authenticated_claims(
        self, monkeypatch
    ):
        private_key, public_key = generate_rsa_keypair()
        config = AgentAuthConfiguration(client_id="client-1", tenant_id="tenant-1")
        validator = JwtTokenValidator(config)
        _patch_signing_key(monkeypatch, validator, public_key)

        token = make_signed_jwt(private_key, {"aud": "client-1"})
        identity = await validator.validate_token(token)

        assert identity.is_authenticated is True
        assert identity.claims["aud"] == "client-1"

    @pytest.mark.asyncio
    async def test_validate_token_invalid_audience_rejected(self, monkeypatch):
        private_key, public_key = generate_rsa_keypair()
        config = AgentAuthConfiguration(client_id="client-1", tenant_id="tenant-1")
        validator = JwtTokenValidator(config)
        _patch_signing_key(monkeypatch, validator, public_key)

        token = make_signed_jwt(private_key, {"aud": "someone-else"})

        with pytest.raises(ValueError, match="Invalid audience"):
            await validator.validate_token(token)

    @pytest.mark.asyncio
    async def test_validate_token_bad_signature_rejected(self, monkeypatch):
        _, public_key = generate_rsa_keypair()
        wrong_private_key, _ = generate_rsa_keypair()
        config = AgentAuthConfiguration(client_id="client-1", tenant_id="tenant-1")
        validator = JwtTokenValidator(config)
        _patch_signing_key(monkeypatch, validator, public_key)

        # Signed with a different private key than the one whose public key
        # the (mocked) JWKS lookup returns.
        token = make_signed_jwt(wrong_private_key, {"aud": "client-1"})

        with pytest.raises(pyjwt.PyJWTError):
            await validator.validate_token(token)

    @pytest.mark.asyncio
    async def test_validate_token_expired_rejected(self, monkeypatch):
        private_key, public_key = generate_rsa_keypair()
        config = AgentAuthConfiguration(client_id="client-1", tenant_id="tenant-1")
        validator = JwtTokenValidator(config)
        _patch_signing_key(monkeypatch, validator, public_key)

        # Leeway is 300s, so put the expiry well beyond that.
        token = make_signed_jwt(private_key, {"aud": "client-1"}, expires_in=-3600.0)

        with pytest.raises(pyjwt.ExpiredSignatureError):
            await validator.validate_token(token)


class TestJwtTokenValidatorMalformedClaimTypes:
    """Regression tests for non-string ``aud``/``iss`` claims (e.g. the
    JWT-spec-permitted array form, or malformed numeric/object claims), which
    must never raise AttributeError/TypeError -- only the well-defined
    ValueError rejections (or, where a check is skipped, successful
    authentication) -- so middleware never leaks an unhandled 500.
    """

    @pytest.mark.asyncio
    async def test_array_audience_rejected_as_invalid_audience(self, monkeypatch):
        private_key, public_key = generate_rsa_keypair()
        config = AgentAuthConfiguration(client_id="client-1", tenant_id="tenant-1")
        validator = JwtTokenValidator(config)
        _patch_signing_key(monkeypatch, validator, public_key)

        # RFC 7519 permits `aud` as an array of strings; this codebase only
        # accepts a single string audience, so it must be cleanly rejected
        # rather than crashing on `.lower()` (AttributeError on a list).
        token = make_signed_jwt(private_key, {"aud": ["client-1", "someone-else"]})

        with pytest.raises(ValueError, match="Invalid audience"):
            await validator.validate_token(token)

    @pytest.mark.asyncio
    async def test_numeric_audience_rejected_as_invalid_audience(self, monkeypatch):
        private_key, public_key = generate_rsa_keypair()
        config = AgentAuthConfiguration(client_id="client-1", tenant_id="tenant-1")
        validator = JwtTokenValidator(config)
        _patch_signing_key(monkeypatch, validator, public_key)

        token = make_signed_jwt(private_key, {"aud": 12345})

        with pytest.raises(ValueError, match="Invalid audience"):
            await validator.validate_token(token)

    @pytest.mark.asyncio
    async def test_list_issuer_does_not_crash_routing_or_tenant_binding(
        self, monkeypatch
    ):
        # A list `iss` is unhashable and must not be used as a dict key for
        # the Bot Framework JWKS lookup (routing) nor crash tenant binding.
        # With VALIDATE_ISSUER left at its default (False), tenant binding is
        # skipped for a non-string issuer, so the token is otherwise accepted.
        private_key, public_key = generate_rsa_keypair()
        config = AgentAuthConfiguration(client_id="client-1", tenant_id="tenant-1")
        validator = JwtTokenValidator(config)
        captured_uris = []
        _patch_signing_key(monkeypatch, validator, public_key, captured_uris)

        token = make_signed_jwt_with_raw_claims(
            private_key,
            {
                "aud": "client-1",
                "iss": ["https://a.example.com", "https://b.example.com"],
            },
        )

        identity = await validator.validate_token(token)
        assert identity.is_authenticated is True
        # Falls through to default (non-Bot-Framework) routing.
        assert captured_uris == [
            "https://login.microsoftonline.com/tenant-1/discovery/v2.0/keys"
        ]

    @pytest.mark.asyncio
    async def test_dict_issuer_does_not_crash_routing_or_tenant_binding(
        self, monkeypatch
    ):
        # A dict `iss` is unhashable, same concern as the list case above.
        private_key, public_key = generate_rsa_keypair()
        config = AgentAuthConfiguration(client_id="client-1", tenant_id="tenant-1")
        validator = JwtTokenValidator(config)
        captured_uris = []
        _patch_signing_key(monkeypatch, validator, public_key, captured_uris)

        token = make_signed_jwt_with_raw_claims(
            private_key,
            {"aud": "client-1", "iss": {"unexpected": "object"}},
        )

        identity = await validator.validate_token(token)
        assert identity.is_authenticated is True
        assert captured_uris == [
            "https://login.microsoftonline.com/tenant-1/discovery/v2.0/keys"
        ]

    @pytest.mark.asyncio
    async def test_list_issuer_rejected_as_invalid_issuer_when_validate_issuer_enabled(
        self, monkeypatch
    ):
        # With VALIDATE_ISSUER opted in, a non-string issuer cannot match the
        # (string) allow-list or the multi-tenant canonical-issuer check, and
        # must be cleanly rejected rather than crash.
        private_key, public_key = generate_rsa_keypair()
        config = AgentAuthConfiguration(
            client_id="client-1", tenant_id="tenant-1", validate_issuer=True
        )
        validator = JwtTokenValidator(config)
        _patch_signing_key(monkeypatch, validator, public_key)

        token = make_signed_jwt_with_raw_claims(
            private_key,
            {"aud": "client-1", "iss": ["https://a.example.com"]},
        )

        with pytest.raises(ValueError, match="Invalid issuer"):
            await validator.validate_token(token)

    @pytest.mark.asyncio
    async def test_non_string_tid_skips_tenant_binding(self, monkeypatch):
        private_key, public_key = generate_rsa_keypair()
        tenant_id = str(uuid.uuid4())
        config = AgentAuthConfiguration(client_id="client-1", tenant_id=tenant_id)
        validator = JwtTokenValidator(config)
        _patch_signing_key(monkeypatch, validator, public_key)

        token = make_signed_jwt_with_raw_claims(
            private_key,
            {
                "aud": "client-1",
                "iss": f"https://login.microsoftonline.com/{tenant_id}/v2.0",
                "tid": ["malformed"],
            },
        )

        identity = await validator.validate_token(token)
        assert identity.is_authenticated is True


class TestJwtTokenValidatorIssuerOptIn:
    @pytest.mark.asyncio
    async def test_tenant_binding_enforced_even_when_issuer_validation_disabled(
        self, monkeypatch
    ):
        # Issue #626: tid-to-issuer binding is always enforced (it is not
        # gated by VALIDATE_ISSUER); only the issuer allow-list check is
        # opt-in. A matching-audience token whose recognized Entra `iss`
        # carries a GUID tenant that does not match its own `tid` must be
        # rejected even with VALIDATE_ISSUER left at its default (False).
        private_key, public_key = generate_rsa_keypair()
        config = AgentAuthConfiguration(client_id="client-1", tenant_id="tenant-1")
        assert config.VALIDATE_ISSUER is False
        validator = JwtTokenValidator(config)
        _patch_signing_key(monkeypatch, validator, public_key)

        other_tenant = str(uuid.uuid4())
        token = make_signed_jwt(
            private_key,
            {
                "aud": "client-1",
                "iss": f"https://login.microsoftonline.com/{other_tenant}/v2.0",
                "tid": str(uuid.uuid4()),  # deliberately mismatched
            },
        )

        with pytest.raises(ValueError, match="Invalid issuer"):
            await validator.validate_token(token)

    @pytest.mark.asyncio
    async def test_missing_tid_skips_binding_even_when_issuer_validation_disabled(
        self, monkeypatch
    ):
        # Resolved choice: a missing tid must SKIP binding rather than reject,
        # regardless of VALIDATE_ISSUER.
        private_key, public_key = generate_rsa_keypair()
        other_tenant = str(uuid.uuid4())
        config = AgentAuthConfiguration(client_id="client-1", tenant_id="tenant-1")
        assert config.VALIDATE_ISSUER is False
        validator = JwtTokenValidator(config)
        _patch_signing_key(monkeypatch, validator, public_key)

        token = make_signed_jwt(
            private_key,
            {
                "aud": "client-1",
                "iss": f"https://login.microsoftonline.com/{other_tenant}/v2.0",
                # no "tid" claim at all
            },
        )

        identity = await validator.validate_token(token)
        assert identity.is_authenticated is True

    @pytest.mark.asyncio
    async def test_noncanonical_entra_issuer_variants_skip_binding(self, monkeypatch):
        private_key, public_key = generate_rsa_keypair()
        issuer_tenant = str(uuid.uuid4())
        mismatched_tid = str(uuid.uuid4())
        config = AgentAuthConfiguration(client_id="client-1", tenant_id="tenant-1")
        validator = JwtTokenValidator(config)
        _patch_signing_key(monkeypatch, validator, public_key)

        for issuer in (
            f"https://sts.windows.net/{issuer_tenant}",
            f"https://login.microsoftonline.com/{issuer_tenant}/v2.0/",
            f"https://login.microsoftonline.com/{issuer_tenant}/V2.0",
        ):
            token = make_signed_jwt(
                private_key,
                {"aud": "client-1", "iss": issuer, "tid": mismatched_tid},
            )
            identity = await validator.validate_token(token)
            assert identity.is_authenticated is True

    @pytest.mark.asyncio
    async def test_issuer_allow_list_not_enforced_when_disabled(self, monkeypatch):
        # With VALIDATE_ISSUER left at its default (False), an unrecognized
        # issuer (not in the allow-list, and self-consistent with its own
        # tid so tenant binding does not reject it) must still be accepted:
        # only the issuer allow-list check is opt-in.
        private_key, public_key = generate_rsa_keypair()
        other_tenant = str(uuid.uuid4())
        config = AgentAuthConfiguration(client_id="client-1", tenant_id="tenant-1")
        assert config.VALIDATE_ISSUER is False
        validator = JwtTokenValidator(config)
        _patch_signing_key(monkeypatch, validator, public_key)

        token = make_signed_jwt(
            private_key,
            {
                "aud": "client-1",
                "iss": f"https://login.microsoftonline.com/{other_tenant}/v2.0",
                "tid": other_tenant,  # self-consistent: binding passes
            },
        )

        identity = await validator.validate_token(token)
        assert identity.is_authenticated is True

    @pytest.mark.asyncio
    async def test_validate_issuer_enabled_default_issuer_accepted(self, monkeypatch):
        private_key, public_key = generate_rsa_keypair()
        tenant_id = str(uuid.uuid4())
        config = AgentAuthConfiguration(
            client_id="client-1", tenant_id=tenant_id, validate_issuer=True
        )
        validator = JwtTokenValidator(config)
        _patch_signing_key(monkeypatch, validator, public_key)

        token = make_signed_jwt(
            private_key,
            {
                "aud": "client-1",
                "iss": f"https://login.microsoftonline.com/{tenant_id}/v2.0",
                "tid": tenant_id,
            },
        )

        identity = await validator.validate_token(token)
        assert identity.is_authenticated is True

    @pytest.mark.asyncio
    async def test_validate_issuer_enabled_unrecognized_issuer_rejected(
        self, monkeypatch
    ):
        private_key, public_key = generate_rsa_keypair()
        tenant_id = str(uuid.uuid4())
        other_tenant = str(uuid.uuid4())
        config = AgentAuthConfiguration(
            client_id="client-1", tenant_id=tenant_id, validate_issuer=True
        )
        validator = JwtTokenValidator(config)
        _patch_signing_key(monkeypatch, validator, public_key)

        token = make_signed_jwt(
            private_key,
            {
                "aud": "client-1",
                "iss": f"https://login.microsoftonline.com/{other_tenant}/v2.0",
                "tid": other_tenant,
            },
        )

        with pytest.raises(ValueError, match="Invalid issuer"):
            await validator.validate_token(token)

    @pytest.mark.asyncio
    async def test_validate_issuer_enabled_v1_issuer_recognized_and_bound(
        self, monkeypatch
    ):
        private_key, public_key = generate_rsa_keypair()
        tenant_id = str(uuid.uuid4())
        config = AgentAuthConfiguration(
            client_id="client-1", tenant_id=tenant_id, validate_issuer=True
        )
        validator = JwtTokenValidator(config)
        _patch_signing_key(monkeypatch, validator, public_key)

        token = make_signed_jwt(
            private_key,
            {
                "aud": "client-1",
                "iss": f"https://sts.windows.net/{tenant_id}/",
                "tid": tenant_id,
            },
        )

        identity = await validator.validate_token(token)
        assert identity.is_authenticated is True

    @pytest.mark.asyncio
    async def test_validate_issuer_enabled_tid_mismatch_rejected(self, monkeypatch):
        private_key, public_key = generate_rsa_keypair()
        tenant_id = str(uuid.uuid4())
        mismatched_tid = str(uuid.uuid4())
        config = AgentAuthConfiguration(
            client_id="client-1", tenant_id=tenant_id, validate_issuer=True
        )
        validator = JwtTokenValidator(config)
        _patch_signing_key(monkeypatch, validator, public_key)

        # iss matches the configured tenant's default issuer, but tid claims a
        # different tenant -- the binding must reject this.
        token = make_signed_jwt(
            private_key,
            {
                "aud": "client-1",
                "iss": f"https://login.microsoftonline.com/{tenant_id}/v2.0",
                "tid": mismatched_tid,
            },
        )

        with pytest.raises(ValueError, match="Invalid issuer"):
            await validator.validate_token(token)

    @pytest.mark.asyncio
    async def test_validate_issuer_enabled_missing_tid_skips_binding(self, monkeypatch):
        # Resolved choice: a missing tid must SKIP binding rather than reject.
        private_key, public_key = generate_rsa_keypair()
        tenant_id = str(uuid.uuid4())
        config = AgentAuthConfiguration(
            client_id="client-1", tenant_id=tenant_id, validate_issuer=True
        )
        validator = JwtTokenValidator(config)
        _patch_signing_key(monkeypatch, validator, public_key)

        token = make_signed_jwt(
            private_key,
            {
                "aud": "client-1",
                "iss": f"https://login.microsoftonline.com/{tenant_id}/v2.0",
                # no "tid" claim at all
            },
        )

        identity = await validator.validate_token(token)
        assert identity.is_authenticated is True

    @pytest.mark.asyncio
    async def test_validate_issuer_enabled_bot_framework_issuer_skips_binding(
        self, monkeypatch
    ):
        private_key, public_key = generate_rsa_keypair()
        config = AgentAuthConfiguration(
            client_id="client-1", tenant_id="tenant-1", validate_issuer=True
        )
        validator = JwtTokenValidator(config)
        captured_uris = []
        _patch_signing_key(monkeypatch, validator, public_key, captured_uris)

        token = make_signed_jwt(
            private_key,
            {
                "aud": "client-1",
                "iss": "https://api.botframework.com",
                # Bot Framework tokens carry no tid; binding must be skipped.
            },
        )

        identity = await validator.validate_token(token)
        assert identity.is_authenticated is True
        assert captured_uris == ["https://login.botframework.com/v1/.well-known/keys"]

    @pytest.mark.asyncio
    async def test_validate_issuer_enabled_alias_tenant_issuer_skips_binding(
        self, monkeypatch
    ):
        # An operator-configured issuer using a tenant domain alias (rather
        # than a GUID) cannot be compared to the GUID `tid` claim, so binding
        # is skipped even though the issuer itself is explicitly allow-listed.
        private_key, public_key = generate_rsa_keypair()
        config = AgentAuthConfiguration(
            client_id="client-1",
            tenant_id="tenant-1",
            validate_issuer=True,
            issuers=["https://login.microsoftonline.com/contoso.onmicrosoft.com/v2.0"],
        )
        validator = JwtTokenValidator(config)
        _patch_signing_key(monkeypatch, validator, public_key)

        token = make_signed_jwt(
            private_key,
            {
                "aud": "client-1",
                "iss": "https://login.microsoftonline.com/contoso.onmicrosoft.com/v2.0",
                "tid": str(uuid.uuid4()),
            },
        )

        identity = await validator.validate_token(token)
        assert identity.is_authenticated is True

    @pytest.mark.asyncio
    async def test_validate_issuer_enabled_well_known_first_party_issuer_accepted(
        self, monkeypatch
    ):
        # Well-known Microsoft first-party tenants are always trusted even
        # though they are not the connection's own configured tenant.
        private_key, public_key = generate_rsa_keypair()
        well_known_tenant = "d6d49420-f39b-4df7-a1dc-d59a935871db"
        config = AgentAuthConfiguration(
            client_id="client-1",
            tenant_id=str(uuid.uuid4()),
            validate_issuer=True,
        )
        validator = JwtTokenValidator(config)
        _patch_signing_key(monkeypatch, validator, public_key)

        token = make_signed_jwt(
            private_key,
            {
                "aud": "client-1",
                "iss": f"https://login.microsoftonline.com/{well_known_tenant}/v2.0",
                "tid": well_known_tenant,
            },
        )

        identity = await validator.validate_token(token)
        assert identity.is_authenticated is True

    @pytest.mark.asyncio
    async def test_validate_issuer_enabled_explicit_issuers_used(self, monkeypatch):
        private_key, public_key = generate_rsa_keypair()
        config = AgentAuthConfiguration(
            client_id="client-1",
            tenant_id="tenant-1",
            validate_issuer=True,
            issuers=["https://custom-issuer.example.com/"],
        )
        validator = JwtTokenValidator(config)
        _patch_signing_key(monkeypatch, validator, public_key)

        token = make_signed_jwt(
            private_key,
            {"aud": "client-1", "iss": "https://custom-issuer.example.com/"},
        )

        identity = await validator.validate_token(token)
        assert identity.is_authenticated is True

    @pytest.mark.asyncio
    async def test_validate_issuer_enabled_common_tenant_accepts_any_same_cloud_tenant(
        self, monkeypatch
    ):
        private_key, public_key = generate_rsa_keypair()
        caller_tenant = str(uuid.uuid4())
        config = AgentAuthConfiguration(
            client_id="client-1", tenant_id="common", validate_issuer=True
        )
        validator = JwtTokenValidator(config)
        _patch_signing_key(monkeypatch, validator, public_key)

        token = make_signed_jwt(
            private_key,
            {
                "aud": "client-1",
                "iss": f"https://login.microsoftonline.com/{caller_tenant}/v2.0",
                "tid": caller_tenant,
            },
        )

        identity = await validator.validate_token(token)
        assert identity.is_authenticated is True

    @pytest.mark.asyncio
    async def test_validate_issuer_enabled_organizations_tenant_accepts_any_same_cloud_tenant(
        self, monkeypatch
    ):
        private_key, public_key = generate_rsa_keypair()
        caller_tenant = str(uuid.uuid4())
        config = AgentAuthConfiguration(
            client_id="client-1", tenant_id="organizations", validate_issuer=True
        )
        validator = JwtTokenValidator(config)
        _patch_signing_key(monkeypatch, validator, public_key)

        token = make_signed_jwt(
            private_key,
            {
                "aud": "client-1",
                "iss": f"https://sts.windows.net/{caller_tenant}/",
                "tid": caller_tenant,
            },
        )

        identity = await validator.validate_token(token)
        assert identity.is_authenticated is True

    @pytest.mark.asyncio
    async def test_validate_issuer_enabled_gov_authority_routes_and_accepts_gov_issuer(
        self, monkeypatch
    ):
        private_key, public_key = generate_rsa_keypair()
        tenant_id = str(uuid.uuid4())
        config = AgentAuthConfiguration(
            client_id="client-1",
            tenant_id=tenant_id,
            authority="https://login.microsoftonline.us",
            validate_issuer=True,
        )
        validator = JwtTokenValidator(config)
        captured_uris = []
        _patch_signing_key(monkeypatch, validator, public_key, captured_uris)

        token = make_signed_jwt(
            private_key,
            {
                "aud": "client-1",
                "iss": f"https://login.microsoftonline.us/{tenant_id}/v2.0",
                "tid": tenant_id,
            },
        )

        identity = await validator.validate_token(token)
        assert identity.is_authenticated is True
        assert captured_uris == [
            f"https://login.microsoftonline.us/{tenant_id}/discovery/v2.0/keys"
        ]

    @pytest.mark.asyncio
    async def test_validate_issuer_enabled_gov_authority_rejects_public_cloud_issuer(
        self, monkeypatch
    ):
        # A v2 issuer from the *other* cloud must not be accepted even if the
        # tenant GUID happens to match: cloud affinity is enforced too.
        private_key, public_key = generate_rsa_keypair()
        tenant_id = str(uuid.uuid4())
        config = AgentAuthConfiguration(
            client_id="client-1",
            tenant_id="organizations",
            authority="https://login.microsoftonline.us",
            validate_issuer=True,
        )
        validator = JwtTokenValidator(config)
        _patch_signing_key(monkeypatch, validator, public_key)

        token = make_signed_jwt(
            private_key,
            {
                "aud": "client-1",
                "iss": f"https://login.microsoftonline.com/{tenant_id}/v2.0",
                "tid": tenant_id,
            },
        )

        with pytest.raises(ValueError, match="Invalid issuer"):
            await validator.validate_token(token)


class TestJwtTokenValidatorMultiConnection:
    @pytest.mark.asyncio
    async def test_public_jwks_routing_preserves_root_connection_endpoint(
        self, monkeypatch
    ):
        # Public-cloud routing intentionally retains the pre-existing root
        # connection endpoint even when another connection matches the token's
        # audience. This avoids changing network egress for existing agents.
        private_key, public_key = generate_rsa_keypair()
        tenant_a = str(uuid.uuid4())
        tenant_b = str(uuid.uuid4())
        config_a = AgentAuthConfiguration(
            client_id="client-a",
            tenant_id=tenant_a,
            connection_name="SERVICE_CONNECTION",
        )
        config_b = AgentAuthConfiguration(
            client_id="client-b", tenant_id=tenant_b, connection_name="MCS"
        )
        shared_connections = {"SERVICE_CONNECTION": config_a, "MCS": config_b}
        config_a._connections = shared_connections
        config_b._connections = shared_connections

        # Validator constructed against connection A's config, but the token
        # is issued for connection B's audience/tenant.
        validator = JwtTokenValidator(config_a)
        captured_uris = []
        _patch_signing_key(monkeypatch, validator, public_key, captured_uris)

        token = make_signed_jwt(private_key, {"aud": "client-b"})
        identity = await validator.validate_token(token)

        assert identity.is_authenticated is True
        assert captured_uris == [
            f"https://login.microsoftonline.com/{tenant_a}/discovery/v2.0/keys"
        ]

    @pytest.mark.asyncio
    async def test_gov_jwks_routing_uses_matching_connection_by_audience(
        self, monkeypatch
    ):
        private_key, public_key = generate_rsa_keypair()
        public_tenant = str(uuid.uuid4())
        gov_tenant = str(uuid.uuid4())
        config_a = AgentAuthConfiguration(
            client_id="client-a",
            tenant_id=public_tenant,
            connection_name="SERVICE_CONNECTION",
        )
        config_b = AgentAuthConfiguration(
            client_id="client-b",
            tenant_id=gov_tenant,
            authority="https://login.microsoftonline.us",
            connection_name="MCS",
        )
        shared_connections = {"SERVICE_CONNECTION": config_a, "MCS": config_b}
        config_a._connections = shared_connections
        config_b._connections = shared_connections

        validator = JwtTokenValidator(config_a)
        captured_uris = []
        _patch_signing_key(monkeypatch, validator, public_key, captured_uris)

        token = make_signed_jwt(private_key, {"aud": "client-b"})
        identity = await validator.validate_token(token)

        assert identity.is_authenticated is True
        assert captured_uris == [
            f"https://login.microsoftonline.us/{gov_tenant}/discovery/v2.0/keys"
        ]

    @pytest.mark.asyncio
    async def test_validate_token_multi_connection_issuer_validation_uses_matched_tenant(
        self, monkeypatch
    ):
        private_key, public_key = generate_rsa_keypair()
        tenant_a = str(uuid.uuid4())
        tenant_b = str(uuid.uuid4())
        config_a = AgentAuthConfiguration(
            client_id="client-a",
            tenant_id=tenant_a,
            connection_name="SERVICE_CONNECTION",
            validate_issuer=True,
        )
        config_b = AgentAuthConfiguration(
            client_id="client-b",
            tenant_id=tenant_b,
            connection_name="MCS",
            validate_issuer=True,
        )
        shared_connections = {"SERVICE_CONNECTION": config_a, "MCS": config_b}
        config_a._connections = shared_connections
        config_b._connections = shared_connections

        validator = JwtTokenValidator(config_a)
        _patch_signing_key(monkeypatch, validator, public_key)

        # Issuer/tid belong to tenant B, matching audience client-b: must be
        # validated against connection B's tenant, not A's.
        token = make_signed_jwt(
            private_key,
            {
                "aud": "client-b",
                "iss": f"https://login.microsoftonline.com/{tenant_b}/v2.0",
                "tid": tenant_b,
            },
        )

        identity = await validator.validate_token(token)
        assert identity.is_authenticated is True


class TestJwtTokenValidatorEffectiveTenant:
    """Covers the authority-embedded tenant segment (e.g.
    ``https://login.microsoftonline.com/common`` or
    ``.../{tenant-guid}``) taking precedence over a separately configured
    TENANT_ID for JWKS routing, multi-tenant detection, and default issuers.
    """

    @pytest.mark.asyncio
    async def test_public_jwks_routing_defaults_to_common_without_tenant(
        self, monkeypatch
    ):
        private_key, public_key = generate_rsa_keypair()
        config = AgentAuthConfiguration(client_id="client-1")
        validator = JwtTokenValidator(config)
        captured_uris = []
        _patch_signing_key(monkeypatch, validator, public_key, captured_uris)

        token = make_signed_jwt(
            private_key,
            {
                "aud": "client-1",
                "iss": "https://custom.example.com",
            },
        )

        identity = await validator.validate_token(token)
        assert identity.is_authenticated is True
        assert captured_uris == [
            "https://login.microsoftonline.com/common/discovery/v2.0/keys"
        ]

    @pytest.mark.asyncio
    async def test_public_jwks_routing_ignores_authority_embedded_common_tenant(
        self, monkeypatch
    ):
        # Issuer policy uses AUTHORITY's effective tenant, but public JWKS
        # routing preserves the legacy root TENANT_ID endpoint.
        private_key, public_key = generate_rsa_keypair()
        caller_tenant = str(uuid.uuid4())
        config = AgentAuthConfiguration(
            client_id="client-1",
            tenant_id="concrete-tenant-id",
            authority="https://login.microsoftonline.com/common",
            validate_issuer=True,
        )
        validator = JwtTokenValidator(config)
        captured_uris = []
        _patch_signing_key(monkeypatch, validator, public_key, captured_uris)

        token = make_signed_jwt(
            private_key,
            {
                "aud": "client-1",
                "iss": f"https://login.microsoftonline.com/{caller_tenant}/v2.0",
                "tid": caller_tenant,
            },
        )

        identity = await validator.validate_token(token)
        assert identity.is_authenticated is True
        assert captured_uris == [
            "https://login.microsoftonline.com/concrete-tenant-id/discovery/v2.0/keys"
        ]

    @pytest.mark.asyncio
    async def test_public_jwks_routing_ignores_authority_embedded_concrete_tenant(
        self, monkeypatch
    ):
        # Issuer policy uses AUTHORITY's concrete tenant, but public JWKS
        # routing preserves the legacy root TENANT_ID endpoint.
        private_key, public_key = generate_rsa_keypair()
        concrete_tenant = str(uuid.uuid4())
        config = AgentAuthConfiguration(
            client_id="client-1",
            tenant_id="common",
            authority=f"https://login.microsoftonline.com/{concrete_tenant}",
            validate_issuer=True,
        )
        validator = JwtTokenValidator(config)
        captured_uris = []
        _patch_signing_key(monkeypatch, validator, public_key, captured_uris)

        token = make_signed_jwt(
            private_key,
            {
                "aud": "client-1",
                "iss": f"https://login.microsoftonline.com/{concrete_tenant}/v2.0",
                "tid": concrete_tenant,
            },
        )

        identity = await validator.validate_token(token)
        assert identity.is_authenticated is True
        assert captured_uris == [
            "https://login.microsoftonline.com/common/discovery/v2.0/keys"
        ]

    @pytest.mark.asyncio
    async def test_authority_embedded_concrete_tenant_rejects_other_tenant_issuer(
        self, monkeypatch
    ):
        # Because AUTHORITY's embedded concrete tenant takes precedence over
        # the "common" TENANT_ID, this connection is NOT treated as
        # multi-tenant: an issuer for a different tenant must be rejected.
        private_key, public_key = generate_rsa_keypair()
        concrete_tenant = str(uuid.uuid4())
        other_tenant = str(uuid.uuid4())
        config = AgentAuthConfiguration(
            client_id="client-1",
            tenant_id="common",
            authority=f"https://login.microsoftonline.com/{concrete_tenant}",
            validate_issuer=True,
        )
        validator = JwtTokenValidator(config)
        _patch_signing_key(monkeypatch, validator, public_key)

        token = make_signed_jwt(
            private_key,
            {
                "aud": "client-1",
                "iss": f"https://login.microsoftonline.com/{other_tenant}/v2.0",
                "tid": other_tenant,
            },
        )

        with pytest.raises(ValueError, match="Invalid issuer"):
            await validator.validate_token(token)
