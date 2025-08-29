import pytest

from microsoft_agents.activity import (
    AIEntity,
    Mention,
    AtEntityTypes,
    EntityTypes,
    GeoCoordinates,
    Place,
    Thing
)

class TestEntityInit:

    @pytest.mark.parametrize(
        "entity_cls, entity_type, at_entity_type",
        [
            (Mention, EntityTypes.MENTION, AtEntityTypes.MENTION),
            (GeoCoordinates, EntityTypes.GEO_COORDINATES, AtEntityTypes.GEO_COORDINATES),
            (Place, EntityTypes.PLACE, AtEntityTypes.PLACE),
            (Thing, EntityTypes.THING, AtEntityTypes.THING),
            (AIEntity, EntityTypes.AI_ENTITY, AtEntityTypes.AI_ENTITY),
        ]
    )
    def test_entity_constants(self, entity_cls, entity_type, at_entity_type):
        entity = entity_cls()
        assert entity.type == entity_type
        assert entity.at_type == at_entity_type