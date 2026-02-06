# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""StreamCollector - Placeholder for stream-based response collection.

This module is a work-in-progress stub for collecting streamed responses
from agents. The implementation is not yet complete.
"""

from .agent_client import AgentClient


class StreamCollector:
    """Collects streamed responses from an agent.

    This class is a placeholder stub and is not yet implemented.
    """

    def __init__(self, agent_client: AgentClient):
        """Initialize the StreamCollector.

        :param agent_client: The AgentClient to collect stream responses from.
        """
        self._client = agent_client
        self._stream_id = None

    async def send(...):
        """Send a streamed activity. Not yet implemented."""
        pass
    