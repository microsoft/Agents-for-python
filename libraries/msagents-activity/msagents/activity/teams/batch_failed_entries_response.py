# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from .batch_failed_entry import BatchFailedEntry


class BatchFailedEntriesResponse(AgentsModel):
    """
    :param operation_id: Unique identifier of the batch operation.
    :type operation_id: str
    """

    continuation_token: str = None
    failed_entries_responses: list[BatchFailedEntry] = None
