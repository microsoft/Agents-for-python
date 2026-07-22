# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import Field

from .card_action import CardAction
from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class SuggestedActions(AgentsModel):
    """SuggestedActions that can be performed.

    :param to: Ids of the recipients that the actions should be shown to.
     These Ids are relative to the channelId and a subset of all recipients of
     the activity
    :type to: list[str]
    :param actions: Actions that can be shown to the user
    :type actions: list[~microsoft_agents.activity.CardAction]
    """

    to: list[NonEmptyString] = Field(default_factory=list)
    actions: list[CardAction]

    def add_action(self, action: CardAction) -> "SuggestedActions":
        """
        Adds a single action to the actions and returns this instance.

        :param action: The action to add.
        :returns: This instance, to allow for method chaining.
        """
        self.actions = self.actions or []
        self.actions.append(action)
        return self

    def add_actions(self, *actions: CardAction) -> "SuggestedActions":
        """
        Adds one or more actions to the actions and returns this instance.

        :param actions: The actions to add.
        :returns: This instance, to allow for method chaining.
        """
        if not actions:
            return self

        self.actions = self.actions or []
        self.actions.extend(actions)
        return self

    def add_recipients(self, *recipients: NonEmptyString) -> "SuggestedActions":
        """
        Adds one or more recipient ids to the recipients and returns this instance.

        :param recipients: The recipient ids to add.
        :returns: This instance, to allow for method chaining.
        """
        if not recipients:
            return self

        self.to = self.to or []
        self.to.extend(recipients)
        return self
