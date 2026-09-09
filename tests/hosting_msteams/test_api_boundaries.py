# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Real upstream clients/models at the extension boundary; no network requests."""

import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 11), reason="Teams API requires Python 3.11+"
)

if sys.version_info >= (3, 11):
    import httpx
    from pydantic import ValidationError
    from microsoft_teams.api import ApiClient
    from microsoft_teams.api.models import (
        ChannelData,
        TaskModuleRequest,
        NotificationInfo,
    )
    from microsoft_agents.activity import Activity
    from microsoft_agents.hosting.msteams._teams_api_client import (
        _get_teams_api_client,
        _set_teams_api_client,
    )
    from microsoft_agents.hosting.msteams._utils import (
        _send_invoke_response,
        _try_get_channel_data,
    )


class Services:
    def __init__(self):
        self.values = {}

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value):
        self.values[key] = value

    def has(self, key):
        return key in self.values


@pytest.mark.asyncio
@pytest.mark.parametrize("authenticated", [False, True])
async def test_client_preserves_headers_url_token_callback_and_per_turn_cache(
    monkeypatch, authenticated
):
    requests = []

    def record(request):
        requests.append(request)
        return httpx.Response(200, json={"ok": True})

    original = httpx.AsyncClient

    def client_with_transport(*args, **kwargs):
        return original(*args, transport=httpx.MockTransport(record), **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", client_with_transport)
    provider = SimpleNamespace(get_access_token=AsyncMock(return_value="test-token"))
    manager = SimpleNamespace(get_token_provider=Mock(return_value=provider))
    identity = object() if authenticated else None
    context = SimpleNamespace(
        services=Services(),
        identity=identity,
        activity=SimpleNamespace(service_url="https://service.example.com/"),
    )
    _set_teams_api_client(context, manager)
    client = _get_teams_api_client(context)
    assert isinstance(client, ApiClient)
    _set_teams_api_client(context, manager)
    assert _get_teams_api_client(context) is client
    try:
        assert client.service_url.rstrip("/") == "https://service.example.com"
        await client.http.get("https://service.example.com/probe")
        assert requests[0].url == "https://service.example.com/probe"
        assert requests[0].headers["accept"] == "application/json"
        assert requests[0].headers["content-type"] == "application/json"
        if authenticated:
            assert requests[0].headers["authorization"] == "Bearer test-token"
            manager.get_token_provider.assert_called_once_with(
                identity, context.activity.service_url
            )
            provider.get_access_token.assert_awaited_once_with(
                "https://api.botframework.com",
                ["https://api.botframework.com/.default"],
            )
        else:
            assert "authorization" not in requests[0].headers
            manager.get_token_provider.assert_not_called()
    finally:
        await client.http.http.aclose()


def test_channel_data_and_request_payload_validation():
    activity = Activity(
        type="event",
        channel_data={
            "eventType": "channelCreated",
            "channel": {"id": "channel-id"},
            "settings": {"selectedChannel": {"id": "selected-id"}},
        },
    )
    data = _try_get_channel_data(activity)
    assert isinstance(data, ChannelData)
    assert data.event_type == "channelCreated"
    assert data.channel.id == "channel-id"
    assert data.settings.selected_channel.id == "selected-id"
    assert TaskModuleRequest.model_validate({"data": {"verb": "save"}}).data == {
        "verb": "save"
    }
    with pytest.raises(ValidationError):
        _try_get_channel_data(
            Activity(type="event", channel_data={"channel": "invalid"})
        )


@pytest.mark.asyncio
async def test_response_serialization_uses_wire_aliases_and_omits_none():
    context = SimpleNamespace(send_activity=AsyncMock())
    response = NotificationInfo(alert=True, alert_in_meeting=True)
    await _send_invoke_response(context, response)
    activity = context.send_activity.await_args.args[0]
    assert activity.value.body == {"alert": True, "alertInMeeting": True}
