# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from os import environ

from microsoft_teams.api.models import (
    AppBasedLinkQuery,
    CardAction,
    CardActionType,
    MessagingExtensionAction,
    MessagingExtensionActionResponse,
    MessagingExtensionAttachment,
    MessagingExtensionQuery,
    MessagingExtensionResponse,
    MessagingExtensionResult,
    MessagingExtensionResultType,
    MessagingExtensionSuggestedAction,
    TaskModuleContinueResponse,
    CardTaskModuleTaskInfo,
    Attachment as TeamsAttachment,
)

from microsoft_agents.hosting.core import AgentApplication, TurnState, TurnContext
from microsoft_agents.hosting.msteams import TeamsAgentExtension, TeamsTurnContext
from microsoft_agents.hosting.slack import SlackAgentExtension
from microsoft_agents.hosting.slack.api import SlackChannelData

from .setup import storage, authorization, agents_sdk_config, logger
from .utils import _thumbnail, _adaptive_card, _list_result

# URL exposed by the agent (dev tunnel / public host) used by the settings command.
SETTINGS_URL = environ.get("SETTINGS_URL", "http://localhost:3978/settings")
_ADAPTIVE_CONTENT_TYPE = "application/vnd.microsoft.card.adaptive"
_THUMBNAIL_CONTENT_TYPE = "application/vnd.microsoft.card.thumbnail"

agent = AgentApplication[TurnState](
    storage=storage,
    authorization=authorization,
    **agents_sdk_config,
)

teams = TeamsAgentExtension[TurnState](agent)
slack = SlackAgentExtension[TurnState](agent)

# ── Slack routes ─────────────────────────────────────────

@slack.on_message()
async def on_slack_message(context: TurnContext, state: TurnState) -> None:
    channel_data = SlackChannelData.from_activity(context.activity)

    await slack.call(
        context,
        "chat.postMessage",
        {
            "channel": channel_data.channel,
            "text": f"You said: {context.activity.text}",
            "thread_ts": channel_data.thread_ts
        },
        channel_data.api_token or "",
    )

# ── Default message — usage hint ─────────────────────────────────────────────


@teams.activity("message")
async def on_message(context: TeamsTurnContext, state: TurnState) -> None:
    await context.send_activity(
        f"Echo: {context.activity.text}\n\n"
        "This is a message extension sample. Use the message extension commands "
        "in Teams to test the functionality."
    )


# ── composeExtension/query (search command) ──────────────────────────────────


@teams.message_extensions.query("searchQuery")
async def on_search_query(
    context: TeamsTurnContext, state: TurnState, query: MessagingExtensionQuery
) -> MessagingExtensionResponse:
    params = {p.name: p.value for p in (query.parameters or [])}

    if str(params.get("initialRun", "")).lower() == "true":
        return MessagingExtensionResponse(
            compose_extension=MessagingExtensionResult(
                type=MessagingExtensionResultType.MESSAGE,
                text="Enter a search query to see results.",
            )
        )

    search_text = str(params.get("searchQuery", "") or "")
    logger.info("Search query received: %s", search_text)

    attachments = []
    for i in range(1, 6):
        card = _adaptive_card(
            f"Search Result {i}",
            f"Query: '{search_text}' — result description for item {i}.",
        )
        preview = _thumbnail(
            title=f"Result {i}",
            text=f"Preview of result {i} for query '{search_text}'.",
            tap_value={"index": str(i), "query": search_text},
        )
        attachments.append(
            MessagingExtensionAttachment(
                content_type=_ADAPTIVE_CONTENT_TYPE,
                content=card,
                preview=MessagingExtensionAttachment(
                    content_type=_THUMBNAIL_CONTENT_TYPE,
                    content=preview,
                ),
            )
        )

    return _list_result(*attachments)


# ── composeExtension/selectItem (tap on a search result preview) ─────────────


@teams.message_extensions.select_item
async def on_select_item(
    context: TeamsTurnContext, state: TurnState, item
) -> MessagingExtensionResponse:
    item = item or {}
    index = item.get("index", "No Index")
    query = item.get("query", "No Query")
    logger.info("Item selected: index=%s query=%s", index, query)

    card = _adaptive_card(
        "Item Selected",
        f"You selected item {index} for query '{query}'.",
    )
    return _list_result(
        MessagingExtensionAttachment(content_type=_ADAPTIVE_CONTENT_TYPE, content=card)
    )


# ── composeExtension/submitAction ("createCard") ─────────────────────────────


@teams.message_extensions.submit_action("createCard")
async def on_create_card(
    context: TeamsTurnContext, state: TurnState, action: MessagingExtensionAction
) -> MessagingExtensionResponse:
    data = action.data if isinstance(action.data, dict) else {}
    title = data.get("title") or "Default Title"
    description = data.get("description") or "Default Description"
    logger.info("Creating card: title=%s description=%s", title, description)

    card = _adaptive_card(title, description)
    return _list_result(
        MessagingExtensionAttachment(content_type=_ADAPTIVE_CONTENT_TYPE, content=card)
    )


# ── composeExtension/queryLink (link unfurling) ──────────────────────────────


@teams.message_extensions.query_link
async def on_query_link(
    context: TeamsTurnContext, state: TurnState, query: AppBasedLinkQuery
) -> MessagingExtensionResponse:
    """Handle link unfurling queries."""
    
    url = query.url or ""
    logger.info("Link query: %s", url)

    if not url:
        return MessagingExtensionResponse(
            compose_extension=MessagingExtensionResult(
                type=MessagingExtensionResultType.MESSAGE,
                text="No URL provided.",
            )
        )

    card = _adaptive_card("Link Preview", f"URL: {url}")
    return _list_result(
        MessagingExtensionAttachment(
            content_type=_ADAPTIVE_CONTENT_TYPE,
            content=card,
            preview=MessagingExtensionAttachment(
                content_type=_THUMBNAIL_CONTENT_TYPE,
                content=_thumbnail("Link Preview", url, {"url": url}),
            ),
        )
    )


# ── composeExtension/querySettingUrl ─────────────────────────────────────────


@teams.message_extensions.query_setting_url
async def on_query_settings_url(
    context: TeamsTurnContext, state: TurnState, query: MessagingExtensionQuery
) -> MessagingExtensionResponse:
    logger.info("Settings URL requested")
    return MessagingExtensionResponse(
        compose_extension=MessagingExtensionResult(
            type=MessagingExtensionResultType.CONFIG,
            suggested_actions=MessagingExtensionSuggestedAction(
                actions=[
                    CardAction(
                        type=CardActionType.OPEN_URL,
                        title="Configure",
                        value=SETTINGS_URL,
                    )
                ]
            ),
        )
    )


# ── composeExtension/setting (settings applied) ──────────────────────────────


@teams.message_extensions.setting
async def on_configure_settings(
    context: TeamsTurnContext, state: TurnState, settings: MessagingExtensionQuery
) -> MessagingExtensionResponse:
    if not settings.state == "CancelledByUser":
        logger.info("Settings saved: %s", settings.state)
    return MessagingExtensionResponse()


# ── composeExtension/fetchTask ───────────────────────────────────────────────


@teams.message_extensions.fetch_action()
async def on_fetch_task(
    context: TeamsTurnContext, state: TurnState, action: MessagingExtensionAction
) -> MessagingExtensionActionResponse:
    logger.info("FetchTask: command=%s", action.command_id)
    card = _adaptive_card(
        "Conversation Members",
        "Conversation Members is not implemented in this sample.",
    )
    return MessagingExtensionActionResponse(
        task=TaskModuleContinueResponse(
            value=CardTaskModuleTaskInfo(
                title="ConversationMembers",
                height="small",
                width="small",
                card=TeamsAttachment(
                    content_type=_ADAPTIVE_CONTENT_TYPE,
                    content=card,
                )
            )  
        )
    )
