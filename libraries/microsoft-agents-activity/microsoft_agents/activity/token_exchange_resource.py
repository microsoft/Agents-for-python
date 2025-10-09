# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .agents_model import AgentsModel

from ._type_aliases import NonEmptyString


class TokenExchangeResource(AgentsModel):
    """
    A type containing information for token exchange.
    """

    id: NonEmptyString = None
    uri: NonEmptyString = None
    provider_id: NonEmptyString = None
