# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel


class O365ConnectorCardFact(AgentsModel):
    """O365 connector card fact.

    :param name: Display name of the fact
    :type name: str
    :param value: Display value for the fact
    :type value: str
    """

    name: str = None
    value: str = None
