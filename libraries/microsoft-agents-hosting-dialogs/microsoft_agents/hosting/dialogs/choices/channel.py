# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.activity import Channels


class Channel:
    """
    Methods for determining channel-specific functionality.
    """

    @staticmethod
    def supports_suggested_actions(channel_id: str, button_cnt: int = 100) -> bool:
        """Determine if a number of Suggested Actions are supported by a Channel.

        Args:
            channel_id (str): The Channel to check the if Suggested Actions are supported in.
            button_cnt (int, optional): Defaults to 100. The number of Suggested Actions to check for the Channel.

        Returns:
            bool: True if the Channel supports the button_cnt total Suggested Actions, False if the Channel does not
             support that number of Suggested Actions.
        """
        return Channels.supports_suggested_actions(channel_id, button_cnt)

    @staticmethod
    def supports_card_actions(channel_id: str, button_cnt: int = 100) -> bool:
        """Determine if a number of Card Actions are supported by a Channel.

        Args:
            channel_id (str): The Channel to check if the Card Actions are supported in.
            button_cnt (int, optional): Defaults to 100. The number of Card Actions to check for the Channel.

        Returns:
            bool: True if the Channel supports the button_cnt total Card Actions, False if the Channel does not support
             that number of Card Actions.
        """
        return Channels.supports_card_actions(channel_id, button_cnt)

    @staticmethod
    def has_message_feed(channel_id: str) -> bool:
        """Determine if a Channel has a Message Feed.

        Args:
            channel_id (str): The Channel to check for Message Feed.

        Returns:
            bool: True if the Channel has a Message Feed, False if it does not.
        """
        return Channels.has_message_feed(channel_id)

    @staticmethod
    def get_channel_id(turn_context: TurnContext) -> str:
        """Get the channel ID from the TurnContext's activity.

        Args:
            turn_context (TurnContext): The current turn context.

        Returns:
            str: The channel ID, or an empty string if not set.
        """
        if turn_context.activity and turn_context.activity.channel_id:
            return turn_context.activity.channel_id
        return ""

    @staticmethod
    def max_action_title_length(
        channel_id: str,
    ) -> int:
        """Maximum length allowed for Action Titles.

        Args:
            channel_id (str): The Channel to determine Maximum Action Title Length.

        Returns:
            int: The total number of characters allowed for an Action Title on a specific Channel.
        """
        return Channels.max_action_title_length(channel_id)
