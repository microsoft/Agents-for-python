# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from typing import Optional
from .o365_connector_card_fact import O365ConnectorCardFact
from .o365_connector_card_image import O365ConnectorCardImage
from .o365_connector_card_action_base import O365ConnectorCardActionBase


class O365ConnectorCardSection(AgentsModel):
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
    :type facts: Optional[list["O365ConnectorCardFact"]]
    :param images: List of images for the section.
    :type images: Optional[list["O365ConnectorCardImage"]]
    :param potential_action: List of actions for the section.
    :type potential_action: Optional[list["O365ConnectorCardActionBase"]]
    """

    title: Optional[str] = None
    text: Optional[str] = None
    activity_title: Optional[str] = None
    activity_subtitle: Optional[str] = None
    activity_image: Optional[str] = None
    activity_text: Optional[str] = None
    facts: Optional[list[O365ConnectorCardFact]] = None
    images: Optional[list[O365ConnectorCardImage]] = None
    potential_action: Optional[list[O365ConnectorCardActionBase]] = None
