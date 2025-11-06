# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import abstractmethod
from typing import Optional, Protocol

from fastapi import Request, Response

from microsoft_agents.hosting.core import Agent


class AgentHttpAdapter(Protocol):
    @abstractmethod
    async def process(self, request: Request, agent: Agent) -> Optional[Response]:
        raise NotImplementedError()
