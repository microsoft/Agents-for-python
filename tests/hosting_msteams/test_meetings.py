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
    from microsoft_teams.api.activities.event.meeting_end import MeetingEndEventValue
    from microsoft_teams.api.activities.event.meeting_start import (
        MeetingStartEventValue,
    )
    from microsoft_agents.activity.teams import MeetingParticipantsEventDetails
    from microsoft_agents.hosting.msteams import TeamsAgentExtension


def _meeting_start_value() -> dict:
    return {
        "Id": "meeting-id",
        "MeetingType": "Scheduled",
        "JoinUrl": "https://example.com/meet",
        "Title": "Test Meeting",
        "StartTime": "2026-10-02T20:48:16.7632115Z",
    }


def _meeting_end_value() -> dict:
    return {
        "Id": "meeting-id",
        "MeetingType": "Scheduled",
        "JoinUrl": "https://example.com/meet",
        "Title": "Test Meeting",
        "EndTime": "2026-10-02T20:49:20.330067Z",
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
        async def handler(ctx, state, meeting: MeetingStartEventValue):
            await user_handler(ctx, state, meeting)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.event,
            name="application/vnd.microsoft.meetingStart",
            value=_meeting_start_value(),
        )
        await route_handler(ctx, MagicMock())
        meeting = user_handler.call_args[0][2]
        assert isinstance(meeting, MeetingStartEventValue)
        assert meeting.id == "meeting-id"
        assert meeting.meeting_type == "Scheduled"
        assert meeting.join_url == "https://example.com/meet"
        assert meeting.title == "Test Meeting"

    @pytest.mark.asyncio
    async def test_end_handler_parses_meeting_details(self):
        user_handler = AsyncMock()

        @self.ext.meetings.end()
        async def handler(ctx, state, meeting: MeetingEndEventValue):
            await user_handler(ctx, state, meeting)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.event,
            name="application/vnd.microsoft.meetingEnd",
            value=_meeting_end_value(),
        )
        await route_handler(ctx, MagicMock())
        meeting = user_handler.call_args[0][2]
        assert isinstance(meeting, MeetingEndEventValue)
        assert meeting.id == "meeting-id"
        assert meeting.meeting_type == "Scheduled"
        assert meeting.join_url == "https://example.com/meet"
        assert meeting.title == "Test Meeting"


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
