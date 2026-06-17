# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import (
    Any,
    Awaitable,
    Protocol,
)

from microsoft_agents.activity import Activity

from microsoft_teams.api.models import (
    Channel,
    Team,
    MeetingDetails,
    MeetingParticipantsEventDetails,
    MessagingExtensionAction,
    MessagingExtensionQuery,
    MessageExtensionActionResponse,
    MessagingExtensionResponse,
    O365ConnectorCardActionQuery,
    TaskModuleRequest,
    TaskModuleResponse
)

from .teams_turn_context import TeamsTurnContext
from .type_defs import StateT

class TeamsRouteHandler(Protocol[StateT]):
    def __call__(self, context: TeamsTurnContext, state: StateT) -> Awaitable[None]: ...

# Meetings route handlers

class MeetingStartHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            state: StateT,
            meeting: MeetingDetails
        ) -> Awaitable[None]: ...

class MeetingEndHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            state: StateT,
            meeting: MeetingDetails
        ) -> Awaitable[None]: ...

class MeetingParticipantsEventHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            state: StateT,
            meeting: MeetingParticipantsEventDetails
        ) -> Awaitable[None]: ...

# Message extension route handlers

# Messages route handler

class O365ConnectorCardActionHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            state: StateT,
            query: O365ConnectorCardActionQuery
        ) -> Awaitable[None]:
        ...

class ReadReceiptHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            state: StateT,
            data: dict
        ) -> Awaitable[None]:
        ...

# Task Modules route handlers

class TaskFetchHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            state: StateT,
            request: TaskModuleRequest,
        ) -> Awaitable[TaskModuleResponse]:
        ...

class TaskSubmitHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            state: StateT,
            request: TaskModuleRequest,
        ) -> Awaitable[TaskModuleResponse]:
        ...

# Teams Channels route handlers

class ChannelUpdateHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            state: StateT,
            data: Channel
        ) -> Awaitable[None]:
        ...

class TeamUpdateHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            state: StateT,
            data: Team
        ) -> Awaitable[None]:
        ...