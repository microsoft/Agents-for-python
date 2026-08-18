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
    EntityTypes.AI_CITATION.value.casefold(): (
        EntityTypes.AI_CITATION.value,
        AIEntity,
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


def _validate_known_entities(entities: Any) -> list[Entity]:
    """Deserialize known activity entities while preserving unknown entity types.

    :param entities: The data to validate and deserialize into known entity types.
    :returns: A list of validated entities, with known types deserialized into their respective classes
    :raises ValueError: If the input is not a list or tuple, or if an entity is not a dict or Entity instance.
    """
    if entities is None:
        return []

    if not isinstance(entities, (list, tuple)):
        raise ValueError("entities must be a list or tuple")

    validated_entities: list[Entity] = []
    for entity in entities:
        if isinstance(entity, Entity):
            validated_entities.append(entity)
            continue

        if not isinstance(entity, dict):
            raise ValueError(f"entity must be a dict or Entity, got {type(entity)}")

        entity_type = entity.get("type")
        if not entity_type:
            raise ValueError(
                "entity must have a 'type' field. Cannot infer entity type from data."
            )

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
