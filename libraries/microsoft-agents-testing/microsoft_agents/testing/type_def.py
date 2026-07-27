# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Awaitable, Callable, TypeVar

from microsoft_agents.hosting.core import TurnContext

T = TypeVar("T")
AgentCallbackHandler = Callable[[TurnContext], Awaitable[T]]
