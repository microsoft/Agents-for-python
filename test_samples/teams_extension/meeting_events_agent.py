# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""
Teams meeting events sample.

Demonstrates the meeting routes on TeamsAgentExtension using the Teams SDK
MeetingDetails model. In the Teams SDK a single MeetingDetails type is used
for both meeting-start and meeting-end events (replacing the prior
MeetingStartEventDetails / MeetingEndEventDetails split).

Also wires read-receipt and participant join/leave handlers, which keep
the legacy ReadReceiptInfo / MeetingParticipantsEventDetails models from
microsoft_agents.activity.teams (no Teams SDK equivalents).
"""

import logging
from os import environ, path
from dotenv import load_dotenv

from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.activity.teams import (
    MeetingParticipantsEventDetails,
    ReadReceiptInfo,
)
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import (
    AgentApplication,
    MemoryStorage,
    TurnContext,
    TurnState,
)
from microsoft_agents.hosting.core.app.oauth.authorization import Authorization
from microsoft_agents.hosting.teams import TeamsAgentExtension
from microsoft_teams.api.models import MeetingDetails

from shared import start_server

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

load_dotenv(path.join(path.dirname(__file__), ".env"))
agents_sdk_config = load_configuration_from_env(environ)

STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)

AGENT_APP = AgentApplication[TurnState](
    storage=STORAGE,
    adapter=ADAPTER,
    authorization=AUTHORIZATION,
    **agents_sdk_config,
)
TEAMS = TeamsAgentExtension[TurnState](AGENT_APP)


@AGENT_APP.activity("message")
async def on_message(context: TurnContext, _state: TurnState):
    await context.send_activity(
        "This sample listens for Teams meeting lifecycle events. "
        "Install it in a meeting context to see start, end, join, leave, and read receipts."
    )


@TEAMS.meeting.on_start
async def on_meeting_start(
    context: TurnContext, _state: TurnState, meeting: MeetingDetails
):
    title = meeting.title or "Untitled meeting"
    await context.send_activity(
        f"Meeting started: {title} (id={meeting.id}, start={meeting.scheduled_start_time})"
    )


@TEAMS.meeting.on_end
async def on_meeting_end(
    context: TurnContext, _state: TurnState, meeting: MeetingDetails
):
    title = meeting.title or "Untitled meeting"
    await context.send_activity(
        f"Meeting ended: {title} (id={meeting.id}, end={meeting.scheduled_end_time})"
    )


@TEAMS.meeting.on_participants_join
async def on_participants_join(
    context: TurnContext, _state: TurnState, details: MeetingParticipantsEventDetails
):
    members = details.members or []
    log.info("Participants joined: %d", len(members))


@TEAMS.meeting.on_participants_leave
async def on_participants_leave(
    context: TurnContext, _state: TurnState, details: MeetingParticipantsEventDetails
):
    members = details.members or []
    log.info("Participants left: %d", len(members))


@TEAMS.on_read_receipt
async def on_read_receipt(
    context: TurnContext, _state: TurnState, receipt: ReadReceiptInfo
):
    log.info("Read receipt: lastReadMessageId=%s", receipt.last_read_message_id)


if __name__ == "__main__":
    start_server(
        agent_application=AGENT_APP,
        auth_configuration=CONNECTION_MANAGER.get_default_connection_configuration(),
    )
