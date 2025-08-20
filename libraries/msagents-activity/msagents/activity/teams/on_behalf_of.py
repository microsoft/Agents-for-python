# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel


class OnBehalfOf(AgentsModel):
    """Specifies the OnBehalfOf entity for meeting notifications.

    :param item_id: The item id of the OnBehalfOf entity.
    :type item_id: str
    :param mention_type: The mention type. Default is "person".
    :type mention_type: str
    :param display_name: The display name of the OnBehalfOf entity.
    :type display_name: str
    :param mri: The MRI of the OnBehalfOf entity.
    :type mri: str
    """

    item_id: str = None
    mention_type: str = None
    display_name: str = None
    mri: str = None
