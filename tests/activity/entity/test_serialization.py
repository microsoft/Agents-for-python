import pytest

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
