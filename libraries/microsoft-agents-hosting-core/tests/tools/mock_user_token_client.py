# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Callable, List, Optional, Awaitable
from collections import deque

from microsoft.agents.hosting.core.authorization import ClaimsIdentity
from microsoft.agents.activity import (
    Activity,
    ActivityTypes,
    ChannelAccount,
    ConversationAccount,
    ConversationReference,
    Channels,
    ResourceResponse,
    RoleTypes,
    InvokeResponse,
)
from microsoft.agents.hosting.core.channel_adapter import ChannelAdapter
from microsoft.agents.hosting.core.turn_context import TurnContext
from microsoft.agents.hosting.core.connector import UserTokenClient

AgentCallbackHandler = Callable[[TurnContext], Awaitable]


# patch userTokenclient constructor
class MockUserTokenClient(UserTokenClient):
    """A mock user token client for testing."""

    def __init__(self, ...):
        self._store = {}
        self._exchange_store = {}
        self._throw_on_exchange = {}
        self._user_token = mocker.Mock()
        self._agent_sign_in = mocker.Mock()

    def add_user_token(
        self,
        connection_name: str,
        channel_id: str,
        user_id: str,
        token: str,
        magic_code: str = None,
    ):
        """Add a token for a user that can be retrieved during testing."""
        key = self._get_key(connection_name, channel_id, user_id)
        self._store[key] = (token, magic_code)

    def add_exchangeable_token(
        self,
        connection_name: str,
        channel_id: str,
        user_id: str,
        exchangeable_item: str,
        token: str,
    ):
        """Add an exchangeable token for a user that can be exchanged during testing."""
        key = self._get_exchange_key(
            connection_name, channel_id, user_id, exchangeable_item
        )
        self._exchange_store[key] = token

    def throw_on_exchange_request(
        self,
        connection_name: str,
        channel_id: str,
        user_id: str,
        exchangeable_item: str,
    ):
        """Add an instruction to throw an exception during exchange requests."""
        key = self._get_exchange_key(
            connection_name, channel_id, user_id, exchangeable_item
        )
        self._throw_on_exchange[key] = True

    def _get_key(self, connection_name: str, channel_id: str, user_id: str) -> str:
        return f"{connection_name}:{channel_id}:{user_id}"

    def _get_exchange_key(
        self,
        connection_name: str,
        channel_id: str,
        user_id: str,
        exchangeable_item: str,
    ) -> str:
        return f"{connection_name}:{channel_id}:{user_id}:{exchangeable_item}"
