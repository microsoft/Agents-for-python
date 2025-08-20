# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .batch_operation_response import BatchOperationResponse


class TeamsBatchOperationResponse(BatchOperationResponse):
    """
    :param operation_id: Unique identifier of the batch operation.
    :type operation_id: str
    :param body_as_text: The body of the request as text.
    :type body_as_text: str
    :param parsed_body: The parsed body of the request.
    :type parsed_body: BatchOperationResponse
    """

    operation_id: str = None
    body_as_text: str = None
    parsed_body: BatchOperationResponse = None
