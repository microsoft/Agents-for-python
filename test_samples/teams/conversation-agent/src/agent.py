# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Teams Conversation Agent — Python port of the .NET ConversationAgent sample.

Demonstrates Teams-specific events: channel lifecycle, team lifecycle, member
add/remove, and message commands (update card, who am I, mention, proactive
message-all, targeted send, etc.).
"""

import json
import logging
from os import environ, path

from dotenv import load_dotenv

from microsoft_teams.api.models import ChannelData

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
    MessageFactory,
    MemoryStorage,
    TurnContext,
    TurnState,
)
from microsoft_agents.hosting.teams import TeamsAgentExtension, TeamsInfo
from microsoft_agents.hosting.teams.teams_turn_context import TeamsTurnContext

logging.basicConfig(level=logging.INFO)
load_dotenv()

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

teams = TeamsAgentExtension[TurnState](AGENT_APP)


def _make_welcome_card(title: str, count: int = 0) -> HeroCard:
    return HeroCard(
        title=title,
        buttons=[
            CardAction(type=ActionTypes.message_back, title="Message all members", text="messageall"),
            CardAction(type=ActionTypes.message_back, title="Who am I?", text="whoami"),
            CardAction(type=ActionTypes.message_back, title="Mention Me", text="mentionme"),
            CardAction(type=ActionTypes.message_back, title="Delete Card", text="delete"),
            CardAction(type=ActionTypes.message_back, title="Send Targeted", text="targeted"),
            CardAction(
                type=ActionTypes.message_back,
                title="Update Card",
                text="update",
                value=json.dumps({"count": count}),
            ),
        ],
    )


# ── Installation update ──────────────────────────────────────────────────────

@teams.activity("installationUpdate")
async def on_installation_update(context: TeamsTurnContext, state: TurnState) -> None:
    conv = context.activity.conversation
    if conv and conv.conversation_type == "channel":
        name = conv.name or "this channel"
        await context.send_activity(
            f"Welcome to Microsoft Teams conversationUpdate events demo. "
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
    for member in context.activity.members_added or []:
        if member.id != context.activity.recipient.id:
            if not conv or conv.conversation_type != "personal":
                await context.send_activity(
                    MessageFactory.text(f"Welcome to the team {member.name}.")
                )


@teams.conversation_update("membersRemoved")
async def on_members_removed(context: TeamsTurnContext, state: TurnState) -> None:
    channel_data = context.activity.channel_data
    team_name = "the team"
    if isinstance(channel_data, dict):
        team_name = (channel_data.get("team") or {}).get("name", team_name)

    for member in context.activity.members_removed or []:
        if member.id == context.activity.recipient.id:
            pass  # bot removed — clear any cached data here if needed
        else:
            card = HeroCard(text=f"{member.name} was removed from {team_name}")
            await context.send_activity(
                MessageFactory.attachment(CardFactory.hero_card(card))
            )


# ── Channel events ───────────────────────────────────────────────────────────

@teams.channels.created
async def on_channel_created(context: TeamsTurnContext, state: TurnState, channel_data: ChannelData) -> None:
    name = channel_data.channel.name if channel_data.channel else "Unknown"
    card = HeroCard(text=f"{name} is the Channel created")
    await context.send_activity(MessageFactory.attachment(CardFactory.hero_card(card)))


@teams.channels.renamed
async def on_channel_renamed(context: TeamsTurnContext, state: TurnState, channel_data: ChannelData) -> None:
    name = channel_data.channel.name if channel_data.channel else "Unknown"
    card = HeroCard(text=f"{name} is the new Channel name")
    await context.send_activity(MessageFactory.attachment(CardFactory.hero_card(card)))


@teams.channels.deleted()
async def on_channel_deleted(context: TeamsTurnContext, state: TurnState, channel_data) -> None:
    name = channel_data.channel.name if channel_data.channel else "Unknown"
    card = HeroCard(text=f"{name} is the Channel deleted")
    await context.send_activity(MessageFactory.attachment(CardFactory.hero_card(card)))


# ── Team events ──────────────────────────────────────────────────────────────

@teams.teams.renamed()
async def on_team_renamed(context: TeamsTurnContext, state: TurnState, channel_data) -> None:
    name = channel_data.team.name if channel_data.team else "Unknown"
    card = HeroCard(text=f"{name} is the new Team name")
    await context.send_activity(MessageFactory.attachment(CardFactory.hero_card(card)))


# ── Message commands ─────────────────────────────────────────────────────────

@teams.message("targeted")
async def on_targeted(context: TeamsTurnContext, state: TurnState) -> None:
    """Send a 1:1 proactive message to every member in the conversation."""
    paged = await TeamsInfo.get_paged_members(context)
    app_id = context.identity.get_app_id() if context.identity else ""
    audience = (
        context.identity.get_token_audience()
        if context.identity
        else "https://api.botframework.com"
    )
    for member in paged.members or []:
        params = ConversationParameters(
            is_group=False,
            members=[ChannelAccount(id=member.id, name=member.name)],
            channel_data={"tenant": {"id": context.activity.conversation.tenant_id}},
            agent=context.activity.recipient,
        )

        async def _send(ctx: TurnContext, _, _name=member.name) -> None:
            await ctx.send_activity(
                f"{_name}, this is a **targeted message** — only you can see this."
            )

        await context.adapter.create_conversation(
            app_id or "",
            Channels.ms_teams,
            context.activity.service_url,
            audience or "https://api.botframework.com",
            params,
            _send,
        )


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

    card = _make_welcome_card("I've been updated", count=count)
    card.text = f"Update count - {count}"

    activity = MessageFactory.attachment(CardFactory.hero_card(card))
    activity.id = context.activity.reply_to_id
    await context.update_activity(activity)


@teams.message("whoami")
async def on_who_am_i(context: TeamsTurnContext, state: TurnState) -> None:
    """Fetch the caller's Teams member profile."""
    try:
        member = await TeamsInfo.get_member(
            context, context.activity.from_property.id
        )
        await context.send_activity(f"You are: {member.name}.")
    except Exception as exc:
        if "MemberNotFoundInConversation" in str(exc):
            await context.send_activity("Member not found.")
        else:
            raise


@teams.message("delete")
async def on_delete_card(context: TeamsTurnContext, state: TurnState) -> None:
    await context.delete_activity(context.activity.reply_to_id)


@teams.message("messageall")
async def on_message_all(context: TeamsTurnContext, state: TurnState) -> None:
    """Proactively send a 1:1 greeting to every team member."""
    app_id = context.identity.get_app_id() if context.identity else ""
    audience = (
        context.identity.get_token_audience()
        if context.identity
        else "https://api.botframework.com"
    )
    continuation_token: str = ""
    while True:
        paged = await TeamsInfo.get_paged_members(
            context, page_size=100, continuation_token=continuation_token
        )
        for member in paged.members or []:
            params = ConversationParameters(
                is_group=False,
                members=[ChannelAccount(id=member.id, name=member.name)],
                channel_data={"tenant": {"id": context.activity.conversation.tenant_id}},
                bot=context.activity.recipient,
            )

            async def _greet(ctx: TurnContext, _, _name=member.name) -> None:
                await ctx.send_activity(f"Hello {_name}. I'm a Teams agent.")

            await context.adapter.create_conversation(
                app_id or "",
                Channels.ms_teams,
                context.activity.service_url,
                audience or "https://api.botframework.com",
                params,
                _greet,
            )
        continuation_token = paged.continuation_token
        if not continuation_token:
            break

    await context.send_activity("All messages have been sent.")


@teams.message("mentionme")
async def on_mention_me(context: TeamsTurnContext, state: TurnState) -> None:
    """Mention the sender by name in the reply."""
    try:
        member = await TeamsInfo.get_member(
            context, context.activity.from_property.id
        )
    except Exception as exc:
        if "MemberNotFoundInConversation" in str(exc):
            await context.send_activity("Member not found.")
            return
        raise

    mention = Mention(
        mentioned=context.activity.from_property,
        text=f"<at>{member.name}</at>",
    )
    reply = MessageFactory.text(f"Hello {mention.text}.")
    reply.entities = [mention]
    await context.send_activity(reply)


@teams.message("atmention")
async def on_at_mention(context: TeamsTurnContext, state: TurnState) -> None:
    from_account = context.activity.from_property
    mention = Mention(
        mentioned=from_account,
        text=f"<at>{from_account.name}</at>",
    )
    reply = MessageFactory.text(f"Hello {mention.text}.")
    reply.entities = [mention]
    await context.send_activity(reply)


# ── Default message — send the welcome card ──────────────────────────────────

@teams.activity("message")
async def on_message(context: TeamsTurnContext, state: TurnState) -> None:
    card = _make_welcome_card("Welcome!")
    await context.send_activity(
        MessageFactory.attachment(CardFactory.hero_card(card))
    )