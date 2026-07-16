# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Shared test helpers for microsoft-agents-hosting-teams tests."""

import sys
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.hosting.core.app import AgentApplication, RouteRank

is_supported_version = sys.version_info >= (3, 11)

if is_supported_version:
    from microsoft_agents.hosting.msteams.teams_turn_context import TeamsTurnContext


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
    context = MagicMock(spec=TurnContext)
    activity = MagicMock(spec=Activity)
    activity.type = activity_type
    activity.name = name
    activity.value = value
    activity.service_url = "https://smba.trafficmanager.net/teams/"
    activity.channel_id = channel_id
    activity.channel_data = channel_data
    activity.members_added = members_added
    activity.members_removed = members_removed
    context.activity = activity
    context.turn_state = {}
    context.send_activity = AsyncMock()

    mock_adapter = MagicMock()
    context.adapter = mock_adapter
    context._responded = False
    context._services = {}
    context._on_send_activities = []
    context._on_update_activity = []
    context._on_delete_activity = []
    context.identity = MagicMock()

    def _copy_to(target):
        target.adapter = mock_adapter
        target._activity = activity
        target._responded = False
        target._services = {}
        target._on_send_activities = []
        target._on_update_activity = []
        target._on_delete_activity = []

    context.copy_to.side_effect = _copy_to
    return context


def _make_teams_context() -> "TeamsTurnContext":
    """Return a MagicMock shaped like a TeamsTurnContext for use in unit tests."""
    ctx = MagicMock(spec=TeamsTurnContext)
    ctx.send_activity = AsyncMock()
    return ctx
