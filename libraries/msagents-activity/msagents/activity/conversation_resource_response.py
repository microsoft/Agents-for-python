from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class ConversationResourceResponse(AgentsModel):
    """A response containing a resource.

    :param activity_id: ID of the Activity (if sent)
    :type activity_id: str
    :param service_url: Service endpoint where operations concerning the
     conversation may be performed
    :type service_url: str
    :param id: Id of the resource
    :type id: str
    """

    activity_id: NonEmptyString = None
    service_url: NonEmptyString = None
    id: NonEmptyString = None
