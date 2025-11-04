# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Protocol

from fastapi import Request, Response

from microsoft_agents.hosting.core import AgentHttpAdapterProtocol


class AgentHttpAdapter(AgentHttpAdapterProtocol[Request, Response], Protocol):
    """Framework specific alias for the shared AgentHttpAdapter protocol."""
