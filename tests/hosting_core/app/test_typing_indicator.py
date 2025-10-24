import asyncio

import pytest

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.hosting.core.app.typing_indicator import TypingIndicator


class StubTurnContext:
    """Test double that tracks sent activities."""

    def __init__(self, should_raise: bool = False) -> None:
        self.sent_activities = []
        self.should_raise = should_raise

    async def send_activity(self, activity: Activity):
        if self.should_raise:
            raise RuntimeError("send_activity failure")
        self.sent_activities.append(activity)
        return None


@pytest.mark.asyncio
async def test_start_sends_typing_activity():
    context = StubTurnContext()
    indicator = TypingIndicator(intervalSeconds=0.01)

    await indicator.start(context)
    await asyncio.sleep(0.03)
    await indicator.stop()

    assert len(context.sent_activities) >= 1
    assert all(
        activity.type == ActivityTypes.typing for activity in context.sent_activities
    )


@pytest.mark.asyncio
async def test_start_is_idempotent():
    context = StubTurnContext()
    indicator = TypingIndicator(intervalSeconds=0.01)

    await indicator.start(context)
    first_task = indicator._task  # noqa: SLF001 - accessing for test verification

    await indicator.start(context)
    second_task = indicator._task  # noqa: SLF001

    assert first_task is second_task

    await indicator.stop()


@pytest.mark.asyncio
async def test_stop_without_start_is_noop():
    indicator = TypingIndicator()

    await indicator.stop()

    assert indicator._task is None  # noqa: SLF001
    assert indicator._running is False  # noqa: SLF001


@pytest.mark.asyncio
async def test_typing_loop_stops_on_send_error():
    context = StubTurnContext(should_raise=True)
    indicator = TypingIndicator(intervalSeconds=0.01)

    await indicator.start(context)
    await asyncio.sleep(0.02)

    assert indicator._task is not None  # noqa: SLF001
    await asyncio.wait_for(indicator._task, timeout=0.1)  # Ensure loop exits

    assert indicator._running is False  # noqa: SLF001
    assert indicator._task.done()  # noqa: SLF001

    await indicator.stop()
