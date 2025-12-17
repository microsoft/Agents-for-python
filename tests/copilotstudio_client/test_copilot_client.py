import pytest

from contextlib import asynccontextmanager

from microsoft_agents.activity import Activity

from microsoft_agents.copilotstudio.client import (
    ConnectionSettings,
    CopilotClient,
    PowerPlatformEnvironment,
)

from aiohttp import ClientSession, ClientError


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
