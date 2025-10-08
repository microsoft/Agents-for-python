# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .agents_model import AgentsModel

from ._type_aliases import NonEmptyString


class TokenPostResource(AgentsModel):
    """
    A type containing information for token posting.
    """

    sas_url: NonEmptyString = None
