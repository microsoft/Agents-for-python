# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Sender - Abstract interface for sending activities to agents.

Defines the protocol for sending activities and receiving responses,
which can be implemented for different HTTP clients or protocols.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from microsoft_agents.activity import Activity

from .transcript import Transcript, Exchange


class Sender(ABC):
    """Abstract client for sending activities to an agent endpoint.
    
    Implementations handle the HTTP communication and response parsing,
    returning Exchange objects that capture the full request-response cycle.
    """

    @abstractmethod
    async def send(self, activity: Activity, transcript: Transcript | None = None, **kwargs) -> Exchange:
        """Send an activity and return the Exchange containing the response.
        
        :param activity: The Activity to send.
        :param transcript: Optional Transcript to record the exchange.
        :param timeout: Optional timeout for the request.
        :return: An Exchange object containing the response.
        """
        ...