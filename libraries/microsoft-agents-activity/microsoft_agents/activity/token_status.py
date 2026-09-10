# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Models for token status operations."""

from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class TokenStatus(AgentsModel):
    """
    The status of a user token.

    :param channel_id: The channelId of the token status pertains to.
    :type channel_id: str | None
    :param connection_name: The name of the connection the token status pertains to.
    :type connection_name: str | None
    :param has_token: True if a token is stored for this ConnectionName.
    :type has_token: bool | None
    :param service_provider_display_name: The display name of the service provider for which this Token belongs to.
    :type service_provider_display_name: str | None
    """

    channel_id: NonEmptyString | None = None
    connection_name: NonEmptyString | None = None
    has_token: bool | None = None
    service_provider_display_name: NonEmptyString | None = None
