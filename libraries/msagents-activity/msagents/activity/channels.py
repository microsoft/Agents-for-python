# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import Enum
from typing_extensions import Self


class Channels(str, Enum):
    """
    Ids of channels supported by ABS.
    """

    console = "console"
    """Console channel."""

    cortana = "cortana"
    """Cortana channel."""

    direct_line = "directline"
    """Direct Line channel."""

    direct_line_speech = "directlinespeech"
    """Direct Line Speech channel."""

    email = "email"
    """Email channel."""

    emulator = "emulator"
    """Emulator channel."""

    facebook = "facebook"
    """Facebook channel."""

    groupme = "groupme"
    """Group Me channel."""

    kik = "kik"
    """Kik channel."""

    line = "line"
    """Line channel."""

    ms_teams = "msteams"
    """MS Teams channel."""

    skype = "skype"
    """Skype channel."""

    skype_for_business = "skypeforbusiness"
    """Skype for Business channel."""

    slack = "slack"
    """Slack channel."""

    sms = "sms"
    """SMS (Twilio) channel."""

    telegram = "telegram"
    """Telegram channel."""

    test = "test"
    """Test channel."""

    webchat = "webchat"
    """WebChat channel."""

    # TODO: validate the need of Self annotations in the following methods
    @staticmethod
    def supports_suggested_actions(channel_id: Self, button_cnt: int = 100) -> bool:
        """Determine if a number of Suggested Actions are supported by a Channel.

        Args:
            channel_id (str): The Channel to check the if Suggested Actions are supported in.
            button_cnt (int, optional): Defaults to 100. The number of Suggested Actions to check for the Channel.

        Returns:
            bool: True if the Channel supports the button_cnt total Suggested Actions, False if the Channel does not
             support that number of Suggested Actions.
        """

        max_actions = {
            # https://developers.facebook.com/docs/messenger-platform/send-messages/quick-replies
            Channels.facebook: 10,
            Channels.skype: 10,
            # https://developers.line.biz/en/reference/messaging-api/#items-object
            Channels.line: 13,
            # https://dev.kik.com/#/docs/messaging#text-response-object
            Channels.kik: 20,
            Channels.telegram: 100,
            Channels.emulator: 100,
            Channels.direct_line: 100,
            Channels.direct_line_speech: 100,
            Channels.webchat: 100,
        }
        return (
            button_cnt <= max_actions[channel_id]
            if channel_id in max_actions
            else False
        )

    @staticmethod
    def supports_card_actions(channel_id: Self, button_cnt: int = 100) -> bool:
        """Determine if a number of Card Actions are supported by a Channel.

        Args:
            channel_id (str): The Channel to check if the Card Actions are supported in.
            button_cnt (int, optional): Defaults to 100. The number of Card Actions to check for the Channel.

        Returns:
            bool: True if the Channel supports the button_cnt total Card Actions, False if the Channel does not support
             that number of Card Actions.
        """

        max_actions = {
            Channels.facebook: 3,
            Channels.skype: 3,
            Channels.ms_teams: 3,
            Channels.line: 99,
            Channels.slack: 100,
            Channels.telegram: 100,
            Channels.emulator: 100,
            Channels.direct_line: 100,
            Channels.direct_line_speech: 100,
            Channels.webchat: 100,
        }
        return (
            button_cnt <= max_actions[channel_id]
            if channel_id in max_actions
            else False
        )

    @staticmethod
    def has_message_feed(_: str) -> bool:
        """Determine if a Channel has a Message Feed.

        Args:
            channel_id (str): The Channel to check for Message Feed.

        Returns:
            bool: True if the Channel has a Message Feed, False if it does not.
        """

        return True

    @staticmethod
    def max_action_title_length(  # pylint: disable=unused-argument
        channel_id: Self,
    ) -> int:
        """Maximum length allowed for Action Titles.

        Args:
            channel_id (str): The Channel to determine Maximum Action Title Length.

        Returns:
            int: The total number of characters allowed for an Action Title on a specific Channel.
        """

        return 20
