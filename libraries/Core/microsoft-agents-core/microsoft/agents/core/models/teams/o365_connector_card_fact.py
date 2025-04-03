from pydantic import BaseModel


class O365ConnectorCardFact(BaseModel):
    """O365 connector card fact.

    :param name: Display name of the fact
    :type name: str
    :param value: Display value for the fact
    :type value: str
    """

    name: str
    value: str
