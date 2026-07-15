# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for TeamsAgentExtension.meetings (meeting lifecycle events)."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from microsoft_agents.activity import ActivityTypes

from .helpers import _make_app, _make_context, is_supported_version

pytestmark = pytest.mark.skipif(
    not is_supported_version,
    reason="microsoft-agents-hosting-teams tests require Python 3.11+",
)

if is_supported_version:
    from microsoft_teams.api.models.meetings import MeetingDetails
    from microsoft_agents.activity.teams import MeetingParticipantsEventDetails
    from microsoft_agents.hosting.msteams import TeamsAgentExtension


def _meeting_details_value() -> dict:
    return {
        "id": "meeting-id",
        "type": "scheduled",
        "joinUrl": "https://example.com/meet",
        "title": "Test Meeting",
        "msGraphResourceId": "graph-id",
    }


class TestMeetingStartEnd:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    def test_start_selector(self):
        @self.ext.meetings.start()
        async def handler(ctx, state, meeting): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.event, name="application/vnd.microsoft.meetingStart"
                )
            )
            is True
        )
        assert (
            selector(
                _make_context(
                    ActivityTypes.event, name="application/vnd.microsoft.meetingEnd"
                )
            )
            is False
        )

    def test_end_selector(self):
        @self.ext.meetings.end()
        async def handler(ctx, state, meeting): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.event, name="application/vnd.microsoft.meetingEnd"
                )
            )
            is True
        )
        assert (
            selector(
                _make_context(
                    ActivityTypes.event, name="application/vnd.microsoft.meetingStart"
                )
            )
            is False
        )

    def test_start_is_not_invoke(self):
        @self.ext.meetings.start()
        async def handler(ctx, state, meeting): ...

        assert self.app._routes[0]["is_invoke"] is False

    def test_end_is_not_invoke(self):
        @self.ext.meetings.end()
        async def handler(ctx, state, meeting): ...

        assert self.app._routes[0]["is_invoke"] is False

    @pytest.mark.asyncio
    async def test_start_handler_parses_meeting_details(self):
        user_handler = AsyncMock()

        @self.ext.meetings.start()
        async def handler(ctx, state, meeting: MeetingDetails):
            await user_handler(ctx, state, meeting)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.event,
            name="application/vnd.microsoft.meetingStart",
            value=_meeting_details_value(),
        )
        await route_handler(ctx, MagicMock())
        assert isinstance(user_handler.call_args[0][2], MeetingDetails)

    @pytest.mark.asyncio
    async def test_end_handler_parses_meeting_details(self):
        user_handler = AsyncMock()

        @self.ext.meetings.end()
        async def handler(ctx, state, meeting: MeetingDetails):
            await user_handler(ctx, state, meeting)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.event,
            name="application/vnd.microsoft.meetingEnd",
            value=_meeting_details_value(),
        )
        await route_handler(ctx, MagicMock())
        assert isinstance(user_handler.call_args[0][2], MeetingDetails)


class TestMeetingParticipants:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    def test_participants_join_selector(self):
        @self.ext.meetings.participants_join()
        async def handler(ctx, state, details): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.event,
                    name="application/vnd.microsoft.meetingParticipantJoin",
                )
            )
            is True
        )
        assert (
            selector(
                _make_context(
                    ActivityTypes.event,
                    name="application/vnd.microsoft.meetingParticipantLeave",
                )
            )
            is False
        )

    def test_participants_leave_selector(self):
        @self.ext.meetings.participants_leave()
        async def handler(ctx, state, details): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.event,
                    name="application/vnd.microsoft.meetingParticipantLeave",
                )
            )
            is True
        )
        assert (
            selector(
                _make_context(
                    ActivityTypes.event,
                    name="application/vnd.microsoft.meetingParticipantJoin",
                )
            )
            is False
        )

    def test_participants_join_is_not_invoke(self):
        @self.ext.meetings.participants_join()
        async def handler(ctx, state, details): ...

        assert self.app._routes[0]["is_invoke"] is False

    @pytest.mark.asyncio
    async def test_participants_join_handler_parses_details(self):
        user_handler = AsyncMock()

        @self.ext.meetings.participants_join()
        async def handler(ctx, state, details: MeetingParticipantsEventDetails):
            await user_handler(ctx, state, details)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.event,
            name="application/vnd.microsoft.meetingParticipantJoin",
            value={},
        )
        await route_handler(ctx, MagicMock())
        assert isinstance(user_handler.call_args[0][2], MeetingParticipantsEventDetails)

    @pytest.mark.asyncio
    async def test_participants_leave_handler_parses_details(self):
        user_handler = AsyncMock()

        @self.ext.meetings.participants_leave()
        async def handler(ctx, state, details: MeetingParticipantsEventDetails):
            await user_handler(ctx, state, details)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.event,
            name="application/vnd.microsoft.meetingParticipantLeave",
            value={},
        )
        await route_handler(ctx, MagicMock())
        assert isinstance(user_handler.call_args[0][2], MeetingParticipantsEventDetails)


class TestMeetingDirectDecoratorStyle:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    def test_start_direct(self):
        @self.ext.meetings.start  # type: ignore[arg-type]
        async def handler(ctx, state, meeting): ...

        assert self.app._routes[0]["selector"] is not None

    def test_end_direct(self):
        @self.ext.meetings.end  # type: ignore[arg-type]
        async def handler(ctx, state, meeting): ...

        assert self.app._routes[0]["selector"] is not None

    def test_participants_join_direct(self):
        @self.ext.meetings.participants_join  # type: ignore[arg-type]
        async def handler(ctx, state, details): ...

        assert self.app._routes[0]["selector"] is not None

    def test_participants_leave_direct(self):
        @self.ext.meetings.participants_leave  # type: ignore[arg-type]
        async def handler(ctx, state, details): ...

        assert self.app._routes[0]["selector"] is not None
