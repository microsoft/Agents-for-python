# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import BaseModel
from typing import List

from ..card_action import CardAction


class MessagingExtensionSuggestedAction(BaseModel):
    """Messaging extension suggested actions.

    :param actions: List of suggested actions.
    :type actions: List["CardAction"]
    """

    actions: List[CardAction] = None
