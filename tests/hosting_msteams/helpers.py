# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Shared test helpers for microsoft-agents-hosting-teams tests."""

import sys
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from microsoft_agents.activity import Activity, ActivityTypes, ResourceResponse
from microsoft_agents.activity._model_utils import SkipNone, pick_model
from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.hosting.core.app import AgentApplication, RouteRank

is_supported_version = sys.version_info >= (3, 11)

if is_supported_version:
    from microsoft_agents.hosting.msteams.teams_turn_context import TeamsTurnContext


class _FakeServiceSet:
    def __init__(self):
        self._state = {}

    def get(self, key):
        return self._state.get(key)

    def has(self, key):
        return key in self._state

    def set(self, key, value):
        self._state[key] = value


class _FakeAdapter:
    def __init__(self):
        self.sent_activities = []

    async def send_activities(self, context, activities):
        self.sent_activities.extend(activities)
        return [ResourceResponse()] * len(activities)


def _make_app() -> Any:
    app = MagicMock(spec=AgentApplication)
    app._routes = []

    def _add_route(
        selector, handler, is_invoke=False, rank=RouteRank.DEFAULT, auth_handlers=None
    ):
        app._routes.append(
            dict(
                selector=selector,
                handler=handler,
                is_invoke=is_invoke,
                rank=rank,
                auth_handlers=auth_handlers,
            )
        )

    app.add_route.side_effect = _add_route
    return app


def _make_context(
    activity_type: str,
    name: str = None,
    value=None,
    channel_id: str = "msteams",
    channel_data: dict = None,
    members_added=None,
    members_removed=None,
) -> TurnContext:
    activity = pick_model(
        Activity,
        type=activity_type,
        name=SkipNone(name),
        value=SkipNone(value),
        service_url="https://smba.trafficmanager.net/teams/",
        channel_id=channel_id,
        channel_data=SkipNone(channel_data),
    )
    activity.members_added = members_added
    activity.members_removed = members_removed

    context = TurnContext(_FakeAdapter(), activity, MagicMock())
    context.send_activity = AsyncMock()
    return context


def _make_teams_context() -> "TeamsTurnContext":
    """Return a MagicMock shaped like a TeamsTurnContext for use in unit tests."""
    ctx = MagicMock(spec=TeamsTurnContext)
    ctx.send_activity = AsyncMock()
    return ctx
