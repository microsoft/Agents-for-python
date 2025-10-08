import pytest

from microsoft_agents.activity import (
    Activity,
    ChannelId
)

class TestActivityModel:

    def test_serialize_basic(self, activity):
        activity_copy = Activity(
            **activity.model_dump(mode="json", exclude_unset=True, by_alias=True)
        )
        assert activity_copy == activity

    @pytest.mark.parametrize(
        "data, expected",
        [
            ("msteams:subchannel", ChannelId(channel="msteams", sub_channel="subchannel")),
            ("msteams/subchannel", ChannelId(channel="msteams/subchannel")),
            ("channel:sub", ChannelId(channel="channel", sub_channel="sub")),
            (ChannelId(channel="msteams", sub_channel="subchannel"), ChannelId(channel="msteams", sub_channel="subchannel")),
            (ChannelId(channel="msteams"), ChannelId(channel="msteams")),
        ])
    def test_channel_id_field_validator(self, data, expected):
        activity = Activity(type="message")
        activity.channel_id = data

        assert activity.channel_id == expected
        breakpoint()
        assert isinstance(activity.channel_id, ChannelId)
        assert activity.channel_id == data