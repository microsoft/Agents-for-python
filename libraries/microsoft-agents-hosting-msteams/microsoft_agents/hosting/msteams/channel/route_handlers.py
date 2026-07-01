# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Protocol definition for Teams channel update route handlers."""

from typing import Awaitable, Protocol

from microsoft_teams.api.models.channel_data import ChannelData

from microsoft_agents.hosting.msteams.teams_turn_context import TeamsTurnContext
from microsoft_agents.hosting.msteams.type_defs import _StateContra


class ChannelUpdateHandler(Protocol[_StateContra]):
    """Protocol for a handler invoked on Teams channel update events.

    Handlers receive the Teams turn context, the current turn state, and the
    parsed :class:`ChannelData` from the activity.
    """

    def __call__(
        self,
        context: TeamsTurnContext,
        state: _StateContra,
        data: ChannelData,
        /,
    ) -> Awaitable[None]:
        """Handle a channel update event.

        :param context: Teams-aware turn context.
        :param state: The current turn state.
        :param data: Parsed channel data from the incoming activity.
        :return: An awaitable that completes when the handler finishes.
        """
        ...
