# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import overload

from .attachment import Attachment
from .card import Card
from .content_types import ContentTypes
from .thumbnail_url import ThumbnailUrl
from .media_url import MediaUrl
from .card_action import CardAction
from ._model_utils import pick_model
from ._type_aliases import NonEmptyString


class AudioCard(Card):
    """Audio card.

    :param title: Title of this card
    :type title: str
    :param subtitle: Subtitle of this card
    :type subtitle: str
    :param text: Text of this card
    :type text: str
    :param image: Thumbnail placeholder
    :type image: ~microsoft_agents.activity.ThumbnailUrl
    :param media: Media URLs for this card. When this field contains more than
     one URL, each URL is an alternative format of the same content.
    :type media: list[~microsoft_agents.activity.MediaUrl]
    :param buttons: Actions on this card
    :type buttons: list[~microsoft_agents.activity.CardAction]
    :param shareable: This content may be shared with others (default:true)
    :type shareable: bool
    :param autoloop: Should the client loop playback at end of content
     (default:true)
    :type autoloop: bool
    :param autostart: Should the client automatically start playback of media
     in this card (default:true)
    :type autostart: bool
    :param aspect: Aspect ratio of thumbnail/media placeholder. Allowed values
     are "16:9" and "4:3"
    :type aspect: str
    :param duration: Describes the length of the media content without
     requiring a receiver to open the content. Formatted as an ISO 8601
     Duration field.
    :type duration: str
    :param value: Supplementary parameter for this card
    :type value: object
    """

    title: NonEmptyString = None
    subtitle: NonEmptyString = None
    text: str = None
    image: ThumbnailUrl = None
    media: list[MediaUrl] = None
    buttons: list[CardAction] = None
    shareable: bool = None
    autoloop: bool = None
    autostart: bool = None
    aspect: NonEmptyString = None
    duration: NonEmptyString = None
    value: object = None

    def to_attachment(self) -> Attachment:
        """
        Creates a new Attachment that wraps this card.

        :returns: The generated attachment.
        """
        return Attachment(content_type=ContentTypes.audio_card, content=self)

    @overload
    def add_media(self, media: MediaUrl) -> "AudioCard": ...

    @overload
    def add_media(
        self, *, url: NonEmptyString, profile: NonEmptyString | None = None
    ) -> "AudioCard": ...

    def add_media(
        self,
        media: MediaUrl | None = None,
        *,
        url: NonEmptyString | None = None,
        profile: NonEmptyString | None = None,
    ) -> "AudioCard":
        """
        Adds a media URL and returns this card.

        :param media: The media URL to add.
        :param url: The URL of the media, used when no media instance is provided.
        :param profile: The profile of the media built from a URL.
        :returns: This card, to allow for method chaining.
        """
        if media is None:
            if url is None:
                raise ValueError(
                    "Either provide a MediaUrl instance or the url parameter."
                )
            media = pick_model(MediaUrl, url=url, profile=profile)

        self.media = self.media or []
        self.media.append(media)
        return self

    def add_button(self, button: CardAction) -> "AudioCard":
        """
        Adds a button and returns this card.

        :param button: The button to add.
        :returns: This card, to allow for method chaining.
        """
        self.buttons = self.buttons or []
        self.buttons.append(button)
        return self
