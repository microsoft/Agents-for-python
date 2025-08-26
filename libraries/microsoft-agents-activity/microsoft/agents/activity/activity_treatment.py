from enum import Enum

from .entity import Entity, EntityTypes
from ._type_aliases import NonEmptyString


class ActivityTreatmentType(str, Enum):
    """Activity treatment types

    TARGETED: only the recipient should be able to see the message even if the activity
        is being sent to a group of people.
    """

    TARGETED = "targeted"


class ActivityTreatment(Entity):
    """Activity treatment information (entity type: "activitytreatment").

    :param treatment: The treatment type
    :type treatment: ~microsoft.agents.activity.ActivityTreatmentType
    :param type: Type of this entity (RFC 3987 IRI)
    :type type: NonEmptyString
    """

    treatment: ActivityTreatmentType = None
    type: NonEmptyString = EntityTypes.ACTIVITY_TREATMENT
