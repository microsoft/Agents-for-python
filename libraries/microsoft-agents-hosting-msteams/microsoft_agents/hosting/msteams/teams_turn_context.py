# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Teams-specific turn context wrapper."""

from __future__ import annotations

from typing import cast

from microsoft_teams.api import ApiClient
from microsoft_teams.api.models import Account

from microsoft_agents.activity import (
    Activity,
    ActivityTreatment,
    ActivityTreatmentTypes,
    ChannelAccount,
    Channels,
    ConversationAccount,
    ConversationParameters,
    ConversationReference,
    ResourceResponse,
)
from microsoft_agents.hosting.core import (
    AgentApplication,
    ClaimsIdentity,
    TurnContext,
    TurnState,
)
from microsoft_agents.hosting.core.app.proactive import (
    CreateConversationOptions,
    Conversation,
    Proactive
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
        self._turn_state.update(context.turn_state)

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

    async def create_conversation(self, account: Account, text: str) -> ResourceResponse:
        """
        Create a new conversation with a user.

        :param account: The account of the user to create the conversation with.
        :param text: The text to send in the initial message.
        :return: The resource response.
        """
        assert self.identity is not None
        aud = self.identity.get_app_id()
        assert aud is not None
        tenant_id = self.activity.conversation.tenant_id
        assert tenant_id

        options = CreateConversationOptions(
            identity=Conversation.identity_from_claims(
                dict(aud=aud)
            ),
            channel_id=Channels.ms_teams.value,
            service_url=self.activity.service_url,
            parameters=ConversationParameters(
                is_group=False,
                bot=ChannelAccount(
                    id=aud
                ),
                members=[
                    ChannelAccount(
                        id=account.id.strip(),
                        name=account.name
                    )
                ],
                tenant_id=tenant_id,
                channel_data={
                    "channel": {
                        "id": tenant_id,
                    }
                }
            )
        )

        async def __handler(context: TurnContext, state: TurnState):
            await context.send_activity(text)

        await self._app.proactive.create_conversation(
            self._app.adapter,
            options,
            __handler
        )

        return ResourceResponse()
    
    async def continue_conversation(self, conversation_id: str, activity: Activity) -> ResourceResponse:

        assert self.identity

        conv = Conversation(
            self.identity,
            ConversationReference(
                bot=activity.recipient,
                channel_id=Channels.ms_teams,
                service_url=activity.service_url,
                conversation=ConversationAccount(id=conversation_id)
            )
        )

        await Proactive._send_activity_impl(
            self._app.adapter,
            conversation=conv,
            activity=activity
        )

    async def reply(self, text: str) -> ResourceResponse:
        new_activity: TeamsActivity
        if self.activity.id:
            new_activity = (self.activity
                .create_reply()
                .add_quote(self.activity.id, self.activity.text)
                .add_text(text)
            )
        else:
            new_activity = self.activity.create_reply(text)

        return await self.send_activity(new_activity)
    
    async def add_reaction(self, reaction_type: str, activity_id: str | None = None) -> ResourceResponse:
        """
        Add a reaction to the current activity.

        :param reaction_type: The type of reaction to add.
        :param activity_id: The ID of the activity to add the reaction to. If None, uses the current activity's ID.
        :return: The resource response.
        """
        if not activity_id:
            if not self.activity.id:
                raise ValueError("Cannot add a reaction to an activity without an ID.")
            activity_id = self.activity.id

        return await self.api_client.conversations.reactions.add(
            conversation_id=self.activity.conversation.id,
            activity_id=activity_id,
            reaction_type=reaction_type)
    
    async def delete_reaction(self, reaction_type: str, activity_id: str | None = None) -> ResourceResponse:
        """
        Delete a reaction from the current activity.

        :param reaction_type: The type of reaction to delete.
        :param activity_id: The ID of the activity to delete the reaction from. If None, uses the current activity's ID.
        :return: The resource response.
        """
        if not activity_id:
            if not self.activity.id:
                raise ValueError("Cannot delete a reaction from an activity without an ID.")
            activity_id = self.activity.id

        return await self.api_client.conversations.reactions.delete(
            conversation_id=self.activity.conversation.id,
            activity_id=activity_id,
            reaction_type=reaction_type)