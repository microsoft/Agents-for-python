# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel


class BatchOperationResponse(AgentsModel):
    """
    :param operation_id: Unique identifier of the batch operation.
    :type operation_id: str
    """

    operation_id: str = None
