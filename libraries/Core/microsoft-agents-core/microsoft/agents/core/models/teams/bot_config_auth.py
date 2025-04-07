# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import BaseModel
from ..suggested_actions import SuggestedActions


class BotConfigAuth(BaseModel):
    """Specifies bot config auth, including type and suggestedActions.

    :param type: The type of bot config auth.
    :type type: str
    :param suggested_actions: The suggested actions of bot config auth.
    :type suggested_actions: SuggestedActions
    """

    type: str = "auth"
    suggested_actions: SuggestedActions = None
