from pydantic import BaseModel


class O365ConnectorCardActionBase(BaseModel):
    """O365 connector card action base.

    :param type: Type of the action. Possible values include: 'ViewAction', 'OpenUri', 'HttpPOST', 'ActionCard'
    :type type: str
    :param name: Name of the action that will be used as button title
    :type name: str
    :param id: Action Id
    :type id: str
    """

    type: str
    name: str
    id: str
