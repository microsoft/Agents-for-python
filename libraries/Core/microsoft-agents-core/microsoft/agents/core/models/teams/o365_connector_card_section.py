from pydantic import BaseModel
from typing import List, Optional


class O365ConnectorCardSection(BaseModel):
    """O365 connector card section.

    :param title: Title of the section.
    :type title: Optional[str]
    :param text: Text for the section.
    :type text: Optional[str]
    :param activity_title: Activity title.
    :type activity_title: Optional[str]
    :param activity_subtitle: Activity subtitle.
    :type activity_subtitle: Optional[str]
    :param activity_image: Activity image URL.
    :type activity_image: Optional[str]
    :param activity_text: Activity text.
    :type activity_text: Optional[str]
    :param facts: List of facts for the section.
    :type facts: Optional[List["O365ConnectorCardFact"]]
    :param images: List of images for the section.
    :type images: Optional[List["O365ConnectorCardImage"]]
    :param potential_action: List of actions for the section.
    :type potential_action: Optional[List["O365ConnectorCardActionBase"]]
    """

    title: Optional[str]
    text: Optional[str]
    activity_title: Optional[str]
    activity_subtitle: Optional[str]
    activity_image: Optional[str]
    activity_text: Optional[str]
    facts: Optional[List["O365ConnectorCardFact"]]
    images: Optional[List["O365ConnectorCardImage"]]
    potential_action: Optional[List["O365ConnectorCardActionBase"]]
