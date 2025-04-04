from pydantic import BaseModel
from typing import Optional


class O365ConnectorCardImage(BaseModel):
    """O365 connector card image.

    :param image: URL for the image.
    :type image: str
    :param title: Title of the image.
    :type title: Optional[str]
    """

    image: str
    title: Optional[str]
