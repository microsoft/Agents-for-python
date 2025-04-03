from pydantic import BaseModel


class TabResponseCard(BaseModel):
    """Envelope for cards for a Tab request.

    :param card: Gets or sets adaptive card for this card tab response.
    :type card: object
    """

    card: object
