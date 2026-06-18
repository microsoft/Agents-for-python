# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Protocol definitions for Teams message and actionable message route handlers."""

from typing import Awaitable, Protocol

from microsoft_teams.api.models.o365 import O365ConnectorCardActionQuery

from microsoft_agents.hosting.teams.teams_turn_context import TeamsTurnContext
from microsoft_agents.hosting.teams.type_defs import StateT


class ExecuteActionHandler(Protocol[StateT]):
    """Protocol for a handler invoked on actionableMessage/executeAction activities."""

    def __call__(
        self,
        context: TeamsTurnContext,
        state: StateT,
        query: O365ConnectorCardActionQuery,
    ) -> Awaitable[None]:
        """Handle an O365 connector card action execution.

        :param context: Teams-aware turn context.
        :param state: The current turn state.
        :param query: The parsed O365 connector card action query.
        """
        ...


class ReadReceiptHandler(Protocol[StateT]):
    """Protocol for a handler invoked on Teams read receipt events."""

    def __call__(
        self,
        context: TeamsTurnContext,
        state: StateT,
        data: dict,
    ) -> Awaitable[None]:
        """Handle a read receipt event.

        :param context: Teams-aware turn context.
        :param state: The current turn state.
        :param data: Raw event payload from the activity value.
        """
        ...
