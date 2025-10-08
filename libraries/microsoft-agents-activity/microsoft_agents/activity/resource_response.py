# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class ResourceResponse(AgentsModel):
    """A response containing a resource ID.

    :param id: Id of the resource
    :type id: str
    """

    id: NonEmptyString = None
