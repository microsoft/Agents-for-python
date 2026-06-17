# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Awaitable, Protocol

from microsoft_teams.api.models import FileConsentCardResponse

from microsoft_agents.hosting.teams.teams_turn_context import TeamsTurnContext
from microsoft_agents.hosting.teams.type_defs import StateT

class FileConsentHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            state: StateT,
            file_consent: FileConsentCardResponse
        ) -> Awaitable[None]: ...