# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from http import HTTPStatus

import pytest

from microsoft_agents.activity import Activity
from microsoft_agents.hosting.core import (
    ChannelServiceClientFactoryBase,
    ClaimsIdentity,
    HttpAdapterBase,
)


class _ConcreteHttpAdapter(HttpAdapterBase):
    pass


def _make_activity(service_url: str | None) -> Activity:
    activity = Activity(
        type="message",
        id="activity-1",
        channel_id="msteams",
        conversation={"id": "conversation-1"},
        from_property={"id": "user-1"},
        recipient={"id": "agent-1"},
    )
    if service_url is not None:
        activity.service_url = service_url
    return activity


def _make_request(
    mocker, claims_service_url: str | None, activity_service_url: str | None
):
    request = mocker.Mock()
    request.method = "POST"
    request.json = mocker.AsyncMock(
        return_value=_make_activity(activity_service_url).model_dump(
            by_alias=True, exclude_none=True
        )
    )
    request.get_claims_identity.return_value = ClaimsIdentity(
        claims={"serviceurl": claims_service_url} if claims_service_url else {}
    )
    return request


def _make_adapter(mocker):
    connector_client = mocker.AsyncMock()
    user_token_client = mocker.AsyncMock()
    factory = mocker.Mock(spec=ChannelServiceClientFactoryBase)
    factory.create_connector_client = mocker.AsyncMock(return_value=connector_client)
    factory.create_user_token_client = mocker.AsyncMock(return_value=user_token_client)
    return _ConcreteHttpAdapter(channel_service_client_factory=factory), factory


@pytest.mark.asyncio
async def test_rejects_service_url_origin_mismatch_before_client_creation(mocker):
    adapter, factory = _make_adapter(mocker)
    agent = mocker.Mock()
    agent.on_turn = mocker.AsyncMock()
    request = _make_request(
        mocker,
        claims_service_url="https://trusted.example/claims-path",
        activity_service_url="https://different.example/activity-path",
    )

    response = await adapter.process_request(request, agent)

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    factory.create_user_token_client.assert_not_awaited()
    factory.create_connector_client.assert_not_awaited()
    agent.on_turn.assert_not_awaited()


@pytest.mark.asyncio
async def test_accepts_matching_service_url_origin(mocker):
    adapter, factory = _make_adapter(mocker)
    agent = mocker.Mock()
    agent.on_turn = mocker.AsyncMock()
    request = _make_request(
        mocker,
        claims_service_url="https://trusted.example/claims-path",
        activity_service_url="https://trusted.example/activity-path",
    )

    response = await adapter.process_request(request, agent)

    assert response.status_code == HTTPStatus.ACCEPTED
    factory.create_user_token_client.assert_awaited_once()
    factory.create_connector_client.assert_awaited_once()
    agent.on_turn.assert_awaited_once()


@pytest.mark.parametrize(
    "claims_service_url, activity_service_url",
    [
        ("https://trusted.example/path", "http://trusted.example/path"),
        ("https://trusted.example/path", "https://trusted.example:444/path"),
        ("https://trusted.example/path", "https://different.example/path"),
        ("https://trusted.example/path", "relative/path"),
        ("https://trusted.example/path", "ftp://trusted.example/path"),
        ("https://trusted.example/path", "https://trusted.example:invalid/path"),
        ("not a URL", "https://trusted.example/path"),
        (123, "https://trusted.example/path"),
    ],
)
@pytest.mark.asyncio
async def test_process_activity_rejects_mismatched_or_invalid_origins_before_clients(
    mocker, claims_service_url, activity_service_url
):
    adapter, factory = _make_adapter(mocker)
    callback = mocker.AsyncMock()
    claims_identity = ClaimsIdentity(claims={"serviceurl": claims_service_url})

    with pytest.raises(PermissionError):
        await adapter.process_activity(
            claims_identity,
            _make_activity(activity_service_url),
            callback,
        )

    factory.create_user_token_client.assert_not_awaited()
    factory.create_connector_client.assert_not_awaited()
    callback.assert_not_awaited()


@pytest.mark.parametrize(
    "claims_service_url, activity_service_url",
    [
        ("https://trusted.example:443/claims", "https://TRUSTED.EXAMPLE/activity"),
        ("http://trusted.example/claims", "http://trusted.example:80/activity"),
        (None, "https://activity.example/path"),
        ("https://trusted.example/path", None),
    ],
)
@pytest.mark.asyncio
async def test_process_activity_accepts_matching_origins_and_missing_claims(
    mocker, claims_service_url, activity_service_url
):
    adapter, factory = _make_adapter(mocker)
    callback = mocker.AsyncMock()
    claims_identity = ClaimsIdentity(
        claims={"serviceurl": claims_service_url} if claims_service_url else {}
    )

    await adapter.process_activity(
        claims_identity,
        _make_activity(activity_service_url),
        callback,
    )

    factory.create_user_token_client.assert_awaited_once()
    factory.create_connector_client.assert_awaited_once()
    callback.assert_awaited_once()
