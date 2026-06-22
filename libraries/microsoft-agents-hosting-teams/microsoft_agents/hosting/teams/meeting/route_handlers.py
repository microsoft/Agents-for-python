# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Protocol definitions for Teams meeting event route handlers."""

from typing import Awaitable, Protocol

from microsoft_teams.api.models.meetings import MeetingDetails
from microsoft_agents.activity.teams import MeetingParticipantsEventDetails

from microsoft_agents.hosting.teams.teams_turn_context import TeamsTurnContext
from microsoft_agents.hosting.teams.type_defs import _StateContra


class MeetingStartHandler(Protocol[_StateContra]):
    """Protocol for a handler invoked when a Teams meeting starts."""

    def __call__(
        self,
        context: TeamsTurnContext,
        state: _StateContra,
        meeting: MeetingDetails,
        /,
    ) -> Awaitable[None]:
        """Handle a meeting start event.

        :param context: Teams-aware turn context.
        :param state: The current turn state.
        :param meeting: Details of the meeting that started.
        """
        ...


class MeetingEndHandler(Protocol[_StateContra]):
    """Protocol for a handler invoked when a Teams meeting ends."""

    def __call__(
        self,
        context: TeamsTurnContext,
        state: _StateContra,
        meeting: MeetingDetails,
        /,
    ) -> Awaitable[None]:
        """Handle a meeting end event.

        :param context: Teams-aware turn context.
        :param state: The current turn state.
        :param meeting: Details of the meeting that ended.
        """
        ...


class MeetingParticipantsEventHandler(Protocol[_StateContra]):
    """Protocol for a handler invoked when participants join or leave a Teams meeting."""

    def __call__(
        self,
        context: TeamsTurnContext,
        state: _StateContra,
        meeting: MeetingParticipantsEventDetails,
        /,
    ) -> Awaitable[None]:
        """Handle a meeting participant join or leave event.

        :param context: Teams-aware turn context.
        :param state: The current turn state.
        :param meeting: Details of the participants event.
        """
        ...
