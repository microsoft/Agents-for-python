# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Teams-specific turn context wrapper."""

from __future__ import annotations

from typing import cast

from msgraph import GraphServiceClient

from microsoft_teams.api import ApiClient

from microsoft_agents.activity import (
    Activity,
    ActivityTreatment,
    ActivityTreatmentTypes,
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

    @staticmethod
    def _make_targeted_activity(activity: Activity) -> None:
        """
        Make an activity targeted.

        :param activity: The activity to make targeted.
        :return: None
        """
        activity.entities = activity.entities or []
        activity.entities.append(
            ActivityTreatment(treatment=ActivityTreatmentTypes.TARGETED)
        )

    async def send_targeted_activity(self, activity: Activity) -> ResourceResponse:
        """
        Send a targeted activity.

        :param activity: The activity to send.
        :return: The resource response.
        """
        TeamsTurnContext._make_targeted_activity(activity)
        return await self.send_activity(activity)

    async def send_targeted_activities(
        self, activities: list[Activity]
    ) -> list[ResourceResponse]:
        """
        Send a list of targeted activities.

        :param activities: The list of activities to send.
        :return: A list of resource responses.
        """
        for activity in activities:
            TeamsTurnContext._make_targeted_activity(activity)
        return await self.send_activities(activities)

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
            the agent's authorization.
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
            the agent's authorization.
        """
        return _common_get_app_graph_client_for_connection(
            self._app, connection_name, graph_base_url=graph_base_url
        )
