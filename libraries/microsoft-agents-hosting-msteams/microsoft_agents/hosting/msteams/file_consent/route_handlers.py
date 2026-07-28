# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Protocol definition for Teams file consent route handlers."""

from typing import Awaitable, Protocol

from microsoft_teams.api.models import FileConsentCardResponse

from microsoft_agents.hosting.msteams.teams_turn_context import TeamsTurnContext
from microsoft_agents.hosting.msteams.type_defs import _StateContra


class FileConsentHandler(Protocol[_StateContra]):
    """Protocol for a handler invoked on fileConsent/invoke activities.

    Called for both ``accept`` and ``decline`` actions; the routing layer sends
    the invoke response automatically after the handler returns.
    """

    def __call__(
        self,
        context: TeamsTurnContext,
        state: _StateContra,
        file_consent: FileConsentCardResponse,
        /,
    ) -> Awaitable[None]:
        """Handle a file consent invoke.

        :param context: Teams-aware turn context.
        :param state: The current turn state.
        :param file_consent: Parsed file consent card response from the invoke payload.
        :return: An awaitable that completes when the handler finishes.
        """
        ...
