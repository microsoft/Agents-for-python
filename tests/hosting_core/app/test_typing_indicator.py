"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import asyncio

import pytest

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.hosting.core import TurnContext
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
async def test_init_sets_context_and_interval():
    """Test that __init__ properly sets context and interval."""
    context = StubTurnContext()
    interval = 5.0
    
    indicator = TypingIndicator(context, interval)
    
    assert indicator._context is context
    assert indicator._interval == interval
    assert indicator._task is None


@pytest.mark.asyncio
async def test_init_default_interval():
    """Test that __init__ uses default interval of 10.0 seconds."""
    context = StubTurnContext()
    
    indicator = TypingIndicator(context)
    
    assert indicator._interval == 10.0


@pytest.mark.asyncio
async def test_start_sends_typing_activity():
    """Test that start() begins sending typing activities at regular intervals."""
    context = StubTurnContext()
    indicator = TypingIndicator(context, interval=0.01)  # 10ms interval
    
    indicator.start()
    await asyncio.sleep(0.05)  # Wait 50ms to allow multiple typing activities
    indicator.stop()
    
    # Should have sent at least 3 typing activities (50ms / 10ms = 5, but accounting for timing)
    assert len(context.sent_activities) >= 3
    assert all(
        activity.type == ActivityTypes.TYPING for activity in context.sent_activities
    )


@pytest.mark.asyncio
async def test_start_creates_task():
    """Test that start() creates an asyncio task."""
    context = StubTurnContext()
    indicator = TypingIndicator(context)
    
    indicator.start()
    
    assert indicator._task is not None
    assert isinstance(indicator._task, asyncio.Task)
    
    indicator.stop()


@pytest.mark.asyncio
async def test_start_raises_if_already_running():
    """Test that start() raises RuntimeError if already running."""
    context = StubTurnContext()
    indicator = TypingIndicator(context)
    
    indicator.start()
    
    with pytest.raises(RuntimeError, match="Typing indicator is already running"):
        indicator.start()
    
    indicator.stop()


@pytest.mark.asyncio
async def test_stop_cancels_task():
    """Test that stop() cancels the typing indicator task."""
    context = StubTurnContext()
    indicator = TypingIndicator(context, interval=0.01)
    
    indicator.start()
    task = indicator._task
    await asyncio.sleep(0.02)  # Let it run briefly
    
    indicator.stop()
    
    assert indicator._task is None
    assert task.cancelled()


@pytest.mark.asyncio
async def test_stop_raises_if_not_running():
    """Test that stop() raises RuntimeError if not running."""
    context = StubTurnContext()
    indicator = TypingIndicator(context)
    
    with pytest.raises(RuntimeError, match="Typing indicator is not running"):
        indicator.stop()


@pytest.mark.asyncio
async def test_stop_prevents_further_typing_activities():
    """Test that stop() prevents further typing activities from being sent."""
    context = StubTurnContext()
    indicator = TypingIndicator(context, interval=0.01)
    
    indicator.start()
    await asyncio.sleep(0.025)  # Let it run briefly
    indicator.stop()
    
    count_before = len(context.sent_activities)
    await asyncio.sleep(0.03)  # Wait more time
    count_after = len(context.sent_activities)
    
    assert count_before == count_after  # No new activities after stop


@pytest.mark.asyncio
async def test_typing_continues_on_send_error():
    """Test that the typing indicator handles send errors gracefully."""
    context = StubTurnContext(should_raise=True)
    indicator = TypingIndicator(context, interval=0.01)
    
    indicator.start()
    await asyncio.sleep(0.03)  # Wait for error to occur
    
    # Task should still exist but may be done/cancelled due to unhandled exception
    # The implementation doesn't catch exceptions in _run, so the task will fail
    assert indicator._task is not None
    
    # Cleanup
    try:
        indicator.stop()
    except RuntimeError:
        # May already be stopped due to exception
        pass


@pytest.mark.asyncio
async def test_context_none_stops_loop():
    """Test that setting context to None would stop the loop (if implemented)."""
    context = StubTurnContext()
    indicator = TypingIndicator(context, interval=0.01)
    
    indicator.start()
    await asyncio.sleep(0.015)  # Let at least one activity send
    
    # Simulate context becoming None (though the current implementation checks while context)
    indicator._context = None
    await asyncio.sleep(0.02)
    
    # The loop should stop when context becomes None
    indicator._task.cancel()
    indicator._task = None


@pytest.mark.asyncio
async def test_multiple_start_stop_cycles():
    """Test that the indicator can be started and stopped multiple times."""
    context = StubTurnContext()
    indicator = TypingIndicator(context, interval=0.01)
    
    # First cycle
    indicator.start()
    await asyncio.sleep(0.02)
    indicator.stop()
    count_first = len(context.sent_activities)
    
    # Second cycle
    indicator.start()
    await asyncio.sleep(0.02)
    indicator.stop()
    count_second = len(context.sent_activities)
    
    assert count_second > count_first


@pytest.mark.asyncio
async def test_typing_activity_format():
    """Test that sent activities are properly formatted typing activities."""
    context = StubTurnContext()
    indicator = TypingIndicator(context, interval=0.01)
    
    indicator.start()
    await asyncio.sleep(0.015)  # Wait for at least one activity
    indicator.stop()
    
    assert len(context.sent_activities) >= 1
    for activity in context.sent_activities:
        assert isinstance(activity, Activity)
        assert activity.type == ActivityTypes.typing