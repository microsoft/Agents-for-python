# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import ABC, abstractmethod

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    DeliveryModes,
    InvokeResponse,
)

from ..models import SRNode

class Sender(ABC):
    """Client for sending activities to an agent endpoint."""

    @abstractmethod
    async def send(self, activity: Activity) -> SRNode:
        """Send an activity and return the response status and content.
        
        :param activity: The Activity to send.
        :return: A SRNode object containing the response status and content.
        """
        ...