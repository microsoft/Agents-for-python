# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import Field

from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class AdaptiveCardInvokeAction(AgentsModel):
    """AdaptiveCardInvokeAction.

    Defines the structure that arrives in the Activity.Value.Action for Invoke activity with
    name of 'adaptiveCard/action'.

    :param type: The Type of this Adaptive Card Invoke Action.
    :type type: str
    :param id: The Id of this Adaptive Card Invoke Action.
    :type id: str | None
    :param verb: The Verb of this Adaptive Card Invoke Action.
    :type verb: str | None
    :param data: The data of this Adaptive Card Invoke Action.
    :type data: dict[str, object]
    """

    type: str
    id: str | None = None
    verb: str | None = None
    data: dict[NonEmptyString, object] = Field(default_factory=dict)
