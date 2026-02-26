"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import asyncio

import pytest

from microsoft_agents.activity import (
    Activity,
    ChannelId,
    Channels,
    DeliveryModes,
    ResourceResponse,
)
from microsoft_agents.hosting.core.app.streaming.citation import Citation
from microsoft_agents.hosting.core.app.streaming.streaming_response import (
    StreamingResponse,
)
from microsoft_agents.hosting.core.turn_context import TurnContext

STREAMING_CHANNELS = [Channels.webchat, Channels.ms_teams, Channels.direct_line]
NON_STREAMING_CHANNELS = [Channels.test, Channels.slack, Channels.email]


@pytest.fixture(name="non_streaming_channel", params=NON_STREAMING_CHANNELS)
def fixture_non_streaming_channel(request) -> ChannelId:
    return ChannelId(channel=request.param)


@pytest.fixture(name="streaming_channel", params=STREAMING_CHANNELS)
def fixture_streaming_channel(request) -> ChannelId:
    return ChannelId(channel=request.param)


def _create_turn_context(
    mocker,
    *,
    channel_id: ChannelId | Channels = Channels.webchat,
    delivery_mode: str | None = DeliveryModes.stream,
    return_value=None,
):
    if isinstance(channel_id, Channels):
        channel_id = ChannelId(channel=channel_id)

    context = mocker.MagicMock(spec=TurnContext)
    activity = mocker.MagicMock(spec=Activity)
    activity.channel_id = channel_id
    activity.delivery_mode = delivery_mode
    activity.is_agentic_request.return_value = False
    context.activity = activity
    if isinstance(return_value, list) and len(return_value) > 0:
        context.send_activity = mocker.AsyncMock(side_effect=return_value)
    else:
        context.send_activity = mocker.AsyncMock(return_value=return_value)
    return context


@pytest.mark.asyncio
async def test_queue_informative_update_is_ignored_for_non_streaming_channel(mocker):
    context = _create_turn_context(
        mocker,
        delivery_mode=DeliveryModes.normal,
        channel_id=Channels.slack,
    )
    response = StreamingResponse(context)

    response.queue_informative_update("working")
    await response.wait_for_queue()

    context.send_activity.assert_not_called()


@pytest.mark.asyncio
async def test_queue_text_chunk_and_end_stream_send_streaming_then_final_message(
    mocker,
):
    context = _create_turn_context(
        mocker,
        delivery_mode=DeliveryModes.stream,
        return_value=ResourceResponse(id="stream-1"),
    )
    response = StreamingResponse(context)

    response.queue_text_chunk("Hello [doc1]")
    await response.end_stream()

    assert context.send_activity.await_count == 1

    final_activity = context.send_activity.await_args_list[0].args[0]

    assert final_activity.type == "message"
    assert final_activity.id != ""
    assert final_activity.text == "Hello [1]"
    assert final_activity.entities[0].stream_type == "final"


@pytest.mark.asyncio
async def test_multiple_queued_text_chunks_are_coalesced_into_one_final_activity(
    mocker,
):
    context = _create_turn_context(
        mocker,
        delivery_mode=DeliveryModes.stream,
        return_value=ResourceResponse(id="stream-1"),
    )
    response = StreamingResponse(context)

    response.queue_text_chunk("Hello")
    response.queue_text_chunk(" ")
    response.queue_text_chunk("world")
    await response.end_stream()

    assert context.send_activity.await_count == 1
    final_activity = context.send_activity.await_args_list[0].args[0]
    assert final_activity.text == "Hello world"
    assert final_activity.entities[0].stream_type == "final"


@pytest.mark.asyncio
async def test_set_citations_only_sends_final_when_end_stream_happens_before_drain(
    mocker,
):
    context = _create_turn_context(
        mocker,
        delivery_mode=DeliveryModes.stream,
        return_value=[ResourceResponse(id="stream-2")],
    )
    response = StreamingResponse(context)
    response.set_citations(
        [
            Citation(content="Document one content", title="Doc One"),
            Citation(content="Document two content", title="Doc Two"),
        ]
    )

    response.queue_text_chunk("Answer with citation [1].")
    await response.end_stream()

    assert context.send_activity.await_count == 1
    final_activity = context.send_activity.await_args_list[0].args[0]

    citation_entities = [
        entity
        for entity in final_activity.entities
        if getattr(entity, "schema_type", None) == "Message"
    ]
    assert len(citation_entities) == 0


@pytest.mark.asyncio
async def test_set_citations_adds_only_used_citations_when_streaming_activity_is_sent(
    mocker,
):
    context = _create_turn_context(
        mocker,
        delivery_mode=DeliveryModes.stream,
        return_value=[ResourceResponse(id="stream-2"), ResourceResponse(id="stream-2")],
    )
    response = StreamingResponse(context)
    response.set_citations(
        [
            Citation(content="Document one content", title="Doc One"),
            Citation(content="Document two content", title="Doc Two"),
        ]
    )

    response.queue_text_chunk("Answer with citation [1].")
    await response.wait_for_queue()
    await response.end_stream()

    assert context.send_activity.await_count == 2
    streaming_activity = context.send_activity.await_args_list[0].args[0]

    citation_entities = [
        entity
        for entity in streaming_activity.entities
        if getattr(entity, "schema_type", None) == "Message"
    ]
    assert len(citation_entities) == 1
    assert len(citation_entities[0].citation) == 1
    assert citation_entities[0].citation[0].position == 1


@pytest.mark.asyncio
async def test_end_stream_cannot_be_called_twice(mocker):
    context = _create_turn_context(
        mocker,
        delivery_mode=DeliveryModes.stream,
        return_value=[ResourceResponse(id="stream-3")],
    )
    response = StreamingResponse(context)

    response.queue_text_chunk("Done")
    await response.end_stream()

    with pytest.raises(RuntimeError, match="already ended"):
        await response.end_stream()


@pytest.mark.asyncio
async def test_teams_403_marks_stream_as_cancelled_and_future_chunks_are_ignored(
    mocker,
):

    context = _create_turn_context(
        mocker,
        channel_id=Channels.ms_teams,
        return_value=[
            RuntimeError("403 Forbidden: Stream cancelled by user"),
            ResourceResponse(id="stream-4"),
        ],
    )

    response = StreamingResponse(context)

    response.queue_text_chunk("first")
    await response.wait_for_queue()

    response.queue_text_chunk(" second")
    await response.wait_for_queue()

    assert context.send_activity.await_count == 1
    assert response.get_message() == "first"


@pytest.mark.asyncio
async def test_feedback_loop_type_added_to_final_streaminfo_entity(mocker):
    context = _create_turn_context(
        mocker,
        delivery_mode=DeliveryModes.stream,
        return_value=[ResourceResponse(id="stream-4")],
    )
    response = StreamingResponse(context)
    response.set_feedback_loop(True)
    response.set_feedback_loop_type("custom")

    response.queue_text_chunk("feedback")
    await response.end_stream()

    final_activity = context.send_activity.await_args_list[-1].args[0]
    stream_info = next(
        entity for entity in final_activity.entities if entity.type == "streaminfo"
    )

    assert stream_info.feedback_loop == {"type": "custom"}


@pytest.mark.asyncio
async def test_generated_by_ai_label_adds_ai_entity_on_final_message(mocker):
    context = _create_turn_context(
        mocker,
        delivery_mode=DeliveryModes.stream,
        return_value=[ResourceResponse(id="stream-5")],
    )
    response = StreamingResponse(context)
    response.set_citations([Citation(content="Document one content", title="Doc One")])
    response.set_generated_by_ai_label(True)

    response.queue_text_chunk("See [1]")
    await response.end_stream()

    final_activity = context.send_activity.await_args_list[-1].args[0]
    ai_entities = [
        entity
        for entity in final_activity.entities
        if "AIGeneratedContent" in (getattr(entity, "additional_type", None) or [])
    ]

    assert len(ai_entities) == 1


@pytest.mark.asyncio
async def test_streaming_operations_with_sleeps_send_informative_and_text_updates(
    mocker,
):
    context = _create_turn_context(
        mocker,
        channel_id=Channels.test,
        delivery_mode=DeliveryModes.stream,
        return_value=[
            ResourceResponse(id="stream-10"),
            ResourceResponse(id="stream-10"),
            ResourceResponse(id="stream-10"),
            ResourceResponse(id="stream-10"),
        ],
    )
    response = StreamingResponse(context)

    response.queue_informative_update("Searching documents")
    await asyncio.sleep(0.2)

    response.queue_text_chunk("Hello")
    await asyncio.sleep(0.2)

    response.queue_text_chunk(" world")
    await asyncio.sleep(0.2)

    await response.end_stream()

    assert context.send_activity.await_count == 4

    sent_activities = [call.args[0] for call in context.send_activity.await_args_list]
    stream_types = [
        next(
            entity for entity in activity.entities if entity.type == "streaminfo"
        ).stream_type
        for activity in sent_activities
    ]
    sent_types = [activity.type for activity in sent_activities]

    assert sent_types == ["typing", "typing", "typing", "message"]
    assert stream_types == ["informative", "streaming", "streaming", "final"]
    assert sent_activities[-1].text == "Hello world"


@pytest.mark.asyncio
async def test_streaming_loop_with_sleep_emits_informative_and_streaming_updates(
    mocker,
):
    context = _create_turn_context(
        mocker,
        channel_id=Channels.test,
        delivery_mode=DeliveryModes.stream,
        return_value=[
            ResourceResponse(id="stream-11"),
            ResourceResponse(id="stream-11"),
            ResourceResponse(id="stream-11"),
            ResourceResponse(id="stream-11"),
            ResourceResponse(id="stream-11"),
            ResourceResponse(id="stream-11"),
            ResourceResponse(id="stream-11"),
        ],
    )
    response = StreamingResponse(context)

    updates = [
        ("Thinking", "Alpha "),
        ("Drafting", "Beta "),
        ("Finalizing", "Gamma"),
    ]

    for informative_text, chunk in updates:
        response.queue_informative_update(informative_text)
        response.queue_text_chunk(chunk)
        await asyncio.sleep(0.3)

    await response.end_stream()

    sent_activities = [call.args[0] for call in context.send_activity.await_args_list]
    stream_types = [
        next(
            entity for entity in activity.entities if entity.type == "streaminfo"
        ).stream_type
        for activity in sent_activities
    ]

    assert stream_types.count("informative") == 3
    assert stream_types.count("streaming") == 3
    assert stream_types[-1] == "final"
    assert sent_activities[-1].type == "message"
    assert sent_activities[-1].text == "Alpha Beta Gamma"


class TestStreamingResponseNonStreamingChannel:

    @pytest.mark.asyncio
    async def test_queue_text_chunk_and_end_stream_send_final_message(
        self, mocker, non_streaming_channel
    ):
        context = _create_turn_context(mocker, channel_id=non_streaming_channel)
        response = StreamingResponse(context)

        response.queue_text_chunk("Hello")
        await response.end_stream()

        assert context.send_activity.await_count == 1
        final_activity = context.send_activity.await_args_list[0].args[0]

        assert final_activity.type == "message"
        assert final_activity.text == "Hello"
        assert final_activity.entities[0].stream_type == "final"


@pytest.mark.asyncio
async def test_wait_for_queue_is_noop_when_nothing_was_queued(mocker):
    context = _create_turn_context(mocker, delivery_mode=DeliveryModes.stream)
    response = StreamingResponse(context)

    await response.wait_for_queue()

    context.send_activity.assert_not_called()


@pytest.mark.asyncio
async def test_end_stream_without_chunks_sends_default_final_text(mocker):
    context = _create_turn_context(
        mocker,
        delivery_mode=DeliveryModes.stream,
        return_value=ResourceResponse(id="stream-1"),
    )
    response = StreamingResponse(context)

    await response.end_stream()

    context.send_activity.assert_awaited_once()
    sent = context.send_activity.await_args.args[0]
    assert sent.type == "message"
    assert sent.text == "end stream response"


@pytest.mark.asyncio
async def test_non_streaming_channel_buffers_text_and_only_sends_on_end(mocker):
    context = _create_turn_context(
        mocker,
        channel_id=Channels.emulator,  # non-streaming branch
        delivery_mode=DeliveryModes.normal,
        return_value=ResourceResponse(id="final-1"),
    )
    response = StreamingResponse(context)

    response.queue_text_chunk("Hello")
    response.queue_text_chunk(" world")

    await asyncio.sleep(1)

    # Should not send partial updates on non-streaming channels
    context.send_activity.assert_not_called()

    await response.end_stream()

    context.send_activity.assert_awaited_once()
    sent = context.send_activity.await_args.args[0]
    assert sent.type == "message"
    assert sent.text == "Hello world"


@pytest.mark.asyncio
async def test_queue_informative_update_is_noop_on_non_streaming_channel(mocker):
    context = _create_turn_context(
        mocker,
        channel_id=Channels.emulator,  # non-streaming
        delivery_mode=None,
    )
    response = StreamingResponse(context)

    response.queue_informative_update("Working...")
    await response.wait_for_queue()

    context.send_activity.assert_not_called()


@pytest.mark.asyncio
async def test_public_methods_raise_after_end_stream(mocker):
    context = _create_turn_context(
        mocker,
        delivery_mode=DeliveryModes.stream,
        return_value=ResourceResponse(id="stream-2"),
    )
    response = StreamingResponse(context)

    response.queue_text_chunk("done")
    await response.end_stream()

    with pytest.raises(RuntimeError):
        response.queue_text_chunk("extra")

    with pytest.raises(RuntimeError):
        response.queue_informative_update("extra")

    with pytest.raises(RuntimeError):
        await response.end_stream()


@pytest.mark.asyncio
async def test_queue_text_chunk_citations_argument_is_currently_ignored(mocker):
    context = _create_turn_context(
        mocker,
        delivery_mode=DeliveryModes.stream,
        return_value=ResourceResponse(id="stream-3"),
    )
    response = StreamingResponse(context)

    response.queue_text_chunk(
        "Answer with [doc1]",
        citations=[Citation(title="Doc 1", content="Citation content")],
    )
    await response.wait_for_queue()

    sent = context.send_activity.await_args.args[0]
    entity_types = [getattr(e, "type", None) for e in (sent.entities or [])]

    # streaminfo should exist; schema.org citation entity should not
    assert "streaminfo" in entity_types
    assert "https://schema.org/Message" not in entity_types


@pytest.mark.asyncio
async def test_feedback_loop_type_without_enable_does_not_emit_feedback_loop_object(
    mocker,
):
    context = _create_turn_context(
        mocker,
        channel_id=Channels.ms_teams,
        return_value=ResourceResponse(id="teams-1"),
    )
    response = StreamingResponse(context)
    response._interval = 0

    response.set_feedback_loop_type("custom")
    response.queue_text_chunk("hello")
    await response.end_stream()

    sent = context.send_activity.await_args_list[-1].args[0]
    streaminfo = next(
        e for e in sent.entities if getattr(e, "type", None) == "streaminfo"
    )

    assert not hasattr(streaminfo, "feedback_loop")
    assert getattr(streaminfo, "feedback_loop_enabled", None) is False
