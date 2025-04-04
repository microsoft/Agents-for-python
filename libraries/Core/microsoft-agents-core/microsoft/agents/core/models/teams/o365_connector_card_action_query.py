from pydantic import BaseModel


class O365ConnectorCardActionQuery(BaseModel):
    """O365 connector card action query.

    :param body: Body of the action query.
    :type body: str
    """

    body: str
