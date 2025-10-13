# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Literal

from .._type_aliases import NonEmptyString
from .entity import Entity
from .entity_types import EntityTypes


class Thing(Entity):
    """Thing (entity type: "https://schema.org/Thing").

    :param type: The type of the thing
    :type type: str
    :param name: The name of the thing
    :type name: str
    """

    type: Literal[EntityTypes.THING] = EntityTypes.THING
    name: NonEmptyString = None
