# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from datetime import datetime
from typing import Optional
from ..agents_model import AgentsModel


class BatchOperationStateResponse(AgentsModel):
    """
    :param state: The state of the batch operation.
    :type state: str
    :param status_map: A map of status codes to their counts.
    :type status_map: dict[int, int]
    :param retry_after: The time after which the operation can be retried.
    :type retry_after: datetime
    :param total_entries_count: The total number of entries in the batch operation.
    :type total_entries_count: int
    """

    state: str = None
    status_map: dict[int, int] = None
    retry_after: Optional[datetime] = None
    total_entries_count: int = None
