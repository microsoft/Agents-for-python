# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import httpx
import pytest

from microsoft_agents.authentication.entra_auth_sidecar import (
    SidecarHttpClient,
    SidecarAuthError,
    SidecarConfigurationError,
    SidecarUnavailableError,
    SidecarRequestOptions,
)


def _make_client(handler, **kwargs):
    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(transport=transport)
    return SidecarHttpClient("http://localhost:5178", http_client=http_client, **kwargs)


class TestResolveBaseUrl:
    def test_default(self, monkeypatch):
        monkeypatch.delenv("SIDECAR_URL", raising=False)
        assert SidecarHttpClient.resolve_base_url() == "http://localhost:5178"

    def test_configured(self, monkeypatch):
        monkeypatch.delenv("SIDECAR_URL", raising=False)
        assert (
            SidecarHttpClient.resolve_base_url("http://10.0.0.1:9000")
            == "http://10.0.0.1:9000"
        )

    def test_env_takes_precedence(self, monkeypatch):
        monkeypatch.setenv("SIDECAR_URL", "http://127.0.0.1:6000")
        assert (
            SidecarHttpClient.resolve_base_url("http://10.0.0.1:9000")
            == "http://127.0.0.1:6000"
        )

    def test_blank_env_falls_back(self, monkeypatch):
        monkeypatch.setenv("SIDECAR_URL", "   ")
        assert (
            SidecarHttpClient.resolve_base_url("http://10.0.0.1:9000")
            == "http://10.0.0.1:9000"
        )


class TestValidateBaseUrl:
    @pytest.mark.parametrize(
        "url",
        [
            "http://localhost:5178",
            "http://app.localhost:5178",
            "http://127.0.0.1:5178",
            "http://10.0.0.5:5178",
            "http://172.16.3.4:5178",
            "http://192.168.1.10:5178",
            "http://169.254.1.1:5178",
            "http://[::1]:5178",
            "https://localhost",
        ],
    )
    def test_allows_loopback_and_private(self, url):
        SidecarHttpClient.validate_base_url(url, False)

    @pytest.mark.parametrize(
        "url",
        [
            "http://example.com",
            "http://8.8.8.8",
            "https://contoso.azurewebsites.net",
        ],
    )
    def test_rejects_public(self, url):
        with pytest.raises(SidecarAuthError):
            SidecarHttpClient.validate_base_url(url, False)

    def test_public_allowed_with_bypass(self):
        SidecarHttpClient.validate_base_url("http://example.com", True)

    def test_rejects_non_http_scheme(self):
        with pytest.raises(SidecarAuthError):
            SidecarHttpClient.validate_base_url("file:///etc/passwd", True)

    def test_rejects_non_http_scheme_with_valid_host(self):
        # A non-http(s) scheme must be rejected even when the host is otherwise a
        # valid loopback/private target (SSRF allowlist is scheme-aware).
        with pytest.raises(SidecarAuthError):
            SidecarHttpClient.validate_base_url("ftp://localhost:21", False)

    def test_rejects_userinfo(self):
        with pytest.raises(SidecarAuthError):
            SidecarHttpClient.validate_base_url(
                "http://user:pass@localhost:5178", False
            )

    def test_rejects_malformed(self):
        with pytest.raises(SidecarAuthError):
            SidecarHttpClient.validate_base_url("not-a-url", False)

    def test_userinfo_not_leaked_in_error(self):
        # A base URL that embeds credentials must not echo the password back in
        # the (commonly logged) validation error.
        with pytest.raises(SidecarAuthError) as exc:
            SidecarHttpClient.validate_base_url(
                "http://user:s3cr3tpassw0rd@localhost:5178", False
            )
        assert "s3cr3tpassw0rd" not in str(exc.value)

    def test_userinfo_with_invalid_port_raises_sidecar_error_without_leak(self):
        # An out-of-range port makes urlparse's lazy ``.port`` raise ValueError;
        # redaction must still yield a SidecarAuthError (not a bare ValueError)
        # and must not leak the embedded password.
        with pytest.raises(SidecarAuthError) as exc:
            SidecarHttpClient.validate_base_url(
                "http://user:s3cr3tpassw0rd@localhost:999999/path", False
            )
        assert "s3cr3tpassw0rd" not in str(exc.value)

    def test_invalid_port_without_userinfo_raises_sidecar_error(self):
        # A bad port with no userinfo must fail as SidecarAuthError at validation
        # time, not slip through and raise a bare ValueError later.
        with pytest.raises(SidecarAuthError):
            SidecarHttpClient.validate_base_url("http://localhost:999999", False)


class TestGetAuthorizationHeader:
    @pytest.mark.asyncio
    async def test_success_strips_scheme(self):
        async def handler(request):
            return httpx.Response(
                200, json={"authorizationHeader": "Bearer abc.def.ghi"}
            )

        client = _make_client(handler)
        result = await client.get_authorization_header_unauthenticated("default")
        assert result.scheme == "Bearer"
        assert result.token == "abc.def.ghi"
        await client.aclose()

    @pytest.mark.asyncio
    async def test_builds_query_params(self):
        captured = {}

        async def handler(request):
            captured["url"] = str(request.url)
            return httpx.Response(200, json={"authorizationHeader": "Bearer t"})

        client = _make_client(handler)
        options = SidecarRequestOptions(
            agent_identity="agent-1",
            agent_user_id="user-1",
            scopes=["api://x/.default", "  ", ""],
            request_app_token=True,
            tenant="tenant-1",
            force_refresh=True,
        )
        await client.get_authorization_header_unauthenticated("svc", options)
        url = captured["url"]
        assert "/AuthorizationHeaderUnauthenticated/svc" in url
        assert "AgentIdentity=agent-1" in url
        assert "AgentUserId=user-1" in url
        assert "optionsOverride.Scopes=api%3A%2F%2Fx%2F.default" in url
        assert "optionsOverride.RequestAppToken=true" in url
        assert "optionsOverride.AcquireTokenOptions.Tenant=tenant-1" in url
        assert "optionsOverride.AcquireTokenOptions.ForceRefresh=true" in url
        await client.aclose()

    @pytest.mark.asyncio
    async def test_username_only_query_param(self):
        captured = {}

        async def handler(request):
            captured["url"] = str(request.url)
            return httpx.Response(200, json={"authorizationHeader": "Bearer t"})

        client = _make_client(handler)
        options = SidecarRequestOptions(
            agent_identity="agent-1", agent_username="user@contoso.com"
        )
        await client.get_authorization_header_unauthenticated("svc", options)
        url = captured["url"]
        assert "AgentUsername=user%40contoso.com" in url
        assert "AgentUserId" not in url
        await client.aclose()

    @pytest.mark.asyncio
    async def test_username_and_userid_mutually_exclusive(self):
        async def handler(request):
            return httpx.Response(200, json={"authorizationHeader": "Bearer t"})

        client = _make_client(handler)
        options = SidecarRequestOptions(
            agent_username="u@contoso.com", agent_user_id="oid"
        )
        with pytest.raises(SidecarAuthError):
            await client.get_authorization_header_unauthenticated("svc", options)
        await client.aclose()

    @pytest.mark.asyncio
    async def test_404_raises_configuration_error(self):
        async def handler(request):
            return httpx.Response(404, json={"title": "Not found"})

        client = _make_client(handler, retry_count=0)
        with pytest.raises(SidecarConfigurationError):
            await client.get_authorization_header_unauthenticated("svc")
        await client.aclose()

    @pytest.mark.asyncio
    async def test_401_raises_auth_error(self):
        async def handler(request):
            return httpx.Response(401, json={"title": "Unauthorized"})

        client = _make_client(handler, retry_count=0)
        with pytest.raises(SidecarAuthError):
            await client.get_authorization_header_unauthenticated("svc")
        await client.aclose()

    @pytest.mark.asyncio
    async def test_400_raises_value_error(self):
        async def handler(request):
            return httpx.Response(400, json={"title": "Bad", "detail": "missing"})

        client = _make_client(handler, retry_count=0)
        with pytest.raises(ValueError):
            await client.get_authorization_header_unauthenticated("svc")
        await client.aclose()

    @pytest.mark.asyncio
    async def test_error_does_not_surface_detail(self):
        async def handler(request):
            return httpx.Response(
                400,
                json={
                    "title": "Bad Request",
                    "detail": "upn=user@contoso.com tenant=abc",
                },
            )

        client = _make_client(handler, retry_count=0)
        with pytest.raises(ValueError) as exc_info:
            await client.get_authorization_header_unauthenticated("svc")
        message = str(exc_info.value)
        # The title/status are surfaced, but the PII-bearing detail must never be.
        assert "Bad Request" in message
        assert "contoso.com" not in message
        assert "tenant=abc" not in message
        await client.aclose()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("header", ["Bearer", "bearer", "PoP"])
    async def test_scheme_only_header_raises(self, header):
        async def handler(request):
            return httpx.Response(200, json={"authorizationHeader": header})

        client = _make_client(handler, retry_count=0)
        with pytest.raises(SidecarAuthError):
            await client.get_authorization_header_unauthenticated("svc")
        await client.aclose()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("header", ["Bearer ", "PoP   "])
    async def test_scheme_with_empty_token_raises(self, header):
        async def handler(request):
            return httpx.Response(200, json={"authorizationHeader": header})

        client = _make_client(handler, retry_count=0)
        with pytest.raises(SidecarAuthError):
            await client.get_authorization_header_unauthenticated("svc")
        await client.aclose()

    @pytest.mark.asyncio
    async def test_missing_header_raises(self):
        async def handler(request):
            return httpx.Response(200, json={"somethingElse": "x"})

        client = _make_client(handler, retry_count=0)
        with pytest.raises(SidecarAuthError):
            await client.get_authorization_header_unauthenticated("svc")
        await client.aclose()

    @pytest.mark.asyncio
    async def test_unparsable_response_raises(self):
        async def handler(request):
            return httpx.Response(200, text="not json")

        client = _make_client(handler, retry_count=0)
        with pytest.raises(SidecarAuthError):
            await client.get_authorization_header_unauthenticated("svc")
        await client.aclose()

    @pytest.mark.asyncio
    async def test_retries_transient_then_succeeds(self):
        calls = {"n": 0}

        async def handler(request):
            calls["n"] += 1
            if calls["n"] < 3:
                return httpx.Response(503, text="busy")
            return httpx.Response(200, json={"authorizationHeader": "Bearer ok"})

        client = _make_client(handler, retry_count=3, retry_backoff_base=0)
        result = await client.get_authorization_header_unauthenticated("svc")
        assert result.token == "ok"
        assert calls["n"] == 3
        await client.aclose()

    @pytest.mark.asyncio
    async def test_connect_error_exhausts_to_unavailable(self):
        async def handler(request):
            raise httpx.ConnectError("refused")

        client = _make_client(handler, retry_count=1, retry_backoff_base=0)
        with pytest.raises(SidecarUnavailableError):
            await client.get_authorization_header_unauthenticated("svc")
        await client.aclose()

    @pytest.mark.asyncio
    async def test_is_healthy_true(self):
        async def handler(request):
            assert request.url.path == "/healthz"
            return httpx.Response(200, text="ok")

        client = _make_client(handler)
        assert await client.is_healthy() is True
        await client.aclose()

    @pytest.mark.asyncio
    async def test_is_healthy_false_on_error(self):
        async def handler(request):
            raise httpx.ConnectError("refused")

        client = _make_client(handler)
        assert await client.is_healthy() is False
        await client.aclose()

    @pytest.mark.asyncio
    async def test_403_raises_auth_error_with_empty_body(self):
        # A non-mapped error status with an empty body still raises (generic auth
        # error) and tolerates the missing problem-details payload.
        async def handler(request):
            return httpx.Response(403, text="")

        client = _make_client(handler, retry_count=0)
        with pytest.raises(SidecarAuthError):
            await client.get_authorization_header_unauthenticated("svc")
        await client.aclose()

    @pytest.mark.asyncio
    async def test_error_body_not_problem_details_json(self):
        # A non-JSON error body must be handled gracefully (no problem details),
        # still surfacing the status-derived error.
        async def handler(request):
            return httpx.Response(401, text="boom")

        client = _make_client(handler, retry_count=0)
        with pytest.raises(SidecarAuthError):
            await client.get_authorization_header_unauthenticated("svc")
        await client.aclose()

    @pytest.mark.asyncio
    async def test_error_without_problem_title_does_not_duplicate_status(self):
        # When the body carries no RFC7807 title, the message must not become
        # "Sidecar returned 403: Sidecar returned 403"; it uses a generic detail.
        async def handler(request):
            return httpx.Response(403, text="")

        client = _make_client(handler, retry_count=0)
        with pytest.raises(SidecarAuthError) as exc_info:
            await client.get_authorization_header_unauthenticated("svc")
        message = str(exc_info.value)
        assert "Sidecar returned 403" in message
        assert "no error details" in message
        assert "Sidecar returned 403: Sidecar returned 403" not in message
        await client.aclose()

    @pytest.mark.asyncio
    async def test_error_body_json_but_not_object(self):
        # A valid-JSON-but-non-object error body (e.g. an array) is not problem
        # details and must not crash the error path.
        async def handler(request):
            return httpx.Response(401, text="[1, 2, 3]")

        client = _make_client(handler, retry_count=0)
        with pytest.raises(SidecarAuthError):
            await client.get_authorization_header_unauthenticated("svc")
        await client.aclose()

    @pytest.mark.asyncio
    async def test_raw_token_without_scheme_defaults_to_bearer(self):
        async def handler(request):
            return httpx.Response(200, json={"authorizationHeader": "abc.def.ghi"})

        client = _make_client(handler)
        result = await client.get_authorization_header_unauthenticated("svc")
        assert result.scheme == "Bearer"
        assert result.token == "abc.def.ghi"
        await client.aclose()

    @pytest.mark.asyncio
    async def test_non_connect_transport_error_unavailable_without_retry(self):
        # A transport error that is not a connect/timeout failure is treated as
        # unavailable immediately, without consuming retries.
        calls = {"n": 0}

        async def handler(request):
            calls["n"] += 1
            raise httpx.ReadError("stream broke")

        client = _make_client(handler, retry_count=3, retry_backoff_base=0)
        with pytest.raises(SidecarUnavailableError):
            await client.get_authorization_header_unauthenticated("svc")
        assert calls["n"] == 1
        await client.aclose()


class TestClientOwnership:
    """Lock in the resource-ownership contract of ``aclose()``."""

    @pytest.mark.asyncio
    async def test_owned_client_is_closed(self):
        # When the client creates its own httpx.AsyncClient it must close it.
        client = SidecarHttpClient("http://localhost:5178")
        underlying = client._http_client
        await client.aclose()
        assert underlying.is_closed is True

    @pytest.mark.asyncio
    async def test_injected_client_is_not_closed(self):
        # An injected client is owned by the caller; aclose() must leave it open.
        transport = httpx.MockTransport(lambda request: httpx.Response(200, text="ok"))
        injected = httpx.AsyncClient(transport=transport)
        client = SidecarHttpClient("http://localhost:5178", http_client=injected)
        await client.aclose()
        assert injected.is_closed is False
        await injected.aclose()
