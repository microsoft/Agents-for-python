# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from pydantic import ValidationError

from microsoft_agents.activity import (
    Activity,
    ActivityTreatment,
    AIEntity,
    Entity,
    GeoCoordinates,
    Mention,
    Place,
    ProductInfo,
    StreamInfo,
    Thing,
)


@pytest.mark.parametrize(
    ("entity_data", "expected_type"),
    [
        (
            {"type": "activityTreatment", "treatment": "targeted"},
            ActivityTreatment,
        ),
        ({"type": "GeoCoordinates", "latitude": 47.6}, GeoCoordinates),
        ({"type": "mention", "text": "Ada"}, Mention),
        ({"type": "Place", "name": "Seattle"}, Place),
        ({"type": "ProductInfo", "id": "copilot"}, ProductInfo),
        ({"type": "streaminfo", "streamSequence": 1}, StreamInfo),
        ({"type": "Thing", "name": "Document"}, Thing),
        (
            {
                "type": "https://schema.org/Message",
                "@type": "Message",
                "@context": "https://schema.org",
            },
            AIEntity,
        ),
    ],
)
def test_activity_deserializes_known_entity_types(entity_data, expected_type):
    activity = Activity.model_validate(
        {
            "type": "message",
            "entities": [entity_data],
        }
    )

    assert isinstance(activity.entities[0], expected_type)


@pytest.mark.parametrize(
    ("entity_data", "expected_type", "canonical_type"),
    [
        ({"type": "MENTION"}, Mention, "mention"),
        (
            {"type": "ACTIVITYTREATMENT", "treatment": "targeted"},
            ActivityTreatment,
            "activityTreatment",
        ),
        ({"type": "PRODUCTINFO", "id": "copilot"}, ProductInfo, "ProductInfo"),
        ({"type": "STREAMINFO", "streamSequence": 1}, StreamInfo, "streaminfo"),
        (
            {"type": "HTTPS://SCHEMA.ORG/MESSAGE"},
            AIEntity,
            "https://schema.org/Message",
        ),
    ],
)
def test_activity_matches_known_entity_types_case_insensitively(
    entity_data, expected_type, canonical_type
):
    activity = Activity.model_validate(
        {
            "type": "message",
            "entities": [entity_data],
        }
    )

    assert isinstance(activity.entities[0], expected_type)
    assert activity.entities[0].type == canonical_type


@pytest.mark.parametrize(
    "entity_data",
    [
        {"type": "streaminfo"},
        {"type": "streaminfo", "streamSequence": None},
    ],
)
def test_activity_deserializes_stream_info_without_sequence(entity_data):
    activity = Activity.model_validate(
        {
            "type": "message",
            "entities": [entity_data],
        }
    )

    stream_info = activity.entities[0]

    assert isinstance(stream_info, StreamInfo)
    assert stream_info.stream_sequence is None


def test_activity_omits_none_stream_sequence_when_serializing():
    activity = Activity(type="message", entities=[StreamInfo()])

    serialized = activity.model_dump(mode="json", by_alias=True, exclude_none=True)

    assert serialized["entities"][0] == {
        "type": "streaminfo",
        "streamType": "streaming",
        "streamId": "",
        "streamResult": "",
        "feedbackLoopEnabled": False,
    }


def test_activity_preserves_unknown_entity_types():
    activity = Activity.model_validate(
        {
            "type": "message",
            "entities": [
                {
                    "type": "customEntity",
                    "customValue": "value",
                }
            ],
        }
    )

    entity = activity.entities[0]
    assert type(entity) is Entity
    assert entity.additional_properties == {"custom_value": "value"}


def test_activity_deserializes_schema_message_as_ai_entity_without_additional_type():
    activity = Activity.model_validate(
        {
            "type": "message",
            "entities": [
                {
                    "type": "https://schema.org/Message",
                    "@type": "Message",
                    "@context": "https://schema.org",
                }
            ],
        }
    )

    assert isinstance(activity.entities[0], AIEntity)
    assert activity.entities[0].additional_type == ["AIGeneratedContent"]


def test_activity_preserves_existing_entity_instances():
    mention = Mention(text="Ada")

    activity = Activity(type="message", entities=[mention])

    assert activity.entities[0] is mention


def test_activity_normalizes_null_entities_to_empty_list():
    activity = Activity.model_validate(
        {
            "type": "message",
            "entities": None,
        }
    )

    assert activity.entities == []


@pytest.mark.parametrize("entities", ["mention", {"type": "mention"}])
def test_activity_rejects_invalid_entities_collection(entities):
    with pytest.raises(ValidationError, match="entities must be a list or tuple"):
        Activity.model_validate(
            {
                "type": "message",
                "entities": entities,
            }
        )


@pytest.mark.parametrize("entity", [None, "mention", 1])
def test_activity_rejects_invalid_entity_items(entity):
    with pytest.raises(ValidationError, match="entity must be a dict or Entity"):
        Activity.model_validate(
            {
                "type": "message",
                "entities": [entity],
            }
        )


@pytest.mark.parametrize("entity", [{}, {"text": "Ada"}, {"type": ""}])
def test_activity_rejects_entities_without_type(entity):
    with pytest.raises(ValidationError, match="entity must have a 'type' field"):
        Activity.model_validate(
            {
                "type": "message",
                "entities": [entity],
            }
        )


def test_activity_accepts_entity_tuple():
    activity = Activity.model_validate(
        {
            "type": "message",
            "entities": ({"type": "mention", "text": "Ada"},),
        }
    )

    assert activity.entities == [Mention(text="Ada")]


def test_activity_rejects_invalid_known_entity():
    with pytest.raises(ValidationError):
        Activity.model_validate(
            {
                "type": "message",
                "entities": [{"type": "activityTreatment"}],
            }
        )


def test_activity_entities_round_trip_preserves_typed_models():
    activity = Activity.model_validate(
        {
            "type": "message",
            "channelId": "msteams:copilot",
            "entities": [
                {"type": "activityTreatment", "treatment": "targeted"},
                {
                    "type": "https://schema.org/Message",
                    "@type": "Message",
                    "@context": "https://schema.org",
                    "citation": [
                        {
                            "@type": "Claim",
                            "position": 1,
                            "appearance": {"name": "SDK documentation"},
                        }
                    ],
                },
                {
                    "type": "GeoCoordinates",
                    "latitude": 47.6,
                    "longitude": -122.3,
                },
                {
                    "type": "mention",
                    "mentioned": {"id": "user-id", "name": "Ada"},
                    "text": "<at>Ada</at>",
                },
                {"type": "Place", "name": "Seattle"},
                {"type": "ProductInfo", "id": "copilot"},
                {
                    "type": "streaminfo",
                    "streamSequence": 1,
                    "streamId": "stream-id",
                },
                {"type": "Thing", "name": "Document"},
                {"type": "customEntity", "customValue": "value"},
            ],
        }
    )

    serialized = activity.model_dump(mode="json", by_alias=True, exclude_none=True)
    round_tripped = Activity.model_validate(serialized)

    assert round_tripped == activity
    assert [type(entity) for entity in round_tripped.entities] == [
        ActivityTreatment,
        AIEntity,
        GeoCoordinates,
        Mention,
        Place,
        ProductInfo,
        StreamInfo,
        Thing,
        Entity,
    ]
