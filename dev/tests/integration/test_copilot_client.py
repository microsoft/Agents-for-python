import pytest

from typing import Awaitable, Callable, Iterable

from aiohttp.web import Request, Response, Application, StreamResponse

from microsoft_agents.activity import Activity

from microsoft_agents.copilotstudio.client import (
    CopilotClient,
    ConnectionSettings,
    PowerPlatformEnvironment,
)

from microsoft_agents.testing.integration import AiohttpRunner

def mock_mcs_handler(
    activities: Iterable[Activity],
) -> Callable[[Request], Awaitable[StreamResponse]]:
    """Creates a mock handler for MCS endpoint returning SSE-formatted activity."""

    async def handler(request: Request) -> StreamResponse:
        response = StreamResponse(status=200)
        response.headers["Content-Type"] = "text/event-stream"
        response.headers["x-ms-conversationid"] = "test-conv-id"
        # response.headers['Content-Length'] = str(len(activity_data))
        await response.prepare(request)

        # Proper SSE format
        for activity in activities:
            activity_data = activity.model_dump_json(exclude_unset=True)
            await response.write(b"event: activity\n")
            await response.write(f"data: {activity_data}\n\n".encode("utf-8"))

        await response.write_eof()
        return response

    return handler


def mock_mcs_endpoint(
    mocker, activities: Iterable[Activity], path: str, port: int
) -> AiohttpRunner:
    """Mock MCS responses for testing."""

    PowerPlatformEnvironment.get_copilot_studio_connection_url = mocker.MagicMock(
        return_value=f"http://localhost:{port}{path}"
    )

    app = Application()
    app.router.add_post(path, mock_mcs_handler(activities))

    return AiohttpRunner(app, port=port)


@pytest.mark.asyncio
async def test_start_conversation_and_ask_question_large_message(mocker):

    activity = Activity(
        type="message", text="*" * 1_000_000, conversation={"id": "conv-id"}
    )

    runner = mock_mcs_endpoint(mocker, [activity], "/mcs-endpoint", port=8081)

    async with runner:
        settings = ConnectionSettings("environment-id", "agent-id")
        client = CopilotClient(settings=settings, token="test-token")

        with pytest.raises(Exception, match="Chunk too big"):
            async for conv_activity in client.start_conversation():
                assert conv_activity.type == "message"

@pytest.mark.asyncio
async def test_start_conversation_and_ask_question_no_error(mocker):

    activity = Activity(
        type="message", text="*" * 1_000_000, conversation={"id": "conv-id"}
    )

    runner = mock_mcs_endpoint(mocker, [activity], "/mcs-endpoint", port=8081)

    async with runner:
        settings = ConnectionSettings("environment-id", "agent-id",
                                      client_session_settings={"read_bufsize": 2**25})
        client = CopilotClient(settings=settings, token="test-token")

        async for conv_activity in client.start_conversation():
            assert conv_activity.type == "message"


def activity_generator(activity: Activity, n: int) -> Iterable[Activity]:
    for i in range(n):
        yield activity


@pytest.mark.asyncio
async def test_start_conversation_many(mocker):

    activity = Activity(type="message", conversation={"id": "conv-id"})
    activities = activity_generator(activity, 100_000)

    runner = mock_mcs_endpoint(mocker, activities, "/mcs-endpoint", port=8081)

    async with runner:
        settings = ConnectionSettings("environment-id", "agent-id")
        client = CopilotClient(settings=settings, token="test-token")

        for i in range(100):
            async for conv_activity in client.start_conversation():
                assert conv_activity.type == "message"