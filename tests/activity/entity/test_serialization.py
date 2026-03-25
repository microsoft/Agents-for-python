import pytest

from microsoft_agents.activity.entity import (
    AIEntity,
    ClientCitation,
    ClientCitationAppearance,
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
