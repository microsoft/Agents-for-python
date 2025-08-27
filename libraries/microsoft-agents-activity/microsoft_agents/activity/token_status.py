# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Models for token status operations."""

from typing import Optional
from pydantic import Field

from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class TokenStatus(AgentsModel):
    """
    The status of a user token.

    :param channel_id: The channelId of the token status pertains to.
    :type channel_id: str
    :param connection_name: The name of the connection the token status pertains to.
    :type connection_name: str
    :param has_token: True if a token is stored for this ConnectionName.
    :type has_token: bool
    :param service_provider_display_name: The display name of the service provider for which this Token belongs to.
    :type service_provider_display_name: str
    """

    channel_id: Optional[NonEmptyString] = Field(None, alias="channelId")
    connection_name: Optional[NonEmptyString] = Field(None, alias="connectionName")
    has_token: Optional[bool] = Field(None, alias="hasToken")
    service_provider_display_name: Optional[NonEmptyString] = Field(
        None, alias="serviceProviderDisplayName"
    )
