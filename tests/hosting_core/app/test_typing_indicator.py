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
    indicator = TypingIndicator(interval=10)  # 10ms interval

    await indicator.start(context)
    await asyncio.sleep(0.05)  # Wait 50ms to allow multiple typing activities
    indicator.stop()

    assert len(context.sent_activities) >= 1
    assert all(
        activity.type == ActivityTypes.typing for activity in context.sent_activities
    )


@pytest.mark.asyncio
async def test_start_is_idempotent():
    context = StubTurnContext()
    indicator = TypingIndicator(interval=10)

    await indicator.start(context)
    first_timer = indicator._timer  # noqa: SLF001 - accessing for test verification

    await indicator.start(context)
    second_timer = indicator._timer  # noqa: SLF001

    assert first_timer is second_timer

    indicator.stop()


@pytest.mark.asyncio
async def test_stop_without_start_is_noop():
    indicator = TypingIndicator()

    indicator.stop()  # stop() is now synchronous

    assert indicator._timer is None  # noqa: SLF001


@pytest.mark.asyncio
async def test_typing_stops_on_send_error():
    context = StubTurnContext(should_raise=True)
    indicator = TypingIndicator(interval=10)

    await indicator.start(context)

    # Wait a bit to allow the error to occur and timer to be cancelled
    await asyncio.sleep(0.05)

    # The timer should be cancelled due to the error
    assert indicator._timer is None  # noqa: SLF001

    indicator.stop()  # Cleanup, should be safe even if already stopped
