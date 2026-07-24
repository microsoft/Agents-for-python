# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Teams Conversation Agent — Python port of the .NET ConversationAgent sample.

Demonstrates Teams conversation events and message commands: installation and
channel/team lifecycle events, member add/remove, card update/delete, mentions,
member lookups via the Teams API client, and proactive 1:1 messaging. Mirrors
src/samples/Teams/ConversationAgent from the microsoft/Agents-for-net repository.
"""

import json
import logging
from os import environ
from typing import Optional

from dotenv import load_dotenv

from microsoft_teams.api.models import (
    ChannelData,
    ChannelInfo,
    TeamInfo,
    TeamsChannelAccount,
)

from microsoft_agents.activity import (
    ActionTypes,
    CardAction,
    ChannelAccount,
    Channels,
    ConversationParameters,
    HeroCard,
    Mention,
    load_configuration_from_env,
)
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import (
    AgentApplication,
    Authorization,
    CardFactory,
    MemoryStorage,
    MessageFactory,
    TurnContext,
    TurnState,
)
from microsoft_agents.hosting.core.storage import (
    ConsoleTranscriptLogger,
    TranscriptLoggerMiddleware,
)
from microsoft_agents.hosting.msteams import TeamsAgentExtension
from microsoft_agents.hosting.msteams.teams_turn_context import TeamsTurnContext

logger = logging.getLogger(__name__)
load_dotenv()

agents_sdk_config = load_configuration_from_env(environ)

STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
ADAPTER.use(TranscriptLoggerMiddleware(ConsoleTranscriptLogger()))
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)

AGENT_APP = AgentApplication[TurnState](
    storage=STORAGE,
    adapter=ADAPTER,
    authorization=AUTHORIZATION,
    **agents_sdk_config,
)

teams = TeamsAgentExtension[TurnState](AGENT_APP)

_MEMBER_NOT_FOUND = "MemberNotFoundInConversation"
_DEFAULT_AUDIENCE = "https://api.botframework.com"


def _welcome_card(title: str, count: int = 0) -> HeroCard:
    """Build the demo welcome card with one button per message command."""
    return HeroCard(
        title=title,
        buttons=[
            CardAction(
                type=ActionTypes.message_back,
                title="Message all members",
                text="messageall",
            ),
            CardAction(type=ActionTypes.message_back, title="Who am I?", text="whoami"),
            CardAction(
                type=ActionTypes.message_back, title="Mention Me", text="mentionme"
            ),
            CardAction(
                type=ActionTypes.message_back, title="Delete Card", text="delete"
            ),
            CardAction(
                type=ActionTypes.message_back, title="Send Targeted", text="targeted"
            ),
            CardAction(
                type=ActionTypes.message_back,
                title="Update Card",
                text="update",
                value=json.dumps({"count": count}),
            ),
        ],
    )


def _scope_id(context: TeamsTurnContext) -> str:
    """Return the team id when in a team channel, otherwise the conversation id.

    The Teams member APIs are scoped to a roster; in a team channel that roster
    is keyed by the team id, while in 1:1 / group chats it is the conversation id.
    """
    channel_data = context.activity.channel_data
    if (
        isinstance(channel_data, ChannelData)
        and channel_data.team
        and channel_data.team.id
    ):
        return channel_data.team.id
    return context.activity.conversation.id


def _app_id(context: TeamsTurnContext) -> str:
    return context.identity.get_app_id() if context.identity else ""


def _audience(context: TeamsTurnContext) -> str:
    if context.identity:
        return context.identity.get_token_audience() or _DEFAULT_AUDIENCE
    return _DEFAULT_AUDIENCE


async def _get_member(
    context: TeamsTurnContext, member_id: str
) -> Optional[TeamsChannelAccount]:
    """Look up a single member, returning None if not found in the conversation."""
    api = teams.get_teams_api_client(context)
    try:
        return await api.conversations.members(context.activity.conversation.id).get(member_id)
    except Exception as exc:  # noqa: BLE001 - surface only the known "not found" case
        if _MEMBER_NOT_FOUND in str(exc):
            return None
        raise


async def _create_one_on_one(
    context: TeamsTurnContext,
    app_id: str,
    audience: str,
    member: TeamsChannelAccount,
    callback,
) -> None:
    """Create a proactive 1:1 conversation with *member* and run *callback*."""
    tenant_id = (
        context.activity.conversation.tenant_id
        if context.activity.conversation
        else None
    )
    params = ConversationParameters(
        is_group=False,
        members=[ChannelAccount(id=member.id, name=member.name)],
        tenant_id=tenant_id,
        agent=context.activity.recipient,
    )
    await context.adapter.create_conversation(
        app_id,
        Channels.ms_teams,
        context.activity.service_url,
        audience,
        params,
        callback,
    )


# ── Installation update ──────────────────────────────────────────────────────


@teams.activity("installationUpdate")
async def on_installation_update(context: TeamsTurnContext, state: TurnState) -> None:
    conv = context.activity.conversation
    if conv and conv.conversation_type == "channel":
        name = conv.name or "this channel"
        await context.send_activity(
            "Welcome to Microsoft Teams conversationUpdate events demo. "
            f"This agent is configured in {name}"
        )
    else:
        await context.send_activity(
            "Welcome to Microsoft Teams conversationUpdate events demo."
        )


# ── Member lifecycle ─────────────────────────────────────────────────────────


@teams.conversation_update("membersAdded")
async def on_members_added(context: TeamsTurnContext, state: TurnState) -> None:
    conv = context.activity.conversation
    recipient_id = context.activity.recipient.id if context.activity.recipient else None
    for member in context.activity.members_added or []:
        if member.id != recipient_id and (
            not conv or conv.conversation_type != "personal"
        ):
            await context.send_activity(
                MessageFactory.text(f"Welcome to the team {member.name}.")
            )


@teams.conversation_update("membersRemoved")
async def on_members_removed(context: TeamsTurnContext, state: TurnState) -> None:
    channel_data = context.activity.channel_data
    team_name = "the team"
    if (
        isinstance(channel_data, ChannelData)
        and channel_data.team
        and channel_data.team.name
    ):
        team_name = channel_data.team.name

    recipient_id = context.activity.recipient.id if context.activity.recipient else None
    for member in context.activity.members_removed or []:
        if member.id == recipient_id:
            # The agent itself was removed — clear any cached team data here.
            continue
        card = HeroCard(text=f"{member.name} was removed from {team_name}")
        await context.send_activity(
            MessageFactory.attachment(CardFactory.hero_card(card))
        )


# ── Channel events ───────────────────────────────────────────────────────────


@teams.channels.created
async def on_channel_created(
    context: TeamsTurnContext, state: TurnState, channel_info: ChannelInfo
) -> None:
    name = channel_info.name or "Unknown"
    card = HeroCard(text=f"{name} is the Channel created")
    await context.send_activity(MessageFactory.attachment(CardFactory.hero_card(card)))


@teams.channels.renamed
async def on_channel_renamed(
    context: TeamsTurnContext, state: TurnState, channel_info: ChannelInfo
) -> None:
    name = channel_info.name or "Unknown"
    card = HeroCard(text=f"{name} is the new Channel name")
    await context.send_activity(MessageFactory.attachment(CardFactory.hero_card(card)))


@teams.channels.deleted
async def on_channel_deleted(
    context: TeamsTurnContext, state: TurnState, channel_info: ChannelInfo
) -> None:
    name = channel_info.name or "Unknown"
    card = HeroCard(text=f"{name} is the Channel deleted")
    await context.send_activity(MessageFactory.attachment(CardFactory.hero_card(card)))


# ── Team events ──────────────────────────────────────────────────────────────


@teams.teams.renamed
async def on_team_renamed(
    context: TeamsTurnContext, state: TurnState, team_info: TeamInfo
) -> None:
    name = team_info.name or "Unknown"
    card = HeroCard(text=f"{name} is the new Team name")
    await context.send_activity(MessageFactory.attachment(CardFactory.hero_card(card)))


# ── Message commands ─────────────────────────────────────────────────────────


@teams.message("targeted")
async def on_targeted(context: TeamsTurnContext, state: TurnState) -> None:
    """Send a 1:1 message to every member of the current conversation."""
    app_id = _app_id(context)
    audience = _audience(context)
    continuation_token: Optional[str] = None
    while True:
        paged = await teams.get_teams_api_client(
            context
        ).conversations.members(context.activity.conversation.id).get_paged(
            100, continuation_token
        )
        for member in paged.members or []:

            async def _send(ctx: TurnContext, _name=member.name) -> None:
                await ctx.send_activity(
                    f"{_name}, this is a **targeted message** — only you can see this."
                )

            await _create_one_on_one(context, app_id, audience, member, _send)

        continuation_token = paged.continuation_token
        if not continuation_token:
            break


@teams.message("update")
async def on_update_card(context: TeamsTurnContext, state: TurnState) -> None:
    """Update the card that triggered this message with an incremented counter."""
    value = context.activity.value
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            value = {}
    count = (int(value.get("count") or 0) + 1) if isinstance(value, dict) else 1

    card = _welcome_card("I've been updated", count=count)
    card.text = f"Update count - {count}"

    activity = MessageFactory.attachment(CardFactory.hero_card(card))
    activity.id = context.activity.reply_to_id
    await context.update_activity(activity)


@teams.message("whoami")
async def on_who_am_i(context: TeamsTurnContext, state: TurnState) -> None:
    """Fetch and report the caller's Teams member profile."""
    member = await _get_member(context, context.activity.from_property.id)
    if member is None:
        await context.send_activity("Member not found.")
        return
    await context.send_activity(f"You are: {member.name}.")


@teams.message("delete")
async def on_delete_card(context: TeamsTurnContext, state: TurnState) -> None:
    await context.delete_activity(context.activity.reply_to_id)


@teams.message("messageall")
async def on_message_all(context: TeamsTurnContext, state: TurnState) -> None:
    """Proactively send a 1:1 greeting to every member of the team."""
    app_id = _app_id(context)
    audience = _audience(context)
    continuation_token: Optional[str] = None
    while True:
        paged = await teams.get_teams_api_client(
            context
        ).conversations.members(context.activity.conversation.id).get_paged(100, continuation_token)
        for member in paged.members or []:

            async def _greet(ctx: TurnContext, _name=member.name) -> None:
                await ctx.send_activity(f"Hello {_name}. I'm a Teams agent.")

            await _create_one_on_one(context, app_id, audience, member, _greet)

        continuation_token = paged.continuation_token
        if not continuation_token:
            break

    await context.send_activity("All messages have been sent.")


@teams.message("mentionme")
async def on_mention_me(context: TeamsTurnContext, state: TurnState) -> None:
    """Reply with an Adaptive Card that @-mentions the caller (UPN and AAD)."""
    member = await _get_member(context, context.activity.from_property.id)
    if member is None:
        await context.send_activity("Member not found.")
        return

    card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            {
                "type": "TextBlock",
                "text": f"Mention by UPN: Hello <at>{member.name} UPN</at>",
            },
            {
                "type": "TextBlock",
                "text": f"Mention by AAD Object Id: Hello <at>{member.name} AAD</at>",
            },
        ],
        "msteams": {
            "entities": [
                {
                    "type": "mention",
                    "text": f"<at>{member.name} UPN</at>",
                    "mentioned": {"id": member.id, "name": member.name},
                },
                {
                    "type": "mention",
                    "text": f"<at>{member.name} AAD</at>",
                    "mentioned": {"id": member.aad_object_id, "name": member.name},
                },
            ]
        },
    }
    await context.send_activity(
        MessageFactory.attachment(CardFactory.adaptive_card(card))
    )


@teams.message("atmention")
async def on_at_mention(context: TeamsTurnContext, state: TurnState) -> None:
    """Reply with a text message that @-mentions the caller."""
    from_account = context.activity.from_property
    mention = Mention(mentioned=from_account, text=f"<at>{from_account.name}</at>")
    reply = MessageFactory.text(f"Hello {mention.text}.")
    reply.entities = [mention]
    await context.send_activity(reply)


# ── Default message — send the welcome card ──────────────────────────────────


@teams.activity("message")
async def on_message(context: TeamsTurnContext, state: TurnState) -> None:
    await context.send_activity(
        MessageFactory.attachment(CardFactory.hero_card(_welcome_card("Welcome!")))
    )
