import pytest
import pydantic

from microsoft_agents.activity import ChannelId

from tests._common.data import TEST_DEFAULTS

DEFAULTS = TEST_DEFAULTS()

class TestChannelId:

    @pytest.mark.parametrize(
        "input, expected",
        [
            [
                "email:support",
                ChannelId(channel="email", sub_channel="support")
            ],
            [
                "email",
                ChannelId(channel="email", sub_channel=None)
            ],
            [
                " email:support ",
                ChannelId(channel="email", sub_channel="support")
            ],
            [
                " email ",
                ChannelId(channel="email", sub_channel=None)
            ],
            [
                "email:support:extra",
                ChannelId(channel="email", sub_channel="support:extra")
            ],
            [
                {
                    "channel": "email",
                    "sub_channel": "support"
                },
                ChannelId(channel="email", sub_channel="support")
            ]
        ]
    )
    def test_validation_dict_form(self, data, expected):
        channel_id = ChannelId.model_validate(data)
        assert channel_id == expected

    @pytest.mark.parametrize(
        "channel_a, channel_b, expected",
        [
            [
                ChannelId(channel="email", sub_channel="support"),
                ChannelId(channel="email", sub_channel="support"),
                True
            ],
            [
                ChannelId(channel="email", sub_channel="support"),
                ChannelId(channel="word", sub_channel="support"),
                True
            ],
            [
                ChannelId(channel="email", sub_channel="support"),
                ChannelId(channel="email", sub_channel="info"),
                False
            ],
            [
                ChannelId(channel="email", sub_channel=None),
                ChannelId(channel="email", sub_channel=None),
                True
            ],
            [
                ChannelId(channel="email", sub_channel=None),
                ChannelId(channel="email", sub_channel="support"),
                False
            ],
            [
                ChannelId(channel="email", sub_channel=None),
                ChannelId(channel="sms", sub_channel=None),
                False
            ]
        ]
    )
    def test_eq(self, channel_a, channel_b, expected):
        assert (a == b) == expected
        assert (a == a) == True

    def test_hash(self):
        a = ChannelId(channel="email", sub_channel="SUPPORT")
        assert hash(a) == hash(str(a))

    def test_str(self):
        a = ChannelId(channel="email", sub_channel="support")
        assert str(a) == "email:support"
        b = ChannelId(channel="email", sub_channel=None)
        assert str(b) == "email"
        c = ChannelId({"channel": "agents", "sub_channel": "word"})
        assert str(c) == "agents:word"
        d = ChannelId("agents:COPILOT")
        assert str(d) == "agents:COPILOT"

    # def test_validation_error(self):
    #     pass

    # def test_serialization(self):
    #     pass