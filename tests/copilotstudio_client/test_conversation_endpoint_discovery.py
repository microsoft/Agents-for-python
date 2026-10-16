# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
import json
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock
from urllib.parse import urlsplit

import aiohttp
import pytest

from microsoft_agents.activity import Activity
from microsoft_agents.copilotstudio.client import (
    AgentType,
    ConnectionSettings,
    CopilotClient,
    PowerPlatformCloud,
    PowerPlatformEnvironment,
    StartRequest,
)
from microsoft_agents.copilotstudio.client._conversation_endpoint_discovery import (
    ConversationEndpoints,
    get_discovery_url,
)

HOST = "default5cae182f63ff49f99f353acc2724e73.8.environment.api.test.powerplatform.com"
DISCOVERY_URL = f"https://{HOST}/copilotstudio/agents/test/conversation-endpoints"
ROOT = f"https://{HOST}/copilotstudio/dataverse-backed/authenticated/bots/test/conversations"


@pytest.fixture
def settings():
    return ConnectionSettings(
        "Default-5cae182f-63ff-49f9-9f35-3acc2724e738",
        "test",
        cloud=PowerPlatformCloud.TEST,
    )


@pytest.fixture
def endpoints():
    return {
        "createConversation": ROOT + "?api-version=create&opaque=%2F+%20",
        "executeTurn": ROOT + "/{conversationId}?api-version=execute",
        "continueTurn": ROOT + "/{conversationId}/continue?api-version=continue",
        "subscribe": ROOT + "/{conversationId}/subscribe?api-version=subscribe",
    }


@pytest.fixture
def transport(mocker, endpoints):
    session = MagicMock(spec=aiohttp.ClientSession)
    session.__aenter__.return_value = session
    response = MagicMock(spec=aiohttp.ClientResponse)
    response.status = 200
    response.headers = {}
    response.json = AsyncMock(return_value=endpoints)

    @asynccontextmanager
    async def get(*args, **kwargs):
        yield response

    session.get.side_effect = get
    factory = mocker.patch("aiohttp.ClientSession", return_value=session)
    return session, response, factory


@pytest.mark.parametrize(
    "cloud,suffix",
    [
        (PowerPlatformCloud.TEST, ".8.environment.api.test.powerplatform.com"),
        (PowerPlatformCloud.PROD, ".38.environment.api.powerplatform.com"),
        (PowerPlatformCloud.GOV, ".8.environment.api.gov.powerplatform.microsoft.us"),
        (PowerPlatformCloud.OTHER, ".8.environment.example.com"),
    ],
)
def test_discovery_url_uses_cloud_and_escapes_schema(settings, cloud, suffix):
    settings.cloud = cloud
    settings.custom_power_platform_cloud = "https://example.com"
    settings.agent_identifier = "schema /?#"
    url = urlsplit(get_discovery_url(settings))
    assert url.hostname.endswith(suffix)
    assert url.path == "/copilotstudio/agents/schema%20%2F%3F%23/conversation-endpoints"
    assert not url.query
    assert not url.fragment


@pytest.mark.parametrize("agentic", [False, True])
@pytest.mark.asyncio
async def test_routes_all_operations_and_reuses_discovery(
    settings, endpoints, transport, mocker, agentic
):
    if agentic:
        endpoints.update(
            {
                key: value.replace("/dataverse-backed", "/agenticruntime/3p")
                for key, value in endpoints.items()
            }
        )
    client = CopilotClient(settings, "test-token")
    sent = []

    async def post(url, data, headers):
        sent.append((url, data, headers))
        yield Activity(type="message", text="response", conversation={"id": "a/b ?#"})

    mocker.patch.object(client, "post_request", side_effect=post)
    assert len([item async for item in client.start_conversation()]) == 1
    assert (
        len(
            [
                item
                async for item in client.start_conversation_with_request(StartRequest())
            ]
        )
        == 1
    )
    activity = Activity(type="message", text="question", conversation={"id": "a/b ?#"})
    assert len([item async for item in client.send_activity(activity)]) == 1
    assert len([item async for item in client.execute("a/b ?#", activity)]) == 1
    assert len([item async for item in client.ask_question("question", "a/b ?#")]) == 1

    session, response, _ = transport

    async def content():
        yield b"id: event-1\n"
        yield b"event: activity\n"
        yield b'data: {"type":"message","text":"event"}\n'

    response.content = content()
    events = [event async for event in client.subscribe("a/b ?#", "previous-event")]
    assert events[0].event_id == "event-1"
    assert events[0].activity.text == "event"
    execute_url = endpoints["executeTurn"].replace("{conversationId}", "a%2Fb%20%3F%23")
    assert [item[0] for item in sent] == [
        endpoints["createConversation"],
        endpoints["createConversation"],
        execute_url,
        execute_url,
        execute_url,
    ]
    assert settings.direct_connect_url == endpoints["createConversation"]
    assert session.get.call_count == 2
    discovery_call, subscribe_call = session.get.call_args_list
    assert discovery_call.args == (DISCOVERY_URL,)
    assert discovery_call.kwargs["allow_redirects"] is False
    assert discovery_call.kwargs["headers"]["Authorization"] == "Bearer test-token"
    assert discovery_call.kwargs["headers"]["Accept"] == "application/json"
    assert "agents-sdk-python" in discovery_call.kwargs["headers"]["User-Agent"]
    assert subscribe_call.args == (
        endpoints["subscribe"].replace("{conversationId}", "a%2Fb%20%3F%23"),
    )
    assert subscribe_call.kwargs["headers"]["Last-Event-ID"] == "previous-event"


@pytest.mark.parametrize(
    "operation", ["createConversation", "executeTurn", "continueTurn", "subscribe"]
)
@pytest.mark.parametrize(
    "bad_url",
    [
        None,
        "",
        " ",
        42,
        {},
        "/relative/{conversationId}",
        "http://{host}/conversations/{conversationId}",
        "https://evil.example/conversations/{conversationId}",
        "https://{host}.evil.example/conversations/{conversationId}",
        "https://evilenvironment.api.test.powerplatform.com/{conversationId}",
        "https://{host}:444/conversations/{conversationId}",
        "https://{host}:0/conversations/{conversationId}",
        "https://user:password@{host}/conversations/{conversationId}",
        "https://@{host}/conversations/{conversationId}",
        "https://{host}/conversations/{conversationId}#fragment",
        "https://{host}/conversations/{unknown}",
        "https://{host}/conversations/{conversationId}/{",
        "https://{host}/conversations/{conversationId}/}",
        "https://{host}:invalid/conversations/{conversationId}",
        "https://[invalid/conversations/{conversationId}",
        "https://{host}\\@evil.example/{conversationId}",
        "https://{host}\n.evil.example/{conversationId}",
    ],
)
def test_rejects_invalid_operation_urls(endpoints, operation, bad_url):
    if bad_url is None and operation == "subscribe":
        endpoints["subscribe"] = None
        assert (
            ConversationEndpoints.from_response(endpoints, DISCOVERY_URL).subscribe
            is None
        )
        return
    endpoints[operation] = (
        bad_url.replace("{host}", HOST) if isinstance(bad_url, str) else bad_url
    )
    with pytest.raises(ValueError, match="invalid operation URL"):
        ConversationEndpoints.from_response(endpoints, DISCOVERY_URL)


@pytest.mark.parametrize("data", [None, [], "", 42, True])
def test_rejects_non_object_response(data):
    with pytest.raises(ValueError, match="invalid JSON object"):
        ConversationEndpoints.from_response(data, DISCOVERY_URL)


@pytest.mark.parametrize(
    "operation", ["createConversation", "executeTurn", "continueTurn"]
)
def test_required_operation_missing(endpoints, operation):
    del endpoints[operation]
    with pytest.raises(ValueError, match="invalid operation URL"):
        ConversationEndpoints.from_response(endpoints, DISCOVERY_URL)


@pytest.mark.parametrize("operation", ["executeTurn", "continueTurn", "subscribe"])
def test_conversation_placeholder_is_required(endpoints, operation):
    endpoints[operation] = ROOT + "/conversation"
    with pytest.raises(ValueError, match="invalid operation URL"):
        ConversationEndpoints.from_response(endpoints, DISCOVERY_URL)


def test_create_must_not_contain_conversation_placeholder(endpoints):
    endpoints["createConversation"] = ROOT + "/{conversationId}"
    with pytest.raises(ValueError, match="invalid operation URL"):
        ConversationEndpoints.from_response(endpoints, DISCOVERY_URL)


@pytest.mark.parametrize("missing", [True, False])
@pytest.mark.asyncio
async def test_subscribe_is_optional(settings, endpoints, transport, missing):
    if missing:
        del endpoints["subscribe"]
    else:
        endpoints["subscribe"] = None
    client = CopilotClient(settings, "token")
    assert await client._resolve_connection_url() == endpoints["createConversation"]
    with pytest.raises(NotImplementedError, match="does not advertise"):
        await client._resolve_connection_url("conversation", subscribe=True)
    transport[0].get.assert_called_once()


def test_conversation_id_required_for_operation(endpoints):
    urls = ConversationEndpoints.from_response(endpoints, DISCOVERY_URL)
    for operation in ("executeTurn", "subscribe"):
        with pytest.raises(ValueError, match="conversation ID is required"):
            urls.get_url(operation)


@pytest.mark.asyncio
async def test_allows_other_environment_hosts_in_same_cloud(
    settings, endpoints, transport
):
    endpoints.update(
        {
            key: value.replace(HOST, "other.1.environment.api.test.powerplatform.com")
            for key, value in endpoints.items()
        }
    )
    client = CopilotClient(settings, "token")
    assert await client._resolve_connection_url() == endpoints["createConversation"]


@pytest.mark.asyncio
async def test_concurrent_calls_share_discovery(settings, endpoints, transport):
    entered = asyncio.Event()
    release = asyncio.Event()

    async def read_json():
        entered.set()
        await release.wait()
        return endpoints

    transport[1].json.side_effect = read_json
    client = CopilotClient(settings, "token")
    first = asyncio.create_task(client._resolve_connection_url())
    await entered.wait()
    second = asyncio.create_task(client._resolve_connection_url("conversation"))
    release.set()
    results = await asyncio.gather(first, second)
    assert results == [
        endpoints["createConversation"],
        endpoints["executeTurn"].replace("{conversationId}", "conversation"),
    ]
    transport[0].get.assert_called_once()


@pytest.mark.parametrize("status", [301, 302, 401, 403, 404, 500])
@pytest.mark.asyncio
async def test_http_failure_is_explicit_and_retryable(
    settings, endpoints, transport, status
):
    client = CopilotClient(settings, "token")
    transport[1].status = status
    with pytest.raises(aiohttp.ClientResponseError) as error:
        await client._resolve_connection_url()
    assert error.value.status == status
    assert settings.direct_connect_url is None
    transport[1].status = 200
    assert await client._resolve_connection_url() == endpoints["createConversation"]
    assert transport[0].get.call_count == 2


@pytest.mark.parametrize("invalid", ["json", "content-type", "endpoints", "empty"])
@pytest.mark.asyncio
async def test_invalid_response_is_retryable(settings, endpoints, transport, invalid):
    client = CopilotClient(settings, "token")
    if invalid == "json":
        transport[1].json.side_effect = json.JSONDecodeError("invalid", "x", 0)
    elif invalid == "content-type":
        transport[1].json.side_effect = aiohttp.ContentTypeError(
            MagicMock(), (), message="Not JSON"
        )
    else:
        transport[1].json.return_value = (
            {"createConversation": "https://evil.example"}
            if invalid == "endpoints"
            else None
        )
    with pytest.raises(ValueError):
        await client._resolve_connection_url()
    assert settings.direct_connect_url is None
    transport[1].json.side_effect = None
    transport[1].json.return_value = endpoints
    assert await client._resolve_connection_url() == endpoints["createConversation"]


@pytest.mark.parametrize("token", ["", " \t", None])
@pytest.mark.asyncio
async def test_empty_token_fails_before_network(settings, transport, token):
    client = CopilotClient(settings, token)
    with pytest.raises(ValueError, match="non-empty access token"):
        await client._resolve_connection_url()
    transport[2].assert_not_called()


@pytest.mark.parametrize("bypass", ["direct", "prebuilt"])
@pytest.mark.asyncio
async def test_direct_and_prebuilt_bypass_discovery(settings, transport, bypass):
    if bypass == "direct":
        settings.direct_connect_url = "https://custom.example/bot"
    else:
        settings.copilot_agent_type = AgentType.PREBUILT
    client = CopilotClient(settings, "")
    for conversation_id, subscribe in [(None, False), ("conv", False), ("conv", True)]:
        expected = PowerPlatformEnvironment.get_copilot_studio_connection_url(
            settings, conversation_id, create_subscribe_link=subscribe
        )
        assert (
            await client._resolve_connection_url(conversation_id, subscribe) == expected
        )
    transport[2].assert_not_called()


@pytest.mark.asyncio
async def test_explicit_url_override_and_clearing_trigger_correct_routing(
    settings, endpoints, transport
):
    client = CopilotClient(settings, "token")
    await client._resolve_connection_url()
    settings.direct_connect_url = "https://custom.example/bot?original=query"
    expected = PowerPlatformEnvironment.get_copilot_studio_connection_url(
        settings, "id"
    )
    assert await client._resolve_connection_url("id") == expected
    transport[0].get.assert_called_once()
    settings.direct_connect_url = ""
    assert await client._resolve_connection_url() == endpoints["createConversation"]
    assert transport[0].get.call_count == 2


@pytest.mark.parametrize("change", ["direct", "prebuilt"])
@pytest.mark.asyncio
async def test_settings_changed_during_discovery_are_preserved(
    settings, endpoints, transport, change
):
    async def read_json():
        if change == "direct":
            settings.direct_connect_url = "https://custom.example/bot"
        else:
            settings.copilot_agent_type = AgentType.PREBUILT
        return endpoints

    transport[1].json.side_effect = read_json
    client = CopilotClient(settings, "token")
    url = await client._resolve_connection_url("conversation")
    assert url == PowerPlatformEnvironment.get_copilot_studio_connection_url(
        settings, "conversation"
    )
    assert client._discovered_endpoints is None


@pytest.mark.asyncio
async def test_cancellation_releases_discovery_lock(settings, endpoints, transport):
    entered = asyncio.Event()
    blocked = asyncio.Event()

    async def read_json():
        entered.set()
        await blocked.wait()
        return endpoints

    transport[1].json.side_effect = read_json
    client = CopilotClient(settings, "token")
    task = asyncio.create_task(client._resolve_connection_url())
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert settings.direct_connect_url is None
    transport[1].json.side_effect = None
    assert await client._resolve_connection_url() == endpoints["createConversation"]


@pytest.mark.asyncio
async def test_session_options_are_honored(settings, transport):
    timeout = aiohttp.ClientTimeout(total=30)
    settings.client_session_settings = {"timeout": timeout}
    await CopilotClient(settings, "token")._resolve_connection_url()
    transport[2].assert_called_once_with(timeout=timeout)


@pytest.mark.asyncio
async def test_discovery_state_is_per_client(settings, endpoints, transport):
    first = CopilotClient(settings, "first-token")
    await first._resolve_connection_url()
    other_settings = ConnectionSettings(
        settings.environment_id, settings.agent_identifier, cloud=settings.cloud
    )
    second = CopilotClient(other_settings, "second-token")
    await second._resolve_connection_url()
    assert transport[0].get.call_count == 2
    assert (
        transport[0].get.call_args_list[1].kwargs["headers"]["Authorization"]
        == "Bearer second-token"
    )


def test_explicit_default_https_port_is_allowed(endpoints):
    endpoints["executeTurn"] = endpoints["executeTurn"].replace(HOST, HOST + ":443")
    urls = ConversationEndpoints.from_response(endpoints, DISCOVERY_URL)
    assert ":443/" in urls.get_url("executeTurn", "id")


@pytest.mark.asyncio
async def test_transport_failure_is_retryable(settings, endpoints, transport):
    client = CopilotClient(settings, "token")
    transport[0].get.side_effect = aiohttp.ClientConnectionError("connection failed")
    with pytest.raises(aiohttp.ClientConnectionError, match="connection failed"):
        await client._resolve_connection_url()
    assert settings.direct_connect_url is None

    @asynccontextmanager
    async def get(*args, **kwargs):
        yield transport[1]

    transport[0].get.side_effect = get
    assert await client._resolve_connection_url() == endpoints["createConversation"]
