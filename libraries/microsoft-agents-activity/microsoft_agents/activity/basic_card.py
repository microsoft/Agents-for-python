# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import overload

from typing_extensions import deprecated

from .action_types import ActionTypes
from .agents_model import AgentsModel
from .card_image import CardImage
from .card_action import CardAction
from ._model_utils import pick_model, SkipNone
from ._type_aliases import NonEmptyString


@deprecated(
    "BasicCard is not an Activity Protocol card type (it has no content type) "
    "and will be removed in a future release."
)
class BasicCard(AgentsModel):
    """A basic card.

    .. deprecated::
        BasicCard is not an Activity Protocol card type (it has no content type)
        and will be removed in a future release.

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

    @overload
    def add_image(self, image: CardImage) -> "BasicCard": ...

    @overload
    def add_image(
        self, *, url: NonEmptyString, alt: NonEmptyString | None = None
    ) -> "BasicCard": ...

    def add_image(
        self,
        image: CardImage | None = None,
        *,
        url: NonEmptyString | None = None,
        alt: NonEmptyString | None = None,
    ) -> "BasicCard":
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
            image = pick_model(CardImage, url=url, alt=SkipNone(alt))

        self.images = self.images or []
        self.images.append(image)
        return self

    @overload
    def add_button(self, button: CardAction) -> "BasicCard": ...

    @overload
    def add_button(
        self,
        *,
        title: NonEmptyString,
        type: NonEmptyString = ActionTypes.im_back,
        value: object | None = None,
    ) -> "BasicCard": ...

    def add_button(
        self,
        button: CardAction | None = None,
        *,
        title: NonEmptyString | None = None,
        type: NonEmptyString = ActionTypes.im_back,
        value: object | None = None,
    ) -> "BasicCard":
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

    def add_buttons(self, *buttons: CardAction) -> "BasicCard":
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
