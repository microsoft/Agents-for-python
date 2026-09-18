# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass

from a2a.server.events import EventQueue

from microsoft_agents.hosting.core import ClaimsIdentity


@dataclass
class AgentRequestContext:
    request_id: str
    identity: ClaimsIdentity
    event_queue: EventQueue
