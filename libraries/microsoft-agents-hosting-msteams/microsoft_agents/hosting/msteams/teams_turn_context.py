# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Teams-specific turn context wrapper."""

from __future__ import annotations

import warnings
from typing import cast

from msgraph import GraphServiceClient

from microsoft_teams.api import ApiClient

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    ChannelAccount,
    InputHints,
    ResourceResponse,
)
from microsoft_agents.hosting.core import (
    AgentApplication,
    TurnContext,
)

from ._graph import (
    _DEFAULT_GRAPH_BASE_URL,
    _create_user_graph_service_client,
    _common_get_app_graph_client,
    _common_get_app_graph_client_for_connection,
)
from ._teams_api_client import _get_teams_api_client, _set_teams_api_client
from .teams_activity import TeamsActivity
from ._utils import _apply_prompt_preview_normalizer, _is_recipient_targeted


class TeamsTurnContext(TurnContext):
    """A context object for handling Teams-specific turn functionality.

    Wraps a plain :class:`TurnContext` so that Teams-aware route handlers
    receive a typed context without changing the core routing engine.
    """

    def __init__(self, context: TurnContext, app: AgentApplication) -> None:
        """Initialise the Teams turn context from a plain turn context.

        :param context: The base turn context provided by the core runtime.
        :param app: The agent application that is handling the turn.
        """
        super().__init__(context)
        self._app = app
        self._turn_state = context.turn_state

        self._original = context

        self._set_teams_activity()

        _set_teams_api_client(self, app.connection_manager)

    def _set_teams_activity(self) -> None:
        """
        Replace the default Activity class with TeamsActivity

        This allows the activity to be treated as a TeamsActivity, which provides
        additional methods for working with Teams-specific data.

        This is a bit of a hack, but it's the only way to get the TeamsActivity class to be used.
        There are possible workarounds, but because:
          1. we do not expect new properties to be added to the TeamsActivity class
          2. we define the TeamsActivity class, and we manage its lifecycle here
        this is the most straightforward approach for now.
        The main pitfall beyond the obvious ones is if a user defines a custom Activity
        and brings in their own Adapter that creates it. This is a tradeoff.
        """
        self._activity.__class__ = TeamsActivity
        self._teams_activity = cast(TeamsActivity, self._activity)

    @property
    def responded(self) -> bool:
        return self._original.responded

    @responded.setter
    def responded(self, value: bool):
        self._original.responded = value

    @property
    def streaming_response(self):
        return self._original.streaming_response

    @property
    def activity(self) -> TeamsActivity:
        """The current activity, typed as a :class:`TeamsActivity`.

        :return: The turn's activity exposing Teams-specific accessors.
        """
        return self._teams_activity

    @property
    def api_client(self) -> ApiClient:
        """Get the API client for the Teams turn context."""
        return _get_teams_api_client(self)

    def _apply_prompt_preview(self, activity: Activity) -> None:
        """
        Apply the prompt preview to the given activity.

        :param activity: The activity to apply the prompt preview to.
        :return: None
        """
        if (
            activity.type == ActivityTypes.message
            and _is_recipient_targeted(self.activity)
            and self.activity.id
        ):
            _apply_prompt_preview_normalizer(activity, self.activity.id)

    async def send_activity(
        self,
        activity_or_text: Activity | str,
        speak: str | None = None,
        input_hint: str | None = None,
    ) -> ResourceResponse:
        """Send an activity after applying the prompt preview.

        :param activity_or_text: The activity or text to send.
        :param speak: Optional speech text for the activity.
        :param input_hint: Optional input hint for the activity.
        :return: The resource response for the sent activity.
        """

        if isinstance(activity_or_text, str):
            activity_or_text = Activity(
                type=ActivityTypes.message,
                text=activity_or_text,
                input_hint=input_hint or InputHints.accepting_input,
            )
            if speak:
                activity_or_text.speak = speak

        self._apply_prompt_preview(
            activity_or_text
            if isinstance(activity_or_text, Activity)
            else Activity(type=ActivityTypes.message, text=activity_or_text)
        )

        return await TurnContext.send_activity(self._original, activity_or_text)

    async def send_activities(
        self, activities: list[Activity]
    ) -> list[ResourceResponse]:
        """Send multiple activities after applying the prompt preview to each.

        :param activities: A list of activities to send.
        :return: A list of resource responses for the sent activities.
        """

        for activity in activities:
            self._apply_prompt_preview(activity)

        return await TurnContext.send_activities(
            self._original,
            activities,
        )

    async def send_targeted_activity(
        self,
        activity: str | Activity,
        recipient: str | ChannelAccount | None = None,
    ) -> ResourceResponse:
        """
        Send a targeted activity.

        :param activity: The activity to send.
        :param recipient: The recipient to target the activity to. Can be a string or a ChannelAccount instance.
        :return: The resource response.
        """
        if recipient is None:
            warnings.warn(
                "Using an empty recipient is deprecated and will be removed in a future release.",
                DeprecationWarning,
                stacklevel=2,
            )
            if isinstance(activity, str) or not activity.recipient:
                raise ValueError(
                    "Cannot infer the recipient from the passed-in activity."
                )
            recipient = activity.recipient

        if isinstance(activity, str):
            activity = Activity(type=ActivityTypes.message, text=activity)
        activity.with_targeted_recipient(recipient)
        return await self.send_activity(activity)

    def get_graph_client(
        self,
        handler_name: str | None = None,
        graph_base_url: str = _DEFAULT_GRAPH_BASE_URL,
    ) -> GraphServiceClient:
        """
        Get a Graph client for the current turn context.

        :param handler_name: Optional name of the handler to use for authentication.
        :param graph_base_url: The base URL for the Microsoft Graph API.

        :return: A :class:`GraphServiceClient` that authenticates each request via
            the agent's authorization.
        """
        return _create_user_graph_service_client(
            self._app, self, handler_name, graph_base_url=graph_base_url
        )

    def get_app_graph_client(
        self,
        graph_base_url: str = _DEFAULT_GRAPH_BASE_URL,
    ) -> GraphServiceClient:
        """
        Get a Graph client for the current turn context.

        :param graph_base_url: The base URL for the Microsoft Graph API.

        :return: A :class:`GraphServiceClient` that authenticates each request via
            the agent's connections.
        """
        return _common_get_app_graph_client(
            self._app, self, graph_base_url=graph_base_url
        )

    def get_app_graph_client_for_connection(
        self,
        connection_name: str,
        graph_base_url: str = _DEFAULT_GRAPH_BASE_URL,
    ) -> GraphServiceClient:
        """
        Get a Graph client for the current turn context using a specific connection.

        :param connection_name: The name of the connection to use for authentication.
        :param graph_base_url: The base URL for the Microsoft Graph API.

        :return: A :class:`GraphServiceClient` that authenticates each request via
            the agent's connections.
        """
        return _common_get_app_graph_client_for_connection(
            self._app, connection_name, graph_base_url=graph_base_url
        )
