# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Awaitable, Protocol

from microsoft_teams.api.models.o365 import (
    O365ConnectorCardActionQuery
)

from microsoft_agents.hosting.teams.teams_turn_context import TeamsTurnContext
from microsoft_agents.hosting.teams.type_defs import StateT

class O365ConnectorCardActionHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            state: StateT,
            query: O365ConnectorCardActionQuery) -> Awaitable[None]: ...
    
class ReadReceiptHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            data: dict) -> Awaitable[None]: ...