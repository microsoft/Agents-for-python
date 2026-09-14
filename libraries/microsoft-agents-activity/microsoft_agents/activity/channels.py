# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from enum import Enum

from .channel_id import ChannelId


class Channels(str, Enum):
    """
    Ids of channels supported by ABS.
    """

    agents = "agents"
    """Agents channel."""

    alexa = "alexa"
    """Alexa channel."""

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

    msteams = "msteams"
    """MS Teams channel."""

    skype = "skype"
    """Skype channel."""

    skype_for_business = "skypeforbusiness"
    """Skype for Business channel."""

    slack = "slack"
    """Slack channel."""

    sms = "sms"
    """SMS (Twilio) channel."""

    twilio = "twilio-sms"
    """Twilio channel."""

    telegram = "telegram"
    """Telegram channel."""

    test = "test"
    """Test channel."""

    webchat = "webchat"
    """WebChat channel."""

    copilot_studio = "pva-studio"
    """Microsoft Copilot Studio channel."""

    ms_teams = "msteams"
    """Deprecated alias for :attr:`msteams`. Kept for backwards compatibility."""

    @staticmethod
    def _normalize_channel_id(channel_id: str | Channels | ChannelId) -> str:
        """Normalize a channel ID to obtain the parent channel.

        :param channel_id: The channel ID to normalize.
        :returns: The canonical string representation of the channel ID.
        """
        return ChannelId(channel_id).channel

    @staticmethod
    def supports_suggested_actions(
        channel_id: str, button_cnt: int = 100, conversation_type: str | None = None
    ) -> bool:
        """Determine if a number of Suggested Actions are supported by a Channel.

        :param channel_id: The ID of the channel to check for support of Suggested Actions.
        :param button_cnt: The number of Suggested Actions to check for the Channel.
        :param conversation_type: The type of conversation, if applicable.
        :returns: True if the Channel supports the button_cnt total Suggested Actions, False if the Channel does not support that number of Suggested Actions.
        """

        channel_id = Channels._normalize_channel_id(channel_id)

        if channel_id == Channels.msteams:
            return conversation_type == "personal" and button_cnt <= 3

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
    def supports_card_actions(channel_id: str, button_cnt: int = 100) -> bool:
        """Determine if a number of Card Actions are supported by a Channel.

        :param button_cnt: The number of Card Actions to check for the Channel.
        :returns: True if the Channel supports the button_cnt total Card Actions, False if the Channel does not support that number of Card Actions.
        """

        channel = Channels._normalize_channel_id(channel_id)

        max_actions = {
            Channels.facebook: 3,
            Channels.skype: 3,
            Channels.msteams: 50,
            Channels.line: 99,
            Channels.slack: 100,
            Channels.telegram: 100,
            Channels.emulator: 100,
            Channels.direct_line: 100,
            Channels.direct_line_speech: 100,
            Channels.webchat: 100,
            Channels.cortana: 100,
        }
        return button_cnt <= max_actions[channel] if channel in max_actions else False

    @staticmethod
    def supports_video_card(channel_id: str) -> bool:
        """Determine if a Channel supports Video Cards.

        :param channel_id: The Channel to check for Video Card support.
        :returns: True if the Channel supports Video Cards, False if it does not.
        """
        channel = Channels._normalize_channel_id(channel_id)
        return channel not in (
            Channels.alexa,
            Channels.msteams,
            Channels.twilio,
        )

    @staticmethod
    def supports_receipt_card(channel_id: str) -> bool:
        """Determine if a Channel supports Receipt Cards.

        :param channel_id: The Channel to check for Receipt Card support.
        :returns: True if the Channel supports Receipt Cards, False if it does not.
        """
        channel = Channels._normalize_channel_id(channel_id)
        return channel not in (
            Channels.alexa,
            Channels.groupme,
            Channels.msteams,
            Channels.twilio,
        )

    @staticmethod
    def supports_thumbnail_card(channel_id: str) -> bool:
        """Determine if a Channel supports Thumbnail Cards.

        :param channel_id: The Channel to check for Thumbnail Card support.
        :returns: True if the Channel supports Thumbnail Cards, False if it does not.
        """
        channel = Channels._normalize_channel_id(channel_id)
        return channel not in (
            Channels.alexa,
            Channels.groupme,
            Channels.line,
            Channels.slack,
            Channels.twilio,
        )

    @staticmethod
    def supports_audio_card(channel_id: str) -> bool:
        """Determine if a Channel supports Audio Cards.

        :param channel_id: The Channel to check for Audio Card support.
        :returns: True if the Channel supports Audio Cards, False if it does not.
        """
        channel = Channels._normalize_channel_id(channel_id)
        return channel not in (
            Channels.alexa,
            Channels.msteams,
            Channels.twilio,
            Channels.email,
            Channels.groupme,
            Channels.line,
            Channels.slack,
            Channels.telegram,
        )

    @staticmethod
    def supports_animation_card(channel_id: str) -> bool:
        """Determine if a Channel supports Animation Cards.

        :param channel_id: The Channel to check for Animation Card support.
        :returns: True if the Channel supports Animation Cards, False if it does not.
        """
        channel = Channels._normalize_channel_id(channel_id)
        return channel not in (
            Channels.alexa,
            Channels.msteams,
            Channels.email,
            Channels.groupme,
            Channels.twilio,
        )

    @staticmethod
    def has_message_feed(channel_id: str) -> bool:
        """Determine if a Channel has a Message Feed.
        :param channel_id: The Channel to check for Message Feed support.
        :returns: True if the Channel has a Message Feed, False if it does not.
        """
        channel = Channels._normalize_channel_id(channel_id)
        return channel != Channels.cortana

    @staticmethod
    def max_action_title_length(channel_id: str) -> int:
        """Maximum length allowed for Action Titles.
        :param channel_id: The Channel to check for maximum Action Title length.
        :returns: The maximum number of characters allowed for an Action Title.
        """
        return 20

    @staticmethod
    def supports_create_conversation(channel_id: str) -> bool:
        """Determine if a Channel supports creating a conversation.

        :param channel_id: The Channel to check for create conversation support.
        :returns: True if the Channel supports creating a conversation, False if it does not.
        """
        channel = Channels._normalize_channel_id(channel_id)
        return channel in (
            Channels.email,
            Channels.facebook,
            Channels.groupme,
            Channels.kik,
            Channels.line,
            Channels.msteams,
            Channels.slack,
            Channels.sms,
            Channels.telegram,
        )

    @staticmethod
    def supports_update_activity(channel_id: str) -> bool:
        """Determine if a Channel supports updating activities.

        :param channel_id: The Channel to check for update activity support.
        :returns: True if the Channel supports updating activities, False if it does not.
        """
        channel = Channels._normalize_channel_id(channel_id)
        return channel == Channels.msteams

    @staticmethod
    def supports_delete_activity(channel_id: str) -> bool:
        """Determine if a Channel supports deleting activities.

        :param channel_id: The Channel to check for delete activity support.
        :returns: True if the Channel supports deleting activities, False if it does not.
        """
        channel = Channels._normalize_channel_id(channel_id)
        return channel in (
            Channels.msteams,
            Channels.slack,
            Channels.telegram,
        )
