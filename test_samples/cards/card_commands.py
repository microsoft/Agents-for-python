# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from collections.abc import Awaitable, Callable
from pathlib import Path

from microsoft_agents.activity import (
    ActionTypes,
    AdaptiveCardCard,
    AnimationCard,
    AudioCard,
    CardAction,
    CardImage,
    ChannelId,
    Channels,
    Fact,
    HeroCard,
    MediaUrl,
    ReceiptCard,
    ReceiptItem,
    ThumbnailCard,
    ThumbnailUrl,
    VideoCard,
)
from microsoft_agents.hosting.core import MessageFactory, TurnContext

_RESOURCES = Path(__file__).parent / "resources"
_AGENT_IMAGE = (
    "https://github.com/microsoft/Agents-for-net/blob/main/"
    "src/images/agent.png?raw=true"
)

CardHandler = Callable[[TurnContext], Awaitable[None]]


def _adaptive_card(resource_name: str) -> AdaptiveCardCard:
    return AdaptiveCardCard(
        content=(_RESOURCES / resource_name).read_text(encoding="utf-8")
    )


async def _send_attachment(context: TurnContext, attachment) -> None:
    await context.send_activity(MessageFactory.attachment(attachment))


async def send_static_submit_card(context: TurnContext) -> None:
    await _send_attachment(
        context,
        _adaptive_card("StaticSearchCard.json").to_attachment(),
    )


async def send_dynamic_search_card(context: TurnContext) -> None:
    await _send_attachment(
        context,
        _adaptive_card("DynamicSearchCard.json").to_attachment(),
    )


async def send_action_execute_card(context: TurnContext) -> None:
    await _send_attachment(
        context,
        _adaptive_card("ActionExecuteWithRefresh.json").to_attachment(),
    )


async def send_hero_card(context: TurnContext) -> None:
    card = HeroCard(
        title="Hero Card",
        text=(
            "Microsoft 365 Agents SDK provides an integrated environment "
            "purpose-built for agent development."
        ),
        images=[CardImage(url=_AGENT_IMAGE)],
        buttons=[
            CardAction(
                type=ActionTypes.open_url,
                title="Agents SDK",
                value="https://learn.microsoft.com/microsoft-365/agents-sdk/",
            ),
            CardAction(
                type=ActionTypes.open_url,
                title="Agents SDK API",
                value=(
                    "https://learn.microsoft.com/python/api/"
                    "?view=m365-agents-sdk"
                ),
            ),
        ],
    )
    await _send_attachment(context, card.to_attachment())


async def send_thumbnail_card(context: TurnContext) -> None:
    card = ThumbnailCard(
        title="Thumbnail Card",
        text=(
            "Microsoft 365 Agents SDK provides an integrated environment "
            "purpose-built for agent development."
        ),
        images=[CardImage(url=_AGENT_IMAGE)],
        buttons=[
            CardAction(
                type=ActionTypes.open_url,
                title="Agents SDK",
                value="https://learn.microsoft.com/microsoft-365/agents-sdk/",
            )
        ],
    )
    await _send_attachment(context, card.to_attachment())


async def send_audio_card(context: TurnContext) -> None:
    card = AudioCard(
        title="I am your father",
        subtitle="Star Wars: Episode V - The Empire Strikes Back",
        text=(
            "A media-card example using an audio clip and an external "
            "information link."
        ),
        image=ThumbnailUrl(
            url=(
                "https://upload.wikimedia.org/wikipedia/en/3/3c/"
                "SW_-_Empire_Strikes_Back.jpg"
            )
        ),
        media=[
            MediaUrl(
                url=(
                    "https://www.mediacollege.com/downloads/sound-effects/"
                    "star-wars/darthvader/darthvader_yourfather.wav"
                )
            )
        ],
        buttons=[
            CardAction(
                type=ActionTypes.open_url,
                title="Read More",
                value=(
                    "https://en.wikipedia.org/wiki/"
                    "The_Empire_Strikes_Back"
                ),
            )
        ],
    )
    await _send_attachment(context, card.to_attachment())


async def send_video_card(context: TurnContext) -> None:
    card = VideoCard(
        title="Big Buck Bunny",
        subtitle="by the Blender Institute",
        text=(
            "Big Buck Bunny is an open-source animated short film created "
            "with Blender."
        ),
        aspect="4:3",
        image=ThumbnailUrl(
            url=(
                "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/"
                "Big_buck_bunny_poster_big.jpg/220px-"
                "Big_buck_bunny_poster_big.jpg"
            )
        ),
        media=[
            MediaUrl(
                url=(
                    "http://download.blender.org/peach/bigbuckbunny_movies/"
                    "BigBuckBunny_320x180.mp4"
                )
            )
        ],
        buttons=[
            CardAction(
                type=ActionTypes.open_url,
                title="Learn More",
                value="https://peach.blender.org/",
            )
        ],
    )
    await _send_attachment(context, card.to_attachment())


async def send_animation_card(context: TurnContext) -> None:
    card = AnimationCard(
        title="Animation Card",
        media=[MediaUrl(url="https://i.giphy.com/Ki55RUbOV5njy.gif")],
        aspect="4:3",
    )
    await _send_attachment(context, card.to_attachment())


async def send_receipt_card(context: TurnContext) -> None:
    card = ReceiptCard(
        title="John Doe",
        facts=[
            Fact(key="Order Number", value="1234"),
            Fact(key="Payment Method", value="VISA 5555-****"),
        ],
        items=[
            ReceiptItem(
                title="Data Transfer",
                price="$ 38.45",
                quantity="368",
                image=CardImage(
                    url=(
                        "https://github.com/amido/azure-vector-icons/raw/"
                        "master/renders/traffic-manager.png"
                    )
                ),
            ),
            ReceiptItem(
                title="App Service",
                price="$ 45.00",
                quantity="720",
                image=CardImage(
                    url=(
                        "https://github.com/amido/azure-vector-icons/raw/"
                        "master/renders/cloud-service.png"
                    )
                ),
            ),
        ],
        tax="$ 7.50",
        total="$ 90.95",
        buttons=[
            CardAction(
                type=ActionTypes.open_url,
                title="More information",
                value="https://azure.microsoft.com/pricing/",
            )
        ],
    )
    await _send_attachment(context, card.to_attachment())


_CARD_COMMANDS: dict[str, CardHandler] = {
    "static_submit": send_static_submit_card,
    "dynamic_search": send_dynamic_search_card,
    "action_execute": send_action_execute_card,
    "hero": send_hero_card,
    "thumbnail": send_thumbnail_card,
    "audio": send_audio_card,
    "video": send_video_card,
    "animation": send_animation_card,
    "receipt": send_receipt_card,
}


async def send_card_commands(context: TurnContext) -> None:
    card = HeroCard(
        title="Types of cards",
        buttons=[
            CardAction(
                type=ActionTypes.im_back,
                title=command,
                value=command,
            )
            for command in _CARD_COMMANDS
        ],
    )
    await _send_attachment(context, card.to_attachment())


async def handle_card_command(context: TurnContext) -> bool:
    command = (context.activity.text or "").strip().lower()
    handler = _CARD_COMMANDS.get(command)
    if handler is None:
        await send_card_commands(context)
        return False

    if (
        command in {"dynamic_search", "action_execute"}
        and ChannelId.get_channel(context.activity.channel_id) != Channels.ms_teams
    ):
        await context.send_activity(f"Only Teams supports `{command}`.")
        return True

    await handler(context)
    return True
