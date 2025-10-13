import pytest

from pydantic import ValidationError

from microsoft_agents.activity import (
    Activity,
    ChannelId,
    Entity,
    EntityTypes,
    ProductInfo,
    ConversationReference,
    ConversationAccount,
)


# validation / serialization tests
class TestActivityIO:

    def test_serialize_basic(self):
        activity = Activity(type="message")
        activity_copy = Activity(
            **activity.model_dump(mode="json", exclude_unset=True, by_alias=True)
        )
        assert activity_copy == activity

    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                "msteams:subchannel",
                ChannelId(channel="msteams", sub_channel="subchannel"),
            ),
            ("msteams/subchannel", ChannelId(channel="msteams/subchannel")),
            ("channel:sub", ChannelId(channel="channel", sub_channel="sub")),
            (
                ChannelId(channel="msteams", sub_channel="subchannel"),
                ChannelId(channel="msteams", sub_channel="subchannel"),
            ),
            (ChannelId(channel="msteams"), ChannelId(channel="msteams")),
        ],
    )
    def test_channel_id_setter_validation(self, data, expected):
        activity = Activity(type="message")
        activity.channel_id = data

        assert activity.channel_id == expected
        assert isinstance(activity.channel_id, ChannelId)
        if not isinstance(data, dict):
            assert activity.channel_id == data

    def test_channel_id_setter_validation_error(self):
        activity = Activity(type="message")
        with pytest.raises(Exception):
            activity.channel_id = {}
        with pytest.raises(Exception):
            activity.channel_id = 123

    def test_channel_id_validate_without_product_info(self):
        data = {"type": "message", "channel_id": "msteams:subchannel"}
        activity = Activity(**data)
        assert activity.channel_id == ChannelId(
            channel="msteams", sub_channel="subchannel"
        )
        assert not activity.get_product_info_entity()

    @pytest.mark.parametrize(
        "data, data_with_alias, expected",
        [
            [
                {
                    "type": "message",
                    "channel_id": "parent:misc",
                    "entities": [{"type": "some_entity"}],
                },
                {
                    "type": "message",
                    "channelId": "parent:misc",
                    "entities": [{"type": "some_entity"}],
                },
                Activity(
                    type="message",
                    channel_id="parent:misc",
                    entities=[Entity(type="some_entity")],
                ),
            ],
            [
                {
                    "type": "message",
                    "channel_id": "parent",
                    "entities": [
                        {"type": "some_entity"},
                        {"type": EntityTypes.PRODUCT_INFO, "id": "misc"},
                    ],
                },
                {
                    "type": "message",
                    "channelId": "parent",
                    "entities": [
                        {"type": "some_entity"},
                        {"type": EntityTypes.PRODUCT_INFO, "id": "misc"},
                    ],
                },
                Activity(
                    type="message",
                    channel_id="parent:misc",
                    entities=[
                        Entity(type="some_entity"),
                        Entity(type=EntityTypes.PRODUCT_INFO, id="misc"),
                    ],
                ),
            ],
        ],
    )
    def test_channel_id_sub_channel_changed_with_product_info(
        self, data, data_with_alias, expected
    ):
        activity = Activity(**data)
        activity_from_alias = Activity(**data_with_alias)
        assert activity == expected
        assert activity_from_alias == expected
        assert activity.model_copy() == activity_from_alias.model_copy()

    def test_channel_id_sub_channel_conflict_on_validation(self):
        with pytest.raises(Exception):
            activity = Activity(
                type="message",
                channel_id="parent:misc",
                entities=[Entity(type="some_type"), ProductInfo(id="sub_channel")],
            )

    def test_channel_id_unset_becomes_set_at_init(self):
        activity = Activity(type="message")
        activity.channel_id = "channel:sub_channel"
        data = activity.model_dump(mode="json", exclude_unset=True, by_alias=True)
        assert data["channelId"] == "channel:sub_channel"

    def test_channel_id_unset_at_init_not_included(self):
        activity = Activity(type="message")
        data = activity.model_dump(mode="json", exclude_unset=True, by_alias=True)
        assert "channelId" not in data

    def test_product_info_avoids_error_no_parent_channel(self):
        activity = Activity(type="message", entities=[ProductInfo(id="sub_channel")])
        assert activity.channel_id is None

    @pytest.mark.parametrize(
        "activity, expected, expected_no_alias",
        [
            [Activity(type="message"), {"type": "message"}, {"type": "message"}],
            [
                Activity(type="message", channel_id="msteams"),
                {"type": "message", "channelId": "msteams"},
                {"type": "message", "channel_id": "msteams"},
            ],
            [
                Activity(type="message", channel_id="msteams:subchannel"),
                {
                    "type": "message",
                    "channelId": "msteams:subchannel",
                    "entities": [
                        {"type": str(EntityTypes.PRODUCT_INFO), "id": "subchannel"}
                    ],
                },
                {
                    "type": "message",
                    "channel_id": "msteams:subchannel",
                    "entities": [
                        {"type": str(EntityTypes.PRODUCT_INFO), "id": "subchannel"}
                    ],
                },
            ],
            [
                Activity(
                    type="message",
                    channel_id="msteams:subchannel",
                    entities=[Entity(type="other")],
                ),
                {
                    "type": "message",
                    "channelId": "msteams:subchannel",
                    "entities": [
                        {"type": "other"},
                        {"type": str(EntityTypes.PRODUCT_INFO), "id": "subchannel"},
                    ],
                },
                {
                    "type": "message",
                    "channel_id": "msteams:subchannel",
                    "entities": [
                        {"type": "other"},
                        {"type": str(EntityTypes.PRODUCT_INFO), "id": "subchannel"},
                    ],
                },
            ],
            [
                Activity(
                    type="message",
                    channel_id="msteams:misc",
                    entities=[{"type": "other"}, ProductInfo(id="misc")],
                ),
                {
                    "type": "message",
                    "channelId": "msteams:misc",
                    "entities": [
                        {"type": "other"},
                        {"type": str(EntityTypes.PRODUCT_INFO), "id": "misc"},
                    ],
                },
                {
                    "type": "message",
                    "channel_id": "msteams:misc",
                    "entities": [
                        {"type": "other"},
                        {"type": str(EntityTypes.PRODUCT_INFO), "id": "misc"},
                    ],
                },
            ],
            [
                Activity(type="message", entities=[ProductInfo(id="misc")]),
                {"type": "message"},
                {"type": "message"},
            ],
        ],
    )
    def test_serialize(self, activity, expected, expected_no_alias):
        data = activity.model_dump(mode="json", exclude_unset=True, by_alias=True)
        data_no_alias = activity.model_dump(exclude_unset=True, by_alias=False)
        assert data == expected
        assert data_no_alias == expected_no_alias

    def test_model_dump(self):
        activity = Activity(type="message")
        data = activity.model_dump(exclude_unset=True)
        assert data == {"type": "message"}

    def test_serialize_misconfiguration_no_sub_channel(self):
        activity = Activity(
            type="message", channel_id="msteams", entities=[{"type": "other"}]
        )
        activity.entities.append(ProductInfo(id="sub_channel"))

        data = activity.model_dump(mode="json", exclude_unset=True, by_alias=True)
        assert data == {
            "type": "message",
            "channelId": "msteams",
            "entities": [
                {"type": "other"},
            ],
        }

    def test_serialize_sub_channel_conflict(self):
        activity = Activity(
            type="message",
            channel_id="msteams:subchannel",
            entities=[{"type": "other"}],
        )
        activity.entities.append(ProductInfo(id="other_sub_channel"))

        with pytest.raises(Exception):
            activity.model_dump(mode="json", exclude_unset=True, by_alias=True)
