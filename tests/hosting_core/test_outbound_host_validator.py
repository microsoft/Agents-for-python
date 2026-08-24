# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from yarl import URL

from microsoft_agents.hosting.core.outbound_host_validator import (
    OutboundHostValidator,
    _normalize,
    _try_create_url,
)


class TestTryCreateUrl:
    def test_creates_url_from_string(self):
        assert _try_create_url("https://example.com/path") == URL(
            "https://example.com/path"
        )

    def test_returns_existing_url(self):
        url = URL("https://example.com/path")

        assert _try_create_url(url) is url

    @pytest.mark.parametrize("url", ["http://[invalid", "https://example.com:invalid"])
    def test_returns_none_for_invalid_url(self, url):
        assert _try_create_url(url) is None


class TestNormalize:
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
        assert _normalize(host) == expected

    @pytest.mark.parametrize("host", ["", " "])
    def test_returns_none_for_empty_normalized_host(self, host):
        assert _normalize(host) is None


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

        assert validator.enabled is True
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
        ],
    )
    def test_enabled_denies_unknown_hosts(self, url):
        validator = OutboundHostValidator(enabled=True)

        assert validator.is_allowed(url) is False

    @pytest.mark.parametrize(
        "configured_host",
        [
            "https://contoso.com",
            "https://contoso.com/some/path",
            "contoso.com:8443",
            "contoso.com/path",
        ],
    )
    def test_enabled_normalizes_configured_host(self, configured_host):
        validator = OutboundHostValidator(enabled=True, hosts=[configured_host])

        assert validator.is_allowed("https://contoso.com/api") is True
        assert validator.is_allowed("https://files.contoso.com/api") is True

    def test_enabled_allows_configured_host_exact_and_subdomain(self):
        validator = OutboundHostValidator(enabled=True, hosts=["contoso.com"])

        assert validator.is_allowed("https://contoso.com/api") is True
        assert validator.is_allowed("https://files.contoso.com/api") is True
        assert validator.is_allowed("https://notcontoso.com/api") is False
        assert validator.is_allowed("https://contoso.com.evil.com/api") is False

    def test_enabled_accepts_wildcard_prefix_in_configured_host(self):
        validator = OutboundHostValidator(enabled=True, hosts=["*.fabrikam.com"])

        assert validator.is_allowed("https://api.fabrikam.com/x") is True
        assert validator.is_allowed("https://fabrikam.com/x") is True

    def test_enabled_without_defaults_denies_microsoft_hosts(self):
        validator = OutboundHostValidator(
            enabled=True,
            hosts=["contoso.com"],
            include_default_microsoft_hosts=False,
        )

        assert validator.is_allowed("https://graph.microsoft.com/v1.0/me") is False
        assert validator.is_allowed("https://contoso.com/x") is True

    def test_enabled_host_match_is_case_insensitive(self):
        validator = OutboundHostValidator(enabled=True)

        assert validator.is_allowed("https://GRAPH.MICROSOFT.COM/v1.0/me") is True

    @pytest.mark.parametrize(
        "url",
        [
            "not-a-uri",
            "/relative/path",
            None,
        ],
    )
    def test_enabled_denies_non_absolute_or_invalid_urls(self, url):
        validator = OutboundHostValidator(enabled=True)

        assert validator.is_allowed(url) is False

    def test_accepts_url_object(self):
        validator = OutboundHostValidator(
            enabled=True,
            hosts=["example.com"],
            include_default_microsoft_hosts=False,
        )

        assert validator.is_allowed(URL("https://example.com/path")) is True

    def test_rejects_userinfo_host_confusion(self):
        validator = OutboundHostValidator(
            enabled=True,
            hosts=["example.com"],
            include_default_microsoft_hosts=False,
        )

        assert validator.is_allowed("https://example.com@evil.example/path") is False
