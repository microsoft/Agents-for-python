# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""
Targeted-message sample for Teams group chats.

Mirrors the scenario from microsoft/Agents-for-net PR #807:

    public static async Task SendTargetedMessagesAsync(ITurnContext turnContext, ...)
    {
        var members = await api.Conversations.Members.GetAsync(turnContext.Activity.Conversation.Id, ct);
        foreach (var member in members)
        {
            var activity = new Activity
            {
                Type = ActivityTypes.Message,
                Text = $"{member.Name}, this is a **targeted message** — only you can see this.",
                Recipient = new ChannelAccount { Id = member.Id, Name = member.Name, Role = RoleTypes.User },
            };
            await turnContext.SendTargetedActivityAsync(activity, ct);
        }
    }

The Python SDK currently lacks:
  * ActivityTreatment entity + EntityTypes.ActivityTreatment
  * IActivity.IsTargetedActivity / MakeTargetedActivity helpers
  * TurnContext.SendTargetedActivityAsync
  * The apply_conversation_reference exemption that preserves an explicit
    Recipient when the activity is marked targeted.

This sample applies the pattern *without* SDK changes by:
  1. Tagging each outgoing activity with a raw "activityTreatment" Entity whose
     treatment is "targeted" (matches the wire format the .NET PR produces).
  2. Setting the per-member Recipient explicitly.
  3. Bypassing TurnContext.send_activity (which would call
     apply_conversation_reference and overwrite Recipient with the sender of
     the incoming message) by calling adapter.send_activities directly with
     a fully-populated Activity.

Note on Teams routing: the .NET client also appends `?isTargetedActivity=true`
to the POST /v3/conversations/{id}/activities call when the channel is msteams.
The Python connector client does not yet do that, so until that pieces lands
the recipient field is sent but Teams may not honor it as a private send. The
sample is still useful for exercising the apply_conversation_reference shape
and for end-to-end verification once the connector change ships.

Triggers (group chat):
  * "targeted"   — send a private targeted message to every member.
  * "members"    — list the current chat's members (sanity check).
  * anything else — echo.
"""

from __future__ import annotations

import logging
from os import environ, path
from typing import List

from dotenv import load_dotenv

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    ChannelAccount,
    RoleTypes,
    load_configuration_from_env,
)
from microsoft_agents.activity.entity import Entity
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import (
    AgentApplication,
    MemoryStorage,
    TurnContext,
    TurnState,
)
from microsoft_agents.hosting.core.app.oauth.authorization import Authorization
from microsoft_agents.hosting.teams import TeamsAgentExtension, TeamsInfo

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


# Wire shape the .NET PR emits: { "type": "activityTreatment", "treatment": "targeted" }
ACTIVITY_TREATMENT_TYPE = "activityTreatment"
TARGETED_TREATMENT = "targeted"


def _targeted_treatment_entity() -> Entity:
    """Build the ActivityTreatment entity that marks an activity as targeted."""
    return Entity(type=ACTIVITY_TREATMENT_TYPE, treatment=TARGETED_TREATMENT)


def _build_targeted_activity(context: TurnContext, member: ChannelAccount, text: str) -> Activity:
    """Compose an outgoing Activity addressed to a single chat member.

    The activity is fully populated (channel_id, service_url, conversation,
    from_property) so it can be sent through adapter.send_activities without
    relying on TurnContext.apply_conversation_reference — which would otherwise
    overwrite Recipient with the incoming message's sender.
    """
    incoming = context.activity
    return Activity(
        type=ActivityTypes.message,
        text=text,
        channel_id=incoming.channel_id,
        service_url=incoming.service_url,
        conversation=incoming.conversation,
        from_property=incoming.recipient,  # the agent
        recipient=ChannelAccount(id=member.id, name=member.name, role=RoleTypes.user),
        reply_to_id=incoming.id,
        entities=[_targeted_treatment_entity()],
    )


async def _send_targeted_activities(
    context: TurnContext, activities: List[Activity]
) -> None:
    """Send activities directly through the adapter, skipping TurnContext.

    TurnContext.send_activity routes through apply_conversation_reference,
    which copies reference.user into Activity.recipient and erases our
    per-member targeting. The adapter's send_activities passes the activity
    object through to the connector client as-is.
    """
    if not activities:
        return
    await context.adapter.send_activities(context, activities)


@AGENT_APP.message("members")
async def on_list_members(context: TurnContext, _state: TurnState) -> None:
    page = await TeamsInfo.get_paged_members(context)
    members = page.members or []
    if not members:
        await context.send_activity("No members found in this conversation.")
        return

    lines = [f"- **{m.name}** (`{m.id}`)" for m in members]
    await context.send_activity("Members in this chat:\n" + "\n".join(lines))


@AGENT_APP.message("targeted")
async def on_send_targeted(context: TurnContext, _state: TurnState) -> None:
    """Iterate chat members and send each one a private targeted message."""
    page = await TeamsInfo.get_paged_members(context)
    members = page.members or []

    if not members:
        await context.send_activity("No members found — cannot send targeted messages.")
        return

    log.info("Sending targeted messages to %d members", len(members))

    outgoing: List[Activity] = []
    for member in members:
        text = (
            f"{member.name}, this is a **targeted message** — "
            "only you can see this."
        )
        activity = _build_targeted_activity(context, member, text)
        log.info(
            "Built targeted activity: recipient.id=%s recipient.name=%s",
            activity.recipient.id,
            activity.recipient.name,
        )
        outgoing.append(activity)

    await _send_targeted_activities(context, outgoing)

    # Acknowledge in the shared thread so the trigger user knows the fanout ran.
    await context.send_activity(
        f"Dispatched {len(outgoing)} targeted message(s)."
    )


@AGENT_APP.activity("message")
async def on_message(context: TurnContext, _state: TurnState) -> None:
    await context.send_activity(
        f"Echo: {context.activity.text}\n\n"
        "Type **targeted** in a Teams group chat to fan out a private message "
        "to each member, or **members** to list the chat's members."
    )


if __name__ == "__main__":
    start_server(
        agent_application=AGENT_APP,
        auth_configuration=CONNECTION_MANAGER.get_default_connection_configuration(),
    )
