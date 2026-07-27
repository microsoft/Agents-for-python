# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class TokenExchangeRequest(AgentsModel):
    """TokenExchangeRequest.

    Either the token to exchange or the uri to exchange.

    :param uri: The URI for the exchange request.
    :param token: The token to be exchanged.
    """

    uri: NonEmptyString | None = None
    token: NonEmptyString | None = None
