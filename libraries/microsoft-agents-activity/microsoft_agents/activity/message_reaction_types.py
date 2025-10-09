# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import Enum


class MessageReactionTypes(str, Enum):
    """MessageReactionType

    Enum for message reaction types.
    """

    REACTIONS_ADDED = "reactionsAdded"
    REACTIONS_REMOVED = "reactionsRemoved"
