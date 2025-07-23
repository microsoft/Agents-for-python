from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class MediaUrl(AgentsModel):
    """Media URL.

    :param url: Url for the media
    :type url: str
    :param profile: Optional profile hint to the client to differentiate
     multiple MediaUrl objects from each other
    :type profile: str
    """

    url: NonEmptyString = None
    profile: NonEmptyString = None
