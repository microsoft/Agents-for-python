from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class AdaptiveCardInvokeAction(AgentsModel):
    """AdaptiveCardInvokeAction.

    Defines the structure that arrives in the Activity.Value.Action for Invoke activity with
    name of 'adaptiveCard/action'.

    :param type: The Type of this Adaptive Card Invoke Action.
    :type type: str
    :param id: The Id of this Adaptive Card Invoke Action.
    :type id: str
    :param verb: The Verb of this Adaptive Card Invoke Action.
    :type verb: str
    :param data: The data of this Adaptive Card Invoke Action.
    :type data: dict[str, object]
    """

    type: NonEmptyString = None
    id: NonEmptyString = None
    verb: NonEmptyString = None
    data: dict[NonEmptyString, object] = None
