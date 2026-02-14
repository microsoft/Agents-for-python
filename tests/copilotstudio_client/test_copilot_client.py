import pytest

from contextlib import asynccontextmanager

from microsoft_agents.activity import Activity

from microsoft_agents.copilotstudio.client import (
    ConnectionSettings,
    CopilotClient,
    PowerPlatformEnvironment,
    StartRequest,
    SubscribeEvent,
    UserAgentHelper,
)

from aiohttp import ClientSession, ClientError
from urllib.parse import urlparse

@pytest.mark.asyncio
async def test_copilot_client_error(mocker):
    # Define the connection settings
    connection_settings = ConnectionSettings(
        "environment-id",
        "agent-id",
        client_session_settings={"base_url": "https://api.copilotstudio.com"},
    )

    mock_session = mocker.MagicMock(spec=ClientSession)
    mock_session.__aenter__.return_value = mock_session

    @asynccontextmanager
    async def response():
        mock_response = mocker.Mock()
        mock_response.status = 401
        yield mock_response

    mock_session.post.return_value = response()

    mocker.patch("aiohttp.ClientSession", return_value=mock_session)

    # Create a CopilotClient instance
    copilot_client = CopilotClient(connection_settings, "token")

    with pytest.raises(ClientError):
        async for message in copilot_client.start_conversation():
            # Process the message received from the conversation
            print(message)


@pytest.mark.asyncio
async def test_copilot_client_basic(mocker):
    # Define the connection settings
    connection_settings = ConnectionSettings(
        "environment-id",
        "agent-id",
        client_session_settings={"base_url": "https://api.copilotstudio.com"},
    )

    mock_session = mocker.MagicMock(spec=ClientSession)
    mock_session.__aenter__.return_value = mock_session

    @asynccontextmanager
    async def response():
        mock_response = mocker.Mock()
        mock_response.status = 200

        activity = Activity(
            type="message", text="Hello, world!", conversation={"id": "1234567890"}
        )
        activity_json = activity.model_dump_json(exclude_unset=True)

        async def content():
            yield "event: activity".encode()
            yield f"data: {activity_json}".encode()

        mock_response.content = content()

        yield mock_response

    mock_session.post.return_value = response()

    mocker.patch("aiohttp.ClientSession", return_value=mock_session)

    # Create a CopilotClient instance
    copilot_client = CopilotClient(connection_settings, "token")

    count = 0
    async for message in copilot_client.start_conversation():
        count += 1
        assert message.type == "message"
        assert message.text == "Hello, world!"
        assert message.conversation.id == "1234567890"

    assert count == 1


@pytest.mark.asyncio
async def test_copilot_client_start_with_request(mocker):
    # Define the connection settings
    connection_settings = ConnectionSettings(
        "environment-id",
        "agent-id",
        client_session_settings={"base_url": "https://api.copilotstudio.com"},
    )

    mock_session = mocker.MagicMock(spec=ClientSession)
    mock_session.__aenter__.return_value = mock_session

    @asynccontextmanager
    async def response():
        mock_response = mocker.Mock()
        mock_response.status = 200

        activity = Activity(
            type="message", text="Hello from start request!", conversation={"id": "123"}
        )
        activity_json = activity.model_dump_json(exclude_unset=True)

        async def content():
            yield "event: activity".encode()
            yield f"data: {activity_json}".encode()

        mock_response.content = content()

        yield mock_response

    mock_session.post.return_value = response()

    mocker.patch("aiohttp.ClientSession", return_value=mock_session)

    # Create a CopilotClient instance
    copilot_client = CopilotClient(connection_settings, "token")

    # Create a start request
    start_request = StartRequest(
        emit_start_conversation_event=True, locale="en-US", conversation_id="123"
    )

    count = 0
    async for message in copilot_client.start_conversation_with_request(start_request):
        count += 1
        assert message.type == "message"
        assert message.text == "Hello from start request!"
        assert message.conversation.id == "123"

    assert count == 1


@pytest.mark.asyncio
async def test_copilot_client_send_activity(mocker):
    # Define the connection settings
    connection_settings = ConnectionSettings(
        "environment-id",
        "agent-id",
        client_session_settings={"base_url": "https://api.copilotstudio.com"},
    )

    mock_session = mocker.MagicMock(spec=ClientSession)
    mock_session.__aenter__.return_value = mock_session

    @asynccontextmanager
    async def response():
        mock_response = mocker.Mock()
        mock_response.status = 200

        activity = Activity(
            type="message", text="Response to activity", conversation={"id": "456"}
        )
        activity_json = activity.model_dump_json(exclude_unset=True)

        async def content():
            yield "event: activity".encode()
            yield f"data: {activity_json}".encode()

        mock_response.content = content()

        yield mock_response

    mock_session.post.return_value = response()

    mocker.patch("aiohttp.ClientSession", return_value=mock_session)

    # Create a CopilotClient instance
    copilot_client = CopilotClient(connection_settings, "token")

    # Create an activity to send
    activity = Activity(type="message", text="Test message", conversation={"id": "456"})

    count = 0
    async for message in copilot_client.send_activity(activity):
        count += 1
        assert message.type == "message"
        assert message.text == "Response to activity"

    assert count == 1


@pytest.mark.asyncio
async def test_copilot_client_execute(mocker):
    # Define the connection settings
    connection_settings = ConnectionSettings(
        "environment-id",
        "agent-id",
        client_session_settings={"base_url": "https://api.copilotstudio.com"},
    )

    mock_session = mocker.MagicMock(spec=ClientSession)
    mock_session.__aenter__.return_value = mock_session

    @asynccontextmanager
    async def response():
        mock_response = mocker.Mock()
        mock_response.status = 200

        activity = Activity(
            type="message", text="Execute response", conversation={"id": "789"}
        )
        activity_json = activity.model_dump_json(exclude_unset=True)

        async def content():
            yield "event: activity".encode()
            yield f"data: {activity_json}".encode()

        mock_response.content = content()

        yield mock_response

    mock_session.post.return_value = response()

    mocker.patch("aiohttp.ClientSession", return_value=mock_session)

    # Create a CopilotClient instance
    copilot_client = CopilotClient(connection_settings, "token")

    # Create an activity to execute
    activity = Activity(type="message", text="Execute message")

    count = 0
    async for message in copilot_client.execute("789", activity):
        count += 1
        assert message.type == "message"
        assert message.text == "Execute response"
        assert message.conversation.id == "789"

    assert count == 1


@pytest.mark.asyncio
async def test_copilot_client_subscribe(mocker):
    # Define the connection settings
    connection_settings = ConnectionSettings(
        "environment-id",
        "agent-id",
        client_session_settings={"base_url": "https://api.copilotstudio.com"},
    )

    mock_session = mocker.MagicMock(spec=ClientSession)
    mock_session.__aenter__.return_value = mock_session

    @asynccontextmanager
    async def response():
        mock_response = mocker.Mock()
        mock_response.status = 200

        activity = Activity(
            type="message", text="Subscribe event", conversation={"id": "999"}
        )
        activity_json = activity.model_dump_json(exclude_unset=True)

        async def content():
            yield "id: event-123".encode()
            yield "event: activity".encode()
            yield f"data: {activity_json}".encode()

        mock_response.content = content()

        yield mock_response

    mock_session.get.return_value = response()

    mocker.patch("aiohttp.ClientSession", return_value=mock_session)

    # Create a CopilotClient instance
    copilot_client = CopilotClient(connection_settings, "token")

    count = 0
    async for subscribe_event in copilot_client.subscribe("999"):
        count += 1
        assert isinstance(subscribe_event, SubscribeEvent)
        assert subscribe_event.activity.type == "message"
        assert subscribe_event.activity.text == "Subscribe event"
        assert subscribe_event.event_id == "event-123"

    assert count == 1


def test_user_agent_helper():
    user_agent = UserAgentHelper.get_user_agent_header()
    assert "CopilotStudioClient.agents-sdk-python" in user_agent
    assert "Python/" in user_agent


def test_start_request():
    start_request = StartRequest(
        emit_start_conversation_event=True, locale="en-US", conversation_id="test-123"
    )
    assert start_request.emit_start_conversation_event is True
    assert start_request.locale == "en-US"
    assert start_request.conversation_id == "test-123"


def test_connection_settings_with_new_properties():
    connection_settings = ConnectionSettings(
        "environment-id",
        "agent-id",
        direct_connect_url="https://custom.url",
        use_experimental_endpoint=True,
        enable_diagnostics=True,
    )
    assert connection_settings.direct_connect_url == "https://custom.url"
    assert connection_settings.use_experimental_endpoint is True
    assert connection_settings.enable_diagnostics is True


def test_connection_settings_direct_url_only():
    # Should allow creation with only direct_connect_url
    connection_settings = ConnectionSettings(
        "", "", direct_connect_url="https://custom.url"
    )
    assert connection_settings.direct_connect_url == "https://custom.url"


def test_scope_from_settings():
    connection_settings = ConnectionSettings("env-id", "agent-id")
    scope = CopilotClient.scope_from_settings(connection_settings)
    assert scope.endswith("/.default")
    assert "https://" in scope


def test_populate_from_environment(monkeypatch):
    from microsoft_agents.copilotstudio.client import PowerPlatformCloud, AgentType

    # Set up environment variables
    monkeypatch.setenv("ENVIRONMENT_ID", "test-env-id")
    monkeypatch.setenv("AGENT_IDENTIFIER", "test-agent-id")
    monkeypatch.setenv("CLOUD", "PROD")
    monkeypatch.setenv("COPILOT_AGENT_TYPE", "PUBLISHED")
    monkeypatch.setenv("CUSTOM_POWER_PLATFORM_CLOUD", "https://custom.cloud")
    monkeypatch.setenv("DIRECT_CONNECT_URL", "https://direct.url")
    monkeypatch.setenv("USE_EXPERIMENTAL_ENDPOINT", "true")
    monkeypatch.setenv("ENABLE_DIAGNOSTICS", "true")

    # Call the populate method
    settings_dict = ConnectionSettings.populate_from_environment()

    # Verify the returned dictionary
    assert settings_dict["environment_id"] == "test-env-id"
    assert settings_dict["agent_identifier"] == "test-agent-id"
    assert settings_dict["cloud"] == PowerPlatformCloud.PROD
    assert settings_dict["copilot_agent_type"] == AgentType.PUBLISHED
    assert settings_dict["custom_power_platform_cloud"] == "https://custom.cloud"
    assert settings_dict["direct_connect_url"] == "https://direct.url"
    assert settings_dict["use_experimental_endpoint"] is True
    assert settings_dict["enable_diagnostics"] is True


def test_populate_from_environment_with_overrides():
    # Call with explicit overrides (should not use env vars)
    settings_dict = ConnectionSettings.populate_from_environment(
        environment_id="override-env",
        agent_identifier="override-agent",
        use_experimental_endpoint=False,
        enable_diagnostics=False,
    )

    # Verify the overrides were used
    assert settings_dict["environment_id"] == "override-env"
    assert settings_dict["agent_identifier"] == "override-agent"
    assert settings_dict["use_experimental_endpoint"] is False
    assert settings_dict["enable_diagnostics"] is False


def test_power_platform_environment_with_direct_connect_url():
    # Test DirectConnect URL mode
    connection_settings = ConnectionSettings(
        "",
        "",
        direct_connect_url="https://api.powerplatform.com/copilotstudio/dataverse-backed/authenticated/bots/test-bot",
    )

    url = PowerPlatformEnvironment.get_copilot_studio_connection_url(
        settings=connection_settings
    )

    parsed_url = urlparse(url)
    assert parsed_url.scheme == "https"
    assert parsed_url.hostname == "api.powerplatform.com"
    assert "/conversations" in url
    assert "api-version=" in url


def test_power_platform_environment_direct_connect_with_conversation_id():
    # Test DirectConnect URL with conversation ID
    connection_settings = ConnectionSettings(
        "",
        "",
        direct_connect_url="https://api.powerplatform.com/copilotstudio/dataverse-backed/authenticated/bots/test-bot",
    )

    url = PowerPlatformEnvironment.get_copilot_studio_connection_url(
        settings=connection_settings, conversation_id="conv-123"
    )

    parsed = urlparse(url)
    assert parsed.scheme == "https"
    assert parsed.hostname == "api.powerplatform.com"
    assert "/conversations/conv-123" in url
    assert "api-version=" in url


def test_power_platform_environment_create_subscribe_link():
    from microsoft_agents.copilotstudio.client import PowerPlatformCloud

    # Test subscribe link creation
    connection_settings = ConnectionSettings(
        "test-env", "test-agent", cloud=PowerPlatformCloud.PROD
    )

    url = PowerPlatformEnvironment.get_copilot_studio_connection_url(
        settings=connection_settings,
        conversation_id="conv-456",
        create_subscribe_link=True,
    )

    assert "/conversations/conv-456/subscribe" in url


def test_power_platform_environment_direct_connect_subscribe_link():
    # Test DirectConnect URL with subscribe link
    connection_settings = ConnectionSettings(
        "",
        "",
        direct_connect_url="https://api.powerplatform.com/copilotstudio/dataverse-backed/authenticated/bots/test-bot",
    )

    url = PowerPlatformEnvironment.get_copilot_studio_connection_url(
        settings=connection_settings,
        conversation_id="conv-789",
        create_subscribe_link=True,
    )

    assert "/conversations/conv-789/subscribe" in url


def test_decode_cloud_from_uri():
    from microsoft_agents.copilotstudio.client import PowerPlatformCloud

    # Test cloud decoding from various URIs
    prod_url = "https://api.powerplatform.com/some/path"
    gov_url = "https://api.gov.powerplatform.microsoft.us/some/path"
    unknown_url = "https://custom.domain.com/some/path"

    assert (
        PowerPlatformEnvironment._decode_cloud_from_uri(prod_url)
        == PowerPlatformCloud.PROD
    )
    assert (
        PowerPlatformEnvironment._decode_cloud_from_uri(gov_url)
        == PowerPlatformCloud.GOV_FR
    )
    assert (
        PowerPlatformEnvironment._decode_cloud_from_uri(unknown_url)
        == PowerPlatformCloud.UNKNOWN
    )


def test_get_token_audience_with_direct_connect():
    # Test token audience with DirectConnect URL
    connection_settings = ConnectionSettings(
        "",
        "",
        direct_connect_url="https://api.powerplatform.com/copilotstudio/dataverse-backed/authenticated/bots/test-bot",
    )

    audience = PowerPlatformEnvironment.get_token_audience(settings=connection_settings)

    assert audience == "https://api.powerplatform.com/.default"


def test_direct_connect_url_path_normalization():
    # Test that paths with /conversations are properly normalized
    connection_settings = ConnectionSettings(
        "",
        "",
        direct_connect_url="https://api.powerplatform.com/copilotstudio/dataverse-backed/authenticated/bots/test-bot/conversations",
    )

    url = PowerPlatformEnvironment.get_copilot_studio_connection_url(
        settings=connection_settings, conversation_id="conv-abc"
    )

    # Should not have double /conversations/conversations
    assert "/conversations/conversations" not in url
    assert "/conversations/conv-abc" in url


@pytest.mark.asyncio
async def test_enable_diagnostics_logging(mocker, caplog):
    import logging

    # Define the connection settings with diagnostics enabled
    connection_settings = ConnectionSettings(
        "environment-id",
        "agent-id",
        client_session_settings={"base_url": "https://api.copilotstudio.com"},
        enable_diagnostics=True,
    )

    mock_session = mocker.MagicMock(spec=ClientSession)
    mock_session.__aenter__.return_value = mock_session

    @asynccontextmanager
    async def response():
        mock_response = mocker.Mock()
        mock_response.status = 200
        mock_response.headers = {
            "Content-Type": "text/event-stream",
            "x-ms-conversationid": "test-conv-123",
        }

        activity = Activity(
            type="message", text="Test response", conversation={"id": "test-conv-123"}
        )
        activity_json = activity.model_dump_json(exclude_unset=True)

        async def content():
            yield "event: activity".encode()
            yield f"data: {activity_json}".encode()

        mock_response.content = content()

        yield mock_response

    mock_session.post.return_value = response()

    mocker.patch("aiohttp.ClientSession", return_value=mock_session)

    # Create a CopilotClient instance
    copilot_client = CopilotClient(connection_settings, "token")

    # Enable logging capture at DEBUG level
    with caplog.at_level(logging.DEBUG):
        count = 0
        async for message in copilot_client.start_conversation():
            count += 1

        assert count == 1

        # Check that diagnostic messages were logged
        debug_messages = [record.message for record in caplog.records]
        assert any(">>> SEND TO" in msg for msg in debug_messages)
        assert any("Content-Type" in msg for msg in debug_messages)
        assert any("=" * 53 in msg for msg in debug_messages)


@pytest.mark.asyncio
async def test_experimental_endpoint_capture(mocker):
    # Define the connection settings with experimental endpoint enabled
    connection_settings = ConnectionSettings(
        "environment-id",
        "agent-id",
        client_session_settings={"base_url": "https://api.copilotstudio.com"},
        use_experimental_endpoint=True,
    )

    # Verify initial state
    assert connection_settings.direct_connect_url is None
    assert connection_settings.use_experimental_endpoint is True

    mock_session = mocker.MagicMock(spec=ClientSession)
    mock_session.__aenter__.return_value = mock_session

    experimental_url = "https://experimental.api.powerplatform.com/bot/test-bot"

    @asynccontextmanager
    async def response():
        mock_response = mocker.Mock()
        mock_response.status = 200
        mock_response.headers = {
            "Content-Type": "text/event-stream",
            "x-ms-conversationid": "test-conv-123",
            "x-ms-d2e-experimental": experimental_url,
        }

        activity = Activity(
            type="message", text="Test response", conversation={"id": "test-conv-123"}
        )
        activity_json = activity.model_dump_json(exclude_unset=True)

        async def content():
            yield "event: activity".encode()
            yield f"data: {activity_json}".encode()

        mock_response.content = content()

        yield mock_response

    mock_session.post.return_value = response()

    mocker.patch("aiohttp.ClientSession", return_value=mock_session)

    # Create a CopilotClient instance
    copilot_client = CopilotClient(connection_settings, "token")

    count = 0
    async for message in copilot_client.start_conversation():
        count += 1

    assert count == 1

    # Verify that the experimental URL was captured and stored
    assert copilot_client._island_experimental_url == experimental_url
    assert copilot_client.settings.direct_connect_url == experimental_url


@pytest.mark.asyncio
async def test_experimental_endpoint_not_captured_when_disabled(mocker):
    # Define the connection settings with experimental endpoint disabled
    connection_settings = ConnectionSettings(
        "environment-id",
        "agent-id",
        client_session_settings={"base_url": "https://api.copilotstudio.com"},
        use_experimental_endpoint=False,
    )

    mock_session = mocker.MagicMock(spec=ClientSession)
    mock_session.__aenter__.return_value = mock_session

    experimental_url = "https://experimental.api.powerplatform.com/bot/test-bot"

    @asynccontextmanager
    async def response():
        mock_response = mocker.Mock()
        mock_response.status = 200
        mock_response.headers = {
            "Content-Type": "text/event-stream",
            "x-ms-conversationid": "test-conv-123",
            "x-ms-d2e-experimental": experimental_url,
        }

        activity = Activity(
            type="message", text="Test response", conversation={"id": "test-conv-123"}
        )
        activity_json = activity.model_dump_json(exclude_unset=True)

        async def content():
            yield "event: activity".encode()
            yield f"data: {activity_json}".encode()

        mock_response.content = content()

        yield mock_response

    mock_session.post.return_value = response()

    mocker.patch("aiohttp.ClientSession", return_value=mock_session)

    # Create a CopilotClient instance
    copilot_client = CopilotClient(connection_settings, "token")

    count = 0
    async for message in copilot_client.start_conversation():
        count += 1

    assert count == 1

    # Verify that the experimental URL was NOT captured
    assert copilot_client._island_experimental_url == ""
    assert copilot_client.settings.direct_connect_url is None


@pytest.mark.asyncio
async def test_experimental_endpoint_not_captured_when_direct_connect_set(mocker):
    # Define the connection settings with both experimental endpoint and direct connect URL
    direct_url = "https://direct.api.powerplatform.com/bot/direct-bot"
    connection_settings = ConnectionSettings(
        "environment-id",
        "agent-id",
        client_session_settings={"base_url": "https://api.copilotstudio.com"},
        use_experimental_endpoint=True,
        direct_connect_url=direct_url,
    )

    mock_session = mocker.MagicMock(spec=ClientSession)
    mock_session.__aenter__.return_value = mock_session

    experimental_url = "https://experimental.api.powerplatform.com/bot/test-bot"

    @asynccontextmanager
    async def response():
        mock_response = mocker.Mock()
        mock_response.status = 200
        mock_response.headers = {
            "Content-Type": "text/event-stream",
            "x-ms-conversationid": "test-conv-123",
            "x-ms-d2e-experimental": experimental_url,
        }

        activity = Activity(
            type="message", text="Test response", conversation={"id": "test-conv-123"}
        )
        activity_json = activity.model_dump_json(exclude_unset=True)

        async def content():
            yield "event: activity".encode()
            yield f"data: {activity_json}".encode()

        mock_response.content = content()

        yield mock_response

    mock_session.post.return_value = response()

    mocker.patch("aiohttp.ClientSession", return_value=mock_session)

    # Create a CopilotClient instance
    copilot_client = CopilotClient(connection_settings, "token")

    count = 0
    async for message in copilot_client.start_conversation():
        count += 1

    assert count == 1

    # Verify that the experimental URL was NOT captured (direct_connect_url takes precedence)
    assert copilot_client._island_experimental_url == ""
    assert copilot_client.settings.direct_connect_url == direct_url
