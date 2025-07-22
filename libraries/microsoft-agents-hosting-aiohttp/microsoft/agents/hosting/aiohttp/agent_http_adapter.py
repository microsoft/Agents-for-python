# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import abstractmethod
from typing import Optional, Protocol

from aiohttp.web import (
    Request,
    Response,
)

from microsoft.agents.hosting.core import Agent


class AgentHttpAdapter(Protocol):
    @abstractmethod
    async def process(self, request: Request, agent: Agent) -> Optional[Response]:
        raise NotImplementedError()
