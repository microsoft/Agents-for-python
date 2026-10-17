# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from a2a.types import AgentInterface, AgentSkill
from a2a.utils.constants import TransportProtocol

from microsoft_agents.hosting.a2a import A2AAdapter

from .agent import AGENT


A2A_ADAPTER = A2AAdapter(
    AGENT,
    agent_card_name="SDK Echo Agent",
    agent_card_description="A simple Microsoft 365 Agents SDK A2A sample.",
    agent_card_version="1.0.0",
    agent_interfaces=[
        AgentInterface(
            url="/a2a",
            protocol_binding=TransportProtocol.JSONRPC,
        )
    ],
    skills=[
        AgentSkill(
            id="echo",
            name="Echo",
            description="Echoes a text message back to the caller.",
            tags=["sample", "echo"],
            examples=["Hello", "Repeat this message"],
            input_modes=["text/plain"],
            output_modes=["text/plain"],
        )
    ],
)