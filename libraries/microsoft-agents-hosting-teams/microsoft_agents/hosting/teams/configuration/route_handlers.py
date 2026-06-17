# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any, Awaitable, Protocol

from microsoft_teams.api.models.config import ConfigResponse

from microsoft_agents.hosting.teams.teams_turn_context import TeamsTurnContext
from microsoft_agents.hosting.teams.type_defs import StateT

class ConfigurationHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            state: StateT,
            config_data: Any,
        ) -> Awaitable[ConfigResponse]: ...