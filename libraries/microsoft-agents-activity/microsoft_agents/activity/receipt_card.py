# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .fact import Fact
from .receipt_item import ReceiptItem
from .card_action import CardAction
from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class ReceiptCard(AgentsModel):
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
