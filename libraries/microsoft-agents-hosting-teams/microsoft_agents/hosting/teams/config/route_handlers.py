# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Protocol definition for Teams configuration route handlers."""

from typing import Any, Awaitable, Protocol

from microsoft_teams.api.models.config import ConfigResponse

from microsoft_agents.hosting.teams.teams_turn_context import TeamsTurnContext
from microsoft_agents.hosting.teams.type_defs import StateT


class ConfigHandler(Protocol[StateT]):
    """Protocol for a handler invoked on Teams config/fetch or config/submit activities.

    The handler returns a :class:`ConfigResponse` which is automatically sent back
    as an invoke response by the routing layer.
    """

    def __call__(
        self,
        context: TeamsTurnContext,
        state: StateT,
        config_data: Any,
    ) -> Awaitable[ConfigResponse]:
        """Handle a configuration invoke.

        :param context: Teams-aware turn context.
        :param state: The current turn state.
        :param config_data: Raw value payload from the invoke activity.
        :return: A :class:`ConfigResponse` to send back to Teams.
        """
        ...
