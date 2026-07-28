# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Teams Message Extensions agent — Python port of the .NET MessageExtensions sample.

Demonstrates the composeExtension (message extension) surface: search-based
queries, item selection, action commands, link unfurling, settings, and a
fetch-task command. Mirrors src/samples/Teams/MessageExtensions from the
microsoft/Agents-for-net repository.
"""

import logging
from os import environ

from dotenv import load_dotenv

from microsoft_teams.api.models import (
    AppBasedLinkQuery,
    CardAction,
    MessagingExtensionAction,
    MessagingExtensionActionResponse,
    MessagingExtensionAttachment,
    MessagingExtensionAttachmentLayout,
    MessagingExtensionQuery,
    MessagingExtensionResponse,
    MessagingExtensionResult,
    MessagingExtensionResultType,
    MessagingExtensionSuggestedAction,
)

from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import (
    AgentApplication,
    Authorization,
    MemoryStorage,
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

# URL exposed by the agent (dev tunnel / public host) used by the settings command.
SETTINGS_URL = environ.get("SETTINGS_URL", "http://localhost:3978/settings")

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

_ADAPTIVE_CONTENT_TYPE = "application/vnd.microsoft.card.adaptive"
_THUMBNAIL_CONTENT_TYPE = "application/vnd.microsoft.card.thumbnail"


def _adaptive_card(title: str, body_text: str) -> dict:
    """Build a minimal Adaptive Card with a bold title and a wrapped body line."""
    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            {"type": "TextBlock", "text": title, "weight": "Bolder", "size": "Large"},
            {"type": "TextBlock", "text": body_text, "wrap": True, "isSubtle": True},
        ],
    }


def _thumbnail(title: str, text: str, tap_value: dict) -> dict:
    """Build a thumbnail-card preview whose tap fires a selectItem invoke."""
    return {
        "title": title,
        "text": text,
        "tap": {"type": "invoke", "value": tap_value},
    }


def _list_result(
    *attachments: MessagingExtensionAttachment,
) -> MessagingExtensionResponse:
    """Wrap attachments in a list-layout composeExtension result."""
    return MessagingExtensionResponse(
        compose_extension=MessagingExtensionResult(
            type=MessagingExtensionResultType.RESULT,
            attachment_layout=MessagingExtensionAttachmentLayout.LIST,
            attachments=list(attachments),
        )
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
                        type="openUrl",
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
) -> None:
    if settings.state == "CancelledByUser":
        return
    logger.info("Settings saved: %s", settings.state)


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
    return MessagingExtensionActionResponse.model_validate(
        {
            "task": {
                "type": "continue",
                "value": {
                    "title": "Conversation Members",
                    "height": "small",
                    "width": "small",
                    "card": {
                        "contentType": _ADAPTIVE_CONTENT_TYPE,
                        "content": card,
                    },
                },
            }
        }
    )
