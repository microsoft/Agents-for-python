# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging

from fastapi import Request, Response

from a2a.server.agent_execution import RequestContext, SimpleRequestContextBuilder
from a2a.server.events.event_queue_v2 import EventQueue


from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    HTTPAuthSecurityScheme,
    SecurityScheme,
)
from a2a.utils.constants import TransportProtocol

from google.protobuf import json_format

from microsoft_agents.hosting.core import (
    Agent,
    ChannelServiceAdapter,
    ClaimsIdentity,
)

from microsoft_agents.hosting.fastapi import CloudAdapter

from .activity import A2AActivity

logger = logging.getLogger(__file__)

class A2AAdapter():

    def __init__(
        self,
        adapter: CloudAdapter,
        *,
        agent_card_name: str | None = None,
        agent_card_description: str | None = None,
        agent_card_version: str | None = None,
    ):
        self._inner = adapter

        self._agent_card_name = agent_card_name or self.__class__.__name__
        self._agent_card_description = agent_card_description or "Agents SDK A2A"
        self._agent_card_version = agent_card_version or "0.0.0"

    async def process(self, request: Request, agent: Agent) -> Response | None:
        return await self.process_json_rpc(request, agent)

    # async def process_json_rpc(self, request: Request, agent: Agent) -> Response | None:
    #     return await A2AJsonRpcProcessor.process_request(

    #     )

    async def process_agent_card(self, request: Request, agent: Agent, path_prefix: str) -> Response:
        agent_card = AgentCard(
            name=self._agent_card_name,
            description=self._agent_card_description,
            version=self._agent_card_version,
            security_schemes={
                "jwt": SecurityScheme(http_auth_security_scheme=HTTPAuthSecurityScheme(scheme="bearer"))
            },
            default_input_modes=["application/json"],
            default_output_modes=["application/json"],
            skills=[],
            capabilities=AgentCapabilities(
                extended_agent_card=True,
                streaming=True,
            ),
            supported_interfaces=[],
        )

        agent_interfaces = []
        if not agent_interfaces:
            agent_card.supported_interfaces.append(
                AgentInterface(
                    protocol_binding=TransportProtocol.JSONRPC,
                    url=f"{request.url.scheme}://{request.url.hostname}{path_prefix}/",
                    protocol_version="1.0",
                )
            )
        else:
            for agent_interface in agent_interfaces:
                if agent_interface.protocol in (TransportProtocol.JSONRPC, TransportProtocol.HTTP_JSON):
                    agent_card.supported_interfaces.append(
                        protocol_binding=agent_interface.protocol,
                        url=f"{request.url.scheme}://{request.url.hostname}{path_prefix}/",
                        protocol_version="1.0",
                    )
                else:
                    logger.info("Unsupported protocol: %s", agent_interface.protocol)

        skills = []
        if skills:
            for skill_info in skills:
                agent_card.skills.append(AgentSkill(
                    id=skill_info.id,
                    name=skill_info.name,
                    description=skill_info.description,
                    tags=skill_info.tags,
                    examples=skill_info.examples,
                    input_modes=skill_info.input_modes,
                    output_modes=skill_info.output_modes,
                ))

        # agent card handler scenario here from .NET...

        logger.debug("Agent card: %s", agent_card)

        return Response(
            content=json_format.MessageToJson(agent_card),
            media_type="application/json",
        )

    def _create_agent_request_context(self, request: Request, agent: Agent, cache: bool = True) -> RequestContext:
        ...

    async def execute_agent_turn(self, request_id: str, identity: ClaimsIdentity, agent: Agent, context: RequestContext, event_queue: EventQueue) -> None:

        if not context.message:
            raise ValueError("Context must have a message.")
        
        activity = A2AActivity.activity_from_message(request_id, context.task_id, context.message)
        