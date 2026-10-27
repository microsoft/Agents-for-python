import pytest

from microsoft_agents.activity import ChannelId

from tests._common.data import DEFAULT_TEST_VALUES

DEFAULTS = DEFAULT_TEST_VALUES()


class TestChannelId:
    def test_init_from_str(self):
        channel_id = ChannelId("email:support")
        assert channel_id.channel == "email"
        assert channel_id.sub_channel == "support"
        assert str(channel_id) == "email:support"
        assert channel_id == "email:support"
        assert channel_id in ["email:support", "other"]
        assert channel_id not in ["email:other", "other"]
        assert channel_id != "email:other"
        assert channel_id in ["wow", ChannelId("email:support")]
        assert channel_id == ChannelId("email:support")

    def test_init_multiple_colons(self):
        assert ChannelId("email:support:extra").channel == "email"
        assert ChannelId("email:support:extra").sub_channel == "support:extra"

    def test_init_from_channel_id_reuses_instance(self):
        channel_id = ChannelId("email:support")

        assert ChannelId(channel_id) is channel_id

    def test_get_channel_strips_and_drops_sub_channel(self):
        assert ChannelId.get_channel(" msteams ") == "msteams"
        assert ChannelId.get_channel("msteams:sub") == "msteams"
        assert ChannelId.get_channel("msteams:") == "msteams"
        assert ChannelId.get_channel(None) is None

    def test_get_sub_channel_empty_is_none(self):
        assert ChannelId.get_sub_channel("msteams:sub") == "sub"
        assert ChannelId.get_sub_channel("msteams:") is None
        assert ChannelId.get_sub_channel(" msteams: sub ") == "sub"
        assert ChannelId.get_sub_channel(None) is None

    def test_init_multiple_args(self):
        with pytest.raises(ValueError):
            ChannelId("email:support", channel="a", sub_channel="b")

    def test_init_from_parts(self):
        channel_id = ChannelId(channel="email", sub_channel="support")
        assert channel_id.channel == "email"
        assert channel_id.sub_channel == "support"
        assert str(channel_id) == "email:support"

        channel_id2 = ChannelId(channel="email")
        assert channel_id2.channel == "email"
        assert channel_id2.sub_channel is None
        assert str(channel_id2) == "email"

    def test_init_errors(self):
        with pytest.raises(Exception):
            ChannelId(channel="email", sub_channel=123)
        with pytest.raises(Exception):
            ChannelId(channel="", sub_channel="support")
        with pytest.raises(Exception):
            ChannelId("")
        with pytest.raises(Exception):
            ChannelId()
        with pytest.raises(Exception):
            ChannelId(channel=None)
        with pytest.raises(Exception):
            ChannelId(sub_channel="sub_channel")
        with pytest.raises(Exception):
            ChannelId("   \t\n  ")
        with pytest.raises(Exception):
            ChannelId("", channel=" ", sub_channel="support")
        with pytest.raises(Exception):
            ChannelId(channel="a:b", sub_channel="support")
