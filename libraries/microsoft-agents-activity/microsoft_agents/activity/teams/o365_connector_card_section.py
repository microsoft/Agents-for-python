# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from .o365_connector_card_fact import O365ConnectorCardFact
from .o365_connector_card_image import O365ConnectorCardImage
from .o365_connector_card_action_base import O365ConnectorCardActionBase


class O365ConnectorCardSection(AgentsModel):
    """O365 connector card section.

    :param title: Title of the section.
    :type title: str | None
    :param text: Text for the section.
    :type text: str | None
    :param activity_title: Activity title.
    :type activity_title: str | None
    :param activity_subtitle: Activity subtitle.
    :type activity_subtitle: str | None
    :param activity_image: Activity image URL.
    :type activity_image: str | None
    :param activity_text: Activity text.
    :type activity_text: str | None
    :param facts: List of facts for the section.
    :type facts: list[O365ConnectorCardFact] | None
    :param images: List of images for the section.
    :type images: list[O365ConnectorCardImage] | None
    :param potential_action: List of actions for the section.
    :type potential_action: list[O365ConnectorCardActionBase] | None
    """

    title: str | None = None
    text: str | None = None
    activity_title: str | None = None
    activity_subtitle: str | None = None
    activity_image: str | None = None
    activity_text: str | None = None
    facts: list[O365ConnectorCardFact] | None = None
    images: list[O365ConnectorCardImage] | None = None
    potential_action: list[O365ConnectorCardActionBase] | None = None
