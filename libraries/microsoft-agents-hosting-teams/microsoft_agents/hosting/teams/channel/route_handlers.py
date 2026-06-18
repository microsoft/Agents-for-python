# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any, Awaitable, Protocol

from microsoft_teams.api.models.channel_data import ChannelData

from microsoft_agents.hosting.teams.teams_turn_context import TeamsTurnContext
from microsoft_agents.hosting.teams.type_defs import StateT

class ChannelUpdateHandler(Protocol[StateT]):
    """A protocol for handling Teams channel update requests."""
    def __call__(
            self,
            context: TeamsTurnContext,
            state: StateT,
            data: ChannelData,
        ) -> Awaitable[None]: ...