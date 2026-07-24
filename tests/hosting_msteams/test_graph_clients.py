# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for Microsoft Graph client creation helpers in Teams hosting."""

from types import SimpleNamespace

import pytest

from .helpers import is_supported_version

pytestmark = pytest.mark.skipif(
    not is_supported_version,
    reason="microsoft-agents-hosting-teams tests require Python 3.11+",
)

if is_supported_version:
    from kiota_abstractions.method import Method
    from kiota_abstractions.request_information import RequestInformation

    from microsoft_agents.activity import TokenResponse
    from microsoft_agents.hosting.msteams._graph import (
        _common_get_app_graph_client,
        _common_get_app_graph_client_for_connection,
        _create_app_graph_service_client,
        _create_user_graph_service_client,
    )


class _RecordingAuthorization:
    def __init__(self):
        self.calls = []

    async def get_token(self, context, handler_name):
        self.calls.append((context, handler_name))
        return TokenResponse(token="delegated-token")


class _RecordingTokenProvider:
    def __init__(self):
        self.calls = []

    async def get_access_token(
        self, resource_url: str, scopes: list[str], force_refresh: bool = False
    ) -> str:
        self.calls.append((resource_url, scopes, force_refresh))
        return "app-token"


class _RecordingConnectionManager:
    def __init__(self):
        self.default_provider = _RecordingTokenProvider()
        self.named_provider = _RecordingTokenProvider()
        self.turn_provider = _RecordingTokenProvider()
        self.calls = []

    def get_token_provider(self, identity, service_url):
        self.calls.append(("get_token_provider", identity, service_url))
        return self.turn_provider

    def get_connection(self, connection_name):
        self.calls.append(("get_connection", connection_name))
        return self.named_provider

    def get_default_connection(self):
        self.calls.append(("get_default_connection",))
        return self.default_provider


@pytest.mark.asyncio
async def test_delegated_graph_client_gets_token_from_authorization_handler():
    authorization = _RecordingAuthorization()
    context = SimpleNamespace()
    app = SimpleNamespace(auth=authorization)
    graph = _create_user_graph_service_client(app, context, "GRAPH")
    request = RequestInformation()
    request.http_method = Method.GET
    request.url = "https://graph.microsoft.com/v1.0/me"

    native_request = await graph.request_adapter.convert_to_native_async(request)

    assert authorization.calls == [(context, "GRAPH")]
    assert "authorization" in native_request.headers


def test_delegated_graph_client_uses_custom_graph_base_url():
    authorization = _RecordingAuthorization()
    context = SimpleNamespace()
    app = SimpleNamespace(auth=authorization)
    graph = _create_user_graph_service_client(
        app,
        context,
        graph_base_url="https://graph.microsoft.us/v1.0",
    )

    assert graph.request_adapter.base_url == "https://graph.microsoft.us/v1.0/"


@pytest.mark.asyncio
async def test_app_graph_client_uses_default_scope_for_custom_graph_cloud():
    token_provider = _RecordingTokenProvider()
    graph = _create_app_graph_service_client(
        token_provider,
        "https://graph.microsoft.us/v1.0",
    )
    request = RequestInformation()
    request.http_method = Method.GET
    request.url = "https://graph.microsoft.us/v1.0/applications"

    native_request = await graph.request_adapter.convert_to_native_async(request)

    assert token_provider.calls == [
        (
            "https://graph.microsoft.us",
            ["https://graph.microsoft.us/.default"],
            False,
        )
    ]
    assert "authorization" in native_request.headers


def test_context_app_graph_client_resolves_connection_from_turn_identity_and_service_url():
    connection_manager = _RecordingConnectionManager()
    app = SimpleNamespace(connection_manager=connection_manager)
    identity = SimpleNamespace()
    context = SimpleNamespace(
        identity=identity,
        activity=SimpleNamespace(service_url="https://smba.trafficmanager.net/teams/"),
    )

    graph = _common_get_app_graph_client(app, context)

    assert graph.request_adapter.base_url == "https://graph.microsoft.com/v1.0/"
    assert connection_manager.calls == [
        (
            "get_token_provider",
            identity,
            "https://smba.trafficmanager.net/teams/",
        )
    ]


def test_named_app_graph_client_uses_named_connection():
    connection_manager = _RecordingConnectionManager()
    app = SimpleNamespace(connection_manager=connection_manager)

    graph = _common_get_app_graph_client_for_connection(app, "SERVICE_CONNECTION_2")

    assert graph.request_adapter.base_url == "https://graph.microsoft.com/v1.0/"
    assert connection_manager.calls == [
        ("get_connection", "SERVICE_CONNECTION_2"),
    ]


def test_default_app_graph_client_uses_default_connection_when_name_is_omitted():
    connection_manager = _RecordingConnectionManager()
    app = SimpleNamespace(connection_manager=connection_manager)

    graph = _common_get_app_graph_client_for_connection(app, None)

    assert graph.request_adapter.base_url == "https://graph.microsoft.com/v1.0/"
    assert connection_manager.calls == [
        ("get_default_connection",),
    ]
