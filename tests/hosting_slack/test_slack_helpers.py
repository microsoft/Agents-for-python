"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import pytest

from microsoft_agents.hosting.slack import (
    create_conversation_id,
    slack_bot_id_from_conversation_id,
    slack_channel_id_from_conversation_id,
    slack_decode,
    slack_encode,
    slack_team_id_from_conversation_id,
    slack_thread_ts_from_conversation_id,
)


class TestEncodeDecode:
    def test_encode_handles_special_chars(self):
        assert slack_encode("a & b <c> d") == "a &amp; b &lt;c&gt; d"

    def test_decode_round_trip(self):
        original = "a & b <c> d"
        assert slack_decode(slack_encode(original)) == original

    def test_encode_none(self):
        assert slack_encode(None) is None
        assert slack_decode(None) is None


class TestConversationIdRoundTrip:
    def test_with_thread_ts(self):
        cid = create_conversation_id("B1", "T1", "C1", "111.222")
        assert cid == "B1:T1:C1:111.222"
        assert slack_bot_id_from_conversation_id(cid) == "B1"
        assert slack_team_id_from_conversation_id(cid) == "T1"
        assert slack_channel_id_from_conversation_id(cid) == "C1"
        assert slack_thread_ts_from_conversation_id(cid) == "111.222"

    def test_without_thread_ts(self):
        cid = create_conversation_id("B1", "T1", "C1")
        assert cid == "B1:T1:C1"
        assert slack_thread_ts_from_conversation_id(cid) is None

    def test_invalid_id_raises(self):
        with pytest.raises(ValueError):
            slack_bot_id_from_conversation_id("only:two")
        with pytest.raises(ValueError):
            slack_bot_id_from_conversation_id("")
