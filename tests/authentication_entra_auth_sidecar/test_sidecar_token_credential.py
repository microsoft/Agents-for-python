# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import jwt
import pytest

from datetime import datetime, timedelta, timezone

from microsoft_agents.hosting.core import AgentAuthConfiguration
from microsoft_agents.authentication.entra_auth_sidecar.sidecar_token_credential import (
    SidecarTokenCredential,
    _get_resource,
)


class FakeSidecarProvider:
    """Records calls and returns a configurable token."""

    def __init__(self, token="token"):
        self.calls = []
        self.token = token
        self.closed = False

    async def get_access_token(self, resource_url, scopes):
        self.calls.append((resource_url, scopes))
        return self.token() if callable(self.token) else self.token

    async def close(self):
        self.closed = True


def _make_credential(token="token"):
    config = AgentAuthConfiguration(
        auth_type="EntraAuthSideCar", client_id="blueprint-id"
    )
    provider = FakeSidecarProvider(token=token)
    return SidecarTokenCredential(config, provider=provider), provider


def _jwt_with_exp(exp: datetime) -> str:
    return jwt.encode({"exp": int(exp.timestamp())}, "x" * 32, algorithm="HS256")


class TestGetResource:
    def test_strips_default_suffix(self):
        assert _get_resource("api://res/.default") == "api://res"

    def test_leaves_scope_without_suffix_unchanged(self):
        assert _get_resource("api://res") == "api://res"


class TestSidecarTokenCredentialInit:
    def test_manage_provider_lifetime_false_when_provider_supplied(self):
        credential, _ = _make_credential()
        assert credential._manage_provider_lifetime is False

    def test_manage_provider_lifetime_true_when_provider_not_supplied(self):
        config = AgentAuthConfiguration(
            auth_type="EntraAuthSideCar", client_id="blueprint-id"
        )
        credential = SidecarTokenCredential(config)
        assert credential._manage_provider_lifetime is True


class TestSidecarTokenCredentialGetToken:
    @pytest.mark.asyncio
    async def test_requires_at_least_one_scope(self):
        credential, _ = _make_credential()
        with pytest.raises(ValueError):
            await credential.get_token()

    @pytest.mark.asyncio
    async def test_uses_resource_derived_from_first_scope(self):
        exp = datetime.now(timezone.utc) + timedelta(hours=1)
        credential, provider = _make_credential(token=_jwt_with_exp(exp))
        await credential.get_token("api://res/.default", "extra-scope")
        resource, scopes = provider.calls[0]
        assert resource == "api://res"
        assert scopes == ["api://res/.default", "extra-scope"]

    @pytest.mark.asyncio
    async def test_returns_access_token_with_resolved_expiry(self):
        exp = datetime.now(timezone.utc) + timedelta(hours=1)
        token = _jwt_with_exp(exp)
        credential, _ = _make_credential(token=token)
        access_token = await credential.get_token("api://res/.default")
        assert access_token.token == token
        assert abs(access_token.expires_on - int(exp.timestamp())) <= 1

    @pytest.mark.asyncio
    async def test_opaque_token_uses_fallback_expiry(self):
        from microsoft_agents.authentication.entra_auth_sidecar._token_expiry import (
            FALLBACK_LIFETIME,
        )

        before = datetime.now(timezone.utc)
        credential, _ = _make_credential(token="opaque-token")
        access_token = await credential.get_token("api://res/.default")
        expected = before + FALLBACK_LIFETIME
        assert abs(access_token.expires_on - int(expected.timestamp())) <= 5

    @pytest.mark.asyncio
    async def test_lazily_creates_provider_when_none_supplied(self, monkeypatch):
        config = AgentAuthConfiguration(
            auth_type="EntraAuthSideCar", client_id="blueprint-id"
        )
        credential = SidecarTokenCredential(config)
        assert credential._provider is None

        exp = datetime.now(timezone.utc) + timedelta(hours=1)
        fake_provider = FakeSidecarProvider(token=_jwt_with_exp(exp))

        import microsoft_agents.authentication.entra_auth_sidecar.sidecar_token_credential as module

        monkeypatch.setattr(module, "SidecarAuth", lambda _config: fake_provider)

        await credential.get_token("api://res/.default")
        assert credential._provider is fake_provider
        assert len(fake_provider.calls) == 1


class TestSidecarTokenCredentialLifecycle:
    """
    Ownership rule: the credential only closes/clears a provider it created
    itself (lazy-init path). A provider supplied by the caller (e.g. from
    ``SidecarAuth.get_token_credential``) is externally owned, so ``close()``
    must leave it open and untouched.
    """

    @pytest.mark.asyncio
    async def test_close_leaves_externally_supplied_provider_open(self):
        credential, provider = _make_credential()
        await credential.close()
        assert provider.closed is False
        assert credential._provider is provider

    @pytest.mark.asyncio
    async def test_close_closes_and_clears_lazily_created_provider(self, monkeypatch):
        config = AgentAuthConfiguration(
            auth_type="EntraAuthSideCar", client_id="blueprint-id"
        )
        credential = SidecarTokenCredential(config)
        fake_provider = FakeSidecarProvider()

        import microsoft_agents.authentication.entra_auth_sidecar.sidecar_token_credential as module

        monkeypatch.setattr(module, "SidecarAuth", lambda _config: fake_provider)
        await credential.get_token("api://res/.default")

        await credential.close()
        assert fake_provider.closed is True
        assert credential._provider is None

    @pytest.mark.asyncio
    async def test_close_is_noop_when_no_provider(self):
        config = AgentAuthConfiguration(
            auth_type="EntraAuthSideCar", client_id="blueprint-id"
        )
        credential = SidecarTokenCredential(config)
        await credential.close()
        assert credential._provider is None

    @pytest.mark.asyncio
    async def test_aexit_leaves_externally_supplied_provider_open(self):
        credential, provider = _make_credential()
        await credential.__aexit__(None, None, None)
        assert provider.closed is False

    @pytest.mark.asyncio
    async def test_aexit_closes_lazily_created_provider(self, monkeypatch):
        config = AgentAuthConfiguration(
            auth_type="EntraAuthSideCar", client_id="blueprint-id"
        )
        credential = SidecarTokenCredential(config)
        fake_provider = FakeSidecarProvider()

        import microsoft_agents.authentication.entra_auth_sidecar.sidecar_token_credential as module

        monkeypatch.setattr(module, "SidecarAuth", lambda _config: fake_provider)
        await credential.get_token("api://res/.default")

        await credential.__aexit__(None, None, None)
        assert fake_provider.closed is True
