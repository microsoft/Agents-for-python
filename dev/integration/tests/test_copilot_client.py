import pytest

from aiohttp.web import Request, Response, Application

from microsoft_agents.activity import Activity

from microsoft_agents.copilotstudio.client import (
    CopilotClient,
    ConnectionSettings,
    PowerPlatformEnvironment
)

from microsoft_agents.testing.integration.core import (
    AiohttpRunner
)

def mock_mcs_handler(activity: Activity) -> Awaitable[[Request], Response]:
    """Creates a mock handler for MCS endpoint returning the given activity."""
    async def handler(request: Request) -> Response:
        activity_data = activity.model_dump_json(exclude_unset=True)
        return Response(
            body=activity_data
        )
    return handler

def mock_mcs_endpoint(
        mocker,
        activity: Activity,
        path: str,
        port: int
    ) -> AiohttpRunner:
    """Mock MCS responses for testing."""

    PowerPlatformEnvironment.get_copilot_studio_connection_url = mocker.MagicMock(
        return_value=f"http://localhost:{port}{path}"
    )

    app = Application()
    app.router.add_post(path, mock_mcs_handler(activity))

    return AiohttpRunner(app, port=port)


@pytest.mark.asyncio
async def test_start_conversation_and_ask_question(mocker):

    activity = Activity(
        type="message"
    )

    runner = mock_mcs_endpoint(mocker, activity, "/mcs-endpoint", port=8081)

    await with runner:
        settings = ConnectionSettings("environment-id", "agent-id")
        client = CopilotClient(settings=settings, token="test-token")

        async for conv_activity in client.start_conversation():
            assert conv_activity.type == "message"

        async for question_activity in client.ask_question("Hello!"):
            assert question_activity.type == "message"