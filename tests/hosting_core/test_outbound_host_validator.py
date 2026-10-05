# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import socket
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from aiohttp import TCPConnector
from aiohttp.abc import ResolveResult
from yarl import URL

from microsoft_agents.hosting.core.security._connector import (
    _SSRFConnector,
    _SSRFError,
)
from microsoft_agents.hosting.core.security._middleware import (
    _validator_middleware,
)
from microsoft_agents.hosting.core.security._utils import (
    _normalize_host,
    _try_create_url,
)
from microsoft_agents.hosting.core.security.outbound_host_validator import (
    OutboundHostValidator,
    _BasicResolveResultValidator,
)


def _resolve_result(
    host: str,
    *,
    hostname: str = "example.com",
    family: int = socket.AF_INET,
    port: int = 443,
) -> ResolveResult:
    return {
        "hostname": hostname,
        "host": host,
        "port": port,
        "family": family,
        "proto": 0,
        "flags": 0,
    }


class TestTryCreateUrl:
    def test_creates_url_from_string(self):
        assert _try_create_url("https://example.com/path") == URL(
            "https://example.com/path"
        )

    def test_returns_existing_url(self):
        url = URL("https://example.com/path")

        assert _try_create_url(url) is url

    @pytest.mark.parametrize(
        "url",
        [
            "http://[invalid",
            "https://example.com:invalid",
            None,
        ],
    )
    def test_returns_none_for_invalid_url(self, url):
        assert _try_create_url(url) is None


class TestNormalizeHost:
    @pytest.mark.parametrize(
        ("host", "expected"),
        [
            ("EXAMPLE.COM", "example.com"),
            ("  example.com  ", "example.com"),
            ("*.example.com", "example.com"),
            ("example.com:443", "example.com"),
            ("example.com/path", "example.com"),
            ("https://Example.COM:443/path", "example.com"),
        ],
    )
    def test_normalizes_host(self, host, expected):
        assert _normalize_host(host) == expected

    @pytest.mark.parametrize("host", ["", " "])
    def test_returns_none_for_empty_normalized_host(self, host):
        assert _normalize_host(host) is None


class TestBasicResolveResultValidator:
    @pytest.mark.parametrize(
        "host",
        [
            "8.8.8.8",
            "2606:4700:4700::1111",
        ],
    )
    def test_allows_global_addresses(self, host):
        validator = _BasicResolveResultValidator()

        assert validator.is_allowed(_resolve_result(host)) is True

    @pytest.mark.parametrize(
        "host",
        [
            "10.0.0.1",
            "127.0.0.1",
            "169.254.169.254",
            "::1",
            "fe80::1",
        ],
    )
    def test_denies_non_global_addresses_by_default(self, host):
        validator = _BasicResolveResultValidator()

        assert validator.is_allowed(_resolve_result(host)) is False

    @pytest.mark.parametrize("host", ["10.0.0.1", "fd00::1"])
    def test_allows_private_addresses_when_configured(self, host):
        validator = _BasicResolveResultValidator(allow_private_network_addresses=True)

        assert validator.is_allowed(_resolve_result(host)) is True

    @pytest.mark.parametrize(
        "resolved",
        [
            _resolve_result("not-an-ip"),
            {
                "hostname": "example.com",
                "host": "",
                "port": 443,
                "family": socket.AF_INET,
                "proto": 0,
                "flags": 0,
            },
        ],
    )
    def test_denies_invalid_resolved_results(self, resolved):
        validator = _BasicResolveResultValidator()

        assert validator.is_allowed(resolved) is False


class TestOutboundHostValidator:
    @pytest.mark.parametrize(
        "url",
        [
            "https://evil.example.com/relay",
            "https://169.254.169.254/latest/meta-data",
            "http://localhost/admin",
            "not-a-uri",
            None,
        ],
    )
    def test_disabled_allows_everything(self, url):
        validator = OutboundHostValidator(enabled=False)

        assert validator.enabled is False
        assert validator.is_allowed(url) is True

    def test_default_options_disable_enforcement(self):
        validator = OutboundHostValidator()

        assert validator.enabled is False
        assert validator.is_allowed("https://evil.example.com/relay") is True

    def test_explicitly_disabled_with_hosts_remains_disabled(self):
        validator = OutboundHostValidator(
            hosts=["contoso.com"],
            enabled=False,
            include_default_microsoft_hosts=False,
        )

        assert validator.enabled is False
        assert validator.is_allowed("https://evil.example.com/relay") is True

    def test_hosts_enable_enforcement_when_enabled_is_unspecified(self):
        validator = OutboundHostValidator(
            hosts=["contoso.com"],
            include_default_microsoft_hosts=False,
        )

        assert validator.enabled is True
        assert validator.is_allowed("https://contoso.com/api") is True
        assert validator.is_allowed("https://evil.example.com/api") is False

    @pytest.mark.parametrize(
        "url",
        [
            "https://smba.trafficmanager.net/teams/",
            "https://graph.microsoft.com/v1.0/me",
            "https://contoso.sharepoint.com/file",
            "https://foo.svc.ms/download",
            "https://account.blob.core.windows.net/container/blob",
            "https://webchat.botframework.com/callback",
        ],
    )
    def test_enabled_allows_first_party_microsoft_hosts(self, url):
        validator = OutboundHostValidator(enabled=True)

        assert validator.is_allowed(url) is True

    @pytest.mark.parametrize(
        "url",
        [
            "https://evil.example.com/relay",
            "https://169.254.169.254/latest/meta-data",
            "https://internal-test.local:8443/secret",
            "http://localhost/admin",
            "https://localhost/admin",
            "https://evil.trafficmanager.net/relay",
            "ftp://graph.microsoft.com/file",
            None,
        ],
    )
    def test_enabled_denies_unknown_or_invalid_urls(self, url):
        validator = OutboundHostValidator(enabled=True)

        assert validator.is_allowed(url) is False

    @pytest.mark.parametrize(
        "configured_host",
        [
            "https://contoso.com",
            "https://contoso.com/some/path",
            "contoso.com:8443",
            "contoso.com/path",
            "*.contoso.com",
        ],
    )
    def test_normalizes_configured_host(self, configured_host):
        validator = OutboundHostValidator(
            hosts=[configured_host],
            include_default_microsoft_hosts=False,
        )

        assert validator.is_allowed("https://contoso.com/api") is True
        assert validator.is_allowed("https://files.contoso.com/api") is True

    def test_allows_configured_host_exact_and_subdomain(self):
        validator = OutboundHostValidator(
            hosts=["contoso.com"],
            include_default_microsoft_hosts=False,
        )

        assert validator.is_allowed("https://contoso.com/api") is True
        assert validator.is_allowed("https://files.contoso.com/api") is True
        assert validator.is_allowed("https://notcontoso.com/api") is False
        assert validator.is_allowed("https://contoso.com.evil.com/api") is False

    def test_can_exclude_default_microsoft_hosts(self):
        validator = OutboundHostValidator(
            hosts=["contoso.com"],
            include_default_microsoft_hosts=False,
        )

        assert validator.is_allowed("https://graph.microsoft.com/v1.0/me") is False
        assert validator.is_allowed("https://contoso.com/x") is True

    def test_host_match_is_case_insensitive(self):
        validator = OutboundHostValidator(enabled=True)

        assert validator.is_allowed("https://GRAPH.MICROSOFT.COM/v1.0/me") is True

    def test_accepts_url_object(self):
        validator = OutboundHostValidator(
            hosts=["example.com"],
            include_default_microsoft_hosts=False,
        )

        assert validator.is_allowed(URL("https://example.com/path")) is True

    def test_rejects_userinfo_host_confusion(self):
        validator = OutboundHostValidator(
            hosts=["example.com"],
            include_default_microsoft_hosts=False,
        )

        assert validator.is_allowed("https://example.com@evil.example/path") is False

    def test_private_ip_literal_requires_both_host_and_private_network_opt_in(self):
        validator = OutboundHostValidator(
            hosts=["10.0.0.1"],
            include_default_microsoft_hosts=False,
            allow_private_network_addresses=True,
        )

        assert validator.is_allowed("https://10.0.0.1/file") is True
        assert validator.is_allowed("https://10.0.0.2/file") is False

    @pytest.mark.asyncio
    async def test_client_uses_ssrf_connector_when_enabled(self):
        validator = OutboundHostValidator(
            hosts=["example.com"],
            include_default_microsoft_hosts=False,
        )

        client = validator.client({"headers": {"X-Test": "value"}})
        try:
            assert isinstance(client.connector, _SSRFConnector)
            assert client.headers["X-Test"] == "value"
            assert len(client._middlewares) == 1
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_client_uses_standard_connector_when_disabled(self):
        validator = OutboundHostValidator(enabled=False)

        client = validator.client()
        try:
            assert isinstance(client.connector, TCPConnector)
            assert not isinstance(client.connector, _SSRFConnector)
            assert client._middlewares == ()
        finally:
            await client.close()

    @pytest.mark.parametrize(
        "option",
        [
            {"connector": Mock()},
            {"connector_owner": False},
            {"middlewares": []},
        ],
    )
    def test_client_rejects_security_sensitive_session_options(self, option):
        validator = OutboundHostValidator(enabled=True)

        with pytest.raises(ValueError):
            validator.client(option)


class TestValidatorMiddleware:
    @pytest.mark.asyncio
    async def test_calls_handler_when_url_is_allowed(self):
        validator = Mock()
        validator.is_allowed.return_value = True
        request = SimpleNamespace(url=URL("https://example.com/file"))
        response = object()
        handler = AsyncMock(return_value=response)

        result = await _validator_middleware(validator)(request, handler)

        assert result is response
        validator.is_allowed.assert_called_once_with(request.url)
        handler.assert_awaited_once_with(request)

    @pytest.mark.asyncio
    async def test_raises_ssrf_error_without_calling_handler_when_url_is_denied(self):
        validator = Mock()
        validator.is_allowed.return_value = False
        request = SimpleNamespace(url=URL("https://evil.example/file"))
        handler = AsyncMock()

        with pytest.raises(_SSRFError, match="evil.example"):
            await _validator_middleware(validator)(request, handler)

        handler.assert_not_awaited()


class TestSSRFConnector:
    @pytest.mark.asyncio
    async def test_returns_all_results_when_validator_allows_them(self, monkeypatch):
        resolved = [
            _resolve_result("8.8.8.8"),
            _resolve_result(
                "2606:4700:4700::1111",
                family=socket.AF_INET6,
            ),
        ]
        traces = [Mock()]
        resolve_host = AsyncMock(return_value=resolved)
        monkeypatch.setattr(TCPConnector, "_resolve_host", resolve_host)
        validator = Mock()
        validator.is_allowed.return_value = True
        connector = _SSRFConnector(validator)

        try:
            result = await connector._resolve_host("example.com", 443, traces)
        finally:
            await connector.close()

        assert result is resolved
        resolve_host.assert_awaited_once_with("example.com", 443, traces)
        assert validator.is_allowed.call_count == 2
        validator.is_allowed.assert_any_call(resolved[0])
        validator.is_allowed.assert_any_call(resolved[1])

    @pytest.mark.asyncio
    async def test_raises_when_any_resolved_result_is_denied(self, monkeypatch):
        resolved = [
            _resolve_result("8.8.8.8"),
            _resolve_result("127.0.0.1"),
        ]
        monkeypatch.setattr(
            TCPConnector,
            "_resolve_host",
            AsyncMock(return_value=resolved),
        )
        validator = Mock()
        validator.is_allowed.side_effect = [True, False]
        connector = _SSRFConnector(validator)

        try:
            with pytest.raises(_SSRFError, match="127.0.0.1"):
                await connector._resolve_host("example.com", 443)
        finally:
            await connector.close()

        assert validator.is_allowed.call_count == 2

    @pytest.mark.asyncio
    async def test_returns_empty_result_without_validation(self, monkeypatch):
        monkeypatch.setattr(
            TCPConnector,
            "_resolve_host",
            AsyncMock(return_value=[]),
        )
        validator = Mock()
        connector = _SSRFConnector(validator)

        try:
            assert await connector._resolve_host("example.com", 443) == []
        finally:
            await connector.close()

        validator.is_allowed.assert_not_called()
