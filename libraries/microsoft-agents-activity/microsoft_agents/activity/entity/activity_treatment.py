# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import Enum
from typing import Literal

from .entity import Entity
from .entity_types import EntityTypes


class ActivityTreatmentTypes(str, Enum):
    """Well-known enumeration of activity treatment types."""

    TARGETED = "targeted"


class ActivityTreatment(Entity):
    """Activity treatment information (entity type: "activityTreatment").

    :param treatment: The type of treatment
    :type treatment: ~microsoft_agents.activity.ActivityTreatmentTypes
    :param type: Type of this entity (RFC 3987 IRI)
    :type type: str
    """

    type: Literal[EntityTypes.ACTIVITY_TREATMENT] = EntityTypes.ACTIVITY_TREATMENT
    treatment: ActivityTreatmentTypes
