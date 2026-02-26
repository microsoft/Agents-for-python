import pytest
import asyncio

from microsoft_agents.activity import ActivityTypes

from microsoft_agents.hosting.core import (
    TurnContext,
    TurnState,
)

from microsoft_agents.testing import (
    AgentClient,
    AgentEnvironment,
    AiohttpScenario,
)

FULL_TEXT = "This is a streaming response."
CHUNKS = FULL_TEXT.split()

async def init_agent(env: AgentEnvironment):

    app = env.agent_application

    @app.message("/stream")
    async def stream_handler(context: TurnContext, state: TurnState):
        
        assert context.streaming_response is not None

        context.streaming_response.queue_informative_update("Starting stream...")

        for chunk in CHUNKS:
            await asyncio.sleep(1.0)  # Simulate delay between chunks
            context.streaming_response.queue_text_chunk(chunk)

        await asyncio.sleep(1.0)

        await context.streaming_response.end_stream()

_SCENARIO = AiohttpScenario(init_agent=init_agent, use_jwt_middleware=False)

@pytest.mark.asyncio
@pytest.mark.agent_test(_SCENARIO)
async def test_basic_streaming_response(agent_client: AgentClient):

    expected_len = len(FULL_TEXT.split())

    # give enough time for all the activities to send
    await agent_client.send("/stream", wait=expected_len * 2.0)

    stream_activities = agent_client.select().where(
        entities=lambda x: any(e.type == "streaminfo" for e in x)
    )

    assert len(stream_activities) == len(CHUNKS) + 2

    informative = stream_activities[0]
    informative_streaminfo = informative[0].entities.first(lambda e: e.type == "streaminfo")

    assert informative_streaminfo.stream_type == "informative"
    assert informative_streaminfo.stream_sequence == 0
    assert informative.text == "Starting stream..."
    assert informative.type == ActivityTypes.typing

    t = ""
    for i, chunk in enumerate(CHUNKS):
        t += chunk

        j = i + 1

        streaminfo = stream_activities[j].entities.first(lambda e: e.type == "streaminfo")

        assert stream_activities[j].text == ""
        assert stream_activities[j].type == ActivityTypes.typing
        assert streaminfo.stream_type == "streaming"
        assert streaminfo.stream_sequence == j

    final_streaminfo = stream_activities[-1].entities.first(lambda e: e.type == "streaminfo")

    assert final_streaminfo.stream_sequence == len(CHUNKS) + 2
    assert final_streaminfo.stream_type == "final"
    assert stream_activities[-1].text == FULL_TEXT

