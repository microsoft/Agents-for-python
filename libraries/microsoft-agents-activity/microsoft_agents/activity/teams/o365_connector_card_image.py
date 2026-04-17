# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel


class O365ConnectorCardImage(AgentsModel):
    """O365 connector card image.

    :param image: URL for the image.
    :type image: str
    :param title: Title of the image.
    :type title: str | None
    """

    image: str = None
    title: str | None = None
