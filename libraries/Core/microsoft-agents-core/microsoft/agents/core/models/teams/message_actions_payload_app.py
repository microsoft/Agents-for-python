from pydantic import BaseModel


class MessageActionsPayloadApp(BaseModel):
    """Represents an application entity.

    :param application_identity_type: The type of application. Possible values include: 'aadApplication', 'bot', 'tenantBot', 'office365Connector', 'webhook'
    :type application_identity_type: str
    :param id: The id of the application.
    :type id: str
    :param display_name: The plaintext display name of the application.
    :type display_name: str
    """

    application_identity_type: str
    id: str
    display_name: str
