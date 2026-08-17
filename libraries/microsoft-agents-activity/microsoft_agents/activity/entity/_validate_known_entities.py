# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any

from .activity_treatment import ActivityTreatment
from .ai_entity import AIEntity
from .entity import Entity
from .entity_types import EntityTypes
from .geo_coordinates import GeoCoordinates
from .mention import Mention
from .place import Place
from .product_info import ProductInfo
from .stream_info import StreamInfo
from .thing import Thing

_KNOWN_ENTITY_TYPES: dict[str, tuple[str, type[Entity]]] = {
    EntityTypes.ACTIVITY_TREATMENT.value.casefold(): (
        EntityTypes.ACTIVITY_TREATMENT.value,
        ActivityTreatment,
    ),
    EntityTypes.GEO_COORDINATES.value.casefold(): (
        EntityTypes.GEO_COORDINATES.value,
        GeoCoordinates,
    ),
    EntityTypes.MENTION.value.casefold(): (EntityTypes.MENTION.value, Mention),
    EntityTypes.PLACE.value.casefold(): (EntityTypes.PLACE.value, Place),
    EntityTypes.PRODUCT_INFO.value.casefold(): (
        EntityTypes.PRODUCT_INFO.value,
        ProductInfo,
    ),
    EntityTypes.STREAM_INFO.value.casefold(): (
        EntityTypes.STREAM_INFO.value,
        StreamInfo,
    ),
    EntityTypes.THING.value.casefold(): (EntityTypes.THING.value, Thing),
}


def _is_ai_entity(data: dict[str, Any]) -> bool:
    entity_type = data.get("type")
    if (
        not isinstance(entity_type, str)
        or entity_type.casefold() != "https://schema.org/Message".casefold()
    ):
        return False

    additional_types = data.get("additionalType", data.get("additional_type", []))
    return (
        isinstance(additional_types, list)
        and "AIGeneratedContent" in additional_types
    )


def _validate_known_entities(entities: Any) -> Any:
    """Deserialize known activity entities while preserving unknown entity types."""
    if not isinstance(entities, (list, tuple)):
        return entities

    validated_entities: list[Any] = []
    for entity in entities:
        if isinstance(entity, Entity):
            validated_entities.append(entity)
            continue

        if not isinstance(entity, dict):
            validated_entities.append(entity)
            continue

        entity_type = entity.get("type")
        if _is_ai_entity(entity):
            entity_data = {**entity, "type": "https://schema.org/Message"}
            validated_entities.append(AIEntity.model_validate(entity_data))
            continue

        known_entity = (
            _KNOWN_ENTITY_TYPES.get(entity_type.casefold())
            if isinstance(entity_type, str)
            else None
        )
        if known_entity:
            canonical_type, entity_cls = known_entity
            entity = {**entity, "type": canonical_type}
        else:
            entity_cls = Entity

        validated_entities.append(entity_cls.model_validate(entity))

    return validated_entities