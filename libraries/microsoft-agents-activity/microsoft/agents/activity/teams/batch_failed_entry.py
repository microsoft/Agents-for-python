# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel


class BatchFailedEntry(AgentsModel):
    """
    :param id: Unique identifier of the entry in the batch operation.
    :type id: str
    :param error: Error message associated with the entry.
    :type error: str
    """

    id: str = None
    error: str = None
