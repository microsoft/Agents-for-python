from .agents_model import AgentsModel


class MediaEventValue(AgentsModel):
    """Supplementary parameter for media events.

    :param card_value: Callback parameter specified in the Value field of the
     MediaCard that originated this event
    :type card_value: object
    """

    card_value: object = None
