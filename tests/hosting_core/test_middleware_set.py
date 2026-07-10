# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from collections.abc import Awaitable, Callable
from typing import Any

import pytest

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.hosting.core.middleware_set import MiddlewareSet


def create_turn_context(text: str) -> TurnContext:
    return TurnContext(object(), Activity(type=ActivityTypes.message, text=text))


def context_text(context: TurnContext) -> str:
    return context.activity.text


class RecordingMiddleware:
    def __init__(
        self,
        name: str,
        events: list[str],
        *,
        call_next: bool = True,
        next_context: Any | None = None,
        result: Any = None,
    ):
        self.name = name
        self.events = events
        self.call_next = call_next
        self.next_context = next_context
        self.result = result

    async def on_turn(
        self, context: TurnContext, logic: Callable[[TurnContext], Awaitable[Any]]
    ):
        self.events.append(f"{self.name}:before:{context_text(context)}")

        if not self.call_next:
            self.events.append(f"{self.name}:short-circuit")
            return self.result

        downstream_result = await logic(
            self.next_context if self.next_context is not None else context
        )
        self.events.append(f"{self.name}:after:{context_text(context)}")
        return downstream_result


@pytest.mark.asyncio
async def test_use_registers_all_middleware_and_returns_self():
    events: list[str] = []
    middleware_set = MiddlewareSet()
    first = RecordingMiddleware("first", events)
    second = RecordingMiddleware("second", events)
    context = create_turn_context("context")

    result = middleware_set.use(first, second)

    assert result is middleware_set

    async def callback(context: TurnContext):
        events.append(f"callback:{context_text(context)}")

    await middleware_set.on_turn(context, callback)

    assert events == [
        "first:before:context",
        "second:before:context",
        "second:after:context",
        "first:after:context",
        "callback:context",
    ]


def test_use_rejects_invalid_middleware():
    middleware_set = MiddlewareSet()

    with pytest.raises(TypeError) as error:
        middleware_set.use(object())

    assert (
        str(error.value)
        == 'MiddlewareSet.use(): invalid middleware at index "0" being added.'
    )


@pytest.mark.asyncio
async def test_on_turn_does_not_return_logic_result():
    events: list[str] = []
    context = create_turn_context("context")
    middleware_set = MiddlewareSet().use(RecordingMiddleware("middleware", events))

    async def logic(context: TurnContext):
        events.append(f"logic:{context_text(context)}")
        return "logic-result"

    result = await middleware_set.on_turn(context, logic)

    assert result is None
    assert events == [
        "middleware:before:context",
        "middleware:after:context",
        "logic:context",
    ]


@pytest.mark.asyncio
async def test_middleware_can_short_circuit_pipeline():
    events: list[str] = []
    context = create_turn_context("context")
    middleware_set = MiddlewareSet().use(
        RecordingMiddleware(
            "first", events, call_next=False, result="short-circuit-result"
        ),
        RecordingMiddleware("second", events),
    )

    async def logic(context: TurnContext):
        events.append(f"logic:{context_text(context)}")
        return "logic-result"

    result = await middleware_set.on_turn(context, logic)

    assert result is None
    assert events == [
        "first:before:context",
        "first:short-circuit",
        "logic:context",
    ]


@pytest.mark.asyncio
async def test_middleware_can_pass_updated_context_to_next_step():
    events: list[str] = []
    original_context = create_turn_context("original-context")
    updated_context = create_turn_context("updated-context")
    middleware_set = MiddlewareSet().use(
        RecordingMiddleware("first", events, next_context=updated_context),
        RecordingMiddleware("second", events),
    )

    async def logic(context: TurnContext):
        events.append(f"logic:{context_text(context)}")

    await middleware_set.on_turn(original_context, logic)

    assert events == [
        "first:before:original-context",
        "second:before:updated-context",
        "second:after:updated-context",
        "first:after:original-context",
        "logic:original-context",
    ]


@pytest.mark.asyncio
async def test_on_turn_runs_middleware_without_final_logic():
    events: list[str] = []
    context = create_turn_context("context")
    middleware_set = MiddlewareSet().use(RecordingMiddleware("middleware", events))

    result = await middleware_set.on_turn(context, None)

    assert result is None
    assert events == [
        "middleware:before:context",
        "middleware:after:context",
    ]


@pytest.mark.asyncio
async def test_on_turn_runs_logic_after_middleware_pipeline_unwinds():
    events: list[str] = []
    context = create_turn_context("context")
    middleware_set = MiddlewareSet().use(
        RecordingMiddleware("first", events),
        RecordingMiddleware("second", events),
    )

    async def logic(context: TurnContext):
        events.append(f"logic:{context_text(context)}")
        return "logic-result"

    result = await middleware_set.on_turn(context, logic)

    assert result is None
    assert events == [
        "first:before:context",
        "second:before:context",
        "second:after:context",
        "first:after:context",
        "logic:context",
    ]


@pytest.mark.asyncio
async def test_middleware_set_can_be_nested_as_middleware():
    events: list[str] = []
    context = create_turn_context("context")
    inner_set = MiddlewareSet().use(RecordingMiddleware("inner", events))
    outer_set = MiddlewareSet().use(
        RecordingMiddleware("outer-before", events),
        inner_set,
        RecordingMiddleware("outer-after", events),
    )

    async def logic(context: TurnContext):
        events.append(f"logic:{context_text(context)}")
        return "logic-result"

    result = await outer_set.on_turn(context, logic)

    assert result is None
    assert events == [
        "outer-before:before:context",
        "inner:before:context",
        "inner:after:context",
        "outer-after:before:context",
        "outer-after:after:context",
        "outer-before:after:context",
        "logic:context",
    ]


@pytest.mark.asyncio
async def test_receive_activity_with_status_runs_logic_inside_middleware_pipeline():
    events: list[str] = []
    context = create_turn_context("context")
    middleware_set = MiddlewareSet().use(
        RecordingMiddleware("first", events),
        RecordingMiddleware("second", events),
    )

    async def logic(context: TurnContext):
        events.append(f"logic:{context_text(context)}")
        return "logic-result"

    result = await middleware_set.receive_activity_with_status(context, logic)

    assert result is None
    assert events == [
        "first:before:context",
        "second:before:context",
        "logic:context",
        "second:after:context",
        "first:after:context",
    ]


@pytest.mark.asyncio
async def test_receive_activity_with_status_honors_short_circuit():
    events: list[str] = []
    context = create_turn_context("context")
    middleware_set = MiddlewareSet().use(
        RecordingMiddleware(
            "first", events, call_next=False, result="short-circuit-result"
        ),
        RecordingMiddleware("second", events),
    )

    async def logic(context: TurnContext):
        events.append(f"logic:{context_text(context)}")
        return "logic-result"

    result = await middleware_set.receive_activity_with_status(context, logic)

    assert result is None
    assert events == [
        "first:before:context",
        "first:short-circuit",
    ]


@pytest.mark.asyncio
async def test_receive_activity_with_status_can_pass_updated_context_to_logic():
    events: list[str] = []
    original_context = create_turn_context("original-context")
    updated_context = create_turn_context("updated-context")
    middleware_set = MiddlewareSet().use(
        RecordingMiddleware("first", events, next_context=updated_context),
        RecordingMiddleware("second", events),
    )

    async def logic(context: TurnContext):
        events.append(f"logic:{context_text(context)}")

    result = await middleware_set.receive_activity_with_status(original_context, logic)

    assert result is None
    assert events == [
        "first:before:original-context",
        "second:before:updated-context",
        "logic:updated-context",
        "second:after:updated-context",
        "first:after:original-context",
    ]


@pytest.mark.asyncio
async def test_receive_activity_with_status_runs_without_final_logic():
    events: list[str] = []
    context = create_turn_context("context")
    middleware_set = MiddlewareSet().use(RecordingMiddleware("middleware", events))

    result = await middleware_set.receive_activity_with_status(context, None)

    assert result is None
    assert events == [
        "middleware:before:context",
        "middleware:after:context",
    ]


@pytest.mark.asyncio
async def test_on_turn_propagates_middleware_exceptions():
    class FailingMiddleware:
        async def on_turn(
            self, context: TurnContext, logic: Callable[[TurnContext], Awaitable[Any]]
        ):
            raise RuntimeError("middleware failed")

    context = create_turn_context("context")
    middleware_set = MiddlewareSet().use(FailingMiddleware())

    async def logic(context: TurnContext):
        return "logic-result"

    with pytest.raises(RuntimeError, match="middleware failed"):
        await middleware_set.on_turn(context, logic)
