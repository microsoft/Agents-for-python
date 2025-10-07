# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Protocol, Optional
from abc import abstractmethod

from microsoft_agents.hosting.core.authorization import ClaimsIdentity
from microsoft_agents.hosting.core.connector import (
    ConnectorClientBase,
    UserTokenClientBase,
)
from microsoft_agents.hosting.core.turn_context import TurnContext


class ChannelServiceClientFactoryBase(Protocol):
    @abstractmethod
    async def create_connector_client(
        self,
        context: TurnContext,
        claims_identity: ClaimsIdentity,
        service_url: str,
        audience: str,
        scopes: Optional[list[str]] = None,
        use_anonymous: bool = False,
    ) -> ConnectorClientBase:
        """
        Creates the appropriate ConnectorClientBase instance.

        :param claims_identity: The inbound Activity's ClaimsIdentity.
        :param service_url: The service URL.
        :param audience: The audience.
        :param scopes: The scopes to request.
        :param use_anonymous: Whether to use anonymous credentials.
        :return: A ConnectorClientBase instance.
        """
        pass

    @abstractmethod
    async def create_user_token_client(
        self,
        context: TurnContext,
        claims_identity: ClaimsIdentity,
        use_anonymous: bool = False,
    ) -> UserTokenClientBase:
        """
        Creates the appropriate UserTokenClientBase instance.

        :param claims_identity: The inbound Activity's ClaimsIdentity.
        :param use_anonymous: Whether to use anonymous credentials.
        :return: Asynchronous Task with UserTokenClientBase instance.
        """
        pass
