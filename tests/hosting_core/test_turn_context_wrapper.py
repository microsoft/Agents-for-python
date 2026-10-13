# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from unittest.mock import AsyncMock, MagicMock

import pytest

from microsoft_agents.activity import (
    Activity,
    ChannelAccount,
    ChannelId,
    ConversationAccount,
    ConversationReference,
    ResourceResponse,
)
from microsoft_agents.hosting.core import ChannelAdapter, TurnContext
from microsoft_agents.hosting.core._utils._turn_context_wrapper import (
    _TurnContextWrapper,
)
from microsoft_agents.hosting.core.authorization import ClaimsIdentity


class WrappedContext(_TurnContextWrapper):
    pass


@pytest.fixture
def original():
    adapter = MagicMock(spec=ChannelAdapter)
    adapter.send_activities.return_value = [ResourceResponse(id="sent")]
    adapter.update_activity.return_value = ResourceResponse(id="updated")
    adapter.delete_activity.return_value = None
    return TurnContext(
        adapter,
        Activity(
            type="message",
            id="incoming",
            channel_id=ChannelId("test"),
            service_url="https://example.invalid",
            conversation=ConversationAccount(id="conversation"),
            from_property=ChannelAccount(id="user"),
            recipient=ChannelAccount(id="agent"),
        ),
        identity=ClaimsIdentity({"aud": "agent"}),
    )


@pytest.fixture
def wrapped(original):
    return WrappedContext(original)


def test_shares_context_references_and_mutable_state(original):
    original.turn_state["before"] = "value"
    original.services.set(str, "before")
    before = Activity(type="message", text="before")
    original.buffered_reply_activities.append(before)

    wrapped = WrappedContext(original)

    assert isinstance(wrapped, TurnContext)
    assert wrapped.adapter is original.adapter
    assert wrapped.activity is original.activity
    assert wrapped.identity is original.identity
    assert wrapped.turn_state is original.turn_state
    assert wrapped.services is original.services
    assert wrapped.buffered_reply_activities is original.buffered_reply_activities
    assert wrapped.turn_state["before"] == "value"
    assert wrapped.services.get(str) == "before"
    assert wrapped.buffered_reply_activities == [before]

    wrapped.turn_state["after"] = "value"
    wrapped.services.set(str, "after")
    after = Activity(type="message", text="after")
    wrapped.buffered_reply_activities.append(after)
    original.activity.text = "changed"

    assert original.turn_state["after"] == "value"
    assert original.services.get(str) == "after"
    assert original.buffered_reply_activities == [before, after]
    assert wrapped.activity.text == "changed"


@pytest.mark.parametrize("initially_responded", [False, True])
def test_preserves_initial_responded_state(original, initially_responded):
    if initially_responded:
        original.responded = True

    assert WrappedContext(original).responded is initially_responded


@pytest.mark.parametrize("set_on_wrapper", [False, True])
def test_shares_responded_changes(original, wrapped, set_on_wrapper):
    target = wrapped if set_on_wrapper else original
    target.responded = True

    assert original.responded is True
    assert wrapped.responded is True


def test_preserves_responded_validation(original, wrapped):
    wrapped.responded = True

    with pytest.raises(ValueError, match="cannot set TurnContext.responded to False"):
        wrapped.responded = False

    assert original.responded is True
    assert wrapped.responded is True


@pytest.mark.parametrize("original_first", [False, True])
def test_shares_lazy_streaming_response(original, wrapped, original_first):
    first = original if original_first else wrapped
    response = first.streaming_response

    assert original.streaming_response is response
    assert wrapped.streaming_response is response


@pytest.mark.asyncio
@pytest.mark.parametrize("as_text", [False, True])
@pytest.mark.parametrize("with_options", [False, True])
async def test_send_activity_delegates_to_original_override(
    original, wrapped, monkeypatch, as_text, with_options
):
    activity = "hello" if as_text else Activity(type="message", text="hello")
    options = {"speak": "spoken", "input_hint": "ignoringInput"} if with_options else {}
    response = ResourceResponse(id="custom-send")
    delegate = AsyncMock(return_value=response)
    monkeypatch.setattr(original, "send_activity", delegate)

    result = await wrapped.send_activity(activity, **options)

    assert result is response
    delegate.assert_awaited_once_with(
        activity,
        speak=options.get("speak"),
        input_hint=options.get("input_hint"),
    )
    original.adapter.send_activities.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method, args, kwargs",
    [
        ("send_activities", ([Activity(type="message", text="hello")],), {}),
        ("send_activities", ([],), {}),
        ("update_activity", (Activity(type="message", id="update"),), {}),
        ("delete_activity", ("delete-id",), {}),
        (
            "delete_activity",
            (
                ConversationReference(
                    activity_id="delete-id",
                    conversation=ConversationAccount(id="conversation"),
                ),
            ),
            {},
        ),
        (
            "send_trace_activity",
            (),
            {
                "name": "trace",
                "value": {"key": "value"},
                "value_type": "custom-type",
                "label": "custom-label",
            },
        ),
    ],
)
async def test_operations_delegate_arguments_and_results(
    original, wrapped, monkeypatch, method, args, kwargs
):
    response = object()
    delegate = AsyncMock(return_value=response)
    monkeypatch.setattr(original, method, delegate)

    result = await getattr(wrapped, method)(*args, **kwargs)

    assert result is response
    delegate.assert_awaited_once_with(*args, **kwargs)
    original.adapter.send_activities.assert_not_awaited()
    original.adapter.update_activity.assert_not_awaited()
    original.adapter.delete_activity.assert_not_awaited()


@pytest.mark.asyncio
async def test_trace_forwards_default_options(original, wrapped, monkeypatch):
    delegate = AsyncMock(return_value=ResourceResponse(id="trace"))
    monkeypatch.setattr(original, "send_trace_activity", delegate)

    result = await wrapped.send_trace_activity("trace")

    assert result is delegate.return_value
    delegate.assert_awaited_once_with(
        name="trace", value=None, value_type=None, label=None
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method, args",
    [
        ("send_activity", ("hello",)),
        ("send_activities", ([],)),
        ("update_activity", (Activity(type="message", id="update"),)),
        ("delete_activity", ("delete-id",)),
        ("send_trace_activity", ("trace",)),
        ("_aclose", ()),
    ],
)
async def test_propagates_original_operation_errors(
    original, wrapped, monkeypatch, method, args
):
    error = RuntimeError("original operation failed")
    delegate = AsyncMock(side_effect=error)
    monkeypatch.setattr(original, method, delegate)

    with pytest.raises(RuntimeError) as exc_info:
        await getattr(wrapped, method)(*args)

    assert exc_info.value is error
    delegate.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "registration, operation, argument",
    [
        ("on_send_activities", "send_activities", [Activity(type="message")]),
        ("on_update_activity", "update_activity", Activity(type="message", id="id")),
        ("on_delete_activity", "delete_activity", "id"),
    ],
)
async def test_hooks_register_on_original_and_receive_original_context(
    original, wrapped, monkeypatch, registration, operation, argument
):
    register = MagicMock(wraps=getattr(original, registration))
    monkeypatch.setattr(original, registration, register)

    async def handler(context, value, next_handler):
        assert context is original
        return await next_handler()

    hook = AsyncMock(side_effect=handler)

    assert getattr(wrapped, registration)(hook) is wrapped
    register.assert_called_once_with(hook)

    await getattr(wrapped, operation)(argument)

    hook.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_preserves_adapter_context_and_responded_state(original, wrapped):
    result = await wrapped.send_activity("hello")

    original.adapter.send_activities.assert_awaited_once()
    context, activities = original.adapter.send_activities.call_args.args
    assert context is original
    assert activities[0].text == "hello"
    assert result.id == "sent"
    assert original.responded is True
    assert wrapped.responded is True


@pytest.mark.asyncio
async def test_cleanup_registers_on_original_and_runs_handlers_in_order(
    original, wrapped, monkeypatch
):
    before = AsyncMock()
    after = AsyncMock()
    original._on_aclose(before)
    register = MagicMock(wraps=original._on_aclose)
    close = AsyncMock(wraps=original._aclose)
    monkeypatch.setattr(original, "_on_aclose", register)
    monkeypatch.setattr(original, "_aclose", close)
    calls = MagicMock()
    calls.attach_mock(before, "before")
    calls.attach_mock(after, "after")

    wrapped._on_aclose(after)
    register.assert_called_once_with(after)
    await wrapped._aclose()

    close.assert_awaited_once_with()
    before.assert_awaited_once_with(original)
    after.assert_awaited_once_with(original)
    assert [entry[0] for entry in calls.mock_calls] == ["before", "after"]


@pytest.mark.asyncio
async def test_nested_wrappers_preserve_delegation_and_shared_state(
    original, wrapped, monkeypatch
):
    outer = WrappedContext(wrapped)
    delegate = AsyncMock(return_value=ResourceResponse(id="nested"))
    monkeypatch.setattr(original, "send_activity", delegate)

    result = await outer.send_activity("hello")
    outer.responded = True

    assert result.id == "nested"
    delegate.assert_awaited_once_with("hello", speak=None, input_hint=None)
    assert outer.turn_state is original.turn_state
    assert outer.services is original.services
    assert outer.buffered_reply_activities is original.buffered_reply_activities
    assert outer.streaming_response is original.streaming_response
    assert original.responded is True
    assert wrapped.responded is True
