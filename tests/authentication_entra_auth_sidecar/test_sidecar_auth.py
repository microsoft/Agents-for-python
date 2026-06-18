# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import jwt
import pytest

from datetime import datetime, timedelta, timezone

from microsoft_agents.hosting.core import AgentAuthConfiguration
from microsoft_agents.authentication.entra_auth_sidecar import SidecarAuth
from microsoft_agents.authentication.entra_auth_sidecar._models import (
    SidecarTokenResult,
)


class FakeSidecarClient:
    """Records calls and returns a configurable token."""

    def __init__(self, token="token", healthy=True):
        self.calls = []
        self.token = token
        self._healthy = healthy
        self.closed = False

    async def get_authorization_header_unauthenticated(
        self, service_name, options=None
    ):
        self.calls.append((service_name, options))
        token = self.token() if callable(self.token) else self.token
        return SidecarTokenResult("Bearer", token)

    async def is_healthy(self):
        return self._healthy

    async def aclose(self):
        self.closed = True


def _make_auth(token="token", scopes=None, healthy=True, **settings):
    config = AgentAuthConfiguration(
        auth_type="EntraAuthSideCar",
        client_id="blueprint-id",
        scopes=scopes,
        **settings,
    )
    client = FakeSidecarClient(token=token, healthy=healthy)
    return SidecarAuth(config, sidecar_client=client), client


class TestSidecarAuthMapping:
    @pytest.mark.asyncio
    async def test_get_access_token_uses_service_name_app_token(self):
        auth, client = _make_auth()
        token = await auth.get_access_token("https://res", ["api://x/.default"])
        assert token == "token"
        service, options = client.calls[0]
        assert service == "default"
        assert options.request_app_token is True
        assert options.scopes == ["api://x/.default"]

    @pytest.mark.asyncio
    async def test_get_agentic_application_token_uses_blueprint(self):
        auth, client = _make_auth()
        token = await auth.get_agentic_application_token("tenant-1", "agent-1")
        assert token == "token"
        service, options = client.calls[0]
        assert service == "agenticblueprint"
        assert options.agent_identity == "agent-1"
        assert options.tenant == "tenant-1"

    @pytest.mark.asyncio
    async def test_get_agentic_application_token_requires_id(self):
        auth, _ = _make_auth()
        with pytest.raises(ValueError):
            await auth.get_agentic_application_token("tenant-1", "")

    @pytest.mark.asyncio
    async def test_get_agentic_instance_token_returns_tuple(self):
        auth, client = _make_auth(scopes=["api://res/.default"])
        result = await auth.get_agentic_instance_token("tenant-1", "agent-1")
        assert result == ("token", "token")
        service, options = client.calls[0]
        assert service == "default"
        assert options.request_app_token is True
        assert options.scopes == ["api://res/.default"]

    @pytest.mark.asyncio
    async def test_get_agentic_user_token_guid_uses_user_id(self):
        auth, client = _make_auth()
        guid = "11111111-1111-1111-1111-111111111111"
        await auth.get_agentic_user_token("tenant-1", "agent-1", guid, ["s"])
        _, options = client.calls[0]
        assert options.agent_user_id == guid
        assert options.agent_username is None

    @pytest.mark.asyncio
    async def test_get_agentic_user_token_upn_uses_username(self):
        auth, client = _make_auth()
        await auth.get_agentic_user_token(
            "tenant-1", "agent-1", "user@contoso.com", ["s"]
        )
        _, options = client.calls[0]
        assert options.agent_username == "user@contoso.com"
        assert options.agent_user_id is None

    @pytest.mark.asyncio
    async def test_get_agentic_user_token_requires_ids(self):
        auth, _ = _make_auth()
        with pytest.raises(ValueError):
            await auth.get_agentic_user_token("tenant-1", "agent-1", "", ["s"])

    @pytest.mark.asyncio
    async def test_is_healthy_delegates(self):
        auth, _ = _make_auth(healthy=False)
        assert await auth.is_healthy() is False

    @pytest.mark.asyncio
    async def test_close_delegates(self):
        auth, client = _make_auth()
        await auth.close()
        assert client.closed is True


class TestSidecarAuthCache:
    @pytest.mark.asyncio
    async def test_caches_repeat_calls(self):
        counter = {"n": 0}

        def token():
            counter["n"] += 1
            return f"token-{counter['n']}"

        auth, client = _make_auth(token=token)
        t1 = await auth.get_agentic_application_token("tenant-1", "agent-1")
        t2 = await auth.get_agentic_application_token("tenant-1", "agent-1")
        assert t1 == t2
        assert len(client.calls) == 1

    @pytest.mark.asyncio
    async def test_distinct_identity_distinct_entry(self):
        auth, client = _make_auth()
        await auth.get_agentic_application_token("tenant-1", "agent-1")
        await auth.get_agentic_application_token("tenant-1", "agent-2")
        assert len(client.calls) == 2

    @pytest.mark.asyncio
    async def test_force_refresh_bypasses_cache(self):
        auth, client = _make_auth()
        await auth.get_access_token("https://res", ["s"])
        await auth.get_access_token("https://res", ["s"], force_refresh=True)
        assert len(client.calls) == 2

    @pytest.mark.asyncio
    async def test_near_expiry_token_not_cached(self):
        # JWT expiring in 10 seconds is within the 30s buffer -> never cached.
        def token():
            exp = datetime.now(timezone.utc) + timedelta(seconds=10)
            return jwt.encode(
                {"exp": int(exp.timestamp())}, "x" * 32, algorithm="HS256"
            )

        auth, client = _make_auth(token=token)
        await auth.get_access_token("https://res", ["s"])
        await auth.get_access_token("https://res", ["s"])
        assert len(client.calls) == 2

    def test_cache_key_scope_order_independent(self):
        from microsoft_agents.authentication.entra_auth_sidecar._models import (
            SidecarRequestOptions,
        )

        k1 = SidecarAuth._build_cache_key(
            "svc", SidecarRequestOptions(scopes=["a", "b"])
        )
        k2 = SidecarAuth._build_cache_key(
            "svc", SidecarRequestOptions(scopes=["b", "a"])
        )
        assert k1 == k2
