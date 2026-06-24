# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Teams-specific turn context wrapper."""

from __future__ import annotations

from microsoft_teams.api import ApiClient

from microsoft_agents.activity import (
    Activity,
    ActivityTreatment,
    ActivityTreatmentTypes,
    ResourceResponse,
)
from microsoft_agents.hosting.core import AgentApplication, TurnContext

from ._teams_api_client import _get_teams_api_client, _set_teams_api_client


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
        self._turn_state.update(context.turn_state)
        _set_teams_api_client(context, app.connection_manager)

    @property
    def api_client(self) -> ApiClient:
        """Get the API client for the Teams turn context."""
        return _get_teams_api_client(self)

    @staticmethod
    def _make_targeted_activity(activity: Activity) -> Activity:
        """
        Make an activity targeted.

        :param activity: The activity to make targeted.
        :return: The targeted activity.
        """
        activity = activity.model_copy()
        activity.entities = activity.entities or []
        activity.entities.append(
            ActivityTreatment(treatment=ActivityTreatmentTypes.TARGETED)
        )
        return activity

    async def send_targeted_activity(self, activity: Activity) -> ResourceResponse:
        """
        Send a targeted activity.

        :param activity: The activity to send.
        :return: The resource response.
        """
        return await self.send_activity(
            TeamsTurnContext._make_targeted_activity(activity)
        )

    async def send_targeted_activities(
        self, activities: list[Activity]
    ) -> list[ResourceResponse]:
        """
        Send a list of targeted activities.

        :param activities: The list of activities to send.
        :return: A list of resource responses.
        """
        return await self.send_activities(
            [TeamsTurnContext._make_targeted_activity(act) for act in activities]
        )
