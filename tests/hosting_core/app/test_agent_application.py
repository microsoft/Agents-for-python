"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.hosting.core import MemoryStorage
from microsoft_agents.hosting.core.app import (
    AgentApplication,
    ApplicationOptions,
    TurnState,
)


class StubAdapter:
    """Minimal adapter for testing AgentApplication._on_turn."""

    def __init__(self):
        self.sent_activities: list[Activity] = []

    async def send_activities(self, context, activities):
        self.sent_activities.extend(activities)
        return [None] * len(activities)


class StubTurnContext:
    """Minimal TurnContext double for AgentApplication tests."""

    def __init__(self, activity: Activity, adapter=None):
        self.activity = activity
        self.adapter = adapter or StubAdapter()
        self._on_send_handlers = []
        self.turn_state = {}
        self.responded = False

    def on_send_activities(self, handler):
        self._on_send_handlers.append(handler)

    async def send_activity(self, activity):
        self.responded = True


@pytest.mark.asyncio
async def test_on_turn_no_typing_when_start_typing_timer_false():
    """When start_typing_timer=False, no typing indicators should be sent."""
    adapter = StubAdapter()
    app = AgentApplication[TurnState](
        options=ApplicationOptions(
            storage=MemoryStorage(),
            start_typing_timer=False,
        )
    )

    context = StubTurnContext(
        Activity(
            type=ActivityTypes.message,
            text="hello",
            channel_id="test",
            conversation={"id": "conv1"},
            from_property={"id": "user1"},
            recipient={"id": "bot1"},
            service_url="https://test",
        ),
        adapter=adapter,
    )

    # Patch internals to avoid needing full infrastructure
    with patch.object(app, "_remove_mentions"), patch.object(
        app, "_initialize_state", new_callable=AsyncMock, return_value=TurnState()
    ), patch.object(
        app, "_run_before_turn_middleware", new_callable=AsyncMock, return_value=True
    ), patch.object(
        app, "_handle_file_downloads", new_callable=AsyncMock
    ), patch.object(
        app, "_on_activity", new_callable=AsyncMock
    ), patch.object(
        app, "_run_after_turn_middleware", new_callable=AsyncMock, return_value=True
    ):
        await app._on_turn(context)

    # Give any background tasks a chance to fire (they shouldn't)
    await asyncio.sleep(0.1)

    # No typing activities should have been sent via adapter
    typing_activities = [
        a for a in adapter.sent_activities if a.type == ActivityTypes.typing
    ]
    assert len(typing_activities) == 0

    # No on_send_activities hook should have been registered
    assert len(context._on_send_handlers) == 0
