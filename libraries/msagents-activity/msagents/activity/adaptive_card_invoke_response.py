from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class AdaptiveCardInvokeResponse(AgentsModel):
    """AdaptiveCardInvokeResponse.

    Defines the structure that is returned as the result of an Invoke activity with Name of 'adaptiveCard/action'.

    :param status_code: The Card Action Response StatusCode.
    :type status_code: int
    :param type: The type of this Card Action Response.
    :type type: str
    :param value: The JSON response object.
    :type value: dict[str, object]
    """

    status_code: int = None
    type: NonEmptyString = None
    value: dict[NonEmptyString, object] = None
