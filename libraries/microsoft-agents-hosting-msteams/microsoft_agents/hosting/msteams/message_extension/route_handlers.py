# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Protocol definitions for Teams Message Extension route handlers."""

from typing import (
    Any,
    Awaitable,
    Protocol,
)

from microsoft_teams.api.models import (
    MessagingExtensionAction,
    MessagingExtensionQuery,
    MessagingExtensionActionResponse,
    MessagingExtensionResponse,
    AppBasedLinkQuery,
)

from microsoft_agents.activity import Activity

from microsoft_agents.hosting.msteams.teams_turn_context import TeamsTurnContext
from microsoft_agents.hosting.msteams.type_defs import _StateContra


class FetchActionHandler(Protocol[_StateContra]):
    """Protocol for a handler invoked on composeExtension/fetchTask activities."""

    def __call__(
        self,
        context: TeamsTurnContext,
        state: _StateContra,
        action: MessagingExtensionAction,
        /,
    ) -> Awaitable[MessagingExtensionActionResponse]:
        """Handle a fetch task invoke.

        :param context: Teams-aware turn context.
        :param state: The current turn state.
        :param action: The parsed messaging extension action from the invoke payload.
        :return: A response containing the task module to display.
        """
        ...


class SubmitActionHandler(Protocol[_StateContra]):
    """Protocol for a handler invoked on composeExtension/submitAction activities."""

    def __call__(
        self,
        context: TeamsTurnContext,
        state: _StateContra,
        action: MessagingExtensionAction,
        /,
    ) -> Awaitable[MessagingExtensionResponse]:
        """Handle a submit action invoke.

        :param context: Teams-aware turn context.
        :param state: The current turn state.
        :param action: The parsed messaging extension action from the invoke payload.
        :return: A messaging extension response.
        """
        ...


class MessagePreviewEditHandler(Protocol[_StateContra]):
    """Protocol for a handler invoked on composeExtension/submitAction with botMessagePreviewAction == 'edit'."""

    def __call__(
        self,
        context: TeamsTurnContext,
        state: _StateContra,
        activity_preview: Activity,
        /,
    ) -> Awaitable[MessagingExtensionResponse]:
        """Handle a message preview edit request.

        :param context: Teams-aware turn context.
        :param state: The current turn state.
        :param activity_preview: The parsed botActivityPreview[0] activity from the invoke payload.
        :return: A messaging extension response.
        """
        ...


class MessagePreviewSendHandler(Protocol[_StateContra]):
    """Protocol for a handler invoked on composeExtension/submitAction with botMessagePreviewAction == 'send'."""

    def __call__(
        self,
        context: TeamsTurnContext,
        state: _StateContra,
        activity_preview: Activity,
        /,
    ) -> Awaitable[MessagingExtensionResponse | None]:
        """Handle a message preview send request.

        :param context: Teams-aware turn context.
        :param state: The current turn state.
        :param activity_preview: The parsed botActivityPreview[0] activity from the invoke payload.
        :return: A messaging extension response, or None when no response body is required.
        """
        ...


class QueryHandler(Protocol[_StateContra]):
    """Protocol for a handler invoked on composeExtension/query activities."""

    def __call__(
        self,
        context: TeamsTurnContext,
        state: _StateContra,
        query: MessagingExtensionQuery,
        /,
    ) -> Awaitable[MessagingExtensionResponse]:
        """Handle a message extension query invoke.

        :param context: Teams-aware turn context.
        :param state: The current turn state.
        :param query: The parsed messaging extension query.
        :return: A messaging extension response containing search results.
        """
        ...


class SelectItemHandler(Protocol[_StateContra]):
    """Protocol for a handler invoked on composeExtension/selectItem activities."""

    def __call__(
        self,
        context: TeamsTurnContext,
        state: _StateContra,
        item: Any,
        /,
    ) -> Awaitable[MessagingExtensionResponse]:
        """Handle a select item invoke.

        :param context: Teams-aware turn context.
        :param state: The current turn state.
        :param item: The raw item selected by the user.
        :return: A messaging extension response.
        """
        ...


class QueryLinkHandler(Protocol[_StateContra]):
    """Protocol for a handler invoked on composeExtension/queryLink or anonymousQueryLink activities."""

    def __call__(
        self,
        context: TeamsTurnContext,
        state: _StateContra,
        query: AppBasedLinkQuery,
        /,
    ) -> Awaitable[MessagingExtensionResponse]:
        """Handle a link unfurling query.

        :param context: Teams-aware turn context.
        :param state: The current turn state.
        :param query: The app-based link query containing the URL to unfurl.
        :return: A messaging extension response with the unfurled card.
        """
        ...


class QueryUrlSettingHandler(Protocol[_StateContra]):
    """Protocol for a handler invoked on composeExtension/querySettingUrl activities."""

    def __call__(
        self,
        context: TeamsTurnContext,
        state: _StateContra,
        query: MessagingExtensionQuery,
        /,
    ) -> Awaitable[MessagingExtensionResponse]:
        """Handle a query setting URL invoke.

        :param context: Teams-aware turn context.
        :param state: The current turn state.
        :param query: The messaging extension query for the settings URL.
        :return: A messaging extension response containing the settings page URL.
        """
        ...


class ConfigureSettingsHandler(Protocol[_StateContra]):
    """Protocol for a handler invoked on composeExtension/setting activities."""

    def __call__(
        self,
        context: TeamsTurnContext,
        state: _StateContra,
        query: MessagingExtensionQuery,
        /,
    ) -> Awaitable[MessagingExtensionResponse]:
        """Handle a configure settings invoke.

        :param context: Teams-aware turn context.
        :param state: The current turn state.
        :param query: The messaging extension query with the settings data.
        :return: A messaging extension response.
        """
        ...


class CardButtonClickedHandler(Protocol[_StateContra]):
    """Protocol for a handler invoked on composeExtension/onCardButtonClicked activities."""

    def __call__(
        self,
        context: TeamsTurnContext,
        state: _StateContra,
        card: Any,
        /,
    ) -> Awaitable[None]:
        """Handle a card button clicked invoke.

        :param context: Teams-aware turn context.
        :param state: The current turn state.
        :param card: The raw card data from the invoke payload.
        """
        ...
