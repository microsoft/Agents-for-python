# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import List, Tuple

import pytest

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    Channels,
    ConversationAccount,
    ChannelAccount,
)
from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.hosting.dialogs.choices import Channel
from tests._common.testing_objects import MockTestingAdapter


class TestChannel:
    def test_supports_suggested_actions(self):
        actual = Channel.supports_suggested_actions(Channels.facebook, 5)
        assert actual

    def test_supports_suggested_actions_many(self):
        supports_suggested_actions_data: List[Tuple[str, int, bool]] = [
            (Channels.line, 13, True),
            (Channels.line, 14, False),
            (Channels.skype, 10, True),
            (Channels.skype, 11, False),
            (Channels.kik, 20, True),
            (Channels.kik, 21, False),
            (Channels.emulator, 100, True),
            (Channels.emulator, 101, False),
            (Channels.direct_line_speech, 100, True),
        ]

        for channel, button_cnt, expected in supports_suggested_actions_data:
            actual = Channel.supports_suggested_actions(channel, button_cnt)
            assert (
                expected == actual
            ), f"channel={channel}, button_cnt={button_cnt}: expected {expected}, got {actual}"

    def test_supports_card_actions_many(self):
        supports_card_action_data: List[Tuple[str, int, bool]] = [
            (Channels.line, 99, True),
            (Channels.line, 100, False),
            (Channels.slack, 100, True),
            (Channels.skype, 3, True),
            (Channels.skype, 5, False),
            (Channels.direct_line_speech, 99, True),
        ]

        for channel, button_cnt, expected in supports_card_action_data:
            actual = Channel.supports_card_actions(channel, button_cnt)
            assert (
                expected == actual
            ), f"channel={channel}, button_cnt={button_cnt}: expected {expected}, got {actual}"

    def test_should_return_channel_id_from_context_activity(self):
        adapter = MockTestingAdapter(channel_id=Channels.facebook)
        test_activity = Activity(
            type=ActivityTypes.message,
            channel_id=Channels.facebook,
            conversation=ConversationAccount(id="test"),
            from_property=ChannelAccount(id="user"),
        )
        test_context = TurnContext(adapter, test_activity)
        channel_id = Channel.get_channel_id(test_context)
        assert Channels.facebook == channel_id

    def test_should_return_empty_from_context_activity_missing_channel(self):
        adapter = MockTestingAdapter()
        test_activity = Activity(
            type=ActivityTypes.message,
            conversation=ConversationAccount(id="test"),
            from_property=ChannelAccount(id="user"),
        )
        test_context = TurnContext(adapter, test_activity)
        channel_id = Channel.get_channel_id(test_context)
        assert "" == channel_id
