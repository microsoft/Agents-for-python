from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class TextHighlight(AgentsModel):
    """Refers to a substring of content within another field.

    :param text: Defines the snippet of text to highlight
    :type text: str
    :param occurrence: Occurrence of the text field within the referenced
     text, if multiple exist.
    :type occurrence: int
    """

    text: NonEmptyString
    occurrence: int
