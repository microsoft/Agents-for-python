import asyncio
import threading
import time

import pytest
from jwt import PyJWKClient

from microsoft_agents.hosting.core.authorization.jwt_token_validator import (
    _JwkClientManager,
)


async def _wait_until_set(event: threading.Event, timeout: float = 1.0) -> None:
    start = time.monotonic()
    while not event.is_set():
        if time.monotonic() - start > timeout:
            raise AssertionError("Timed out waiting for threading event.")
        await asyncio.sleep(0.01)


class TestJwkClientManager:
    def test_get_jwk_client_reuses_cache_for_same_uri(self):
        manager = _JwkClientManager()
        jwks_uri = "https://issuer.example.com/keys"

        first = manager._get_jwk_client(jwks_uri)
        second = manager._get_jwk_client(jwks_uri)

        assert first is second
        assert len(manager._cache) == 1

    def test_get_jwk_client_creates_distinct_entries_for_distinct_uris(self):
        manager = _JwkClientManager()

        first = manager._get_jwk_client("https://issuer-a.example.com/keys")
        second = manager._get_jwk_client("https://issuer-b.example.com/keys")

        assert first is not second
        assert first.lock is not second.lock
        assert len(manager._cache) == 2

    @pytest.mark.asyncio
    async def test_get_signing_key_calls_pyjwkclient_with_header_kid(
        self, monkeypatch
    ):
        manager = _JwkClientManager()
        jwks_uri = "https://issuer.example.com/keys"
        seen_kids = []
        expected_key = object()

        def fake_get_signing_key(self, kid):
            seen_kids.append(kid)
            return expected_key

        # Only mocked member: PyJWKClient.get_signing_key
        monkeypatch.setattr(PyJWKClient, "get_signing_key", fake_get_signing_key)

        key = await manager.get_signing_key(jwks_uri, {"kid": "kid-123"})

        assert key is expected_key
        assert seen_kids == ["kid-123"]

    @pytest.mark.asyncio
    async def test_get_signing_key_reuses_same_client_for_same_uri(self, monkeypatch):
        manager = _JwkClientManager()
        jwks_uri = "https://issuer.example.com/keys"
        client_ids = []

        def fake_get_signing_key(self, kid):
            client_ids.append(id(self))
            return {"kid": kid}

        # Only mocked member: PyJWKClient.get_signing_key
        monkeypatch.setattr(PyJWKClient, "get_signing_key", fake_get_signing_key)

        await manager.get_signing_key(jwks_uri, {"kid": "kid-a"})
        await manager.get_signing_key(jwks_uri, {"kid": "kid-b"})

        assert client_ids[0] == client_ids[1]
        assert len(manager._cache) == 1

    @pytest.mark.asyncio
    async def test_get_signing_key_serializes_concurrent_calls_per_uri(
        self, monkeypatch
    ):
        manager = _JwkClientManager()
        jwks_uri = "https://issuer.example.com/keys"

        first_entered = threading.Event()
        second_entered = threading.Event()
        release_first = threading.Event()

        def fake_get_signing_key(self, kid):
            if kid == "kid-1":
                first_entered.set()
                if not release_first.wait(timeout=2):
                    raise TimeoutError("First call was not released in time.")
            elif kid == "kid-2":
                second_entered.set()
            return {"kid": kid}

        # Only mocked member: PyJWKClient.get_signing_key
        monkeypatch.setattr(PyJWKClient, "get_signing_key", fake_get_signing_key)

        first_task = asyncio.create_task(
            manager.get_signing_key(jwks_uri, {"kid": "kid-1"})
        )
        await _wait_until_set(first_entered)

        second_task = asyncio.create_task(
            manager.get_signing_key(jwks_uri, {"kid": "kid-2"})
        )

        # If per-URI lock works, second call must not enter get_signing_key yet.
        await asyncio.sleep(0.05)
        assert not second_entered.is_set()

        release_first.set()
        results = await asyncio.gather(first_task, second_task)

        assert results[0]["kid"] == "kid-1"
        assert results[1]["kid"] == "kid-2"
        assert second_entered.is_set()

    @pytest.mark.asyncio
    async def test_get_signing_key_raises_key_error_when_header_has_no_kid(self):
        manager = _JwkClientManager()

        with pytest.raises(KeyError):
            await manager.get_signing_key("https://issuer.example.com/keys", {})