# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""End-to-end routing integration tests for ``TeamsAgentExtension``.

Unlike the other ``hosting_msteams`` test modules (which register routes on a
mocked ``AgentApplication`` and invoke handlers/selectors directly), these tests
wire a **real** :class:`AgentApplication` to a real :class:`TeamsAgentExtension`
and drive activities through :meth:`AgentApplication.on_turn`. They verify that
Teams routes are actually registered, selected, and executed by the core routing
engine -- and that non-matching activities do not trigger them.

The only test double is a minimal adapter that records sent activities; the turn
context, routing, state initialization, and Teams context upgrade all run for
real.
"""

import pytest

from microsoft_agents.activity import Activity, ActivityTypes, ResourceResponse
from microsoft_agents.hosting.core import MemoryStorage, TurnContext
from microsoft_agents.hosting.core.app import (
    AgentApplication,
    ApplicationOptions,
    TurnState,
)
from tests._common.testing_objects import TestingConnectionManager as _ConnectionManager

from .helpers import _cache_teams_api_client, is_supported_version

pytestmark = pytest.mark.skipif(
    not is_supported_version,
    reason="microsoft-agents-hosting-teams tests require Python 3.11+",
)

if is_supported_version:
    from microsoft_agents.hosting.msteams import TeamsAgentExtension
    from microsoft_agents.hosting.msteams.teams_turn_context import TeamsTurnContext


class _StubAdapter:
    """Minimal adapter that records activities sent during a turn."""

    def __init__(self):
        self.sent_activities: list[Activity] = []

    async def send_activities(self, context, activities):
        self.sent_activities.extend(activities)
        return [ResourceResponse()] * len(activities)


def _make_app() -> "AgentApplication[TurnState]":
    """Build a real AgentApplication wired for on_turn integration tests."""
    storage = MemoryStorage()
    app = AgentApplication[TurnState](
        options=ApplicationOptions(
            storage=storage,
            start_typing_timer=False,
            remove_recipient_mention=False,
        ),
        connection_manager=_ConnectionManager(),
    )
    # Shadow class-level middleware lists with fresh instance-level lists so the
    # Teams before_turn hook registered below does not leak across app instances.
    app._internal_before_turn = []
    app._internal_after_turn = []
    return app


def _make_activity(**kwargs) -> Activity:
    """Create an Activity with the fields required for state loading/routing."""
    return Activity(
        channel_id=kwargs.pop("channel_id", "msteams"),
        conversation={"id": "conv1"},
        from_property={"id": "user1"},
        recipient={"id": "bot1"},
        service_url="https://smba.trafficmanager.net/teams/",
        **kwargs,
    )


def _make_context(activity: Activity) -> TurnContext:
    context = TurnContext(_StubAdapter(), activity)
    _cache_teams_api_client(context)
    return context


class TestMessageRouteIntegration:
    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)
        self.calls: list[str] = []

    @pytest.mark.asyncio
    async def test_message_route_fires_when_text_matches(self):
        @self.ext.message("hello")
        async def handler(context, state):
            self.calls.append(context.activity.text)

        await self.app.on_turn(
            _make_context(_make_activity(type=ActivityTypes.message, text="hello"))
        )
        assert self.calls == ["hello"]

    @pytest.mark.asyncio
    async def test_message_handler_receives_teams_turn_context(self):
        captured: list[object] = []

        @self.ext.message("hello")
        async def handler(context, state):
            captured.append(context)

        await self.app.on_turn(
            _make_context(_make_activity(type=ActivityTypes.message, text="hello"))
        )
        assert len(captured) == 1
        assert isinstance(captured[0], TeamsTurnContext)

    @pytest.mark.asyncio
    async def test_message_route_not_fired_when_text_differs(self):
        @self.ext.message("hello")
        async def handler(context, state):
            self.calls.append(context.activity.text)

        await self.app.on_turn(
            _make_context(_make_activity(type=ActivityTypes.message, text="goodbye"))
        )
        assert self.calls == []

    @pytest.mark.asyncio
    async def test_non_message_activity_does_not_fire_message_route(self):
        @self.ext.message("hello")
        async def handler(context, state):
            self.calls.append("called")

        await self.app.on_turn(
            _make_context(_make_activity(type=ActivityTypes.event, text="hello"))
        )
        assert self.calls == []


class TestActivityRouteIntegration:
    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)
        self.calls: list[str] = []

    @pytest.mark.asyncio
    async def test_activity_route_fires_for_matching_type(self):
        @self.ext.activity(ActivityTypes.event)
        async def handler(context, state):
            self.calls.append(context.activity.type)

        await self.app.on_turn(_make_context(_make_activity(type=ActivityTypes.event)))
        assert self.calls == [ActivityTypes.event]

    @pytest.mark.asyncio
    async def test_activity_route_not_fired_for_other_type(self):
        @self.ext.activity(ActivityTypes.event)
        async def handler(context, state):
            self.calls.append("called")

        await self.app.on_turn(
            _make_context(_make_activity(type=ActivityTypes.message, text="hi"))
        )
        assert self.calls == []


class TestConversationUpdateRouteIntegration:
    """Drives a Teams-specific conversation update route (message edit)."""

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)
        self.calls: list[str] = []

    def _register_edit(self):
        @self.ext.messages.edit()
        async def handler(context, state):
            self.calls.append(type(context).__name__)

    @pytest.mark.asyncio
    async def test_edit_route_fires_for_edit_event(self):
        self._register_edit()
        await self.app.on_turn(
            _make_context(
                _make_activity(
                    type=ActivityTypes.message_update,
                    channel_data={"eventType": "editMessage"},
                )
            )
        )
        assert self.calls == ["TeamsTurnContext"]

    @pytest.mark.asyncio
    async def test_edit_route_not_fired_for_other_event(self):
        self._register_edit()
        await self.app.on_turn(
            _make_context(
                _make_activity(
                    type=ActivityTypes.message_update,
                    channel_data={"eventType": "undeleteMessage"},
                )
            )
        )
        assert self.calls == []

    @pytest.mark.asyncio
    async def test_edit_route_not_fired_on_non_teams_channel(self):
        self._register_edit()
        await self.app.on_turn(
            _make_context(
                _make_activity(
                    type=ActivityTypes.message_update,
                    channel_id="webchat",
                    channel_data={"eventType": "editMessage"},
                )
            )
        )
        assert self.calls == []


class TestRouteSelectionOrderingIntegration:
    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)
        self.call_order: list[str] = []

    @pytest.mark.asyncio
    async def test_only_first_matching_route_fires(self):
        @self.ext.message("hello")
        async def first(context, state):
            self.call_order.append("first")

        @self.ext.message("hello")
        async def second(context, state):
            self.call_order.append("second")

        await self.app.on_turn(
            _make_context(_make_activity(type=ActivityTypes.message, text="hello"))
        )
        assert self.call_order == ["first"]

    @pytest.mark.asyncio
    async def test_non_matching_route_is_skipped(self):
        @self.ext.message("bye")
        async def first(context, state):
            self.call_order.append("first")

        @self.ext.message("hello")
        async def second(context, state):
            self.call_order.append("second")

        await self.app.on_turn(
            _make_context(_make_activity(type=ActivityTypes.message, text="hello"))
        )
        assert self.call_order == ["second"]

    @pytest.mark.asyncio
    async def test_distinct_routes_each_fire_for_their_own_activity(self):
        @self.ext.message("hello")
        async def on_message(context, state):
            self.call_order.append("message")

        @self.ext.activity(ActivityTypes.event)
        async def on_event(context, state):
            self.call_order.append("event")

        await self.app.on_turn(_make_context(_make_activity(type=ActivityTypes.event)))
        await self.app.on_turn(
            _make_context(_make_activity(type=ActivityTypes.message, text="hello"))
        )
        assert self.call_order == ["event", "message"]


class TestDirectRouteHooksChannelFiltering:
    """Direct hooks must only route Teams activities at core dispatch."""

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)
        self.calls: list[str] = []

    @pytest.mark.parametrize(
        "route_name",
        [
            "activity",
            "message",
            "conversation_update",
            "message_reaction",
            "message_update",
            "installation_update",
            "end_of_conversation",
            "handoff",
        ],
    )
    @pytest.mark.parametrize(
        ("channel_id", "expected"),
        [("msteams", True), ("msteams:copilot", True), ("webchat", False)],
    )
    @pytest.mark.asyncio
    async def test_direct_route_only_matches_msteams_channel(
        self, route_name: str, channel_id: str, expected: bool
    ):
        async def handler(context, state, continuation=None):
            self.calls.append("called")

        if route_name == "activity":
            self.ext.activity(ActivityTypes.event)(handler)
            route_values = {"type": ActivityTypes.event}
        elif route_name == "message":
            self.ext.message("hello")(handler)
            route_values = {"type": ActivityTypes.message, "text": "hello"}
        elif route_name == "conversation_update":
            self.ext.conversation_update("membersAdded")(handler)
            route_values = {
                "type": ActivityTypes.conversation_update,
                "members_added": [{"id": "new-member"}],
            }
        elif route_name == "message_reaction":
            self.ext.message_reaction("reactionsAdded")(handler)
            route_values = {
                "type": ActivityTypes.message_reaction,
                "reactions_added": [{"type": "like"}],
            }
        elif route_name == "message_update":
            self.ext.message_update("editMessage")(handler)
            route_values = {
                "type": ActivityTypes.message_update,
                "channel_data": {"event_type": "editMessage"},
            }
        elif route_name == "installation_update":
            self.ext.installation_update()(handler)
            route_values = {"type": ActivityTypes.installation_update}
        elif route_name == "end_of_conversation":
            self.ext.end_of_conversation()(handler)
            route_values = {"type": ActivityTypes.end_of_conversation}
        else:
            self.ext.handoff()(handler)
            route_values = {
                "type": ActivityTypes.invoke,
                "name": "handoff/action",
                "value": {"continuation": "continuation"},
            }

        await self.app._on_activity(
            _make_context(_make_activity(channel_id=channel_id, **route_values)),
            TurnState(),
        )

        assert self.calls == (["called"] if expected else [])
