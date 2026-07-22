# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import overload

from .action_types import ActionTypes
from .attachment import Attachment
from .card import Card
from .card_action import CardAction
from .card_image import CardImage
from .content_types import ContentTypes
from ._type_aliases import NonEmptyString


class HeroCard(Card):
    """A Hero card (card with a single, large image).

    :param title: Title of the card
    :type title: str
    :param subtitle: Subtitle of the card
    :type subtitle: str
    :param text: Text for the card
    :type text: str
    :param images: Array of images for the card
    :type images: list[~microsoft_agents.activity.CardImage]
    :param buttons: Set of actions applicable to the current card
    :type buttons: list[~microsoft_agents.activity.CardAction]
    :param tap: This action will be activated when user taps on the card
     itself
    :type tap: ~microsoft_agents.activity.CardAction
    """

    title: NonEmptyString = None
    subtitle: NonEmptyString = None
    text: str = None
    images: list[CardImage] = None
    buttons: list[CardAction] = None
    tap: CardAction = None

    def to_attachment(self) -> Attachment:
        """
        Creates a new Attachment that wraps this card.

        :returns: The generated attachment.
        """
        return Attachment(content_type=ContentTypes.hero_card, content=self)

    @overload
    def add_image(self, image: CardImage) -> "HeroCard":
        ...

    @overload
    def add_image(
        self, *, url: NonEmptyString, alt: NonEmptyString | None = None
    ) -> "HeroCard":
        ...

    def add_image(
        self,
        image: CardImage | None = None,
        *,
        url: NonEmptyString | None = None,
        alt: NonEmptyString | None = None,
    ) -> "HeroCard":
        """
        Adds an image and returns this card.

        :param image: The image to add.
        :param url: The URL of the image, used when no image instance is provided.
        :param alt: The alternate text for the image built from a URL.
        :returns: This card, to allow for method chaining.
        """
        if image is None:
            if url is None:
                raise ValueError(
                    "Either provide a CardImage instance or the url parameter."
                )
            if alt is None:
                image = CardImage(url=url)
            else:
                image = CardImage(url=url, alt=alt)

        self.images = self.images or []
        self.images.append(image)
        return self

    @overload
    def add_button(self, button: CardAction) -> "HeroCard":
        ...

    @overload
    def add_button(
        self,
        *,
        title: NonEmptyString,
        type: NonEmptyString = ActionTypes.im_back,
        value: object | None = None,
    ) -> "HeroCard":
        ...

    def add_button(
        self,
        button: CardAction | None = None,
        *,
        title: NonEmptyString | None = None,
        type: NonEmptyString = ActionTypes.im_back,
        value: object | None = None,
    ) -> "HeroCard":
        """
        Adds a button and returns this card.

        :param button: The button to add.
        :param title: The title of the button, used when no button instance is provided.
        :param type: The action type of the button built from a title.
        :param value: The value of the button built from a title. Defaults to the title.
        :returns: This card, to allow for method chaining.
        """
        if button is None:
            if title is None:
                raise ValueError(
                    "Either provide a CardAction instance or the title parameter."
                )
            button = CardAction(
                type=type, title=title, value=value if value is not None else title
            )

        self.buttons = self.buttons or []
        self.buttons.append(button)
        return self

    def add_buttons(self, *buttons: CardAction) -> "HeroCard":
        """
        Adds one or more buttons and returns this card.

        :param buttons: The buttons to add.
        :returns: This card, to allow for method chaining.
        """
        if not buttons:
            return self

        self.buttons = self.buttons or []
        self.buttons.extend(buttons)
        return self
