# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft.agents.hosting.core.storage import Storage

from ..turn_context import TurnContext
from .agent_state import AgentState


class UserState(AgentState):
    """
    Reads and writes user state for your bot to storage.
    """

    no_key_error_message = (
        "UserState: channel_id and/or conversation missing from context.activity."
    )

    def __init__(self, storage: Storage, namespace=""):
        """
        Creates a new UserState instance.
        :param storage:
        :param namespace:
        """
        self.namespace = namespace

        super().__init__(storage, namespace or "Internal.UserState")

    def get_storage_key(self, turn_context: TurnContext) -> str:
        """
        Returns the storage key for the current user state.
        :param turn_context:
        :return:
        """
        channel_id = turn_context.activity.channel_id or self.__raise_type_error(
            "Invalid Activity: missing channelId"
        )
        user_id = turn_context.activity.from_property.id or self.__raise_type_error(
            "Invalid Activity: missing from_property.id"
        )

        storage_key = None
        if channel_id and user_id:
            storage_key = f"{channel_id}/users/{user_id}"

        return storage_key

    def __raise_type_error(self, err: str = "NoneType found while expecting value"):
        raise TypeError(err)
