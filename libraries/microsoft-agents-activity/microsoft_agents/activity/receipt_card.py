# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .attachment import Attachment
from .card import Card
from .content_types import ContentTypes
from .fact import Fact
from .receipt_item import ReceiptItem
from .card_action import CardAction
from ._type_aliases import NonEmptyString


class ReceiptCard(Card):
    """A receipt card.

    :param title: Title of the card
    :type title: str
    :param facts: Array of Fact objects
    :type facts: list[~microsoft_agents.activity.Fact]
    :param items: Array of Receipt Items
    :type items: list[~microsoft_agents.activity.ReceiptItem]
    :param tap: This action will be activated when user taps on the card
    :type tap: ~microsoft_agents.activity.CardAction
    :param total: Total amount of money paid (or to be paid)
    :type total: str
    :param tax: Total amount of tax paid (or to be paid)
    :type tax: str
    :param vat: Total amount of VAT paid (or to be paid)
    :type vat: str
    :param buttons: Set of actions applicable to the current card
    :type buttons: list[~microsoft_agents.activity.CardAction]
    """

    title: NonEmptyString = None
    facts: list[Fact] = None
    items: list[ReceiptItem] = None
    tap: CardAction = None
    total: NonEmptyString = None
    tax: NonEmptyString = None
    vat: NonEmptyString = None
    buttons: list[CardAction] = None

    def to_attachment(self) -> Attachment:
        """
        Creates a new Attachment that wraps this card.

        :returns: The generated attachment.
        """
        return Attachment(content_type=ContentTypes.receipt_card, content=self)

    def add_fact(self, fact: Fact) -> "ReceiptCard":
        """
        Adds a fact and returns this card.

        :param fact: The fact to add.
        :returns: This card, to allow for method chaining.
        """
        self.facts = self.facts or []
        self.facts.append(fact)
        return self

    def add_item(self, item: ReceiptItem) -> "ReceiptCard":
        """
        Adds a receipt item and returns this card.

        :param item: The receipt item to add.
        :returns: This card, to allow for method chaining.
        """
        self.items = self.items or []
        self.items.append(item)
        return self

    def add_button(self, button: CardAction) -> "ReceiptCard":
        """
        Adds a button and returns this card.

        :param button: The button to add.
        :returns: This card, to allow for method chaining.
        """
        self.buttons = self.buttons or []
        self.buttons.append(button)
        return self
