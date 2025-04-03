from pydantic import BaseModel
from typing import Optional


class TeamsChannelAccount(BaseModel):
    """Teams channel account detailing user Azure Active Directory details.

    :param id: Channel id for the user or bot on this channel (Example: joe@smith.com, or @joesmith or 123456)
    :type id: str
    :param name: Display friendly name
    :type name: str
    :param given_name: Given name part of the user name.
    :type given_name: Optional[str]
    :param surname: Surname part of the user name.
    :type surname: Optional[str]
    :param email: Email Id of the user.
    :type email: Optional[str]
    :param user_principal_name: Unique user principal name.
    :type user_principal_name: Optional[str]
    :param tenant_id: Tenant Id of the user.
    :type tenant_id: Optional[str]
    :param user_role: User Role of the user.
    :type user_role: Optional[str]
    """

    id: str
    name: str
    given_name: Optional[str]
    surname: Optional[str]
    email: Optional[str]
    user_principal_name: Optional[str]
    tenant_id: Optional[str]
    user_role: Optional[str]
