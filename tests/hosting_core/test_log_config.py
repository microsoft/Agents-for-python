import json
from unittest.mock import Mock

import pytest

from microsoft_agents.hosting.core import AgentAuthConfiguration
from microsoft_agents.hosting.core.authorization._log_config import (
    _log_config,
    _redact_scopes,
    _redact_str,
    _redact_str_or_none,
    _redact_url,
    _redact_url_or_none,
    _summarize_auth_configs,
    _summarize_connections_map,
)


class TestRedactionUtils:
    @pytest.mark.parametrize("value", ["", "short", "12345678"])
    def test_redact_str_without_peek(self, value):
        assert _redact_str(value) == "..."

    def test_redact_str_with_peek_for_long_value(self):
        assert _redact_str("client-id-secret", peek=True) == "cli..."

    @pytest.mark.parametrize("value", ["", "short", "12345678"])
    def test_redact_str_with_peek_for_short_values(self, value):
        assert _redact_str(value, peek=True) == "..."

    def test_redact_str_or_none_returns_none_for_none(self):
        assert _redact_str_or_none(None) is None

    def test_redact_str_or_none_redacts_value(self):
        assert _redact_str_or_none("tenant-id-secret", peek=True) == "ten..."

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


class TestLogConfig:
    def test_summarize_auth_configs_formats_connections_as_json_array(self):
        summary = _summarize_auth_configs(
            {
                "SERVICE_CONNECTION": AgentAuthConfiguration(
                    client_id="client-id-secret",
                    tenant_id="tenant-id-secret",
                    client_secret="client-secret",
                    connection_name="configured-name",
                    authority="https://login.microsoftonline.com/tenant/oauth2/v2.0/token",
                    scopes=["scope1", "scope2"],
                )
            }
        )

        parsed_summary = json.loads(summary)

        assert parsed_summary == [
            {
                "CONNECTION": "SERVICE_CONNECTION",
                "CONNECTION_NAME": "configured-name",
                "CLIENTID": "cli...",
                "TENANTID": "ten...",
                "CLIENTSECRET": "...",
                "AUTHORITY": "https://login.microsoftonline.com/...",
                "SCOPES": "... [2 scope(s)]",
                "ANONYMOUS_ALLOWED": "False",
            }
        ]
        assert "client-secret" not in summary
        assert "oauth2/v2.0/token" not in summary

    def test_summarize_connections_map_redacts_service_urls(self):
        summary = _summarize_connections_map(
            [
                {
                    "CONNECTION": "SERVICE_CONNECTION",
                    "AUDIENCE": "api://service",
                    "SERVICEURL": "https://service.example.com/path?secret=value",
                },
                {"CONNECTION": "AGENTIC", "SERVICEURL": "*"},
            ]
        )

        parsed_summary = json.loads(summary)

        assert parsed_summary == [
            {
                "CONNECTION": "SERVICE_CONNECTION",
                "AUDIENCE": "api://service",
                "SERVICEURL": "https://service.example.com/...",
            },
            {"CONNECTION": "AGENTIC", "SERVICEURL": "*"},
        ]
        assert "path?secret=value" not in summary

    def test_log_config_uses_clean_parameterized_format(self):
        logger = Mock()
        config_map = {
            "SERVICE_CONNECTION": AgentAuthConfiguration(client_id="client-id-secret")
        }
        connections_map = [{"CONNECTION": "SERVICE_CONNECTION", "SERVICEURL": "*"}]

        _log_config(logger, config_map, connections_map)

        logger.info.assert_called_once()
        message, connections_output, connections_map_output = logger.info.call_args.args
        assert message == "\nConnections:\n%s\n\nConnections Map:\n%s"
        assert json.loads(connections_output)[0]["CONNECTION"] == "SERVICE_CONNECTION"
        assert json.loads(connections_map_output)[0]["CONNECTION"] == (
            "SERVICE_CONNECTION"
        )
