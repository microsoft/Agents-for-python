# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Teams-specific turn context wrapper."""

from microsoft_agents.activity import (
    Activity,
    ActivityTreatment,
    ActivityTreatmentTypes,
    ResourceResponse,
)
from microsoft_agents.hosting.core import AgentApplication, TurnContext


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
        self._context = context
        self._app = app

        self._turn_state.update(context.turn_state)

    @staticmethod
    def _make_targeted_activity(activity: Activity) -> Activity:
        activity = activity.model_copy()
        activity.entities = activity.entities or []
        activity.entities.append(
            ActivityTreatment(treatment=ActivityTreatmentTypes.TARGETED)
        )
        return activity

    async def send_targeted_activity(self, activity: Activity) -> ResourceResponse:
        return await self.send_activity(
            TeamsTurnContext._make_targeted_activity(activity)
        )

    async def send_targeted_activities(
        self, activities: list[Activity]
    ) -> list[ResourceResponse]:
        return await self.send_activities(
            [TeamsTurnContext._make_targeted_activity(act) for act in activities]
        )
