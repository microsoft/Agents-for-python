import pytest
from pydantic import ValidationError

from microsoft_agents.activity.entity import Entity


def test_entity_requires_type():
    with pytest.raises(ValidationError):
        Entity()


def test_entity_additional_properties_returns_extra_fields():
    entity = Entity(type="custom", custom_value="value", count=1)

    assert entity.additional_properties == {
        "custom_value": "value",
        "count": 1,
    }


def test_entity_validates_camel_case_extra_fields_as_snake_case():
    entity = Entity.model_validate(
        {
            "type": "custom",
            "customValue": "value",
        }
    )

    assert entity.additional_properties == {"custom_value": "value"}
    assert entity.model_dump(by_alias=True) == {
        "type": "custom",
        "customValue": "value",
    }
    assert entity.model_dump(by_alias=False) == {
        "type": "custom",
        "custom_value": "value",
    }


def test_entity_serialization_always_includes_type():
    entity = Entity(type="custom")

    assert entity.model_dump(exclude_unset=True) == {"type": "custom"}
    assert entity.model_dump(exclude_none=True) == {"type": "custom"}


def test_entity_preserves_schema_at_fields_when_serializing_by_alias():
    entity = Entity.model_validate(
        {
            "type": "custom",
            "@type": "schema-type",
            "@context": "https://schema.org",
            "@id": "schema-id",
        }
    )

    assert entity.additional_properties == {
        "@type": "schema-type",
        "@context": "https://schema.org",
        "@id": "schema-id",
        "at_type": "schema-type",
        "at_context": "https://schema.org",
        "at_id": "schema-id",
    }
    assert entity.model_dump(by_alias=True) == {
        "type": "custom",
        "@type": "schema-type",
        "@context": "https://schema.org",
        "@id": "schema-id",
        "atType": "schema-type",
        "atContext": "https://schema.org",
        "atId": "schema-id",
    }
    assert entity.model_dump(by_alias=False) == {
        "type": "custom",
        "@type": "schema-type",
        "@context": "https://schema.org",
        "@id": "schema-id",
        "at_type": "schema-type",
        "at_context": "https://schema.org",
        "at_id": "schema-id",
    }
