# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.hosting.core import (
    AgentAuthConfiguration,
    AccessTokenProviderBase,
    ClaimsIdentity,
    ConnectionManager,
)


class FakeProvider(AccessTokenProviderBase):
    """Minimal provider that records the configuration it was built from."""

    def __init__(self, configuration: AgentAuthConfiguration):
        self._configuration = configuration

    @property
    def configuration(self) -> AgentAuthConfiguration:
        return self._configuration

    async def get_access_token(self, resource_url, scopes, force_refresh=False):
        return "fake-token"


ENV_CONFIG = {
    "CONNECTIONS": {
        "SERVICE_CONNECTION": {
            "SETTINGS": {
                "CLIENTID": "client-service",
                "TENANTID": "tenant-service",
            }
        },
        "AGENTIC": {"SETTINGS": {"CLIENTID": "client-agentic"}},
        "MISC": {"SETTINGS": {"CLIENTID": "client-misc"}},
    },
    "CONNECTIONSMAP": [
        {"CONNECTION": "AGENTIC", "SERVICEURL": "agentic"},
        {"CONNECTION": "MISC", "AUDIENCE": "api://misc", "SERVICEURL": "*"},
        {
            "CONNECTION": "SERVICE_CONNECTION",
            "AUDIENCE": "api://service",
            "SERVICEURL": "https://service*",
        },
        {"CONNECTION": "MISC", "SERVICEURL": "https://microsoft.com/*"},
    ],
}


class TestGenericConnectionManager:
    def _make(self, **kwargs):
        return ConnectionManager(provider_factory=FakeProvider, **kwargs)

    def test_uses_provider_factory(self):
        cm = self._make(**ENV_CONFIG)
        provider = cm.get_default_connection()
        assert isinstance(provider, FakeProvider)
        assert provider.configuration.CLIENT_ID == "client-service"

    def test_requires_service_connection(self):
        bad = {"CONNECTIONS": {"MISC": {"SETTINGS": {"CLIENTID": "x"}}}}
        with pytest.raises(ValueError):
            self._make(**bad)

    def test_get_connection_unknown_raises(self):
        cm = self._make(**ENV_CONFIG)
        with pytest.raises(ValueError):
            cm.get_connection("DOES_NOT_EXIST")

    def test_get_connection_none_defaults_to_service(self):
        cm = self._make(**ENV_CONFIG)
        assert cm.get_connection(None) is cm.get_default_connection()

    def test_token_provider_aud_and_service_url_match(self):
        cm = self._make(**ENV_CONFIG)
        claims = ClaimsIdentity(claims={"aud": "api://service"}, is_authenticated=True)
        assert cm.get_token_provider(
            claims, "https://service.com/api"
        ) is cm.get_connection("SERVICE_CONNECTION")

    def test_token_provider_service_url_match(self):
        cm = self._make(**ENV_CONFIG)
        claims = ClaimsIdentity(claims={}, is_authenticated=False)
        assert cm.get_token_provider(claims, "agentic") is cm.get_connection("AGENTIC")

    def test_service_url_is_regex_unanchored(self):
        # SERVICEURL is a regex matched with re.search (mirrors .NET Regex.Match),
        # so a bare substring pattern matches anywhere in the service URL.
        cm = self._make(**ENV_CONFIG)
        claims = ClaimsIdentity(claims={}, is_authenticated=False)
        assert cm.get_token_provider(
            claims, "https://host/agentic/path"
        ) is cm.get_connection("AGENTIC")

    def test_service_url_regex_dot_is_wildcard(self):
        # '.' in a SERVICEURL regex is a wildcard (regex semantics, matching .NET),
        # so "https://microsoft.com/*" also matches a host like "microsoftXcom".
        cm = self._make(**ENV_CONFIG)
        claims = ClaimsIdentity(claims={}, is_authenticated=False)
        assert cm.get_token_provider(
            claims, "https://microsoftXcom/foo"
        ) is cm.get_connection("MISC")

    def test_invalid_service_url_regex_raises_clear_value_error(self):
        # A malformed SERVICEURL regex must surface as a clear ValueError, not an
        # opaque re.error crashing provider selection.
        config = {
            "CONNECTIONS": {"SERVICE_CONNECTION": {"SETTINGS": {"CLIENTID": "x"}}},
            "CONNECTIONSMAP": [{"CONNECTION": "SERVICE_CONNECTION", "SERVICEURL": "["}],
        }
        cm = self._make(**config)
        claims = ClaimsIdentity(claims={}, is_authenticated=False)
        with pytest.raises(ValueError, match="Invalid SERVICEURL regex"):
            cm.get_token_provider(claims, "https://example.com")

    def test_token_provider_no_map_returns_default(self):
        config = {k: v for k, v in ENV_CONFIG.items() if k != "CONNECTIONSMAP"}
        cm = self._make(**config)
        claims = ClaimsIdentity(claims={"aud": "api://misc"}, is_authenticated=True)
        assert (
            cm.get_token_provider(claims, "https://example.com")
            is cm.get_default_connection()
        )

    @pytest.mark.parametrize(
        "claims, service_url",
        [
            [None, ""],
            [ClaimsIdentity(claims={}, is_authenticated=False), None],
            [ClaimsIdentity(claims={"aud": "api://misc"}, is_authenticated=False), ""],
        ],
    )
    def test_token_provider_errors(self, claims, service_url):
        cm = self._make(**ENV_CONFIG)
        with pytest.raises(ValueError):
            cm.get_token_provider(claims, service_url)

    def test_default_connection_configuration(self):
        cm = self._make(**ENV_CONFIG)
        config = cm.get_default_connection_configuration()
        assert config.CLIENT_ID == "client-service"

    def test_default_connections_map_is_empty_list(self):
        config = {k: v for k, v in ENV_CONFIG.items() if k != "CONNECTIONSMAP"}
        cm = self._make(**config)
        assert cm._connections_map == []
        assert isinstance(cm._connections_map, list)

    def test_explicit_empty_connections_map_overrides_kwargs(self):
        # An explicit empty map must win over a CONNECTIONSMAP kwarg and disable
        # URL-based routing (falling back to the default connection).
        cm = ConnectionManager(
            provider_factory=FakeProvider,
            connections_map=[],
            **ENV_CONFIG,
        )
        assert cm._connections_map == []
        claims = ClaimsIdentity(claims={"aud": "api://service"}, is_authenticated=True)
        assert (
            cm.get_token_provider(claims, "https://service.com/api")
            is cm.get_default_connection()
        )
