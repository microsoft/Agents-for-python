# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
import sys
from typing import Callable, List, Optional, TypeVar, Union, Any, Dict
from datetime import timedelta
from functools import reduce

from microsoft_agents.activity import Activity
from microsoft_agents.hosting.core import Connections

T = TypeVar("T")


# currently unused (probably outdated)
# but may be useful to bring up-to-date for future testing scenarios
class TestClient:
    """
    A testing channel that connects directly to an adapter.

    You can use this class to mimic input from a user or a channel to validate
    that the agent or adapter responds as expected.
    """

    def __init__(self, adapter, callback=None):
        """
        Initializes a new instance of the TestingFlow class.

        Args:
            adapter: The test adapter to use.
            callback: The agent turn processing logic to test.
        """
        self._adapter = adapter
        self._callback = callback
        self._test_task = asyncio.create_task(asyncio.sleep(0))

    @classmethod
    def _clone(cls, task, client):
        new_flow = cls(client._adapter, client._callback)
        new_flow._test_task = task
        return new_flow

    async def start_test_async(self):
        """
        Starts the execution of the test flow.

        Returns:
            A Task that runs the exchange between the user and the agent.
        """
        return await self._test_task

    def send(self, user_says):
        """
        Adds a message activity from the user to the agent.

        Args:
            user_says: The text of the message to send or an Activity.

        Returns:
            A new TestingFlow object that appends a new message activity from the user to the modeled exchange.
        """
        if user_says is None:
            raise ValueError("You have to pass a userSays parameter")

        async def new_task():
            await self._test_task

            if isinstance(user_says, str):
                await self._adapter.send_text_to_bot_async(user_says, self._callback)
            else:
                await self._adapter.process_activity_async(user_says, self._callback)

        return TestingFlow._create_from_flow(new_task(), self)

    def send_conversation_update(self):
        """
        Creates a conversation update activity and processes the activity.

        Returns:
            A new TestingFlow object.
        """

        async def new_task():
            await self._test_task

            cu = Activity.create_conversation_update_activity()
            cu.members_added.append(self._adapter.conversation.user)
            await self._adapter.process_activity_async(cu, self._callback)

        return TestingFlow._create_from_flow(new_task(), self)

    def delay(self, ms_or_timespan):
        """
        Adds a delay in the conversation.

        Args:
            ms_or_timespan: The delay length in milliseconds or a timedelta.

        Returns:
            A new TestingFlow object that appends a delay to the modeled exchange.
        """

        async def new_task():
            await self._test_task

            if isinstance(ms_or_timespan, timedelta):
                delay_seconds = ms_or_timespan.total_seconds()
            else:
                delay_seconds = ms_or_timespan / 1000.0

            await asyncio.sleep(delay_seconds)

        return TestingFlow._create_from_flow(new_task(), self)

    def assert_reply(self, expected, description=None, timeout=3000):
        """
        Adds an assertion that the turn processing logic responds as expected.

        Args:
            expected: The expected text, activity, or validation function to apply to the bot's response.
            description: A message to send if the actual response is not as expected.
            timeout: The amount of time in milliseconds within which a response is expected.

        Returns:
            A new TestingFlow object that appends this assertion to the modeled exchange.
        """
        if isinstance(expected, str):
            expected_activity = self._adapter.make_activity(expected)
            return self._assert_reply_activity(
                expected_activity, description or expected, timeout
            )
        elif callable(expected):
            return self._assert_reply_validate(expected, description, timeout)
        else:
            return self._assert_reply_activity(expected, description, timeout)

    def _assert_reply_activity(
        self, expected_activity, description=None, timeout=3000, equality_comparer=None
    ):
        """
        Implementation for asserting replies with an expected activity.
        """

        async def validate_activity(reply):
            description_text = description or (
                expected_activity.text.strip()
                if hasattr(expected_activity, "text") and expected_activity.text
                else None
            )

            if expected_activity.type != reply.type:
                raise ValueError(f"{description_text}: Type should match")

            if equality_comparer:
                if not equality_comparer(expected_activity, reply):
                    raise ValueError(f"Expected:{expected_activity}\nReceived:{reply}")
            else:
                expected_text = (
                    expected_activity.text.strip()
                    if hasattr(expected_activity, "text") and expected_activity.text
                    else ""
                )
                actual_text = (
                    reply.text.strip() if hasattr(reply, "text") and reply.text else ""
                )

                if expected_text != actual_text:
                    if description_text:
                        raise ValueError(
                            f"{description_text}:\nExpected:{expected_text}\nReceived:{actual_text}"
                        )
                    else:
                        raise ValueError(
                            f"Expected:{expected_text}\nReceived:{actual_text}"
                        )

        return self._assert_reply_validate(validate_activity, description, timeout)

    def _assert_reply_validate(self, validate_activity, description=None, timeout=3000):
        """
        Implementation for asserting replies with a validation function.
        """

        async def new_task():
            await self._test_task

            # If debugger is attached, extend the timeout
            if hasattr(sys, "gettrace") and sys.gettrace():
                timeout_ms = sys.maxsize
            else:
                timeout_ms = timeout

            try:
                reply_activity = await asyncio.wait_for(
                    self._adapter.get_next_reply_async(), timeout=timeout_ms / 1000.0
                )

                if callable(validate_activity):
                    if asyncio.iscoroutinefunction(validate_activity):
                        await validate_activity(reply_activity)
                    else:
                        validate_activity(reply_activity)

            except asyncio.TimeoutError:
                raise TimeoutError(
                    f"No reply received within the timeout period of {timeout_ms}ms"
                )

        return TestingFlow._create_from_flow(new_task(), self)

    def assert_reply_contains(self, expected, description=None, timeout=3000):
        """
        Adds an assertion that the turn processing logic response contains the expected text.

        Args:
            expected: The part of the expected text of a message from the bot.
            description: A message to send if the actual response is not as expected.
            timeout: The amount of time in milliseconds within which a response is expected.

        Returns:
            A new TestingFlow object that appends this assertion to the modeled exchange.
        """

        def validate_contains(reply):
            if (
                reply is None
                or not hasattr(reply, "text")
                or expected not in reply.text
            ):
                if description is None:
                    raise ValueError(
                        f"Expected:{expected}\nReceived:{reply.text if hasattr(reply, 'text') else 'Not a Message Activity'}"
                    )
                else:
                    raise ValueError(
                        f"{description}:\nExpected:{expected}\nReceived:{reply.text if hasattr(reply, 'text') else 'Not a Message Activity'}"
                    )

        return self._assert_reply_validate(validate_contains, description, timeout)

    def assert_no_reply(self, description=None, timeout=3000):
        """
        Adds an assertion that the turn processing logic finishes responding as expected.

        Args:
            description: A message to send if the turn still responds.
            timeout: The amount of time in milliseconds within which no response is expected.

        Returns:
            A new TestingFlow object that appends this assertion to the modeled exchange.
        """

        async def new_task():
            await self._test_task

            try:
                reply_activity = await asyncio.wait_for(
                    self._adapter.get_next_reply_async(), timeout=timeout / 1000.0
                )

                if reply_activity is not None:
                    raise ValueError(
                        f"{reply_activity} is responded when waiting for no reply:'{description}'"
                    )

            except asyncio.TimeoutError:
                # Expected behavior - no response within timeout
                pass

        return TestingFlow._create_from_flow(new_task(), self)

    def test(self, user_says, expected=None, description=None, timeout=3000):
        """
        Shortcut for calling send followed by assert_reply.

        Args:
            user_says: The text of the message to send.
            expected: The expected response, text, activity, or validation function.
            description: A message to send if the actual response is not as expected.
            timeout: The amount of time in milliseconds within which a response is expected.

        Returns:
            A new TestingFlow object that appends this exchange to the modeled exchange.
        """
        if expected is None:
            raise ValueError("expected parameter is required")

        return self.send(user_says).assert_reply(expected, description, timeout)

    def test_activities(
        self, activities, validate_reply=None, description=None, timeout=3000
    ):
        """
        Shortcut for adding an arbitrary exchange between the user and bot.

        Args:
            activities: The list of activities to test.
            validate_reply: Optional delegate to call to validate responses from the bot.
            description: A message to send if the actual response is not as expected.
            timeout: The amount of time in milliseconds within which a response is expected.

        Returns:
            A new TestingFlow object that appends this exchange to the modeled exchange.
        """
        if activities is None:
            raise ValueError("activities parameter is required")

        def process_activity(flow, activity):
            if self._is_reply(activity):
                if validate_reply:
                    return flow.assert_reply(
                        lambda actual: validate_reply(activity, actual),
                        description,
                        timeout,
                    )
                else:
                    return flow.assert_reply(activity, description, timeout)
            else:
                return flow.send(activity)

        return reduce(process_activity, activities, self)

    def assert_reply_one_of(self, candidates, description=None, timeout=3000):
        """
        Adds an assertion that the bot's response is contained within a set of acceptable responses.

        Args:
            candidates: The set of acceptable messages.
            description: A message to send if the actual response is not as expected.
            timeout: The amount of time in milliseconds within which a response is expected.

        Returns:
            A new TestingFlow object that appends this assertion to the modeled exchange.
        """
        if candidates is None:
            raise ValueError("candidates parameter is required")

        def validate_one_of(reply):
            if not hasattr(reply, "text"):
                raise ValueError(f"Reply does not have text property: {reply}")

            text = reply.text

            for candidate in candidates:
                if text == candidate:
                    return

            message = (
                description
                or f"Text \"{text}\" does not match one of candidates: {', '.join(candidates)}"
            )
            raise ValueError(message)

        return self._assert_reply_validate(validate_one_of, description, timeout)

    @staticmethod
    def _is_reply(activity):
        """
        Determines if an activity is a reply from a bot.

        Args:
            activity: The activity to check.

        Returns:
            True if the activity is from a bot, False otherwise.
        """
        return (
            hasattr(activity, "from_property")
            and hasattr(activity.from_property, "role")
            and activity.from_property.role.lower() == "bot"
        )
