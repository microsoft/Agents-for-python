# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import abstractmethod
from typing import Protocol

from .turn_context import TurnContext


class Agent(Protocol):
    """
    Represents an agent that can operate on incoming activities.
    """

    @abstractmethod
    async def on_turn(self, context: TurnContext):
        """
        When implemented in an agent, handles an incoming activity.
        :param context: The context object for this turn.
        :return:
        """
        raise NotImplementedError()
