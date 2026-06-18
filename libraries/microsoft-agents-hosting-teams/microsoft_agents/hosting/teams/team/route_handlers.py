# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Protocol definition for Teams team update route handlers."""

from typing import Awaitable, Protocol

from microsoft_teams.api.models.channel_data import ChannelData

from microsoft_agents.hosting.teams.teams_turn_context import TeamsTurnContext
from microsoft_agents.hosting.teams.type_defs import StateT


class TeamUpdateHandler(Protocol[StateT]):
    """Protocol for a handler invoked on Teams team conversation update events."""

    def __call__(
        self,
        context: TeamsTurnContext,
        state: StateT,
        data: ChannelData,
    ) -> Awaitable[None]:
        """Handle a team update event.

        :param context: Teams-aware turn context.
        :param state: The current turn state.
        :param data: Parsed team data from the incoming activity's channel_data.
        """
        ...
