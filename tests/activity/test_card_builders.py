# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import pytest
from microsoft_agents.activity import (
    ActionTypes,
    AdaptiveCardCard,
    AnimationCard,
    AudioCard,
    BasicCard,
    CardAction,
    CardImage,
    ContentTypes,
    Fact,
    HeroCard,
    MediaCard,
    MediaUrl,
    ReceiptCard,
    ReceiptItem,
    ThumbnailCard,
    VideoCard,
)


class TestHeroCardBuilders:
    def test_hero_card_fluent_builders(self):
        card = (
            HeroCard(
                title="t",
                subtitle="s",
                text="txt",
                tap=CardAction(type=ActionTypes.open_url, title="tap"),
            )
            .add_image(url="https://img", alt="alt")
            .add_image(CardImage(url="https://img2"))
            .add_button(title="Yes", value="yes")
            .add_button(CardAction(type=ActionTypes.post_back, title="No"))
            .add_buttons(
                CardAction(type=ActionTypes.im_back, title="A"),
                CardAction(type=ActionTypes.im_back, title="B"),
            )
        )

        assert card.title == "t"
        assert card.subtitle == "s"
        assert card.text == "txt"
        assert card.tap.type == ActionTypes.open_url
        assert len(card.images) == 2
        assert card.images[0].url == "https://img"
        assert card.images[0].alt == "alt"
        assert len(card.buttons) == 4
        assert card.buttons[0].title == "Yes"
        assert card.buttons[0].value == "yes"


class TestThumbnailAndBasicCardBuilders:
    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    def test_thumbnail_and_basic_card_builders(self):
        thumb = ThumbnailCard(title="t").add_image(url="u").add_button(title="b")
        assert thumb.title == "t"
        assert len(thumb.images) == 1
        assert len(thumb.buttons) == 1

        basic = (
            BasicCard(text="x")
            .add_image(CardImage(url="u"))
            .add_button(CardAction(type=ActionTypes.im_back, title="b"))
        )
        assert basic.text == "x"
        assert len(basic.images) == 1
        assert len(basic.buttons) == 1


class TestMediaCardBuilders:
    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    def test_media_card_builders_add_media_and_buttons(self):
        animation = (
            AnimationCard(title="a")
            .add_media(url="https://m")
            .add_button(CardAction(type=ActionTypes.im_back, title="b"))
        )
        assert animation.title == "a"
        assert len(animation.media) == 1
        assert animation.media[0].url == "https://m"
        assert len(animation.buttons) == 1

        audio = AudioCard().add_media(MediaUrl(url="https://a"))
        assert len(audio.media) == 1

        video = VideoCard().add_media(url="https://v", profile="profile")
        assert video.media[0].profile == "profile"

        media = MediaCard(text="m").add_media(url="https://x")
        assert media.text == "m"
        assert len(media.media) == 1


class TestReceiptCardBuilders:
    def test_receipt_card_builders(self):
        receipt = (
            ReceiptCard(
                title="r",
                total="$10",
                tax="$1",
                tap=CardAction(type=ActionTypes.open_url, title="tap"),
            )
            .add_fact(Fact(key="key", value="value"))
            .add_item(ReceiptItem(title="item"))
            .add_button(CardAction(type=ActionTypes.im_back, title="b"))
        )

        assert receipt.title == "r"
        assert receipt.total == "$10"
        assert receipt.tax == "$1"
        assert receipt.tap.type == ActionTypes.open_url
        assert len(receipt.facts) == 1
        assert len(receipt.items) == 1
        assert len(receipt.buttons) == 1


class TestAdaptiveCardCardBuilders:
    def test_adaptive_card_card_from_json_to_attachment(self):
        json_content = '{"type":"AdaptiveCard","version":"1.4"}'
        card = AdaptiveCardCard(content=json_content)

        assert card.content == json_content

        attachment = card.to_attachment()
        assert attachment.content_type == ContentTypes.adaptive_card
        assert attachment.content == {"type": "AdaptiveCard", "version": "1.4"}

    def test_adaptive_card_card_serializes_content_as_nested_json(self):
        json_content = '{"type":"AdaptiveCard","version":"1.4"}'
        activity = AdaptiveCardCard(content=json_content).to_message()

        data = activity.model_dump(mode="json", by_alias=True, exclude_none=True)

        # Content is unpacked into nested JSON (an object), not an escaped string.
        assert data["attachments"][0]["content"] == {
            "type": "AdaptiveCard",
            "version": "1.4",
        }
        assert data["attachments"][0]["contentType"] == ContentTypes.adaptive_card
