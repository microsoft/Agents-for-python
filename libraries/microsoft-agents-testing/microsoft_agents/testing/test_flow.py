# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import asyncio
from inspect import isawaitable
from collections.abc import Awaitable, Callable, Coroutine, Iterable
from typing import Any, TypeAlias

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    ChannelAccount,
    RoleTypes,
)

from .test_adapter import TestAdapter
from .type_def import AgentCallbackHandler

ReplyValidator: TypeAlias = Callable[[Activity], None | Awaitable[None]]

__test__ = False  # for pytest: don't collect this module as a test case


class TestFlow:
    """Fluent helper for driving a ``TestAdapter`` conversation in tests.

    ``TestFlow`` mirrors the .NET testing pattern: each fluent method returns a
    new flow object whose task waits for the previous flow's task before running
    its own send or assertion. The adapter and callback are shared across the
    chain, while the accumulated task changes at each step.

    The implementation is intentionally queue-oriented. Sends go through
    :class:`TestAdapter`; replies are read from the adapter's captured activity
    queue in order. This is best suited to deterministic, unit-style
    conversation scripts.
    """

    __test__ = False  # for pytest: don't collect this class as a test case

    def __init__(
        self,
        adapter: TestAdapter,
        callback: AgentCallbackHandler | None = None,
        *,
        task: asyncio.Task[None] | None = None,
    ) -> None:
        """Create a flow for an adapter and optional agent turn callback.

        :param adapter: Test adapter used to process inbound activities and
            capture replies.
        :param callback: Agent turn callback to invoke for sent activities.
        :param task: Accumulated task for internal chaining.
        """

        self._adapter = adapter
        self._callback = callback
        self._task = task

    async def start_test(self) -> None:
        """Await the accumulated flow and surface any exceptions."""

        if self._task:
            await self._task

    async def start_test_async(self) -> None:
        """Await the accumulated flow and surface any exceptions.

        This alias matches the .NET method name.
        """

        await self.start_test()

    def send(self, user_input: str | Activity) -> TestFlow:
        """Append a user activity to the flow.

        :param user_input: Text to send as a message activity, or a fully formed
            activity to process through the adapter.
        :return: A new ``TestFlow`` with this send step appended.
        """

        if user_input is None:
            raise ValueError("TestFlow.send(): user_input cannot be None.")

        async def step() -> None:
            await self._await_previous()

            if isinstance(user_input, str):
                if not self._callback:
                    raise ValueError("TestFlow.send(): callback is required.")
                await self._adapter.send_text_to_bot(user_input, self._callback)
                return

            if not self._callback:
                raise ValueError("TestFlow.send(): callback is required.")

            await self._adapter.process_activity(
                self._adapter.claims_identity,
                user_input,
                self._callback,
            )

        return self._append(step)

    def send_conversation_update(
        self, members_added: Iterable[ChannelAccount] | None = None
    ) -> TestFlow:
        """Append a conversation update activity to the flow.

        :param members_added: Members to include in ``members_added``. When
            omitted, the adapter's default test user is added.
        :return: A new ``TestFlow`` with this send step appended.
        """

        if members_added is None:
            members = [self._adapter.conversation.user]
        else:
            members = list(members_added)
            if len(members) == 0:
                raise ValueError(
                    "TestFlow.send_conversation_update(): members_added cannot be empty."
                )

        async def step() -> None:
            await self._await_previous()

            if not self._callback:
                raise ValueError(
                    "TestFlow.send_conversation_update(): callback is required."
                )

            activity = Activity(
                type=ActivityTypes.conversation_update,
                members_added=members,
            )
            await self._adapter.process_activity(
                self._adapter.claims_identity,
                activity,
                self._callback,
            )

        return self._append(step)

    def delay(self, seconds: float) -> TestFlow:
        """Append a delay to the flow.

        :param seconds: Number of seconds to wait after previous steps complete.
        :return: A new ``TestFlow`` with this delay step appended.
        """

        if seconds < 0:
            raise ValueError("TestFlow.delay(): seconds cannot be negative.")

        async def step() -> None:
            await self._await_previous()
            await asyncio.sleep(seconds)

        return self._append(step)

    def assert_reply(
        self,
        expected: str | Activity | ReplyValidator,
        description: str | None = None,
        *,
        timeout: float = 3.0,
    ) -> TestFlow:
        """Append an assertion for the next captured reply.

        :param expected: Expected reply text, expected activity, or a validator
            callable. Validators receive the next reply and may raise an
            assertion error or return an awaitable.
        :param description: Optional failure description.
        :param timeout: Seconds to wait for the next reply.
        :return: A new ``TestFlow`` with this assertion appended.
        """

        async def step() -> None:
            await self._await_previous()
            reply = await self._get_next_reply(timeout)

            if reply is None:
                raise AssertionError(
                    description
                    or f"Expected a reply within {timeout} seconds, but no reply was received."
                )

            if callable(expected):
                result = expected(reply)
                if isawaitable(result):
                    await result
                return

            if isinstance(expected, str):
                if reply.text != expected:
                    raise AssertionError(
                        description
                        or f"Expected reply text '{expected}', received '{reply.text}'."
                    )
                return

            self._assert_activity(expected, reply, description)

        return self._append(step)

    def assert_reply_contains(
        self,
        expected: str,
        description: str | None = None,
        *,
        timeout: float = 3.0,
    ) -> TestFlow:
        """Append an assertion that the next reply contains text.

        :param expected: Text expected to appear in the next reply.
        :param description: Optional failure description.
        :param timeout: Seconds to wait for the next reply.
        :return: A new ``TestFlow`` with this assertion appended.
        """

        async def validate(reply: Activity) -> None:
            if expected not in (reply.text or ""):
                raise AssertionError(
                    description
                    or f"Expected reply text to contain '{expected}', received '{getattr(reply, 'text', None)}'."
                )

        return self.assert_reply(validate, timeout=timeout)

    def assert_typing_indicator(self, *, timeout: float = 3.0) -> TestFlow:
        """Append an assertion that the next reply is a typing activity."""

        async def validate(reply: Activity) -> None:
            if reply.type != ActivityTypes.typing:
                raise AssertionError(
                    f"Expected typing activity, received '{getattr(reply, 'type', None)}'."
                )

        return self.assert_reply(validate, timeout=timeout)

    def assert_no_more_replies(self, *, timeout: float = 0.3) -> TestFlow:
        """Append an assertion that no reply arrives within ``timeout`` seconds."""

        async def step() -> None:
            await self._await_previous()
            reply = await self._get_next_reply(timeout)
            if reply is not None:
                raise AssertionError(f"Expected no more replies, received {reply!r}.")

        return self._append(step)

    def test(
        self,
        user_input: str | Activity,
        expected: str | Activity | ReplyValidator,
        *,
        timeout: float = 3.0,
    ) -> TestFlow:
        """Append a send followed by an expected reply assertion."""

        return self.send(user_input).assert_reply(expected, timeout=timeout)

    def test_activities(self, activities: Iterable[Activity]) -> TestFlow:
        """Append sends and assertions from a mixed activity transcript.

        Activities whose sender role is ``agent`` are treated as expected
        replies. All other activities are sent as user input.
        """

        flow: TestFlow = self
        for activity in activities:
            role = getattr(activity.from_property, "role", None)
            if role == RoleTypes.agent:
                flow = flow.assert_reply(activity)
            else:
                flow = flow.send(activity)
        return flow

    def _append(self, step: Callable[[], Coroutine[Any, Any, None]]) -> TestFlow:
        task = asyncio.create_task(step())
        return TestFlow(self._adapter, self._callback, task=task)

    async def _await_previous(self) -> None:
        if self._task:
            await self._task

    async def _get_next_reply(self, timeout: float) -> Activity | None:
        try:
            return await asyncio.wait_for(
                self._adapter.get_next_reply_async(), timeout=timeout
            )
        except asyncio.TimeoutError:
            return None

    @staticmethod
    def _assert_activity(
        expected: Activity,
        actual: Activity,
        description: str | None,
    ) -> None:
        if actual.type != expected.type:
            raise AssertionError(
                description
                or f"Expected reply type '{expected.type}', received '{actual.type}'."
            )

        if expected.text is not None and actual.text != expected.text:
            raise AssertionError(
                description
                or f"Expected reply text '{expected.text}', received '{actual.text}'."
            )

        if expected.input_hint is not None and actual.input_hint != expected.input_hint:
            raise AssertionError(
                description
                or (
                    f"Expected reply input_hint '{expected.input_hint}', "
                    f"received '{actual.input_hint}'."
                )
            )

        if expected.speak is not None and actual.speak != expected.speak:
            raise AssertionError(
                description
                or f"Expected reply speak '{expected.speak}', received '{actual.speak}'."
            )
