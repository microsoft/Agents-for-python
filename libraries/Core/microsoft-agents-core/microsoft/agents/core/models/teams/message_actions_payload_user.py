from pydantic import BaseModel


class MessageActionsPayloadUser(BaseModel):
    """Represents a user entity.

    :param user_identity_type: The identity type of the user. Possible values include: 'aadUser', 'onPremiseAadUser', 'anonymousGuest', 'federatedUser'
    :type user_identity_type: str
    :param id: The id of the user.
    :type id: str
    :param display_name: The plaintext display name of the user.
    :type display_name: str
    """

    user_identity_type: str
    id: str
    display_name: str
