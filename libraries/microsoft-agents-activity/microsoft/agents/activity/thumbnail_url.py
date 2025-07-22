from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class ThumbnailUrl(AgentsModel):
    """Thumbnail URL.

    :param url: URL pointing to the thumbnail to use for media content
    :type url: str
    :param alt: HTML alt text to include on this thumbnail image
    :type alt: str
    """

    url: NonEmptyString = None
    alt: NonEmptyString = None
