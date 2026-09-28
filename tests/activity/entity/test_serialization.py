import pytest

from microsoft_agents.activity import Activity
from microsoft_agents.activity.entity import (
    AIEntity,
    ClientCitation,
    ClientCitationAppearance,
    ClientCitationIconName,
    SensitivityPattern,
    SensitivityUsageInfo,
)


@pytest.mark.parametrize(
    "entity_cls",
    [
        ClientCitation,
        SensitivityUsageInfo,
        ClientCitationAppearance,
        SensitivityPattern,
    ],
)
def test_schema_mixin_at_type_serialization(entity_cls):

    entity = entity_cls()

    data = entity.model_dump(exclude_unset=True, by_alias=True)

    assert "@type" in data
    assert data["@type"] == entity.at_type
    assert "at_type" not in data


@pytest.mark.parametrize(
    "entity_cls",
    [
        ClientCitation,
        SensitivityUsageInfo,
        ClientCitationAppearance,
        SensitivityPattern,
    ],
)
def test_schema_mixin_at_type_serialization_no_alias(entity_cls):

    entity = entity_cls()

    data = entity.model_dump(exclude_unset=True, by_alias=False)

    assert "@type" not in data


def test_schema_mixin_at_context_serialization():

    ai_entity = AIEntity()

    data = ai_entity.model_dump(exclude_unset=True, by_alias=True)

    assert data["@type"] == "Message"
    assert data["@context"] == "https://schema.org"

    assert "at_type" not in data
    assert "at_context" not in data


@pytest.mark.parametrize(
    "entity_cls",
    [
        SensitivityUsageInfo,
        ClientCitationAppearance,
        SensitivityPattern,
    ],
)
def test_schema_mixin_ignores_at_id_when_model_does_not_define_it(entity_cls):
    entity = entity_cls.model_validate({"@id": "schema-id"})

    assert not hasattr(entity, "at_id")
    assert "@id" not in entity.model_dump(exclude_unset=True, by_alias=True)


def test_client_citation_without_at_id_omits_schema_id():
    data = ClientCitation().model_dump(exclude_unset=True, by_alias=True)

    assert "@id" not in data
    assert "atId" not in data


def test_client_citation_deserializes_and_serializes_schema_id():
    citation = ClientCitation.model_validate(
        {
            "@type": "Claim",
            "@id": "turn16search0",
            "position": 1,
            "appearance": {
                "@type": "DigitalDocument",
                "name": "Example citation",
            },
        }
    )

    assert citation.at_id == "turn16search0"

    data = citation.model_dump(exclude_unset=True, by_alias=True)

    assert data["@type"] == "Claim"
    assert data["@id"] == "turn16search0"
    assert "atType" not in data
    assert "atId" not in data
    assert data["appearance"]["@type"] == "DigitalDocument"
    assert "atType" not in data["appearance"]


def test_activity_deserializes_client_citation_schema_id():
    activity = Activity.model_validate(
        {
            "type": "message",
            "entities": [
                {
                    "type": "https://schema.org/Message",
                    "@type": "Message",
                    "@context": "https://schema.org",
                    "citation": [
                        {
                            "@type": "Claim",
                            "@id": "turn16search0",
                            "position": 1,
                            "appearance": {
                                "@type": "DigitalDocument",
                                "name": "Example citation",
                            },
                        }
                    ],
                }
            ],
        }
    )

    entity = activity.entities[0]

    assert isinstance(entity, AIEntity)
    assert entity.citation is not None
    assert entity.citation[0].at_id == "turn16search0"


def test_client_citation_icon_name_matches_teams_docs():
    """The icon names must match the predefined values documented for
    citation.appearance.image.name in the Teams "Add citations" article:
    https://learn.microsoft.com/en-us/microsoftteams/platform/bots/how-to/bot-messages-ai-generated-content#add-citations
    """
    expected_values = [
        "Microsoft Word",
        "Microsoft Excel",
        "Microsoft PowerPoint",
        "Microsoft OneNote",
        "Microsoft SharePoint",
        "Microsoft Visio",
        "Microsoft Loop",
        "Microsoft Whiteboard",
        "Source Code",
        "Sketch",
        "Adobe Illustrator",
        "Adobe Photoshop",
        "Adobe InDesign",
        "Adobe Flash",
        "Image",
        "GIF",
        "Video",
        "Sound",
        "ZIP",
        "Text",
        "PDF",
    ]

    actual_values = [member.value for member in ClientCitationIconName]

    assert set(actual_values) == set(expected_values)
    assert actual_values == expected_values
