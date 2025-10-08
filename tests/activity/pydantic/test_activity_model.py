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
        "data, expected,
        [
            (ChannelId.MSTEAMS, ChannelId(channel=C)),
            ("msteams", "msteams",),
            ("msteams/subchannel", "msteams/subchannel"),
            ("channel:sub", "channel:sub"),
        ]

    def test_channel_id_field_validator_basic(self):
        activity = Activity(type="message")
        activity.channel_id = ChannelId.MSTEAMS
        assert activity.channel_id == ChannelId.MSTEAMS
        assert isinstance(activity.channel_id, ChannelId)

    def test_channel_id_field_validator_from_str_basic(self):
        activity = Activity(type="message")
        activity.channel_id = "msteams"
        assert activity.channel_id == "msteams"
        assert isinstance(activity.channel_id, ChannelId)

    def test_channel_id_field_validator_from_str_with_sub_channel(self):
        pass