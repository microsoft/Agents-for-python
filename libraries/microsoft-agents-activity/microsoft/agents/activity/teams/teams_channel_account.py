# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any
from pydantic import ConfigDict
from ..agents_model import AgentsModel


class TeamsChannelAccount(AgentsModel):
    """Teams channel account detailing user Azure Active Directory details.

    :param id: Channel id for the user or bot on this channel (Example: joe@smith.com, or @joesmith or 123456)
    :type id: str
    :param name: Display friendly name
    :type name: str
    :param given_name: Given name part of the user name.
    :type given_name: str
    :param surname: Surname part of the user name.
    :type surname: str
    :param email: Email Id of the user.
    :type email: str
    :param user_principal_name: Unique user principal name.
    :type user_principal_name: str
    :param tenant_id: Tenant Id of the user.
    :type tenant_id: str
    :param user_role: User Role of the user.
    :type user_role: str
    """

    model_config = ConfigDict(extra="allow")

    id: str = None
    name: str = None
    given_name: str = None
    surname: str = None
    email: str = None
    user_principal_name: str = None
    tenant_id: str = None
    user_role: str = None

    @property
    def properties(self) -> dict[str, Any]:
        """Returns the set of properties that are not None."""
        return self.model_extra
