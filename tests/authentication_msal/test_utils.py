import pytest

from microsoft_agents.authentication.msal._utils import (
    _redact_scopes,
    _redact_str,
    _redact_str_or_none,
    _redact_url,
    _redact_url_or_none,
)


class TestRedactionUtils:
    @pytest.mark.parametrize("value", ["", "short", "12345678"])
    def test_redact_str_without_peek(self, value):
        assert _redact_str(value) == "..."

    def test_redact_str_with_peek_for_long_value(self):
        assert _redact_str("client-id-secret", peek=True) == "cl..."

    @pytest.mark.parametrize("value", ["", "short", "12345678"])
    def test_redact_str_with_peek_for_short_values(self, value):
        assert _redact_str(value, peek=True) == "..."

    def test_redact_str_or_none_returns_none_for_none(self):
        assert _redact_str_or_none(None) is None

    def test_redact_str_or_none_redacts_value(self):
        assert _redact_str_or_none("tenant-id-secret", peek=True) == "te..."

    def test_redact_scopes_returns_none_for_none(self):
        assert _redact_scopes(None) is None

    @pytest.mark.parametrize(
        "scopes, expected",
        [
            ([], "... [0 scope(s)]"),
            (["scope1"], "... [1 scope(s)]"),
            (["scope1", "scope2"], "... [2 scope(s)]"),
        ],
    )
    def test_redact_scopes_summarizes_count(self, scopes, expected):
        assert _redact_scopes(scopes) == expected

    @pytest.mark.parametrize(
        "url, expected",
        [
            (
                "https://login.microsoftonline.com/tenant/oauth2/v2.0/token",
                "https://login.microsoftonline.com/...",
            ),
            ("  https://example.com/path?secret=value  ", "https://example.com/..."),
            ("", ""),
            ("   ", ""),
        ],
    )
    def test_redact_url(self, url, expected):
        assert _redact_url(url) == expected

    def test_redact_url_or_none_returns_none_for_none(self):
        assert _redact_url_or_none(None) is None

    def test_redact_url_or_none_redacts_value(self):
        assert (
            _redact_url_or_none("https://example.com/path") == "https://example.com/..."
        )
