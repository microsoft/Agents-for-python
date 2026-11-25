import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from microsoft_agents.hosting.aiohttp import CloudAdapter as AiohttpAdapter
from microsoft_agents.hosting.fastapi import CloudAdapter as FastapiAdapter


@pytest.mark.asyncio
@pytest.mark.parametrize("adapter_type", [AiohttpAdapter, FastapiAdapter])
@pytest.mark.parametrize("emit_stack_trace", [False, True])
async def test_default_error_diagnostics(adapter_type, emit_stack_trace, caplog):
    adapter = adapter_type(
        channel_service_client_factory=MagicMock(),
        emit_stack_trace=emit_stack_trace,
    )
    context = MagicMock()
    context.send_activity = AsyncMock()
    context.send_trace_activity = AsyncMock()
    try:
        raise RuntimeError("private diagnostic detail")
    except RuntimeError as caught:
        error = caught

    with caplog.at_level(logging.ERROR):
        await adapter.on_turn_error(context, error)

    response = context.send_activity.call_args.args[0]
    assert response.text == "Sorry, something went wrong."
    trace = context.send_trace_activity.call_args.args
    assert trace[0] == "OnTurnError Trace"
    assert "private diagnostic detail" in trace[1]
    assert ("Traceback (most recent call last)" in trace[1]) == emit_stack_trace
    assert caplog.records[-1].exc_info[1] is error
    assert "test_default_error_diagnostics" in caplog.text


@pytest.mark.asyncio
async def test_error_without_traceback():
    adapter = AiohttpAdapter(
        channel_service_client_factory=MagicMock(), emit_stack_trace=True
    )
    context = MagicMock(send_activity=AsyncMock(), send_trace_activity=AsyncMock())
    await adapter.on_turn_error(context, ValueError("never raised"))
    assert context.send_trace_activity.call_args.args[1] == "ValueError: never raised\n"


@pytest.mark.asyncio
async def test_response_failure_propagates_before_trace():
    adapter = AiohttpAdapter(channel_service_client_factory=MagicMock())
    failure = RuntimeError("send failed")
    context = MagicMock(
        send_activity=AsyncMock(side_effect=failure), send_trace_activity=AsyncMock()
    )
    with pytest.raises(RuntimeError) as caught:
        await adapter.on_turn_error(context, ValueError("turn failed"))
    assert caught.value is failure
    context.send_trace_activity.assert_not_called()


@pytest.mark.asyncio
async def test_pipeline_uses_replacement_and_propagates_its_failure():
    adapter = AiohttpAdapter(channel_service_client_factory=MagicMock())
    context = MagicMock(send_activity=AsyncMock(), send_trace_activity=AsyncMock())
    original = ValueError("turn failed")
    replacement_failure = RuntimeError("handler failed")
    handler = AsyncMock(side_effect=replacement_failure)
    adapter.on_turn_error = handler
    adapter.middleware_set.receive_activity_with_status = AsyncMock(
        side_effect=original
    )

    with pytest.raises(RuntimeError) as caught:
        await adapter.run_pipeline(context)

    assert caught.value is replacement_failure
    handler.assert_awaited_once_with(context, original)
    context.send_activity.assert_not_called()
    context.send_trace_activity.assert_not_called()


@pytest.mark.asyncio
async def test_omitted_option_omits_traceback():
    adapter = AiohttpAdapter(channel_service_client_factory=MagicMock())
    context = MagicMock(send_activity=AsyncMock(), send_trace_activity=AsyncMock())
    await adapter.on_turn_error(context, ValueError("diagnostic"))
    assert (
        context.send_trace_activity.call_args.args[1] == "Exception caught : diagnostic"
    )
