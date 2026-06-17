# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import (
    Any,
    Awaitable,
    Protocol,
)

from microsoft_teams.api.models import (
    Channel,
    Team,
    MeetingDetails,
    MeetingParticipantsEventDetails,
    MessageExtensionAction,
    MessageExtensionQuery,
    MessageExtensionActionResponse,
    MessageExtensionResponse,
    O365ConnectorCardActionQuery,
    TaskModuleRequest,
    TaskModuleResponse,
    AppBasedLinkQuery
)

from microsoft_agents.activity import Activity

from microsoft_agents.hosting.teams_turn_context import TeamsTurnContext
from microsoft_agents.hosting.teams.type_defs import StateT

class FetchActionHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            state: StateT,
            action: MessageExtensionAction
        ) -> Awaitable[MessageExtensionActionResponse]: ...

class SubmitActionHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            state: StateT,
            action: MessageExtensionAction
        ) -> Awaitable[MessageExtensionResponse]: ...

class MessagePreviewEditHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            state: StateT,
            activity_preview: Activity
        ) -> Awaitable[MessageExtensionResponse]:
        ...

class MessagePreviewSendHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            activity_preview: Activity
        ) -> Awaitable[None]:
        ...

class QueryHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            state: StateT,
            query: MessageExtensionQuery
        ) -> Awaitable[MessageExtensionResponse]:
        ...

class SelectItemHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            state: StateT,
            item: Any
        ) -> Awaitable[MessageExtensionResponse]:
        ...

class QueryLinkHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            state: StateT,
            query: AppBasedLinkQuery
        ) -> Awaitable[MessageExtensionResponse]:
        ...

class QueryUrlSettingHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            state: StateT,
        ) -> Awaitable[MessageExtensionResponse]:
        ...

class ConfigureSettingsHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            state: StateT,
            query: MessageExtensionQuery
        ) -> Awaitable[MessageExtensionResponse]:
        ...

class CardButtonClickedHandler(Protocol[StateT]):
    def __call__(
            self,
            context: TeamsTurnContext,
            state: StateT,
            card: Any
        ) -> Awaitable[None]:
        ...