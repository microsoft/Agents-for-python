# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel

from ..card_action import CardAction


class MessagingExtensionSuggestedAction(AgentsModel):
    """Messaging extension suggested actions.

    :param actions: List of suggested actions.
    :type actions: list["CardAction"]
    """

    actions: list[CardAction] = None
