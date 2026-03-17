import pytest

from microsoft_agents.activity.entity import (
    AIEntity,
    ClientCitation,
    ClientCitationAppearance,
    SensitivityPattern,
    SensitivityUsageInfo,
)

@pytest.mark.parametrize(
    "entity_cls"
    [
        ClientCitation,
        SensitivityUsageInfo,
        ClientCitationAppearance,
        SensitivityPattern
    ]
)
def test_schema_mixin_at_type_serialization(entity_cls):

    expected = entity_cls.at_type
    assert isinstance(expected, str) and expected != ""

    entity = entity_cls()

    data = entity.model_dump(exclude_unset=True)

    assert "@type" in data
    assert data["@type"] == expected

def test_schema_mixin_at_context_serialization():

    ai_entity = AIEntity()

    data = ai_entity.model_dump(exclude_unset=True)

    assert data["@type"] == AIEntity.at_type
    assert data["@context"] == AIEntity.at_context