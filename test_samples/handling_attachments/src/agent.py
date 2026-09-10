# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dotenv import load_dotenv

from pathlib import Path

import os
import base64

from microsoft_agents.activity import (
    Activity,
    ActionTypes,
    Attachment,
    AttachmentData,
    CardAction,
    Channels,
    HeroCard,
)

from microsoft_agents.hosting.core import (
    Authorization,
    AgentApplication,
    TurnState,
    TurnContext,
    MemoryStorage,
    MessageFactory,
    ConnectorClientBase,
)
from microsoft_agents.hosting.core.app.attachment_downloader import (
    AttachmentDownloader,
)
from microsoft_agents.hosting.core.app.m365_attachment_downloader import (
    M365AttachmentDownloader,
)
from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.fastapi import CloudAdapter


# Create the agent application

load_dotenv()

agents_sdk_config = load_configuration_from_env(os.environ)

STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)

AGENT_APP = AgentApplication[TurnState](
    storage=STORAGE,
    adapter=ADAPTER,
    authorization=AUTHORIZATION,
    file_downloaders=[
        AttachmentDownloader(),
        M365AttachmentDownloader(connections=CONNECTION_MANAGER),
    ],
    **agents_sdk_config,
)


# Agent handlers
async def _help(context: TurnContext, _state: TurnState):
    for member in context.activity.members_added:
        if member.id != context.activity.recipient.id:
            await context.send_activity(
                "Welcome to the HandlingAttachments Agent." +
                "This agent will introduce you to attachments." +
                "Please select an option."
            )
            await display_options(context)

AGENT_APP.conversation_update("membersAdded")(_help)
AGENT_APP.message("/help")(_help)


@AGENT_APP.activity("message")
async def on_message(context: TurnContext, state: TurnState):
    reply = await process_input(context, state)
    if reply is not None:
        await context.send_activity(reply)
    await display_options(context)

async def display_options(context: TurnContext) -> None:
    card = HeroCard(
        text="You can upload an image or select one of the following choices",
        buttons=[
            CardAction(
                type=ActionTypes.im_back,
                title="1. Inline Attachment",
                value="1"
            ),
            CardAction(
                type=ActionTypes.im_back,
                title="2. Internet Attachment",
                value="2"
            )
        ]
    )

    if context.activity.channel_id == Channels.ms_teams:
        card.buttons.append(
            CardAction(
                type=ActionTypes.im_back,
                title="3. Upload Attachment",
                value="3"
            )
        )

    reply = MessageFactory.attachment(card.to_attachment())
    await context.send_activity(reply)

async def process_input(context: TurnContext, state: TurnState) -> Activity | None:

    reply: Activity | None = None

    if state.temp.input_files:
        reply = MessageFactory.text(f"There are {len(state.temp.input_files)} attachments.")
        image_data = base64.b64encode(state.temp.input_files[0].content).decode(
            "utf-8"
        )
        reply.attachments = [
            Attachment(
                name=state.temp.input_files[0].filename,
                content_type="image/png",
                content_url=f"data:image/png;base64,{image_data}"
            )
        ]
    else:
        reply = await handle_outgoing_attachment(context, context.activity)

    return reply

async def handle_outgoing_attachment(context: TurnContext, activity: Activity) -> Activity | None:
    if not activity.text:
        return None

    reply: Activity | None = None

    if activity.text.startswith("1"):
        reply = MessageFactory.text("This is an inline attachment.")
        reply.attachments = [get_inline_attachment()]
    elif activity.text.startswith("2"):
        reply = MessageFactory.text("This is an attachment from an HTTP URL.")
        reply.attachments = [get_internet_attachment()]
    elif activity.text.startswith("3"):
        reply = MessageFactory.text("This is an uploaded attachment.")
        uploaded_attachment = await upload_attachment(context, activity.service_url, activity.conversation.id)
        reply.attachments = [uploaded_attachment]
    return reply

def get_inline_attachment() -> Attachment:
    image_path = Path(os.getcwd()) / "resources" / "build-agents.png"
    image_data = base64.b64encode(image_path.read_bytes()).decode("utf-8")

    return Attachment(
        name="resources\\build-agents.png",
        content_type="image/png",
        content_url=f"data:image/png;base64,{image_data}"
    )

async def upload_attachment(context: TurnContext, service_url: str, conversation_id: str) -> Attachment:
    if not service_url:
        raise ValueError("Service URL is required.")
    if not conversation_id:
        raise ValueError("Conversation ID is required.")

    image_path = Path(os.getcwd()) / "resources" / "agents-sdk.png"

    connector = context.services.get(ConnectorClientBase)
    if not connector:
        raise RuntimeError("Connector client is required.")

    response = await connector.conversations.upload_attachment(
        conversation_id,
        AttachmentData(
            name="resources\\agents-sdk.png",
            type="image/png",
            original_base64=image_path.read_bytes()
        )
    )

    attachment_uri = connector.attachments.get_attachment_uri(response.id)

    return Attachment(
        name="resources\\agents-sdk.png",
        content_type="image/png",
        content_url=attachment_uri,
    )

def get_internet_attachment() -> Attachment:
    return Attachment(
        name="resources\\introducing-agents-sdk.png",
        content_type="image/png",
        content_url="https://devblogs.microsoft.com/microsoft365dev/wp-content/uploads/sites/73/2024/11/word-image-23435-1.png"
    )