# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel


class TabSubmitData(AgentsModel):
    """Invoke ('tab/submit') request value payload data.

    :param type: Currently, 'tab/submit'.
    :type type: str
    :param properties: Gets or sets properties that are not otherwise defined by the TabSubmit
     type but that might appear in the serialized REST JSON object.
    :type properties: object
    """

    type: str = None
    properties: object = None
