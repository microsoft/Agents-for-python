# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel


class O365ConnectorCardActionQuery(AgentsModel):
    """O365 connector card action query.

    :param body: Body of the action query.
    :type body: str
    """

    body: str = None
    action_id: str = None
