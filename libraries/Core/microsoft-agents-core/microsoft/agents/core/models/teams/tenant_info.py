# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel


class TenantInfo(AgentsModel):
    """Describes a tenant.

    :param id: Unique identifier representing a tenant
    :type id: str
    """

    id: str = None
